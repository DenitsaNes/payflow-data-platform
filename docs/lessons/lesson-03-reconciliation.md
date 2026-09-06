# Lesson 3: Run Reconciliation and Understand the SQL Logic

> This lesson is the heart of the project. We will compare internal transactions against gateway transactions and find the differences.

---

## 1. What is reconciliation?

**Reconciliation** means comparing two sets of records to find differences.

In our project:

- **Set 1:** PayFlow's internal transaction records.
- **Set 2:** What the payment providers reported.

We want to answer questions like:

- Did Provider A report the same amount as our internal system?
- Did Provider B miss a transaction?
- Did Provider C report a transaction that we don't have?

This is exactly what the finance team does manually every day. We will automate it with SQL.

---

## 2. Load the gateway transactions

Before we can reconcile, we need to put the provider data into a table.

Run this SQL file:

```bash
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < data/sample/seed_gateway_transactions.sql
```

Password: `payflow`

This loads all the provider records into the table `reconciliation_gateway_transactions`.

### Check what was loaded

Connect to MySQL:

```bash
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow
```

Password: `payflow`

Run:

```sql
SELECT COUNT(*) FROM reconciliation_gateway_transactions;
```

You should see `34`. That includes the duplicate TX003 and TX011.

Look at the data:

```sql
SELECT * FROM reconciliation_gateway_transactions LIMIT 10;
```

---

## 3. The reconciliation logic

Open the reconciliation SQL file:

```bash
less sql/reconciliation/reconcile_transactions.sql
```

Read it slowly. We will explain every part.

### Part 1: Deduplicate gateway records

```sql
WITH latest_gateway_record AS (
    SELECT
        transaction_id,
        provider,
        merchant_id,
        amount,
        currency,
        status,
        transaction_timestamp,
        source_file,
        ROW_NUMBER() OVER (
            PARTITION BY transaction_id, provider
            ORDER BY transaction_timestamp DESC, loaded_at DESC
        ) AS rn
    FROM reconciliation_gateway_transactions
)
```

**What is this doing?**

Provider A sent TX003 twice. We only want to compare against the most recent one.

`ROW_NUMBER() OVER (PARTITION BY transaction_id, provider ORDER BY transaction_timestamp DESC, loaded_at DESC)` means:

- For each group of records with the same `transaction_id` and `provider`...
- Sort them by `transaction_timestamp` (newest first)...
- Give each row a number: 1, 2, 3, ...

Then in the next CTE, we keep only rows where `rn = 1`.

> **Analogy:** Imagine you have two photos of the same transaction. You only need the newest one. `ROW_NUMBER` labels them and you throw away everything except number 1.

### Part 2: Compare internal vs gateway

```sql
matched AS (
    SELECT
        i.transaction_id,
        DATE(i.transaction_timestamp) AS txn_date,
        i.merchant_id,
        g.provider,
        i.amount AS internal_amount,
        g.amount AS gateway_amount,
        (COALESCE(i.amount, 0) - COALESCE(g.amount, 0)) AS amount_difference,
        i.status AS internal_status,
        g.status AS gateway_status,
        CASE
            WHEN g.transaction_id IS NULL THEN 'MISSING_FROM_GATEWAY'
            WHEN i.amount <> g.amount THEN 'AMOUNT_MISMATCH'
            WHEN i.status <> g.status THEN 'STATUS_MISMATCH'
            ELSE 'MATCH'
        END AS reconciliation_status
    FROM reconciliation_internal_transactions i
    LEFT JOIN gateway g
        ON i.transaction_id = g.transaction_id
)
```

**What is this doing?**

We take every internal transaction and try to find a matching gateway transaction by `transaction_id`.

- `LEFT JOIN` means: keep every internal transaction, even if there is no match in gateway.
- If `g.transaction_id IS NULL`, the gateway has no record of this transaction → `MISSING_FROM_GATEWAY`.
- If amounts are different → `AMOUNT_MISMATCH`.
- If statuses are different → `STATUS_MISMATCH`.
- Otherwise → `MATCH`.

> **Analogy:** You have your own notebook of sales. You compare it against the credit card company's report. Some sales are missing, some have different amounts, some match perfectly.

### Part 3: Find gateway records missing from internal

```sql
missing_internal AS (
    SELECT
        g.transaction_id,
        DATE(g.transaction_timestamp) AS txn_date,
        g.merchant_id,
        g.provider,
        NULL AS internal_amount,
        g.amount AS gateway_amount,
        NULL AS amount_difference,
        NULL AS internal_status,
        g.status AS gateway_status,
        'MISSING_INTERNAL' AS reconciliation_status
    FROM gateway g
    LEFT JOIN reconciliation_internal_transactions i
        ON g.transaction_id = i.transaction_id
    WHERE i.transaction_id IS NULL
)
```

**What is this doing?**

This finds records that exist in the gateway but not in internal.

`WHERE i.transaction_id IS NULL` means: keep only gateway records that have no matching internal record.

### Part 4: Combine and save

```sql
combined AS (
    SELECT * FROM matched
    UNION ALL
    SELECT * FROM missing_internal
)
```

This puts both results together.

Then we insert the final result into `warehouse_fact_reconciliation`.

---

## 4. Run the reconciliation

Run this command:

```bash
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < sql/reconciliation/reconcile_transactions.sql
```

Password: `payflow`

If it works, you will see no error.

---

## 5. Look at the results

Connect to MySQL:

```bash
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow
```

### See the summary

```sql
SELECT * FROM warehouse_v_reconciliation_summary;
```

You should see something like:

| reconciliation_status | transaction_count | total_discrepancy_amount |
|-------------------------|-------------------|--------------------------|
| MATCH | 9 | 0 |
| AMOUNT_MISMATCH | 1 | 5 |
| MISSING_FROM_GATEWAY | 1 | 0 |
| MISSING_INTERNAL | 1 | 0 |

### See the details

```sql
SELECT * FROM warehouse_fact_reconciliation;
```

Look at each row and understand why it got that status:

- TX003 should be `AMOUNT_MISMATCH` because internal is 120.00 and gateway is 125.00.
- TX011 should be `MISSING_INTERNAL` because it only exists in gateway.
- TX016 should be `MISSING_FROM_GATEWAY` because it only exists in internal.
- All others should be `MATCH`.

### Count by status

```sql
SELECT
    reconciliation_status,
    COUNT(*) AS count
FROM warehouse_fact_reconciliation
GROUP BY reconciliation_status;
```

---

## 6. Key SQL concepts you just used

| Concept | What it does | Where we used it |
|---------|--------------|------------------|
| **CTE** (`WITH ... AS`) | Creates a temporary named result set | `latest_gateway_record`, `gateway`, `matched` |
| **Window function** (`ROW_NUMBER() OVER`) | Numbers rows within groups | Deduplicate gateway records |
| **JOIN** (`LEFT JOIN`) | Combines two tables | Match internal to gateway |
| **CASE** | Creates conditional logic | Decide reconciliation status |
| **COALESCE** | Replaces NULL with a default value | Calculate amount difference |
| **INSERT INTO ... SELECT** | Inserts query results into a table | Save reconciliation output |

These are the exact SQL skills Accedia wants.

---

## 7. Your homework before Lesson 4

1. Run the reconciliation SQL.
2. Look at the results in `warehouse_fact_reconciliation`.
3. Verify that TX003 is an amount mismatch and TX011 is missing internal.
4. Try to answer: *Why do we use `LEFT JOIN` instead of `JOIN`?*
5. Look at the SQL again and identify the CTE, window function, and CASE parts.

---

## 8. What is next?

In **Lesson 4**, we will build the Python ingestion pipeline. We will write code that:

- Reads CSV and JSON files.
- Normalizes them into the common format.
- Validates data quality.
- Loads clean records into MySQL.

This replaces the manual `seed_gateway_transactions.sql` file with real code.
