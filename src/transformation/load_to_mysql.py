"""PayFlow — Load Silver transactions into the legacy reconciliation gateway table.

This module copies valid, deduplicated Silver provider transactions into
reconciliation_gateway_transactions so the existing reconciliation SQL can
run unchanged. The long-term target is to make all downstream SQL read from
silver_transactions directly.
"""

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.utils.config import PROCESSED_DIR
from src.utils.db import get_engine


def load_to_mysql(batch_size: int = 1000) -> int:
    """Load Silver provider transactions into reconciliation_gateway_transactions."""
    engine = get_engine()

    # Read valid provider transactions from the Silver layer
    query = """
        SELECT
            transaction_id,
            provider,
            transaction_timestamp,
            merchant_id,
            amount,
            currency,
            status,
            source_file
        FROM silver_transactions
        WHERE source_system <> 'internal'
    """
    df = pd.read_sql_query(text(query), engine.connect())
    print(f"Read {len(df)} Silver provider records")

    if df.empty:
        print("No records to load.")
        return 0

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
    parser = argparse.ArgumentParser(description="Load Silver provider transactions into MySQL")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of rows to insert per batch",
    )
    args = parser.parse_args()

    load_to_mysql(args.batch_size)


if __name__ == "__main__":
    main()
