import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from data_loader import (
    load_data, get_lookup,
    load_precomputed_page_misc_counts,
    load_precomputed_page_misc_loyal_avg,
    load_precomputed_page_misc_reach_frequency,
)

tab1,tab2 = st.tabs(['Хэрэглэгчдийн Онооны Тархалт', '1000 Хүрсэн Хэрэглэгчдийн Онооны Тархалт'])    

@st.cache_data(show_spinner=False)
def load_base():
    return load_data(), get_lookup()

df, loyal_code_to_desc = load_base()


available_years = sorted(df["year"].dropna().astype(int).unique())

selected_year = st.sidebar.selectbox(
    "Жил сонгох",
    available_years,
    index=len(available_years) - 1
)
df_year = df[df["year"] == selected_year].copy()



st.sidebar.caption(f"Одоогийн сонголт: {selected_year}")

bucket_order = [
    '0-49','50-99','100-199','200-299','300-399',
    '400-499','500-599','600-699','700-799',
    '800-899','900-999','1000+'
]

with tab1:
    counts_all = load_precomputed_page_misc_counts()
    loyal_avg_all = load_precomputed_page_misc_loyal_avg()
    counts = counts_all[counts_all["year"] == selected_year].copy()
    loyal_avg = loyal_avg_all[loyal_avg_all["year"] == selected_year].copy()
    # ------------------------------------------------------------------
    # Prepare data
    # ------------------------------------------------------------------
    user_level_stat_monthly = counts_all.sort_values("year_month")

    # ------------------------------------------------------------------
    # Plot
    # ------------------------------------------------------------------
    # fig = px.bar(
    #     counts,
    #     x="Counts",
    #     y="point_bucket",
    #     orientation="h",
    #     animation_frame="year_month",
    #     animation_group="point_bucket", 
    #     #color="Counts",
    #     #color_continuous_scale="Blues",
    #     category_orders={"point_bucket": bucket_order},
    #     template="plotly_white",
    # )
    # fig.update_traces(
    #     #texttemplate="%{customdata:.1f}%",
    #     customdata=counts["Percent"],
    #     #textposition="outside",
    #     marker_line_width=1,
    #     marker_line_color="white",
    #     opacity=0.9,
    #     hovertemplate=(
    #         "Онооны ангилал: %{y}<br>"
    #         "Хэрэглэгчдийн тоо: %{x}<br>"
    #         "Хувь: %{customdata:.1f}%"
    #         "<extra></extra>"
    #     ),
    # )
    # fig.update_layout(
    #     bargap=0.05,
    #     xaxis_title="<b>Хэрэглэгчдийн тоо</b>",
    #     yaxis_title="<b>Онооны ангилал</b>",
    #     height = 500,
    #     title=dict(
    #         text="<b>Хэрэглэгчдийн Онооны Тархалт (Сараар)</b>",
    #         x=0.5,
    #         y=0.95,
    #         xanchor="center",
    #         yanchor="top",
    #         font=dict(size=24),
    #     ),
    #     xaxis=dict(title_font=dict(size=18), tickfont=dict(size=14)),
    #     yaxis=dict(title_font=dict(size=18), tickfont=dict(size=14)),
    # )
    # fig.update_xaxes(showgrid=True)

    # fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1000
    # fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 300
    fig = px.bar(counts, x="Counts", y="point_bucket", orientation="h")

    st.plotly_chart(fig, width= 'stretch')

    loyal_avg_fig_df = loyal_avg[(loyal_avg.PERCENTAGE > 1) & (loyal_avg.LOYAL_CODE != 'None')].nlargest(10,columns=['AVG']).sort_values(by='AVG',ascending=True)
    fig = px.bar(
        loyal_avg_fig_df,
        x='AVG',
        y='DESC',
        color = 'AVG',
        text = 'AVG',
        hover_data=['PERCENTAGE'],
        labels= {
            'DESC': 'УРАМШУУЛЛЫН НЭР',
            'AVG': 'ДУНДАЖ ОНОО',
            'PERCENTAGE': 'Эзлэх Хувь'
        },
    )

    fig.update_layout(
        title=dict(
            text = 'Нэгж гүйлгээний дундаж урамшууллын оноо',
            xanchor = 'center',
            x = 0.5
        ),
    )
    fig.update_traces(textposition='outside')
    
    st.divider()

    st.subheader("Нэгж гүйлгээний дундаж урамшууллын онооны шинжилгээ")
    st.plotly_chart(fig,width='stretch')
    st.caption('Нийт оноонд 1% аас илүү хувь нэмэр оруулсан, дундаж оноогоор топ 10-т орсон гүйлгээнүүдийг жагсаав.')
     
    with st.expander(expanded=False, label="Тайлбар:"):

        st.markdown("""
        ### Графикийн тайлбар
        - Гүйлгээний төрлүүдийг **нэг гүйлгээнд ногдох дундаж урамшууллын оноогоор** харьцуулсан  
        - **Багана:** Дундаж онооны хэмжээ  
        - **Баганан дээрх хувь:** Гүйлгээний нийт оноонд эзлэх хувь  
        """)


        df_year_summary = loyal_avg.copy()

        # If loyal_avg has year column, filter correctly
        if "year" in df_year_summary.columns:
            df_year_summary = df_year_summary[df_year_summary["year"] == selected_year].copy()

        total_loyal_types = df_year_summary["LOYAL_CODE"].nunique()

        # Sort by TXN_AMOUNT (most impactful)
        df_sorted = df_year_summary.sort_values("TXN_AMOUNT", ascending=False).reset_index(drop=True)

        # Top5 share
        top5_share = df_sorted.head(5)["TXN_AMOUNT"].sum() / df_sorted["TXN_AMOUNT"].sum() * 100

        # "Top 10% makes 80%" type metric (Pareto-ish)
        n_top10pct = max(1, int(np.ceil(total_loyal_types * 0.10)))
        top10pct_share = df_sorted.head(n_top10pct)["TXN_AMOUNT"].sum() / df_sorted["TXN_AMOUNT"].sum() * 100

        # Top10pct count shown like (x/total)
        top10pct_count_text = f"{n_top10pct}/{total_loyal_types}"

        # 10K_TRANSACTION stats (safe even if missing)
        target_code = "10K_TRANSACTION"
        target_row = df_year_summary[df_year_summary["LOYAL_CODE"] == target_code]

        target_desc = (
            target_row["DESC"].dropna().iloc[0]
            if ("DESC" in target_row.columns and not target_row["DESC"].dropna().empty)
            else target_code
        )

        target_points = target_row["TXN_AMOUNT"].sum() if not target_row.empty else 0

        # if df_year exists, get unique users; otherwise show "-"
        if "df_year" in locals():
            target_users = df_year[df_year["LOYAL_CODE"] == target_code]["CUST_CODE"].nunique()
            target_users_text = f"{target_users:,}"
        else:
            target_users_text = "—"

        st.markdown(f"""
        #### Гүйлгээний шинжилгээ ({selected_year})

        - **Топ 5** гүйлгээний төрөл нийлээд нийт онооны **{top5_share:.1f}%**-ийг бүрдүүлж байна.
        - Бүх гүйлгээний төрлүүдийн **10%** ({top10pct_count_text}) нь нийт онооны **{top10pct_share:.1f}%**-ийг бүрдүүлж байна.

        #### {target_desc} ({target_code})
        - {selected_year} онд нийт **{target_users_text}** хэрэглэгчдэд **{target_points:,.0f}** оноо тараагдсан.
        """)



with tab2:

    
    reach_freq_all = load_precomputed_page_misc_reach_frequency()
    reach_frequency = reach_freq_all[reach_freq_all["year"] == selected_year].copy()

    fig = px.bar(
        reach_frequency,
        x="Times_Reached_1000",
        y="Number_of_Users",
        text="Number_of_Users",
        title=f"<b>{selected_year} онд давхардаагүй тоогоор хэрэглэгчид хэдэн удаа 1,000 онооны босго давсан бэ?</b>",
        labels={"Times_Reached_1000": "Босго давсан удаа", "Number_of_Users": "Хэрэглэгчийн тоо"},
        template="plotly_white",
        color="Number_of_Users",           # Adds a color gradient based on value
        color_continuous_scale="Blues"   
    )

    fig.update_traces(
        textposition="outside",          
        marker_line_color='rgb(8,48,107)', 
        marker_line_width=1.5,
        opacity=0.85                     
    )

    fig.update_layout(
        title_font_size=20,
        xaxis_tickangle=0,
        bargap=0.3,                       
        showlegend=False,                
        hovermode="x unified",            
        font_family="Arial",
        margin=dict(t=80, l=50, r=50, b=50) # Standardize padding
    )

    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_xaxes(tickmode="linear")

    st.plotly_chart(fig, width = 'stretch')

    st.info(
        f"""
        {selected_year} онд нийт давхардаагүй тоогоор **{reach_frequency['Number_of_Users'].sum():,}**
        давхардсан тоогоор **{reach_frequency['Total'].sum():,}** хэрэглэгч 1000 оноо давсан байна.
        """
    )
