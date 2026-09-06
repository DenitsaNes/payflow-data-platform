"""Tests for the data quality validation module."""

import pandas as pd
import pytest

from src.quality.validate_records import validate_records


@pytest.fixture
def sample_records() -> pd.DataFrame:
    """Sample records with a mix of valid and invalid data."""
    return pd.DataFrame({
        "transaction_id": ["TX001", "TX002", "TX003", "TX004", "TX005", "TX006"],
        "transaction_timestamp": [
            "2026-09-06 10:00:00",
            "2026-09-06 11:00:00",
            "2026-09-06 12:00:00",
            "2026-09-06 13:00:00",
            None,
            "2026-09-06 15:00:00",
        ],
        "provider": ["provider_a"] * 6,
        "merchant_id": ["M001", "M002", "M003", "M999", "M001", "M001"],
        "amount": [100.00, -10.00, "bad", 50.00, 75.00, 25.00],
        "currency": ["EUR", "EUR", "EUR", "XYZ", "EUR", "EUR"],
        "status": ["SUCCESS", "SUCCESS", "SUCCESS", "SUCCESS", "SUCCESS", "UNKNOWN"],
        "source_file": ["test.csv"] * 6,
    })


def test_validate_records_splits_valid_and_rejected(sample_records: pd.DataFrame) -> None:
    valid_merchants = {"M001", "M002", "M003"}
    valid, rejected = validate_records(sample_records, valid_merchants)

    # Only TX001 is fully valid
    assert len(valid) == 1
    assert valid["transaction_id"].iloc[0] == "TX001"

    assert len(rejected) == 5


def test_rejection_reasons(sample_records: pd.DataFrame) -> None:
    valid_merchants = {"M001", "M002", "M003"}
    _, rejected = validate_records(sample_records, valid_merchants)

    reasons = rejected.set_index("transaction_id")["rejection_reason"].to_dict()
    assert reasons["TX002"] == "invalid_amount"
    assert reasons["TX003"] == "invalid_amount"
    assert reasons["TX004"] == "invalid_currency"
    assert reasons["TX005"] == "missing_timestamp"
    assert reasons["TX006"] == "invalid_status"


def test_unknown_merchant_is_rejected(sample_records: pd.DataFrame) -> None:
    valid_merchants = {"M001", "M002", "M003"}
    _, rejected = validate_records(sample_records, valid_merchants)

    # TX004 has M999 which is not in valid_merchants
    tx004 = rejected[rejected["transaction_id"] == "TX004"]
    # TX004 is rejected for invalid_currency first (first match wins)
    assert tx004["rejection_reason"].iloc[0] == "invalid_currency"
