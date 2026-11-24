"""Plotly Chart Generation Functions for Streamlit Dashboard.

Creates clean, well-formatted, branded visualizations for all 5 dashboard sections.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def chart_monthly_revenue_trend(df: pd.DataFrame) -> go.Figure:
    """Monthly gross revenue and order count trend."""
    df_copy = df.copy()
    df_copy["month"] = pd.to_datetime(df_copy["order_date"]).dt.strftime("%Y-%m")
    monthly = df_copy.groupby("month").agg(
        revenue=("revenue", "sum"),
        orders=("order_id", "nunique")
    ).reset_index().sort_values("month")
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly["month"],
        y=monthly["revenue"],
        name="Gross Revenue ($)",
        marker_color="#2b5c8f",
        yaxis="y"
    ))
    fig.add_trace(go.Scatter(
        x=monthly["month"],
        y=monthly["orders"],
        name="Distinct Orders",
        mode="lines+markers",
        line=dict(color="#e65c00", width=3),
        marker=dict(size=8),
        yaxis="y2"
    ))
    fig.update_layout(
        title="Monthly Revenue & Order Volume (Jan - Jul 2025)",
        xaxis_title="Month",
        yaxis=dict(title="Gross Revenue ($)", side="left"),
        yaxis2=dict(title="Distinct Orders", side="right", overlaying="y", showgrid=False),
        legend=dict(x=0.01, y=0.99),
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=50, b=40)
    )
    return fig


def chart_category_revenue_share(df: pd.DataFrame) -> go.Figure:
    """Category revenue breakdown and share of total."""
    cat_rev = df.groupby("category")["revenue"].sum().reset_index().sort_values("revenue", ascending=False)
    fig = px.pie(
        cat_rev,
        values="revenue",
        names="category",
        hole=0.45,
        title="Revenue Share by Product Category",
        color_discrete_sequence=["#1f77b4", "#ff7f0e", "#2ca02c"]
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=40, b=20))
    return fig


def chart_channel_mix_trend(df: pd.DataFrame) -> go.Figure:
    """Monthly channel mix (In-Store, Online, Phone)."""
    df_copy = df.copy()
    df_copy["month"] = pd.to_datetime(df_copy["order_date"]).dt.strftime("%Y-%m")
    channel_monthly = df_copy.groupby(["month", "sales_channel"])["revenue"].sum().reset_index()
    
    fig = px.bar(
        channel_monthly,
        x="month",
        y="revenue",
        color="sales_channel",
        title="Revenue by Sales Channel Over Time",
        barmode="stack",
        color_discrete_map={
            "In-Store": "#2b5c8f",
            "Online": "#2ca02c",
            "Phone": "#ff7f0e"
        }
    )
    fig.update_layout(
        template="plotly_white",
        xaxis_title="Month",
        yaxis_title="Gross Revenue ($)",
        legend_title="Sales Channel",
        margin=dict(l=30, r=30, t=40, b=30)
    )
    return fig


def chart_regional_performance(df: pd.DataFrame) -> go.Figure:
    """Rank regions by revenue and distinct order count."""
    reg = df.groupby("region").agg(
        revenue=("revenue", "sum"),
        orders=("order_id", "nunique")
    ).reset_index().sort_values("revenue", ascending=True)
    
    fig = px.bar(
        reg,
        x="revenue",
        y="region",
        orientation="h",
        text="revenue",
        title="Revenue by Geographic Region",
        color="revenue",
        color_continuous_scale="Blues"
    )
    fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
    fig.update_layout(
        template="plotly_white",
        xaxis_title="Gross Revenue ($)",
        yaxis_title="Region",
        coloraxis_showscale=False,
        margin=dict(l=40, r=60, t=40, b=30)
    )
    return fig


def chart_return_rate_by_segment(df: pd.DataFrame) -> go.Figure:
    """Return rate by customer type and category."""
    grouped = df.groupby(["category", "customer_type"]).agg(
        total=("returned", "count"),
        returned=("returned", lambda x: (x == True).sum())
    ).reset_index()
    grouped["return_rate_pct"] = (grouped["returned"] / grouped["total"] * 100).round(1)
    
    fig = px.bar(
        grouped,
        x="category",
        y="return_rate_pct",
        color="customer_type",
        barmode="group",
        title="Return Rate (%) by Category & Customer Segment",
        color_discrete_sequence=["#1f77b4", "#ff7f0e", "#2ca02c"]
    )
    fig.update_layout(
        template="plotly_white",
        yaxis_title="Return Rate (%)",
        xaxis_title="Category",
        legend_title="Customer Type",
        margin=dict(l=30, r=30, t=40, b=30)
    )
    return fig


def chart_discount_vs_volume(df: pd.DataFrame) -> go.Figure:
    """Quantity sold per line vs discount tier."""
    df_copy = df.copy()
    disc_tier = df_copy.groupby("discount").agg(
        avg_qty=("quantity", "mean"),
        total_revenue=("revenue", "sum"),
        dollars_given_away=("revenue", lambda r: (df_copy.loc[r.index, "quantity"] * df_copy.loc[r.index, "unit_price"] * df_copy.loc[r.index, "discount"]).sum())
    ).reset_index()
    disc_tier["discount_label"] = (disc_tier["discount"] * 100).astype(int).astype(str) + "%"
    
    fig = px.bar(
        disc_tier,
        x="discount_label",
        y="avg_qty",
        text="avg_qty",
        title="Average Quantity Sold per Line by Discount Tier",
        color="avg_qty",
        color_continuous_scale="Viridis"
    )
    fig.update_traces(texttemplate="%{text:.2f} units", textposition="outside")
    fig.update_layout(
        template="plotly_white",
        xaxis_title="Discount Tier",
        yaxis_title="Average Quantity per Line",
        coloraxis_showscale=False,
        margin=dict(l=30, r=30, t=40, b=30)
    )
    return fig


def chart_shipping_duration_distribution(df: pd.DataFrame) -> go.Figure:
    """Distribution of order-to-ship delivery duration."""
    valid_ship = df[df["shipping_days"].notna()].copy()
    fig = px.histogram(
        valid_ship,
        x="shipping_days",
        nbins=12,
        color="region",
        title="Order-to-Ship Duration Distribution (Days)",
        barmode="overlay",
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    fig.update_layout(
        template="plotly_white",
        xaxis_title="Days from Order to Shipment",
        yaxis_title="Number of Orders",
        legend_title="Region",
        margin=dict(l=30, r=30, t=40, b=30)
    )
    return fig


def chart_naive_vs_corrected(raw_df: pd.DataFrame, clean_df: pd.DataFrame) -> go.Figure:
    """Side-by-side comparison of naive vs cleaned monthly revenue."""
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

    raw_copy = raw_df.copy()
    raw_copy["naive_rev"] = raw_copy["revenue"].apply(naive_parse)
    raw_copy["month"] = pd.to_datetime(raw_copy["order_date"], errors="coerce").dt.strftime("%Y-%m")
    raw_monthly = raw_copy.dropna(subset=["month"]).groupby("month")["naive_rev"].sum().reset_index()
    
    clean_copy = clean_df.copy()
    clean_copy["month"] = pd.to_datetime(clean_copy["order_date"]).dt.strftime("%Y-%m")
    clean_monthly = clean_copy.groupby("month")["revenue"].sum().reset_index()
    
    merged = pd.merge(raw_monthly, clean_monthly, on="month", how="outer").sort_values("month")
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=merged["month"],
        y=merged["naive_rev"],
        name="Naive Raw Calculation",
        marker_color="#d62728"
    ))
    fig.add_trace(go.Bar(
        x=merged["month"],
        y=merged["revenue"],
        name="Corrected Cleaned Calculation",
        marker_color="#2ca02c"
    ))
    fig.update_layout(
        title="Impact of Data Quality on Monthly Revenue (Naive vs Corrected)",
        xaxis_title="Month",
        yaxis_title="Total Revenue ($)",
        barmode="group",
        template="plotly_white",
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=40, r=30, t=40, b=30)
    )
    return fig
