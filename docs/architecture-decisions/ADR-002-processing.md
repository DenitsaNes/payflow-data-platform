# ADR-002: Batch Processing with Python / PySpark, Optional Kinesis for Streaming

## Status

Accepted

## Context

PayFlow receives daily provider files in CSV and JSON formats. The business also wants the ability to ingest near-real-time transactions from a payment API in the future. We need a processing approach that handles current batch needs while leaving room for streaming.

## Decision

Use **batch processing as the primary path** with Python for local development and **AWS Glue with PySpark** for cloud ETL. Add an optional **Amazon Kinesis → Lambda → S3** path for real-time transactions, but keep it separate from the batch reconciliation flow.

```text
Batch:  S3 raw → Glue (PySpark) → PostgreSQL staging
Stream: API → Kinesis → Lambda → S3 raw → batch pipeline
```

## Consequences

### Positive

- Batch is simpler to develop, test, and debug — ideal for an MVP.
- PySpark handles large CSV/JSON files and schema normalization efficiently.
- Kinesis path demonstrates streaming knowledge without blocking the core pipeline.
- Lambda handles lightweight streaming events and writes them to S3 for downstream processing.

### Negative

- Two ingestion paths require separate monitoring.
- Streaming records may arrive slightly later than batch cutoff times, affecting same-day reconciliation.

## Alternatives Considered

| Alternative | Why Not Chosen |
|-------------|----------------|
| Pure streaming architecture | Over-engineered for daily provider files. |
| AWS Step Functions only | Good for orchestration but not for heavy transformation. |
| Only local Python | Does not showcase AWS skills expected for the role. |

## Related Decisions

- ADR-001: Raw storage in S3.
- ADR-003: Star-schema data warehouse.
