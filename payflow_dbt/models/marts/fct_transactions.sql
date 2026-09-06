{{ config(materialized='table') }}

SELECT
    g.transaction_id,
    g.transaction_timestamp,
    CAST(DATE_FORMAT(DATE(g.transaction_timestamp), '%Y%m%d') AS UNSIGNED) AS date_key,
    m.merchant_key,
    p.provider_key,
    c.currency_key,
    s.status_key,
    g.amount,
    g.source_file,
    CURRENT_TIMESTAMP() AS loaded_at
FROM {{ ref('stg_gateway_transactions') }} g
LEFT JOIN {{ source('payflow', 'warehouse_dim_merchant') }} m
    ON g.merchant_id = m.merchant_id
LEFT JOIN {{ source('payflow', 'warehouse_dim_provider') }} p
    ON g.provider = p.provider_id
LEFT JOIN {{ source('payflow', 'warehouse_dim_currency') }} c
    ON g.currency = c.currency_code
LEFT JOIN {{ source('payflow', 'warehouse_dim_transaction_status') }} s
    ON g.status = s.status_code
