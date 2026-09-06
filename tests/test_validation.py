"""Tests for the data quality validation module."""

from datetime import datetime, timedelta

import pandas as pd
import pytest

from src.quality.validate_records import clean_and_validate, validate_records


@pytest.fixture
def sample_records() -> pd.DataFrame:
    """Sample records with a mix of valid and invalid data."""
    return pd.DataFrame({
        "transaction_id": ["TX001", "TX002", "TX003", "TX004", "TX005", "TX006", "TX007", "TX008", "TX009", "TX010"],
        "transaction_timestamp": [
            "2026-09-06 10:00:00",
            "2026-09-06 11:00:00",
            "2026-09-06 12:00:00",
            "2026-09-06 13:00:00",
            None,
            "2026-09-06 15:00:00",
            "2026-09-06 16:00:00",
            "not-a-date",
            (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S"),
            "2026-09-06 17:00:00",
        ],
        "provider": ["provider_a"] * 10,
        "merchant_id": ["M001", "M002", "M003", "M999", "M001", "M001", "", "M001", "M001", "M999"],
        "amount": [100.00, -10.00, "bad", 50.00, 75.00, 25.00, 30.00, 35.00, 40.00, 45.00],
        "currency": ["EUR", "EUR", "EUR", "XYZ", "EUR", "EUR", "EUR", "EUR", "EUR", "EUR"],
        "status": ["SUCCESS", "SUCCESS", "SUCCESS", "SUCCESS", "SUCCESS", "UNKNOWN", "SUCCESS", "SUCCESS", "SUCCESS", "SUCCESS"],
        "source_file": ["test.csv"] * 10,
    })


def test_validate_records_splits_valid_and_rejected(sample_records: pd.DataFrame) -> None:
    valid_merchants = {"M001", "M002", "M003"}
    valid, rejected = clean_and_validate(sample_records, valid_merchants)

    # TX001 and TX007? TX007 has missing merchant id -> rejected. TX001 is fully valid.
    assert len(valid) == 1
    assert valid["transaction_id"].iloc[0] == "TX001"

    assert len(rejected) == 9


def test_rejection_reasons(sample_records: pd.DataFrame) -> None:
    valid_merchants = {"M001", "M002", "M003"}
    _, rejected = clean_and_validate(sample_records, valid_merchants)

    reasons = rejected.set_index("transaction_id")["rejection_reason"].to_dict()
    assert reasons["TX002"] == "negative_amount"
    assert reasons["TX003"] == "invalid_amount"
    assert reasons["TX004"] == "invalid_currency"
    assert reasons["TX005"] == "invalid_timestamp"
    assert reasons["TX006"] == "invalid_status"
    assert reasons["TX007"] == "missing_merchant_id"
    assert reasons["TX008"] == "invalid_timestamp"
    assert reasons["TX009"] == "future_timestamp"
    assert reasons["TX010"] == "unknown_merchant"


def test_unknown_merchant_is_rejected(sample_records: pd.DataFrame) -> None:
    valid_merchants = {"M001", "M002", "M003"}
    _, rejected = clean_and_validate(sample_records, valid_merchants)

    tx004 = rejected[rejected["transaction_id"] == "TX004"]
    # TX004 is rejected for invalid_currency first (first match wins)
    assert tx004["rejection_reason"].iloc[0] == "invalid_currency"


def test_missing_transaction_id_is_rejected() -> None:
    df = pd.DataFrame({
        "transaction_id": ["", "TX002"],
        "transaction_timestamp": ["2026-09-06 10:00:00", "2026-09-06 10:00:00"],
        "provider": ["provider_a", "provider_a"],
        "merchant_id": ["M001", "M001"],
        "amount": [100.0, 100.0],
        "currency": ["EUR", "EUR"],
        "status": ["SUCCESS", "SUCCESS"],
        "source_file": ["test.csv", "test.csv"],
    })
    valid_merchants = {"M001"}
    _, rejected = clean_and_validate(df, valid_merchants)
    assert len(rejected) == 1
    assert rejected["rejection_reason"].iloc[0] == "missing_transaction_id"


def test_validate_records_handles_already_parsed_timestamps() -> None:
    df = pd.DataFrame({
        "transaction_id": ["TX001"],
        "transaction_timestamp": [pd.Timestamp("2026-09-06 10:00:00")],
        "provider": ["provider_a"],
        "merchant_id": ["M001"],
        "amount": [100.0],
        "currency": ["EUR"],
        "status": ["SUCCESS"],
        "source_file": ["test.csv"],
    })
    valid_merchants = {"M001"}
    valid, rejected = validate_records(df, valid_merchants)
    assert len(valid) == 1
    assert len(rejected) == 0
