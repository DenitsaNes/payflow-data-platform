# Lesson 6: Add dbt (Data Build Tool)

> dbt is the most popular tool for modern SQL transformations. Adding it to PayFlow makes the project look like real work at a data engineering team.

---

## 1. Why dbt?

| Without dbt | With dbt |
|-------------|----------|
| SQL files in a folder | Organized model layers (staging, marts) |
| Manual execution | `dbt run` executes everything in order |
| No tests | Built-in data tests (`not_null`, `unique`, `accepted_values`) |
| No documentation | Auto-generated docs |
| Hard to track dependencies | dbt builds a dependency graph |

---

## 2. Install dbt

```bash
pip install dbt-mysql
```

---

## 3. Initialize dbt project

```bash
dbt init payflow_dbt
```

Select **mysql** as the database.

---

## 4. Configure profile

Edit `~/.dbt/profiles.yml`:

```yaml
payflow_dbt:
  target: dev
  outputs:
    dev:
      type: mysql
      server: 127.0.0.1
      port: 3307
      database: payflow
      schema: payflow
      username: payflow
      password: payflow
      driver: MySQL ODBC 8.0 ANSI Driver
```

Test the connection:

```bash
cd payflow_dbt
dbt debug
```

---

## 5. Project structure

```text
payflow_dbt/
  models/
    sources.yml
    schema.yml
    staging/
      stg_internal_transactions.sql
      stg_gateway_transactions.sql
    marts/
      fct_transactions.sql
      fct_reconciliation.sql
      fct_billing.sql
  dbt_project.yml
```

---

## 6. Run dbt

```bash
cd payflow_dbt
dbt run
```

This creates views and tables in MySQL.

---

## 7. Run dbt tests

```bash
dbt test
```

You should see all tests pass.

---

## 8. Generate documentation

```bash
dbt docs generate
dbt docs serve
```

Open the URL shown in the terminal to see the auto-generated data documentation.

---

## 9. Why this impresses interviewers

You can now say:

> "I built a dbt project with staging models, mart models, sources, and automated tests. The reconciliation and billing logic are version-controlled SQL models with data quality checks."

This is exactly the kind of tooling Accedia and similar companies use.
