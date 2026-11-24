# Retail Orders Analysis Project

A comprehensive data analysis, data auditing, SQL modeling, and dashboarding project based on the **Retail Orders Analysis Practice Workbook**.

---

## 1. Project Directory Structure

```text
data_analysis_proj/
├── data/
│   ├── raw/
│   │   └── topic3-data.csv          # Raw, immutable dataset (480 rows x 15 columns)
│   └── clean/
│       └── topic3-clean.csv         # Cleaned output dataset (generated after cleaning stage)
├── db/
│   └── retail.db                    # SQLite database containing orders_raw and orders_clean
├── src/
│   ├── utils.py                     # Plumbing helpers (data loaders, db connection, init)
│   ├── audit.py                     # Python/pandas audit and profiling checks
│   ├── clean.py                     # Python cleaning pipeline
│   └── questions.py                 # Solutions for business questions Q1 - Q15 (pandas)
├── sql/
│   ├── 00_load_raw.sql              # Raw table DDL (every column TEXT)
│   ├── 01_audit.sql                 # SQL audit queries
│   ├── 02_clean.sql                 # Clean view/table DDL (orders_clean)
│   ├── 03_questions.sql             # SQL solutions for questions Q1 - Q15
│   └── run.py                       # CLI script to execute SQL files against db/retail.db
├── notebooks/
│   ├── 00_audit.ipynb               # Interactive data profiling
│   ├── 01_cleaning.ipynb            # Step-by-step cleaning experiments
│   └── 02_questions.ipynb           # Interactive exploration of Q1 - Q15
├── app/
│   ├── streamlit_app.py             # Streamlit dashboard entry point
│   ├── data_access.py               # Cached data loaders for dashboard
│   └── charts.py                    # Plotly chart generation functions
├── decisions_log.md                 # Complete log of cleaning rules and verifications
├── requirements.txt                 # Project dependencies
└── README.md                        # Project documentation and execution instructions
```

---

## 2. Environment Setup

The project uses a Python virtual environment with SQLite (`sqlite3` is built into Python).

1. **Activate virtual environment**:
   - **Windows PowerShell**:
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   - **Windows Command Prompt**:
     ```cmd
     .venv\Scripts\activate.bat
     ```

2. **Verify installed dependencies**:
   ```powershell
   .venv\Scripts\pip list
   ```

---

## 3. How to Run Each Component

### A. Initialize the Database
Loads the raw CSV into `db/retail.db` under table `orders_raw` with all columns as text:
```powershell
.venv\Scripts\python src/utils.py
```

### B. Run Python Audit, Cleaning, and Questions
- **Run the data-quality audit script**:
  ```powershell
  .venv\Scripts\python src/audit.py
  ```
- **Run the cleaning pipeline** (exports to `data/clean/topic3-clean.csv`):
  ```powershell
  .venv\Scripts\python src/clean.py
  ```
- **Run the business questions analysis**:
  ```powershell
  .venv\Scripts\python src/questions.py
  ```

### C. Run SQL Queries
Use the runner utility `sql/run.py` to execute queries against `db/retail.db`:
- **Run raw data audit queries**:
  ```powershell
  .venv\Scripts\python sql/run.py sql/01_audit.sql
  ```
- **Build the clean table / view (`orders_clean`)**:
  ```powershell
  .venv\Scripts\python sql/run.py sql/02_clean.sql
  ```
- **Run business questions queries (Q1 - Q15)**:
  ```powershell
  .venv\Scripts\python sql/run.py sql/03_questions.sql
  ```

### D. Interactive Jupyter Notebooks
Launch Jupyter to work through notebooks cell by cell:
```powershell
.venv\Scripts\jupyter notebook
```
Open:
- `notebooks/00_audit.ipynb` for data profiling
- `notebooks/01_cleaning.ipynb` for cleaning logic
- `notebooks/02_questions.ipynb` for answering Q1 - Q15

### E. Launch the Streamlit Dashboard
```powershell
.venv\Scripts\streamlit run app/streamlit_app.py
```

---

## 4. Mentoring Workflow & Guardrails

- **Compare Python and SQL**: For every business question, we solve it in both pandas and SQLite, then compare the results to verify consistency.
- **Before/After Checks**: After each cleaning step, verify row counts, column totals, and missing value counts.
- **Log Decisions**: Keep `decisions_log.md` updated with rules, reasoning, and verified checks.
- **Never Overwrite Raw Data**: `data/raw/topic3-data.csv` and SQLite `orders_raw` remain immutable.
