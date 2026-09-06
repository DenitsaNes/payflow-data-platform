-- PayFlow — Late arrival analysis: gap between internal and gateway timestamps

USE payflow;

SELECT
    i.transaction_id,
    i.merchant_id,
    i.transaction_timestamp AS internal_timestamp,
    g.transaction_timestamp AS gateway_timestamp,
    TIMESTAMPDIFF(MINUTE, i.transaction_timestamp, g.transaction_timestamp) AS lag_minutes
FROM reconciliation_internal_transactions i
JOIN silver_transactions g
    ON i.transaction_id = g.transaction_id
WHERE g.transaction_timestamp > i.transaction_timestamp
ORDER BY lag_minutes DESC
LIMIT 20;
