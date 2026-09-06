{{ config(materialized='view') }}

SELECT
    bronze_id,
    file_id,
    transaction_id,
    transaction_timestamp,
    provider,
    source_system,
    merchant_id,
    amount,
    currency,
    status,
    source_file,
    batch_id,
    loaded_at,
    raw_record
FROM {{ source('payflow', 'bronze_provider_transactions') }}
