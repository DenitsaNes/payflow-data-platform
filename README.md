# PayFlow — Automated Payment Reconciliation & Billing Data Platform

[![PayFlow CI](https://github.com/DenitsaNes/payflow-data-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/DenitsaNes/payflow-data-platform/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?logo=mysql)
![dbt](https://img.shields.io/badge/dbt-1.8-FF694B?logo=dbt)

> **A production-inspired data engineering platform that ingests heterogeneous payment data, reconciles it against internal records, detects data-quality issues, and produces merchant billing analytics.**

---

## 📌 Table of Contents

1. [Why PayFlow?](#why-payflow)
2. [The Business Problem](#the-business-problem)
3. [Architecture](#architecture)
4. [Tech Stack & Rationale](#tech-stack--rationale)
5. [Data Sources](#data-sources)
6. [Reconciliation Logic](#reconciliation-logic)
7. [Data Warehouse](#data-warehouse)
8. [Data Quality](#data-quality)
9. [Dashboard](#dashboard)
10. [Quick Start](#quick-start)
11. [Lessons Learned](#lessons-learned)
12. [Future Enhancements](#future-enhancements)
13. [Contact](#contact)
14. [License](#license)

---

## Why PayFlow?

PayFlow is a fictional European fintech that receives transaction files from multiple payment gateways. Finance currently compares these files manually against internal systems — a **4-hour, error-prone process**.

This project simulates a real client engagement and demonstrates how a Junior Data Engineer would:

- Translate a business problem into a data pipeline.
- Model data for both operational and analytical workloads.
- Build automated reconciliation and financial reporting.
- Enforce data quality and test-driven development.
- Deliver a reproducible, CI/CD-backed solution.

> **Impact:** PayFlow automates a daily 4-hour reconciliation process, flags discrepancies automatically, and produces billing reports that previously required manual spreadsheet work.

---

## The Business Problem

> *“We receive transaction files from three payment providers every day. Finance manually compares them against our internal system. This takes ~4 hours and errors are hard to spot.”*

PayFlow needs:

1. **Automated ingestion** of heterogeneous provider data (CSV, JSON, API).
2. **Standardization** of different schemas into one canonical model.
3. **Reconciliation** between internal transactions and gateway-reported transactions.
4. **Duplicate detection** and malformed-record handling.
5. **Merchant billing calculations** with fee logic.
6. **Historical analytics** via a star-schema data warehouse.
7. **Operational dashboard** for finance and operations teams.

---

## Architecture

```text
                 PAYMENT PROVIDERS
              /        |        \
           CSV       JSON       API
             \         |         /
              \        |        /
                   AWS S3
                     |
          +----------+----------+
          |                     |
       Batch                Streaming
          |                     |
       AWS Glue            AWS Kinesis
          |                     |
          +----------+----------+
                     |
                     ▼
              TRANSFORMATION
                 Python / PySpark
                     |
            Bronze / Silver / Gold
                     |
                     ▼
                MySQL 8.0
                     |
              SQL Procedures
                     |
          +----------+----------+
          |                     |
    Reconciliation          Billing
          |                     |
          +----------+----------+
                     |
                     ▼
                Gold Layer
                     |
                     ▼
              BI Dashboard
```

### Data Layers

| Layer | Purpose | Storage |
|-------|---------|---------|
| **Bronze** | Raw provider files exactly as received. Immutable. | S3 `raw/` |
| **Silver** | Cleaned, standardized, deduplicated transactions. | S3 `processed/`, MySQL staging |
| **Gold** | Business-ready fact and dimension tables. | MySQL `warehouse` schema |

---

## Tech Stack & Rationale

| Area | Tools | Why |
|------|-------|-----|
| **Languages** | SQL, Python | Core data engineering languages. |
| **Database** | MySQL 8.0 | Widely used in mid-market companies; good practice for schema design and stored procedures. |
| **Cloud (designed)** | AWS S3, Lambda, Glue, Kinesis | Event-driven ingestion, batch processing, and streaming in one architecture. |
| **Processing** | Python, pandas, PySpark | pandas for local ETL; PySpark designed for scale. |
| **Data Quality** | Custom validators + dbt tests | Lightweight but extensible; easy to swap for Great Expectations later. |
| **Transformation** | dbt | Industry-standard analytics engineering tool; tests and documentation out of the box. |
| **Orchestration** | Apache Airflow (designed) | Planned for scheduling and monitoring. |
| **Dashboard** | Streamlit | Quick, Python-native dashboard for portfolio demos. |
| **Testing** | pytest, GitHub Actions | Automated tests on every commit. |
| **Docs** | Markdown ADRs, business requirements, lesson plans | Consulting-style documentation. |

---

## Data Sources

Three external providers send data in different structures.

### Provider A — CSV

```csv
transaction_id,merchant_id,amount,currency,status,timestamp
TX001,M001,125.50,EUR,COMPLETED,2026-09-06 10:32:11
```

### Provider B — JSON

```json
{
  "payment_id": "TX001",
  "merchant": "M001",
  "value": 125.50,
  "currency": "EUR",
  "payment_status": "SUCCESS",
  "created_at": "2026-09-06T10:32:11Z"
}
```

### Provider C — CSV with different names

```csv
transactionId,merchant,amount,currency,result,date
```

### Canonical Target Schema

```text
transaction_id
transaction_timestamp
provider
merchant_id
amount
currency
status
loaded_at
source_file
```

---

## Reconciliation Logic

The centerpiece of the project is SQL-based reconciliation between internal transactions and gateway-reported transactions.

| Transaction | Internal | Gateway | Result |
|-------------|----------|---------|--------|
| TX001 | €100 | €100 | `MATCH` |
| TX002 | €250 | €250 | `MATCH` |
| TX003 | €120 | €125 | `AMOUNT_MISMATCH` |
| TX004 | €80 | — | `MISSING_FROM_GATEWAY` |
| TX005 | — | €90 | `MISSING_INTERNAL` |
| TX006 | SUCCESS | FAILED | `STATUS_MISMATCH` |

See [`sql/reconciliation/reconcile_transactions.sql`](sql/reconciliation/reconcile_transactions.sql) for the CTE-driven implementation.

---

## Data Warehouse

Star schema for analytics:

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

### Fact Tables

- `fact_transaction`
- `fact_reconciliation`
- `fact_billing`

### Dimension Tables

- `dim_merchant`
- `dim_provider`
- `dim_currency`
- `dim_date`
- `dim_transaction_status`

---

## Data Quality

Incoming records are validated before processing:

- `transaction_id` is not null and unique
- `amount` is numeric and non-negative
- `currency` is in the allowed set
- `timestamp` is valid and not in the future
- `merchant_id` exists in `dim_merchant`
- `status` is a known value
- Duplicate detection across files

Invalid records are moved to the `rejected/` prefix and logged in a quarantine table.

---

## Dashboard

A Streamlit dashboard connects to the warehouse and shows:

- Executive KPIs (total transactions, match rate, discrepancies)
- Reconciliation breakdown chart
- Merchant billing table
- Filterable discrepancy details

![PayFlow Dashboard](docs/assets/dashboard.png)

Run it locally:

```bash
streamlit run src/dashboard/dashboard.py
```

---

## Quick Start

### 1. Start MySQL

```bash
docker compose up -d
```

MySQL is exposed on host port `3307` to avoid conflicts with any native MySQL install.

### 2. Create schema and seed data

```bash
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < sql/schema/01_create_database.sql
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < data/sample/seed_data.sql
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < data/sample/seed_gateway_transactions.sql
```

Password: `payflow`

### 3. Install Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Run the pipeline

```bash
python run_pipeline.py
```

### 5. Reconcile and bill

```bash
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < sql/reconciliation/reconcile_transactions.sql
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < sql/billing/generate_billing.sql
```

### 6. Run dbt

```bash
cd payflow_dbt
dbt run
dbt test
```

### 7. Run tests

```bash
pytest tests/ -v
```

---

## Lessons Learned

1. **MySQL CTE syntax differs from PostgreSQL.** Reconciliation and billing SQL had to be rewritten from `WITH ... INSERT` to `INSERT ... WITH ... SELECT` for MySQL compatibility.
2. **Port mapping matters.** Mapping the Docker MySQL container to host port `3307` prevented collisions with macOS native MySQL and taught me to always isolate dev services.
3. **Tests need import paths.** Adding `tests/conftest.py` to inject the project root into `sys.path` was the cleanest way to make `pytest` resolve the `src` package without a complex install.
4. **Data quality is a feature, not an afterthought.** Building rejected-record handling and validation rules from the start made the pipeline robust against malformed provider files.
5. **dbt changes how you think about analytics code.** Separating staging, marts, and tests made the warehouse much easier to explain and maintain.

---

## Future Enhancements

- [ ] **Apache Airflow** — schedule ingestion, reconciliation, and billing daily.
- [ ] **Terraform / AWS SAM** — provision S3, Glue, Kinesis, and RDS MySQL.
- [ ] **Great Expectations** — richer data quality suites and profiling.
- [ ] **Incremental loads** — only process new/changed records in the warehouse.
- [ ] **SCD Type 2** — track historical changes to merchant and provider dimensions.
- [ ] **Streaming ingestion** — consume provider API events via Kinesis.
- [ ] **Cost monitoring** — track pipeline run cost and SLA metrics.

---

## Contact

Built by **Denitsa Nesheva** — aspiring Junior Data Engineer.

- GitHub: [@DenitsaNes](https://github.com/DenitsaNes)
- LinkedIn: *(add your link)*
- Email: *(add your email)*

If you're hiring for a junior data engineering role, I'd love to talk.

---

## License

This project is released under the [MIT License](LICENSE).
