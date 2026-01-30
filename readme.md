# Ardiin Erh Streamlit Dashboard (Precomputed Pipeline)

This repository contains a Streamlit dashboard backed by a precomputation pipeline.

The pipeline is designed to:
- Build a clean master dataset (`CODE_GROUPED`)
- Generate small precomputed `.pqt` files for each Streamlit page
- Avoid heavy computations inside Streamlit runtime (faster startup and better performance)

---

## Project Structure (Key Files)
```text
.
├── pipeline_all_in_one.py
├── data/
│   ├── data_loader.py
│   ├── data_pre_compute.py
│   ├── loyalty_lookup_2.csv
│   ├── ardiin_erh_code_grouped_combined.pqt
│   └── pre_computed_data/
│       ├── page1/
│       ├── page2/
│       ├── page4/
│       ├── page5/
│       └── page_misc/
└── pages/
    ├── page1.py
    ├── page2.py
    ├── page4.py
    └── page5.py
```

---

## Data Precompute Pipeline (CODE_GROUPED + Streamlit Parquet Outputs)

### What the Pipeline Does

This pipeline runs in two major phases:

#### 1) Build CODE_GROUPED Master Dataset
Creates a cleaned dataset and adds a `CODE_GROUP` column based on business logic rules from `LOYAL_CODE`.

**Output:**
- `data/ardiin_erh_code_grouped_combined.pqt`

#### 2) Precompute Streamlit Page Parquet Files
Generates smaller `.pqt` files used by Streamlit pages.

**Output root folder:**
- `data/pre_computed_data/`

---

## Required Input Files

To run the pipeline, you need:

### 1) Master transaction parquet file
Example file used in code:
- `ardiin_erh_2024_2025.pqt` (if stored locally) 

### Required Columns (Input Dataset)

To run the pipeline and generate all Streamlit precomputed outputs correctly, the raw dataset is expected to contain the following columns:

```text
    TXN_DATE
    TXN_CODE
    TXN_DESC
    TXN_AMOUNT
    CUST_CODE
    LOYAL_CODE
```

### 2) Lookup file (required)
- `data/loyalty_lookup_2.csv`

**Note:** Very large datasets (initial RAW dataset) are intentionally excluded from GitHub to avoid push/deployment issues.

---

## Outputs Generated

All generated files are stored under `data/pre_computed_data/`

### Page 1 Outputs (`data/pre_computed_data/page1/`)
- `precomputed_user_level_stat_monthly.pqt`
- `precomputed_monthly_reward_stat.pqt`
- `precomputed_point_cutoff.pqt`

### Page 2 Outputs (`data/pre_computed_data/page2/`)
- `precomputed_grouped_reward.pqt`
- `precomputed_transaction_summary.pqt`
- `precomputed_transaction_summary_with_pad.pqt`
- `precomputed_codegroup_loyalcode_map.pqt`
- `precomputed_movers_monthly.pqt`

### Page 4 Outputs (`data/pre_computed_data/page4/`)
- `users_agg_df.pqt`
- `thresholds.pqt`
- `user_segment_monthly_df.pqt`
- `segment_loyal_summary.pqt`

### Page 5 Outputs (`data/pre_computed_data/page5/`)
- `precomputed_users_agg_df.pqt`
- `precomputed_thresholds_by_year.pqt`
- `precomputed_reach_frequency_by_year.pqt`
- `precomputed_monthly_customer_points.pqt`
- `precomputed_user_month_profile_achievers.pqt`

### Misc Outputs (`data/pre_computed_data/page_misc/`)
- `precomputed_monthly_bucket_counts.pqt`
- `precomputed_loyal_avg_by_year.pqt`
- `precomputed_reach_frequency_by_year.pqt`

---

## Data Loader Module

### Overview

`data_loader.py` is the central module that handles **all data loading and caching** for the Streamlit app.

Instead of repeating `pd.read_parquet()` and preprocessing logic inside every Streamlit page, each page imports functions from `data_loader.py` and reuses the same cached datasets.

**Benefits:**
- Faster loading after first run (cache)
- Less repeated disk reads
- Consistent dataframe schema across pages
- Cleaner Streamlit page scripts

### Core Functions

#### 1. Main Dataset Loader
```python
@st.cache_resource(show_spinner=True)
def load_data() -> pd.DataFrame:
```

Loads the main dataset once from `data/ardiin_erh_code_grouped_combined.pqt`

**Processing steps:**
- Keeps only the required columns (RAM optimization)
- Converts `TXN_DATE` to datetime and generates:
  - `year`
  - `year_month`
- Converts key columns to optimized dtypes (`category`, `int16`, `int32`)

This dataframe is treated as the base dataset used across the whole app.

#### 2. Lookup Loader
```python
@st.cache_data(show_spinner=False)
def get_lookup() -> dict:
```

Loads a `LOYAL_CODE` → `TXN_DESC` mapping from `data/loyalty_lookup_2.csv`

This is used to display readable labels in charts/tables instead of showing raw `LOYAL_CODE`.

#### 3. Precomputed Data Loaders

Each Streamlit page loads its data using specialized functions:

- `load_precomputed_page1()`
- `load_precomputed_page2()`
- `load_precomputed_page4()`
- `load_precomputed_page_misc_*()`
- `load_precomputed_page5_*()`

**Example usage:**
```python
from data_loader import load_precomputed_page2

grouped_reward, transaction_summary, transaction_summary_with_pad = load_precomputed_page2()
```

Because these files are already aggregated, the page only needs to visualize them (no heavy computation required).

---

## CODE_GROUP Categories

The pipeline assigns a `CODE_GROUP` column using mapping rules derived from `LOYAL_CODE`.

Main categories include:

- Core Transactions
- Financial Transactions
- Account Opening
- Investments & Securities
- Merchant & Lifestyle
- Insurance
- Campaigns & Events
- Other

---

## Data Cleaning Rules

### Invalid / Test Filtering

Rows are removed when:
- `TXN_DESC == "Тест"`
- `LOYAL_CODE == "LUNAR_RDXQR"`

### Missing Values
- Missing `LOYAL_CODE` values are filled with `"None"`

### Date Parsing
Dates are parsed using format: `%d-%b-%y`

**Example:** `01-JAN-24`

---

## How `loyalty_lookup_2.csv` is Generated

`loyalty_lookup_2.csv` is a lookup table that maps **`LOYAL_CODE` → `TXN_DESC`** (human-readable description).

Since the raw dataset can contain multiple `TXN_DESC` values for the same `LOYAL_CODE` (typos, different wording), the lookup is generated by:

1. Cleaning and normalizing `TXN_DESC` (lowercase, remove punctuation, fix known typos)
2. Grouping by `LOYAL_CODE`
3. Selecting the **most frequent** `TXN_DESC` for each `LOYAL_CODE` (canonical 1–1 mapping)
4. Exporting the result to `loyalty_lookup_2.csv`

This lookup is then used in the pipeline/Streamlit app to display consistent labels.

---

## Installation & Setup

### Requirements

Install dependencies using:
```bash
pip install -r requirements.txt
```

### Running the Pipeline

To generate all precomputed data files:
```bash
python date_pre_compute.py
```

### Running the Streamlit Dashboard

After running the pipeline:
```bash
streamlit run app.py
```

---

## Notes

- The precomputed pipeline approach significantly improves Streamlit app performance
- All heavy data processing is done offline in the pipeline
- Streamlit pages only handle visualization and user interaction
- Cache decorators (`@st.cache_resource`, `@st.cache_data`) ensure data is loaded only once per session