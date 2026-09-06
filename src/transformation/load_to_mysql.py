"""PayFlow — Load validated transactions into MySQL.

Reads the valid_transactions.parquet file and loads the records into the
reconciliation_gateway_transactions table. Uses SQLAlchemy for the connection
and INSERTs records in batches for performance.
"""

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.utils.config import PROCESSED_DIR
from src.utils.db import get_engine


def load_to_mysql(input_file: Path, batch_size: int = 1000) -> int:
    """Load valid transactions into reconciliation_gateway_transactions."""
    df = pd.read_parquet(input_file)
    print(f"Read {len(df)} valid records from {input_file}")

    if df.empty:
        print("No records to load.")
        return 0

    # Rename columns to match MySQL table
    columns = [
        "transaction_id",
        "provider",
        "transaction_timestamp",
        "merchant_id",
        "amount",
        "currency",
        "status",
        "source_file",
    ]
    df = df[columns]

    engine = get_engine()

    # Clear existing gateway records before loading fresh data
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE reconciliation_gateway_transactions"))

    insert_sql = text(
        """
        INSERT INTO reconciliation_gateway_transactions
        (transaction_id, provider, transaction_timestamp, merchant_id, amount, currency, status, source_file)
        VALUES
        (:transaction_id, :provider, :transaction_timestamp, :merchant_id, :amount, :currency, :status, :source_file)
        """
    )

    rows_inserted = 0
    with engine.begin() as conn:
        for start in range(0, len(df), batch_size):
            batch = df.iloc[start : start + batch_size]
            records = batch.to_dict("records")
            conn.execute(insert_sql, records)
            rows_inserted += len(records)
            print(f"Inserted {rows_inserted} / {len(df)} records ...")

    print(f"Done. Loaded {rows_inserted} records into reconciliation_gateway_transactions.")
    return rows_inserted


def main() -> None:
    parser = argparse.ArgumentParser(description="Load validated transactions into MySQL")
    parser.add_argument(
        "--input",
        type=Path,
        default=PROCESSED_DIR / "valid_transactions.parquet",
        help="Path to valid_transactions.parquet",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of rows to insert per batch",
    )
    args = parser.parse_args()

    load_to_mysql(args.input, args.batch_size)


if __name__ == "__main__":
    main()
