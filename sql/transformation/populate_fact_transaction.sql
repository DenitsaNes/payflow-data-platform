-- PayFlow — Populate fact_transaction from cleaned gateway transactions.
-- This represents the Gold layer: business-ready transaction facts.

USE payflow;

TRUNCATE TABLE warehouse_fact_transaction;

INSERT INTO warehouse_fact_transaction (
    transaction_id,
    transaction_timestamp,
    date_key,
    merchant_key,
    provider_key,
    currency_key,
    status_key,
    amount,
    source_file
)
SELECT
    g.transaction_id,
    g.transaction_timestamp,
    CAST(DATE_FORMAT(DATE(g.transaction_timestamp), '%Y%m%d') AS UNSIGNED) AS date_key,
    m.merchant_key,
    p.provider_key,
    c.currency_key,
    s.status_key,
    g.amount,
    g.source_file
FROM reconciliation_gateway_transactions g
LEFT JOIN warehouse_dim_merchant m
    ON g.merchant_id = m.merchant_id
LEFT JOIN warehouse_dim_provider p
    ON g.provider = p.provider_id
LEFT JOIN warehouse_dim_currency c
    ON g.currency = c.currency_code
LEFT JOIN warehouse_dim_transaction_status s
    ON g.status = s.status_code;
