"""PayFlow — End-to-end local pipeline runner.

Usage:
    python run_pipeline.py [--source data/raw]
"""

import argparse
import subprocess
from pathlib import Path

from src.ingestion.ingest_providers import ingest_all
from src.quality.validate_records import validate_all
from src.transformation.load_to_mysql import load_to_mysql
from src.utils.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER, RAW_DIR, PROCESSED_DIR, REJECTED_DIR


def run_sql_file(sql_path: Path) -> None:
    """Execute a SQL file using the MySQL client."""
    cmd = [
        "mysql",
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
    args = parser.parse_args()

    print("=" * 60)
    print("PayFlow Local Pipeline")
    print("=" * 60)

    # Step 1: Ingest and normalize provider files
    print("\n[1/4] Ingesting provider files...")
    ingest_all(args.source, PROCESSED_DIR)

    # Step 2: Validate data quality
    print("\n[2/4] Validating records...")
    validate_all(PROCESSED_DIR, REJECTED_DIR)

    # Step 3: Load into MySQL
    print("\n[3/4] Loading into MySQL...")
    load_to_mysql(PROCESSED_DIR / "valid_transactions.parquet")

    # Step 4: Populate star-schema fact table
    print("\n[4/4] Populating warehouse_fact_transaction...")
    run_sql_file(Path("sql/transformation/populate_fact_transaction.sql"))

    print("\nPipeline complete.")
    print("Next steps:")
    print("  mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < sql/reconciliation/reconcile_transactions.sql")
    print("  mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < sql/billing/generate_billing.sql")


if __name__ == "__main__":
    main()
