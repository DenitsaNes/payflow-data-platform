# Lesson 7: Tests and CI/CD

> Production data engineering projects need automated tests and CI/CD. In this lesson, we add pytest tests and GitHub Actions.

---

## 1. Why tests matter

Without tests, you cannot trust your pipeline. Tests prove that:

- Provider normalization works correctly.
- Data quality rules catch bad records.
- dbt models produce valid output.
- The project still works after changes.

---

## 2. Run tests locally

```bash
cd payflow-data-platform
source .venv/bin/activate
pytest tests/ -v
```

You should see:

```text
8 passed
```

---

## 3. What the tests cover

| Test file | What it tests |
|-----------|---------------|
| `tests/test_ingestion.py` | Provider columns are normalized, statuses are canonicalized, bad amounts become NaN |
| `tests/test_validation.py` | Invalid amounts, currencies, timestamps, statuses, and unknown merchants are rejected |

---

## 4. GitHub Actions CI/CD

The file `.github/workflows/ci.yml` runs automatically on every push and pull request.

It has two jobs:

1. **python-tests** — installs dependencies and runs pytest.
2. **dbt-tests** — starts a MySQL service, loads schema and sample data, then runs `dbt run` and `dbt test`.

This means every code change is automatically verified.

---

## 5. How to see CI in action

After pushing to GitHub:

1. Go to your repository on GitHub.
2. Click the **Actions** tab.
3. You will see the workflow running.
4. Green checkmark = all tests passed.

---

## 6. Why this impresses interviewers

You can now say:

> "The project has automated tests for ingestion and data validation, plus a CI/CD pipeline that runs pytest and dbt tests against a real MySQL database on every commit."

This shows you understand software engineering discipline, not just SQL.
