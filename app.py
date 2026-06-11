import streamlit as st
import pandas as pd
import tempfile
import os
from pathlib import Path
from datetime import date, timedelta

from database import (init_db, date_exists, insert_production, insert_sells,
                      log_upload, get_date_range, get_uploaded_dates,
                      get_upload_count, get_upload_log,
                      get_total_production_amount,
                      get_total_sells_amount, delete_date, delete_all)
from parser import parse_excel, extract_date_from_filename
from analytics import Aggregator, KPIEngine, load_dataframe
from ui import (inject_css, render_header, kpi_card, trend_chart,
                bar_chart, donut_chart, DARK_THEME)
from sample_data import generate_sample_data

st.set_page_config(page_title="Fakher Statistics", layout="wide", page_icon="📊")
inject_css()

init_db()

if "upload_key" not in st.session_state:
    st.session_state.upload_key = 0

SECTIONS = {"Production": "production", "Sells": "sells"}

# ─── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f'<div style="font-size:1.3rem;font-weight:700;background:linear-gradient(135deg,{DARK_THEME["accent_teal"]},{DARK_THEME["accent_purple"]});-webkit-background-clip:text;-webkit-text-fill-color:transparent;padding:0.5rem 0;">⚡ Fakher Statistics</div>',
        unsafe_allow_html=True)
    st.markdown(f'<div style="color:{DARK_THEME["text_muted"]};font-size:0.8rem;margin-bottom:1.5rem;">Production & Sales Analytics</div>',
                unsafe_allow_html=True)

    st.markdown("---")

    # Section selector
    section_label = st.selectbox("Data Section", list(SECTIONS.keys()), index=0)
    section = SECTIONS[section_label]

    # Time granularity
    granularity = st.selectbox("Time Granularity",
                               ["Daily", "Weekly", "Monthly", "Quarterly", "Yearly"],
                               index=0)

    # Chart type toggle
    chart_type = st.radio("Chart Type", ["Line", "Bar"], horizontal=True, index=0)

    # Date range filter
    min_date, max_date = get_date_range()
    if min_date and max_date:
        st.markdown(f'<div style="color:{DARK_THEME["text_muted"]};font-size:0.75rem;">Date Range</div>',
                    unsafe_allow_html=True)
        date_range = st.date_input(
            "Filter by date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            label_visibility="collapsed",
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_filter, end_filter = date_range
        else:
            start_filter, end_filter = min_date, max_date
    else:
        start_filter = end_filter = None

    st.markdown("---")
    st.markdown(f'<div style="color:{DARK_THEME["text_muted"]};font-size:0.75rem;text-transform:uppercase;letter-spacing:1px;">Data Management</div>',
                unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload Excel file",
        type=["xlsx", "xlsm", "xls", "csv"],
        help="Upload daily production/sales report",
        key=f"uploader_{st.session_state.upload_key}"
    )

    if uploaded_file:
        with st.spinner("Parsing file..."):
            try:
                ext = Path(uploaded_file.name).suffix.lower()
                if ext == ".csv":
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name
                else:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name

                report_date = extract_date_from_filename(uploaded_file.name)
                if report_date is None:
                    report_date = date.today()

                result = parse_excel(tmp_path, report_date)
                os.unlink(tmp_path)

                rd = result["report_date"]
                if date_exists(rd):
                    st.error(f"⚠ Data for {rd.isoformat()} already exists. Delete it first to re-upload.")
                else:
                    insert_production(rd, result["production"])
                    insert_sells(rd, result["sells"])
                    log_upload(uploaded_file.name, rd,
                               len(result["production"]), len(result["sells"]))
                    st.success(f"✅ Uploaded {uploaded_file.name} ({rd.isoformat()})")
                    st.rerun()
            except Exception as e:
                st.error(f"Upload failed: {e}")

    # Load sample data button
    if st.button("Generate Sample Data (90 days)", type="secondary", use_container_width=True):
        with st.spinner("Generating sample data..."):
            count = generate_sample_data(90)
            st.success(f"✅ Generated {count} days of sample data")
            st.rerun()

    # Data management expander
    with st.expander("🗑 Manage Uploaded Dates"):
        dates = get_uploaded_dates()
        if dates:
            del_col, btn_col = st.columns([3, 1])
            with del_col:
                del_date_sel = st.selectbox("Select date to delete", dates,
                                            format_func=lambda d: d.isoformat(),
                                            label_visibility="collapsed")
            with btn_col:
                if st.button("Delete", type="primary", use_container_width=True):
                    delete_date(del_date_sel.isoformat())
                    st.session_state.upload_key += 1
                    st.rerun()
            if st.button("Delete All Data", type="secondary", use_container_width=True):
                delete_all()
                st.session_state.upload_key += 1
                st.rerun()
        else:
            st.caption("No data uploaded yet.")

    # Stats
    upload_count = get_upload_count()
    st.markdown(f'<div style="color:{DARK_THEME["text_muted"]};font-size:0.75rem;margin-top:1rem;">{upload_count} files uploaded</div>',
                unsafe_allow_html=True)

# ─── Main Content ──────────────────────────────────────────────────────────
render_header("📈 Analytics Dashboard",
              f"Real-time {section_label.lower()} metrics & trends")

# ─── KPI Cards Row ─────────────────────────────────────────────────────────
kpi_period_map = {
    "Daily": "day", "Weekly": "week", "Monthly": "month",
    "Quarterly": "quarter", "Yearly": "year"
}
kpi_engine = KPIEngine(section)

col1, col2, col3, col4 = st.columns(4)

with col1:
    kpi = kpi_engine.current_vs_previous(kpi_period_map[granularity])
    period_label = granularity.lower()
    kpi_card(
        f"Current {period_label}",
        f"{kpi['current']:,.0f}",
        f"{kpi['pct_change']:+.1f}% vs prev {period_label}",
        delta_positive=kpi["is_positive"],
        icon="📊"
    )

with col2:
    df_all = load_dataframe(section, start_filter, end_filter)
    total = float(df_all["amount"].sum()) if not df_all.empty else 0
    kpi_card(
        "Total amount",
        f"{total:,.0f}",
        icon="💰"
    )

with col3:
    total_trf = float(df_all["transfer"].sum()) if not df_all.empty and "transfer" in df_all.columns else 0
    kpi_card(
        "Total transfer",
        f"{total_trf:,.0f}",
        icon="🔄"
    )

with col4:
    avg_daily = total / max(1, (end_filter - start_filter).days + 1) if start_filter and end_filter else 0
    kpi_card(
        "Avg daily",
        f"{avg_daily:,.1f}",
        icon="📅"
    )

# ─── Time-Series Chart ─────────────────────────────────────────────────────
st.markdown("---")
agg = Aggregator(df_all)

gran_map = {
    "Daily": agg.by_day,
    "Weekly": agg.by_week,
    "Monthly": agg.by_month,
    "Quarterly": agg.by_quarter,
    "Yearly": agg.by_year,
}

if not df_all.empty:
    gran_df = gran_map[granularity]()
    if not gran_df.empty:
        if granularity == "Weekly":
            x_col = "week_start"
            x_label = "Week"
        elif granularity in ("Monthly", "Quarterly", "Yearly"):
            x_col = gran_df.columns[0]
        else:
            x_col = "report_date"

        y_cols = [c for c in ["amount", "transfer"] if c in gran_df.columns]
        names = ["Amount", "Transfer"]

        if chart_type == "Line":
            fig = trend_chart(
                gran_df, x_col, y_cols, names,
                title=f"{section_label} — {granularity} Trend"
            )
        else:
            fig = bar_chart(
                gran_df, x_col, y_cols[0],
                title=f"{section_label} — {granularity} Amount",
                color=DARK_THEME["accent_teal"]
            )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data available. Upload files or generate sample data.")

# ─── Charts Row ────────────────────────────────────────────────────────────
st.markdown("---")
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    top = agg.top_products(10)
    if not top.empty:
        fig = bar_chart(top, "product_name", "amount",
                        title=f"Top 10 Products by Amount ({section_label})",
                        color=DARK_THEME["accent_teal"])
        st.plotly_chart(fig, use_container_width=True)

with chart_col2:
    if section == "sells":
        cat = agg.category_breakdown()
        if not cat.empty:
            fig = donut_chart(cat, "main_name", "amount",
                              title="Category Distribution (Sells)")
            st.plotly_chart(fig, use_container_width=True)
    else:
        top_trf = agg.top_products(10)
        if not top_trf.empty and "transfer" in top_trf.columns:
            fig = bar_chart(top_trf, "product_name", "transfer",
                            title=f"Top 10 Products by Transfer ({section_label})",
                            color=DARK_THEME["accent_purple"])
            st.plotly_chart(fig, use_container_width=True)

# ─── Data Table ────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("📋 Detailed Data Table", expanded=False):
    if not df_all.empty:
        display_df = df_all.copy()
        if "report_date" in display_df.columns:
            display_df["report_date"] = display_df["report_date"].dt.strftime("%Y-%m-%d")
        display_df = display_df.fillna("")
        st.dataframe(display_df, use_container_width=True, height=400)
    else:
        st.caption("No data to display.")

with st.expander("📁 Uploaded Files", expanded=False):
    upload_log_df = pd.DataFrame(get_upload_log())
    if not upload_log_df.empty:
        upload_log_df["report_date"] = pd.to_datetime(
            upload_log_df["report_date"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")
        upload_log_df["uploaded_at"] = pd.to_datetime(
            upload_log_df["uploaded_at"], errors="coerce"
        ).dt.strftime("%Y-%m-%d %H:%M")
        upload_log_df = upload_log_df.rename(columns={
            "file_name": "File name",
            "report_date": "Report date",
            "uploaded_at": "Uploaded at",
            "records_prod": "Production rows",
            "records_sells": "Sells rows",
        }).fillna("")
        st.dataframe(upload_log_df, use_container_width=True, height=320)
    else:
        st.caption("No uploaded files yet.")

# ─── Footer Stats ──────────────────────────────────────────────────────────
st.markdown("---")
st.caption(f"Fakher Statistics Dashboard · {upload_count} days loaded · "
           f"Last updated: {date.today().isoformat()}")
