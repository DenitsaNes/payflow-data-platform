# PayFlow — Project Overview for Beginners

## The goal

Build a realistic data engineering project that looks like a **real client engagement**. When you finish, you will have:

- A working MySQL data warehouse.
- A Python ETL pipeline.
- SQL reconciliation logic.
- A billing calculation.
- A dashboard.
- Documentation and architecture decisions.

You can put all of this on GitHub and talk about it in job interviews.

---

## The story

**PayFlow** is a fictional fintech company. It helps online shops accept payments.

Every day, PayFlow receives transaction files from three external payment providers:

- **Provider A** sends a CSV file.
- **Provider B** sends a JSON file.
- **Provider C** sends a CSV file with different column names.

PayFlow also has its own internal system that records every transaction.

### The problem

The finance team currently downloads these files and compares them manually in spreadsheets. This takes **4 hours per day** and is full of mistakes.

### Our solution

We will build an automated data platform that:

1. Reads all three provider files.
2. Converts them into one common format.
3. Checks for bad data.
4. Compares provider data against internal records.
5. Calculates how much to bill each merchant.
6. Shows the results in a dashboard.

---

## The architecture

```text
PAYMENT PROVIDERS
   ├─ Provider A (CSV)
   ├─ Provider B (JSON)
   └─ Provider C (CSV)
          │
          ▼
    [Python ETL]
    Read → Clean → Validate
          │
          ▼
      MySQL Database
          │
    ┌─────┴──────┐
    ▼            ▼
Reconciliation  Billing
    │            │
    └──────┬─────┘
           ▼
      Dashboard
```

---

## What we will build step by step

### Step 0 — Project foundation

**What:** Create the folder structure, README, and documentation.

**Why:** Before writing code, a data engineer must understand the business problem and design the architecture. This is what consultants do.

**What you learn:** How to organize a real project and write business requirements.

**Status:** ✅ Done.

---

### Step 1 — Set up MySQL

**What:** Start a MySQL database inside Docker and create the tables.

**Why:** We need a place to store all the transaction data.

**What you learn:** Docker basics, MySQL, database connections, ports, users.

**Status:** ✅ Done.

---

### Step 2 — Understand the data

**What:** Look at the provider files and understand how they are different.

**Why:** Before writing code, you must understand the data. This is the most important step.

**What you learn:** CSV vs JSON, data normalization, why different companies use different names for the same thing.

**Status:** This is Lesson 2.

---

### Step 3 — Build the data warehouse

**What:** Create fact tables and dimension tables in MySQL.

**Why:** A data warehouse makes reporting fast and easy. It separates facts (transactions) from dimensions (merchants, currencies, dates).

**What you learn:** Star schema, fact tables, dimension tables, OLTP vs OLAP, primary keys, foreign keys, indexes.

**Status:** ✅ SQL schema is done. We will learn how it works.

---

### Step 4 — Load internal transactions

**What:** Put PayFlow's own transaction records into the database.

**Why:** Internal records are the source of truth. We will compare provider data against these.

**What you learn:** INSERT statements, seed data, timestamps.

**Status:** ✅ Done.

---

### Step 5 — Build the Python ingestion pipeline

**What:** Write Python scripts that read CSV and JSON files and load them into MySQL.

**Why:** Providers send files in different formats. Python normalizes them into one format.

**What you learn:** Python, pandas, CSV/JSON parsing, SQLAlchemy, database connections, error handling.

**Status:** Not done yet — Lesson 4.

---

### Step 6 — Validate data quality

**What:** Check for duplicates, bad amounts, invalid currencies, missing merchants, and wrong statuses.

**Why:** Bad data will break reconciliation and billing. We must catch it early.

**What you learn:** Data validation, data quality rules, rejected/quarantine records.

**Status:** Not done yet.

---

### Step 7 — Reconcile transactions

**What:** Compare internal transactions against provider transactions and classify the results.

**Why:** This is the core business value. Finance needs to know what matches and what doesn't.

**What you learn:** SQL JOINs, CTEs, window functions, CASE statements, reconciliation logic.

**Status:** ✅ SQL is written. We will run and explain it in Lesson 3.

---

### Step 8 — Calculate billing

**What:** Calculate how much each merchant owes PayFlow.

**Why:** PayFlow makes money by charging fees. The business must know how much to bill each merchant.

**What you learn:** SQL aggregations, fee calculations, GROUP BY, business logic in SQL.

**Status:** ✅ SQL is written. We will run it later.

---

### Step 9 — Build a dashboard

**What:** Create charts and KPIs from the warehouse data.

**Why:** Finance and operations teams need to see results visually, not just SQL tables.

**What you learn:** Dashboard tools, connecting to MySQL, KPIs, filters.

**Status:** Not done yet.

---

### Step 10 — Add AWS layer (optional but impressive)

**What:** Design how this would work with AWS S3, Lambda, Glue, and Kinesis.

**Why:** Accedia and similar companies want to see cloud knowledge.

**What you learn:** AWS basics, cloud data architecture, batch vs streaming.

**Status:** Documented, but not fully implemented yet.

---

### Step 11 — Tests, polish, and publish

**What:** Write tests, clean up documentation, and publish to GitHub.

**Why:** A portfolio project must look professional and work reliably.

**What you learn:** Testing, documentation, GitHub, presenting your work.

**Status:** Not done yet.

---

## How each step maps to the Accedia job

| Accedia wants | PayFlow project proves it |
|---------------|---------------------------|
| Strong SQL | Reconciliation + billing SQL |
| Relational DB fundamentals | MySQL schema with keys, indexes, constraints |
| Data warehouse principles | Star schema with facts and dimensions |
| ETL / data pipelines | Python ingestion script |
| Data quality | Validation layer |
| Visualization | Dashboard |
| AWS basics | S3/Lambda/Glue/Kinesis design |
| Communication / consulting | README, business requirements, ADRs |

---

## Your learning path

| Lesson | Topic | Status |
|--------|-------|--------|
| Lesson 1 | Set up MySQL | ✅ Done |
| Lesson 2 | Understand the data | Current |
| Lesson 3 | Reconciliation SQL | Next |
| Lesson 4 | Python ingestion pipeline | Later |
| Lesson 5 | Billing + dashboard | Later |

---

## The mindset

You are not just "writing code." You are **solving a business problem**. Every time you write SQL or Python, ask:

- Why does the business need this?
- What would happen if this data were wrong?
- How would I explain this to someone who is not technical?

That is exactly what makes a good junior data engineer.
