"""PayFlow — Silver cleaner.

Reads raw Bronze provider records, normalizes them, validates them, and
upserts valid records into silver_transactions. Rejected records are
stored in silver_rejected_transactions with a reason.
"""

import argparse
import json
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.quality.validate_records import clean_and_validate, deduplicate_valid_records, get_valid_merchants
from src.utils.config import RAW_DIR
from src.utils.db import get_engine


CANONICAL_COLUMNS = [
    "transaction_id",
    "transaction_timestamp",
    "source_system",
    "provider",
    "merchant_id",
    "amount",
    "currency",
    "status",
    "source_file",
    "batch_id",
    "loaded_at",
]


def read_bronze_records(batch_id: str | None = None) -> pd.DataFrame:
    """Read Bronze provider records. If batch_id is None, read all unprocessed records."""
    engine = get_engine()

    if batch_id:
        query = "SELECT * FROM bronze_provider_transactions WHERE batch_id = :batch_id"
        params = {"batch_id": batch_id}
    else:
        query = """
            SELECT bp.*
            FROM bronze_provider_transactions bp
            LEFT JOIN pipeline_processed_files pp
                ON bp.source_file = pp.source_file
                AND bp.provider = pp.provider
                AND bp.batch_id = pp.batch_id
            WHERE pp.processed_id IS NULL
               OR pp.status != 'success'
        """
        params = {}

    with engine.connect() as conn:
        df = pd.read_sql_query(text(query), conn, params=params)

    # Expand raw_record JSON into columns for normalization
    if "raw_record" in df.columns and not df.empty:
        raw_records = df["raw_record"].apply(lambda x: json.loads(x) if x else {})
        # Map provider-specific keys to canonical names
        canonical_maps = {
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

        normalized = []
        for _, row in df.iterrows():
            provider = row["provider"]
            raw = raw_records.loc[_] if isinstance(raw_records, pd.Series) else raw_records[_]
            mapping = canonical_maps.get(provider, {})
            norm = {canonical: raw.get(source, None) for source, canonical in mapping.items()}
            norm["provider"] = provider
            norm["source_system"] = provider
            norm["source_file"] = row["source_file"]
            norm["batch_id"] = row["batch_id"]
            norm["loaded_at"] = row["loaded_at"]
            normalized.append(norm)

        df = pd.DataFrame(normalized)

    for col in CANONICAL_COLUMNS:
        if col not in df.columns:
            df[col] = None

    return df[CANONICAL_COLUMNS]


def upsert_silver(valid: pd.DataFrame) -> int:
    """Upsert valid records into silver_transactions."""
    if valid.empty:
        return 0

    engine = get_engine()
    records = []
    for _, row in valid.iterrows():
        records.append(
            {
                "transaction_id": row["transaction_id"],
                "transaction_timestamp": row["transaction_timestamp"],
                "source_system": row["source_system"],
                "provider": row["provider"],
                "merchant_id": row["merchant_id"],
                "amount": float(row["amount"]),
                "currency": row["currency"],
                "status": row["status"],
                "source_file": row["source_file"],
                "batch_id": row["batch_id"],
            }
        )

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO silver_transactions
                    (transaction_id, transaction_timestamp, source_system, provider, merchant_id,
                     amount, currency, status, source_file, batch_id)
                VALUES
                    (:transaction_id, :transaction_timestamp, :source_system, :provider, :merchant_id,
                     :amount, :currency, :status, :source_file, :batch_id)
                ON DUPLICATE KEY UPDATE
                    transaction_timestamp = VALUES(transaction_timestamp),
                    amount = VALUES(amount),
                    status = VALUES(status),
                    source_file = VALUES(source_file),
                    batch_id = VALUES(batch_id),
                    cleaned_at = CURRENT_TIMESTAMP
                """
            ),
            records,
        )

    return len(records)


def insert_rejected(rejected: pd.DataFrame) -> int:
    """Insert rejected records into silver_rejected_transactions."""
    if rejected.empty:
        return 0

    engine = get_engine()
    records = []
    for _, row in rejected.iterrows():
        raw = {}
        for col in CANONICAL_COLUMNS:
            if col in row:
                raw[col] = row[col]
        records.append(
            {
                "transaction_id": row["transaction_id"],
                "transaction_timestamp": str(row["transaction_timestamp"]) if pd.notna(row["transaction_timestamp"]) else None,
                "source_system": row["source_system"],
                "provider": row["provider"],
                "merchant_id": row["merchant_id"],
                "amount": str(row["amount"]) if pd.notna(row["amount"]) else None,
                "currency": row["currency"],
                "status": row["status"],
                "source_file": row["source_file"],
                "batch_id": row["batch_id"],
                "rejection_reason": row["rejection_reason"],
                "raw_json": json.dumps(raw, default=str),
            }
        )

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO silver_rejected_transactions
                    (transaction_id, transaction_timestamp, source_system, provider, merchant_id,
                     amount, currency, status, source_file, batch_id, rejection_reason, raw_json)
                VALUES
                    (:transaction_id, :transaction_timestamp, :source_system, :provider, :merchant_id,
                     :amount, :currency, :status, :source_file, :batch_id, :rejection_reason, :raw_json)
                """
            ),
            records,
        )

    return len(records)


def clean_silver(batch_id: str | None = None) -> tuple[int, int, pd.DataFrame, pd.DataFrame]:
    """Clean Bronze records into Silver.

    Returns (valid_count, rejected_count, valid_df, rejected_df).
    """
    print("Reading Bronze records...")
    df = read_bronze_records(batch_id=batch_id)
    print(f"Read {len(df)} Bronze records")

    valid_merchants = get_valid_merchants()
    print(f"Loaded {len(valid_merchants)} valid merchants")

    print("Validating records...")
    valid, rejected = clean_and_validate(df, valid_merchants)

    print(f"Valid: {len(valid)}, Rejected: {len(rejected)}")

    print("Deduplicating valid records...")
    valid = deduplicate_valid_records(valid)
    print(f"After deduplication: {len(valid)}")

    valid_count = upsert_silver(valid)
    rejected_count = insert_rejected(rejected)

    print(f"Upserted {valid_count} records into silver_transactions")
    print(f"Inserted {rejected_count} records into silver_rejected_transactions")

    if not rejected.empty:
        print("\nRejection breakdown:")
        print(rejected["rejection_reason"].value_counts())

    return valid_count, rejected_count, valid, rejected


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean Bronze records into Silver")
    parser.add_argument("--batch-id", type=str, default=None, help="Process only a specific batch")
    args = parser.parse_args()

    clean_silver(batch_id=args.batch_id)


if __name__ == "__main__":
    main()
