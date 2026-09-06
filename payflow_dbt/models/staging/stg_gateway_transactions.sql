WITH deduplicated AS (
    SELECT
        transaction_id,
        provider,
        transaction_timestamp,
        merchant_id,
        amount,
        currency,
        status,
        source_file,
        loaded_at,
        ROW_NUMBER() OVER (
            PARTITION BY transaction_id, provider
            ORDER BY transaction_timestamp DESC, loaded_at DESC
        ) AS rn
    FROM {{ source('payflow', 'reconciliation_gateway_transactions') }}
)

SELECT
    transaction_id,
    provider,
    transaction_timestamp,
    merchant_id,
    amount,
    currency,
    status,
    source_file,
    loaded_at
FROM deduplicated
WHERE rn = 1
