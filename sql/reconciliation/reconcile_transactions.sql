-- PayFlow — Transaction Reconciliation (MySQL 8.0+)
--
-- Compares internal_transactions against the latest gateway_transactions
-- per provider and classifies the result.
--
-- Reconciliation statuses:
--   MATCH                  : amounts and statuses agree
--   AMOUNT_MISMATCH        : same transaction, different amount
--   STATUS_MISMATCH        : same transaction, different status
--   MISSING_FROM_GATEWAY   : internal has it, gateway does not
--   MISSING_INTERNAL       : gateway has it, internal does not

USE payflow;

TRUNCATE TABLE warehouse_fact_reconciliation;

INSERT INTO warehouse_fact_reconciliation (
    transaction_id,
    date_key,
    merchant_key,
    provider_key,
    internal_amount,
    gateway_amount,
    amount_difference,
    internal_status_key,
    gateway_status_key,
    reconciliation_status
)
WITH latest_gateway_record AS (
    -- Deduplicate gateway records: keep the most recent per transaction/provider.
    SELECT
        transaction_id,
        provider,
        merchant_id,
        amount,
        currency,
        status,
        transaction_timestamp,
        source_file,
        ROW_NUMBER() OVER (
            PARTITION BY transaction_id, provider
            ORDER BY transaction_timestamp DESC, loaded_at DESC
        ) AS rn
    FROM reconciliation_gateway_transactions
),

gateway AS (
    SELECT *
    FROM latest_gateway_record
    WHERE rn = 1
),

matched AS (
    SELECT
        i.transaction_id,
        DATE(i.transaction_timestamp) AS txn_date,
        i.merchant_id,
        g.provider,
        i.amount AS internal_amount,
        g.amount AS gateway_amount,
        (COALESCE(i.amount, 0) - COALESCE(g.amount, 0)) AS amount_difference,
        i.status AS internal_status,
        g.status AS gateway_status,
        CASE
            WHEN g.transaction_id IS NULL THEN 'MISSING_FROM_GATEWAY'
            WHEN i.amount <> g.amount THEN 'AMOUNT_MISMATCH'
            WHEN i.status <> g.status THEN 'STATUS_MISMATCH'
            ELSE 'MATCH'
        END AS reconciliation_status
    FROM reconciliation_internal_transactions i
    LEFT JOIN gateway g
        ON i.transaction_id = g.transaction_id
),

missing_internal AS (
    -- Gateway records that do not exist in internal transactions.
    SELECT
        g.transaction_id,
        DATE(g.transaction_timestamp) AS txn_date,
        g.merchant_id,
        g.provider,
        NULL AS internal_amount,
        g.amount AS gateway_amount,
        NULL AS amount_difference,
        NULL AS internal_status,
        g.status AS gateway_status,
        'MISSING_INTERNAL' AS reconciliation_status
    FROM gateway g
    LEFT JOIN reconciliation_internal_transactions i
        ON g.transaction_id = i.transaction_id
    WHERE i.transaction_id IS NULL
),

combined AS (
    SELECT * FROM matched
    UNION ALL
    SELECT * FROM missing_internal
)

SELECT
    c.transaction_id,
    CAST(DATE_FORMAT(c.txn_date, '%Y%m%d') AS UNSIGNED) AS date_key,
    m.merchant_key,
    p.provider_key,
    c.internal_amount,
    c.gateway_amount,
    c.amount_difference,
    s_in.status_key AS internal_status_key,
    s_gw.status_key AS gateway_status_key,
    c.reconciliation_status
FROM combined c
LEFT JOIN warehouse_dim_merchant m
    ON c.merchant_id = m.merchant_id
LEFT JOIN warehouse_dim_provider p
    ON COALESCE(c.provider, 'unknown') = p.provider_id
LEFT JOIN warehouse_dim_transaction_status s_in
    ON c.internal_status = s_in.status_code
LEFT JOIN warehouse_dim_transaction_status s_gw
    ON c.gateway_status = s_gw.status_code;

-- Summary view for dashboards and reports
CREATE OR REPLACE VIEW warehouse_v_reconciliation_summary AS
SELECT
    reconciliation_status,
    COUNT(*) AS transaction_count,
    COALESCE(SUM(ABS(COALESCE(internal_amount, 0) - COALESCE(gateway_amount, 0))), 0) AS total_discrepancy_amount
FROM warehouse_fact_reconciliation
GROUP BY reconciliation_status
ORDER BY transaction_count DESC;
