import streamlit as st
from data.data_loader import load_data, get_lookup, load_precomputed_page4
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from plotly.subplots import make_subplots

users_all, thresholds_all, seg_monthly_all, loyal_summary_all = load_precomputed_page4()

available_years = sorted(users_all["year"].unique())

selected_year = st.sidebar.selectbox("Жил сонгох", available_years)

users_agg_df = users_all[users_all["year"] == selected_year].copy()
thresholds = thresholds_all[thresholds_all["year"] == selected_year].iloc[0].to_dict()
thresholds.pop("year", None)

user_segment_monthly_df = seg_monthly_all[seg_monthly_all["year"] == selected_year].copy()
segment_loyal_summary = loyal_summary_all[loyal_summary_all["year"] == selected_year].copy()


st.sidebar.caption(f"Одоогийн сонголт: {selected_year}")


tab1, tab2, tab3, tab4 = st.tabs(['Methodology',"Threshold Analysis (Users reached 1000)", "User Segmentation (Under 1000 Point)", 'User Segment Analysis'])

with tab1:

    st.title("Segmentation Methodology")
    st.markdown("""
        Хэрэглэгчдийг гүйлгээний тоо, урамшуулал ашигласан өдрөөр хэрхэн сегмэнтэд хуваасан аргыг тайлбарлав.
    """)

    st.divider()

    # --- 1. THE THRESHOLDS (METRICS) ---
    st.header("Statistical Thresholds")
    st.write("Q25 and Q75 квартилыг ашиглан 'High' 'Low' идэвхийн босгыг тодорхойлов.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Гүйлгээ")
        st.metric("Low (Q25)", f"{thresholds['txn_q25']:.0f} гүйлгээ")
        st.metric("High (Q75)", f"{thresholds['txn_q75']:.0f} гүйлгээ")
        st.metric("Амжилтийн босго", f"{thresholds['achievers_txn_q25']:.0f} гүйлгээ", help="Bottom 25% of successful users")

    with col2:
        st.subheader("Өдөр")
        st.metric("Low (Q25)", f"{thresholds['days_q25']:.0f} өдөр")
        st.metric("High (Q75)", f"{thresholds['days_q75']:.0f} өдөр")

    with col3:
        st.subheader("Нийт оноо")
        st.metric("Low (Q25)", f"{thresholds['points_q25']:.0f}")
        st.metric("High (Q75)", f"{thresholds['points_q75']:.0f}")

    st.header("Segment Definition Logic")

    
    logic_data = {
        "Сегмэнт": ["Inactive", "Achiever", "High Effort", "Explorer", "Consistent", "Irregular"],
        "Шалгуур": [
            "Transactions / Month = 1",
            "Points ≥ 1000",
            f"Transactions ≥ {thresholds['achievers_txn_q25']:.0f}",
            f"Transactions < {thresholds['txn_q75']:.0f}  AND  Days ≤ {thresholds['days_q75']:.0f}",
            f"Transactions ≥ {thresholds['txn_q75']:.0f}  AND  Days > {thresholds['days_q75']:.0f}",
            "Else (Fallback)"
        ],
        "Тайлбар": [
            "Сард зөвхөн 1 гүйлгээ хийсэн хэрэглэгчид.",
            "1000 онооны босго давсан хэрэглэгчид.",
            "1000 оноо давсан хэрэглэгчидтэй адил гүйлгээтэй ч босго даваагүй хэрэглэгчид.",
            "Цөөн өдөр бага гүйлгээтэй туршилт хийж буй хэрэглэгчид.",
            "Олон өдрийн давтамжтай урамшуулалын гүйлгээ хийдэг хэрэглэгчид.",
            "Сегмэнтэд багтаагүй хэрэглээтэй хэрэглэгчид (жишээ: олон өдөр, бага гүйлгээ)."
        ]
    }

    df_logic = pd.DataFrame(logic_data)
    st.caption("Доорх хүснэгт нь сегмэнт бүрийн шалгуур болон утгыг харуулна.")

    st.dataframe(
        df_logic,
        width='stretch',
        hide_index=True,
        column_config={
            "Сегмэнт": st.column_config.TextColumn(width="small"),
            "Шалгуур": st.column_config.TextColumn(width="medium"),
            "Тайлбар": st.column_config.TextColumn(width="large"),
        }
    )

with tab2:
    st.subheader("Сарын 1000 онооны босгыг давсан хэрэглэгчид")
    user_reached_1000_agg = users_agg_df[users_agg_df.Reached_1000_Flag == 1]
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Хэрэглэгч (≥1000 оноо)", f"{user_reached_1000_agg['CUST_CODE'].nunique():,}")
    c2.metric("Дундаж гүйлгээ", f"{user_reached_1000_agg['Transaction_Count'].median():.0f}")
    c3.metric("Дундаж идэвхтэй хоног", f"{user_reached_1000_agg['Active_Days'].median():.0f}")
    c4.metric("Дундаж урамшуулын төрлүүд", f"{user_reached_1000_agg['Unique_Loyal_Codes'].median():.0f}")

    st.divider()

    fig_box = make_subplots(
            rows=1,
            cols=3,
            subplot_titles=[
                "Гүйлгээний тоо",
                "Идэвхтэй хоног",
                "Урамшуулын төрлүүдийн тоо"
            ],
            horizontal_spacing=0.12
        )

    # 1) Transactions
    fig_box.add_trace(go.Box(
            y=user_reached_1000_agg["Transaction_Count"],
            name="Гүйлгээ",
            boxpoints=False,
            orientation="v",
        ),
        row=1, col=1
    )

    # 2) Active days
    fig_box.add_trace(
        go.Box(
            y=user_reached_1000_agg["Active_Days"],
            name="Идэвхтэй өдөр",
            boxpoints=False,
            orientation="v",
        ),
        row=1, col=2
    )

    # 3) Unique loyal codes
    fig_box.add_trace(
        go.Box(
            y=user_reached_1000_agg["Unique_Loyal_Codes"],
            name="Лояал код",
            boxpoints=False,
            orientation="v",
        ),
        row=1, col=3
    )


    fig_box.update_layout(
        template="plotly_white",
        height=420,
        showlegend=False,
        title={
            "text": "<b>Амжилттай хэрэглэгчдийн тархалт</b><br><span style='font-size:12px'>1,000 онооны босго давсан хэрэглэгчид</span>",
            "x": 0.5,
            "xanchor": "center",
            "y": 0.96, 
        },
        margin=dict(l=20, r=20, t=100, b=20) 
    )

    st.plotly_chart(fig_box, width='stretch')

    st.divider()

    # ----------------------------
    # 5) Minimum viable effort (Q1)
    # ----------------------------
    st.subheader("Боломжит хамгийн бага идэвх (Доод квартил = 25%)")

    q1_txn = user_reached_1000_agg["Transaction_Count"].quantile(0.25)
    q1_days = user_reached_1000_agg["Active_Days"].quantile(0.25)
    achievers_points_q25 = user_reached_1000_agg["Total_Points"].quantile(0.25)

    st.caption("Амжилттай хэрэглэгчдийн доод 25%-ийн түвшин")

    m1, m2, m3 = st.columns(3)

    with m1:
        with st.container(border=True):
            st.metric(
                "Q1 - Гүйлгээ",
                f"{q1_txn:.0f}",
                help=f"Доод идэвхтэй хэрэглэгчид дунджаар ~{q1_txn:.0f} гүйлгээ хийдэг"
            )

    with m2:
        with st.container(border=True):
            st.metric(
                "Q1 - Идэвхтэй хоног",
                f"{q1_days:.0f}",
                help=f"Тэд хамгийн багадаа ~{q1_days:.0f} өөр өдөр идэвхтэй байсан"
            )

    with m3:
        with st.container(border=True):
            st.metric(
                "Q1 - Оноо",
                f"{achievers_points_q25:.0f}"
            )



    st.info(
        f"**~{q1_txn:.0f}-оос бага** гүйлгээ хийсэн эсвэл **~{q1_days:.0f}-аас цөөн** өдөр идэвхтэй байсан хэрэглэгч "
        f"1,000 оноонд хүрэх магадлал харьцангуй бага байна."
    )

    st.divider()

    # ----------------------------
    # 6) Typical user (Median)
    # ----------------------------
    st.subheader("Дундаж амжилттай хэрэглэгчийн зан төлөв (50%)")

    med_txn = user_reached_1000_agg["Transaction_Count"].median()
    med_days = user_reached_1000_agg["Active_Days"].median()
    med_points = user_reached_1000_agg["Total_Points"].median() if "Total_Points" in user_reached_1000_agg.columns else 1000

    m1, m2, m3 = st.columns(3)
    with m1:
        with st.container(border=True):
            st.metric(
                "Гүйлгээ",
                f"{med_txn:.0f}",
                help=f"Доод идэвхтэй хэрэглэгчид дунджаар ~{med_txn:.0f} гүйлгээ хийдэг (median)"
            )

    with m2:
        with st.container(border=True):
            st.metric(
                "Идэвхтэй хоног",
                f"{med_days:.0f}",
                help=f"Тэд хамгийн багадаа ~{med_days:.0f} өөр өдөр идэвхтэй байсан (median)"
            )

    with m3:
        with st.container(border=True):
            st.metric(
                "Оноо",
                f"{med_points:.0f}"
            )

    st.divider()

    # ----------------------------
    # 7) High effort (75%)
    # ----------------------------
    st.subheader("Өндөр идэвхтэй хэрэглэгчид (75%)")

    txn_q75_achiever = user_reached_1000_agg["Transaction_Count"].quantile(0.75)
    day_q75_achiever = user_reached_1000_agg["Active_Days"].quantile(0.75)
    point_q75_achiever = user_reached_1000_agg["Total_Points"].quantile(0.75)

    m1, m2, m3 = st.columns(3)
    with m1:
        with st.container(border=True):
            st.metric(
                "Гүйлгээ",
                f"{txn_q75_achiever:.0f}",
                help=f"Дээд идэвхтэй хэрэглэгчид дунджаар ~{txn_q75_achiever:.0f} гүйлгээ хийдэг"
            )

    with m2:
        with st.container(border=True):
            st.metric(
                "Идэвхтэй хоног",
                f"{day_q75_achiever:.0f}",
                help=f"~{q1_days:.0f} өдөр идэвхтэй байсан"
            )

    with m3:
        with st.container(border=True):
            st.metric(
                "Оноо",
                f"{point_q75_achiever:.0f}"
            )


with tab3:

    color_map = {
        "Explorer": "#FFBB34",              
        "Irregular_Participant": "#00D1FF", 
        "Consistent": "#FF5A7E",            
        "High_Effort": "#4A4DFF"            
    }

 
    plot_df = users_agg_df[
        (users_agg_df['User_Segment'] != 'Achiever') & 
        (users_agg_df['User_Segment'] != 'Inactive') & 
        (users_agg_df['Transaction_Count'] < 400)
    ]

    fig = px.scatter(
        plot_df, 
        x="Active_Days", 
        y="Transaction_Count", 
        color="User_Segment",
        color_discrete_map=color_map,
        custom_data=['Total_Points'],
        hover_data=['Total_Points'],
        title="<b>User Segmentation Map</b><br><sup>Visualizing segments based on Active Days and Transaction thresholds</sup>",
        labels={"Active_Days": "Consistency (Active Days)", "Transaction_Count": "Intensity (Transactions)", 'Total_Points' : 'Total Points'},
        opacity=0.5,
        category_orders={"User_Segment": ["High_Effort", "Consistent", "Irregular_Participant", "Explorer"]},
    )


    line_style = dict(color="#666666", width=2, dash="dash")


    for val in [thresholds['days_q25'], thresholds['days_q75']]:
        fig.add_vline(x=val, line=line_style)

    for val in [thresholds['txn_q25'], thresholds['txn_q75'], thresholds['achievers_txn_q25']]:
        fig.add_hline(y=val, line=line_style)

    #fig.update_traces(marker=dict(size=8)) 

    fig.update_layout(
        template="plotly_white",
        width=1000,
        height=700,
        showlegend=True,
        legend_title="User Segments",
        # Grid styling
        xaxis=dict(showgrid=True, gridcolor="#E5E7EB", zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#E5E7EB", zeroline=False),
        # Font styling
        font=dict(family="Arial", size=14, color="#374151"),
    #    yaxis=dict(automargin=True),

    )
    st.plotly_chart(fig, width='stretch')

    st.caption('Inactive болон 1000 оноо давсан хэрэглэгчдээс бусад сегмэнтийн тархалтыг харуулав')


    #st.divider()
    # Count users per segment
    segment_counts = users_agg_df['User_Segment'].value_counts().reset_index()
    segment_counts.columns = ['Segment', 'User_Count']

    fig = px.treemap(
        segment_counts, 
        path=['Segment'], 
        values='User_Count',
        color='User_Count',
        color_continuous_scale='RdYlGn',
        title="Proportional Size of User Segments"
    )

    fig.update_traces(textinfo="label+value+percent root")
    st.plotly_chart(fig,width='stretch')
    #st.caption('Сегмэнтэлсэн хэрэглэгчдийн бүлгийн тархацийг харуулав')

    
with tab4:
    st.subheader(f"User Segment Analysis - {selected_year}")

    with st.expander("Monthly User Distribution by Segment", expanded=False):
        fig = px.line(
            user_segment_monthly_df,
            x="year_month",
            y="count",
            color="User_Segment",
            markers=True,
            title="<b>Monthly User Distribution by Segment</b><br><sup>Comparing total user volume across months</sup>",
            labels={"count": "Number of Users", "year_month": "Month"},
            template="plotly_white",
            category_orders={
                "User_Segment": ["Achiever", "High_Effort", "Consistent", "Irregular_Participant", "Explorer", "Inactive"]
            },
        )

        fig.update_xaxes(type="category", tickangle=-45)
        fig.update_layout(
            showlegend=True,
            height=520,
            margin=dict(t=90, b=60, l=40, r=40),
            font=dict(family="Arial", size=12),
        )

        st.plotly_chart(fig, width='stretch')

    # ---- Monthly total points by segment
    with st.expander("Monthly User Point Distribution by Segment", expanded=False):
        user_segment_points_df = (
            users_agg_df.groupby(["User_Segment", "year_month"],observed=True)["Total_Points"]
            .sum()
            .reset_index()
        )

        fig = px.line(
            user_segment_points_df,
            x="year_month",
            y="Total_Points",
            color="User_Segment",
            markers=True,
            title="<b>Monthly User Point Distribution by Segment</b><br><sup>Comparing total points across months</sup>",
            labels={"Total_Points": "Total Points", "year_month": "Month"},
            template="plotly_white",
            category_orders={
                "User_Segment": ["Achiever", "High_Effort", "Consistent", "Irregular_Participant", "Explorer", "Inactive"]
            },
        )

        fig.update_xaxes(type="category", tickangle=-45)
        fig.update_layout(
            showlegend=True,
            height=520,
            margin=dict(t=90, b=60, l=40, r=40),
            font=dict(family="Arial", size=12),
        )

        st.plotly_chart(fig,width='stretch')

    # ---- Monthly average points per user
    with st.expander("Monthly Average User Point Distribution by Segment", expanded=False):
        avg_points_df = (
            users_agg_df.groupby(["User_Segment", "year_month"],observed = True)
            .agg(Total_Points=("Total_Points", "sum"), Users=("CUST_CODE", "nunique"))
            .reset_index()
        )

        avg_points_df["avg_point_per_user"] = (avg_points_df["Total_Points"] / avg_points_df["Users"]).round(2)

        fig = px.line(
            avg_points_df,
            x="year_month",
            y="avg_point_per_user",
            color="User_Segment",
            markers=True,
            title="<b>Monthly Average User Point Distribution by Segment</b><br><sup>Comparing average points per user across months</sup>",
            labels={"avg_point_per_user": "Avg Points / User", "year_month": "Month"},
            template="plotly_white",
            category_orders={
                "User_Segment": ["Achiever", "High_Effort", "Consistent", "Irregular_Participant", "Explorer", "Inactive"]
            },
        )

        fig.update_xaxes(type="category", tickangle=-45)
        fig.update_layout(
            showlegend=True,
            height=520,
            margin=dict(t=90, b=60, l=40, r=40),
            font=dict(family="Arial", size=12),
        )

        st.plotly_chart(fig,width='stretch')

    # ============================================================
    # Loyal code analysis (year-filtered + correct merge keys)
    # ============================================================


    ordered_segments = ["Achiever", "High_Effort", "Consistent", "Irregular_Participant", "Explorer", "Inactive"]
    segment_loyal_summary["User_Segment"] = pd.Categorical(
        segment_loyal_summary["User_Segment"],
        categories=ordered_segments,
        ordered=True,
    )

    segment_loyal_summary = segment_loyal_summary.sort_values(["User_Segment", "TXN_AMOUNT"], ascending=[True, False])

    # ---- Top 3 loyal codes by spend volume
    with st.expander("Top 3 Loyal Codes by User Segment", expanded=False):
        top_3_per_seg = segment_loyal_summary.groupby("User_Segment",observed = True).head(3)

        fig = px.bar(
            top_3_per_seg,
            x="User_Segment",
            y="TXN_AMOUNT",
            color="DESC",
            barmode="group",
            title="<b>Top 3 Loyal Codes by User Segment</b><br><sup>by Spend Volume</sup>",
            template="plotly_white",
        )

        fig.update_layout(height=520, margin=dict(t=90, b=40, l=40, r=40), bargap=0.18, bargroupgap=0.12)
        st.plotly_chart(fig,width='stretch')


