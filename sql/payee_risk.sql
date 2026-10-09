-- Payee mule-risk features from a UPI/IMPS transaction ledger (AMLSim / PaySim shaped).
-- Replace `project.rakshak.transactions` with the bank's ledger table (payer_vpa, payee_vpa, amount_inr, ts, channel).
CREATE OR REPLACE TABLE `project.rakshak.payee_risk` AS
WITH inflow AS (
  SELECT payee_vpa AS vpa,
         COUNT(DISTINCT payer_vpa) AS fan_in_48h,
         SUM(amount_inr) AS inflow_48h_inr,
         AVG(amount_inr) AS avg_ticket_inr
  FROM `project.rakshak.transactions`
  WHERE ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
  GROUP BY vpa
), outflow AS (
  SELECT payer_vpa AS vpa, COUNT(DISTINCT payee_vpa) AS fan_out_48h, SUM(amount_inr) AS outflow_7d_inr
  FROM `project.rakshak.transactions`
  WHERE ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  GROUP BY vpa
), age AS (
  SELECT vpa, DATE_DIFF(CURRENT_DATE(), DATE(MIN(ts)), DAY) AS account_age_days,
         DATE_DIFF(DATE(MAX(ts)), DATE(MIN(ts)), DAY) AS active_span_days
  FROM (SELECT payee_vpa AS vpa, ts FROM `project.rakshak.transactions`
        UNION ALL SELECT payer_vpa, ts FROM `project.rakshak.transactions`)
  GROUP BY vpa
), feats AS (
  SELECT a.vpa, a.account_age_days,
         IFNULL(i.fan_in_48h, 0) AS fan_in_48h, IFNULL(o.fan_out_48h, 0) AS fan_out_48h,
         IFNULL(i.inflow_48h_inr, 0) AS inflow_48h_inr, IFNULL(i.avg_ticket_inr, 0) AS avg_ticket_inr,
         SAFE_DIVIDE(IFNULL(o.outflow_7d_inr, 0), NULLIF(IFNULL(i.inflow_48h_inr, 0), 0)) AS cash_out_ratio_7d,
         GREATEST(a.active_span_days - 2, 0) AS dormant_days_before_burst,
         f.fri_level, IFNULL(c.linked_complaints_1930, 0) AS linked_complaints_1930, k.kyc_tier
  FROM age a
  LEFT JOIN inflow i USING (vpa) LEFT JOIN outflow o USING (vpa)
  LEFT JOIN `project.rakshak.fri_lookup` f USING (vpa)          -- telecom Financial Risk Indicator feed
  LEFT JOIN `project.rakshak.complaints_1930` c USING (vpa)     -- cybercrime-helpline complaint counts
  LEFT JOIN `project.rakshak.kyc` k USING (vpa)
)
SELECT *,
  -- transparent, monotone score; swap for a Vertex AI / BQML model when labelled mule data exists
  LEAST(1.0,
    0.30 * (fan_in_48h >= 8) + 0.20 * (cash_out_ratio_7d >= 0.8) + 0.15 * (dormant_days_before_burst >= 30)
    + 0.15 * (fri_level IN ('high','very_high')) + 0.15 * (linked_complaints_1930 > 0) + 0.05 * (account_age_days < 30)
  ) AS mule_risk_score,
  CASE WHEN fan_in_48h >= 8 AND cash_out_ratio_7d >= 0.8 THEN 'critical'
       WHEN fan_in_48h >= 5 OR linked_complaints_1930 > 0 OR fri_level IN ('high','very_high') THEN 'high'
       WHEN account_age_days < 30 OR cash_out_ratio_7d >= 0.6 THEN 'medium' ELSE 'low' END AS risk_band,
  ARRAY<STRING>[] AS reasons
FROM feats;
