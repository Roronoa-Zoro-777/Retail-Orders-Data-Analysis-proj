"""Shared utilities for Retail Orders Analysis project.

Plumbing functions for loading datasets as text, connecting to SQLite,
and initializing the database tables.
"""

from pathlib import Path
import sqlite3
import pandas as pd

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_CSV_PATH = BASE_DIR / "data" / "raw" / "topic3-data.csv"
CLEAN_CSV_PATH = BASE_DIR / "data" / "clean" / "topic3-clean.csv"
DB_PATH = BASE_DIR / "db" / "retail.db"


def load_raw_data(csv_path: Path = RAW_CSV_PATH) -> pd.DataFrame:
    """Load the raw CSV strictly as string data without auto-converting NaNs or numbers.
    
    Using dtype=str and keep_default_na=False ensures no values like 'NA', 'None',
    or dates are silently converted before profiling.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Raw data file not found at: {csv_path}")
    return pd.read_csv(csv_path, dtype=str, keep_default_na=False)


def load_clean_data(csv_path: Path = CLEAN_CSV_PATH) -> pd.DataFrame:
    """Load the cleaned dataset once generated.
    
    TODO (User): Decide appropriate dtypes and date parsing once cleaning rules are finalized.
    """
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Cleaned data file not found at: {csv_path}. Run src/clean.py or 01_cleaning.ipynb first."
        )
    return pd.read_csv(csv_path)


def get_db_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Get a SQLite database connection."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(raw_csv_path: Path = RAW_CSV_PATH, db_path: Path = DB_PATH) -> None:
    """Initialize db/retail.db with orders_raw loaded as TEXT columns."""
    df_raw = load_raw_data(raw_csv_path)
    conn = get_db_connection(db_path)
    try:
        # Load schema definition
        schema_file = BASE_DIR / "sql" / "00_load_raw.sql"
        if schema_file.exists():
            with open(schema_file, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
        
        # Insert raw rows as text
        df_raw.to_sql("orders_raw", conn, if_exists="replace", index=False)
        print(f"Loaded {len(df_raw)} raw rows into 'orders_raw' in {db_path}")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
