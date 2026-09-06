# ADR-003: Use a Star-Schema Data Warehouse in PostgreSQL

## Status

Accepted

## Context

PayFlow needs to analyze transactions, reconciliation results, and billing across multiple dimensions: merchant, provider, currency, date, and status. A transactional OLTP schema optimized for row-by-row inserts is not suitable for analytical queries.

## Decision

Implement a **star-schema data warehouse** in PostgreSQL under a dedicated `warehouse` schema.

```text
                       dim_date
                          |
                          ▼
dim_merchant ───── fact_transaction ───── dim_provider
                          |
                          ▼
                     dim_currency
                          |
                          ▼
                   fact_reconciliation
                          |
                          ▼
                    fact_billing
```

## Fact Tables

- `fact_transaction` — one row per cleaned transaction.
- `fact_reconciliation` — one row per reconciliation comparison.
- `fact_billing` — one row per merchant per billing period.

## Dimension Tables

- `dim_merchant`
- `dim_provider`
- `dim_currency`
- `dim_date`
- `dim_transaction_status`

## Consequences

### Positive

- Simplifies analytical queries and dashboard development.
- Demonstrates understanding of OLTP vs OLAP.
- Makes aggregation by merchant, provider, currency, and date efficient.
- Easy for interviewers to understand and discuss.

### Negative

- Requires ETL to maintain dimensions before loading facts.
- PostgreSQL is not a dedicated OLAP database; very large volumes may eventually require Redshift/BigQuery/Snowflake.

## Alternatives Considered

| Alternative | Why Not Chosen |
|-------------|----------------|
| Normalized OLTP schema | Poor performance for analytical aggregations. |
| Snowflake schema | More complex; star schema is sufficient for this scale. |
| Dedicated cloud warehouse (Redshift/Snowflake) | Higher cost and complexity than needed for a portfolio project. |

## Related Decisions

- ADR-001: Raw storage in S3.
- ADR-002: Processing strategy.
