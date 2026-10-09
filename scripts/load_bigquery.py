"""Create the BigQuery dataset/table for payee mule risk and load data/payees.json.
Usage: uv run python scripts/load_bigquery.py --project $GOOGLE_CLOUD_PROJECT --dataset rakshak --table payee_risk
Then set BIGQUERY_PAYEE_TABLE=project.rakshak.payee_risk for the app."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from google.cloud import bigquery

ROOT = Path(__file__).resolve().parent.parent

SCHEMA = [
    bigquery.SchemaField("vpa", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("display_name", "STRING"),
    bigquery.SchemaField("account_age_days", "INT64"),
    bigquery.SchemaField("fan_in_48h", "INT64"),
    bigquery.SchemaField("fan_out_48h", "INT64"),
    bigquery.SchemaField("inflow_48h_inr", "FLOAT64"),
    bigquery.SchemaField("cash_out_ratio_7d", "FLOAT64"),
    bigquery.SchemaField("dormant_days_before_burst", "INT64"),
    bigquery.SchemaField("avg_ticket_inr", "FLOAT64"),
    bigquery.SchemaField("fri_level", "STRING"),
    bigquery.SchemaField("linked_complaints_1930", "INT64"),
    bigquery.SchemaField("kyc_tier", "STRING"),
    bigquery.SchemaField("mule_risk_score", "FLOAT64"),
    bigquery.SchemaField("risk_band", "STRING"),
    bigquery.SchemaField("reasons", "STRING", mode="REPEATED"),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--dataset", default="rakshak")
    ap.add_argument("--table", default="payee_risk")
    ap.add_argument("--location", default="asia-southeast1")
    a = ap.parse_args()
    bq = bigquery.Client(project=a.project)
    ds_ref = bigquery.Dataset(f"{a.project}.{a.dataset}")
    ds_ref.location = a.location
    bq.create_dataset(ds_ref, exists_ok=True)
    table_id = f"{a.project}.{a.dataset}.{a.table}"
    bq.create_table(bigquery.Table(table_id, schema=SCHEMA), exists_ok=True)
    rows = json.loads((ROOT / "data" / "payees.json").read_text(encoding="utf-8"))
    job = bq.load_table_from_json(rows, table_id, job_config=bigquery.LoadJobConfig(schema=SCHEMA, write_disposition="WRITE_TRUNCATE"))
    job.result()
    print(f"loaded {len(rows)} rows into {table_id}")
    print(f"export BIGQUERY_PAYEE_TABLE={table_id}")


if __name__ == "__main__":
    main()
