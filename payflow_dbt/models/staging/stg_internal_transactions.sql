SELECT
    transaction_id,
    transaction_timestamp,
    merchant_id,
    amount,
    currency,
    status,
    loaded_at,
    'internal' AS source_system
FROM {{ source('payflow', 'reconciliation_internal_transactions') }}
