#!/usr/bin/env python3
"""
PayFlow — Synthetic Data Generator (production-like dataset)

Generates realistic payment transaction data for portfolio demonstration:
- 100 merchants
- 30 days of data (September 2026)
- Configurable internal transactions (default 10,000)
- Matching gateway transactions from 3 providers with different schemas
- Realistic data-quality issues injected deliberately into provider records:
    * duplicates
    * amount mismatches
    * status mismatches
    * missing-from-gateway records
    * missing-internal (gateway-only) records
    * malformed amounts
    * invalid currencies
    * unknown merchants
    * missing transaction IDs
    * missing merchant IDs
    * negative amounts
    * malformed timestamps
    * future timestamps
    * invalid statuses

Run with:
    python src/utils/generate_data.py
    python src/utils/generate_data.py --num-transactions 100000
"""

import argparse
import csv
import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from src.utils.config import MAX_TRANSACTION_DATE

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path("data/generated")
RAW_OUTPUT_DIR = OUTPUT_DIR / "raw"
NUM_MERCHANTS = 100
NUM_TRANSACTIONS = 10_000
CURRENCY = "EUR"
START_DATE = datetime(2026, 9, 1)
END_DATE = datetime(2026, 9, 30)
MIN_AMOUNT = 10.0
MAX_AMOUNT = 500.0

# Percentages must sum to ~100
STATUS_WEIGHTS = {
    "SUCCESS": 0.85,
    "FAILED": 0.10,
    "REFUNDED": 0.05,
}

# How often each provider reports a given internal transaction
PROVIDER_REPORT_RATES = {
    "provider_a": 0.95,
    "provider_b": 0.92,
    "provider_c": 0.88,
}

# Error injection rates (applied only when a provider does report the tx)
ERROR_RATES = {
    "amount_mismatch": 0.02,
    "status_mismatch": 0.02,
    "duplicate": 0.01,
    "late_arrival": 0.03,
    "missing_transaction_id": 0.005,
    "missing_merchant_id": 0.005,
    "negative_amount": 0.005,
    "malformed_timestamp": 0.005,
    "future_timestamp": 0.005,
    "invalid_currency": 0.005,
    "invalid_status": 0.005,
    "unknown_merchant": 0.005,
}

# Extra gateway-only transactions (missing from internal)
EXTRA_GATEWAY_TRANSACTIONS = 150

random.seed(42)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def generate_merchant_id(index: int) -> str:
    return f"M{index + 1:03d}"


def generate_transaction_id(index: int) -> str:
    return f"TX{index + 1:08d}"


def random_timestamp(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def round_amount(value: float) -> float:
    return round(value, 2)


def internal_status_to_provider(status: str, provider: str) -> str:
    mapping = {
        "provider_a": {
            "SUCCESS": "COMPLETED",
            "FAILED": "FAILED",
            "REFUNDED": "REFUNDED",
        },
        "provider_b": {
            "SUCCESS": "SUCCESS",
            "FAILED": "FAILED",
            "REFUNDED": "DECLINED",
        },
        "provider_c": {
            "SUCCESS": "completed",
            "FAILED": "failed",
            "REFUNDED": "declined",
        },
    }
    return mapping[provider][status]


def format_timestamp_for_provider(ts: datetime, provider: str) -> str:
    if provider == "provider_a":
        return ts.strftime("%Y-%m-%d %H:%M:%S")
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def provider_status_from_base(base_status: str, provider: str) -> str:
    """Map a canonical internal status to the provider-specific status.

    If the base status is not a canonical value (e.g. an injected invalid status),
    keep it as-is so validation can reject it.
    """
    canonical = {"SUCCESS", "FAILED", "REFUNDED"}
    if base_status not in canonical:
        return base_status
    return internal_status_to_provider(base_status, provider)


def inject_quality_issue(record: dict, provider: str) -> dict:
    """
    Inject a single realistic data-quality issue into a provider record.
    Returns the mutated record.
    """
    issue = random.choices(
        population=[
            "missing_transaction_id",
            "missing_merchant_id",
            "negative_amount",
            "malformed_timestamp",
            "future_timestamp",
            "invalid_currency",
            "invalid_status",
            "unknown_merchant",
        ],
        weights=[
            ERROR_RATES["missing_transaction_id"],
            ERROR_RATES["missing_merchant_id"],
            ERROR_RATES["negative_amount"],
            ERROR_RATES["malformed_timestamp"],
            ERROR_RATES["future_timestamp"],
            ERROR_RATES["invalid_currency"],
            ERROR_RATES["invalid_status"],
            ERROR_RATES["unknown_merchant"],
        ],
        k=1,
    )[0]

    if issue == "missing_transaction_id":
        record["transaction_id"] = ""
    elif issue == "missing_merchant_id":
        record["merchant_id"] = ""
    elif issue == "negative_amount":
        record["amount"] = -abs(record["amount"])
    elif issue == "malformed_timestamp":
        record["timestamp"] = random.choice(["not-a-date", "2026-13-45 25:00:00", ""])
    elif issue == "future_timestamp":
        future = MAX_TRANSACTION_DATE + timedelta(days=random.randint(1, 90))
        record["timestamp"] = future
    elif issue == "invalid_currency":
        record["currency"] = random.choice(["XYZ", "ABC", "000"])
    elif issue == "invalid_status":
        record["status"] = random.choice(["HOLD", "UNKNOWN", "PENDING_REVIEW"])
    elif issue == "unknown_merchant":
        record["merchant_id"] = "M999"

    return record


# ---------------------------------------------------------------------------
# Generate merchants
# ---------------------------------------------------------------------------

def generate_merchants() -> list[dict]:
    countries = ["BG", "DE", "GB", "FR", "IT", "ES", "NL", "RO", "PL", "CZ"]
    names = [
        "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta",
        "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi", "Omicron", "Pi", "Rho",
        "Sigma", "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega", "Nova",
        "Pulse", "Orbit", "Flux", "Spark", "Vertex", "Helix", "Prism", "Axiom",
    ]

    merchants = []
    for i in range(NUM_MERCHANTS):
        name = f"{random.choice(names)} {random.choice(['Shop', 'Store', 'Market', 'Hub', 'Pay'])} {i + 1}"
        merchants.append({
            "merchant_id": generate_merchant_id(i),
            "merchant_name": name,
            "country": random.choice(countries),
            "contract_start_date": datetime(random.randint(2023, 2025), random.randint(1, 12), 1).strftime("%Y-%m-%d"),
            "fee_variable_pct": 0.0150,
            "fee_fixed_amount": 0.25,
            "is_active": True,
        })
    return merchants


# ---------------------------------------------------------------------------
# Generate internal transactions
# ---------------------------------------------------------------------------

def generate_internal_transactions(merchants: list[dict]) -> list[dict]:
    statuses = list(STATUS_WEIGHTS.keys())
    weights = list(STATUS_WEIGHTS.values())

    transactions = []
    for i in range(NUM_TRANSACTIONS):
        merchant = random.choice(merchants)
        ts = random_timestamp(START_DATE, END_DATE)
        amount = round_amount(random.uniform(MIN_AMOUNT, MAX_AMOUNT))
        status = random.choices(statuses, weights=weights)[0]

        transactions.append({
            "transaction_id": generate_transaction_id(i),
            "transaction_timestamp": ts,
            "merchant_id": merchant["merchant_id"],
            "amount": amount,
            "currency": CURRENCY,
            "status": status,
            "source_system": "internal",
            "source_file": "internal_transactions_2026_09.csv",
        })

    # Sort by timestamp for realism
    transactions.sort(key=lambda x: x["transaction_timestamp"])
    return transactions


# ---------------------------------------------------------------------------
# Generate gateway transactions from providers
# ---------------------------------------------------------------------------

def generate_gateway_transactions(
    internal_transactions: list[dict], merchants: list[dict]
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """
    Returns provider_a, provider_b, provider_c records and a list of
    gateway transactions in canonical form.
    """
    provider_a_records = []
    provider_b_records = []
    provider_c_records = []
    gateway_records = []

    merchant_ids = {m["merchant_id"] for m in merchants}

    for tx in internal_transactions:
        for provider, report_rate in PROVIDER_REPORT_RATES.items():
            # Decide if this provider reports the transaction
            if random.random() > report_rate:
                continue

            amount = tx["amount"]
            provider_status = internal_status_to_provider(tx["status"], provider)
            canonical_status = tx["status"]
            ts = tx["transaction_timestamp"]
            tx_id = tx["transaction_id"]
            merchant_id = tx["merchant_id"]

            # Inject amount mismatch
            if random.random() < ERROR_RATES["amount_mismatch"]:
                amount = round_amount(amount + random.uniform(-5.0, 5.0))
                if amount < 0:
                    amount = round_amount(abs(amount))

            # Inject status mismatch into canonical status (rare)
            if random.random() < ERROR_RATES["status_mismatch"]:
                if canonical_status == "SUCCESS":
                    canonical_status = "FAILED"
                elif canonical_status == "FAILED":
                    canonical_status = "SUCCESS"
                elif canonical_status == "REFUNDED":
                    canonical_status = "SUCCESS"

            # Inject late arrival
            if random.random() < ERROR_RATES["late_arrival"]:
                ts = ts + timedelta(minutes=random.randint(10, 120))

            # Base canonical record used for gateway and raw transformation
            base_record = {
                "transaction_id": tx_id,
                "merchant_id": merchant_id,
                "amount": amount,
                "currency": CURRENCY,
                "status": canonical_status,
                "timestamp": ts,
            }

            # Inject realistic quality issues (only a small share of records)
            total_new_error_rate = sum(ERROR_RATES[k] for k in [
                "missing_transaction_id", "missing_merchant_id", "negative_amount",
                "malformed_timestamp", "future_timestamp", "invalid_currency",
                "invalid_status", "unknown_merchant",
            ])
            if random.random() < total_new_error_rate:
                base_record = inject_quality_issue(base_record, provider)

            source_file = f"{provider}_2026_09_{ts.day:02d}.{'csv' if provider != 'provider_b' else 'json'}"

            # Build provider-specific records using the (possibly mutated) base record
            if provider == "provider_a":
                record = {
                    "transaction_id": base_record["transaction_id"],
                    "merchant_id": base_record["merchant_id"],
                    "amount": base_record["amount"],
                    "currency": base_record["currency"],
                    "status": provider_status_from_base(base_record["status"], provider),
                    "timestamp": format_timestamp_for_provider(base_record["timestamp"], provider) if isinstance(base_record["timestamp"], datetime) else base_record["timestamp"],
                    "source_file": source_file,
                }
                provider_a_records.append(record)

            elif provider == "provider_b":
                record = {
                    "payment_id": base_record["transaction_id"],
                    "merchant": base_record["merchant_id"],
                    "value": base_record["amount"],
                    "currency": base_record["currency"],
                    "payment_status": provider_status_from_base(base_record["status"], provider),
                    "created_at": format_timestamp_for_provider(base_record["timestamp"], provider) if isinstance(base_record["timestamp"], datetime) else base_record["timestamp"],
                    "source_file": source_file,
                }
                provider_b_records.append(record)

            elif provider == "provider_c":
                record = {
                    "transactionId": base_record["transaction_id"],
                    "merchant": base_record["merchant_id"],
                    "amount": base_record["amount"],
                    "currency": base_record["currency"],
                    "result": provider_status_from_base(base_record["status"], provider),
                    "date": format_timestamp_for_provider(base_record["timestamp"], provider) if isinstance(base_record["timestamp"], datetime) else base_record["timestamp"],
                    "source_file": source_file,
                }
                provider_c_records.append(record)

            # Canonical gateway record
            gateway_records.append({
                "transaction_id": base_record["transaction_id"],
                "provider": provider,
                "transaction_timestamp": base_record["timestamp"] if isinstance(base_record["timestamp"], datetime) else None,
                "merchant_id": base_record["merchant_id"],
                "amount": base_record["amount"],
                "currency": base_record["currency"],
                "status": base_record["status"],
                "source_file": source_file,
            })

            # Inject duplicate for this provider sometimes
            if random.random() < ERROR_RATES["duplicate"]:
                dup_ts = ts + timedelta(seconds=random.randint(1, 60))
                dup_source = f"{provider}_2026_09_{dup_ts.day:02d}.{'csv' if provider != 'provider_b' else 'json'}"
                gateway_records.append({
                    "transaction_id": base_record["transaction_id"],
                    "provider": provider,
                    "transaction_timestamp": dup_ts,
                    "merchant_id": base_record["merchant_id"],
                    "amount": base_record["amount"],
                    "currency": base_record["currency"],
                    "status": base_record["status"],
                    "source_file": dup_source,
                })
                if provider == "provider_a":
                    provider_a_records.append({
                        "transaction_id": base_record["transaction_id"],
                        "merchant_id": base_record["merchant_id"],
                        "amount": base_record["amount"],
                        "currency": base_record["currency"],
                        "status": record["status"],
                        "timestamp": format_timestamp_for_provider(dup_ts, provider),
                        "source_file": dup_source,
                    })
                elif provider == "provider_b":
                    provider_b_records.append({
                        "payment_id": base_record["transaction_id"],
                        "merchant": base_record["merchant_id"],
                        "value": base_record["amount"],
                        "currency": base_record["currency"],
                        "payment_status": record["payment_status"],
                        "created_at": format_timestamp_for_provider(dup_ts, provider),
                        "source_file": dup_source,
                    })
                elif provider == "provider_c":
                    provider_c_records.append({
                        "transactionId": base_record["transaction_id"],
                        "merchant": base_record["merchant_id"],
                        "amount": base_record["amount"],
                        "currency": base_record["currency"],
                        "result": record["result"],
                        "date": format_timestamp_for_provider(dup_ts, provider),
                        "source_file": dup_source,
                    })

    # Generate extra gateway-only transactions (missing from internal)
    for _ in range(EXTRA_GATEWAY_TRANSACTIONS):
        merchant = random.choice(merchants)
        ts = random_timestamp(START_DATE, END_DATE)
        amount = round_amount(random.uniform(MIN_AMOUNT, MAX_AMOUNT))
        status = random.choices(["SUCCESS", "FAILED"], weights=[0.9, 0.1])[0]
        tx_id = f"TX{uuid.uuid4().hex[:8].upper()}"

        provider = random.choice(list(PROVIDER_REPORT_RATES.keys()))
        provider_status = internal_status_to_provider(status, provider)
        source_file = f"{provider}_2026_09_{ts.day:02d}.{'csv' if provider != 'provider_b' else 'json'}"

        if provider == "provider_a":
            provider_a_records.append({
                "transaction_id": tx_id,
                "merchant_id": merchant["merchant_id"],
                "amount": amount,
                "currency": CURRENCY,
                "status": provider_status,
                "timestamp": format_timestamp_for_provider(ts, provider),
                "source_file": source_file,
            })
        elif provider == "provider_b":
            provider_b_records.append({
                "payment_id": tx_id,
                "merchant": merchant["merchant_id"],
                "value": amount,
                "currency": CURRENCY,
                "payment_status": provider_status,
                "created_at": format_timestamp_for_provider(ts, provider),
                "source_file": source_file,
            })
        elif provider == "provider_c":
            provider_c_records.append({
                "transactionId": tx_id,
                "merchant": merchant["merchant_id"],
                "amount": amount,
                "currency": CURRENCY,
                "result": provider_status,
                "date": format_timestamp_for_provider(ts, provider),
                "source_file": source_file,
            })

        gateway_records.append({
            "transaction_id": tx_id,
            "provider": provider,
            "transaction_timestamp": ts,
            "merchant_id": merchant["merchant_id"],
            "amount": amount,
            "currency": CURRENCY,
            "status": status,
            "source_file": source_file,
        })

    return provider_a_records, provider_b_records, provider_c_records, gateway_records


# ---------------------------------------------------------------------------
# Write CSV / JSON files
# ---------------------------------------------------------------------------

def write_provider_a_csv(records: list[dict]) -> None:
    provider_dir = RAW_OUTPUT_DIR / "provider_a"
    provider_dir.mkdir(parents=True, exist_ok=True)
    path = provider_dir / "provider_a_2026_09.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["transaction_id", "merchant_id", "amount", "currency", "status", "timestamp", "source_file"],
        )
        writer.writeheader()
        for r in records:
            writer.writerow({
                "transaction_id": r["transaction_id"],
                "merchant_id": r["merchant_id"],
                "amount": r["amount"],
                "currency": r["currency"],
                "status": r["status"],
                "timestamp": r["timestamp"],
                "source_file": r["source_file"],
            })
    print(f"Wrote {len(records)} records to {path}")


def write_provider_b_json(records: list[dict]) -> None:
    provider_dir = RAW_OUTPUT_DIR / "provider_b"
    provider_dir.mkdir(parents=True, exist_ok=True)
    path = provider_dir / "provider_b_2026_09.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    print(f"Wrote {len(records)} records to {path}")


def write_provider_c_csv(records: list[dict]) -> None:
    provider_dir = RAW_OUTPUT_DIR / "provider_c"
    provider_dir.mkdir(parents=True, exist_ok=True)
    path = provider_dir / "provider_c_2026_09.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["transactionId", "merchant", "amount", "currency", "result", "date", "source_file"],
        )
        writer.writeheader()
        for r in records:
            writer.writerow({
                "transactionId": r["transactionId"],
                "merchant": r["merchant"],
                "amount": r["amount"],
                "currency": r["currency"],
                "result": r["result"],
                "date": r["date"],
                "source_file": r["source_file"],
            })
    print(f"Wrote {len(records)} records to {path}")


def write_internal_transactions_csv(records: list[dict]) -> None:
    provider_dir = RAW_OUTPUT_DIR / "internal"
    provider_dir.mkdir(parents=True, exist_ok=True)
    path = provider_dir / "internal_transactions_2026_09.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["transaction_id", "merchant_id", "amount", "currency", "status", "timestamp", "source_system", "source_file"],
        )
        writer.writeheader()
        for r in records:
            row = {
                "transaction_id": r["transaction_id"],
                "merchant_id": r["merchant_id"],
                "amount": r["amount"],
                "currency": r["currency"],
                "status": r["status"],
                "timestamp": r["transaction_timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                "source_system": r["source_system"],
                "source_file": r["source_file"],
            }
            writer.writerow(row)
    print(f"Wrote {len(records)} records to {path}")


def write_merchants_csv(records: list[dict]) -> None:
    path = OUTPUT_DIR / "merchants.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["merchant_id", "merchant_name", "country", "contract_start_date", "fee_variable_pct", "fee_fixed_amount", "is_active"],
        )
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {len(records)} records to {path}")


# ---------------------------------------------------------------------------
# Write SQL seed files
# ---------------------------------------------------------------------------

def chunk_list(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def write_seed_data_sql(merchants: list[dict], internal_transactions: list[dict]) -> None:
    path = OUTPUT_DIR / "seed_data.sql"
    with path.open("w", encoding="utf-8") as f:
        f.write("-- PayFlow — Large synthetic seed data\n")
        f.write("USE payflow;\n\n")

        # Merchants
        f.write("-- Seed merchants\n")
        f.write("INSERT IGNORE INTO warehouse_dim_merchant (merchant_id, merchant_name, country, contract_start_date, fee_variable_pct, fee_fixed_amount) VALUES\n")
        for i, m in enumerate(merchants):
            comma = "," if i < len(merchants) - 1 else ";"
            f.write(
                f"('{m['merchant_id']}', '{m['merchant_name'].replace(chr(39), chr(39)+chr(39))}', "
                f"'{m['country']}', '{m['contract_start_date']}', {m['fee_variable_pct']}, {m['fee_fixed_amount']}){comma}\n"
            )

        # Dates
        f.write("\n-- Seed dates for September 2026\n")
        f.write("INSERT IGNORE INTO warehouse_dim_date (date_key, full_date, year, month, day, quarter, day_of_week, is_weekend) VALUES\n")
        current = START_DATE
        date_rows = []
        while current <= END_DATE:
            wd = current.weekday()  # Monday=0, Sunday=6 (matches MySQL WEEKDAY)
            date_rows.append(
                f"({current.strftime('%Y%m%d')}, '{current.strftime('%Y-%m-%d')}', "
                f"{current.year}, {current.month}, {current.day}, {((current.month - 1) // 3) + 1}, "
                f"{wd}, {str(wd in [5, 6]).upper()})"
            )
            current += timedelta(days=1)
        for i, row in enumerate(date_rows):
            comma = "," if i < len(date_rows) - 1 else ";"
            f.write(f"{row}{comma}\n")

        # Internal transactions
        f.write("\n-- Seed internal transactions\n")
        f.write("TRUNCATE TABLE reconciliation_internal_transactions;\n")
        for chunk in chunk_list(internal_transactions, 500):
            f.write("INSERT INTO reconciliation_internal_transactions (transaction_id, transaction_timestamp, merchant_id, amount, currency, status, source_system, source_file) VALUES\n")
            for i, tx in enumerate(chunk):
                comma = "," if i < len(chunk) - 1 else ";"
                ts = tx["transaction_timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                f.write(
                    f"('{tx['transaction_id']}', '{ts}', '{tx['merchant_id']}', "
                    f"{tx['amount']}, '{tx['currency']}', '{tx['status']}', "
                    f"'{tx['source_system']}', '{tx['source_file']}'){comma}\n"
                )

    print(f"Wrote seed SQL to {path}")


def write_seed_gateway_sql(gateway_records: list[dict]) -> None:
    path = OUTPUT_DIR / "seed_gateway_transactions.sql"
    with path.open("w", encoding="utf-8") as f:
        f.write("-- PayFlow — Large synthetic gateway transactions (directly into Silver)\n")
        f.write("USE payflow;\n\n")
        f.write("TRUNCATE TABLE silver_transactions;\n")

        # Only keep records with valid transaction_id, merchant_id, timestamp, and numeric amount
        # because Silver is the validated layer. Simpler: keep all and let the Silver cleaner handle them.
        # For the seed we insert into Silver directly, so filter out obvious rejects.
        valid_for_silver = []
        for r in gateway_records:
            if (
                r["transaction_id"]
                and r["merchant_id"]
                and isinstance(r["transaction_timestamp"], datetime)
                and isinstance(r["amount"], (int, float))
                and r["amount"] >= 0
                and r["currency"] in {"EUR", "USD", "GBP"}
                and r["status"] in {"SUCCESS", "FAILED", "REFUNDED", "PENDING"}
                and r["merchant_id"].startswith("M")
            ):
                valid_for_silver.append(r)

        for chunk in chunk_list(valid_for_silver, 500):
            f.write("INSERT IGNORE INTO silver_transactions (transaction_id, transaction_timestamp, source_system, provider, merchant_id, amount, currency, status, source_file, batch_id) VALUES\n")
            for i, r in enumerate(chunk):
                comma = "," if i < len(chunk) - 1 else ";"
                ts = r["transaction_timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                source_file = r["source_file"].replace("'", "''")
                f.write(
                    f"('{r['transaction_id']}', '{ts}', '{r['provider']}', '{r['provider']}', "
                    f"'{r['merchant_id']}', {r['amount']}, '{r['currency']}', "
                    f"'{r['status']}', '{source_file}', 'generated_seed'){comma}\n"
                )

    print(f"Wrote gateway seed SQL to {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic PayFlow transaction data"
    )
    parser.add_argument(
        "--num-transactions",
        type=int,
        default=NUM_TRANSACTIONS,
        help="Number of internal transactions to generate (default: 10,000)",
    )
    args = parser.parse_args()

    global NUM_TRANSACTIONS, EXTRA_GATEWAY_TRANSACTIONS
    NUM_TRANSACTIONS = args.num_transactions
    EXTRA_GATEWAY_TRANSACTIONS = max(150, int(NUM_TRANSACTIONS * 0.015))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Generating {NUM_TRANSACTIONS:,} internal transactions...")
    merchants = generate_merchants()

    print("Generating internal transactions...")
    internal_transactions = generate_internal_transactions(merchants)

    print("Generating provider transactions...")
    provider_a, provider_b, provider_c, gateway = generate_gateway_transactions(
        internal_transactions, merchants
    )

    print("\nWriting files...")
    write_merchants_csv(merchants)
    write_internal_transactions_csv(internal_transactions)
    write_provider_a_csv(provider_a)
    write_provider_b_json(provider_b)
    write_provider_c_csv(provider_c)

    print("\nWriting SQL seed files...")
    write_seed_data_sql(merchants, internal_transactions)
    write_seed_gateway_sql(gateway)

    print("\nDone!")
    print(f"  Merchants: {len(merchants)}")
    print(f"  Internal transactions: {len(internal_transactions)}")
    print(f"  Provider A records: {len(provider_a)}")
    print(f"  Provider B records: {len(provider_b)}")
    print(f"  Provider C records: {len(provider_c)}")
    print(f"  Gateway records (canonical): {len(gateway)}")


if __name__ == "__main__":
    main()
