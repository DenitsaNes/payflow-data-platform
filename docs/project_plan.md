# PayFlow — 3-Week Build Plan

> Goal: Build a complete, portfolio-ready data engineering project that simulates an Accedia-style client engagement for a Junior Data Engineer role.

---

## Week 1 — Foundation & Data Ingestion

**Theme:** Get the data in, clean it, and model it correctly.

### Day 1 — Project Setup & Requirements

- [ ] Create repository structure and README.
- [ ] Write `business_requirements.md`.
- [ ] Define the fictional client (PayFlow), stakeholders, and success criteria.
- [ ] Document expected data providers and formats.

**Deliverable:** Repo scaffold + business requirements document.

### Day 2 — Architecture & ADRs

- [ ] Draw the end-to-end architecture diagram.
- [ ] Write ADR-001: Raw storage in S3.
- [ ] Write ADR-002: Batch processing with Python / PySpark.
- [ ] Write ADR-003: Star-schema data warehouse in PostgreSQL.

**Deliverable:** Three ADRs and architecture diagram in README.

### Day 3 — PostgreSQL Schema (Bronze / Silver)

- [ ] Create `staging` schema for cleaned provider data.
- [ ] Create `warehouse` schema with star-schema tables.
- [ ] Build dimension tables: `dim_merchant`, `dim_provider`, `dim_currency`, `dim_date`, `dim_transaction_status`.
- [ ] Build fact table: `fact_transaction`.
- [ ] Add indexes, constraints, and primary/foreign keys.

**Deliverable:** `sql/schema/01_create_database.sql` runs successfully.

### Day 4 — Sample Data Generation

- [ ] Generate 3 provider datasets (CSV, JSON, CSV-variant).
- [ ] Introduce intentional problems:
  - Duplicates
  - Missing transactions
  - Amount mismatches
  - Status mismatches
  - Currency mismatches
  - Malformed amounts
  - Late-arriving records
- [ ] Generate internal transaction reference dataset.

**Deliverable:** Realistic sample files under `data/raw/` and `data/sample/`.

### Day 5 — Ingestion & Standardization

- [ ] Build Python ingestion script (`src/ingestion/ingest_providers.py`).
- [ ] Normalize all three provider schemas to canonical form.
- [ ] Handle missing/unknown columns gracefully.
- [ ] Persist cleaned data as Parquet/CSV in `data/processed/`.

**Deliverable:** Running ingestion pipeline from raw → processed.

### Day 6 — Data Quality Layer

- [ ] Implement validation rules:
  - `transaction_id` not null and unique
  - `amount` numeric and >= 0
  - `currency` in allowed set
  - `timestamp` valid and not future-dated
  - `merchant_id` exists in `dim_merchant`
  - `status` valid
- [ ] Route invalid records to `data/rejected/`.
- [ ] Generate a data-quality report.

**Deliverable:** `src/quality/validate_records.py` + sample quality report.

### Day 7 — Load to PostgreSQL

- [ ] Build `src/transformation/load_to_postgres.py`.
- [ ] Insert clean records into `staging.transactions`.
- [ ] Populate dimensions from seed data.
- [ ] Populate `fact_transaction` from staging.
- [ ] Test end-to-end with sample data.

**Deliverable:** Database populated with clean transaction facts.

**Week 1 Checkpoint:**

- Can ingest heterogeneous data.
- Can validate and reject bad records.
- Has a working star-schema warehouse with transactions loaded.

---

## Week 2 — Reconciliation, Billing & AWS

**Theme:** Build the business logic and introduce AWS services.

### Day 8 — Reconciliation Logic Design

- [ ] Create `internal_transactions` and `gateway_transactions` tables.
- [ ] Design reconciliation output schema.
- [ ] Define statuses: `MATCH`, `AMOUNT_MISMATCH`, `STATUS_MISMATCH`, `MISSING_FROM_GATEWAY`, `MISSING_INTERNAL`.

**Deliverable:** Reconciliation schema and rule definitions.

### Day 9 — Reconciliation SQL

- [ ] Write CTE-based reconciliation query:
  - Deduplicate gateway records with `ROW_NUMBER()`.
  - `LEFT JOIN` internal to gateway.
  - Use `CASE` to classify reconciliation status.
- [ ] Create stored procedure `sp_reconcile_transactions()`.
- [ ] Persist results to `fact_reconciliation`.

**Deliverable:** `sql/reconciliation/reconcile_transactions.sql`.

### Day 10 — Reconciliation Reporting

- [ ] Build summary query: match rate, mismatch breakdown by provider/merchant/date.
- [ ] Create view `v_reconciliation_summary`.
- [ ] Generate sample reconciliation report.

**Deliverable:** Reconciliation report and analytical views.

### Day 11 — Billing Logic

- [ ] Define fee structure: 1.5% + €0.25 per successful transaction.
- [ ] Handle refunds and chargebacks.
- [ ] Write billing aggregation SQL with CTEs.
- [ ] Create stored procedure `sp_generate_billing()`.
- [ ] Persist results to `fact_billing`.

**Deliverable:** `sql/billing/generate_billing.sql`.

### Day 12 — AWS S3 & Lambda

- [ ] Set up AWS account / Free Tier.
- [ ] Create S3 bucket `payflow-data-{alias}`.
- [ ] Define prefixes: `raw/`, `processed/`, `rejected/`, `archive/`.
- [ ] Write Lambda function to detect new files, validate metadata, and move them.
- [ ] Test Lambda with sample uploads.

**Deliverable:** Files flowing through S3 + Lambda locally or in AWS.

### Day 13 — AWS Glue ETL

- [ ] Create Glue Data Catalog tables for raw provider data.
- [ ] Write a Glue job (PySpark) to standardize and clean provider files.
- [ ] Output Parquet to `processed/` prefix.
- [ ] Document how Glue fits into the bronze → silver flow.

**Deliverable:** Glue job script in `infra/glue/`.

### Day 14 — Kinesis Streaming (Stretch)

- [ ] Design a simple real-time path: simulated payment API → Kinesis → Lambda → S3.
- [ ] Create a Python simulator that sends transactions to a Kinesis stream.
- [ ] Write Lambda consumer to append streaming records to S3.
- [ ] Keep batch as the primary path; streaming is documented as future-ready.

**Deliverable:** Kinesis simulator + consumer documented in README.

**Week 2 Checkpoint:**

- Reconciliation and billing SQL procedures run end-to-end.
- AWS S3 + Lambda ingestion path is functional.
- Glue job demonstrates bronze → silver transformation.

---

## Week 3 — Dashboard, Testing, Polish & Portfolio

**Theme:** Make it presentable, reliable, and interview-ready.

### Day 15 — Dashboard Page 1 — Executive Overview

- [ ] Connect dashboard tool to PostgreSQL warehouse.
- [ ] Build KPIs:
  - Total processing volume
  - Total transactions
  - Success rate
  - Reconciliation rate
- [ ] Add daily volume trend chart.

**Deliverable:** Executive dashboard page.

### Day 16 — Dashboard Page 2 — Reconciliation

- [ ] Build reconciliation breakdown:
  - Match vs mismatch counts
  - Discrepancies by provider
  - Discrepancies by merchant
- [ ] Add filters: provider, merchant, date, currency.

**Deliverable:** Reconciliation dashboard page.

### Day 17 — Dashboard Page 3 — Billing

- [ ] Build merchant billing table:
  - Merchant
  - Billing period
  - Gross volume
  - Successful transactions
  - Transaction fees
  - Refunds
  - Net volume
  - Amount due
- [ ] Add chart of top merchants by volume.

**Deliverable:** Billing dashboard page.

### Day 18 — Testing

- [ ] Write pytest tests for ingestion and standardization.
- [ ] Write SQL tests for reconciliation edge cases.
- [ ] Verify duplicate handling.
- [ ] Verify mismatch classification.
- [ ] Run full pipeline on sample data and assert outputs.

**Deliverable:** Passing test suite under `tests/`.

### Day 19 — Documentation Polish

- [ ] Finalize README with architecture, run instructions, and skills map.
- [ ] Add data dictionary (`docs/data_dictionary.md`).
- [ ] Add runbook for common issues (`docs/runbook.md`).
- [ ] Add `requirements.txt` and `docker-compose.yml` for one-command startup.

**Deliverable:** Clean, complete documentation.

### Day 20 — Portfolio Packaging

- [ ] Record a short Loom/video walkthrough (optional but recommended).
- [ ] Create a concise project card for LinkedIn / resume.
- [ ] Publish the repository to GitHub.
- [ ] Add a one-page project summary PDF.

**Deliverable:** Public repo + portfolio assets.

### Day 21 — Buffer & Interview Prep

- [ ] Rehearse explaining the project in 10 minutes.
- [ ] Prepare answers for common questions:
  - Why this architecture?
  - How did you handle duplicates?
  - How would you scale this?
  - What would you do differently in production?
- [ ] Fix any last bugs.
- [ ] Celebrate finishing a genuinely hard project.

**Deliverable:** Confidence and a polished portfolio piece.

---

## Milestones

| Week | Milestone |
|------|-----------|
| 1 | Ingestion → validation → star-schema warehouse is working locally. |
| 2 | Reconciliation + billing SQL procedures are functional; AWS S3/Lambda/Glue in place. |
| 3 | Dashboard live; tests passing; repo public and documented. |

---

## Daily Time Budget

- **Weekdays:** 3–4 hours per day.
- **Weekends:** 5–6 hours per day.
- **Total:** ~60–70 hours over 3 weeks.

---

## Stretch Goals

If time allows, add these to make the project even stronger:

- [ ] Orchestrate the pipeline with Apache Airflow.
- [ ] Add incremental loads with `loaded_at` / `etl_timestamp` tracking.
- [ ] Add Slowly Changing Dimension Type 2 for `dim_merchant`.
- [ ] Add idempotency checks so re-running the pipeline does not duplicate data.
- [ ] Add Terraform / SAM templates for AWS infrastructure as code.
- [ ] Add CI/CD with GitHub Actions running tests on every commit.
- [ ] Add dbt models and tests for the warehouse layer.

---

## Success Criteria

At the end of 3 weeks, this project should prove that you can:

1. Translate a business requirement into a technical design.
2. Build a real ETL pipeline with SQL and Python.
3. Apply data warehouse modeling (star schema).
4. Implement reconciliation and financial logic in SQL.
5. Use AWS services for ingestion and processing.
6. Validate data quality and handle bad records.
7. Present results through a dashboard.
8. Document decisions and communicate clearly in English.

This is exactly the profile Accedia is looking for in a Junior Data Engineer.
