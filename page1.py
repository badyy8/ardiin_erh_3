import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data_loader import load_segment_counts_cutoff_fast, get_page1_bundle

st.set_page_config(page_title="ХЭРЭГЛЭГЧДИЙН ОНООНЫ ТАРХАЦ", layout="wide")
st.title("ХЭРЭГЛЭГЧДИЙН ОНООНЫ ТАРХАЦ")

color_2025 = "#3498DB"

# ✅ Do NOT load data on import instantly
# Instead: let user trigger it OR lazy-load with spinner
with st.sidebar:
    st.subheader("⚙️ Page 1 Data")
    load_now = st.button("📦 Load Page 1 Data", type="primary")

if "page1_bundle" not in st.session_state:
    st.session_state.page1_bundle = None

if load_now and st.session_state.page1_bundle is None:
    with st.spinner("Loading data & precomputing stats (first run can take time)..."):
        st.session_state.page1_bundle = get_page1_bundle()

bundle = st.session_state.page1_bundle

if bundle is None:
    st.info("👉 Click **'Load Page 1 Data'** in the sidebar to load and compute the dataset.")
    st.stop()

# ✅ Now safe to use
df = bundle["df"]
user_level_stat_monthly = bundle["user_level_stat_monthly"]
monthly_reward_stat = bundle["monthly_reward_stat"]

tab1, tab2, tab3 = st.tabs(
    [
        "САР БҮРИЙН ОНООНЫ ТАРХАЛТ",
        "ХЭРЭГЛЭГЧДИЙН ОНООНЫ БҮЛЭГ",
        "1000 ОНООНЫ БОСГО ДАВСАН ХЭРЭГЛЭГЧИД",
    ]
)

# ---------------- TAB 3 ----------------
with tab3:
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=monthly_reward_stat["year_month"],
            y=monthly_reward_stat["num_user_fail_1000"],
            name="1000 хүрээгүй",
            marker_color="lightgrey",
            visible="legendonly",
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Bar(
            x=monthly_reward_stat["year_month"],
            y=monthly_reward_stat["num_user_passed_1000"],
            name="1000 хүрсэн",
            marker_color=color_2025,
            hovertemplate="<b>1000 давсан:</b> %{y:,.0f}<extra></extra>",
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=monthly_reward_stat["year_month"],
            y=monthly_reward_stat["percentage"],
            name="Амжилтын хувь (%)",
            line=dict(color="#F75A5A", width=3),
            mode="lines+markers",
            hovertemplate="<b>амжилтын хувь:</b> %{y}<extra></extra>",
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title_text="Сар бүрийн хэрэглэгчдийн онооны гүйцэтгэл (1000 онооны босго)",
        barmode="stack",
        height=450,
        xaxis_title="Сар",
        hovermode="x unified",
        template="plotly_white",
        title={"xanchor": "center", "x": 0.5},
        legend=dict(orientation="h", yanchor="top", xanchor="right", y=1.1, x=0.94),
    )

    fig.update_xaxes(type="category")

    fig.update_yaxes(title_text="Хэрэглэгчийн тоо", secondary_y=False)
    max_pct = monthly_reward_stat["percentage"].max()
    fig.update_yaxes(secondary_y=True, range=[0, max_pct * 1.2])

    # ✅ Replace deprecated
    st.plotly_chart(fig, width="stretch")

    with st.expander(expanded=True, label="Тайлбар:"):
        st.subheader("Ерөнхий тойм")
        st.markdown(
            f"""
            - Сард дунджаар **{monthly_reward_stat['num_user_passed_1000'].mean():,.0f}** хэрэглэгч 1000 онооны босгыг давсан нь,
            сарын нийт оролцогчдын **{monthly_reward_stat['percentage'].mean():.2f}%**-ийг эзэлж байна.
            """
        )

    with st.expander(label="Хүснэгт харах:", expanded=False):
        st.dataframe(monthly_reward_stat, hide_index=True, width="stretch")


# ---------------- TAB 2 ----------------
with tab2:
    cutoffs = [400, 500, 600, 700, 800, 900]

    segment_counts_all = load_segment_counts_cutoff_fast(user_level_stat_monthly, cutoffs)

    fig = px.line(
        segment_counts_all,
        x="year_month",
        y="Counts",
        color="cutoff",
        markers=True,
        template="plotly_white",
    )

    fig.update_xaxes(type="category")
    fig.update_yaxes(range=[0, segment_counts_all["Counts"].max() * 1.05])

    st.plotly_chart(fig, width="stretch")

    with st.expander("Тайлбар", expanded=True):
        st.subheader("2025 ОНЫ ХЭРЭГЛЭГЧДИЙН ОНООНЫ CUT-OFF СЕГМЕНТИЙН ШИНЖИЛГЭЭ")
        st.caption("Онооны босго (cumulative): 400+ | 500+ | 600+ | 700+ | 800+ | 900+")
        st.divider()
        st.markdown(
            """
            - Бүх босго сегментүүд **жил бүрийн 4-р сар болон 12-р сард өсөж**,
            **7–8-р сард хамгийн доод түвшинд** хүрж байна  
            - **800+ ба 900+ сегментүүд** нь нийт хэмжээгээр цөөн боловч
            **харьцангуй тогтвортой хэлбэлзэлтэй**
            """
        )

# ---------------- TAB 1 ----------------
with tab1:
    df_2024 = monthly_reward_stat[monthly_reward_stat["year_month"].str.startswith("2024")]
    df_2025 = monthly_reward_stat[monthly_reward_stat["year_month"].str.startswith("2025")]

    color_2024 = "#5D6D7E"
    color_2025 = "#3498DB"

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=df_2024["year_month"],
            y=df_2024["total_points"],
            name="2024 Нийт Оноо",
            marker_color=color_2024,
            text=df_2024["total_points"],
            texttemplate="%{y:,.0f}",
            textposition="outside",
            hovertemplate="<b>Нийт оноо:</b> %{y:,.0f}<extra></extra>",
            legendgroup="2024",
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Bar(
            x=df_2025["year_month"],
            y=df_2025["total_points"],
            name="2025 Нийт Оноо",
            marker_color=color_2025,
            text=df_2025["total_points"],
            texttemplate="%{y:,.0f}",
            textposition="outside",
            hovertemplate="<b>Нийт оноо:</b> %{y:,.0f}<extra></extra>",
            legendgroup="2025",
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=monthly_reward_stat["year_month"],
            y=monthly_reward_stat["total_users"],
            name="Хэрэглэгчдийн тоо",
            mode="lines+markers",
            line=dict(width=3),
            hovertemplate="<b>Оролцогчид (unique):</b> %{y}<extra></extra>",
        ),
        secondary_y=True,
    )

    fig.update_layout(
        height=500,
        title={"text": "RDX Цуглуулалтын Тренд", "xanchor": "center", "x": 0.5},
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="top", xanchor="right", y=0.99, x=0.99),
    )

    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Нийт Оноо", secondary_y=False)
    fig.update_yaxes(title_text="Нийт Оролцогчид", secondary_y=True, rangemode="tozero")

    st.plotly_chart(fig, width="stretch")

    with st.expander(expanded=True, label="Тайлбар:"):
        st.subheader("Ерөнхий тойм")
        st.markdown(
            f"""
            - **2024-2025** онуудад нийт **{df['CUST_CODE'].nunique():,}** хэрэглэгч урамшууллын хөтөлбөрт хамрагдсан байна.
            - 2024 онд: **{df_2024['total_new_users'].sum():,}** хэрэглэгч
            - 2025 онд: **56,267** хэрэглэгч. (29,995 хэрэглэгчид бүх жилд ороролцсон)
            - Сард дунджаар **{df.groupby('MONTH_NUM')['CUST_CODE'].nunique().mean():,.0f}** хэрэглэгч урамшуулалд оролцсон байна.
            """
        )

    with st.expander(expanded=False, label="Хүснэгт харах:"):
        st.dataframe(monthly_reward_stat, width="stretch", hide_index=True)
