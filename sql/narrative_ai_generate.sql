-- Fraud-desk narrative with BigQuery AI.GENERATE (same prompt as app/narrative.py), run over the cases table.
-- Requires a BigQuery connection to Vertex AI / Agent Platform; see docs/DEPLOYMENT.md.
SELECT case_id,
  AI.GENERATE(
    CONCAT('You write concise, auditable fraud-desk records for a bank. Never invent facts. Case JSON: ', TO_JSON_STRING(c),
           ' Return a 4-6 sentence incident narrative and a 1930 cybercrime-helpline referral text.'),
    connection_id => 'asia-southeast1.vertex_conn',
    endpoint => 'gemini-3.8-flash'
  ).result AS fraud_desk_record
FROM `project.rakshak.cases` AS c
WHERE status IN ('on_hold', 'overridden_by_user', 'cancelled_by_user');
