#!/usr/bin/env python3
"""Run an end-to-end scale test and print a timing report.

Usage:
    python scripts/run_scale_test.py --num-transactions 100000

The script assumes Docker MySQL is running on port 3307. It:
1. Resets the payflow schema.
2. Generates the synthetic dataset.
3. Loads seed data.
4. Runs Bronze -> Silver -> fact -> reconciliation -> billing.
5. Prints a timing and row-count report.
"""

import argparse
import subprocess
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str], description: str) -> float:
    """Run a shell command from the project root and return elapsed seconds."""
    print(f"\n>>> {description}")
    start = time.perf_counter()
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)
    elapsed = time.perf_counter() - start
    print(f"    {elapsed:.2f}s")
    return elapsed


def mysql_cmd() -> list[str]:
    return [
        "mysql",
        "-h", "127.0.0.1",
        "-P", "3307",
        "-u", "payflow",
        "-ppayflow",
        "payflow",
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="PayFlow scale test")
    parser.add_argument(
        "--num-transactions",
        type=int,
        default=100_000,
        help="Number of internal transactions to generate",
    )
    args = parser.parse_args()

    print("=" * 60)
    print(f"PayFlow Scale Test — {args.num_transactions:,} internal transactions")
    print("=" * 60)

    timings: dict[str, float] = {}

    # 1. Reset schema
    schema_path = PROJECT_ROOT / "sql" / "schema" / "01_create_database.sql"
    print("\n>>> Reset database schema")
    start = time.perf_counter()
    with open(schema_path, "rb") as f:
        subprocess.run(mysql_cmd(), stdin=f, cwd=PROJECT_ROOT, check=True)
    timings["reset_schema"] = time.perf_counter() - start
    print(f"    {timings['reset_schema']:.2f}s")

    # 2. Generate data
    timings["generate_data"] = run(
        [".venv/bin/python", "-m", "src.utils.generate_data", "--num-transactions", str(args.num_transactions)],
        "Generate synthetic data",
    )

    # 3. Load seed data
    seed_path = PROJECT_ROOT / "data" / "generated" / "seed_data.sql"
    start = time.perf_counter()
    with open(seed_path, "rb") as f:
        subprocess.run(mysql_cmd(), stdin=f, cwd=PROJECT_ROOT, check=True)
    timings["load_seed"] = time.perf_counter() - start
    print(f"    {timings['load_seed']:.2f}s")

    # 4. Bronze
    timings["bronze"] = run(
        [".venv/bin/python", "-m", "src.transformation.load_bronze", "--source", "data/generated/raw"],
        "Load Bronze layer",
    )

    # 5. Silver
    timings["silver"] = run(
        [".venv/bin/python", "-m", "src.transformation.silver_cleaner"],
        "Clean Bronze -> Silver",
    )

    # 6. Fact table
    fact_sql = PROJECT_ROOT / "sql" / "transformation" / "populate_fact_transaction.sql"
    start = time.perf_counter()
    with open(fact_sql, "rb") as f:
        subprocess.run(mysql_cmd(), stdin=f, cwd=PROJECT_ROOT, check=True)
    timings["fact"] = time.perf_counter() - start
    print(f"    {timings['fact']:.2f}s")

    # 7. Reconciliation
    rec_sql = PROJECT_ROOT / "sql" / "reconciliation" / "reconcile_transactions.sql"
    start = time.perf_counter()
    with open(rec_sql, "rb") as f:
        subprocess.run(mysql_cmd(), stdin=f, cwd=PROJECT_ROOT, check=True)
    timings["reconciliation"] = time.perf_counter() - start
    print(f"    {timings['reconciliation']:.2f}s")

    # 8. Billing
    bill_sql = PROJECT_ROOT / "sql" / "billing" / "generate_billing.sql"
    start = time.perf_counter()
    with open(bill_sql, "rb") as f:
        subprocess.run(mysql_cmd(), stdin=f, cwd=PROJECT_ROOT, check=True)
    timings["billing"] = time.perf_counter() - start
    print(f"    {timings['billing']:.2f}s")

    # Summary
    total = sum(timings.values())
    print("\n" + "=" * 60)
    print("Scale Test Summary")
    print("=" * 60)
    for stage, elapsed in timings.items():
        print(f"  {stage:20s}: {elapsed:6.2f}s")
    print(f"  {'total':20s}: {total:6.2f}s")
    print(f"\nDataset: {args.num_transactions:,} internal transactions")


if __name__ == "__main__":
    main()
