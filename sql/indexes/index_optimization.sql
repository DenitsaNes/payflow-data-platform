-- PayFlow — Index optimization demonstration

USE payflow;

-- Query we want to optimize: successful transactions for a specific merchant
EXPLAIN
SELECT provider, COUNT(*) AS cnt
FROM silver_transactions
WHERE merchant_id = 'M001'
  AND status = 'SUCCESS'
GROUP BY provider;

-- Add a covering index for merchant + status + provider lookups
CREATE INDEX idx_silver_merchant_status_provider
ON silver_transactions(merchant_id, status, provider);

-- Re-run EXPLAIN and notice the change (typically from ALL -> ref/range)
EXPLAIN
SELECT provider, COUNT(*) AS cnt
FROM silver_transactions
WHERE merchant_id = 'M001'
  AND status = 'SUCCESS'
GROUP BY provider;
