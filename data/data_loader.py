import streamlit as st
import pandas as pd
from pathlib import Path
# ------------------- BASE DATA -------------------

DATA_PATH = Path("data/ardiin_erh_code_grouped_combined.pqt")
LOOKUP_PATH = Path("data/loyalty_lookup_2.csv")

@st.cache_resource(show_spinner=True)
def load_data() -> pd.DataFrame:
    """
    Load the main parquet ONCE as a resource (best for big data).
    Reduce columns early to save RAM.
    """
    df = pd.read_parquet(DATA_PATH)

    # Keep only columns used across your pages (reduce RAM massively)
    keep_cols = [
        "TXN_DATE",
        "CUST_CODE",
        "MONTH_NUM",
        "MONTH_NAME",
        "TXN_AMOUNT",
        "LOYAL_CODE",
        "JRNO",
        "CODE_GROUP"
    ]
    existing = [c for c in keep_cols if c in df.columns]
    df = df[existing].copy()

    # Clean / types
    df["TXN_DATE"] = pd.to_datetime(df["TXN_DATE"], errors="coerce")
    df = df[df["TXN_DATE"].notna()].copy()

    df["year"] = df["TXN_DATE"].dt.year.astype("int16")

    # If you still need year_month sometimes
    df["year_month"] = df["TXN_DATE"].dt.to_period("M").astype(str)

    # Dtypes
    df["CUST_CODE"] = df["CUST_CODE"].astype("category")
    df["MONTH_NUM"] = df["MONTH_NUM"].astype("int16")
    df["TXN_AMOUNT"] = pd.to_numeric(df["TXN_AMOUNT"], errors="coerce").fillna(0).astype("int32")

    # LOYAL_CODE is often high-cardinality -> category saves RAM
    if "LOYAL_CODE" in df.columns:
        df["LOYAL_CODE"] = df["LOYAL_CODE"].astype("category")

    return df


@st.cache_data(show_spinner=False)
def get_lookup() -> dict:
    lookup_df = pd.read_csv(LOOKUP_PATH)
    return dict(zip(lookup_df["LOYAL_CODE"], lookup_df["TXN_DESC"].astype(str).str.capitalize()))


@st.cache_data(show_spinner=False)
def filter_df_by_year(df: pd.DataFrame, year: int) -> pd.DataFrame:
    # No need for df.copy() before filter; filter first then copy
    out = df[df["year"] == year]
    return out.copy()

@st.cache_data(show_spinner=False) 
def get_most_growing_loyal_code_from_monthly(movers_monthly: pd.DataFrame, year: int): 
    df = movers_monthly[movers_monthly["year"] == year].copy() # Enforce > 6 active months 
    df = df.groupby("LOYAL_CODE", observed=True).filter(lambda x: x["MONTH_NUM"].nunique() > 6) 
    stats = df.groupby("LOYAL_CODE", observed=True)["TXN_AMOUNT"].agg(first="first", last="last") 
    stats = stats[stats["first"] > 0] 
    stats["PCT_INCREASE"] = ((stats["last"] - stats["first"]) / stats["first"]) * 100 
    movers_df = ( stats[(stats["PCT_INCREASE"] > 20) & (stats["last"] > 100_000)] 
                 .sort_values("PCT_INCREASE", ascending=False).head(4).reset_index() ) 
    return movers_df["LOYAL_CODE"], movers_df

# ------------------- PRECOMPUTED LOADERS -------------------

@st.cache_data(show_spinner=False)
def load_precomputed_page1():
    user_level_stat_monthly = pd.read_parquet("data/pre_computed_data/page1/precomputed_user_level_stat_monthly.pqt", engine="pyarrow")
    monthly_reward_stat = pd.read_parquet("data/pre_computed_data/page1/precomputed_monthly_reward_stat.pqt", engine="pyarrow")
    point_cutoff = pd.read_parquet("data/pre_computed_data/page1/precomputed_point_cutoff.pqt", engine="pyarrow")
    return user_level_stat_monthly, monthly_reward_stat, point_cutoff


@st.cache_data(show_spinner=False)
def load_precomputed_page2():
    grouped_reward = pd.read_parquet("data/pre_computed_data/page2/precomputed_grouped_reward.pqt", engine="pyarrow")
    transaction_summary = pd.read_parquet("data/pre_computed_data/page2/precomputed_transaction_summary.pqt", engine="pyarrow")
    transaction_summary_with_pad = pd.read_parquet("data/pre_computed_data/page2/precomputed_transaction_summary_with_pad.pqt", engine="pyarrow")
    return grouped_reward, transaction_summary, transaction_summary_with_pad


@st.cache_data(show_spinner=False)
def load_page2_codegroup_map():
    return pd.read_parquet("data/pre_computed_data/page2/precomputed_codegroup_loyalcode_map.pqt", engine="pyarrow")


@st.cache_data(show_spinner=False)
def load_page2_movers_monthly():
    return pd.read_parquet("data/pre_computed_data/page2/precomputed_movers_monthly.pqt", engine="pyarrow")


@st.cache_data(show_spinner=False)
def load_precomputed_page4():
    users_agg_df = pd.read_parquet("data/pre_computed_data/page4/users_agg_df.pqt", engine="pyarrow")
    thresholds_df = pd.read_parquet("data/pre_computed_data/page4/thresholds.pqt", engine="pyarrow")
    user_segment_monthly_df = pd.read_parquet("data/pre_computed_data/page4/user_segment_monthly_df.pqt", engine="pyarrow")
    segment_loyal_summary = pd.read_parquet("data/pre_computed_data/page4/segment_loyal_summary.pqt", engine="pyarrow")
    return users_agg_df, thresholds_df, user_segment_monthly_df, segment_loyal_summary


# -------------------- PAGE 5 (OPTIMIZED) --------------------

def get_users_agg_by_monthnum(df_year: pd.DataFrame) -> pd.DataFrame:

    users_agg_df = (
        df_year.groupby(["CUST_CODE", "MONTH_NUM"], observed=True)
        .agg(
            Total_Points=("TXN_AMOUNT", "sum"),
            Transaction_Count=("JRNO", "count"),
            Unique_Loyal_Codes=("LOYAL_CODE", "nunique"),
            Active_Days=("TXN_DATE", "nunique"),
        )
        .reset_index()
    )

    users_agg_df["Reached_1000_Flag"] = (users_agg_df["Total_Points"] >= 1000).astype("int8")
    users_agg_df["Inactive"] = (users_agg_df["Transaction_Count"] <= 1).astype("int8")

    return users_agg_df


def get_page5_thresholds(users_agg_df: pd.DataFrame) -> dict:

    user_under_1000 = users_agg_df[(users_agg_df["Reached_1000_Flag"] == 0) & (users_agg_df["Inactive"] == 0)]
    user_reached_1000 = users_agg_df[users_agg_df["Reached_1000_Flag"] == 1]

    return {
        "txn_q25": float(user_under_1000["Transaction_Count"].quantile(0.25)),
        "txn_q75": float(user_under_1000["Transaction_Count"].quantile(0.75)),
        "days_q25": float(user_under_1000["Active_Days"].quantile(0.25)),
        "days_q75": float(user_under_1000["Active_Days"].quantile(0.75)),
        "points_q25": float(user_under_1000["Total_Points"].quantile(0.25)),
        "points_q75": float(user_under_1000["Total_Points"].quantile(0.75)),
        "achievers_txn_q25": float(user_reached_1000["Transaction_Count"].quantile(0.25)),
    }


def assign_page5_segments(users_agg_df: pd.DataFrame, thresholds: dict) -> pd.DataFrame:
    out = users_agg_df.copy()

    txn_q75 = thresholds["txn_q75"]
    days_q75 = thresholds["days_q75"]
    achievers_txn_q25 = thresholds["achievers_txn_q25"]

    out["User_Segment"] = "Тогтмол_бус_оролцогч"

    out.loc[(out["Transaction_Count"] >= txn_q75) & (out["Active_Days"] > days_q75), "User_Segment"] = "Тогтвортой"
    out.loc[(out["Transaction_Count"] < txn_q75) & (out["Active_Days"] <= days_q75), "User_Segment"] = "Туршигч"
    out.loc[out["Transaction_Count"] >= achievers_txn_q25, "User_Segment"] = "Их_чармайлттай"
    out.loc[out["Reached_1000_Flag"] == 1, "User_Segment"] = "Амжилттай"
    out.loc[out["Inactive"] == 1, "User_Segment"] = "Идэвхгүй"

    return out


def get_page5_user_milestone_counts(users_agg_df: pd.DataFrame) -> pd.DataFrame:
    reached = users_agg_df[users_agg_df["Reached_1000_Flag"] == 1]

    user_milestone_counts = (
        reached.groupby("CUST_CODE", observed=True)
        .size()
        .reset_index(name="Times_Reached_1000")
    )

    reach_frequency = (
        user_milestone_counts.groupby("Times_Reached_1000", observed=True)["CUST_CODE"]
        .size()
        .reset_index(name="Number_of_Users")
        .sort_values("Times_Reached_1000")
    )

    reach_frequency["Total"] = reach_frequency["Times_Reached_1000"] * reach_frequency["Number_of_Users"]
    return reach_frequency


def get_page5_loyal_normalized_profile(df_year: pd.DataFrame, users_agg_df: pd.DataFrame) -> pd.DataFrame:
    """
    Memory optimized version:
    - filter early to achievers only
    - remove unnecessary merges
    """
    # Only achiever months (>=1000)
    achiever_months = users_agg_df.loc[users_agg_df["Reached_1000_Flag"] == 1, ["CUST_CODE", "MONTH_NUM"]]

    # Reduce df to only achiever months BEFORE grouping
    df_ach = df_year.merge(achiever_months, on=["CUST_CODE", "MONTH_NUM"], how="inner")

    # Monthly totals for normalization
    monthly_totals = (
        df_ach.groupby(["CUST_CODE", "MONTH_NUM"], observed=True)["TXN_AMOUNT"]
        .sum()
        .reset_index(name="True_Monthly_Total")
    )

    loyal_code_agg = (
        df_ach.groupby(["CUST_CODE", "MONTH_NUM", "LOYAL_CODE"], observed=True)["TXN_AMOUNT"]
        .sum()
        .reset_index()
    )

    final_df = loyal_code_agg.merge(monthly_totals, on=["CUST_CODE", "MONTH_NUM"], how="left")

    # Business cleaning
    final_df = final_df[final_df["LOYAL_CODE"].notna()]
    final_df = final_df[final_df["LOYAL_CODE"] != "10K_PURCH_INSUR"]

    final_df["Normalized_Points"] = (final_df["TXN_AMOUNT"] / final_df["True_Monthly_Total"]) * 1000

    # profile per user-month-loyal
    user_month_profile = (
        final_df.groupby(["CUST_CODE", "MONTH_NUM", "LOYAL_CODE"], observed=True)["Normalized_Points"]
        .sum()
        .reset_index()
    )

    return user_month_profile


def get_page5_bundle(df_base: pd.DataFrame, year: int, include_profile: bool = False) -> dict:
    """
    include_profile=False prevents the RAM-heavy Tab3 compute.
    """
    df_year = filter_df_by_year(df_base, year)

    users_agg_df = get_users_agg_by_monthnum(df_year)
    thresholds = get_page5_thresholds(users_agg_df)
    users_agg_df = assign_page5_segments(users_agg_df, thresholds)

    reach_frequency = get_page5_user_milestone_counts(users_agg_df)

    out = {
        "df_year": df_year,
        "users_agg_df": users_agg_df,
        "thresholds": thresholds,
        "reach_frequency": reach_frequency,
    }

    if include_profile:
        out["user_month_profile"] = get_page5_loyal_normalized_profile(df_year, users_agg_df)

    return out


# ------------------- PAGE MISC ----------------------

@st.cache_data(show_spinner=False)
def load_precomputed_page_misc_counts():
    return pd.read_parquet("data/pre_computed_data/page_misc/precomputed_monthly_bucket_counts.pqt", engine="pyarrow")


@st.cache_data(show_spinner=False)
def load_precomputed_page_misc_loyal_avg():
    return pd.read_parquet("data/pre_computed_data/page_misc/precomputed_loyal_avg_by_year.pqt", engine="pyarrow")


@st.cache_data(show_spinner=False)
def load_precomputed_page_misc_reach_frequency():
    return pd.read_parquet("data/pre_computed_data/page_misc/precomputed_reach_frequency_by_year.pqt", engine="pyarrow")


# --------------------- PAGE 5 ----------------------------

@st.cache_data(show_spinner=False)
def load_precomputed_page5_users_agg():
    return pd.read_parquet("data/pre_computed_data/page5/precomputed_users_agg_df.pqt", engine="pyarrow")

@st.cache_data(show_spinner=False)
def load_precomputed_page5_thresholds():
    return pd.read_parquet("data/pre_computed_data/page5/precomputed_thresholds_by_year.pqt", engine="pyarrow")

@st.cache_data(show_spinner=False)
def load_precomputed_page5_reach_frequency():
    return pd.read_parquet("data/pre_computed_data/page5/precomputed_reach_frequency_by_year.pqt", engine="pyarrow")

@st.cache_data(show_spinner=False)
def load_precomputed_page5_monthly_points():
    return pd.read_parquet("data/pre_computed_data/page5/precomputed_monthly_customer_points.pqt", engine="pyarrow")

@st.cache_data(show_spinner=False)
def load_precomputed_page5_user_month_profile():
    return pd.read_parquet("data/pre_computed_data/page5/precomputed_user_month_profile_achievers.pqt", engine="pyarrow")
