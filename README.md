# PayFlow — Automated Payment Reconciliation & Billing Data Platform

> **A production-inspired AWS data engineering platform that ingests heterogeneous payment data, performs automated SQL reconciliation, detects data-quality issues, and generates merchant billing analytics.**

---

## TL;DR

PayFlow is a fictional European fintech that processes payments through multiple external providers. This project simulates a real client engagement: building an end-to-end data platform that ingests provider files, reconciles them against internal records, surfaces discrepancies automatically, and produces daily billing analytics.

It is designed specifically to demonstrate the skills expected of a **Junior Data Engineer** at a services company like Accedia: strong SQL, data modeling, AWS fundamentals, data quality discipline, and the ability to translate business requirements into working data pipelines.

---

## Dashboard Preview

![PayFlow Dashboard](docs/assets/dashboard.png)

---

## The Business Problem

> *"We currently receive transaction files from three payment providers. Finance manually compares these files against our internal transaction system every day. This takes approximately 4 hours and errors are difficult to identify."*

PayFlow needs:

1. **Automated ingestion** of heterogeneous provider data (CSV, JSON, API).
2. **Standardization** of different schemas into a single canonical model.
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
                MySQL
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
| **Gold** | Business-ready fact and dimension tables. | MySQL warehouse schema |

---

## Tech Stack

| Area | Tools |
|------|-------|
| **Languages** | SQL, Python |
| **Database** | MySQL 8.0 |
| **Cloud** | AWS S3, AWS Lambda, AWS Glue, Amazon Kinesis |
| **Processing** | Python, PySpark |
| **Data Quality** | Great Expectations (community) / custom validators |
| **Dashboard** | Power BI / Metabase / Streamlit |
| **Data Transformation** | dbt |
| **Orchestration** | Apache Airflow (introduced in later phase) |
| **Testing** | pytest, dbt tests (optional) |
| **Docs** | Markdown ADRs, business requirements |

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

## Reconciliation

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

## Data Warehouse Star Schema

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

Invalid records are moved to the `rejected/` S3 prefix and logged in a quarantine table.

---

## Billing

PayFlow charges merchants:

- **1.5%** of successful transaction volume
- **€0.25** fixed fee per successful transaction

The billing pipeline produces:

```text
merchant
billing_period
successful_transactions
gross_volume
transaction_fees
refunds
net_volume
amount_due
```

---

## Project Structure

```text
payflow-data-platform/
├── README.md
├── docs/
│   ├── business/
│   │   └── business_requirements.md
│   └── architecture-decisions/
│       ├── ADR-001-storage.md
│       ├── ADR-002-processing.md
│       └── ADR-003-data-model.md
├── sql/
│   ├── schema/              # DDL for warehouse tables
│   ├── stored_procedures/   # Reconciliation and billing logic
│   ├── queries/             # Analytical queries
│   ├── reconciliation/      # Reconciliation SQL
│   └── billing/             # Billing SQL
├── src/
│   ├── ingestion/           # File ingestion scripts
│   ├── transformation/      # Standardization and cleaning
│   ├── quality/             # Data quality checks
│   ├── reconciliation/      # Reconciliation runner
│   ├── billing/             # Billing calculator
│   └── dashboard/           # Dashboard helpers
├── data/
│   ├── raw/                 # Provider sample files
│   ├── processed/           # Cleaned outputs
│   ├── rejected/              # Invalid records
│   ├── archive/               # Archived raw files
│   └── sample/                # Seed data
├── notebooks/               # Exploration notebooks
├── tests/                   # Unit and integration tests
├── infra/                   # Terraform / SAM templates
└── requirements.txt
```

---

## How to Run

### 1. Local MySQL

```bash
# Start MySQL (Docker example)
docker run -d --name payflow-mysql \
  -e MYSQL_ROOT_PASSWORD=rootpass \
  -e MYSQL_DATABASE=payflow \
  -e MYSQL_USER=payflow \
  -e MYSQL_PASSWORD=payflow \
  -p 3307:3306 mysql:8.0

# Create tables and seed data (when prompted, enter password: payflow)
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < sql/schema/01_create_database.sql
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < data/sample/seed_data.sql
```

### 2. Local Pipeline

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the full pipeline (ingest → validate → load)
python run_pipeline.py

# Reconcile
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < sql/reconciliation/reconcile_transactions.sql

# Generate billing
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < sql/billing/generate_billing.sql

# Run dbt models and tests
cd payflow_dbt
dbt run
dbt test

# Run Python tests
pytest tests/ -v
```

For large-scale testing, generate 10,000+ synthetic transactions and rerun the pipeline:

```bash
python src/utils/generate_data.py
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < data/generated/seed_data.sql
python run_pipeline.py
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < sql/reconciliation/reconcile_transactions.sql
```

### 3. Dashboard

Open the dashboard configuration in `src/dashboard/` or connect Power BI / Metabase to the MySQL warehouse schema.

---

## Key Skills Demonstrated

| Skill | Where It Appears |
|-------|------------------|
| **SQL (CTEs, joins, window functions, CASE)** | `sql/reconciliation/`, `sql/billing/` |
| **Data modeling (OLTP vs OLAP, Star Schema)** | `sql/schema/`, ADR-003 |
| **ETL / ELT pipelines** | `src/ingestion/`, `src/transformation/` |
| **dbt transformations** | `payflow_dbt/models/` |
| **Data quality** | `src/quality/`, dbt tests, rejected-record handling |
| **Testing** | `pytest` in `tests/` |
| **CI/CD** | GitHub Actions `.github/workflows/ci.yml` |
| **AWS fundamentals** | `infra/`, S3/Lambda/Glue/Kinesis design |
| **Reconciliation logic** | `sql/reconciliation/reconcile_transactions.sql` |
| **Financial / billing logic** | `sql/billing/generate_billing.sql` |
| **Business requirements translation** | `docs/business/business_requirements.md` |
| **Documentation / consulting mindset** | README, ADRs, project plan |

---

## Project Status

This project is being built iteratively over 3 weeks. See [`docs/project_plan.md`](docs/project_plan.md) for the detailed build schedule.

---

## About the Author

This project was designed to simulate a real client engagement for a Junior Data Engineer role. The focus is not on pretending to have years of production experience, but on demonstrating the ability to approach a real business problem with the right tools, structure, and communication.
