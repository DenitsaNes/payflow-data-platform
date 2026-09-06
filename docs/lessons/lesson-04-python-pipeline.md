# Lesson 4: Build the Python Ingestion Pipeline

> In this lesson, we replace the manual SQL seed files with a real Python ETL pipeline.

---

## 1. What we will build

We will create three Python scripts and one runner:

| Script | Purpose |
|--------|---------|
| `src/ingestion/ingest_providers.py` | Read CSV/JSON, normalize schemas |
| `src/quality/validate_records.py` | Validate data, split valid/rejected |
| `src/transformation/load_to_mysql.py` | Load valid records into MySQL |
| `run_pipeline.py` | Run all three steps end-to-end |

---

## 2. Install Python dependencies

Make sure you are in the project folder and have a virtual environment:

```bash
cd payflow-data-platform
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

This installs pandas, SQLAlchemy, PyMySQL, and other libraries.

---

## 3. Understand normalization in Python

Open the ingestion script:

```bash
open src/ingestion/ingest_providers.py
```

The key idea:

```python
COLUMN_MAP = {
    "provider_a": {
        "transaction_id": "transaction_id",
        "merchant_id": "merchant_id",
        "amount": "amount",
        ...
    },
    "provider_b": {
        "payment_id": "transaction_id",
        "merchant": "merchant_id",
        "value": "amount",
        ...
    },
    ...
}
```

Each provider has its own column names. We map them to one common set of names.

Then we normalize statuses:

```python
STATUS_NORMALIZATION = {
    "COMPLETED": "SUCCESS",
    "completed": "SUCCESS",
    "SUCCESS": "SUCCESS",
    ...
}
```

This is the same canonical-status idea we discussed.

---

## 4. Run the pipeline

First, make sure your MySQL container is running:

```bash
docker ps
```

You should see `payflow-mysql`.

Then run the full pipeline:

```bash
python run_pipeline.py
```

You should see output like:

```text
============================================================
PayFlow Local Pipeline
============================================================

[1/3] Ingesting provider files...
Processing data/raw/provider_a/provider_a_2026_09_06.csv ...
...
Wrote 34 records to data/processed/combined_transactions.parquet

[2/3] Validating records...
Read 34 records from data/processed/combined_transactions.parquet
Wrote 32 valid records to data/processed/valid_transactions.parquet
Wrote 2 rejected records to data/rejected/rejected_transactions.parquet

[3/3] Loading into MySQL...
Done. Loaded 32 records into reconciliation_gateway_transactions.
```

---

## 5. Check what was loaded

Connect to MySQL:

```bash
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow
```

```sql
SELECT provider, COUNT(*) FROM reconciliation_gateway_transactions GROUP BY provider;
SELECT * FROM reconciliation_gateway_transactions LIMIT 10;
```

Notice:

- All three providers are now in one table.
- All statuses are normalized to `SUCCESS`, `FAILED`, `REFUNDED`, or `PENDING`.
- Column names are the same for every provider.

---

## 6. Run reconciliation again

Now that the gateway table was loaded by Python, run the reconciliation SQL again:

```bash
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < sql/reconciliation/reconcile_transactions.sql
```

Check the results:

```bash
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow
```

```sql
SELECT * FROM warehouse_v_reconciliation_summary;
EXIT;
```

---

## 7. Look at rejected records

The validation script put bad records into `data/rejected/rejected_transactions.parquet`.

You can inspect them with Python:

```bash
python - <<'PY'
import pandas as pd
rejected = pd.read_parquet("data/rejected/rejected_transactions.parquet")
print(rejected)
PY
```

You should see the malformed amount `"one hundred"` and the invalid currency `XYZ` records.

---

## 8. What you learned

| Concept | What it means |
|---------|---------------|
| **ETL** | Extract, Transform, Load |
| **Schema normalization** | Convert different formats into one common format |
| **Canonical values** | Use one standard set of values (statuses, currencies) |
| **Data validation** | Check records and reject bad ones |
| **Batch inserts** | Load many rows efficiently |

This is the core of data engineering.

---

## 9. Your homework

1. Run `python run_pipeline.py`.
2. Verify the records in MySQL.
3. Run reconciliation and check the summary.
4. Look at the rejected records.
5. Try changing one of the validation rules (for example, add a maximum amount check).

---

## 10. What is next?

In **Lesson 5**, we will:

- Run the billing calculation.
- Build a dashboard with the results.
- Polish the project for GitHub.
