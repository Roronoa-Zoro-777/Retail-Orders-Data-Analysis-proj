"""Business Questions Analysis Module (pandas).

Answers questions Q1 through Q15 using pandas on data/clean/topic3-clean.csv.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
from src.utils import load_clean_data, load_raw_data


def q1_monthly_revenue_trend(df: pd.DataFrame):
    """Q1: Monthly revenue trend."""
    df_copy = df.copy()
    df_copy["month"] = pd.to_datetime(df_copy["order_date"]).dt.strftime("%Y-%m")
    trend = df_copy.groupby("month").agg(
        total_revenue=("revenue", "sum"),
        distinct_orders=("order_id", "nunique"),
        total_units=("quantity", "sum")
    ).reset_index().sort_values("month")
    strongest_month = trend.loc[trend["total_revenue"].idxmax(), "month"]
    return trend, strongest_month


def q2_revenue_by_category(df: pd.DataFrame):
    """Q2: Revenue by category."""
    cat_rev = df.groupby("category")["revenue"].sum().reset_index()
    total_rev = cat_rev["revenue"].sum()
    cat_rev["share_of_total_pct"] = (cat_rev["revenue"] / total_rev * 100).round(2)
    return cat_rev.sort_values("revenue", ascending=False)


def q3_regional_ranking(df: pd.DataFrame):
    """Q3: Regional ranking by revenue and orders."""
    reg = df.groupby("region").agg(
        revenue=("revenue", "sum"),
        distinct_orders=("order_id", "nunique")
    ).reset_index()
    reg["revenue_rank"] = reg["revenue"].rank(ascending=False, method="min").astype(int)
    reg["orders_rank"] = reg["distinct_orders"].rank(ascending=False, method="min").astype(int)
    return reg.sort_values("revenue_rank")


def q4_orders_lines_basket_size(df: pd.DataFrame):
    """Q4: Orders, lines and basket size."""
    distinct_orders = df["order_id"].nunique()
    total_lines = len(df)
    total_revenue = df["revenue"].sum()
    aov = total_revenue / distinct_orders
    avg_lines = total_lines / distinct_orders
    return {
        "distinct_orders": distinct_orders,
        "total_line_items": total_lines,
        "avg_lines_per_order": round(avg_lines, 2),
        "average_order_value": round(aov, 2),
    }


def q5_channel_mix_over_time(df: pd.DataFrame):
    """Q5: Channel mix over time."""
    df_copy = df.copy()
    df_copy["month"] = pd.to_datetime(df_copy["order_date"]).dt.strftime("%Y-%m")
    pivot = df_copy.pivot_table(
        index="month",
        columns="sales_channel",
        values="revenue",
        aggfunc="sum",
        fill_value=0.0
    )
    pivot["Total"] = pivot.sum(axis=1)
    return pivot.round(2)


def q6_return_problem_areas(df: pd.DataFrame):
    """Q6: Return problem areas."""
    grouped = df.groupby(["category", "customer_type"]).agg(
        total_lines=("returned", "count"),
        returned_lines=("returned", lambda x: (x == True).sum()),
        returned_revenue=("revenue", lambda s: s[df.loc[s.index, "returned"] == True].sum())
    ).reset_index()
    grouped["return_rate_pct"] = (grouped["returned_lines"] / grouped["total_lines"] * 100).round(1)
    return grouped.sort_values("returned_revenue", ascending=False)


def q7_discount_effectiveness(df: pd.DataFrame):
    """Q7: Do discounts work?"""
    df_copy = df.copy()
    df_copy["is_discounted"] = df_copy["discount"] > 0
    grouped = df_copy.groupby("is_discounted").agg(
        avg_quantity=("quantity", "mean"),
        total_revenue=("revenue", "sum"),
        line_count=("quantity", "count")
    ).reset_index()
    
    # Dollars surrendered
    df_copy["dollars_surrendered"] = df_copy["quantity"] * df_copy["unit_price"] * df_copy["discount"]
    tier_summary = df_copy.groupby("discount").agg(
        lines=("quantity", "count"),
        dollars_surrendered=("dollars_surrendered", "sum")
    ).reset_index()
    return grouped, tier_summary


def q8_customer_segments(df: pd.DataFrame):
    """Q8: Customer segments."""
    seg = df.groupby("customer_type").agg(
        distinct_orders=("order_id", "nunique"),
        total_revenue=("revenue", "sum")
    ).reset_index()
    seg["revenue_per_order"] = (seg["total_revenue"] / seg["distinct_orders"]).round(2)
    return seg.sort_values("revenue_per_order", ascending=False)


def q9_shipping_speed(df: pd.DataFrame):
    """Q9: Shipping speed."""
    valid_ship = df[df["shipping_days"].notna()].copy()
    overall_avg = valid_ship["shipping_days"].mean()
    by_region = valid_ship.groupby(["region", "sales_channel"])["shipping_days"].mean().reset_index()
    late_orders = valid_ship[valid_ship["shipping_days"] > 5]
    return round(overall_avg, 2), by_region.round(2), len(late_orders)


def q10_revenue_reconciliation(df: pd.DataFrame):
    """Q10: Revenue reconciliation."""
    expected = df["quantity"] * df["unit_price"] * (1.0 - df["discount"])
    residuals = (df["revenue"] - expected).abs()
    disagreements = (residuals > 0.05).sum()
    return {"total_lines": len(df), "disagree_count": int(disagreements)}


def q11_missing_revenue_sensitivity(df_clean: pd.DataFrame, df_raw: pd.DataFrame):
    """Q11: Missing revenue sensitivity."""
    # Treatment 1: Drop rows where raw revenue was 'unknown'
    raw_unknown_orders = df_raw.loc[df_raw["revenue"] == "unknown", "order_id"].unique()
    t1_rev = df_clean[~df_clean["order_id"].isin(raw_unknown_orders)]["revenue"].sum()
    
    # Treatment 2: Recomputed from formula (Current clean standard)
    t2_rev = df_clean["revenue"].sum()
    
    # Treatment 3: Impute with mean subcategory revenue
    subcat_means = df_clean.groupby("subcategory")["revenue"].transform("mean")
    t3_rev = np.where(df_clean["order_id"].isin(raw_unknown_orders), subcat_means, df_clean["revenue"]).sum()
    
    return {
        "Treatment 1 (Drop unknown)": round(t1_rev, 2),
        "Treatment 2 (Recompute formula)": round(t2_rev, 2),
        "Treatment 3 (Impute subcat mean)": round(t3_rev, 2),
    }


def q12_subcategory_scorecard(df: pd.DataFrame):
    """Q12: Subcategory scorecard."""
    sc = df.groupby(["subcategory", "category"]).agg(
        gross_revenue=("revenue", "sum"),
        net_revenue=("net_revenue", "sum"),
        units_sold=("quantity", "sum"),
        return_rate_pct=("returned", lambda s: (s == True).mean() * 100)
    ).reset_index()
    return sc.round(2).sort_values("gross_revenue", ascending=False)


def q13_market_basket_combinations(df: pd.DataFrame):
    """Q13: What gets bought together."""
    baskets = df.groupby("order_id").agg(
        categories=("category", lambda s: tuple(sorted(set(s)))),
        basket_revenue=("revenue", "sum")
    ).reset_index()
    baskets["is_multi_category"] = baskets["categories"].apply(lambda c: len(c) > 1)
    combo_counts = baskets["categories"].value_counts().reset_index()
    aov_comparison = baskets.groupby("is_multi_category")["basket_revenue"].mean().to_dict()
    return combo_counts, aov_comparison


def q14_naive_vs_corrected(raw_df: pd.DataFrame, clean_df: pd.DataFrame):
    """Q14: Naive vs corrected comparison."""
    # Naive revenue sum: parse numbers dropping commas and symbols, treating blanks as 0
    def naive_parse(val):
        if not val or val == "unknown":
            return 0.0
        import re
        is_neg = str(val).startswith("-") or "(" in str(val)
        num = re.sub(r"[^\d.]", "", str(val))
        try:
            res = float(num) if num else 0.0
            return -res if is_neg else res
        except ValueError:
            return 0.0

    naive_rev = raw_df["revenue"].apply(naive_parse).sum()
    clean_gross_rev = clean_df["revenue"].sum()
    clean_net_rev = clean_df["net_revenue"].sum()
    return {
        "Raw Rows": len(raw_df),
        "Clean Rows": len(clean_df),
        "Raw Naive Revenue": round(naive_rev, 2),
        "Cleaned Gross Revenue": round(clean_gross_rev, 2),
        "Cleaned Net Revenue": round(clean_net_rev, 2),
        "Revenue Difference": round(clean_gross_rev - naive_rev, 2)
    }


def run_all_questions():
    df_clean = load_clean_data()
    df_raw = load_raw_data()
    print("=" * 60)
    print("SOLUTIONS FOR BUSINESS QUESTIONS Q1 - Q15")
    print("=" * 60)
    trend, strong_m = q1_monthly_revenue_trend(df_clean)
    print(f"\n[Q1] Strongest Month: {strong_m}")
    print(trend)
    
    print("\n[Q2] Category Revenue & Share:")
    print(q2_revenue_by_category(df_clean))
    
    print("\n[Q3] Regional Ranking:")
    print(q3_regional_ranking(df_clean))
    
    print("\n[Q4] Orders & Basket Size:")
    print(q4_orders_lines_basket_size(df_clean))
    
    print("\n[Q8] Customer Segments Revenue per Order:")
    print(q8_customer_segments(df_clean))
    
    print("\n[Q14] Naive vs Corrected Impact:")
    print(q14_naive_vs_corrected(df_raw, df_clean))


if __name__ == "__main__":
    run_all_questions()
