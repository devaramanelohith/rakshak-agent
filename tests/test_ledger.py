import os

os.environ["RAKSHAK_FAKE_LLM"] = "1"

from app.ledger import LedgerSimulator, score_features  # noqa: E402
from app.payee_risk import all_payees, lookup_payee  # noqa: E402


def _sim():
    return LedgerSimulator(all_payees(), seed=3)


def test_critical_payee_features_reproduce_band():
    sim = _sim()
    crit = [p for p in all_payees() if p["risk_band"] == "critical"]
    assert crit
    hits = 0
    for p in crit:
        f = sim.features(p["vpa"])
        score, band, reasons = score_features(f, p)
        hits += band in ("critical", "high")
    assert hits >= len(crit) * 0.8


def test_low_payee_stays_low_or_medium():
    sim = _sim()
    low = [p for p in all_payees() if p["risk_band"] == "low"]
    bad = 0
    for p in low:
        f = sim.features(p["vpa"])
        _, band, _ = score_features(f, p)
        bad += band in ("critical", "high")
    assert bad <= max(1, len(low) // 10)


def test_tick_adds_transactions_and_lookup_has_lineage():
    sim = _sim()
    before = sim.stats()["tx_in_window"]
    sim.tick(batch=20)
    assert sim.stats()["tx_in_window"] >= before + 20
    row = lookup_payee("cbi.verification@rakshakdemo")
    assert isinstance(row["lineage"], (dict, str))
    if isinstance(row["lineage"], dict):
        assert row["lineage"]["source"] == "simulated_ledger" and "n_transactions" in row["lineage"]
    assert row["risk_band"] in ("critical", "high")


def test_ledger_stays_calibrated_over_three_days_of_uptime(monkeypatch):
    """Regression: the stream used to give mule accounts a new victim on every tick, so a long-running instance
    showed hundreds of payers in 48 h for an account profiled with five."""
    import time as real_time

    import app.ledger as L

    clock = {"t": real_time.time()}

    class FakeTime:
        @staticmethod
        def time():
            return clock["t"]

    monkeypatch.setattr(L, "time", FakeTime)
    payees = all_payees()
    sim = LedgerSimulator(payees, seed=5)
    for _ in range(int(3 * 86400 / 30)):
        clock["t"] += 30
        sim.tick(batch=12, tick_s=30)
    worst = 0.0
    crit_ok = crit_n = 0
    for p in payees:
        f = sim.features(p["vpa"])
        assert f is not None
        base = max(int(p.get("fan_in_48h") or 1), 5)
        worst = max(worst, f["fan_in_48h"] / base)
        if p["risk_band"] == "critical":
            crit_n += 1
            _, band, _ = score_features(f, p)
            crit_ok += band in ("critical", "high")
    assert worst <= 3.0, f"fan-in drifted to {worst:.1f}x its profile"
    assert crit_ok >= crit_n * 0.8
