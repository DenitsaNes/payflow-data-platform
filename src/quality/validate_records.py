"""PayFlow — Data quality validation.

Reads transaction records, validates each record, and splits into valid and rejected.
Can be used from the Silver cleaner or from file-based validation.
"""

import argparse
import math
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.utils.config import MAX_TRANSACTION_DATE, PROCESSED_DIR, REJECTED_DIR
from src.utils.db import get_engine


VALID_CURRENCIES = {"EUR", "USD", "GBP"}
VALID_STATUSES = {"SUCCESS", "FAILED", "REFUNDED", "PENDING"}

STATUS_NORMALIZATION = {
    "COMPLETED": "SUCCESS",
    "SUCCESS": "SUCCESS",
    "completed": "SUCCESS",
    "FAILED": "FAILED",
    "failed": "FAILED",
    "DECLINED": "FAILED",
    "declined": "FAILED",
    "REFUNDED": "REFUNDED",
    "refunded": "REFUNDED",
    "PENDING": "PENDING",
    "pending": "PENDING",
}


def get_valid_merchants() -> set[str]:
    """Fetch valid merchant IDs from the warehouse dimension table."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT merchant_id FROM warehouse_dim_merchant"))
        return {row[0] for row in result}


def normalize_status(status) -> str:
    """Convert a provider status to canonical internal status."""
    if pd.isna(status):
        return status
    raw = str(status).strip()
    return STATUS_NORMALIZATION.get(raw, raw)


def parse_timestamp(ts) -> datetime | None:
    """Try to parse a timestamp string into a datetime."""
    if pd.isna(ts):
        return None
    ts = str(ts).strip()
    if not ts:
        return None
    # Normalize ISO-like separators
    ts = ts.replace("T", " ").replace("Z", "")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue
    return None


def validate_records(df: pd.DataFrame, valid_merchants: set[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split records into valid and rejected.

    Assumes the DataFrame already has canonical column names and normalized status.
    Timestamp may still be a string; it is parsed here.
    """
    df = df.copy()
    df["rejection_reason"] = None

    # Rule 1: transaction_id is not null/empty
    missing_id = df["transaction_id"].isna() | (df["transaction_id"].astype(str).str.strip() == "")
    df.loc[missing_id, "rejection_reason"] = "missing_transaction_id"

    # Rule 2: merchant_id is not null/empty
    missing_merchant = df["merchant_id"].isna() | (df["merchant_id"].astype(str).str.strip() == "")
    df.loc[missing_merchant & df["rejection_reason"].isna(), "rejection_reason"] = "missing_merchant_id"

    # Rule 3: amount is numeric and >= 0
    def amount_invalid(value):
        try:
            if value is None or (isinstance(value, float) and math.isnan(value)):
                return "invalid_amount"
            num = float(value)
            if num < 0:
                return "negative_amount"
            return None
        except (ValueError, TypeError):
            return "invalid_amount"

    amount_reason = df["amount"].apply(amount_invalid)
    df.loc[amount_reason.notna() & df["rejection_reason"].isna(), "rejection_reason"] = amount_reason

    # Rule 4: currency is valid
    invalid_currency = ~df["currency"].isin(VALID_CURRENCIES)
    df.loc[invalid_currency & df["rejection_reason"].isna(), "rejection_reason"] = "invalid_currency"

    # Rule 5: timestamp is parseable and not in the future
    def timestamp_reason(value):
        parsed = parse_timestamp(value)
        if parsed is None:
            return "invalid_timestamp"
        if parsed > MAX_TRANSACTION_DATE:
            return "future_timestamp"
        return None

    ts_reason = df["transaction_timestamp"].apply(timestamp_reason)
    df.loc[ts_reason.notna() & df["rejection_reason"].isna(), "rejection_reason"] = ts_reason

    # Rule 6: status is one of the known values
    invalid_status = ~df["status"].isin(VALID_STATUSES)
    df.loc[invalid_status & df["rejection_reason"].isna(), "rejection_reason"] = "invalid_status"

    # Rule 7: merchant_id exists in dimension table
    invalid_merchant = ~df["merchant_id"].isin(valid_merchants)
    df.loc[invalid_merchant & df["rejection_reason"].isna(), "rejection_reason"] = "unknown_merchant"

    valid = df[df["rejection_reason"].isna()].copy()
    rejected = df[df["rejection_reason"].notna()].copy()

    return valid, rejected


def clean_and_validate(df: pd.DataFrame, valid_merchants: set[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Normalize statuses and timestamps, then validate records."""
    df = df.copy()
    df["status"] = df["status"].apply(normalize_status)
    df["transaction_timestamp"] = df["transaction_timestamp"].apply(parse_timestamp)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    return validate_records(df, valid_merchants)


def deduplicate_valid_records(df: pd.DataFrame) -> pd.DataFrame:
    """Keep the latest record per (transaction_id, provider)."""
    if df.empty:
        return df
    df = df.sort_values(by=["transaction_timestamp", "loaded_at"], ascending=[False, False])
    return df.drop_duplicates(subset=["transaction_id", "provider"], keep="first")


def validate_all(input_dir: Path, rejected_dir: Path) -> pd.DataFrame:
    """Validate combined transactions and write valid/rejected files."""
    input_file = input_dir / "combined_transactions.parquet"
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    df = pd.read_parquet(input_file)
    print(f"Read {len(df)} records from {input_file}")

    valid_merchants = get_valid_merchants()
    print(f"Loaded {len(valid_merchants)} valid merchants from warehouse_dim_merchant")

    valid, rejected = clean_and_validate(df, valid_merchants)

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
