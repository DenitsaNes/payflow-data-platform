"""PayFlow — Streamlit dashboard.

Run with:
    streamlit run src/dashboard/dashboard.py
"""

import sys
from pathlib import Path

# Add project root to Python path so Streamlit can find the src package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
import streamlit as st

from src.utils.db import get_engine


def run_query(query: str) -> pd.DataFrame:
    """Run a SQL query and return a DataFrame."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql_query(query, conn)


def main() -> None:
    st.set_page_config(page_title="PayFlow Dashboard", layout="wide")
    st.title("PayFlow — Payment Reconciliation & Billing")

    # -------------------------------------------------------------------------
    # Executive KPIs
    # -------------------------------------------------------------------------
    st.header("Executive Summary")

    reconciliation = run_query(
        "SELECT reconciliation_status, transaction_count FROM warehouse_v_reconciliation_summary"
    )

    total_transactions = reconciliation["transaction_count"].sum()
    match_count = reconciliation.loc[
        reconciliation["reconciliation_status"] == "MATCH", "transaction_count"
    ].sum()
    match_rate = (match_count / total_transactions * 100) if total_transactions else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Transactions", f"{total_transactions:,}")
    col2.metric("Match Rate", f"{match_rate:.2f}%")
    col3.metric(
        "Discrepancies",
        f"{total_transactions - match_count:,}",
    )

    # -------------------------------------------------------------------------
    # Reconciliation breakdown
    # -------------------------------------------------------------------------
    st.header("Reconciliation Breakdown")

    col_chart, col_table = st.columns([2, 1])
    with col_chart:
        st.bar_chart(
            reconciliation.set_index("reconciliation_status")["transaction_count"]
        )
    with col_table:
        st.dataframe(reconciliation, use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------------
    # Billing report
    # -------------------------------------------------------------------------
    st.header("Merchant Billing")

    billing = run_query(
        """
        SELECT
            merchant_id,
            merchant_name,
            billing_period,
            successful_transactions,
            gross_volume,
            refunds_volume,
            net_volume,
            total_fees,
            amount_due
        FROM warehouse_v_billing_report
        ORDER BY amount_due DESC
        """
    )

    if not billing.empty:
        st.dataframe(
            billing.style.format(
                {
                    "gross_volume": "{:.2f}",
                    "refunds_volume": "{:.2f}",
                    "net_volume": "{:.2f}",
                    "total_fees": "{:.2f}",
                    "amount_due": "{:.2f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        total_revenue = billing["total_fees"].sum()
        st.metric("Total Platform Revenue", f"€{total_revenue:,.2f}")
    else:
        st.info("Run sql/billing/generate_billing.sql to populate billing data.")

    # -------------------------------------------------------------------------
    # Discrepancy details
    # -------------------------------------------------------------------------
    st.header("Discrepancy Details")

    status_filter = st.selectbox(
        "Filter by reconciliation status",
        ["ALL", "AMOUNT_MISMATCH", "STATUS_MISMATCH", "MISSING_FROM_GATEWAY", "MISSING_INTERNAL"],
    )

    query = """
        SELECT
            fr.transaction_id,
            m.merchant_id,
            p.provider_id,
            fr.internal_amount,
            fr.gateway_amount,
            fr.amount_difference,
            fr.reconciliation_status,
            fr.reconciled_at
        FROM warehouse_fact_reconciliation fr
        LEFT JOIN warehouse_dim_merchant m ON fr.merchant_key = m.merchant_key
        LEFT JOIN warehouse_dim_provider p ON fr.provider_key = p.provider_key
    """

    if status_filter != "ALL":
        query += f" WHERE fr.reconciliation_status = '{status_filter}'"

    query += " ORDER BY fr.reconciliation_status, fr.transaction_id LIMIT 500"

    discrepancies = run_query(query)
    st.dataframe(
        discrepancies.style.format(
            {
                "internal_amount": "{:.2f}",
                "gateway_amount": "{:.2f}",
                "amount_difference": "{:.2f}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


if __name__ == "__main__":
    main()
