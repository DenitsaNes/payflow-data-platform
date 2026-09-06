-- PayFlow — Merchant Billing Calculation (MySQL 8.0+)
--
-- Calculates monthly billing for each merchant based on successful transactions.
-- Fee structure: 1.5% variable fee + EUR 0.25 fixed fee per successful transaction.
-- Refunds reduce the billable volume.

USE payflow;

TRUNCATE TABLE warehouse_fact_billing;

INSERT INTO warehouse_fact_billing (
    merchant_key,
    billing_period,
    successful_transactions,
    gross_volume,
    refunds_volume,
    net_volume,
    variable_fees,
    fixed_fees,
    total_fees,
    amount_due
)
WITH merchant_fees AS (
    SELECT
        merchant_key,
        COALESCE(fee_variable_pct, 0.0150) AS fee_variable_pct,
        COALESCE(fee_fixed_amount, 0.25) AS fee_fixed_amount
    FROM warehouse_dim_merchant
),

transaction_summary AS (
    SELECT
        ft.merchant_key,
        DATE_FORMAT(ft.transaction_timestamp, '%Y-%m') AS billing_period,
        SUM(CASE WHEN ds.status_category = 'completed' THEN 1 ELSE 0 END) AS successful_transactions,
        COALESCE(SUM(CASE WHEN ds.status_category = 'completed' THEN ft.amount ELSE 0 END), 0) AS gross_volume,
        COALESCE(SUM(CASE WHEN ds.status_category = 'refund' THEN ft.amount ELSE 0 END), 0) AS refunds_volume
    FROM warehouse_fact_transaction ft
    JOIN warehouse_dim_transaction_status ds
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
        + (ts.successful_transactions * mf.fee_fixed_amount) AS amount_due
FROM transaction_summary ts
JOIN merchant_fees mf
    ON ts.merchant_key = mf.merchant_key;

-- Billing report view
CREATE OR REPLACE VIEW warehouse_v_billing_report AS
SELECT
    m.merchant_id,
    m.merchant_name,
    fb.billing_period,
    fb.successful_transactions,
    fb.gross_volume,
    fb.refunds_volume,
    fb.net_volume,
    fb.variable_fees,
    fb.fixed_fees,
    fb.total_fees,
    fb.amount_due,
    fb.calculated_at
FROM warehouse_fact_billing fb
JOIN warehouse_dim_merchant m
    ON fb.merchant_key = m.merchant_key
ORDER BY
    fb.billing_period DESC,
    fb.amount_due DESC;
