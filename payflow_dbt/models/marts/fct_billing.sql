{{ config(materialized='table') }}

WITH merchant_fees AS (
    SELECT
        merchant_key,
        COALESCE(fee_variable_pct, 0.0150) AS fee_variable_pct,
        COALESCE(fee_fixed_amount, 0.25) AS fee_fixed_amount
    FROM {{ source('payflow', 'warehouse_dim_merchant') }}
),

transaction_summary AS (
    SELECT
        ft.merchant_key,
        DATE_FORMAT(ft.transaction_timestamp, '%Y-%m') AS billing_period,
        SUM(CASE WHEN ds.status_category = 'completed' THEN 1 ELSE 0 END) AS successful_transactions,
        COALESCE(SUM(CASE WHEN ds.status_category = 'completed' THEN ft.amount ELSE 0 END), 0) AS gross_volume,
        COALESCE(SUM(CASE WHEN ds.status_category = 'refund' THEN ft.amount ELSE 0 END), 0) AS refunds_volume
    FROM {{ ref('fct_transactions') }} ft
    JOIN {{ source('payflow', 'warehouse_dim_transaction_status') }} ds
        ON ft.status_key = ds.status_key
    GROUP BY
        ft.merchant_key,
        DATE_FORMAT(ft.transaction_timestamp, '%Y-%m')
)

SELECT
    ts.merchant_key,
    ts.billing_period,
    ts.successful_transactions,
    ts.gross_volume,
    ts.refunds_volume,
    (ts.gross_volume - ts.refunds_volume) AS net_volume,
    ((ts.gross_volume - ts.refunds_volume) * mf.fee_variable_pct) AS variable_fees,
    (ts.successful_transactions * mf.fee_fixed_amount) AS fixed_fees,
    ((ts.gross_volume - ts.refunds_volume) * mf.fee_variable_pct)
        + (ts.successful_transactions * mf.fee_fixed_amount) AS total_fees,
    ((ts.gross_volume - ts.refunds_volume) * mf.fee_variable_pct)
        + (ts.successful_transactions * mf.fee_fixed_amount) AS amount_due,
    CURRENT_TIMESTAMP() AS calculated_at
FROM transaction_summary ts
JOIN merchant_fees mf
    ON ts.merchant_key = mf.merchant_key
