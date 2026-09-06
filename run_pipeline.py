"""PayFlow — End-to-end local pipeline runner.

Usage:
    python run_pipeline.py [--source data/generated/raw] [--force]

Pipeline stages:
    1. Bronze: load raw provider files with metadata.
    2. Silver: clean, validate, deduplicate, and upsert into silver_transactions.
    3. Load Silver provider records into reconciliation_gateway_transactions.
    4. Populate warehouse_fact_transaction.
    5. Run reconciliation and billing SQL.
"""

import argparse
import shutil
import subprocess
from pathlib import Path

from src.transformation.load_bronze import load_bronze, update_processed_files
from src.transformation.silver_cleaner import clean_silver
from src.utils.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER, RAW_DIR


def run_sql_file(sql_path: Path) -> None:
    """Execute a SQL file using the MySQL client."""
    mysql_bin = shutil.which("mysql")
    if mysql_bin is None:
        # Common Homebrew location on macOS; fail with a helpful message otherwise.
        candidate = Path("/opt/homebrew/opt/mysql-client/bin/mysql")
        if candidate.exists():
            mysql_bin = str(candidate)
        else:
            raise FileNotFoundError(
                "mysql client not found in PATH. Install it with: brew install mysql-client"
            )

    cmd = [
        mysql_bin,
        f"-h{DB_HOST}",
        f"-P{DB_PORT}",
        f"-u{DB_USER}",
        f"-p{DB_PASSWORD}",
        DB_NAME,
    ]
    with open(sql_path, "r", encoding="utf-8") as f:
        subprocess.run(cmd, stdin=f, check=True, capture_output=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="PayFlow local pipeline")
    parser.add_argument(
        "--source",
        type=Path,
        default=RAW_DIR,
        help="Directory containing provider raw files (default: data/raw)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reprocess files already marked as processed",
    )
    parser.add_argument(
        "--skip-reconciliation",
        action="store_true",
        help="Skip reconciliation and billing SQL steps",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("PayFlow Local Pipeline")
    print("=" * 60)

    # Step 1: Bronze — load raw provider files
    print("\n[1/4] Loading Bronze layer...")
    processed_files = load_bronze(args.source, force=args.force)
    if not processed_files:
        print("No new files to process. Rebuilding Silver from existing Bronze.")

    # Step 2: Silver — clean, validate, deduplicate
    print("\n[2/4] Cleaning Bronze into Silver...")
    _, _, valid, rejected = clean_silver()

    # Update idempotency log with actual loaded/rejected counts per source file
    if processed_files:
        records_loaded = {}
        records_rejected = {}
        if not valid.empty:
            for (source_file, provider), group in valid.groupby(["source_file", "provider"]):
                records_loaded[(source_file, provider)] = len(group)
        if not rejected.empty:
            for (source_file, provider), group in rejected.groupby(["source_file", "provider"]):
                records_rejected[(source_file, provider)] = len(group)
        update_processed_files(processed_files, records_loaded, records_rejected)

    # Step 3: Populate star-schema fact table
    print("\n[3/4] Populating warehouse_fact_transaction...")
    run_sql_file(Path("sql/transformation/populate_fact_transaction.sql"))

    if not args.skip_reconciliation:
        # Step 4: Reconciliation and billing
        print("\n[4/4] Running reconciliation and billing...")
        run_sql_file(Path("sql/reconciliation/reconcile_transactions.sql"))
        run_sql_file(Path("sql/billing/generate_billing.sql"))
        print("\nPipeline complete.")
    else:
        print("\nPipeline complete (reconciliation skipped).")
        print("Next steps:")
        print("  mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < sql/reconciliation/reconcile_transactions.sql")
        print("  mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < sql/billing/generate_billing.sql")


if __name__ == "__main__":
    main()
