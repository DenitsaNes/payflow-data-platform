# Lesson 5: Billing Calculation and Dashboard

> In this lesson, we calculate merchant billing and build a simple dashboard to visualize the results.

---

## 1. Populating the star schema

So far, our pipeline has loaded records into `reconciliation_gateway_transactions`. For billing and reporting, we need the data in the star-schema fact table: `warehouse_fact_transaction`.

The pipeline now does this automatically in step 4. If you already ran it, the fact table is populated.

If you want to run it manually:

```bash
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < sql/transformation/populate_fact_transaction.sql
```

---

## 2. Run reconciliation

If you have not run it yet:

```bash
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < sql/reconciliation/reconcile_transactions.sql
```

Password: `payflow`

---

## 3. Calculate billing

PayFlow charges merchants:

- **1.5%** of successful transaction volume
- **€0.25** per successful transaction

Run the billing SQL:

```bash
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < sql/billing/generate_billing.sql
```

Password: `payflow`

Check the results:

```bash
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow
```

```sql
SELECT * FROM warehouse_v_billing_report LIMIT 10;
EXIT;
```

---

## 4. Build the dashboard

We will use **Streamlit** because it is free, Python-based, and easy to share on GitHub.

### Start the dashboard

Make sure your virtual environment is active:

```bash
source .venv/bin/activate
```

Then run:

```bash
streamlit run src/dashboard/dashboard.py
```

Streamlit will open a local web server. Open the URL it shows you, usually:

```text
http://localhost:8501
```

### What you will see

- **Executive Summary:** total transactions, match rate, discrepancies.
- **Reconciliation Breakdown:** bar chart of statuses.
- **Merchant Billing:** table of what each merchant owes.
- **Discrepancy Details:** filterable table of mismatched transactions.

---

## 5. Screenshot for your portfolio

Take a screenshot of the dashboard. This is great visual proof for GitHub and interviews.

---

## 6. What is next?

You now have a complete working project:

- ✅ MySQL data warehouse
- ✅ Python ETL pipeline
- ✅ Data quality validation
- ✅ Reconciliation logic
- ✅ Billing calculation
- ✅ Dashboard

The next step is to publish it all to **GitHub** with a clean README and project structure.
