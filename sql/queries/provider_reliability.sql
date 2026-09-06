-- PayFlow — Provider reliability: match rate per provider

USE payflow;

SELECT
    p.provider_name,
    r.reconciliation_status,
    COUNT(*) AS transaction_count,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY p.provider_name),
        2
    ) AS pct_of_provider
FROM warehouse_fact_reconciliation r
JOIN warehouse_dim_provider p
    ON r.provider_key = p.provider_key
GROUP BY p.provider_name, r.reconciliation_status
ORDER BY p.provider_name, transaction_count DESC;
