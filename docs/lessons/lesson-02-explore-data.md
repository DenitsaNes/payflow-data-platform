# Lesson 2: Understand the Data and Run First SQL Queries

> In this lesson, we explore the raw data files and the database tables we created. We will understand why the provider files are different and what we need to do about it.

---

## 1. The big picture

PayFlow has three payment providers. Each one sends transaction data in a different format.

Imagine you work at PayFlow. Every morning, three different files arrive:

- `provider_a_2026_09_06.csv` — a CSV file.
- `provider_b_2026_09_06.json` — a JSON file.
- `provider_c_2026_09_06.csv` — another CSV file, but with different column names.

Your job is to read all three files and put them into one clean table in MySQL.

---

## 2. Look at the raw provider files

Open your terminal and go to the project folder:

```bash
cd payflow-data-platform
```

### Provider A — CSV

Look at the file:

```bash
cat data/raw/provider_a/provider_a_2026_09_06.csv
```

You will see:

```csv
transaction_id,merchant_id,amount,currency,status,timestamp
TX001,M001,125.50,EUR,COMPLETED,2026-09-06 10:32:11
...
```

This is clean and easy to read. The columns are:

- `transaction_id`
- `merchant_id`
- `amount`
- `currency`
- `status`
- `timestamp`

### Provider B — JSON

Look at the file:

```bash
cat data/raw/provider_b/provider_b_2026_09_06.json
```

You will see something like:

```json
[
  {
    "payment_id": "TX001",
    "merchant": "M001",
    "value": 125.50,
    "currency": "EUR",
    "payment_status": "SUCCESS",
    "created_at": "2026-09-06T10:32:11Z"
  },
  ...
]
```

Notice the differences:

| Concept | Provider A | Provider B |
|---------|------------|------------|
| ID | `transaction_id` | `payment_id` |
| Merchant | `merchant_id` | `merchant` |
| Amount | `amount` | `value` |
| Status | `status` | `payment_status` |
| Time | `timestamp` | `created_at` |

### Provider C — CSV with different names

Look at the file:

```bash
cat data/raw/provider_c/provider_c_2026_09_06.csv
```

You will see:

```csv
transactionId,merchant,amount,currency,result,date
TX001,M001,125.50,EUR,completed,2026-09-06T10:32:11Z
...
```

Different again:

| Concept | Provider C |
|---------|------------|
| ID | `transactionId` |
| Merchant | `merchant` |
| Amount | `amount` |
| Status | `result` |
| Time | `date` |

Also notice that Provider C has a bad record:

```csv
TX014,M001,one hundred,EUR,completed,2026-09-06T23:00:00Z
```

The amount is the text `"one hundred"` instead of a number. Our data-quality layer will catch this later.

---

## 3. The goal: one common format

We want all three providers to end up in the same table with the same column names.

Our target table is `staging_transactions`. Its columns are:

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
is_valid
rejection_reason
```

This is called **normalization** or **standardization**.

> **Analogy:** Imagine three people give you their shopping lists. One writes "milk", another writes "cow juice", and another draws a picture of a carton. You rewrite them all as "milk" so you can compare them.

---

## 4. Look at the dimension tables

Connect to MySQL again:

```bash
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow
```

Password: `payflow`

### Currency

```sql
SELECT * FROM warehouse_dim_currency;
```

This table lists all valid currencies.

### Provider

```sql
SELECT * FROM warehouse_dim_provider;
```

This table lists the three providers and their file formats.

### Transaction status

```sql
SELECT * FROM warehouse_dim_transaction_status;
```

This table maps different status words to categories:

- `SUCCESS` and `COMPLETED` → `completed`
- `FAILED` and `DECLINED` → `failed`
- `REFUNDED` → `refund`
- `PENDING` → `pending`

This is important because Provider A says `COMPLETED` while Provider B says `SUCCESS`. We need to treat them as the same thing.

### Date

```sql
SELECT * FROM warehouse_dim_date LIMIT 7;
```

This table has one row per day. We use it to make date-based reporting faster.

---

## 5. Look at the internal transactions

```sql
SELECT * FROM reconciliation_internal_transactions;
```

These are PayFlow's own records. They are our source of truth.

Notice:

- TX001 to TX010 are real transactions.
- TX016 exists in internal records but not in any provider file — this will be important for reconciliation.

---

## 6. Count the internal transactions

```sql
SELECT COUNT(*) AS total_internal_transactions FROM reconciliation_internal_transactions;
```

You should see `11`.

---

## 7. Count transactions per merchant

```sql
SELECT
    merchant_id,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_amount
FROM reconciliation_internal_transactions
GROUP BY merchant_id;
```

This query:

- Groups the transactions by `merchant_id`.
- Counts how many each merchant has.
- Sums the amounts.

You should see:

| merchant_id | transaction_count | total_amount |
|-------------|-------------------|--------------|
| M001 | 4 | 550.50 |
| M002 | 4 | 467.00 |
| M003 | 3 | 190.00 |

---

## 8. Preview: what is reconciliation?

Internal records say one thing. Provider files say another. We compare them.

For example:

- Internal says TX003 = €120.
- Provider B says TX003 = €125.
- This is an **amount mismatch**.

- Internal says TX016 exists.
- No provider reports TX016.
- This is **missing from gateway**.

- Provider B reports TX011 for merchant M004.
- Internal records do not have TX011.
- This is **missing internal**.

In the next lesson, we will run the actual reconciliation SQL and see all of these results.

---

## 9. Your homework before Lesson 3

1. Look at all three provider files with `cat`.
2. Connect to MySQL and explore the dimension tables.
3. Run the aggregation query above.
4. Try to find the bad record in Provider C.
5. Think about this question: *Why do we need a `dim_transaction_status` table when Provider A and Provider B use different words?*

If you can answer that question, you understand one of the most important ideas in data engineering.

---

## 10. What is next?

In **Lesson 3**, we will:

- Load the provider files into `reconciliation_gateway_transactions`.
- Run the reconciliation SQL.
- Learn about CTEs, window functions, and JOINs in plain language.
- See the mismatch results in a table.
