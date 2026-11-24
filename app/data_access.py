"""Data Access Layer for Streamlit Dashboard.

Loads cleaned data (cached) and provides raw data access exclusively
for the data-quality audit / naive vs corrected view.
"""

from pathlib import Path
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
CLEAN_CSV_PATH = BASE_DIR / "data" / "clean" / "topic3-clean.csv"
RAW_CSV_PATH = BASE_DIR / "data" / "raw" / "topic3-data.csv"


def get_clean_data() -> pd.DataFrame:
    """Load the cleaned dataset for dashboard views with auto-refresh on file change."""
    if not CLEAN_CSV_PATH.exists():
        return pd.DataFrame()
    return _load_clean_cached(CLEAN_CSV_PATH.stat().st_mtime)


@st.cache_data
def _load_clean_cached(mtime: float) -> pd.DataFrame:
    return pd.read_csv(CLEAN_CSV_PATH)


def get_raw_data() -> pd.DataFrame:
    """Load raw dataset strictly for the Data Quality / Naive vs Corrected page."""
    if not RAW_CSV_PATH.exists():
        return pd.DataFrame()
    return _load_raw_cached(RAW_CSV_PATH.stat().st_mtime)


@st.cache_data
def _load_raw_cached(mtime: float) -> pd.DataFrame:
    return pd.read_csv(RAW_CSV_PATH, dtype=str, keep_default_na=False)
