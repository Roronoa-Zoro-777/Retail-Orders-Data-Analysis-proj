"""Data Cleaning Pipeline Module for Retail Orders Dataset.

Transforms messy data/raw/topic3-data.csv into data/clean/topic3-clean.csv.
Adheres strictly to documented rules and logs in decisions_log.md.
"""

import sys
import re
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils import load_raw_data, CLEAN_CSV_PATH, get_db_connection

# Domain mappings
CITY_TO_REGION = {
    "Atlanta": "South",
    "Boston": "Northeast",
    "Chicago": "Midwest",
    "Dallas": "South",
    "Houston": "South",
    "Indianapolis": "Midwest",
    "Madison": "Midwest",
    "Milwaukee": "Midwest",
    "Nashville": "South",
    "New York": "Northeast",
    "Philadelphia": "Northeast",
    "Phoenix": "West",
    "Pittsburgh": "Northeast",
    "Portland": "West",
    "San Diego": "West",
    "Seattle": "West",
}

SUBCAT_TO_CAT = {
    "Chair": "Furniture",
    "Bookcase": "Furniture",
    "Desk": "Furniture",
    "Binder": "Office Supplies",
    "Paper": "Office Supplies",
    "Pen": "Office Supplies",
    "Headphones": "Technology",
    "Laptop": "Technology",
    "Monitor": "Technology",
}

WORD_TO_NUM = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}


def handle_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Step 1: Remove exact duplicate rows (all 15 columns identical)."""
    initial_rows = len(df)
    df_dedup = df.drop_duplicates(keep="first").copy()
    dropped = initial_rows - len(df_dedup)
    print(f"[Step 1: Duplicates] Dropped {dropped} exact duplicates. Remaining rows: {len(df_dedup)}")
    return df_dedup


def clean_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Step 2: Parse order_date and ship_date; impute invalid order_dates from sibling lines."""
    df = df.copy()
    
    # 1. Parse with mixed format handling
    order_parsed = pd.to_datetime(df["order_date"], format="mixed", errors="coerce")
    ship_parsed = pd.to_datetime(df["ship_date"], format="mixed", errors="coerce")
    
    # 2. Impute bad order_date ('2025-02-30', 'not recorded') from sibling rows in the same order
    bad_order_mask = order_parsed.isna()
    for idx in df[bad_order_mask].index:
        order_id = df.loc[idx, "order_id"]
        sibling_dates = df.loc[(df["order_id"] == order_id) & (~bad_order_mask), "order_date"]
        if not sibling_dates.empty:
            imputed_val = pd.to_datetime(sibling_dates.iloc[0], format="mixed", errors="coerce")
            order_parsed.loc[idx] = imputed_val
            
    # 3. Format as ISO strings (YYYY-MM-DD)
    df["order_date"] = order_parsed.dt.strftime("%Y-%m-%d")
    df["ship_date"] = ship_parsed.dt.strftime("%Y-%m-%d")  # NaT becomes NaN
    
    print(f"[Step 2: Dates] order_date valid count: {df['order_date'].notna().sum()}, ship_date valid count: {df['ship_date'].notna().sum()}")
    return df


def standardize_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Step 3: Standardize text labels and impute missing/unknown categoricals."""
    df = df.copy()
    
    # Clean city first
    df["city"] = df["city"].astype(str).str.strip()
    city_map = {
        "SanDiego": "San Diego",
        "san diego": "San Diego",
        "boston": "Boston",
        "chicago": "Chicago",
        "dallas": "Dallas",
        "houston": "Houston",
        "indianapolis": "Indianapolis",
        "madison": "Madison",
        "milwaukee": "Milwaukee",
        "nashville": "Nashville",
        "new york": "New York",
        "philadelphia": "Philadelphia",
        "phoenix": "Phoenix",
        "pittsburgh": "Pittsburgh",
        "portland": "Portland",
        "seattle": "Seattle",
    }
    df["city"] = df["city"].replace(city_map)
    
    # Standardize region (use CITY_TO_REGION to guarantee 100% accuracy)
    df["region"] = df["city"].map(CITY_TO_REGION)
    
    # Clean subcategory
    df["subcategory"] = df["subcategory"].astype(str).str.strip().str.title()
    subcat_map = {
        "Headphone": "Headphones",
        "Headphones ": "Headphones",
        "Desk ": "Desk",
        "Paper ": "Paper",
        "Pen ": "Pen",
        "Binder ": "Binder",
        "Chair ": "Chair",
        "Bookcase ": "Bookcase",
        "Monitor ": "Monitor",
        "Laptop ": "Laptop",
    }
    df["subcategory"] = df["subcategory"].replace(subcat_map)
    
    # Standardize category (map uniquely from subcategory)
    df["category"] = df["subcategory"].map(SUBCAT_TO_CAT)
    
    # Standardize sales_channel
    channel_clean = df["sales_channel"].astype(str).str.strip().str.lower()
    channel_map = {
        "in store": "In-Store",
        "in-store": "In-Store",
        "instore": "In-Store",
        "online": "Online",
        "web": "Online",
        "e-commerce": "Online",
        "phone": "Phone",
        "phone order": "Phone",
    }
    df["sales_channel"] = channel_clean.map(channel_map).fillna("Online")
    
    # Standardize customer_type
    cust_clean = df["customer_type"].astype(str).str.strip().str.lower()
    cust_map = {
        "consumer": "Consumer",
        "corporate": "Corporate",
        "corp": "Corporate",
        "home office": "Home Office",
        "homeoffice": "Home Office",
    }
    df["customer_type"] = cust_clean.map(cust_map).fillna("Consumer")
    
    print("[Step 3: Labels] Standardized region, city, category, sales_channel, customer_type.")
    return df


def clean_discount(df: pd.DataFrame) -> pd.DataFrame:
    """Step 4: Normalize 25 discount formats into numeric rates (0.0 to 1.0)."""
    df = df.copy()
    
    def parse_disc(val: str) -> float:
        if not val or pd.isna(val):
            return 0.0
        val = str(val).strip().lower()
        if val in ["", "none", "no discount", "0"]:
            return 0.0
        if "%" in val:
            num = re.sub(r"[^\d.]", "", val)
            return float(num) / 100.0 if num else 0.0
        if "percent" in val:
            num = re.sub(r"[^\d.]", "", val)
            return float(num) / 100.0 if num else 0.0
        try:
            return float(val)
        except ValueError:
            return 0.0

    df["discount"] = df["discount"].apply(parse_disc).round(2)
    print(f"[Step 4: Discount] Normalized discount values. Unique rates: {sorted(df['discount'].unique())}")
    return df


def clean_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Step 5: Normalize 14 return flag codes into boolean."""
    df = df.copy()
    ret_series = df["returned"].astype(str).str.strip()
    
    true_set = {"1", "y", "yes", "true"}
    false_set = {"0", "n", "no", "false"}
    
    def parse_ret(val: str) -> bool:
        low = str(val).strip().lower()
        if low in true_set:
            return True
        return False  # False, unknown, blank, '.', '—' treated as not returned

    df["returned"] = ret_series.apply(parse_ret)
    print(f"[Step 5: Returns] Standardized return flags: {df['returned'].value_counts().to_dict()}")
    return df


def clean_numeric_fields_and_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Step 6: Clean quantity, unit_price, and reconcile revenue."""
    df = df.copy()
    
    # 1. Parse quantity
    def parse_qty(val: str):
        if not val or pd.isna(val):
            return np.nan
        val = str(val).strip().lower()
        if val in WORD_TO_NUM:
            return float(WORD_TO_NUM[val])
        val = re.sub(r"[^\d.]", "", val)
        try:
            return float(val) if val else np.nan
        except ValueError:
            return np.nan

    df["quantity"] = df["quantity"].apply(parse_qty)
    
    # 2. Parse unit_price
    def parse_price(val: str):
        if not val or pd.isna(val):
            return np.nan
        val = re.sub(r"[^\d.]", "", str(val))
        try:
            return float(val) if val else np.nan
        except ValueError:
            return np.nan

    df["unit_price"] = df["unit_price"].apply(parse_price)
    
    # 3. Parse recorded revenue
    def parse_rev(val: str):
        if not val or pd.isna(val):
            return np.nan
        val = str(val).strip()
        if val.lower() in ["unknown", "", "none", "."]:
            return np.nan
        is_neg = val.startswith("-") or (val.startswith("(") and val.endswith(")"))
        clean_num = re.sub(r"[^\d.]", "", val)
        try:
            res = float(clean_num) if clean_num else np.nan
            return -res if is_neg else res
        except ValueError:
            return np.nan

    df["recorded_revenue"] = df["revenue"].apply(parse_rev)
    
    # 4. Impute missing quantity using unit_price, discount, and recorded_revenue
    missing_qty_mask = df["quantity"].isna() & df["unit_price"].notna() & df["recorded_revenue"].notna()
    for idx in df[missing_qty_mask].index:
        p = df.loc[idx, "unit_price"]
        d = df.loc[idx, "discount"]
        r = abs(df.loc[idx, "recorded_revenue"])
        # If recorded revenue was negative return (-60%), unscale to gross
        if df.loc[idx, "recorded_revenue"] < 0:
            r = r / 0.60
        eff_price = p * (1.0 - d)
        if eff_price > 0:
            df.loc[idx, "quantity"] = round(r / eff_price)

    # 5. Impute missing unit_price using subcategory median or formula
    missing_price_mask = df["unit_price"].isna() & df["quantity"].notna() & df["recorded_revenue"].notna()
    for idx in df[missing_price_mask].index:
        q = df.loc[idx, "quantity"]
        d = df.loc[idx, "discount"]
        r = abs(df.loc[idx, "recorded_revenue"])
        if df.loc[idx, "recorded_revenue"] < 0:
            r = r / 0.60
        denom = q * (1.0 - d)
        if denom > 0:
            df.loc[idx, "unit_price"] = round(r / denom, 2)
            
    # For any remaining missing unit_price, impute from subcategory median
    subcat_medians = df.groupby("subcategory")["unit_price"].transform("median")
    df["unit_price"] = df["unit_price"].fillna(subcat_medians)
    df["quantity"] = df["quantity"].fillna(1.0).astype(int)
    
    # 6. Reconcile expected gross revenue: quantity * unit_price * (1 - discount)
    expected_rev = (df["quantity"] * df["unit_price"] * (1.0 - df["discount"])).round(2)
    
    # The primary revenue column for business analysis is gross revenue per line
    df["revenue"] = expected_rev
    
    # Net revenue: If item was returned, revenue is 0.0 (or gross minus refund)
    df["net_revenue"] = np.where(df["returned"], 0.0, df["revenue"])
    
    # Days to ship calculation
    order_dt = pd.to_datetime(df["order_date"])
    ship_dt = pd.to_datetime(df["ship_date"])
    df["shipping_days"] = (ship_dt - order_dt).dt.days
    
    print(f"[Step 6: Numeric & Revenue] Revenue reconciled. Total gross revenue: ${df['revenue'].sum():,.2f}")
    return df


def run_cleaning_pipeline() -> pd.DataFrame:
    """Execute complete cleaning pipeline, write output, and display before/after metrics."""
    print("=" * 60)
    print("EXECUTING RETAIL ORDERS CLEANING PIPELINE")
    print("=" * 60)
    
    df_raw = load_raw_data()
    print(f"Raw dataset loaded: {df_raw.shape[0]} rows, {df_raw.shape[1]} columns.")
    
    df_clean = handle_duplicates(df_raw)
    df_clean = clean_dates(df_clean)
    df_clean = standardize_labels(df_clean)
    df_clean = clean_discount(df_clean)
    df_clean = clean_returns(df_clean)
    df_clean = clean_numeric_fields_and_revenue(df_clean)
    
    # Ensure columns order
    cols_order = [
        "order_id", "order_date", "ship_date", "shipping_days",
        "region", "city", "category", "subcategory", "sales_channel",
        "customer_type", "quantity", "unit_price", "discount",
        "revenue", "net_revenue", "returned", "notes"
    ]
    df_clean = df_clean[cols_order]
    
    # Save cleaned output
    CLEAN_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(CLEAN_CSV_PATH, index=False)
    print(f"\n[DONE] Cleaned data exported successfully to: {CLEAN_CSV_PATH}")
    
    # Also sync clean table to SQLite
    conn = get_db_connection()
    try:
        df_clean.to_sql("orders_clean", conn, if_exists="replace", index=False)
        print("Cleaned data synced to SQLite table 'orders_clean' in db/retail.db")
    finally:
        conn.close()
        
    print(f"Clean rows: {len(df_clean)}, Clean columns: {len(df_clean.columns)}")
    print(f"Total Gross Revenue: ${df_clean['revenue'].sum():,.2f}")
    print(f"Total Orders: {df_clean['order_id'].nunique()}")
    print("=" * 60)
    return df_clean


if __name__ == "__main__":
    run_cleaning_pipeline()
