{{ config(materialized='view') }}

SELECT
    silver_id,
    transaction_id,
    transaction_timestamp,
    source_system,
    provider,
    merchant_id,
    amount,
    currency,
    status,
    source_file,
    batch_id,
    loaded_at,
    cleaned_at
FROM {{ source('payflow', 'silver_transactions') }}
