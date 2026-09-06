"""PayFlow — Bronze loader.

Reads raw provider files and lands them in the Bronze layer with metadata.
Tracks processed files for idempotent reruns.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.utils.config import RAW_DIR
from src.utils.db import get_engine


BATCH_ID_FORMAT = "%Y%m%d_%H%M%S"


def is_file_already_processed(source_file: str, provider: str, engine) -> bool:
    """Return True if this file has already been successfully processed."""
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
                SELECT 1 FROM pipeline_processed_files
                WHERE source_file = :source_file
                  AND provider = :provider
                  AND status = 'success'
                LIMIT 1
                """
            ),
            {"source_file": source_file, "provider": provider},
        )
        return result.fetchone() is not None


def read_raw_file(file_path: Path, provider: str) -> pd.DataFrame:
    """Read a raw provider file while preserving original columns."""
    if file_path.suffix.lower() == ".csv":
        df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
    elif file_path.suffix.lower() == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            records = json.load(f)
        df = pd.DataFrame(records, dtype=str)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")

    # Ensure source_file column reflects the actual file name
    df["source_file"] = file_path.name
    df["provider"] = provider
    df["source_system"] = provider
    return df


def load_file_to_bronze(file_path: Path, provider: str, batch_id: str, engine) -> dict:
    """Load one raw provider file into Bronze tables."""
    df = read_raw_file(file_path, provider)
    record_count = len(df)

    file_format = file_path.suffix.lower().lstrip(".")

    with engine.begin() as conn:
        # Insert file metadata
        conn.execute(
            text(
                """
                INSERT INTO bronze_raw_provider_files
                    (source_file, provider, file_format, batch_id, record_count, status)
                VALUES
                    (:source_file, :provider, :file_format, :batch_id, :record_count, 'loaded')
                ON DUPLICATE KEY UPDATE
                    file_format = VALUES(file_format),
                    batch_id = VALUES(batch_id),
                    record_count = VALUES(record_count),
                    loaded_at = CURRENT_TIMESTAMP,
                    status = 'loaded'
                """
            ),
            {
                "source_file": file_path.name,
                "provider": provider,
                "file_format": file_format,
                "batch_id": batch_id,
                "record_count": record_count,
            },
        )

        # Get the file_id (auto-increment). We can also use LAST_INSERT_ID but safer to select.
        file_id_row = conn.execute(
            text(
                """
                SELECT file_id FROM bronze_raw_provider_files
                WHERE source_file = :source_file AND provider = :provider
                """
            ),
            {"source_file": file_path.name, "provider": provider},
        ).fetchone()
        file_id = file_id_row[0] if file_id_row else None

        # Insert raw records
        records = []
        for _, row in df.iterrows():
            raw_record = row.to_dict()
            records.append(
                {
                    "file_id": file_id,
                    "transaction_id": raw_record.get("transaction_id") or raw_record.get("payment_id") or raw_record.get("transactionId"),
                    "transaction_timestamp": str(
                        raw_record.get("timestamp") or raw_record.get("created_at") or raw_record.get("date")
                    ),
                    "provider": provider,
                    "merchant_id": raw_record.get("merchant_id") or raw_record.get("merchant"),
                    "amount": str(raw_record.get("amount") or raw_record.get("value")),
                    "currency": raw_record.get("currency"),
                    "status": raw_record.get("status") or raw_record.get("payment_status") or raw_record.get("result"),
                    "source_file": file_path.name,
                    "batch_id": batch_id,
                    "raw_record": json.dumps(raw_record, default=str),
                }
            )

        if records:
            conn.execute(
                text(
                    """
                    INSERT INTO bronze_provider_transactions
                        (file_id, transaction_id, transaction_timestamp, provider, merchant_id,
                         amount, currency, status, source_file, batch_id, raw_record)
                    VALUES
                        (:file_id, :transaction_id, :transaction_timestamp, :provider, :merchant_id,
                         :amount, :currency, :status, :source_file, :batch_id, :raw_record)
                    """
                ),
                records,
            )

    return {
        "source_file": file_path.name,
        "provider": provider,
        "batch_id": batch_id,
        "record_count": record_count,
        "records_rejected": 0,
        "status": "processing",
    }


def mark_file_processed(processed: dict, engine) -> None:
    """Record a file as successfully processed in the idempotency log."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO pipeline_processed_files
                    (source_file, provider, batch_id, records_loaded, records_rejected, status)
                VALUES
                    (:source_file, :provider, :batch_id, :records_loaded, :records_rejected, 'success')
                ON DUPLICATE KEY UPDATE
                    records_loaded = VALUES(records_loaded),
                    records_rejected = VALUES(records_rejected),
                    status = VALUES(status),
                    loaded_at = CURRENT_TIMESTAMP
                """
            ),
            {
                "source_file": processed["source_file"],
                "provider": processed["provider"],
                "batch_id": processed["batch_id"],
                "records_loaded": processed["records_loaded"],
                "records_rejected": processed["records_rejected"],
            },
        )


def load_bronze(raw_dir: Path, batch_id: str | None = None, force: bool = False) -> list[dict]:
    """Load all raw provider files into the Bronze layer.

    Returns a list of per-file processing metadata.
    """
    engine = get_engine()
    batch_id = batch_id or datetime.now().strftime(BATCH_ID_FORMAT)

    provider_dirs = {
        "provider_a": raw_dir / "provider_a",
        "provider_b": raw_dir / "provider_b",
        "provider_c": raw_dir / "provider_c",
    }

    processed_files = []

    for provider, directory in provider_dirs.items():
        if not directory.exists():
            print(f"Warning: {directory} does not exist. Skipping.")
            continue

        for file_path in sorted(directory.iterdir()):
            if file_path.suffix.lower() not in (".csv", ".json"):
                continue

            if not force and is_file_already_processed(file_path.name, provider, engine):
                print(f"Skipping already processed file: {file_path.name}")
                continue

            print(f"Loading Bronze: {file_path} ...")
            processed = load_file_to_bronze(file_path, provider, batch_id, engine)
            processed_files.append(processed)

    return processed_files


def update_processed_files(processed_files: list[dict], records_loaded: dict, records_rejected: dict) -> None:
    """Update the idempotency log after Silver cleaning is complete."""
    engine = get_engine()
    for processed in processed_files:
        key = (processed["source_file"], processed["provider"])
        processed["records_loaded"] = records_loaded.get(key, 0)
        processed["records_rejected"] = records_rejected.get(key, 0)
        mark_file_processed(processed, engine)


def main() -> None:
    parser = argparse.ArgumentParser(description="Load raw provider files into Bronze")
    parser.add_argument("--source", type=Path, default=RAW_DIR, help="Directory containing raw provider files")
    parser.add_argument("--batch-id", type=str, default=None, help="Batch identifier")
    parser.add_argument("--force", action="store_true", help="Reprocess already processed files")
    args = parser.parse_args()

    load_bronze(args.source, batch_id=args.batch_id, force=args.force)


if __name__ == "__main__":
    main()
