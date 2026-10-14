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
