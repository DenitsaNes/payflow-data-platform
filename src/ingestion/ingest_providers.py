"""PayFlow — Provider file ingestion and normalization.

Reads raw CSV/JSON files from the three providers, normalizes them into a
common schema, and writes a combined Parquet file for downstream processing.
"""

import argparse
import json
import re
from pathlib import Path

import pandas as pd

from src.utils.config import RAW_DIR, PROCESSED_DIR


# Canonical column names we want in every record
CANONICAL_COLUMNS = [
    "transaction_id",
    "transaction_timestamp",
    "provider",
    "source_system",
    "merchant_id",
    "amount",
    "currency",
    "status",
    "source_file",
]


# Map each provider's column names to canonical names
COLUMN_MAP = {
    "provider_a": {
        "transaction_id": "transaction_id",
        "merchant_id": "merchant_id",
        "amount": "amount",
        "currency": "currency",
        "status": "status",
        "timestamp": "transaction_timestamp",
    },
    "provider_b": {
        "payment_id": "transaction_id",
        "merchant": "merchant_id",
        "value": "amount",
        "currency": "currency",
        "payment_status": "status",
        "created_at": "transaction_timestamp",
    },
    "provider_c": {
        "transactionId": "transaction_id",
        "merchant": "merchant_id",
        "amount": "amount",
        "currency": "currency",
        "result": "status",
        "date": "transaction_timestamp",
    },
}

# Map provider-specific status words to canonical internal statuses
STATUS_NORMALIZATION = {
    "COMPLETED": "SUCCESS",
    "SUCCESS": "SUCCESS",
    "completed": "SUCCESS",
    "FAILED": "FAILED",
    "FAILED": "FAILED",
    "failed": "FAILED",
    "DECLINED": "FAILED",
    "declined": "FAILED",
    "REFUNDED": "REFUNDED",
    "refunded": "REFUNDED",
    "PENDING": "PENDING",
    "pending": "PENDING",
}


def normalize_status(status: str) -> str:
    """Convert a provider status to canonical internal status."""
    if pd.isna(status):
        return status
    return STATUS_NORMALIZATION.get(str(status).strip(), str(status).strip())


def normalize_timestamp(ts: str) -> str:
    """Convert various timestamp formats to MySQL DATETIME format."""
    if pd.isna(ts):
        return ts
    ts = str(ts).strip()
    # Replace 'T' and 'Z' from ISO format
    ts = ts.replace("T", " ").replace("Z", "")
    return ts


def load_provider_a(file_path: Path) -> pd.DataFrame:
    """Load Provider A CSV file."""
    df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
    has_source_file = "source_file" in df.columns
    df = df.rename(columns=COLUMN_MAP["provider_a"])
    df["provider"] = "provider_a"
    df["source_system"] = "provider_a"
    df["source_file"] = df["source_file"] if has_source_file else file_path.name
    return df


def load_provider_b(file_path: Path) -> pd.DataFrame:
    """Load Provider B JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        records = json.load(f)
    df = pd.DataFrame(records, dtype=str)
    has_source_file = "source_file" in df.columns
    df = df.rename(columns=COLUMN_MAP["provider_b"])
    df["provider"] = "provider_b"
    df["source_system"] = "provider_b"
    df["source_file"] = df["source_file"] if has_source_file else file_path.name
    return df


def load_provider_c(file_path: Path) -> pd.DataFrame:
    """Load Provider C CSV file."""
    df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
    has_source_file = "source_file" in df.columns
    df = df.rename(columns=COLUMN_MAP["provider_c"])
    df["provider"] = "provider_c"
    df["source_system"] = "provider_c"
    df["source_file"] = df["source_file"] if has_source_file else file_path.name
    return df


def process_provider(file_path: Path, provider: str) -> pd.DataFrame:
    """Load and normalize a single provider file."""
    if provider == "provider_a":
        df = load_provider_a(file_path)
    elif provider == "provider_b":
        df = load_provider_b(file_path)
    elif provider == "provider_c":
        df = load_provider_c(file_path)
    else:
        raise ValueError(f"Unknown provider: {provider}")

    # Normalize status and timestamp
    df["status"] = df["status"].apply(normalize_status)
    df["transaction_timestamp"] = df["transaction_timestamp"].apply(normalize_timestamp)

    # Coerce amount to numeric; bad strings like "one hundred" become NaN
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    # Ensure all canonical columns exist
    for col in CANONICAL_COLUMNS:
        if col not in df.columns:
            df[col] = None

    return df[CANONICAL_COLUMNS]


def ingest_all(raw_dir: Path, output_dir: Path) -> pd.DataFrame:
    """Ingest all provider files and combine them."""
    output_dir.mkdir(parents=True, exist_ok=True)

    all_records = []
    provider_dirs = {
        "provider_a": raw_dir / "provider_a",
        "provider_b": raw_dir / "provider_b",
        "provider_c": raw_dir / "provider_c",
    }

    for provider, directory in provider_dirs.items():
        if not directory.exists():
            print(f"Warning: {directory} does not exist. Skipping.")
            continue

        for file_path in sorted(directory.iterdir()):
            if file_path.suffix.lower() not in (".csv", ".json"):
                continue

            print(f"Processing {file_path} ...")
            df = process_provider(file_path, provider)
            all_records.append(df)

    if not all_records:
        combined = pd.DataFrame(columns=CANONICAL_COLUMNS)
    else:
        combined = pd.concat(all_records, ignore_index=True)

    output_file = output_dir / "combined_transactions.parquet"
    combined.to_parquet(output_file, index=False)
    print(f"Wrote {len(combined)} records to {output_file}")

    return combined


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest PayFlow provider files")
    parser.add_argument(
        "--source",
        type=Path,
        default=RAW_DIR,
        help="Directory containing raw provider files",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=PROCESSED_DIR,
        help="Directory to write processed output",
    )
    args = parser.parse_args()

    ingest_all(args.source, args.target)


if __name__ == "__main__":
    main()
