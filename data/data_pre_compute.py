"""
pipeline_all_in_one.py

✅ ONE scalable pipeline that:
1) Builds a clean CODE_GROUPED dataset (overwrite output parquet)
2) Precomputes all Streamlit page-level parquet files

Run:
    python pipeline_all_in_one.py

Recommended outputs:
- data/ardiin_erh_code_grouped_2024_2025.pqt
- streamlit/data/page*/precomputed_*.pqt
"""

from __future__ import annotations

import os
import pandas as pd
from pathlib import Path

# =========================
# CONFIG
# =========================

BASE_DIR = Path(__file__).resolve().parent

INPUT_PARQUET = str(BASE_DIR / "ardiin_erh_2024_2025.pqt") # Put new RAW dataset here 
LOOKUP_CSV = str(BASE_DIR / "loyalty_lookup_2.csv")

# overwrite output
CODE_GROUPED_OUTPUT = "ardiin_erh_code_grouped_combined.pqt"

# filter years (probaly gonna need later on)

# DATE_START = "2024-01-01"
# DATE_END = "2025-12-31"


# Streamlit precompute folders
OUT_DIR_PAGE_1 = os.path.join("pre_computed_data", "page1")
OUT_DIR_PAGE_2 = os.path.join("pre_computed_data", "page2")
OUT_DIR_PAGE_4 = os.path.join("pre_computed_data", "page4")
OUT_DIR_PAGE_5 = os.path.join("pre_computed_data", "page5")
OUT_DIR_PAGE_MISC = os.path.join("pre_computed_data", "page_misc")


# Page 1 outputs
OUT_USER_MONTHLY = os.path.join(OUT_DIR_PAGE_1, "precomputed_user_level_stat_monthly.pqt")
OUT_MONTHLY_SUMMARY = os.path.join(OUT_DIR_PAGE_1, "precomputed_monthly_reward_stat.pqt")
OUT_POINT_CUTOFF = os.path.join(OUT_DIR_PAGE_1, "precomputed_point_cutoff.pqt")

# Page 2 outputs
OUT_GROUPED_REWARD = os.path.join(OUT_DIR_PAGE_2, "precomputed_grouped_reward.pqt")
OUT_TS_NO_PAD = os.path.join(OUT_DIR_PAGE_2, "precomputed_transaction_summary.pqt")
OUT_TS_PAD = os.path.join(OUT_DIR_PAGE_2, "precomputed_transaction_summary_with_pad.pqt")
OUT_CODEGROUP_MAP = os.path.join(OUT_DIR_PAGE_2, "precomputed_codegroup_loyalcode_map.pqt")
OUT_MOVERS_BASE = os.path.join(OUT_DIR_PAGE_2, "precomputed_movers_monthly.pqt")

# Page misc outputs
OUT_COUNTS = os.path.join(OUT_DIR_PAGE_MISC, "precomputed_monthly_bucket_counts.pqt")
OUT_LOYAL_AVG = os.path.join(OUT_DIR_PAGE_MISC, "precomputed_loyal_avg_by_year.pqt")
OUT_REACH_FREQ = os.path.join(OUT_DIR_PAGE_MISC, "precomputed_reach_frequency_by_year.pqt")

# Page 4
OUT_PAGE4_USERS = os.path.join(OUT_DIR_PAGE_4, "users_agg_df.pqt")
OUT_PAGE4_THRESH = os.path.join(OUT_DIR_PAGE_4, "thresholds.pqt")
OUT_PAGE4_SEG_MONTH = os.path.join(OUT_DIR_PAGE_4, "user_segment_monthly_df.pqt")
OUT_PAGE4_SEG_LOYAL = os.path.join(OUT_DIR_PAGE_4, "segment_loyal_summary.pqt")

# Page 5 outputs
OUT_PAGE5_USERS_AGG = os.path.join(OUT_DIR_PAGE_5, "precomputed_users_agg_df.pqt")
OUT_PAGE5_THRESHOLDS = os.path.join(OUT_DIR_PAGE_5, "precomputed_thresholds_by_year.pqt")
OUT_PAGE5_REACH_FREQ = os.path.join(OUT_DIR_PAGE_5, "precomputed_reach_frequency_by_year.pqt")
OUT_PAGE5_MONTHLY_POINTS = os.path.join(OUT_DIR_PAGE_5, "precomputed_monthly_customer_points.pqt")
OUT_PAGE5_USER_MONTH_PROFILE = os.path.join(OUT_DIR_PAGE_5, "precomputed_user_month_profile_achievers.pqt")


# =========================
# HELPERS
# =========================

def ensure_dirs() -> None:
    os.makedirs("pre_computed_data", exist_ok=True)
    os.makedirs(OUT_DIR_PAGE_1, exist_ok=True)
    os.makedirs(OUT_DIR_PAGE_2, exist_ok=True)
    os.makedirs(OUT_DIR_PAGE_4, exist_ok=True)
    os.makedirs(OUT_DIR_PAGE_5, exist_ok=True)
    os.makedirs(OUT_DIR_PAGE_MISC, exist_ok=True)


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip()
    return df


# =========================
# 1) BUILD CODE_GROUPED DATASET
# =========================

GEO_CODES = {
    "BAGANUUR", "BULGAN", "DARKHAN", "ERDENET",
    "KHENTII", "CHOIR", "SAINSHAND", "SELENGE"
}

def map_code_group(code: str) -> str:
    if pd.isna(code):
        return "Financial Transactions"

    code = str(code).strip().upper()

    if code in {
        "10K_TRANSACTION",
        "10K_CHARGE_CUPCAKE",
        "10K_CHARGE_CUPCAKE_1",
        "10K_TULBUR_TSES",
        '10K_TRANSACTION_CARD'
    }:
        return "Core Transactions"

    if code in GEO_CODES:
        return "Campaigns & Events"

    if (
        code.startswith("10K_OPEN")
        or code in {"ARD_SEC", "ARD_SEC1", "ARD_SEC100", "10K_KIDS61"}
        or code.endswith("UTSD")
        or "TETDANS" in code
    ):
        return "Account Opening"

    if (
        "TRANSACTION" in code
        or "CHARGE" in code
        or "CCA" in code
        or "AFFILIATE" in code
        or code in {"LOYALTY_LIMIT", "ACO", "ZEEL_TULULT"}
    ):
        return "Financial Transactions"

    if "INSUR" in code or "DAATGAL" in code:
        return "Insurance"

    if (
        code.startswith(("MARAL", "MARAN"))
        or "KRYPTOS" in code
        or "PNP" in code
        or "LOTTO" in code
        or code == "10K_GAME"
    ):
        return "Merchant & Lifestyle"

    if (
        "SOCIAL" in code
        or "FACEBOOK" in code
        or "SELFIE" in code
        or "MEDEE" in code
        or "TUUH" in code
    ):
        return "Campaigns & Events"

    if (
        code.startswith("10K_BUY")
        or code.startswith("ARD_")
        or "1072" in code
        or "HOS" in code
        or "HOUS" in code
    ):
        return "Investments & Securities"

    if code.startswith((
        "INVESTORWEEK", "TVMEN", "SMART", "HURUNGU",
        "PENSION_SURGALT", "CREDIT_SURGALT", "CREDIT_ZEEL",
        "ARDCOIN", "CREDIT_AIRDROP"
    )):
        return "Campaigns & Events"

    if code.startswith("INF") and len(code) >= 7 and code[3:7].isdigit():
        return "Campaigns & Events"

    return "Other"

def build_code_grouped_dataset() -> pd.DataFrame:
    print("Loading raw parquet:", INPUT_PARQUET)
    df = pd.read_parquet(INPUT_PARQUET)
    df = standardize_columns(df)

    # Remove test / invalid (from your pipeline) :contentReference[oaicite:5]{index=5}
    if "TXN_DESC" in df.columns:
        df = df[df["TXN_DESC"].fillna("").astype(str).str.strip() != "Тест"]
    if "LOYAL_CODE" in df.columns:
        df = df[df["LOYAL_CODE"].fillna("") != "LUNAR_RDXQR"]

    # Fill LOYAL_CODE
    if "LOYAL_CODE" not in df.columns:
        df["LOYAL_CODE"] = "None"
    df["LOYAL_CODE"] = df["LOYAL_CODE"].fillna("None").astype(str)


    # Dates
    df["TXN_DATE"] = pd.to_datetime(df["TXN_DATE"], format="%d-%b-%y", errors="coerce")
    if "POST_DATE" in df.columns:
        df["POST_DATE"] = pd.to_datetime(df["POST_DATE"], format="%d-%b-%y", errors="coerce")
        
    df = df[df["TXN_DATE"].notna()].copy()

    # Filter year range (overwrite output = stable) 
    #df = df[(df["TXN_DATE"] >= DATE_START) & (df["TXN_DATE"] <= DATE_END)].copy()

    # Time cols
    df["year"] = df["TXN_DATE"].dt.year.astype("int16")
    df["MONTH_NUM"] = df["TXN_DATE"].dt.month.astype("int8")
    df["MONTH_NAME"] = df["TXN_DATE"].dt.strftime("%b").str.upper()
    df["year_month"] = df["TXN_DATE"].dt.to_period("M").astype(str)

    # TXN_AMOUNT numeric
    if "TXN_AMOUNT" in df.columns:
        df["TXN_AMOUNT"] = pd.to_numeric(df["TXN_AMOUNT"], errors="coerce").fillna(0)

    # Clean TXN_DESC
    if "TXN_DESC" not in df.columns:
        df["TXN_DESC"] = ""
    df["TXN_DESC"] = df["TXN_DESC"].fillna("").astype(str).str.strip()

    df["TXN_DESC"] = (
        df["TXN_DESC"]
        .str.replace("Крипто Вик", "Crypto Week", regex=False)
        .str.replace("Кривто Вик", "Crypto Week", regex=False)
        .str.replace(".", "", regex=False)
        .str.lower()
    )

    mask_crypto_week = df["TXN_DESC"].str.contains("crypto week", case=False, na=False)
    df.loc[mask_crypto_week, "LOYAL_CODE"] = "ARD_LOTTO"

    # 2) Lotto keywords BUT not crypto week → 10K_GET_LOTTO
    mask_lotto = df["TXN_DESC"].str.contains(r"lotto|6/42|лотто", case=False, na=False)
    mask_not_crypto_week = ~mask_crypto_week

    df.loc[mask_lotto & mask_not_crypto_week, "LOYAL_CODE"] = "10K_GET_LOTTO"

    # Add CODE_GROUP
    df["CODE_GROUP"] = df["LOYAL_CODE"].apply(map_code_group)

    return df


def save_code_grouped(df: pd.DataFrame) -> None:
    ensure_dirs()
    df.to_parquet(CODE_GROUPED_OUTPUT, index=False)
    print("✅ Saved CODE_GROUPED:", CODE_GROUPED_OUTPUT)
    print("Rows:", len(df))
    print("Years:", sorted(df["year"].unique().tolist()))


# =========================
# 2) PRECOMPUTE FILES (PAGE OUTPUTS)
# =========================

def load_lookup() -> dict:
    lookup_df = pd.read_csv(LOOKUP_CSV)
    lookup_df["TXN_DESC"] = lookup_df["TXN_DESC"].astype(str).str.capitalize()
    return dict(zip(lookup_df["LOYAL_CODE"], lookup_df["TXN_DESC"]))


def pre_compute_user_and_monthly_data(df: pd.DataFrame):
    df = df[["CUST_CODE", "TXN_DATE", "TXN_AMOUNT"]].copy()

    user_level_stat_monthly = (
        df.groupby(["CUST_CODE", pd.Grouper(key="TXN_DATE", freq="ME")], observed=True)
        .agg(user_total_point=("TXN_AMOUNT", "sum"))
        .reset_index()
    )

    user_level_stat_monthly["year_month"] = user_level_stat_monthly["TXN_DATE"].dt.to_period("M").astype(str)
    user_level_stat_monthly["month_num"] = user_level_stat_monthly["TXN_DATE"].dt.month.astype("int8")

    # bucket
    point_bins = [0, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, float("inf")]
    labels = [
        "0-49", "50-99", "100-199", "200-299", "300-399",
        "400-499", "500-599", "600-699", "700-799",
        "800-899", "900-999", "1000+",
    ]

    user_level_stat_monthly["point_bucket"] = pd.cut(
        user_level_stat_monthly["user_total_point"],
        bins=point_bins,
        labels=labels,
        right=False,
        include_lowest=True,
    )

    monthly_reward_stat = (
        df.groupby(pd.Grouper(key="TXN_DATE", freq="ME"), observed=True)
        .agg(
            total_points=("TXN_AMOUNT", "sum"),
            total_users=("CUST_CODE", "nunique"),
        )
        .reset_index()
    )

    # passed 1000 counts per month
    user_level_stat_monthly["user_reached_1000"] = (user_level_stat_monthly["user_total_point"] >= 1000).astype("int8")

    passed_1000 = (
        user_level_stat_monthly.groupby("TXN_DATE", observed=True)["user_reached_1000"]
        .sum()
        .reset_index(name="num_user_passed_1000")
    )

    monthly_reward_stat = monthly_reward_stat.merge(passed_1000, on="TXN_DATE", how="left")
    monthly_reward_stat["num_user_passed_1000"] = monthly_reward_stat["num_user_passed_1000"].fillna(0).astype("int32")
    monthly_reward_stat["num_user_fail_1000"] = (monthly_reward_stat["total_users"] - monthly_reward_stat["num_user_passed_1000"]).astype("int32")

    monthly_reward_stat["percentage"] = (
        monthly_reward_stat["num_user_passed_1000"] / monthly_reward_stat["total_users"] * 100
    ).round(2)

    # new users in their first month
    first_month = user_level_stat_monthly.groupby("CUST_CODE", observed=True)["TXN_DATE"].transform("min")
    user_level_stat_monthly["is_first_month"] = (user_level_stat_monthly["TXN_DATE"] == first_month).astype("int8")

    new_users = (
        user_level_stat_monthly.groupby("TXN_DATE", observed=True)["is_first_month"]
        .sum()
        .reset_index(name="total_new_users")
    )

    monthly_reward_stat = monthly_reward_stat.merge(new_users, on="TXN_DATE", how="left")
    monthly_reward_stat["total_new_users"] = monthly_reward_stat["total_new_users"].fillna(0).astype("int32")
    monthly_reward_stat["year_month"] = monthly_reward_stat["TXN_DATE"].dt.to_period("M").astype(str)

    return user_level_stat_monthly, monthly_reward_stat


def load_segment_counts_cutoff_fast(user_level_stat_monthly: pd.DataFrame, cutoffs: list[int]) -> pd.DataFrame:
    out = []
    user_level_stat_monthly_under_1000 = user_level_stat_monthly[user_level_stat_monthly["user_total_point"] < 1000]

    for c in cutoffs:
        tmp = (
            user_level_stat_monthly_under_1000[user_level_stat_monthly_under_1000["user_total_point"] >= c]
            .groupby("year_month", observed=True)
            .size()
            .reset_index(name="Counts")
        )
        tmp["cutoff"] = f"{c}+"
        out.append(tmp)

    segment_counts_all = pd.concat(out, ignore_index=True)

    segment_counts_all["cutoff"] = pd.Categorical(
        segment_counts_all["cutoff"],
        categories=[f"{c}+" for c in cutoffs],
        ordered=True,
    )

    return segment_counts_all


# ---------- PAGE 2 ----------
def get_grouped_reward(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["CODE_GROUP", "year_month"], observed=True)["TXN_AMOUNT"]
        .sum()
        .reset_index(name="TOTAL_AMOUNT")
        .sort_values("year_month")
    )


def build_transaction_summary_no_pad(df: pd.DataFrame, lookup: dict) -> pd.DataFrame:
    ts = (
        df.groupby(["LOYAL_CODE", "year_month", "CODE_GROUP"], observed=True)
        .agg(
            Transaction_Freq=("TXN_AMOUNT", "size"),
            Total_Users=("CUST_CODE", "nunique"),
            Total_Amount=("TXN_AMOUNT", "sum"),
        )
        .reset_index()
        .rename(columns={"CODE_GROUP": "GROUP"})
    )
    ts["DESC"] = ts["LOYAL_CODE"].map(lookup).fillna(ts["LOYAL_CODE"])
    ts["year"] = ts["year_month"].astype(str).str[:4].astype(int)
    return ts


def build_transaction_summary_with_pad(df: pd.DataFrame, lookup: dict) -> pd.DataFrame:
    EPS = 1e-6

    ts = (
        df.groupby(["LOYAL_CODE", "year_month", "CODE_GROUP"], observed=True)
        .agg(
            Transaction_Freq=("TXN_AMOUNT", "size"),
            Total_Users=("CUST_CODE", "nunique"),
            Total_Amount=("TXN_AMOUNT", "sum"),
        )
        .reset_index()
        .rename(columns={"CODE_GROUP": "GROUP"})
    )

    ts["DESC"] = ts["LOYAL_CODE"].map(lookup).fillna(ts["LOYAL_CODE"])

    all_months = ts["year_month"].unique()
    all_groups = ts["GROUP"].unique()

    pad = (
        pd.MultiIndex.from_product([all_months, all_groups], names=["year_month", "GROUP"])
        .to_frame(index=False)
    )

    out = (
        pad.merge(ts, on=["year_month", "GROUP"], how="left")
        .fillna(
            {
                "Transaction_Freq": EPS,
                "Total_Users": EPS,
                "Total_Amount": EPS,
                "LOYAL_CODE": "__PAD__",
                "DESC": "—",
            }
        )
        .sort_values("year_month")
    )

    out["year"] = out["year_month"].astype(str).str[:4].astype(int)
    return out


def build_codegroup_loyalcode_map(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("CODE_GROUP", observed=True)["LOYAL_CODE"]
        .unique()
        .reset_index()
        .rename(columns={"LOYAL_CODE": "LOYAL_CODES"})
    )


def build_movers_monthly(df: pd.DataFrame) -> pd.DataFrame:
    base = df[df["LOYAL_CODE"].notna() & (df["LOYAL_CODE"] != "None")].copy()
    return (
        base.groupby(["year", "LOYAL_CODE", "MONTH_NUM"], as_index=False, observed=True)["TXN_AMOUNT"]
        .sum()
        .sort_values(["year", "LOYAL_CODE", "MONTH_NUM"])
    )


def make_precompute_page_1(df: pd.DataFrame) -> None:
    print("\n PAGE1: precomputing user monthly + monthly summary + cutoff counts...")
    cutoffs = [400, 500, 600, 700, 800, 900]

    user_level_stat_monthly, monthly_reward_stat = pre_compute_user_and_monthly_data(df)
    segment_counts_all = load_segment_counts_cutoff_fast(user_level_stat_monthly, cutoffs)

    user_level_stat_monthly.to_parquet(OUT_USER_MONTHLY, index=False)
    monthly_reward_stat.to_parquet(OUT_MONTHLY_SUMMARY, index=False)
    segment_counts_all.to_parquet(OUT_POINT_CUTOFF, index=False)

    print("Saved:")
    print("-", OUT_USER_MONTHLY)
    print("-", OUT_MONTHLY_SUMMARY)
    print("-", OUT_POINT_CUTOFF)


def make_precompute_page_2(df: pd.DataFrame, loyal_code_to_desc: dict) -> None:
    print("\nPAGE2: precomputing grouped_reward / transaction_summary / codegroup_map / movers...")
    keep_cols = [
        "TXN_AMOUNT",
        "CUST_CODE",
        "LOYAL_CODE",
        "CODE_GROUP",
        "year_month",
        "year",
        "MONTH_NUM",
    ]
    keep_cols = [c for c in keep_cols if c in df.columns]
    base = df[keep_cols].copy()

    grouped_reward = get_grouped_reward(base)
    ts_no_pad = build_transaction_summary_no_pad(base, loyal_code_to_desc)
    ts_pad = build_transaction_summary_with_pad(base, loyal_code_to_desc)
    codegroup_map = build_codegroup_loyalcode_map(base)
    movers_monthly = build_movers_monthly(base)

    grouped_reward.to_parquet(OUT_GROUPED_REWARD, index=False)
    ts_no_pad.to_parquet(OUT_TS_NO_PAD, index=False)
    ts_pad.to_parquet(OUT_TS_PAD, index=False)
    codegroup_map.to_parquet(OUT_CODEGROUP_MAP, index=False)
    movers_monthly.to_parquet(OUT_MOVERS_BASE, index=False)

    print("Saved:")
    print("-", OUT_GROUPED_REWARD)
    print("-", OUT_TS_NO_PAD)
    print("-", OUT_TS_PAD)
    print("-", OUT_CODEGROUP_MAP)
    print("-", OUT_MOVERS_BASE)


# ---------- PAGE MISC ----------
def build_monthly_bucket_counts(df: pd.DataFrame) -> pd.DataFrame:
    user_monthly = (
        df.groupby(["year", "CUST_CODE", "year_month"], observed=True)["TXN_AMOUNT"]
        .sum()
        .reset_index(name="user_total_point")
    )

    point_bins = [0, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, float("inf")]
    labels = [
        "0-49", "50-99", "100-199", "200-299", "300-399",
        "400-499", "500-599", "600-699", "700-799",
        "800-899", "900-999", "1000+",
    ]

    user_monthly["point_bucket"] = pd.cut(
        user_monthly["user_total_point"],
        bins=point_bins,
        labels=labels,
        right=False,
        include_lowest=True,
    )

    counts = (
        user_monthly.groupby(["year", "year_month", "point_bucket"], observed=True)
        .size()
        .reset_index(name="Counts")
    )

    counts["Percent"] = (
        counts["Counts"]
        / counts.groupby(["year", "year_month"], observed=True)["Counts"].transform("sum")
        * 100
    ).round(2)

    return counts


def build_loyal_avg_by_year(df: pd.DataFrame, lookup: dict) -> pd.DataFrame:
    ts = (
        df.groupby(["year", "LOYAL_CODE"], observed=True)
        .agg(
            TXN_AMOUNT=("TXN_AMOUNT", "sum"),
            JRNO=("TXN_AMOUNT", "size"),
        )
        .reset_index()
    )
    ts["AVG"] = (ts["TXN_AMOUNT"] / ts["JRNO"]).round(2)
    ts["PERCENTAGE"] = (
        ts["TXN_AMOUNT"] / ts.groupby("year", observed=True)["TXN_AMOUNT"].transform("sum") * 100
    ).round(2)
    ts["DESC"] = ts["LOYAL_CODE"].map(lookup)
    return ts


def build_reach_frequency(df: pd.DataFrame) -> pd.DataFrame:
    user_monthly = (
        df.groupby(["year", "CUST_CODE", df["TXN_DATE"].dt.to_period("M")], observed=True)["TXN_AMOUNT"]
        .sum()
        .reset_index(name="Total_Points")
    )

    user_monthly["Reached_1000_Flag"] = (user_monthly["Total_Points"] >= 1000).astype("int8")
    reached = user_monthly[user_monthly["Reached_1000_Flag"] == 1]

    counts = (
        reached.groupby(["year", "CUST_CODE"], observed=True)
        .size()
        .reset_index(name="Times_Reached_1000")
    )

    reach_frequency = (
        counts.groupby(["year", "Times_Reached_1000"], observed=True)["CUST_CODE"]
        .size()
        .reset_index(name="Number_of_Users")
    )

    reach_frequency["Total"] = reach_frequency["Times_Reached_1000"] * reach_frequency["Number_of_Users"]
    return reach_frequency


def make_precompute_misc(df: pd.DataFrame, loyal_code_to_desc: dict) -> None:
    print("\nMISC: precomputing bucket counts / loyal avg / reach frequency...")

    counts = build_monthly_bucket_counts(df)
    loyal_avg = build_loyal_avg_by_year(df, loyal_code_to_desc)
    reach_freq = build_reach_frequency(df)

    counts.to_parquet(OUT_COUNTS, index=False)
    loyal_avg.to_parquet(OUT_LOYAL_AVG, index=False)
    reach_freq.to_parquet(OUT_REACH_FREQ, index=False)

    print("Saved:")
    print("-", OUT_COUNTS)
    print("-", OUT_LOYAL_AVG)
    print("-", OUT_REACH_FREQ)

def make_precompute_page_4_all_years(df: pd.DataFrame, loyal_code_to_desc: dict) -> None:
    os.makedirs(OUT_DIR_PAGE_4, exist_ok=True)

    years = sorted(df["year"].unique().tolist())  # use year (consistent)

    all_users = []
    all_seg_monthly = []
    all_loyal_summary = []
    all_thresholds = []

    for y in years:
        df_year = df[df["year"] == y].copy()

        # 1) users monthly agg for this year
        users_agg_df = (
            df_year.groupby(["CUST_CODE", "year_month"], observed=True)
            .agg(
                Total_Points=("TXN_AMOUNT", "sum"),
                Transaction_Count=("TXN_AMOUNT", "size"),
                Unique_Loyal_Codes=("LOYAL_CODE", "nunique"),
                Active_Days=("TXN_DATE", "nunique"),
            )
            .reset_index()
        )

        users_agg_df["Reached_1000_Flag"] = (users_agg_df["Total_Points"] >= 1000).astype("int8")
        users_agg_df["Inactive"] = (users_agg_df["Transaction_Count"] <= 1).astype("int8")

        # 2) thresholds
        reached = users_agg_df[users_agg_df["Reached_1000_Flag"] == 1]
        under = users_agg_df[(users_agg_df["Reached_1000_Flag"] == 0) & (users_agg_df["Inactive"] == 0)]

        thresholds = {
            "year": y,
            "txn_q25": float(under["Transaction_Count"].quantile(0.25)),
            "txn_q75": float(under["Transaction_Count"].quantile(0.75)),
            "days_q25": float(under["Active_Days"].quantile(0.25)),
            "days_q75": float(under["Active_Days"].quantile(0.75)),
            "points_q25": float(under["Total_Points"].quantile(0.25)),
            "points_q75": float(under["Total_Points"].quantile(0.75)),
            "achievers_txn_q25": float(reached["Transaction_Count"].quantile(0.25)) if len(reached) else 0.0,
            "achievers_points_q25": float(reached["Total_Points"].quantile(0.25)) if len(reached) else 0.0,
        }

        all_thresholds.append(thresholds)

        # 3) segmentation
        txn_q75 = thresholds["txn_q75"]
        days_q75 = thresholds["days_q75"]
        achievers_txn_q25 = thresholds["achievers_txn_q25"]

        users_agg_df["User_Segment"] = "Irregular_Participant"
        users_agg_df.loc[
            (users_agg_df["Transaction_Count"] >= txn_q75) & (users_agg_df["Active_Days"] > days_q75),
            "User_Segment"
        ] = "Consistent"

        users_agg_df.loc[
            (users_agg_df["Transaction_Count"] < txn_q75) & (users_agg_df["Active_Days"] <= days_q75),
            "User_Segment"
        ] = "Explorer"

        users_agg_df.loc[
            users_agg_df["Transaction_Count"] >= achievers_txn_q25,
            "User_Segment"
        ] = "High_Effort"

        users_agg_df.loc[
            users_agg_df["Reached_1000_Flag"] == 1,
            "User_Segment"
        ] = "Achiever"

        users_agg_df.loc[
            users_agg_df["Inactive"] == 1,
            "User_Segment"
        ] = "Inactive"

        users_agg_df["year"] = y

        # 4) user segment monthly counts
        user_segment_monthly_df = (
            users_agg_df.groupby(["year", "year_month", "User_Segment"], observed=True)
            .size()
            .reset_index(name="count")
        )

        # 5) segment-loyal summary
        segment_map = users_agg_df[["CUST_CODE", "year_month", "User_Segment"]].copy()

        loyal_code_agg = (
            df_year.groupby(["CUST_CODE", "LOYAL_CODE", "year_month"], observed=True)["TXN_AMOUNT"]
            .sum()
            .reset_index()
        )

        loyal_with_segments = loyal_code_agg.merge(
            segment_map,
            on=["CUST_CODE", "year_month"],
            how="inner",
        )

        segment_loyal_summary = (
            loyal_with_segments.groupby(["User_Segment", "LOYAL_CODE"], observed=True)["TXN_AMOUNT"]
            .sum()
            .reset_index()
        )

        segment_loyal_summary["DESC"] = segment_loyal_summary["LOYAL_CODE"].map(loyal_code_to_desc)
        segment_loyal_summary["year"] = y
        segment_loyal_summary = segment_loyal_summary.sort_values(
            ["User_Segment", "TXN_AMOUNT"], ascending=[True, False]
        )

        all_users.append(users_agg_df)
        all_seg_monthly.append(user_segment_monthly_df)
        all_loyal_summary.append(segment_loyal_summary)

    # concat all years
    users_all_years = pd.concat(all_users, ignore_index=True)
    seg_monthly_all_years = pd.concat(all_seg_monthly, ignore_index=True)
    loyal_summary_all_years = pd.concat(all_loyal_summary, ignore_index=True)
    thresholds_all_years = pd.DataFrame(all_thresholds)

    # export
    users_all_years.to_parquet(OUT_PAGE4_USERS, index=False)
    thresholds_all_years.to_parquet(OUT_PAGE4_THRESH, index=False)
    seg_monthly_all_years.to_parquet(OUT_PAGE4_SEG_MONTH, index=False)
    loyal_summary_all_years.to_parquet(OUT_PAGE4_SEG_LOYAL, index=False)

    print("\n PAGE4 DONE")
    print("-", OUT_PAGE4_USERS)
    print("-", OUT_PAGE4_THRESH)
    print("-", OUT_PAGE4_SEG_MONTH)
    print("-", OUT_PAGE4_SEG_LOYAL)


# ---------- PAGE 5 ----------
def page5_users_agg_by_monthnum(df_all: pd.DataFrame) -> pd.DataFrame:
    out = (
        df_all.groupby(["year", "CUST_CODE", "MONTH_NUM", "MONTH_NAME"], observed=True)
        .agg(
            Total_Points=("TXN_AMOUNT", "sum"),
            Transaction_Count=("TXN_AMOUNT", "size"),
            Unique_Loyal_Codes=("LOYAL_CODE", "nunique"),
            Active_Days=("TXN_DATE", "nunique"),
        )
        .reset_index()
    )

    out["Reached_1000_Flag"] = (out["Total_Points"] >= 1000).astype("int8")
    out["Inactive"] = (out["Transaction_Count"] <= 1).astype("int8")
    return out


def page5_thresholds_by_year(users_agg_all_years: pd.DataFrame) -> pd.DataFrame:
    out = []

    for y in sorted(users_agg_all_years["year"].unique()):
        dfy = users_agg_all_years[users_agg_all_years["year"] == y].copy()

        reached = dfy[dfy["Reached_1000_Flag"] == 1]
        under = dfy[(dfy["Reached_1000_Flag"] == 0) & (dfy["Inactive"] == 0)]

        thresholds = {
            "year": y,
            "txn_q25": float(under["Transaction_Count"].quantile(0.25)),
            "txn_q75": float(under["Transaction_Count"].quantile(0.75)),
            "days_q25": float(under["Active_Days"].quantile(0.25)),
            "days_q75": float(under["Active_Days"].quantile(0.75)),
            "points_q25": float(under["Total_Points"].quantile(0.25)),
            "points_q75": float(under["Total_Points"].quantile(0.75)),
            "achievers_txn_q25": float(reached["Transaction_Count"].quantile(0.25)) if len(reached) else 0.0,
        }
        out.append(thresholds)

    return pd.DataFrame(out)


def page5_reach_frequency(users_agg_all_years: pd.DataFrame) -> pd.DataFrame:
    reached = users_agg_all_years[users_agg_all_years["Reached_1000_Flag"] == 1]

    user_counts = (
        reached.groupby(["year", "CUST_CODE"], observed=True)
        .size()
        .reset_index(name="Times_Reached_1000")
    )

    reach_frequency = (
        user_counts.groupby(["year", "Times_Reached_1000"], observed=True)["CUST_CODE"]
        .size()
        .reset_index(name="Number_of_Users")
        .sort_values(["year", "Times_Reached_1000"])
    )

    reach_frequency["Total"] = reach_frequency["Times_Reached_1000"] * reach_frequency["Number_of_Users"]
    return reach_frequency


def page5_monthly_customer_points(df_all: pd.DataFrame) -> pd.DataFrame:
    return (
        df_all.groupby(["year", "MONTH_NUM", "MONTH_NAME", "CUST_CODE"], observed=True)["TXN_AMOUNT"]
        .sum()
        .reset_index(name="Total_Points")
    )


def page5_user_month_profile_achievers(df_all: pd.DataFrame, users_agg_all_years: pd.DataFrame) -> pd.DataFrame:
    achiever_months = users_agg_all_years.loc[
        users_agg_all_years["Reached_1000_Flag"] == 1,
        ["year", "CUST_CODE", "MONTH_NUM"]
    ].copy()

    df_ach = df_all.merge(achiever_months, on=["year", "CUST_CODE", "MONTH_NUM"], how="inner")

    monthly_totals = (
        df_ach.groupby(["year", "CUST_CODE", "MONTH_NUM"], observed=True)["TXN_AMOUNT"]
        .sum()
        .reset_index(name="True_Monthly_Total")
    )

    loyal_code_agg = (
        df_ach.groupby(["year", "CUST_CODE", "MONTH_NUM", "LOYAL_CODE"], observed=True)["TXN_AMOUNT"]
        .sum()
        .reset_index()
    )

    final_df = loyal_code_agg.merge(monthly_totals, on=["year", "CUST_CODE", "MONTH_NUM"], how="left")

    final_df = final_df[final_df["LOYAL_CODE"].notna()]
    final_df = final_df[final_df["LOYAL_CODE"] != "10K_PURCH_INSUR"]

    final_df["Normalized_Points"] = (final_df["TXN_AMOUNT"] / final_df["True_Monthly_Total"]) * 1000

    user_month_profile = (
        final_df.groupby(["year", "CUST_CODE", "MONTH_NUM", "LOYAL_CODE"], observed=True)["Normalized_Points"]
        .sum()
        .reset_index()
    )

    return user_month_profile


def make_precompute_page_5(df_all: pd.DataFrame) -> None:
    print("\nPAGE5: computing users agg + thresholds + reach freq + heavy achiever profile...")

    users_agg_all = page5_users_agg_by_monthnum(df_all)
    thresholds_all = page5_thresholds_by_year(users_agg_all)
    reach_freq_all = page5_reach_frequency(users_agg_all)
    monthly_points_all = page5_monthly_customer_points(df_all)

    print("PAGE5 heavy step: user_month_profile_achievers ...")
    user_month_profile = page5_user_month_profile_achievers(df_all, users_agg_all)

    users_agg_all.to_parquet(OUT_PAGE5_USERS_AGG, index=False)
    thresholds_all.to_parquet(OUT_PAGE5_THRESHOLDS, index=False)
    reach_freq_all.to_parquet(OUT_PAGE5_REACH_FREQ, index=False)
    monthly_points_all.to_parquet(OUT_PAGE5_MONTHLY_POINTS, index=False)
    user_month_profile.to_parquet(OUT_PAGE5_USER_MONTH_PROFILE, index=False)

    print("Saved:")
    print("-", OUT_PAGE5_USERS_AGG)
    print("-", OUT_PAGE5_THRESHOLDS)
    print("-", OUT_PAGE5_REACH_FREQ)
    print("-", OUT_PAGE5_MONTHLY_POINTS)
    print("-", OUT_PAGE5_USER_MONTH_PROFILE)


# =========================
# MASTER RUNNER
# =========================

def run_pipeline(run_precompute: bool = True) -> None:
    print("\n" + "=" * 60)
    print("[PIPELINE] START")
    print("=" * 60)

    ensure_dirs()
    print("[INIT] ensured output folders: pre_computed_data/...")

    # 1) build + save main dataset
    print("\n[STEP 1] build CODE_GROUPED dataset")
    print(f"[LOAD] INPUT_PARQUET = {INPUT_PARQUET}")
    df = build_code_grouped_dataset()

    print(f"[SAVE] CODE_GROUPED_OUTPUT = {CODE_GROUPED_OUTPUT}")
    save_code_grouped(df)

    if not run_precompute:
        print("\n[INFO] run_precompute=False -> skipping page precompute outputs")
        print("[PIPELINE] COMPLETE")
        return

    # 2) lookup + precompute smaller pieces
    print("\n[STEP 2] load lookup mapping")
    print(f"[LOAD] LOOKUP_CSV = {LOOKUP_CSV}")
    loyal_code_to_desc = load_lookup()
    print(f"[INFO] lookup mappings loaded: {len(loyal_code_to_desc):,}")

    print("\n[PAGE 1] precompute outputs")
    make_precompute_page_1(df)

    print("\n[PAGE 2] precompute outputs")
    make_precompute_page_2(df, loyal_code_to_desc)

    print("\n[MISC] precompute outputs")
    make_precompute_misc(df, loyal_code_to_desc)

    print("\n[PAGE 4] precompute outputs")
    make_precompute_page_4_all_years(df, loyal_code_to_desc)

    print("\n[PAGE 5] precompute outputs")
    make_precompute_page_5(df)

    print("\n" + "=" * 60)
    print("[PIPELINE] COMPLETE")
    print("=" * 60)


def main():
    run_pipeline(run_precompute=True)


if __name__ == "__main__":
    main()
