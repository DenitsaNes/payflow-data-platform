-- PayFlow — Detect duplicate provider records kept vs dropped

USE payflow;

WITH ranked AS (
    SELECT
        transaction_id,
        provider,
        transaction_timestamp,
        amount,
        ROW_NUMBER() OVER (
            PARTITION BY transaction_id, provider
            ORDER BY transaction_timestamp DESC, loaded_at DESC
        ) AS rn
    FROM silver_transactions
)
SELECT
    transaction_id,
    provider,
    COUNT(*) AS duplicate_count,
    SUM(CASE WHEN rn = 1 THEN 1 ELSE 0 END) AS kept_records,
    SUM(CASE WHEN rn > 1 THEN 1 ELSE 0 END) AS dropped_records
FROM ranked
GROUP BY transaction_id, provider
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC
LIMIT 20;
