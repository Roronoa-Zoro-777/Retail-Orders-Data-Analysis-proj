"""Data-Quality Audit Module.

Profiles the 10 data quality issues documented in the workbook.
"""

import sys
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from src.utils import load_raw_data


def audit_exact_duplicates(df: pd.DataFrame) -> None:
    print("=" * 60)
    print("1. EXACT DUPLICATE ROWS")
    dup_mask = df.duplicated(keep="first")
    dup_count = dup_mask.sum()
    print(f"Total exact duplicate rows found: {dup_count} (Workbook target: 16)")
    if dup_count > 0:
        print("Sample duplicate row IDs:")
        print(df[dup_mask]["order_id"].head(5).tolist())


def audit_order_ids(df: pd.DataFrame) -> None:
    print("=" * 60)
    print("2. REPEATED ORDER IDs & GRAIN")
    unique_ids = df["order_id"].nunique()
    total_rows = len(df)
    counts = df["order_id"].value_counts()
    multi_line = (counts > 1).sum()
    single_line = (counts == 1).sum()
    print(f"Total rows: {total_rows}, Unique order_ids: {unique_ids} (Workbook target: 260)")
    print(f"Orders with 1 line: {single_line}, Orders with >1 line: {multi_line}")


def audit_date_formats_and_placeholders(df: pd.DataFrame) -> None:
    print("=" * 60)
    print("3. DATE FORMATS & PLACEHOLDERS")
    print("\n--- order_date samples & unparseable ---")
    unparseable_order = []
    for val in df["order_date"].unique():
        parsed = pd.to_datetime(val, errors="coerce")
        if pd.isna(parsed):
            count = (df["order_date"] == val).sum()
            unparseable_order.append((val, count))
    print(f"Unparseable order_dates ({len(unparseable_order)} distinct, total rows: {sum(c for _, c in unparseable_order)}):")
    for val, count in unparseable_order:
        print(f"  '{val}': {count} rows")

    print("\n--- ship_date samples & placeholders ---")
    unparseable_ship = []
    for val in df["ship_date"].unique():
        parsed = pd.to_datetime(val, errors="coerce")
        if pd.isna(parsed):
            count = (df["ship_date"] == val).sum()
            unparseable_ship.append((val, count))
    print(f"Unparseable ship_dates ({len(unparseable_ship)} distinct, total rows: {sum(c for _, c in unparseable_ship)}):")
    for val, count in unparseable_ship:
        print(f"  '{val}': {count} rows")


def audit_categorical_labels(df: pd.DataFrame) -> None:
    print("=" * 60)
    print("4. CATEGORICAL LABELS")
    for col in ["region", "city", "category", "sales_channel", "customer_type"]:
        unique_vals = sorted(df[col].unique().tolist())
        print(f"\nColumn '{col}': {len(unique_vals)} distinct values:")
        print(unique_vals)


def audit_numeric_text_fields(df: pd.DataFrame) -> None:
    print("=" * 60)
    print("5. NUMERIC FIELDS STORED AS TEXT")
    print("Sample quantity values that are not pure digits:")
    non_digit_qty = [q for q in df["quantity"].unique() if not q.strip().isdigit()]
    print(non_digit_qty)

    print("\nSample unit_price values:")
    print(df["unit_price"].unique()[:10])

    print("\nSample revenue values:")
    print(df["revenue"].unique()[:10])


def audit_negative_and_bracketed_revenue(df: pd.DataFrame) -> None:
    print("=" * 60)
    print("6. NEGATIVE AND BRACKETED REVENUE")
    neg_mask = df["revenue"].str.contains(r"^-|^\(", regex=True, na=False)
    neg_rows = df[neg_mask]
    print(f"Found {len(neg_rows)} negative/bracketed revenue rows:")
    for _, row in neg_rows[["order_id", "quantity", "unit_price", "discount", "revenue", "returned"]].iterrows():
        print(f"  {row['order_id']} | qty: {row['quantity']} | price: {row['unit_price']} | disc: {row['discount']} | rev: {row['revenue']} | returned: {row['returned']}")


def audit_discount_formats(df: pd.DataFrame) -> None:
    print("=" * 60)
    print("7. DISCOUNT FORMATS")
    disc_vals = df["discount"].value_counts(dropna=False)
    print(f"Found {len(disc_vals)} distinct discount values (Workbook target: 25):")
    for val, count in disc_vals.items():
        print(f"  '{val}': {count}")


def audit_return_flag_codes(df: pd.DataFrame) -> None:
    print("=" * 60)
    print("8. RETURN FLAG CODES")
    ret_vals = df["returned"].value_counts(dropna=False)
    print(f"Found {len(ret_vals)} distinct returned codes (Workbook target: 14):")
    for val, count in ret_vals.items():
        print(f"  '{val}': {count}")


def audit_missing_value_representations(df: pd.DataFrame) -> None:
    print("=" * 60)
    print("9. MISSING-VALUE CODES")
    missing_codes = ["", ".", "—", "-", "unknown", "TBD", "not recorded", "none"]
    for code in missing_codes:
        total = (df == code).sum().sum()
        cols_hit = {col: (df[col] == code).sum() for col in df.columns if (df[col] == code).sum() > 0}
        print(f"Code '{code}': total occurrences = {total}, columns: {cols_hit}")


def audit_internal_consistency(df: pd.DataFrame) -> None:
    print("=" * 60)
    print("10. INTERNAL FORMULA CONSISTENCY AUDIT")
    print("Components to check: revenue vs quantity * unit_price * (1 - discount)")


def run_full_audit() -> None:
    print("Loading raw data...")
    df = load_raw_data()
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns.\n")
    audit_exact_duplicates(df)
    audit_order_ids(df)
    audit_date_formats_and_placeholders(df)
    audit_categorical_labels(df)
    audit_numeric_text_fields(df)
    audit_negative_and_bracketed_revenue(df)
    audit_discount_formats(df)
    audit_return_flag_codes(df)
    audit_missing_value_representations(df)
    audit_internal_consistency(df)
    print("\n" + "=" * 60)
    print("Audit profiling complete!")


if __name__ == "__main__":
    run_full_audit()
