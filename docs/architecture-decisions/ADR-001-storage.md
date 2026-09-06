# ADR-001: Store Raw Provider Files in S3 Before Transformation

## Status

Accepted

## Context

PayFlow receives transaction files from multiple external payment providers. These files are the only source of truth for what each provider reported. If transformation logic changes, or if a data-quality dispute arises, we need to be able to reprocess the original files.

We must decide where and how to store these raw files.

## Decision

Store every provider file exactly as received in Amazon S3 under a partitioned prefix before any transformation occurs.

```text
s3://payflow-data/raw/
    provider=provider_a/year=2026/month=09/day=06/
    provider=provider_b/year=2026/month=09/day=06/
    provider=provider_c/year=2026/month=09/day=06/
```

## Consequences

### Positive

- **Auditability:** Finance and operations can always retrieve the original provider file.
- **Reprocessability:** If transformation logic changes, we can re-run the pipeline from bronze.
- **Durability:** S3 provides durable, low-cost object storage suitable for retention requirements.
- **Decoupling:** Ingestion, transformation, and analytics can evolve independently.

### Negative

- Additional storage cost (mitigated by S3 lifecycle policies moving old data to cheaper tiers).
- Slightly longer initial pipeline because files are copied before processing.

## Alternatives Considered

| Alternative | Why Not Chosen |
|-------------|----------------|
| Process files in-place from provider SFTP | Loses audit trail if provider deletes or modifies files. |
| Store only transformed data | Cannot reprocess or investigate upstream data-quality issues. |

## Related Decisions

- ADR-002: Processing strategy.
