"""Synthetic UPI ledger and ledger-derived payee features.

The bank's real signal for a mule account is its own ledger: who paid this VPA in the last 48 hours, how fast the
money left, how old or dormant the account is. Here a simulator plays the payment rail: it seeds seven days of
history shaped by the demo payee profiles, keeps streaming new transactions while the server runs, and the payee
features are recomputed from that stream with the same formula as sql/payee_risk.sql. Registry fields that a bank
gets from outside (telecom FRI, 1930 complaint counts, KYC tier) stay static. Optional sinks mirror the stream to
Pub/Sub and BigQuery so the production path is the same code.
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass

from .config import settings

log = logging.getLogger("rakshak.ledger")
DAY = 86400.0
WINDOW_7D = 7 * DAY
WINDOW_48H = 2 * DAY


@dataclass
class Tx:
    tx_id: str
    ts: float
    payer_vpa: str
    payee_vpa: str
    amount_inr: float
    kind: str  # inflow | cashout


class LedgerSimulator:
    def __init__(self, payees: list[dict], seed: int = 7) -> None:
        self.rng = random.Random(seed)
        self.profiles: dict[str, dict] = {p["vpa"].lower(): p for p in payees}
        self.txs: deque[Tx] = deque()
        self.by_payee: dict[str, deque[Tx]] = defaultdict(deque)
        self.history: dict[str, dict] = {}  # per vpa: first_seen_ts, last_tx_before_window_ts, prior_tx_count
        self.total_generated = 0
        self.started_at = time.time()
        self.last_tick = 0.0
        self.sinks: list[str] = []
        self._pending_sink: list[Tx] = []
        self._seed_history()

    # ------------------------------------------------------------------ generation
    def _seed_history(self) -> None:
        now = time.time()
        for vpa, p in self.profiles.items():
            age_days = int(p.get("account_age_days") or 365)
            first_seen = now - age_days * DAY
            dormant = int(p.get("dormant_days_before_burst") or 0)
            band = p.get("risk_band", "low")
            # Activity before the 7-day window: dormant accounts went quiet `dormant` days before the burst.
            last_before = now - (dormant * DAY if dormant else 8 * DAY)
            prior_count = 0 if age_days < 30 else (3 if dormant else self.rng.randint(20, 400))
            self.history[vpa] = {"first_seen_ts": min(first_seen, now - DAY), "last_tx_before_window_ts": min(last_before, now - WINDOW_7D), "prior_tx_count": prior_count}
            for tx in self._pattern(vpa, p, band, now - WINDOW_7D, now):
                self._append(tx)
        self.total_generated = len(self.txs)

    def _pattern(self, vpa: str, p: dict, band: str, t0: float, t1: float) -> list[Tx]:
        """Generate inflows/cashouts for one payee between t0 and t1 that reproduce its profile."""
        out: list[Tx] = []
        r = self.rng
        fan_in = int(p.get("fan_in_48h") or 2)
        avg = float(p.get("avg_ticket_inr") or 1500)
        cash = float(p.get("cash_out_ratio_7d") or 0.1)
        if band in ("critical", "high"):
            # burst in the last 48 h from many distinct payers, then rapid cash-out
            burst_start = t1 - WINDOW_48H * r.uniform(0.6, 1.0)
            n = max(fan_in, 8 if band == "critical" else 5)
            for i in range(n):
                ts = r.uniform(burst_start, t1 - 600)
                amt = max(500.0, r.gauss(avg, avg * 0.35))
                out.append(Tx(uuid.uuid4().hex[:12], ts, f"victim{r.randint(100, 999)}@rakshakdemo", vpa, round(amt, 2), "inflow"))
            inflow = sum(t.amount_inr for t in out)
            remaining = inflow * max(cash, 0.75 if band == "critical" else 0.6)
            k = r.randint(2, 4)
            for i in range(k):
                out.append(Tx(uuid.uuid4().hex[:12], min(t1 - 60, max(t.ts for t in out) + r.uniform(600, 7200)), vpa, f"mule{r.randint(10, 99)}@rakshakdemo", round(remaining / k, 2), "cashout"))
        elif band == "medium":
            n = max(2, fan_in)
            for i in range(n):
                ts = r.uniform(t0, t1 - 600)
                out.append(Tx(uuid.uuid4().hex[:12], ts, f"payer{r.randint(100, 999)}@rakshakdemo", vpa, round(max(200.0, r.gauss(avg, avg * 0.4)), 2), "inflow"))
            inflow = sum(t.amount_inr for t in out)
            out.append(Tx(uuid.uuid4().hex[:12], t1 - r.uniform(3600, DAY), vpa, f"acct{r.randint(10, 99)}@rakshakdemo", round(inflow * min(cash, 0.6), 2), "cashout"))
        else:
            # ordinary merchant or individual: steady inflows over the week, low cash-out
            n = max(1, int(fan_in * 3.5)) if fan_in else r.randint(1, 4)
            payers = [f"cust{r.randint(100, 999)}@rakshakdemo" for _ in range(max(1, fan_in))]
            for i in range(n):
                ts = r.uniform(t0, t1 - 600)
                out.append(Tx(uuid.uuid4().hex[:12], ts, r.choice(payers), vpa, round(max(50.0, r.gauss(avg, avg * 0.5)), 2), "inflow"))
            inflow = sum(t.amount_inr for t in out)
            if cash > 0:
                out.append(Tx(uuid.uuid4().hex[:12], t1 - r.uniform(3600, 3 * DAY), vpa, "ownbank.settlement@rakshakdemo", round(inflow * min(cash, 0.3), 2), "cashout"))
        return sorted(out, key=lambda t: t.ts)

    def _append(self, tx: Tx) -> None:
        self.txs.append(tx)
        key = tx.payee_vpa if tx.kind == "inflow" else tx.payer_vpa
        self.by_payee[key].append(tx)

    def tick(self, batch: int = 12) -> list[Tx]:
        """Add a few fresh transactions (keeps the demo 'live') and prune beyond 7 days."""
        now = time.time()
        r = self.rng
        new: list[Tx] = []
        vpas = list(self.profiles.keys())
        for _ in range(batch):
            vpa = r.choice(vpas)
            p = self.profiles[vpa]
            band = p.get("risk_band", "low")
            avg = float(p.get("avg_ticket_inr") or 1500)
            if band in ("critical", "high"):
                # a mule receives from a new victim and forwards most of it within minutes: keep the ratio true to profile
                amt = round(max(500.0, r.gauss(avg, avg * 0.35)), 2)
                tx = Tx(uuid.uuid4().hex[:12], now - r.uniform(5, 30), f"victim{r.randint(100, 999)}@rakshakdemo", vpa, amt, "inflow")
                self._append(tx)
                new.append(tx)
                cash = float(p.get("cash_out_ratio_7d") or 0.9)
                tx = Tx(uuid.uuid4().hex[:12], now - r.uniform(0, 5), vpa, f"mule{r.randint(10, 99)}@rakshakdemo", round(amt * max(cash, 0.85), 2), "cashout")
            else:
                tx = Tx(uuid.uuid4().hex[:12], now - r.uniform(0, 30), f"cust{r.randint(100, 999)}@rakshakdemo", vpa, round(max(50.0, r.gauss(avg, avg * 0.5)), 2), "inflow")
            self._append(tx)
            new.append(tx)
        self.total_generated += len(new)
        self.last_tick = now
        cutoff = now - WINDOW_7D
        while self.txs and self.txs[0].ts < cutoff:
            old = self.txs.popleft()
            key = old.payee_vpa if old.kind == "inflow" else old.payer_vpa
            dq = self.by_payee.get(key)
            if dq and dq[0] is old:
                dq.popleft()
            h = self.history.setdefault(key, {"first_seen_ts": old.ts, "last_tx_before_window_ts": old.ts, "prior_tx_count": 0})
            h["last_tx_before_window_ts"] = old.ts
            h["prior_tx_count"] += 1
        self._pending_sink.extend(new)
        return new

    # ------------------------------------------------------------------ features
    def features(self, vpa: str) -> dict | None:
        vpa = vpa.lower()
        txs = list(self.by_payee.get(vpa, ()))
        hist = self.history.get(vpa)
        if not txs and not hist:
            return None
        now = time.time()
        inflow48 = [t for t in txs if t.kind == "inflow" and t.ts >= now - WINDOW_48H]
        inflow7 = [t for t in txs if t.kind == "inflow"]
        out7 = [t for t in txs if t.kind == "cashout"]
        fan_in = len({t.payer_vpa for t in inflow48})
        fan_out = len({t.payee_vpa for t in out7 if t.ts >= now - WINDOW_48H})
        inflow_sum48 = sum(t.amount_inr for t in inflow48)
        inflow_sum7 = sum(t.amount_inr for t in inflow7)
        out_sum7 = sum(t.amount_inr for t in out7)
        cash_out = round(min(1.5, out_sum7 / inflow_sum7), 3) if inflow_sum7 else 0.0
        first_seen = (hist or {}).get("first_seen_ts") or (txs[0].ts if txs else now)
        age_days = int((now - first_seen) / DAY)
        first_in_window = min((t.ts for t in inflow7), default=now)
        last_before = (hist or {}).get("last_tx_before_window_ts")
        dormant = int((first_in_window - last_before) / DAY) if last_before and (hist or {}).get("prior_tx_count", 0) else 0
        avg_ticket = round(inflow_sum48 / len(inflow48), 2) if inflow48 else 0.0
        return {
            "account_age_days": age_days,
            "fan_in_48h": fan_in,
            "fan_out_48h": fan_out,
            "inflow_48h_inr": round(inflow_sum48, 2),
            "cash_out_ratio_7d": cash_out,
            "dormant_days_before_burst": max(0, dormant),
            "avg_ticket_inr": avg_ticket,
            "tx_count_7d": len(txs),
        }

    def recent(self, vpa: str, limit: int = 12) -> list[dict]:
        txs = list(self.by_payee.get(vpa.lower(), ()))[-limit:]
        return [{"tx_id": t.tx_id, "ts": t.ts, "payer_vpa": t.payer_vpa, "payee_vpa": t.payee_vpa, "amount_inr": t.amount_inr, "kind": t.kind} for t in reversed(txs)]

    def stats(self) -> dict:
        now = time.time()
        return {
            "tx_in_window": len(self.txs),
            "tx_generated_total": self.total_generated,
            "tx_last_minute": sum(1 for t in reversed(self.txs) if t.ts >= now - 60),
            "payees": len(self.profiles),
            "last_tick": self.last_tick,
            "uptime_s": int(now - self.started_at),
            "sinks": self.sinks,
            "formula": "sql/payee_risk.sql",
        }

    # ------------------------------------------------------------------ sinks
    def flush_sinks(self) -> None:  # pragma: no cover - needs GCP
        if not self._pending_sink:
            return
        batch, self._pending_sink = self._pending_sink, []
        rows = [{"tx_id": t.tx_id, "ts": t.ts, "payer_vpa": t.payer_vpa, "payee_vpa": t.payee_vpa, "amount_inr": t.amount_inr, "kind": t.kind} for t in batch]
        if settings.bigquery_ledger_table:
            try:
                from google.cloud import bigquery

                bq = bigquery.Client(project=settings.project)
                errors = bq.insert_rows_json(settings.bigquery_ledger_table, rows)
                if errors:
                    log.warning("BigQuery insert errors: %s", str(errors)[:200])
                elif "bigquery" not in self.sinks:
                    self.sinks.append("bigquery")
            except Exception as e:
                log.warning("BigQuery sink failed: %s", str(e)[:120])
        if settings.pubsub_ledger_topic:
            try:
                from google.cloud import pubsub_v1

                pub = pubsub_v1.PublisherClient()
                topic = settings.pubsub_ledger_topic
                if not topic.startswith("projects/"):
                    topic = pub.topic_path(settings.project, topic)
                for row in rows:
                    pub.publish(topic, json.dumps(row).encode("utf-8"), event_type="upi_transaction")
                if "pubsub" not in self.sinks:
                    self.sinks.append("pubsub")
            except Exception as e:
                log.warning("Pub/Sub sink failed: %s", str(e)[:120])


# ---------------------------------------------------------------------- scoring (mirrors sql/payee_risk.sql)
def score_features(f: dict, registry: dict) -> tuple[float, str, list[str]]:
    fan_in = f.get("fan_in_48h") or 0
    cash = f.get("cash_out_ratio_7d") or 0.0
    dormant = f.get("dormant_days_before_burst") or 0
    age = f.get("account_age_days")
    fri = (registry.get("fri_level") or "none").lower()
    complaints = int(registry.get("linked_complaints_1930") or 0)
    score = (0.30 * (fan_in >= 8) + 0.20 * (cash >= 0.8) + 0.15 * (dormant >= 30)
             + 0.15 * (fri in ("high", "very_high")) + 0.15 * (complaints > 0) + 0.05 * (age is not None and age < 30))
    score = round(min(1.0, score), 2)
    # Band follows the score: many payers alone is normal for a shop or a hospital; it is the combination with
    # rapid cash-out, dormancy, a new account or registry hits that marks a mule.
    if score >= 0.85:
        band = "critical"
    elif score >= 0.65:
        band = "high"
    elif score >= 0.35:
        band = "medium"
    else:
        band = "low"
    reasons: list[str] = []
    if band == "low":
        return score, band, [f"Steady pattern: {fan_in} regular payers in 48 h, {int(cash * 100)}% moved out this week, account {age} days old" if age is not None else "Steady, ordinary payment pattern"]
    if fan_in >= 8:
        reasons.append(f"Received money from {fan_in} different payers in the last 48 hours")
    if cash >= 0.8:
        reasons.append(f"{int(cash * 100)}% of the money received this week was moved out within hours")
    if dormant >= 30:
        reasons.append(f"Account was silent for {dormant} days, then suddenly active")
    if age is not None and age < 30:
        reasons.append(f"Account is only {age} days old")
    if complaints > 0:
        reasons.append(f"Named in {complaints} cybercrime-helpline (1930) complaints")
    if fri in ("high", "very_high"):
        reasons.append(f"Telecom Financial Risk Indicator for the linked mobile is {fri.replace('_', ' ')}")
    if not reasons:
        reasons.append("Steady, ordinary payment pattern; no risk indicators")
    return score, band, reasons[:3]


_sim: LedgerSimulator | None = None


def simulator() -> LedgerSimulator | None:
    global _sim
    if _sim is None and settings.ledger_enabled:
        path = settings.data_dir / "payees.json"
        payees = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        _sim = LedgerSimulator(payees)
        log.info("ledger simulator seeded: %d txs for %d payees", len(_sim.txs), len(_sim.profiles))
    return _sim


async def run_ticker(interval_s: float = 5.0) -> None:
    sim = simulator()
    if sim is None:
        return
    while True:
        await asyncio.sleep(interval_s)
        try:
            sim.tick()
            sim.flush_sinks()
        except Exception as e:  # pragma: no cover
            log.warning("ledger tick failed: %s", e)
