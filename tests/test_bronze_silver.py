"""Tests for Bronze loading and Silver cleaning (idempotency and quarantine)."""

from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import text

from src.transformation.load_bronze import load_bronze
from src.transformation.silver_cleaner import clean_silver
from src.utils.db import get_engine


@pytest.fixture
def raw_dir(tmp_path: Path) -> Path:
    """Create a temporary raw directory with provider files."""
    provider_a_dir = tmp_path / "provider_a"
    provider_a_dir.mkdir(parents=True)
    provider_a_file = provider_a_dir / "provider_a_2026_09_06.csv"
    provider_a_file.write_text(
        "transaction_id,merchant_id,amount,currency,status,timestamp,source_file\n"
        "TX001,M001,100.00,EUR,COMPLETED,2026-09-06 10:00:00,provider_a_2026_09_06.csv\n"
        "TX002,M002,200.00,EUR,FAILED,2026-09-06 11:00:00,provider_a_2026_09_06.csv\n"
        "TX001,M001,100.00,EUR,COMPLETED,2026-09-06 10:00:00,provider_a_2026_09_06.csv\n"
    )

    provider_b_dir = tmp_path / "provider_b"
    provider_b_dir.mkdir(parents=True)
    provider_b_file = provider_b_dir / "provider_b_2026_09_06.json"
    provider_b_file.write_text(
        '[{"payment_id":"TX001","merchant":"M001","value":100.00,"currency":"EUR",'
        '"payment_status":"SUCCESS","created_at":"2026-09-06T10:00:00Z",'
        '"source_file":"provider_b_2026_09_06.json"}]'
    )

    return tmp_path


def reset_tables(engine) -> None:
    """Clear Bronze/Silver tables before a test and seed test merchants."""
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM bronze_provider_transactions"))
        conn.execute(text("DELETE FROM bronze_raw_provider_files"))
        conn.execute(text("DELETE FROM silver_transactions"))
        conn.execute(text("DELETE FROM silver_rejected_transactions"))
        conn.execute(text("DELETE FROM pipeline_processed_files"))
        conn.execute(
            text(
                """
                INSERT IGNORE INTO warehouse_dim_merchant
                    (merchant_id, merchant_name, country, fee_variable_pct, fee_fixed_amount)
                VALUES
                    ('M001', 'Test Merchant 1', 'BG', 0.0150, 0.25),
                    ('M002', 'Test Merchant 2', 'DE', 0.0150, 0.25),
                    ('M003', 'Test Merchant 3', 'FR', 0.0150, 0.25)
                """
            )
        )


def test_bronze_and_silver_flow(raw_dir: Path) -> None:
    engine = get_engine()
    reset_tables(engine)

    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    processed = load_bronze(raw_dir, batch_id=batch_id, force=True)

    assert len(processed) == 2  # provider_a and provider_b files

    with engine.connect() as conn:
        bronze_count = conn.execute(text("SELECT COUNT(*) FROM bronze_provider_transactions")).scalar()
    assert bronze_count == 4  # 3 from A + 1 from B

    valid_count, rejected_count, valid_df, rejected_df = clean_silver(batch_id=batch_id)

    # All records are valid in this fixture
    assert valid_count == 3
    assert rejected_count == 0

    # TX001 from provider_a is duplicated; only one survives
    tx001_a = valid_df[(valid_df["transaction_id"] == "TX001") & (valid_df["provider"] == "provider_a")]
    assert len(tx001_a) == 1


def test_idempotency(raw_dir: Path) -> None:
    engine = get_engine()
    reset_tables(engine)

    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # First run
    load_bronze(raw_dir, batch_id=batch_id, force=True)
    clean_silver(batch_id=batch_id)

    with engine.connect() as conn:
        first_count = conn.execute(text("SELECT COUNT(*) FROM silver_transactions")).scalar()

    # Second run with the same batch_id — Bronze loader should skip unless forced
    load_bronze(raw_dir, batch_id=batch_id, force=False)
    clean_silver(batch_id=batch_id)

    with engine.connect() as conn:
        second_count = conn.execute(text("SELECT COUNT(*) FROM silver_transactions")).scalar()

    assert first_count == second_count, "Silver count should remain stable on rerun"


def test_quarantine_rejects_bad_records(tmp_path: Path) -> None:
    engine = get_engine()
    reset_tables(engine)

    provider_c_dir = tmp_path / "provider_c"
    provider_c_dir.mkdir(parents=True)
    provider_c_file = provider_c_dir / "provider_c_2026_09_06.csv"
    provider_c_file.write_text(
        "transactionId,merchant,amount,currency,result,date,source_file\n"
        "TX001,M001,100.00,EUR,completed,2026-09-06T10:00:00Z,provider_c_2026_09_06.csv\n"
        "TX002,M001,-50.00,EUR,completed,2026-09-06T11:00:00Z,provider_c_2026_09_06.csv\n"
        "TX003,M001,100.00,XYZ,completed,2026-09-06T12:00:00Z,provider_c_2026_09_06.csv\n"
    )

    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    load_bronze(tmp_path, batch_id=batch_id, force=True)
    valid_count, rejected_count, _, rejected_df = clean_silver(batch_id=batch_id)

    assert valid_count == 1
    assert rejected_count == 2

    reasons = set(rejected_df["rejection_reason"].tolist())
    assert "negative_amount" in reasons
    assert "invalid_currency" in reasons
