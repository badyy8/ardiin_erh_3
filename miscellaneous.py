import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Import your loaders
from data_loader import (
    load_data, get_lookup,
    load_precomputed_page_misc_counts,
    load_precomputed_page_misc_loyal_avg,
    load_precomputed_page_misc_reach_frequency,
)

# 1. CACHED DATA LOADING (Moves data to memory once, prevents re-reading disk)
@st.cache_data(show_spinner="Өгөгдөл ачаалж байна...")
def get_all_data():
    df, lookup = load_data(), get_lookup()
    counts = load_precomputed_page_misc_counts()
    loyal_avg = load_precomputed_page_misc_loyal_avg()
    reach = load_precomputed_page_misc_reach_frequency()
    return df, lookup, counts, loyal_avg, reach

# Initialize Data
df, loyal_code_to_desc, counts_all, loyal_avg_all, reach_freq_all = get_all_data()

# --- Sidebar ---
available_years = sorted(counts_all["year"].dropna().astype(int).unique())
selected_year = st.sidebar.selectbox("Жил сонгох", available_years, index=len(available_years) - 1)

# --- Tabs ---
tab1, tab2 = st.tabs(['Хэрэглэгчдийн Онооны Тархалт', '1000 Хүрсэн Хэрэглэгчдийн Онооны Тархалт'])

bucket_order = ['0-49','50-99','100-199','200-299','300-399','400-499','500-599','600-699','700-799','800-899','900-999','1000+']

with tab1:
    # Filter only what we need for this year to save RAM
    counts = counts_all[counts_all["year"] == selected_year].copy()
    loyal_avg = loyal_avg_all[loyal_avg_all["year"] == selected_year].copy()

    # --- Plot 1: Points Distribution ---
    fig1 = px.bar(
        counts,
        x="Counts",
        y="point_bucket",
        orientation="h",
        animation_frame="year_month",
        category_orders={"point_bucket": bucket_order},
        template="plotly_white",
        height=500
    )
    fig1.update_layout(
        title_text="<b>Хэрэглэгчдийн Онооны Тархалт</b>", 
        title = {
            'xanchor' : 'center',
            'x': 0.5
        },
    )
    st.plotly_chart(fig1, use_container_width=True)

    # --- Plot 2: Average Points ---
    loyal_avg_fig_df = loyal_avg[(loyal_avg.PERCENTAGE > 1) & (loyal_avg.LOYAL_CODE != 'None')].nlargest(10, 'AVG').sort_values('AVG')
    
    fig2 = px.bar(
        loyal_avg_fig_df,
        x='AVG', y='DESC', color='AVG', text='AVG',
        labels={'DESC': 'УРАМШУУЛЛЫН НЭР', 'AVG': 'ДУНДАЖ ОНОО'}
    )
    st.divider()
    fig2.update_layout(
        title_text="<b>Нэгж гүйлгээний дундаж урамшууллын онооны шинжилгээ</b>", 
        title = {
            'xanchor' : 'center',
            'x': 0.5
        },
    )
    st.plotly_chart(fig2, use_container_width=True)

    # --- Analysis Section (Memory Optimized) ---
    with st.expander("Тайлбар:"):
        df_sorted = loyal_avg.sort_values("TXN_AMOUNT", ascending=False).reset_index(drop=True)
        total_amt = df_sorted["TXN_AMOUNT"].sum()
        
        top5_share = (df_sorted.head(5)["TXN_AMOUNT"].sum() / total_amt * 100) if total_amt > 0 else 0
        
        target_code = "10K_TRANSACTION"
        target_row = loyal_avg[loyal_avg["LOYAL_CODE"] == target_code]
        
        # We avoid running .nunique() on the full DF if possible. 
        # If you MUST use it, filter df specifically for the code first.
        target_users = df[df["LOYAL_CODE"] == target_code]["CUST_CODE"].nunique() if "LOYAL_CODE" in df.columns else 0

        st.markdown(f"""
        #### Гүйлгээний шинжилгээ ({selected_year})
        - **Топ 5** гүйлгээний төрөл нийт онооны **{top5_share:.1f}%**-ийг бүрдүүлж байна.
        - **{target_code}**: Нийт **{target_users:,}** хэрэглэгчдэд оноо тараагдсан.
        """)

with tab2:
    reach_frequency = reach_freq_all[reach_freq_all["year"] == selected_year].copy()

    fig3 = px.bar(
        reach_frequency,
        x="Times_Reached_1000", y="Number_of_Users", text="Number_of_Users",
        color="Number_of_Users", color_continuous_scale="Blues",
        template="plotly_white",
    )
    
    fig3.update_layout(showlegend=False, title_text=f"<b>{selected_year} онд хэрэглэгчдийн босго давсан давтамж</b>",
        xaxis=dict(
            tickmode = 'linear'
        ),
    )
    st.plotly_chart(fig3, use_container_width=True)

    reach_frequency['Total'] = reach_frequency['Number_of_Users'] * reach_frequency['Times_Reached_1000']
    st.info(f"{selected_year} онд нийт **{reach_frequency['Number_of_Users'].sum():,}** хэрэглэгч нийт **{reach_frequency['Total'].sum():,}** удаа 1000 оноо давсан.")