# PayFlow — Business Requirements Document

## Client

**PayFlow** — a fictional European fintech / payment processing company.

## Current Pain

PayFlow processes payments on behalf of merchants through several external payment gateways. Each provider sends transaction data in a different format and at different times. Finance currently:

- Downloads provider files manually.
- Opens them in spreadsheets.
- Compares them line-by-line against PayFlow's internal transaction system.
- Calculates merchant billing using manual formulas.

This process takes approximately **4 hours per day**, is error-prone, and makes it difficult to detect discrepancies such as missing transactions, duplicate charges, or amount mismatches.

## Stakeholders

| Role | Concern |
|------|---------|
| Finance Team | Accurate daily billing and revenue reporting. |
| Operations Team | Detect failed, duplicated, or mismatched transactions quickly. |
| Data Team | Maintain a clean, queryable historical record of all transactions. |
| Merchants | Receive correct invoices based on actual processed volume. |

## Business Objectives

1. **Automate ingestion** of all provider transaction files.
2. **Standardize** heterogeneous formats into a single model.
3. **Reconcile** provider data against internal transactions automatically.
4. **Detect duplicates**, missing records, amount mismatches, and status mismatches.
5. **Calculate merchant billing** daily using defined fee rules.
6. **Provide a dashboard** for finance and operations monitoring.
7. **Maintain historical data** for auditing and reprocessing.

## Success Criteria

| # | Criterion | How Measured |
|---|-----------|--------------|
| 1 | Manual reconciliation time reduced from 4 hours to under 30 minutes. | Time-tracking comparison. |
| 2 | Discrepancies are identified automatically with clear categories. | Reconciliation report coverage. |
| 3 | Daily billing data is available by 09:00 local time. | Pipeline SLA. |
| 4 | Bad records are quarantined, not silently lost. | Rejected record audit trail. |
| 5 | New payment providers can be added with minimal code changes. | Time to onboard a new provider. |
| 6 | Historical transaction data is retained for at least 2 years. | S3 lifecycle policy. |

## Data Providers

| Provider | Format | Delivery | Notes |
|----------|--------|----------|-------|
| Provider A | CSV | Daily file drop | Standard column names. |
| Provider B | JSON | Daily file drop | Different naming convention. |
| Provider C | CSV | Daily file drop | Mixed-case column names, inconsistent timestamps. |
| Streaming API | JSON | Real-time | Optional near-real-time path. |

## Key Business Questions

The platform must answer:

- How much money was processed today / this month?
- How many transactions succeeded, failed, or were disputed?
- Which transactions are duplicated across providers?
- Which internal transactions are missing from provider reports?
- Which provider-reported transactions are missing from internal records?
- Where do amount or status mismatches exist?
- How much should each merchant be billed?
- What is PayFlow's revenue from transaction fees?
- Are there suspicious discrepancies requiring investigation?

## Fee Structure

PayFlow charges merchants per successful transaction:

- **Variable fee:** 1.5% of transaction amount.
- **Fixed fee:** €0.25 per successful transaction.

Refunds and chargebacks reduce the merchant's billable volume.

## Non-Functional Requirements

- **Auditability:** Raw provider files must be retained unchanged.
- **Traceability:** Every processed record must link back to its source file.
- **Idempotency:** Re-running the pipeline on the same input must not duplicate data.
- **Scalability:** Design should handle millions of transactions per month without rework.
- **Extensibility:** New providers and statuses should be configurable, not hard-coded.

## Out of Scope (for MVP)

- Real-time fraud detection.
- Merchant-facing portal.
- Automated invoicing and PDF generation.
- Multi-currency FX conversion.
- GDPR data deletion workflows.

These may be added in future phases.

## Glossary

| Term | Definition |
|------|------------|
| **Reconciliation** | Comparing internal transaction records against external provider records to identify mismatches. |
| **Settlement** | The process of transferring funds to merchants; not in scope, but billing informs it. |
| **Chargeback** | A reversal of a transaction initiated by the cardholder or bank. |
| **Discrepancy** | Any difference between internal and provider data (amount, status, missing record). |
