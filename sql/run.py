"""SQL Runner Utility.

Executes a specified SQL file against db/retail.db and formats output.
Usage:
    python sql/run.py sql/01_audit.sql
    python sql/run.py sql/02_clean.sql
    python sql/run.py sql/03_questions.sql
"""

import sys
import re
from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db" / "retail.db"


def clean_sql_comments(sql_text: str) -> str:
    """Remove single-line comments (-- ...) and block comments (/* ... */) before splitting."""
    # Remove block comments
    no_block = re.sub(r"/\*.*?\*/", "", sql_text, flags=re.DOTALL)
    # Remove line comments
    clean_lines = []
    for line in no_block.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        cleaned = re.sub(r"--.*$", "", line)
        if cleaned.strip():
            clean_lines.append(cleaned)
    return "\n".join(clean_lines)


def run_sql_file(sql_file_path: str | Path, db_path: Path = DB_PATH) -> None:
    path = Path(sql_file_path)
    if not path.is_absolute():
        path = BASE_DIR / path
        
    if not path.exists():
        print(f"Error: SQL file not found at: {path}")
        sys.exit(1)
        
    if not db_path.exists():
        print(f"Error: Database not found at: {db_path}. Run 'python src/utils.py' first to initialize.")
        sys.exit(1)
        
    print(f"Connecting to database: {db_path}")
    print(f"Executing: {path.name}\n" + "=" * 60)
    
    with open(path, "r", encoding="utf-8") as f:
        raw_content = f.read()
        
    cleaned_content = clean_sql_comments(raw_content)
    # Split statements by semicolon
    statements = [stmt.strip() for stmt in cleaned_content.split(";") if stmt.strip()]
    
    if not statements:
        print("No active SQL statements found (all lines are comments or scaffolds).")
        print("Uncomment or write a query to see results!")
        print("=" * 60)
        return
        
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    total_executed = 0
    for stmt in statements:
        print(f"\n[QUERY #{total_executed + 1}]:")
        preview_lines = stmt.splitlines()[:4]
        print("  " + "\n  ".join(preview_lines))
        if len(stmt.splitlines()) > 4:
            print("  ...")
            
        try:
            cursor.execute(stmt)
            total_executed += 1
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                print(f"-> Returned {len(rows)} row(s):")
                print(" | ".join(columns))
                print("-" * 60)
                for r in rows[:15]:
                    print(" | ".join(str(val) if val is not None else "NULL" for val in r))
                if len(rows) > 15:
                    print(f"... ({len(rows) - 15} more rows)")
            else:
                conn.commit()
                print(f"-> Statement executed successfully ({cursor.rowcount} row(s) affected).")
        except sqlite3.Error as e:
            print(f"-> SQLite Error: {e}")
            
    conn.close()
    print("\n" + "=" * 60)
    print(f"Execution complete. Total queries executed: {total_executed}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
    else:
        target_file = "sql/01_audit.sql"
    run_sql_file(target_file)
