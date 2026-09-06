{{ config(materialized='table') }}

WITH internal AS (
    SELECT * FROM {{ ref('stg_internal_transactions') }}
),

gateway AS (
    SELECT * FROM {{ ref('stg_gateway_transactions') }}
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
        END AS reconciliation_status,
        CURRENT_TIMESTAMP() AS reconciled_at
    FROM internal i
    LEFT JOIN gateway g
        ON i.transaction_id = g.transaction_id
),

missing_internal AS (
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
        'MISSING_INTERNAL' AS reconciliation_status,
        CURRENT_TIMESTAMP() AS reconciled_at
    FROM gateway g
    LEFT JOIN internal i
        ON g.transaction_id = i.transaction_id
    WHERE i.transaction_id IS NULL
)

SELECT * FROM matched
UNION ALL
SELECT * FROM missing_internal
