# ADR-004: Bronze / Silver Layer Split and Idempotent Pipeline

## Status

Accepted

## Context

PayFlow started with a simple Python pipeline that read provider files, normalized them, validated them, and loaded the results directly into a MySQL table used for reconciliation. This worked for the MVP, but it had several gaps that would be red flags in a real data engineering interview:

- Raw provider data was transformed before being stored, so we lost the original values.
- Rejected records were written to local Parquet files, not to a database quarantine table.
- Re-running the pipeline on the same files would re-insert records because there was no processed-file log.
- The distinction between Bronze (raw), Silver (cleaned), and Gold (business-ready) data was implicit at best.

## Decision

Introduce explicit Bronze and Silver layers and make the pipeline idempotent:

1. **Bronze layer** (`bronze_raw_provider_files`, `bronze_provider_transactions`)
   - Stores raw provider files with metadata (`source_file`, `provider`, `batch_id`, `loaded_at`).
   - Each raw record is stored as JSON in `raw_record` so the original data is never lost.

2. **Silver layer** (`silver_transactions`, `silver_rejected_transactions`)
   - Reads from Bronze.
   - Normalizes status and timestamps.
   - Validates records using clear rejection reasons.
   - Deduplicates records by `(transaction_id, provider)`.
   - Upserts valid records into `silver_transactions`.
   - Stores rejected records in `silver_rejected_transactions` with a reason and the raw JSON.

3. **Idempotency** (`pipeline_processed_files`)
   - Tracks every processed file by `(source_file, provider, batch_id)`.
   - Re-running the pipeline on the same files skips already-successful files unless `--force` is passed.
   - Silver upserts use `ON DUPLICATE KEY UPDATE` so duplicate keys are updated instead of inserted twice.

## Consequences

**Positive:**

- We can replay the pipeline from Bronze if normalization logic changes.
- Bad records are visible in SQL, not hidden in Parquet files.
- Re-running the pipeline is safe and predictable.
- The architecture maps cleanly to the medallion pattern used in modern data lakes and warehouses.

**Negative:**

- More tables to maintain.
- Slightly more complex pipeline orchestration.
- The pipeline now requires MySQL to be available for the Bronze/Silver steps.

## Alternatives Considered

- **Keep file-based rejected records**: simpler, but harder to query and not production-like.
- **Use MERGE instead of INSERT ... ON DUPLICATE KEY UPDATE**: MySQL 8.0 supports `INSERT ... ON DUPLICATE KEY UPDATE`, which is simpler and widely used; `MERGE` is not standard MySQL syntax.
- **Track idempotency by file hash instead of file name**: more robust against renames, but overkill for a portfolio project; file name + batch_id is sufficient here.

## Related Files

- `sql/schema/01_create_database.sql`
- `src/transformation/load_bronze.py`
- `src/transformation/silver_cleaner.py`
- `run_pipeline.py`
