"""Evaluate Rakshak on data/eval/calls.json.

Two measurements per call:
  1. Call-level detection: the rubric's risk_score on the transcript up to the payment attempt (or the whole call)
     versus the label, at the hold threshold.
  2. Payment-level decision: the fusion policy (call rubric x payee risk x profile) versus the expected action
     (scam -> hold/hold_and_alert, benign -> proceed/warn).
Writes data/runtime/eval_results.json and docs/EVAL_RESULTS.md.

Usage: uv run python scripts/eval.py [--limit N] [--stub]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--stub", action="store_true", help="use the keyword stub instead of Gemini")
    ap.add_argument("--concurrency", type=int, default=4)
    args = ap.parse_args()
    if args.stub:
        os.environ["RAKSHAK_FAKE_LLM"] = "1"

    from app.analysis import analyze_transcript  # noqa: E402
    from app.config import configure_env, settings  # noqa: E402
    from app.payee_risk import lookup_payee  # noqa: E402
    from app.policy import fuse  # noqa: E402

    configure_env()
    calls = json.loads((ROOT / "data" / "eval" / "calls.json").read_text(encoding="utf-8"))
    if args.limit:
        calls = calls[: args.limit]
    sem = asyncio.Semaphore(args.concurrency)

    async def one(c: dict) -> dict:
        async with sem:
            t0 = time.time()
            turns = [{"t": t["t"], "speaker": t["speaker"], "text": t["text"]} for t in c["turns"]]
            pay = c.get("payment_attempt")
            if pay and pay.get("at_t") is not None:
                turns_upto = [t for t in turns if t["t"] <= pay["at_t"]] or turns
            else:
                turns_upto = turns
            profile = {"age_band": c["victim_profile"]["age_band"], "language": c["victim_profile"]["preferred_language"],
                       "trusted_contact_name": c["victim_profile"].get("trusted_contact"), "typical_transfer_inr": 5000}
            try:
                rubric = await analyze_transcript(turns_upto, profile)
                err = None
            except Exception as e:  # pragma: no cover
                from app.analysis import Rubric
                rubric, err = Rubric(), str(e)[:120]
            payee = lookup_payee(pay["vpa"]) if pay else None
            fusion = fuse(rubric.risk_score, rubric.signals, payee, float(pay["amount_inr"]) if pay else 0.0, profile) if pay else None
            return {
                "id": c["id"], "label": c["label"], "scam_type": c.get("scam_type"), "language": c["language"],
                "risk_score": rubric.risk_score, "scam_type_pred": rubric.scam_type, "stage": rubric.stage,
                "signals_pred": rubric.signals, "signals_expected": c["expected_signals"],
                "payment": bool(pay), "payee_band": payee.get("risk_band") if payee else None,
                "fusion_score": fusion.score if fusion else None, "action": fusion.action if fusion else None,
                "latency_ms": int((time.time() - t0) * 1000), "error": err,
            }

    results = await asyncio.gather(*(one(c) for c in calls))
    thr = settings.hold_threshold
    tp = sum(1 for r in results if r["label"] == "scam" and r["risk_score"] >= thr)
    fn = sum(1 for r in results if r["label"] == "scam" and r["risk_score"] < thr)
    fp = sum(1 for r in results if r["label"] == "benign" and r["risk_score"] >= thr)
    tn = sum(1 for r in results if r["label"] == "benign" and r["risk_score"] < thr)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    pay_rows = [r for r in results if r["payment"]]
    pay_ok = sum(1 for r in pay_rows if (r["label"] == "scam") == (r["action"] in ("hold", "hold_and_alert")))
    sig_total = sig_hit = 0
    for r in results:
        for k, v in r["signals_expected"].items():
            sig_total += 1
            sig_hit += int(bool(r["signals_pred"].get(k)) == bool(v))
    summary = {
        "n": len(results), "threshold": thr, "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": round(prec, 3), "recall": round(rec, 3), "f1": round(f1, 3),
        "payment_decisions": len(pay_rows), "payment_decision_accuracy": round(pay_ok / len(pay_rows), 3) if pay_rows else None,
        "signal_accuracy": round(sig_hit / sig_total, 3) if sig_total else None,
        "mean_latency_ms": int(sum(r["latency_ms"] for r in results) / len(results)),
        "model": "stub" if settings.fake_llm else settings.model_rubric, "run_at": time.time(),
    }
    out = {"summary": summary, "results": results}
    settings.runtime_dir.mkdir(parents=True, exist_ok=True)
    (settings.runtime_dir / "eval_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    md = [f"# Rakshak evaluation ({summary['model']})", "",
          f"n={summary['n']} calls, hold threshold {thr}", "",
          "| metric | value |", "|---|---|",
          f"| precision (scam detection at payment moment) | {summary['precision']} |",
          f"| recall | {summary['recall']} |", f"| F1 | {summary['f1']} |",
          f"| signal accuracy (8 signals x calls) | {summary['signal_accuracy']} |",
          f"| payment decision accuracy (fusion policy) | {summary['payment_decision_accuracy']} |",
          f"| mean rubric latency | {summary['mean_latency_ms']} ms |", "",
          "| id | label | lang | risk | pred type | action | payee band |", "|---|---|---|---|---|---|---|"]
    for r in results:
        md.append(f"| {r['id']} | {r['label']} | {r['language']} | {r['risk_score']:.2f} | {r['scam_type_pred']} | {r['action'] or '-'} | {r['payee_band'] or '-'} |")
    (ROOT / "docs" / "EVAL_RESULTS.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    for r in results:
        flag = "" if (r["label"] == "scam") == (r["risk_score"] >= thr) else "  <-- MISS"
        print(f"{r['id']} {r['label']:6} {r['language']:8} risk={r['risk_score']:.2f} type={r['scam_type_pred']:14} action={r['action']}{flag}")


if __name__ == "__main__":
    asyncio.run(main())
