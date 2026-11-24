"""Streamlit Analytics Dashboard Entry Point.

Multi-page interactive dashboard:
1. Overview: Headline KPIs & monthly revenue trend
2. Breakdowns: Category, region, channel, customer segment with interactive filters
3. Returns & Discounts: Return rates & discount effectiveness
4. Fulfilment: Shipping duration & late orders
5. Data Quality: Naive vs Corrected view (Q14)
"""

import sys
from pathlib import Path

# Ensure project root and app directory are both in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import pandas as pd
import streamlit as st

try:
    from app.data_access import get_clean_data, get_raw_data
    from app.charts import (
        chart_monthly_revenue_trend,
        chart_category_revenue_share,
        chart_channel_mix_trend,
        chart_regional_performance,
        chart_return_rate_by_segment,
        chart_discount_vs_volume,
        chart_shipping_duration_distribution,
        chart_naive_vs_corrected,
    )
except ImportError:
    from data_access import get_clean_data, get_raw_data
    from charts import (
        chart_monthly_revenue_trend,
        chart_category_revenue_share,
        chart_channel_mix_trend,
        chart_regional_performance,
        chart_return_rate_by_segment,
        chart_discount_vs_volume,
        chart_shipping_duration_distribution,
        chart_naive_vs_corrected,
    )

st.set_page_config(
    page_title="Retail Orders Executive Dashboard",
    page_icon="📊",
    layout="wide"
)

# Sidebar Navigation
st.sidebar.title("Retail Intelligence")
page = st.sidebar.radio(
    "Select View:",
    [
        "1. Overview",
        "2. Breakdowns",
        "3. Returns & Discounts",
        "4. Fulfilment",
        "5. Data Quality (Naive vs Corrected)"
    ]
)

# Load data
df_clean = get_clean_data()
df_raw = get_raw_data()

is_clean_ready = not df_clean.empty

# ==============================================================================
# PAGE 1: OVERVIEW
# ==============================================================================
if page == "1. Overview":
    st.title("Executive Overview")
    st.caption("Clean dataset: 464 lines across 260 distinct orders. Revenue formula: `quantity * unit_price * (1 - discount)`.")
    
    if not is_clean_ready:
        st.error("Cleaned dataset not found. Run `python src/clean.py` first.")
    else:
        # KPI Cards
        gross_rev = df_clean["revenue"].sum()
        net_rev = df_clean["net_revenue"].sum()
        total_orders = df_clean["order_id"].nunique()
        aov = gross_rev / total_orders
        return_rate = (df_clean["returned"] == True).mean() * 100
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Gross Revenue", f"${gross_rev:,.2f}", help="Total order value before return deductions")
        col2.metric("Net Revenue", f"${net_rev:,.2f}", delta=f"-${gross_rev - net_rev:,.2f} returned", help="Gross revenue minus returned line items")
        col3.metric("Distinct Orders", f"{total_orders:,}", help="Count of unique order_id transactions")
        col4.metric("Average Order Value", f"${aov:,.2f}", help="Gross revenue divided by distinct orders")
        col5.metric("Line Return Rate", f"{return_rate:.1f}%", help="Percentage of line items flagged as returned")
        
        st.divider()
        st.plotly_chart(chart_monthly_revenue_trend(df_clean), use_container_width=True)
        
        # Monthly summary breakdown
        df_clean["month"] = pd.to_datetime(df_clean["order_date"]).dt.strftime("%Y-%m")
        monthly_table = df_clean.groupby("month").agg(
            gross_revenue=("revenue", "sum"),
            net_revenue=("net_revenue", "sum"),
            orders=("order_id", "nunique"),
            units_sold=("quantity", "sum")
        ).reset_index().rename(columns={
            "month": "Month",
            "gross_revenue": "Gross Revenue ($)",
            "net_revenue": "Net Revenue ($)",
            "orders": "Orders",
            "units_sold": "Units Sold"
        })
        st.subheader("Monthly Performance Summary")
        st.dataframe(monthly_table.style.format({
            "Gross Revenue ($)": "${:,.2f}",
            "Net Revenue ($)": "${:,.2f}",
            "Orders": "{:,}",
            "Units Sold": "{:,}"
        }), use_container_width=True)


# ==============================================================================
# PAGE 2: BREAKDOWNS (WITH INTERACTIVE FILTERS)
# ==============================================================================
elif page == "2. Breakdowns":
    st.title("Sales Breakdowns")
    st.caption("Standardized dimensions: 4 geographic regions, 3 categories, 3 sales channels, and 3 customer segments.")
    
    if not is_clean_ready:
        st.error("Cleaned dataset not found.")
    else:
        # Sidebar interactive filters
        st.sidebar.subheader("Dashboard Filters")
        
        all_regions = sorted(df_clean["region"].unique().tolist())
        selected_regions = st.sidebar.multiselect("Regions", all_regions, default=all_regions)
        
        all_cats = sorted(df_clean["category"].unique().tolist())
        selected_cats = st.sidebar.multiselect("Categories", all_cats, default=all_cats)
        
        all_channels = sorted(df_clean["sales_channel"].unique().tolist())
        selected_channels = st.sidebar.multiselect("Sales Channels", all_channels, default=all_channels)
        
        # Filter dataframe
        filtered_df = df_clean[
            df_clean["region"].isin(selected_regions) &
            df_clean["category"].isin(selected_cats) &
            df_clean["sales_channel"].isin(selected_channels)
        ]
        
        st.info(f"Showing **{len(filtered_df)}** line items matching active filters (out of {len(df_clean)} total).")
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(chart_category_revenue_share(filtered_df), use_container_width=True)
        with col2:
            st.plotly_chart(chart_channel_mix_trend(filtered_df), use_container_width=True)
            
        st.divider()
        st.plotly_chart(chart_regional_performance(filtered_df), use_container_width=True)


# ==============================================================================
# PAGE 3: RETURNS & DISCOUNTS
# ==============================================================================
elif page == "3. Returns & Discounts":
    st.title("Returns & Discounts Analysis")
    st.caption("Analysis of return volume across segments and effectiveness of discount tiers.")
    
    if not is_clean_ready:
        st.error("Cleaned dataset not found.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(chart_return_rate_by_segment(df_clean), use_container_width=True)
            st.markdown("""
            **Key Return Takeaway:**
            - **Technology** drives the vast majority of returned revenue ($19,944 out of $26,989 total returned dollars).
            - **Corporate Technology** lines experience the highest return rate at **21.3%**.
            """)
        with col2:
            st.plotly_chart(chart_discount_vs_volume(df_clean), use_container_width=True)
            st.markdown("""
            **Discount Elasticity Takeaway:**
            - Discounted lines sell an average of **2.35 units** vs **2.31 units** for full price—a minimal volume lift (+1.7%).
            - Discounts surrendered **$12,439.10** in revenue without meaningfully increasing order basket size.
            """)
            
        st.subheader("Subcategory Risk Scorecard")
        scorecard = df_clean.groupby(["subcategory", "category"]).agg(
            units_sold=("quantity", "sum"),
            gross_revenue=("revenue", "sum"),
            net_revenue=("net_revenue", "sum"),
            return_rate_pct=("returned", lambda s: (s == True).mean() * 100)
        ).reset_index().sort_values("gross_revenue", ascending=False)
        st.dataframe(scorecard.style.format({
            "units_sold": "{:,}",
            "gross_revenue": "${:,.2f}",
            "net_revenue": "${:,.2f}",
            "return_rate_pct": "{:.1f}%"
        }), use_container_width=True)


# ==============================================================================
# PAGE 4: FULFILMENT
# ==============================================================================
elif page == "4. Fulfilment":
    st.title("Fulfilment & Shipping Speed")
    st.caption("Tracking order fulfillment time from placement to shipment across regions and channels.")
    
    if not is_clean_ready:
        st.error("Cleaned dataset not found.")
    else:
        valid_ship = df_clean[df_clean["shipping_days"].notna()]
        overall_ship_avg = valid_ship["shipping_days"].mean()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Average Shipping Time", f"{overall_ship_avg:.2f} Days")
        m2.metric("Orders with 'TBD' Ship Date", f"{(df_clean['ship_date'].isna()).sum()} Lines")
        
        # Interactive threshold
        late_threshold = st.slider("Define Late Order Threshold (Days):", min_value=3, max_value=10, value=5)
        late_lines = valid_ship[valid_ship["shipping_days"] > late_threshold]
        m3.metric(f"Late Orders (>{late_threshold} Days)", f"{late_lines['order_id'].nunique()} Orders", delta=f"{len(late_lines)} lines", delta_color="inverse")
        
        st.plotly_chart(chart_shipping_duration_distribution(df_clean), use_container_width=True)
        
        st.subheader(f"Delayed Orders Exceeding {late_threshold} Days")
        st.dataframe(late_lines[["order_id", "order_date", "ship_date", "shipping_days", "region", "sales_channel", "notes"]], use_container_width=True)


# ==============================================================================
# PAGE 5: DATA QUALITY (NAIVE VS CORRECTED - Q14)
# ==============================================================================
elif page == "5. Data Quality (Naive vs Corrected)":
    st.title("Data Quality Impact: Naive vs Corrected")
    st.caption("Direct comparison of raw export calculations versus the fully audited and cleaned dataset (Workbook Q14).")
    
    if df_raw.empty or not is_clean_ready:
        st.error("Both raw and clean datasets are required for this comparison.")
    else:
        # Calculations
        def naive_parse(val):
            import re
            if not val or val == "unknown":
                return 0.0
            is_neg = str(val).startswith("-") or "(" in str(val)
            num = re.sub(r"[^\d.]", "", str(val))
            try:
                res = float(num) if num else 0.0
                return -res if is_neg else res
            except ValueError:
                return 0.0

        raw_naive_rev = df_raw["revenue"].apply(naive_parse).sum()
        clean_gross_rev = df_clean["revenue"].sum()
        clean_net_rev = df_clean["net_revenue"].sum()
        delta_rev = clean_gross_rev - raw_naive_rev
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Raw Rows", f"{len(df_raw)}", delta="-16 Duplicates", delta_color="inverse")
        c2.metric("Clean Rows", f"{len(df_clean)}")
        c3.metric("Raw Naive Revenue", f"${raw_naive_rev:,.2f}")
        c4.metric("Cleaned Gross Revenue", f"${clean_gross_rev:,.2f}", delta=f"+${delta_rev:,.2f} recovered")
        
        st.divider()
        st.plotly_chart(chart_naive_vs_corrected(df_raw, df_clean), use_container_width=True)
        
        st.subheader("Data Cleaning Step Reconciliation")
        rec_data = [
            {"Issue": "Exact Duplicate Rows", "Impact": "+16 phantom rows in raw export", "Resolution": "Dropped exact identical rows (-16 rows)."},
            {"Issue": "Negative & Bracketed Revenue", "Impact": "23 rows recorded return payouts as negative revenue", "Resolution": "Separated gross transaction value from return refunds."},
            {"Issue": "'Unknown' Revenue Rows", "Impact": "24 rows missing recorded revenue ($16k+ missing)", "Resolution": "Recomputed via formula `quantity * unit_price * (1 - discount)`."},
            {"Issue": "Unparseable & Invalid Dates", "Impact": "6 order dates failed ('2025-02-30', 'not recorded')", "Resolution": "Imputed 100% of missing order dates from multi-line sibling orders."},
            {"Issue": "Inconsistent Categorical Labels", "Impact": "21 regions, 17 categories, 16 channels fragmented metrics", "Resolution": "Unified taxonomy; imputed missing regions from city and categories from subcategories."}
        ]
        st.table(pd.DataFrame(rec_data))
