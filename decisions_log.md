# Cleaning Decisions Log

This document tracks all data cleaning decisions made during the project.
All rules applied in Python (`src/clean.py`) and SQL (`sql/02_clean.sql`) match 100%.

| Column | Problem | My rule | Rows affected | Check I ran after |
| :--- | :--- | :--- | :--- | :--- |
| **All Columns** | 16 rows are exact duplicate copies across all 15 columns | Dropped exact duplicate rows (`drop_duplicates(keep='first')`), preserving valid multi-line orders | 16 rows dropped (480 ➔ 464) | Row count: 464 rows; distinct `order_id` count remained intact at 260 |
| **order_date** | Mixed formats (4 formats) + 6 unparseable values (`2025-02-30`, `not recorded`) | Parsed formats with `format='mixed'`. Imputed all 6 invalid dates from sibling lines within the same `order_id` transaction | 6 rows imputed, 464 standardized | Null count: 0 nulls. Date range: 2025-01-02 to 2025-07-30 |
| **ship_date** | Mixed formats (4 formats) + 4 placeholder `TBD` values | Parsed with `format='mixed'`. Coerced `TBD` to NaT / NULL representing orders awaiting dispatch | 4 rows set to NULL | Exactly 4 nulls; delivery duration calculated for all other 460 rows |
| **region** | 21 distinct values (casing, abbreviations `MW`/`NE`/`W.`, blanks, `unknown`, `—`) | Standardized using a 1-to-1 lookup against `city` (all 16 cities map uniquely to 1 of 4 regions) | 141 rows normalized / imputed | Distinct region count: exactly 4 (South: 122, West: 141, Northeast: 108, Midwest: 93), 0 nulls |
| **city** | 40 distinct values (casing, trailing spaces, typos like `SanDiego`) | Trimmed whitespace, title-cased, and mapped `SanDiego` ➔ `San Diego` | 38 rows standardized | Distinct city count: exactly 16 intended cities |
| **category** | 17 distinct values (typo `Furnitures`, casing, underscores, blanks, `unknown`, `.`) | Mapped deterministically from `subcategory` (all 9 subcategories belong to exactly 1 category) | 464 rows standardized | Distinct category count: exactly 3 (Technology: 134, Furniture: 106, Office Supplies: 224), 0 nulls |
| **subcategory** | Trailing whitespace and minor casing | Stripped whitespace and title-cased | 15 rows cleaned | Exactly 9 intended subcategories (3 per category) |
| **sales_channel** | 16 distinct values (`Web`, `E-Commerce`, `Phone Order`, `In Store`, casing, spaces) | Mapped `Web` and `E-Commerce` ➔ `Online`; `Phone Order` ➔ `Phone`; `In Store` ➔ `In-Store` | 180 rows standardized | Distinct channel count: exactly 3 (`Online`: 218, `In-Store`: 183, `Phone`: 63) |
| **customer_type** | 12 distinct values (`Corp`, `HomeOffice`, casing, spaces, `unknown`) | Mapped `Corp` ➔ `Corporate`; `HomeOffice` ➔ `Home Office`; `unknown` defaulted to `Consumer` | 45 rows standardized | Distinct segment count: exactly 3 (`Consumer`: 269, `Corporate`: 144, `Home Office`: 51) |
| **quantity** | Number words (`one` to `five`), suffixes (`3 units`), blanks, `.` | Converted number words to digits, stripped `units`, imputed missing `.` via `revenue / (unit_price * (1 - discount))` | 82 rows cleaned, 13 missing imputed | Minimum quantity = 1, maximum = 6, 0 nulls, all integer types |
| **unit_price** | Symbols (`$`, `USD`), commas, spaces, `—` (16 missing rows) | Stripped non-numeric characters; imputed missing `—` from formula and subcategory medians | 464 parsed, 16 missing imputed | Minimum price = $2.55, maximum = $1,107.72, 0 nulls |
| **discount** | 25 distinct spellings (decimals, percentages, `none`, `No discount`, blanks) | Converted all variants to standard decimal float (0.00 to 0.20); blanks and `none` mapped to `0.00` | 464 rows normalized | Distinct discount rates: `[0.00, 0.05, 0.10, 0.15, 0.20]`, 0 nulls |
| **revenue** | Symbols, commas, `unknown` (24 rows), negative/bracketed values (23 rows) | Identified negative values as 60% return refunds on returned items. Reconciled gross line revenue via `quantity * unit_price * (1 - discount)` | 464 rows reconciled | Total gross revenue = $179,532.37; net revenue = $152,542.41; formula discrepancies > $0.05 = 0 |
| **returned** | 14 distinct codes (`Y`, `Yes`, `TRUE`, `1`, `N`, `No`, `0`, `unknown`, `—`, `.`) | Mapped `1`/`y`/`yes`/`true` ➔ `True`; all other codes ➔ `False` | 464 rows normalized | True = 71 lines (15.3% return rate); False = 393 lines (84.7%) |

---

### Self-Review Quality Checklist
- [x] **Row counts reconcile**: Explained every row: started with 480 raw rows, removed exactly 16 duplicate rows, leaving 464 verified rows across 260 distinct orders.
- [x] **Totals compared**: Compared naive raw revenue ($158,995.35) against cleaned gross revenue ($179,532.37) and net revenue ($152,542.41).
- [x] **Explicit rules**: Every cleaning rule documented above with root cause, transformation logic, and verification check.
- [x] **Missing codes accounted for**: Identified and resolved `''`, `.`, `—`, `unknown`, `TBD`, `not recorded`, and `none`.
- [x] **Grain defined**: The grain of `orders_clean` is **one line item per row**. Distinct orders are evaluated via `COUNT(DISTINCT order_id)`.
- [x] **Spot-checked**: Cross-verified rows against raw input (`ORD-1001`, `ORD-1016`, `ORD-1017`, `ORD-1033`, `ORD-1069`, `ORD-1085`, `ORD-1115`, `ORD-1122`, `ORD-1154`, `ORD-1224`).
- [x] **Limitations stated**: 4 orders carry `TBD` shipping dates (fulfillment speed unknown); negative revenues reflect refund payout conventions rather than order loss.
