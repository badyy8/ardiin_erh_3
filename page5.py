import streamlit as st
from data_loader import load_data, get_lookup
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from plotly.subplots import make_subplots

df = load_data()

loyal_code_to_desc = get_lookup()

@st.cache_data(show_spinner=False)
def get_user_df():
    users_agg_df = (
        df.groupby(['CUST_CODE', 'MONTH_NUM'])
        .agg(
            Total_Points=('TXN_AMOUNT', 'sum'),
            Transaction_Count=('JRNO', 'count'),
            Unique_Loyal_Codes=('LOYAL_CODE', 'nunique'),
            Active_Days=('TXN_DATE', 'nunique'),
            Dominant_Code_Group=('CODE_GROUP', lambda x: x.mode().iloc[0])
        )
        .reset_index()
    )

    users_agg_df['Reached_1000_Flag'] = (
        users_agg_df['Total_Points'] >= 1000
    ).astype(int)

    return users_agg_df

users_agg_df = get_user_df()
users_agg_df['Inactive'] = (users_agg_df['Transaction_Count'] <= 1).astype(int)
user_under_1000_agg = users_agg_df[(users_agg_df['Reached_1000_Flag'] == 0 ) & (users_agg_df['Inactive'] == 0)]
user_reached_1000_agg = users_agg_df[users_agg_df['Reached_1000_Flag'] == 1]

txn_q25 = user_under_1000_agg['Transaction_Count'].quantile(0.25)
txn_q75 = user_under_1000_agg['Transaction_Count'].quantile(0.75)

days_q25 = user_under_1000_agg['Active_Days'].quantile(0.25)
days_q75 = user_under_1000_agg['Active_Days'].quantile(0.75)

points_q25 = user_under_1000_agg['Total_Points'].quantile(0.25)
points_q75 = user_under_1000_agg['Total_Points'].quantile(0.75)

achievers_txn_q25 = user_reached_1000_agg['Transaction_Count'].quantile(0.25)
def assign_segment(row):

    if row['Inactive'] == 1:
        return 'Идэвхгүй'

    if row['Reached_1000_Flag'] == 1:
        return 'Амжилттай'

    if row['Transaction_Count'] >= achievers_txn_q25:
        return 'Их_чармайлттай'

    if row['Transaction_Count'] < txn_q75 and row['Active_Days'] <= days_q75:
        return 'Туршигч'

    if row['Transaction_Count'] >= txn_q75 and row['Active_Days'] > days_q75:
        return 'Тогтвортой'
    
    # Everything else
    return 'Тогтмол_бус_оролцогч'

users_agg_df['User_Segment'] = users_agg_df.apply(assign_segment, axis=1)


user_reached_1000_agg = users_agg_df[users_agg_df['Reached_1000_Flag'] == 1]

def bar_plot_h(df, x, y, selected_month):
    fig = px.bar(
        df,
        x=x, 
        y=y,
        orientation='h',
        labels={x: 'Утга', y: 'Ангилал'}, 
        color=x,
        text='Percentage',
        color_continuous_scale='Blues', 
        template='plotly_white',  
    )

    fig.update_traces(
        textposition='outside', 
        cliponaxis=False,         
        textfont_size=16,   
    )

    # Combine layout updates into one block
    fig.update_layout(
        height=500,
        coloraxis_showscale=False,
        margin=dict(r=100), # Increased margin for larger % labels
        title=dict(
            text=f'<b>{selected_month}-р сарын хэрэглэгчдийн онооны хуваарилалт </b>',
            font=dict(size=24)
        ),
        xaxis=dict(
            title_text="<b>Нийт хэрэглэгчдийн тоо </b>",
            title_font=dict(size=18),
            tickfont=dict(size=14)
        ),
        yaxis=dict(
            title_text="<b>Онооны хэсгүүд</b>",
            title_font=dict(size=18),
            tickfont=dict(size=14)
        )
    )

    return fig
loyal_code_to_desc = get_lookup()

tab1, tab2, tab3, tab4, tab5 = st.tabs(['Ардын Эрх Сараар',"1000 Хүрсэн Хэрэглэгчдийн Давтамж", "1000 Хүрсэн Хэрэглэгчдийн Онооны Тархалт", 'Зардал/Борлуулалт', 'RDX Хөнгөлөлт'])


with tab1:


    monthly_customer_points = (
            df.groupby(
                ['MONTH_NUM', 'MONTH_NAME', 'CUST_CODE'],
                observed=True
            )['TXN_AMOUNT']
            .sum()
            .reset_index()
        )
    monthly_customer_points.rename(columns={'TXN_AMOUNT' : 'Total_Points'}, inplace=True)

    months = (
        monthly_customer_points
        .sort_values('MONTH_NUM')
        [['MONTH_NUM', 'MONTH_NAME']]
        .drop_duplicates()
    )
    bins = [0, 100, 200,300,400, 500,600,700,800,900, 1000, monthly_customer_points['Total_Points'].max() + 1]
    labels = ['0-99','100-199','200-299','300-399','400-499','500-599', '600-699', '700-799','800-899','900-999', '1000+']

    selected_month = st.selectbox(
    'Шинжилгээ хийх сараа сонгоно уу',
    options=months['MONTH_NUM'],
    key='tab2'
    )

    filtered_df = monthly_customer_points[monthly_customer_points['MONTH_NUM'] == selected_month]
    segments = pd.cut(filtered_df['Total_Points'], bins=bins, labels=labels, right=False)
    segment_counts = segments.value_counts().sort_index()
    segment_counts = segment_counts.to_frame().reset_index()
    segment_counts.columns = ['Segments', 'Counts']

    total_customers = segment_counts['Counts'].sum()
    segment_counts['Percentage'] = (segment_counts['Counts'] / total_customers * 100).round(1)
    segment_counts['Percentage'] = segment_counts['Percentage'].astype(str) + '%'


    fig = bar_plot_h(df=segment_counts, 
            x = 'Counts', 
            y = 'Segments', 
            selected_month=selected_month
    )
    st.plotly_chart(fig)


with tab2:
    user_milestone_counts = user_reached_1000_agg.groupby('CUST_CODE').size().reset_index(name='Times_Reached_1000')

    user_milestone_counts = user_milestone_counts.sort_values(by='Times_Reached_1000', ascending=False)

    reach_frequency = user_milestone_counts.groupby('Times_Reached_1000')['CUST_CODE'].size().reset_index(name='Number_of_Users')
    fig = px.bar(
        reach_frequency,
        x='Times_Reached_1000',
        y='Number_of_Users',
        text='Number_of_Users',
        title="Давхардаагүй тоогоор хэрэглэгчид хэдэн удаа 1,000 онооны босго давсан бэ?",
        labels={'Times_Reached_1000': 'Босгонд хүрсэн тоо', 'Number_of_Users': 'Хэрэглэгчийн тоо'},
        template="plotly_white"
    )

    fig.update_traces(textposition='outside')
    fig.update_xaxes(tickmode='linear')   
    st.plotly_chart(fig,use_container_width=True)

    st.info(
        """
        2025 онд нийт давхардаагүй тоогоор **3,102**, давхардсан тоогоор **9,466** хэрэглэгч 1000 оноо давсан байна.
    """)


with tab3:
    monthly_totals = (
        df.groupby(['CUST_CODE', 'MONTH_NUM'])['TXN_AMOUNT']
        .sum()
        .reset_index(name='True_Monthly_Total')
    )

    loyal_code_agg = df.groupby(['CUST_CODE', 'LOYAL_CODE', 'MONTH_NUM'])['TXN_AMOUNT'].sum().reset_index()
    segment_map = users_agg_df[['CUST_CODE', 'MONTH_NUM', 'User_Segment']]

    total_loyal_df = (
        loyal_code_agg
        .merge(segment_map, on=['CUST_CODE', 'MONTH_NUM'], how='inner')
        .merge(monthly_totals, on=['CUST_CODE', 'MONTH_NUM'], how='left')
    )

    final_df = total_loyal_df[
        total_loyal_df['True_Monthly_Total'] >= 1000
    ].copy()
    final_df = final_df[final_df['LOYAL_CODE'] != '10K_PURCH_INSUR']


    final_df['Normalized_Points'] = (
        final_df['TXN_AMOUNT'] / final_df['True_Monthly_Total']
    ) * 1000


    user_month_profile = (
    final_df
        .groupby(['CUST_CODE', 'MONTH_NUM', 'LOYAL_CODE'])['Normalized_Points']
        .sum()
        .reset_index()
    )
    profile_wide = user_month_profile.pivot_table(
        index=['CUST_CODE', 'MONTH_NUM'],
        columns='LOYAL_CODE',
        values='Normalized_Points',
        fill_value=0
    )

    avg_user_points = (
        profile_wide
        .mean()
        .reset_index()
    )

    avg_user_points.columns = ['LOYAL_CODE', 'Normalized_Points']
    avg_user_points.Normalized_Points.sum()
    avg_user_points = avg_user_points.sort_values(
        'Normalized_Points', ascending=False
    )        
    avg_user_points['Normalized_Points'] = (
        avg_user_points['Normalized_Points']
        / avg_user_points['Normalized_Points'].sum()
        * 1000
    )

    avg_user_points['DESC'] = avg_user_points['LOYAL_CODE'].map(loyal_code_to_desc)
    avg_user_points = avg_user_points[avg_user_points['LOYAL_CODE'] != '10K_PURCH_INSUR']

    threshold = 50 # points

    main = avg_user_points[avg_user_points['Normalized_Points'] >= threshold]
    other_sum = avg_user_points[avg_user_points['Normalized_Points'] < threshold]['Normalized_Points'].sum()

    avg_user_simple = pd.concat([
        main,
        pd.DataFrame([{
            'DESC': 'Бусад үйлдлүүд',
            'Normalized_Points': other_sum
        }])
    ])



    fig = go.Figure()

    for _, row in avg_user_simple.iterrows():
        fig.add_bar(
            y=['Дундаж хэрэглэгч = 1000 Оноо'],
            x=[row['Normalized_Points']],
            name=row['DESC'],
            orientation='h',
            hovertemplate='%{x:.0f} оноог %{fullData.name}-аас авсан<extra></extra>'
        )

    fig.update_layout(
        barmode='stack',
        title='Хэрэглэгч дунджаар хэрхэн 1000 оноонд хүрдэг вэ?',
        xaxis_title='Оноо',
        yaxis_title='',
        template='plotly_white',
        height=350,
        legend_title_text='Үйлдлийн төрөл'
    )

    st.plotly_chart(fig,use_container_width=True)
    st.caption('Даатгал авсны урамшууллын оноог оролцуулаагүй болно')

    top_code = avg_user_points.iloc[0]['LOYAL_CODE']

    share_users = (
        final_df
        .groupby(['CUST_CODE', 'MONTH_NUM'])['LOYAL_CODE']
        .apply(lambda x: top_code in x.values)
        .mean()
    ) * 100


    conditional_avg = (
        final_df[final_df['LOYAL_CODE'] == top_code]
            .groupby(['CUST_CODE', 'MONTH_NUM'])['Normalized_Points']
            .sum()
            .mean()
    )
    avg_loyal_share = (
        final_df
        .groupby(['CUST_CODE', 'MONTH_NUM'])['Normalized_Points']
        .sum()
        .mean()
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "1к эрхийн гүйлгээний урамшууллын оноо",
        f"{avg_user_points.iloc[0]['Normalized_Points']:.0f} оноо"
    )

    col2.metric(
        "Гол урамшууллын ашиглаж буй хэрэглэгчид",
        f"{share_users:.1f}%"
    )


with tab4:
    st.markdown("## 1,000 оноонд хүрэх Зардал / Борлуулалт")
    st.info('**Зардлыг хэрхэн тооцсон бэ?**')
    st.markdown("""

    - Оноо цуглуулах хамгийн боломжит арга бол **дансандаа орлого хийх** юм
        - Хэрэглэгчид **цэнэглэсэн 100,000 төгрөг тутамд 50 оноо** авдаг (**1 оноо = 2,000 төгрөг**)
    """)

    # Base scenario assumptions
    dominant_points = 400
    remaining_points = 600

    mnt_per_block = 100_000
    points_per_block = 50
    cost_per_point = mnt_per_block / points_per_block  # 2,000 MNT

    remaining_cost = remaining_points * cost_per_point

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Үндсэн гүйлгээнээс авсан оноо",
        f"~{dominant_points} оноо"
    )

    col2.metric(
        "Данс цэнэглэлтээр авах оноо",
        f"{remaining_points} оноо"
    )

    col3.metric(
        "Шаардлагатай орлого хийх дүн",
        f"{remaining_cost:,.0f} төг"
    )

    # st.markdown("""
    # **Тайлбар**

    # - Үндсэн гүйлгээний үйлдлээс оноо авсны дараа хэрэглэгчдэд ихэвчлэн  
    #   **~600 нэмэлт оноо** шаардлагатай болдог
    # - Эдгээр оноог цуглуулахын тулд **~1.2 сая төгрөгөөр** дансаа цэнэглэх шаардлагатай
    # """)

    st.divider()

    st.subheader("Хэрэв гүйлгээний урамшууллын оноог 300-аар хязгаарлавал:")
    capped_points = 300
    new_remaining_points = 1000 - capped_points
    new_required_cost = new_remaining_points * cost_per_point
    incremental_cost = new_required_cost - remaining_cost

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "10K_TRANSACTION-аас авах оноо",
        f"{capped_points} оноо",
        delta="-100 оноо"
    )

    col3.metric(
        "Үлдэгдэл оноонд шаардлагатай орлого",
        f"{new_required_cost:,.0f} ТӨГ",
        delta=f"+{incremental_cost:,.0f} ТӨГ"
    )

    col2.metric(
        "Данс цэнэглэлтээр авах оноо",
        f"{new_remaining_points} оноо",
        delta="+100 оноо"
    )

    st.markdown("""
    **Энэхүү өөрчлөлтийн нөлөө**

    - Хэрэглэгчид ижил хэмжээний урамшуулал авахын тулд **илүү их бодит мөнгө** төвлөрүүлэх шаардлагатай болно
    - Шаардлагатай орлого хийх дүн **1.2 сая -аас  1.4 сая төгрөг** болж нэмэгдэнэ
    - Ганцхан төрлийн гүйлгээний урамшууллаас хамааралтай байхыг бууруулна
    """)



with tab5:
    st.markdown("## Хөнгөлөлттэй Ардын Эрх")

    monthly_customer_points = (
    df.groupby(
        ['MONTH_NUM', 'MONTH_NAME', 'CUST_CODE'],
        observed=True
    )['TXN_AMOUNT']
    .sum()
    .reset_index()
    )
    monthly_customer_points.rename(columns={'TXN_AMOUNT': 'Total_Points'}, inplace=True)

    bins = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 
            monthly_customer_points['Total_Points'].max() + 1]
    labels = ['0-99', '100-199', '200-299', '300-399', '400-499', '500-599', 
            '600-699', '700-799', '800-899', '900-999', '1000+']

    # Create segments for ALL months (not filtered)
    monthly_customer_points['Segments'] = pd.cut(
        monthly_customer_points['Total_Points'], 
        bins=bins, 
        labels=labels, 
        right=False
    )

    # Aggregate across all months by counting customers in each segment
    segment_counts = (
        monthly_customer_points
        .groupby('Segments', observed=True)
        .size()
        .reset_index(name='Counts')
    )

    total_customers = segment_counts['Counts'].sum()
    segment_counts['Percentage'] = (segment_counts['Counts'] / total_customers * 100).round(1)
    segment_counts['Percentage'] = segment_counts['Percentage'].astype(str) + '%'

    withdrawal_map = {
        '0-99': 0, '100-199': 0, '200-299': 0, '300-399': 0, '400-499': 0,
        '500-599': 1, '600-699': 1, '700-799': 1, '800-899': 1, '900-999': 1, '1000+': 1,
    }

    segment_counts['Can_Withdraw_Discounted'] = (
        segment_counts['Segments']
        .astype(str)
        .map(withdrawal_map)
        .fillna(0)
        .astype(int)
    )

    segment_counts['Can_Withdraw_Current'] = (
        segment_counts['Segments'] == '1000+'
    ).astype(int)

    current_success = (
        segment_counts
        .loc[segment_counts['Can_Withdraw_Current'] == 1, 'Counts']
        .sum()
    )

    discounted_success = (
        segment_counts
        .loc[segment_counts['Can_Withdraw_Discounted'] == 1, 'Counts']
        .sum()
    )



    total_users = segment_counts['Counts'].sum()

    current_rate = current_success / total_users * 100
    discounted_rate = discounted_success / total_users * 100
    lift = discounted_rate - current_rate

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Одоогийн амжилттай хэрэглэгчдийн тоо",
        f"{current_success:,}",
        help="≥ 1000 RDX оноотой хэрэглэгчид давтагдсан тоогоор"
    )

    col2.metric(
        "Хөнгөлөлттөй ардын эрхийн амжилттай хэрэглэгчдийн тоо",
        f"{discounted_success:,}",
        delta=f"+{discounted_success - current_success:,} хэрэглэгч",
        help="≥ 500 RDX оноотой хэрэглэгчид"
    )

    col3.metric(
        "Амжилтын хувийн өсөлт",
        f"{discounted_rate:.1f}%",
        delta=f"+{lift:.1f} %"
    )
    success_df = pd.DataFrame({
        "Хувилбар": ["Одоогийн (1000 RDX)", "Хөнгөлөлттэй (≥500 RDX)"],
        "Амжилттай хэрэглэгчид": [current_success, discounted_success]
    })

    # Calculate metrics for the title/labels
    increase = success_df.iloc[1]["Амжилттай хэрэглэгчид"] - success_df.iloc[0]["Амжилттай хэрэглэгчид"]
    increase_pct = (increase / success_df.iloc[0]["Амжилттай хэрэглэгчид"] * 100)

    # Create the figure
    fig = px.bar(
        success_df,
        x="Хувилбар",
        y="Амжилттай хэрэглэгчид",
        text="Амжилттай хэрэглэгчид",
        template="plotly_white",
        color="Хувилбар",
        # Grey for baseline, Brand Blue/Green for the 'Win'
        color_discrete_map={
            success_df.iloc[0]["Хувилбар"]: "#BDC3C7", 
            success_df.iloc[1]["Хувилбар"]: "#2ECC71"
        }
    )

    # Refine bar look and labels
    fig.update_traces(
        textposition="inside",
        texttemplate='<b>%{text:,}</b>',
        marker_line_width=0,
        width=0.6 # Thinner bars look more modern
    )

    fig.update_layout(
        height=600,
        title={
            'text': f"Амжилттай хэрэглэгчдийн өсөлт: <span style='color:#2ECC71'>+{increase_pct:.1f}%</span>",
            'y': 0.95,
            'x': 0.05,
            'xanchor': 'left',
            'yanchor': 'top'
        },
        xaxis_title="",
        yaxis_title="Хэрэглэгчдийн тоо",
        showlegend=False,
        margin=dict(t=80, b=20, l=50, r=20),
        yaxis=dict(showgrid=True, gridcolor='#F0F0F0', zeroline=False)
    )

    st.divider()
    # Streamlit Layout
    col1, col2 = st.columns([0.5, 0.5], gap="large")

    with col1:
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(f"""
        ### Шинжилгээний дүгнэлт
        Нөхцөлийг хөнгөлснөөр нийт **{increase:,}** хэрэглэгч шинээр урамшуулал авах боломжтой болж байна.
        
        * **Хүртээмж:** 1,000 RDX-ээс бага оноотой хэрэглэгчид идэвхжих хөшүүрэг болно.
        * **Retention:** Зорилтдоо дөхсөн хэрэглэгчдийг "амжилттай" болгох нь системээс гарах магадлалыг бууруулна.
        """)
        lift_source = segment_counts[

            (segment_counts['Can_Withdraw_Discounted'] == 1) &

            (segment_counts['Can_Withdraw_Current'] == 0)

        ][['Segments', 'Counts']]
        # Clean up the dataframe view
        st.write("---")
        st.caption("Шинээр нэмэгдэж буй сегментүүд")
        st.dataframe(
            lift_source.style.background_gradient(cmap='Greens', subset=['Counts']),
            use_container_width=True,
            hide_index=True
        )