"""Streamlit dashboard for jjbank."""

from __future__ import annotations

import io
import json
import sys
import tempfile
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Ensure jjbank root is on the path when running via `streamlit run web/app.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from execution.ingest_statement import normalise_statement
from execution.reports import build_report, render_markdown

st.set_page_config(page_title="jjbank", layout="wide")

SUPPORTED_TYPES = ["csv", "xlsx", "xls", "pdf"]


def main() -> None:
    st.title("jjbank Dashboard")
    st.markdown(
        "Upload a bank statement (CSV, XLSX, PDF) to analyse money in/out, recurring depositors, missing payments, and spending breakdown."
    )

    with st.sidebar:
        uploaded = st.file_uploader("Statement file", type=SUPPORTED_TYPES)
        password = st.text_input("PDF password (optional)", type="password")
        if uploaded:
            if st.button("Analyse"):
                st.session_state["analyse"] = True

    if not uploaded:
        st.info("Upload a statement to get started.")
        return

    if st.session_state.get("analyse") is None:
        st.session_state["analyse"] = True

    if not st.session_state.get("analyse"):
        return

    with tempfile.NamedTemporaryFile(suffix=Path(uploaded.name).suffix, delete=False) as tmp:
        tmp.write(uploaded.getbuffer())
        tmp_path = tmp.name

    try:
        suffix = Path(uploaded.name).suffix.lower()
        if suffix == ".pdf" and not password:
            st.warning("This PDF appears to be password protected. Enter the password and click Analyse again.")
            return

        statement = normalise_statement(tmp_path, password=password or None)
        if statement.empty:
            st.warning("No transactions could be parsed from this file.")
            return
        rows = statement.to_dict(orient="records")
        for row in rows:
            row["title"] = row.get("description", "")
        report = build_report(rows)
        st.session_state["report"] = report
        st.session_state["rows"] = rows
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    report: dict = st.session_state.get("report", {})
    money_in_out = report.get("money_in_out", {})
    income = report.get("income_analysis", {})
    spend = report.get("spending_summary", {})

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Money In", f"{money_in_out.get('total_in', 0):.2f}")
    with col2:
        st.metric("Money Out", f"{money_in_out.get('total_out', 0):.2f}")

    st.subheader("Recurring Depositors")
    depositors = income.get("monthly_depositors", [])
    if depositors:
        for name in depositors:
            st.write(f"- {name}")
    else:
        st.write("None detected")

    st.subheader("Missing Payment Alerts")
    alerts = income.get("alerts", [])
    if alerts:
        for alert in alerts:
            st.warning(f"{alert['name']} missing in {alert['month']}")
    else:
        st.write("No missing payments detected.")

    st.subheader("Spending by Category")
    categories = spend.get("categories", {})
    if categories:
        chart_df = pd.DataFrame(
            [{"category": cat, "amount": amt} for cat, amt in categories.items()]
        )
        fig = px.bar(chart_df, x="category", y="amount", labels={"amount": "Amount", "category": "Category"})
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Total Out: {spend.get('total_out', 0):.2f}")
    else:
        st.write("No spending data available.")

    st.subheader("Export")
    report_json = st.session_state.get("report", {})
    report_md = render_markdown(report_json)
    col_json, col_md = st.columns(2)
    with col_json:
        st.download_button(
            "Download report.json",
            data=json.dumps(report_json, indent=2),
            file_name="report.json",
            mime="application/json",
        )
    with col_md:
        st.download_button(
            "Download report.md",
            data=report_md,
            file_name="report.md",
            mime="text/markdown",
        )


if __name__ == "__main__":
    main()
