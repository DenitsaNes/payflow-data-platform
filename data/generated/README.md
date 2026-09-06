# Generated Synthetic Data

This folder contains a large, realistic synthetic dataset for the PayFlow project.

## What was generated

| File | Description | Rows |
|------|-------------|------|
| `merchants.csv` | 100 fake merchants | 100 |
| `internal_transactions_2026_09.csv` | PayFlow internal records | 10,000 |
| `provider_a_2026_09.csv` | Provider A CSV format | ~9,500 |
| `provider_b_2026_09.json` | Provider B JSON format | ~9,200 |
| `provider_c_2026_09.csv` | Provider C CSV format | ~8,800 |
| `seed_data.sql` | SQL to load merchants, dates, internal transactions | — |
| `seed_gateway_transactions.sql` | SQL to load gateway transactions | ~28,000 |

## How it was generated

Run the generator script:

```bash
python src/utils/generate_data.py
```

You can edit the constants at the top of the script to change volume.

## Data-quality issues intentionally included

- **Duplicates** — some transactions appear twice from the same provider.
- **Amount mismatches** — provider reports a different amount than internal.
- **Status mismatches** — provider reports a different status than internal.
- **Missing from gateway** — internal has a transaction no provider reported.
- **Missing internal** — provider reports a transaction internal does not have.
- **Late arrivals** — some timestamps are later than the original.
- **Malformed amounts** — some Provider C records have text instead of numbers.
- **Invalid currencies** — some Provider C records use `XYZ`.
- **Unknown merchants** — some Provider C records use `M999`.

## How to load the large dataset

Make sure your MySQL container is running, then:

```bash
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < data/generated/seed_data.sql
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < data/generated/seed_gateway_transactions.sql
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow < sql/reconciliation/reconcile_transactions.sql
```

Password: `payflow`

Then connect and check:

```bash
mysql -h 127.0.0.1 -P 3307 -u payflow -p payflow
```

```sql
SELECT * FROM warehouse_v_reconciliation_summary;
```

## Notes

- This data is entirely synthetic. No real financial information is used.
- The script uses only Python standard library, so no extra packages are needed.
- You can regenerate with a different random seed by changing `random.seed(42)` in `src/utils/generate_data.py`.
