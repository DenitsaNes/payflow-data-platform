"""Tests for the ingestion module."""

import json
from pathlib import Path

import pandas as pd
import pytest

from src.ingestion.ingest_providers import process_provider


@pytest.fixture
def provider_a_file(tmp_path: Path) -> Path:
    """Create a temporary Provider A CSV file."""
    file_path = tmp_path / "provider_a_test.csv"
    file_path.write_text(
        "transaction_id,merchant_id,amount,currency,status,timestamp\n"
        "TX001,M001,125.50,EUR,COMPLETED,2026-09-06 10:32:11\n"
        "TX002,M002,80.00,EUR,FAILED,2026-09-06 11:00:00\n"
    )
    return file_path


@pytest.fixture
def provider_b_file(tmp_path: Path) -> Path:
    """Create a temporary Provider B JSON file."""
    file_path = tmp_path / "provider_b_test.json"
    records = [
        {
            "payment_id": "TX001",
            "merchant": "M001",
            "value": 125.50,
            "currency": "EUR",
            "payment_status": "SUCCESS",
            "created_at": "2026-09-06T10:32:11Z",
        },
        {
            "payment_id": "TX003",
            "merchant": "M003",
            "value": 200.00,
            "currency": "EUR",
            "payment_status": "SUCCESS",
            "created_at": "2026-09-06T12:00:00Z",
        },
    ]
    file_path.write_text(json.dumps(records))
    return file_path


@pytest.fixture
def provider_c_file(tmp_path: Path) -> Path:
    """Create a temporary Provider C CSV file."""
    file_path = tmp_path / "provider_c_test.csv"
    file_path.write_text(
        "transactionId,merchant,amount,currency,result,date\n"
        "TX001,M001,125.50,EUR,completed,2026-09-06T10:32:11Z\n"
    )
    return file_path


def test_process_provider_a_normalizes_columns(provider_a_file: Path) -> None:
    df = process_provider(provider_a_file, "provider_a")

    expected_columns = {
        "transaction_id",
        "transaction_timestamp",
        "provider",
        "merchant_id",
        "amount",
        "currency",
        "status",
        "source_file",
    }
    assert set(df.columns) == expected_columns
    assert len(df) == 2


def test_process_provider_a_normalizes_status(provider_a_file: Path) -> None:
    df = process_provider(provider_a_file, "provider_a")

    # COMPLETED should become SUCCESS
    assert df["status"].tolist() == ["SUCCESS", "FAILED"]


def test_process_provider_b_normalizes_columns(provider_b_file: Path) -> None:
    df = process_provider(provider_b_file, "provider_b")

    assert "payment_id" not in df.columns
    assert "transaction_id" in df.columns
    assert len(df) == 2


def test_process_provider_c_normalizes_columns(provider_c_file: Path) -> None:
    df = process_provider(provider_c_file, "provider_c")

    assert "transactionId" not in df.columns
    assert "transaction_id" in df.columns
    assert df["status"].iloc[0] == "SUCCESS"


def test_amount_coerced_to_numeric(tmp_path: Path) -> None:
    file_path = tmp_path / "provider_c_bad.csv"
    file_path.write_text(
        "transactionId,merchant,amount,currency,result,date\n"
        "TX001,M001,one hundred,EUR,completed,2026-09-06T10:32:11Z\n"
        "TX002,M002,50.00,EUR,completed,2026-09-06T11:00:00Z\n"
    )

    df = process_provider(file_path, "provider_c")

    # Bad amount becomes NaN
    assert pd.isna(df["amount"].iloc[0])
    assert df["amount"].iloc[1] == 50.00
