import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from data.data_loader import (
    get_lookup,
    load_precomputed_page5_users_agg,
    load_precomputed_page5_thresholds,
    load_precomputed_page5_reach_frequency,
    load_precomputed_page5_monthly_points,
    load_precomputed_page5_user_month_profile,
)

st.set_page_config(layout="wide")

# -------------------------
# Load lookup + precomputed tables
# -------------------------
@st.cache_data(show_spinner=False)
def load_lookup():
    return get_lookup()

loyal_code_to_desc = load_lookup()

users_agg_all = load_precomputed_page5_users_agg()
thresholds_all = load_precomputed_page5_thresholds()
reach_freq_all = load_precomputed_page5_reach_frequency()
monthly_points_all = load_precomputed_page5_monthly_points()

# This file is big, but still MUCH safer than computing live.
# Keep cached by Streamlit.
user_month_profile_all = load_precomputed_page5_user_month_profile()

# -------------------------
# Year selector
# -------------------------
available_years = sorted(users_agg_all["year"].dropna().astype(int).unique())

selected_year = st.sidebar.selectbox(
    "Жил сонгох",
    available_years,
    index=len(available_years) - 1,
)

st.sidebar.caption(f"Одоогийн сонголт: {selected_year}")

# Filter to year
users_agg_df = users_agg_all[users_agg_all["year"] == selected_year].copy()
reach_frequency = reach_freq_all[reach_freq_all["year"] == selected_year].copy()
monthly_customer_points = monthly_points_all[monthly_points_all["year"] == selected_year].copy()
user_month_profile = user_month_profile_all[user_month_profile_all["year"] == selected_year].copy()

# Thresholds row (optional usage if you need)
threshold_row = thresholds_all[thresholds_all["year"] == selected_year]
thresholds = threshold_row.iloc[0].to_dict() if not threshold_row.empty else {}

# -------------------------
# Tabs
# -------------------------
tab3, tab4, tab5 = st.tabs([
    "1000 Хүрсэн Хэрэглэгчдийн Онооны Тархалт",
    "Зардал/Борлуулалт",
    "RDX Хөнгөлөлт",
])

# ============================================================
# TAB 3 (Precomputed profile)
# ============================================================
with tab3:
    st.subheader("Хэрэглэгч дунджаар хэрхэн 1000 оноонд хүрдэг вэ?")

    if user_month_profile.empty:
        st.warning("Энэ жилд 1000 оноонд хүрсэн хэрэглэгчийн профайл дата байхгүй байна.")
        st.stop()

    profile_wide = user_month_profile.pivot_table(
        index=["CUST_CODE", "MONTH_NUM"],
        columns="LOYAL_CODE",
        values="Normalized_Points",
        fill_value=0,
        observed=True,
    )

    avg_user_points = profile_wide.mean().reset_index()
    avg_user_points.columns = ["LOYAL_CODE", "Normalized_Points"]

    avg_user_points = avg_user_points.sort_values("Normalized_Points", ascending=False)

    # Normalize to "average user = 1000"
    s = avg_user_points["Normalized_Points"].sum()
    if s > 0:
        avg_user_points["Normalized_Points"] = avg_user_points["Normalized_Points"] / s * 1000

    avg_user_points["DESC"] = avg_user_points["LOYAL_CODE"].map(loyal_code_to_desc)

    # Thresholding into "Other"
    threshold = 50
    main = avg_user_points.copy()

    main.loc[main["DESC"].isna(), "DESC"] = "Бусад урамшуулал"
    main.loc[main["Normalized_Points"] < threshold, "DESC"] = "Бусад урамшуулал"

    avg_user_simple = (
        main.groupby("DESC", observed=True)["Normalized_Points"]
        .sum()
        .reset_index()
        .sort_values("Normalized_Points", ascending=False)
    )

    fig = go.Figure()

    left_name = "1к эрхийн гүйлгээний"
    right_name = "Бусад урамшуулал"

    left_df = avg_user_simple[avg_user_simple["DESC"] == left_name]
    right_df = avg_user_simple[avg_user_simple["DESC"] == right_name]
    middle_df = avg_user_simple[
        (avg_user_simple["DESC"] != left_name) &
        (avg_user_simple["DESC"] != right_name)
    ]

    # LEFT
    for _, row in left_df.iterrows():
        fig.add_bar(
            y=["Дундаж хэрэглэгч = 1000 Оноо"],
            x=[row["Normalized_Points"]],
            name=row["DESC"],
            orientation="h",
            hovertemplate="<b>%{x:.0f}</b> оноог %{fullData.name}<extra></extra>",
        )

    # MIDDLE
    for _, row in middle_df.iterrows():
        fig.add_bar(
            y=["Дундаж хэрэглэгч = 1000 Оноо"],
            x=[row["Normalized_Points"]],
            name=row["DESC"],
            orientation="h",
            hovertemplate="<b>%{x:.0f}</b> оноог %{fullData.name}<extra></extra>",
        )

    # RIGHT
    for _, row in right_df.iterrows():
        fig.add_bar(
            y=["Дундаж хэрэглэгч = 1000 Оноо"],
            x=[row["Normalized_Points"]],
            name=row["DESC"],
            orientation="h",
            hovertemplate="<b>%{x:.0f}</b> оноог %{fullData.name}-аас авсан<extra></extra>",
            marker_color="grey",
        )

    fig.update_layout(
        barmode="stack",
        title="Хэрэглэгч дунджаар хэрхэн 1000 оноонд хүрдэг вэ?",
        xaxis_title="Оноо",
        yaxis_title="",
        template="plotly_white",
        height=360,
        legend_title_text="Урамшууллын төрөл",
    )

    st.plotly_chart(fig, use_container_width=True)
    st.caption("Даатгал авсны урамшууллын оноог оролцуулаагүй болно.")

# ============================================================
# TAB 4
# ============================================================
with tab4:
    st.markdown("## 1,000 оноонд хүрэх Зардал / Борлуулалт")
    st.info("**Зардлыг хэрхэн тооцсон бэ?**")
    st.markdown("""
    - Оноо цуглуулах хамгийн боломжит арга бол **дансандаа орлого хийх** юм
        - Хэрэглэгчид **цэнэглэсэн 100,000 төгрөг тутамд 50 оноо** авдаг (**1 оноо = 2,000 төгрөг**)
    """)

    dominant_points = 400
    remaining_points = 600

    mnt_per_block = 100_000
    points_per_block = 50
    cost_per_point = mnt_per_block / points_per_block

    remaining_cost = remaining_points * cost_per_point

    col1, col2, col3 = st.columns(3)
    col1.metric("Үндсэн гүйлгээнээс авсан оноо", f"~{dominant_points} оноо")
    col2.metric("Данс цэнэглэлтээр авах оноо", f"{remaining_points} оноо")
    col3.metric("Шаардлагатай орлого хийх дүн", f"{remaining_cost:,.0f} төг")

    st.divider()

    st.subheader("Хэрэв гүйлгээний урамшууллын оноог 300-аар хязгаарлавал:")
    capped_points = 300
    new_remaining_points = 1000 - capped_points
    new_required_cost = new_remaining_points * cost_per_point
    incremental_cost = new_required_cost - remaining_cost

    col1, col2, col3 = st.columns(3)
    col1.metric("10K_TRANSACTION-аас авах оноо", f"{capped_points} оноо", delta="-100 оноо")
    col2.metric("Данс цэнэглэлтээр авах оноо", f"{new_remaining_points} оноо", delta="+100 оноо")
    col3.metric("Үлдэгдэл оноонд шаардлагатай орлого", f"{new_required_cost:,.0f} ТӨГ", delta=f"+{incremental_cost:,.0f} ТӨГ")

    st.markdown("""
    **Энэхүү өөрчлөлтийн нөлөө**
    - Хэрэглэгчид ижил хэмжээний урамшуулал авахын тулд **илүү их бодит мөнгө** төвлөрүүлэх шаардлагатай болно
    - Шаардлагатай орлого хийх дүн **1.2 сая -аас 1.4 сая төгрөг** болж нэмэгдэнэ
    - Ганцхан төрлийн гүйлгээний урамшууллаас хамааралтай байхыг бууруулна
    """)

# ============================================================
# TAB 5
# ============================================================
with tab5:
    st.markdown("## Хөнгөлөлттэй Ардын Эрх")

    df_table = pd.DataFrame({
        "RDX reached": ["500 RDX", "600 RDX", "700 RDX", "800 RDX", "900 RDX", "1000 RDX"],
        "Discount": ["50%", "60%", "70%", "80%", "90%", "100%"],
        "ARDX received": ["250 ARDX", "360 ARDX", "490 ARDX", "640 ARDX", "810 ARDX", "1000 ARDX"],
    })

    mcp = monthly_customer_points.copy()
    mcp["Total_Points"] = pd.to_numeric(mcp["Total_Points"], errors="coerce").fillna(0)

    bins = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, mcp["Total_Points"].max() + 1]
    labels = ['0-99', '100-199', '200-299', '300-399', '400-499', '500-599',
              '600-699', '700-799', '800-899', '900-999', '1000+']

    mcp["Segments"] = pd.cut(mcp["Total_Points"], bins=bins, labels=labels, right=False)

    segment_counts = (
        mcp.groupby("Segments", observed=True)
        .size()
        .reset_index(name="Counts")
    )

    total_users = segment_counts["Counts"].sum()

    withdrawal_map = {
        '0-99': 0, '100-199': 0, '200-299': 0, '300-399': 0, '400-499': 0,
        '500-599': 1, '600-699': 1, '700-799': 1, '800-899': 1, '900-999': 1, '1000+': 1,
    }

    segment_counts["Can_Withdraw_Discounted"] = (
        segment_counts["Segments"].astype(str).map(withdrawal_map).fillna(0).astype(int)
    )
    segment_counts["Can_Withdraw_Current"] = (segment_counts["Segments"] == "1000+").astype(int)

    current_success = segment_counts.loc[segment_counts["Can_Withdraw_Current"] == 1, "Counts"].sum()
    discounted_success = segment_counts.loc[segment_counts["Can_Withdraw_Discounted"] == 1, "Counts"].sum()

    current_rate = (current_success / total_users * 100) if total_users else 0
    discounted_rate = (discounted_success / total_users * 100) if total_users else 0
    lift = discounted_rate - current_rate

    col1, col2, col3 = st.columns(3, gap="large")
    with col1:
        with st.container(border=True):
            st.metric(
                "Одоогийн амжилттай хэрэглэгчдийн тоо",
                f"{current_success:,}",
                help="≥ 1000 RDX оноотой хэрэглэгчид (сар бүрийн давтагдсан тоо)",
            )
    with col2:
        with st.container(border=True):
            st.metric(
                "Хөнгөлөлтийн дараах амжилттай хэрэглэгчдийн тоо",
                f"{discounted_success:,}",
                delta=f"+{discounted_success - current_success:,} хэрэглэгч",
                help="≥ 500 RDX оноотой хэрэглэгчид",
            )
    with col3:
        with st.container(border=True):
            st.metric(
                "Амжилтын хувийн өсөлт",
                f"{discounted_rate:.1f}%",
                delta=f"+{lift:.1f} %",
            )

    success_df = pd.DataFrame({
        "Хувилбар": ["Одоогийн (1000 RDX)", "Хөнгөлөлттэй (≥500 RDX)"],
        "Амжилттай хэрэглэгчид": [current_success, discounted_success],
    })

    increase = discounted_success - current_success
    increase_pct = (increase / current_success * 100) if current_success else 0

    fig = px.bar(
        success_df,
        x="Хувилбар",
        y="Амжилттай хэрэглэгчид",
        text="Амжилттай хэрэглэгчид",
        template="plotly_white",
        color="Хувилбар",
    )

    fig.update_traces(
        textposition="inside",
        texttemplate="<b>%{text:,}</b>",
        marker_line_width=0,
    )

    fig.update_layout(
        height=520,
        title={
            "text": f"Амжилттай хэрэглэгчдийн өсөлт: +{increase_pct:.1f}%",
            "y": 0.95,
            "x": 0.05,
            "xanchor": "left",
            "yanchor": "top",
        },
        xaxis_title="",
        yaxis_title="Хэрэглэгчдийн тоо",
        showlegend=False,
        margin=dict(t=80, b=20, l=50, r=20),
    )

    with st.expander(expanded=False, label="Хөнгөлөлтийн шатлал"):
        st.subheader("Хөнгөлөлтийн шатлал")
        st.table(df_table)

    st.divider()

    col1, col2 = st.columns([0.5, 0.5], gap="large")

    with col1:
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(f"""
        ### Шинжилгээний дүгнэлт
        Нөхцөлийг хөнгөлснөөр нийт **{increase:,}** хэрэглэгч шинээр урамшуулал авах боломжтой болж байна.
        
        * **Хүртээмж:** 1,000 RDX-ээс бага оноотой хэрэглэгчид идэвхжих хөшүүрэг болно.
        * **Retention:** Зорилтдоо дөхсөн хэрэглэгчдийг "амжилттай" болгох нь системээс гарах магадлалыг бууруулна
        """)

        lift_source = segment_counts[
            (segment_counts["Can_Withdraw_Discounted"] == 1) &
            (segment_counts["Can_Withdraw_Current"] == 0)
        ][["Segments", "Counts"]].copy()

        st.write("---")
        st.caption("Шинээр нэмэгдэж буй сегментүүд")

        st.dataframe(lift_source, use_container_width=True, hide_index=True)
