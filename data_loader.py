import streamlit as st
import pandas as pd

@st.cache_data(show_spinner=True)
def load_data():
    df = pd.read_parquet("ardiin_erh_code_grouped_2024_2025.pqt", engine="pyarrow")

    # ensure datetime (critical)
    df["TXN_DATE"] = pd.to_datetime(df["TXN_DATE"], errors="coerce")
    df = df[df["TXN_DATE"].notna()].copy()

    # core time cols
    df["year_month"] = df["TXN_DATE"].dt.to_period("M").astype(str)
    df["year"] = df["TXN_DATE"].dt.year
    df["CUST_CODE"] = df["CUST_CODE"].astype("category")
    df["MONTH_NUM"] = df["MONTH_NUM"].astype("int16")
    df["TXN_AMOUNT"] = pd.to_numeric(df["TXN_AMOUNT"], errors="coerce")


    return df

@st.cache_data(show_spinner=False)
def get_lookup():

    lookup_df = pd.read_csv("loyalty_lookup_2.csv")
    loyal_code_to_desc = dict(
        zip(lookup_df["LOYAL_CODE"], lookup_df["TXN_DESC"].str.capitalize())
    )
    return loyal_code_to_desc

@st.cache_data(show_spinner=True)
def get_stat_monthly(df):

    user_level_stat_monthly = (
        df.groupby(['CUST_CODE', pd.Grouper(key='TXN_DATE', freq='ME')],observed=True)
        .agg(user_total_point=('TXN_AMOUNT', 'sum'))
        .reset_index()
    )

    user_level_stat_monthly["user_reached_1000"] = (
        user_level_stat_monthly["user_total_point"] >= 1000
    ).astype(int)

    monthly_reward_stat = (
        df.groupby(pd.Grouper(key='TXN_DATE', freq='ME'),observed=True)
        .agg(
            total_points=('TXN_AMOUNT', 'sum'),
            total_users=('CUST_CODE', 'nunique')
        )
    )

    passed_1000 = (
        user_level_stat_monthly
        .groupby(pd.Grouper(key='TXN_DATE', freq='ME'),observed=True)['user_reached_1000']
        .sum()
    )

    monthly_reward_stat['num_user_passed_1000'] = (
        passed_1000.reindex(monthly_reward_stat.index, fill_value=0)
    )
    monthly_reward_stat['num_user_fail_1000'] = monthly_reward_stat.total_users - monthly_reward_stat.num_user_passed_1000
    monthly_reward_stat['percentage'] = (monthly_reward_stat.num_user_passed_1000 / monthly_reward_stat.total_users * 100).round(2)

    first_month = (
        user_level_stat_monthly
        .groupby('CUST_CODE',observed=True)['TXN_DATE']
        .transform('min')
    )

    user_level_stat_monthly["is_first_month"] = (
        user_level_stat_monthly["TXN_DATE"] == first_month
    ).astype(int)

    new_users = (
        user_level_stat_monthly
        .groupby('TXN_DATE',observed=True)['is_first_month']
        .sum()
    )

    monthly_reward_stat['total_new_users'] = (
        new_users.reindex(monthly_reward_stat.index, fill_value=0)
    )
    monthly_reward_stat = monthly_reward_stat.reset_index()
    monthly_reward_stat["year_month"] = monthly_reward_stat["TXN_DATE"].dt.to_period("M").astype(str)

    point_bins = [0,50,100,200,300,400,500,600,700,800,900,1000,float('inf')]
    labels = [
        '0-49','50-99','100-199','200-299','300-399',
        '400-499','500-599','600-699','700-799',
        '800-899','900-999','1000+'
    ]

    user_level_stat_monthly["point_bucket"] = pd.cut(
        user_level_stat_monthly['user_total_point'],
        bins=point_bins,
        labels=labels,
        right=False,
        include_lowest=True
    )
    user_level_stat_monthly["year_month"] = user_level_stat_monthly["TXN_DATE"].dt.to_period("M").astype(str)
    user_level_stat_monthly['month_num'] = user_level_stat_monthly.TXN_DATE.dt.month


    return user_level_stat_monthly, monthly_reward_stat

@st.cache_data(show_spinner=False)
def load_segment_counts_cutoff_fast(user_level_stat_monthly: pd.DataFrame, cutoffs: list[int]) -> pd.DataFrame:
    out = []
    user_level_stat_monthly_under_1000 = user_level_stat_monthly[user_level_stat_monthly['user_total_point'] < 1000]

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



# ------------------- PAGE 1 DATA ---------------------------
@st.cache_data(show_spinner=False)
def get_page1_bundle():
    """
    Precompute and cache everything Page 1 needs for the full dataset
    (2024-01 to 2025-12, and future years if present).
    """
    df = load_data()
    user_level_stat_monthly, monthly_reward_stat = get_stat_monthly(df)

    return {
        "df": df,
        "user_level_stat_monthly": user_level_stat_monthly,
        "monthly_reward_stat": monthly_reward_stat,
    }



# ------------------- PAGE 2 DATA ----------------------------

@st.cache_data(show_spinner=False)
def get_grouped_reward(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.groupby(["CODE_GROUP", "year_month"], observed=True)["TXN_AMOUNT"]
        .sum()
        .reset_index(name="TOTAL_AMOUNT")
        .sort_values("year_month")
    )
    return out

@st.cache_data(show_spinner=False)
def build_transaction_summary_no_pad(df: pd.DataFrame, lookup: dict) -> pd.DataFrame:
    ts = (
        df.groupby(["LOYAL_CODE", "year_month", "CODE_GROUP"], observed=True)
        .agg(
            Transaction_Freq=("JRNO", "size"),
            Total_Users=("CUST_CODE", "nunique"),
            Total_Amount=("TXN_AMOUNT", "sum"),
        )
        .reset_index()
        .rename(columns={"CODE_GROUP": "GROUP"})
    )

    ts["LOYAL_CODE"] = ts["LOYAL_CODE"].astype(str)
    ts["DESC"] = ts["LOYAL_CODE"].map(lookup)

    # year already exists in df, but summary doesn't contain TXN_DATE anymore
    ts["year"] = ts["year_month"].astype(str).str[:4].astype(int)

    return ts

@st.cache_data(show_spinner=False)
def build_transaction_summary_with_pad(df: pd.DataFrame, lookup: dict) -> pd.DataFrame:
    EPS = 1e-6

    ts = (
        df.groupby(["LOYAL_CODE", "year_month", "CODE_GROUP"], observed=True)
        .agg(
            Transaction_Freq=("JRNO", "size"),
            Total_Users=("CUST_CODE", "nunique"),
            Total_Amount=("TXN_AMOUNT", "sum"),
        )
        .reset_index()
        .rename(columns={"CODE_GROUP": "GROUP"})
    )

    ts["LOYAL_CODE"] = ts["LOYAL_CODE"].astype(str)
    ts["DESC"] = ts["LOYAL_CODE"].map(lookup)

    # padding (month x group)
    all_months = ts["year_month"].unique()
    all_groups = ts["GROUP"].unique()

    pad = (
        pd.MultiIndex.from_product([all_months, all_groups], names=["year_month", "GROUP"])
        .to_frame(index=False)
    )

    out = (
        pad.merge(ts, on=["year_month", "GROUP"], how="left")
        .fillna({
            "Transaction_Freq": EPS,
            "Total_Users": EPS,
            "Total_Amount": EPS,
            "LOYAL_CODE": "__PAD__",
            "DESC": "—",
        })
        .sort_values("year_month")
    )

    return out

@st.cache_data(show_spinner=False)
def get_page2_data(df: pd.DataFrame, lookup: dict) -> dict:
    """
    One call: returns everything page2 needs.
    Heavy objects are cached.
    """
    grouped_reward = get_grouped_reward(df)
    ts_no_pad = build_transaction_summary_no_pad(df, lookup)
    ts_pad = build_transaction_summary_with_pad(df, lookup)

    return {
        "grouped_reward": grouped_reward,
        "transaction_summary": ts_no_pad,
        "transaction_summary_with_pad": ts_pad,
    }

@st.cache_data(show_spinner=False)
def get_most_growing_loyal_code(df, ):
    df = df.copy()

    # 1. Clean
    df = df[df["LOYAL_CODE"].notna() & (df["LOYAL_CODE"] != "None")]

    # 2. Enforce minimum activity window
    df = df.groupby("LOYAL_CODE",observed=True).filter(
        lambda x: x["MONTH_NUM"].nunique() > 6
    )

    # 3. Monthly aggregation
    monthly = (
        df.groupby(["LOYAL_CODE", "MONTH_NUM"], as_index=False,observed=True)["TXN_AMOUNT"]
        .sum()
        .sort_values(["LOYAL_CODE", "MONTH_NUM"])
    )

    # 4. Growth stats
    stats = monthly.groupby("LOYAL_CODE",observed=True)["TXN_AMOUNT"].agg(
        first="first",
        last="last"
    )

    # 5. Safe growth calculation
    stats = stats[stats["first"] > 0]
    stats["PCT_INCREASE"] = (
        (stats["last"] - stats["first"]) / stats["first"] * 100
    )

    # 6. Business filters
    movers_df = (
        stats[(stats["PCT_INCREASE"] > 20) & (stats["last"] > 100_000)]
        .sort_values("PCT_INCREASE", ascending=False)
        .head(4)
        .reset_index()
    )

    return movers_df["LOYAL_CODE"], movers_df


#------------------ PAGE 4 ---------------------

@st.cache_data(show_spinner=False)
def add_year_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["year"] = df["year_month"].astype(str).str[:4].astype(int)
    return df


@st.cache_data(show_spinner=False)
def filter_df_by_year(df: pd.DataFrame, year: int) -> pd.DataFrame:
    df = df.copy()
    return df[df["year"] == year].copy()


@st.cache_data(show_spinner=False)
def get_user_agg_monthly(df_year: pd.DataFrame) -> pd.DataFrame:
    """
    Heavy aggregation: one row per user per month.
    """
    users_agg_df = (
        df_year.groupby(["CUST_CODE", "year_month"],observed=True)
        .agg(
            Total_Points=("TXN_AMOUNT", "sum"),
            Transaction_Count=("JRNO", "size"),
            Unique_Loyal_Codes=("LOYAL_CODE", "nunique"),
            Active_Days=("TXN_DATE", "nunique"),
        )
        .reset_index()
    )

    users_agg_df["Reached_1000_Flag"] = (users_agg_df["Total_Points"] >= 1000).astype(int)
    users_agg_df["Inactive"] = (users_agg_df["Transaction_Count"] <= 1).astype(int)

    return users_agg_df


@st.cache_data(show_spinner=False)
def get_thresholds(users_agg_df: pd.DataFrame) -> dict:
    """
    Compute all percentiles ONCE for the selected year.
    Returns a dict of thresholds.
    """
    reached = users_agg_df[users_agg_df["Reached_1000_Flag"] == 1]
    under = users_agg_df[(users_agg_df["Reached_1000_Flag"] == 0) & (users_agg_df["Inactive"] == 0)]

    thresholds = {
        "txn_q25": under["Transaction_Count"].quantile(0.25),
        "txn_q75": under["Transaction_Count"].quantile(0.75),
        "days_q25": under["Active_Days"].quantile(0.25),
        "days_q75": under["Active_Days"].quantile(0.75),
        "points_q25": under["Total_Points"].quantile(0.25),
        "points_q75": under["Total_Points"].quantile(0.75),
        "achievers_txn_q25": reached["Transaction_Count"].quantile(0.25),
        "achievers_points_q25": reached["Total_Points"].quantile(0.25),
    }
    return thresholds


@st.cache_data(show_spinner=False)
def assign_segments(users_agg_df: pd.DataFrame, thresholds: dict) -> pd.DataFrame:
    """
    Vectorized segmentation (MUCH faster than .apply).
    """
    out = users_agg_df.copy()

    txn_q75 = thresholds["txn_q75"]
    days_q75 = thresholds["days_q75"]
    achievers_txn_q25 = thresholds["achievers_txn_q25"]

    out["User_Segment"] = "Irregular_Participant"

    # Order matters: start from most specific / final rules
    out.loc[(out["Transaction_Count"] >= txn_q75) & (out["Active_Days"] > days_q75), "User_Segment"] = "Consistent"
    out.loc[(out["Transaction_Count"] < txn_q75) & (out["Active_Days"] <= days_q75), "User_Segment"] = "Explorer"
    out.loc[out["Transaction_Count"] >= achievers_txn_q25, "User_Segment"] = "High_Effort"
    out.loc[out["Reached_1000_Flag"] == 1, "User_Segment"] = "Achiever"
    out.loc[out["Inactive"] == 1, "User_Segment"] = "Inactive"

    return out


@st.cache_data(show_spinner=False)
def build_loyal_segment_summary(
    df_year: pd.DataFrame,
    users_agg_df_segmented: pd.DataFrame,
    loyal_code_to_desc: dict
) -> pd.DataFrame:
    """
    Heavy merge + groupby used in Tab4.
    Returns segment_loyal_summary with DESC.
    """
    segment_map = users_agg_df_segmented[["CUST_CODE", "year_month", "User_Segment"]].copy()

    loyal_code_agg = (
        df_year.groupby(["CUST_CODE", "LOYAL_CODE", "year_month"],observed=True)["TXN_AMOUNT"]
        .sum()
        .reset_index()
    )

    loyal_with_segments = loyal_code_agg.merge(
        segment_map,
        on=["CUST_CODE", "year_month"],
        how="inner",
    )

    segment_loyal_summary = (
        loyal_with_segments.groupby(["User_Segment", "LOYAL_CODE"],observed=True)["TXN_AMOUNT"]
        .sum()
        .reset_index()
    )

    segment_loyal_summary["DESC"] = segment_loyal_summary["LOYAL_CODE"].map(loyal_code_to_desc)
    segment_loyal_summary = segment_loyal_summary.sort_values(["User_Segment", "TXN_AMOUNT"], ascending=[True, False])

    return segment_loyal_summary


@st.cache_data(show_spinner=False)
def build_page4_data(df: pd.DataFrame, loyal_code_to_desc: dict, selected_year: int) -> dict:
    """
    One call returns everything page4 needs for the selected year.
    """
    df_year = df[df["year"] == selected_year].copy()

    users_agg_df = get_user_agg_monthly(df_year)
    thresholds = get_thresholds(users_agg_df)
    users_agg_df = assign_segments(users_agg_df, thresholds)

    segment_loyal_summary = build_loyal_segment_summary(df_year, users_agg_df, loyal_code_to_desc)

    user_segment_monthly_df = (
        users_agg_df.groupby(["year_month", "User_Segment"], observed=True)
        .size()
        .reset_index(name="count")
    )

    return {
        "df_year": df_year,
        "users_agg_df": users_agg_df,
        "thresholds": thresholds,
        "segment_loyal_summary": segment_loyal_summary,
        "user_segment_monthly_df": user_segment_monthly_df,
    }



# -------------------- PAGE 5 ----------------------

@st.cache_data(show_spinner=False)
def get_monthly_customer_points(df: pd.DataFrame) -> pd.DataFrame:
    """
    One row per customer per month: Total monthly points.
    Used in tab5 (distribution / bins).
    """
    out = (
        df.groupby(["MONTH_NUM", "MONTH_NAME", "CUST_CODE"], observed=True)["TXN_AMOUNT"]
        .sum()
        .reset_index()
        .rename(columns={"TXN_AMOUNT": "Total_Points"})
    )
    return out


@st.cache_data(show_spinner=False)
def get_users_agg_by_monthnum(df: pd.DataFrame) -> pd.DataFrame:
    """
    One row per customer per month_num (aggregated).
    Used throughout Page 5.
    """
    users_agg_df = (
        df.groupby(["CUST_CODE", "MONTH_NUM"], observed=True)
        .agg(
            Total_Points=("TXN_AMOUNT", "sum"),
            Transaction_Count=("JRNO", "count"),
            Unique_Loyal_Codes=("LOYAL_CODE", "nunique"),
            Active_Days=("TXN_DATE", "nunique"),
        )
        .reset_index()
    )

    users_agg_df["Reached_1000_Flag"] = (users_agg_df["Total_Points"] >= 1000).astype(int)
    users_agg_df["Inactive"] = (users_agg_df["Transaction_Count"] <= 1).astype(int)

    return users_agg_df


@st.cache_data(show_spinner=False)
def get_page5_thresholds(users_agg_df: pd.DataFrame) -> dict:
    """
    Percentile thresholds used for segmentation (Page 5).
    """
    user_under_1000 = users_agg_df[(users_agg_df["Reached_1000_Flag"] == 0) & (users_agg_df["Inactive"] == 0)]
    user_reached_1000 = users_agg_df[users_agg_df["Reached_1000_Flag"] == 1]

    return {
        "txn_q25": user_under_1000["Transaction_Count"].quantile(0.25),
        "txn_q75": user_under_1000["Transaction_Count"].quantile(0.75),
        "days_q25": user_under_1000["Active_Days"].quantile(0.25),
        "days_q75": user_under_1000["Active_Days"].quantile(0.75),
        "points_q25": user_under_1000["Total_Points"].quantile(0.25),
        "points_q75": user_under_1000["Total_Points"].quantile(0.75),
        "achievers_txn_q25": user_reached_1000["Transaction_Count"].quantile(0.25),
    }


@st.cache_data(show_spinner=False)
def assign_page5_segments(users_agg_df: pd.DataFrame, thresholds: dict) -> pd.DataFrame:
    """
    Vectorized segmentation (fast).
    Mongolian labels to match your page.
    """
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


@st.cache_data(show_spinner=False)
def get_page5_user_milestone_counts(users_agg_df: pd.DataFrame) -> pd.DataFrame:
    """
    For tab2: how many times each user reached 1000.
    """
    reached = users_agg_df[(users_agg_df["Reached_1000_Flag"] == 1)]

    user_milestone_counts = (
        reached.groupby("CUST_CODE", observed=True)
        .size()
        .reset_index(name="Times_Reached_1000")
        .sort_values("Times_Reached_1000", ascending=False)
    )

    reach_frequency = (
        user_milestone_counts.groupby("Times_Reached_1000", observed=True)["CUST_CODE"]
        .size()
        .reset_index(name="Number_of_Users")
    )
    reach_frequency["Total"] = reach_frequency["Times_Reached_1000"] * reach_frequency["Number_of_Users"]

    return reach_frequency


@st.cache_data(show_spinner=False)
def get_page5_loyal_normalized_profile(df: pd.DataFrame, users_agg_df: pd.DataFrame) -> pd.DataFrame:
    """
    For tab3: build normalized points per loyal code among months where total >= 1000.
    """
    monthly_totals = (
        df.groupby(["CUST_CODE", "MONTH_NUM"], observed=True)["TXN_AMOUNT"]
        .sum()
        .reset_index(name="True_Monthly_Total")
    )

    loyal_code_agg = (
        df.groupby(["CUST_CODE", "LOYAL_CODE", "MONTH_NUM"], observed=True)["TXN_AMOUNT"]
        .sum()
        .reset_index()
    )

    segment_map = users_agg_df[["CUST_CODE", "MONTH_NUM", "User_Segment"]].copy()

    total_loyal_df = (
        loyal_code_agg
        .merge(segment_map, on=["CUST_CODE", "MONTH_NUM"], how="inner")
        .merge(monthly_totals, on=["CUST_CODE", "MONTH_NUM"], how="left")
    )

    final_df = total_loyal_df[total_loyal_df["True_Monthly_Total"] >= 1000].copy()

    # Business cleaning
    final_df = final_df[final_df["LOYAL_CODE"].notna()]
    #final_df = final_df[final_df["LOYAL_CODE"] != "None"]
    final_df = final_df[final_df["LOYAL_CODE"] != "10K_PURCH_INSUR"]

    final_df["Normalized_Points"] = (final_df["TXN_AMOUNT"] / final_df["True_Monthly_Total"]) * 1000

    user_month_profile = (
        final_df.groupby(["CUST_CODE", "MONTH_NUM", "LOYAL_CODE"], observed=True)["Normalized_Points"]
        .sum()
        .reset_index()
    )

    return user_month_profile

@st.cache_data(show_spinner=False)
def get_page5_bundle(df: pd.DataFrame, year: int) -> dict:
    df_year = df[df["year"] == year].copy()

    monthly_customer_points = get_monthly_customer_points(df_year)

    users_agg_df = get_users_agg_by_monthnum(df_year)
    thresholds = get_page5_thresholds(users_agg_df)
    users_agg_df = assign_page5_segments(users_agg_df, thresholds)

    reach_frequency = get_page5_user_milestone_counts(users_agg_df)

    # ✅ Tab3 heavy profile (only for achievers)
    user_month_profile = get_page5_loyal_normalized_profile(df_year, users_agg_df)

    return {
        "df_year": df_year,
        "monthly_customer_points": monthly_customer_points,
        "users_agg_df": users_agg_df,
        "thresholds": thresholds,
        "reach_frequency": reach_frequency,
        "user_month_profile": user_month_profile,
    }


# ----------- Warmup -----------
@st.cache_data(show_spinner=False)
def warm_year_cache(df: pd.DataFrame, loyal_code_to_desc: dict, year: int):
    df_year = df[df["year"] == year].copy()

    get_stat_monthly(df)

    # Page 4 heavy
    build_page4_data(df, loyal_code_to_desc, year)

    # Page 5 heavy (only what you need often)
    users_agg = get_users_agg_by_monthnum(df_year)
    thresholds = get_page5_thresholds(users_agg)
    assign_page5_segments(users_agg, thresholds)
    get_page5_user_milestone_counts(users_agg)

    return True