SELECT
    transaction_id,
    transaction_timestamp,
    merchant_id,
    amount,
    currency,
    status,
    source_system,
    source_file,
    loaded_at
FROM {{ source('payflow', 'reconciliation_internal_transactions') }}
