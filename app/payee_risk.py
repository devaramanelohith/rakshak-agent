"""Payee (mule-account) risk lookup.

Production path: BigQuery table built from AMLSim/PaySim-style graph features (see sql/payee_risk.sql).
Demo path: data/payees.json. Unknown payees get a conservative 'thin-file' record.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any

from .config import settings

log = logging.getLogger("rakshak.payee")

UNKNOWN_TEMPLATE: dict[str, Any] = {
    "display_name": "Unknown payee",
    "account_age_days": None,
    "fan_in_48h": None,
    "fan_out_48h": None,
    "inflow_48h_inr": None,
    "cash_out_ratio_7d": None,
    "dormant_days_before_burst": None,
    "avg_ticket_inr": None,
    "fri_level": "unknown",
    "linked_complaints_1930": 0,
    "kyc_tier": "unknown",
    "mule_risk_score": 0.3,
    "risk_band": "medium",
    "reasons": ["No history for this payee in the risk table (thin file)"],
    "source": "unknown",
}


@lru_cache(maxsize=1)
def _local_table() -> dict[str, dict]:
    path = settings.data_dir / "payees.json"
    if not path.exists():
        log.warning("payees.json missing at %s", path)
        return {}
    rows = json.loads(path.read_text(encoding="utf-8"))
    return {r["vpa"].lower(): r for r in rows}


def _from_bigquery(vpa: str) -> dict | None:  # pragma: no cover - needs GCP
    try:
        from google.cloud import bigquery
    except ImportError:
        log.warning("google-cloud-bigquery not installed; falling back to local table")
        return None
    try:
        bq = bigquery.Client(project=settings.project)
        q = f"SELECT * FROM `{settings.bigquery_payee_table}` WHERE LOWER(vpa) = @vpa LIMIT 1"
        job = bq.query(q, job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("vpa", "STRING", vpa.lower())]))
        for row in job.result():
            d = dict(row.items())
            d["source"] = "bigquery"
            return d
        return None
    except Exception as e:
        log.warning("BigQuery lookup failed (%s); using local table", str(e)[:120])
        return None


def lookup_payee(vpa: str) -> dict:
    vpa = (vpa or "").strip().lower()
    row: dict | None = None
    if settings.bigquery_payee_table:
        row = _from_bigquery(vpa)
    if row is None:
        row = _local_table().get(vpa)
        if row is not None:
            row = {**row, "source": "local_table"}
    if row is None:
        row = {**UNKNOWN_TEMPLATE, "vpa": vpa}
    return row


def all_payees() -> list[dict]:
    return list(_local_table().values())
