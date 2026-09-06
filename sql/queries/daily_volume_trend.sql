-- PayFlow — Daily volume trend with running total and 7-day moving average

USE payflow;

WITH daily AS (
    SELECT
        DATE(transaction_timestamp) AS txn_date,
        COUNT(*) AS tx_count,
        SUM(amount) AS daily_volume
    FROM silver_transactions
    GROUP BY DATE(transaction_timestamp)
)
SELECT
    txn_date,
    tx_count,
    ROUND(daily_volume, 2) AS daily_volume,
    ROUND(SUM(daily_volume) OVER (ORDER BY txn_date), 2) AS running_volume,
    ROUND(AVG(tx_count) OVER (
        ORDER BY txn_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2) AS avg_7d_tx_count
FROM daily
ORDER BY txn_date;
