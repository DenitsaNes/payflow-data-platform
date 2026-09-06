"""PayFlow — Data quality validation.

Reads the combined transactions Parquet file, validates each record,
writes valid records to one file, and rejected records to another.
"""

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.utils.config import PROCESSED_DIR, REJECTED_DIR
from src.utils.db import get_engine


VALID_CURRENCIES = {"EUR", "USD", "GBP"}


def get_valid_merchants() -> set[str]:
    """Fetch valid merchant IDs from the warehouse dimension table."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT merchant_id FROM warehouse_dim_merchant"))
        return {row[0] for row in result}


def validate_records(df: pd.DataFrame, valid_merchants: set[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split records into valid and rejected."""
    df = df.copy()
    df["rejection_reason"] = None

    # Rule 1: transaction_id is not null/empty
    missing_id = df["transaction_id"].isna() | (df["transaction_id"].astype(str).str.strip() == "")
    df.loc[missing_id, "rejection_reason"] = "missing_transaction_id"

    # Rule 2: amount is numeric and >= 0
    def amount_invalid(value):
        import math
        try:
            if value is None or (isinstance(value, float) and math.isnan(value)):
                return True
            return float(value) < 0
        except (ValueError, TypeError):
            return True

    invalid_amount = df["amount"].apply(amount_invalid)
    df.loc[invalid_amount & df["rejection_reason"].isna(), "rejection_reason"] = "invalid_amount"

    # Rule 3: currency is valid
    invalid_currency = ~df["currency"].isin(VALID_CURRENCIES)
    df.loc[invalid_currency & df["rejection_reason"].isna(), "rejection_reason"] = "invalid_currency"

    # Rule 4: timestamp is not null
    missing_ts = df["transaction_timestamp"].isna() | (df["transaction_timestamp"].astype(str).str.strip() == "")
    df.loc[missing_ts & df["rejection_reason"].isna(), "rejection_reason"] = "missing_timestamp"

    # Rule 5: status is one of the known values
    valid_statuses = {"SUCCESS", "FAILED", "REFUNDED", "PENDING"}
    invalid_status = ~df["status"].isin(valid_statuses)
    df.loc[invalid_status & df["rejection_reason"].isna(), "rejection_reason"] = "invalid_status"

    # Rule 6: merchant_id exists in dimension table
    invalid_merchant = ~df["merchant_id"].isin(valid_merchants)
    df.loc[invalid_merchant & df["rejection_reason"].isna(), "rejection_reason"] = "unknown_merchant"

    valid = df[df["rejection_reason"].isna()].copy()
    rejected = df[df["rejection_reason"].notna()].copy()

    return valid, rejected


def validate_all(input_dir: Path, rejected_dir: Path) -> pd.DataFrame:
    """Validate combined transactions and write valid/rejected files."""
    input_file = input_dir / "combined_transactions.parquet"
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    df = pd.read_parquet(input_file)
    print(f"Read {len(df)} records from {input_file}")

    valid_merchants = get_valid_merchants()
    print(f"Loaded {len(valid_merchants)} valid merchants from warehouse_dim_merchant")

    valid, rejected = validate_records(df, valid_merchants)

    # Write valid records
    valid_file = input_dir / "valid_transactions.parquet"
    valid.to_parquet(valid_file, index=False)
    print(f"Wrote {len(valid)} valid records to {valid_file}")

    # Write rejected records
    rejected_dir.mkdir(parents=True, exist_ok=True)
    rejected_file = rejected_dir / "rejected_transactions.parquet"
    rejected.to_parquet(rejected_file, index=False)
    print(f"Wrote {len(rejected)} rejected records to {rejected_file}")

    # Summary
    print("\nRejection breakdown:")
    print(rejected["rejection_reason"].value_counts())

    return valid


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate PayFlow transaction records")
    parser.add_argument(
        "--input",
        type=Path,
        default=PROCESSED_DIR,
        help="Directory containing combined_transactions.parquet",
    )
    parser.add_argument(
        "--rejected-dir",
        type=Path,
        default=REJECTED_DIR,
        help="Directory to write rejected records",
    )
    args = parser.parse_args()

    validate_all(args.input, args.rejected_dir)


if __name__ == "__main__":
    main()
