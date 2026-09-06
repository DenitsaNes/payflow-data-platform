-- PayFlow — Breakdown of rejected records by reason and provider

USE payflow;

SELECT
    COALESCE(provider, 'UNKNOWN') AS provider,
    rejection_reason,
    COUNT(*) AS rejected_count
FROM silver_rejected_transactions
GROUP BY provider, rejection_reason
ORDER BY rejected_count DESC;
