-- PayFlow — Top 10 merchants by successful transaction volume

USE payflow;

SELECT
    m.merchant_id,
    m.merchant_name,
    COUNT(*) AS successful_tx_count,
    ROUND(SUM(t.amount), 2) AS total_volume,
    ROW_NUMBER() OVER (ORDER BY SUM(t.amount) DESC) AS volume_rank
FROM silver_transactions t
JOIN warehouse_dim_merchant m
    ON t.merchant_id = m.merchant_id
JOIN warehouse_dim_transaction_status s
    ON t.status = s.status_code
WHERE s.status_category = 'completed'
GROUP BY m.merchant_id, m.merchant_name
ORDER BY total_volume DESC
LIMIT 10;
