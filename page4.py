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
            Transaction_Count=('JRNO', 'size'),
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
user_reached_1000_agg = users_agg_df[users_agg_df['Reached_1000_Flag'] == 1]
users_agg_df['Inactive'] = (users_agg_df['Transaction_Count'] <= 1).astype(int)
user_under_1000_agg = users_agg_df[(users_agg_df['Reached_1000_Flag'] == 0 ) & (users_agg_df['Inactive'] == 0)]

txn_q25 = user_under_1000_agg['Transaction_Count'].quantile(0.25)
txn_q75 = user_under_1000_agg['Transaction_Count'].quantile(0.75)

days_q25 = user_under_1000_agg['Active_Days'].quantile(0.25)
days_q75 = user_under_1000_agg['Active_Days'].quantile(0.75)

points_q25 = user_under_1000_agg['Total_Points'].quantile(0.25)
points_q75 = user_under_1000_agg['Total_Points'].quantile(0.75)

achievers_txn_q25 = user_reached_1000_agg['Transaction_Count'].quantile(0.25)


def assign_segment(row):

    if row['Inactive'] == 1:
        return 'Inactive'

    if row['Reached_1000_Flag'] == 1:
        return 'Achiever'

    if row['Transaction_Count'] >= achievers_txn_q25:
        return 'High_Effort'

    if row['Transaction_Count'] < txn_q75 and row['Active_Days'] <= days_q75:
        return 'Explorer'

    if row['Transaction_Count'] >= txn_q75 and row['Active_Days'] > days_q75:
        return 'Consistent'
    
    # Everything else
    return 'Irregular_Participant'

users_agg_df['User_Segment'] = users_agg_df.apply(assign_segment, axis=1)

user_segment_monthly_df = users_agg_df.groupby('MONTH_NUM')['User_Segment'].value_counts().reset_index()

segment_map = users_agg_df[['CUST_CODE', 'MONTH_NUM', 'User_Segment']]
loyal_code_agg = df.groupby(['CUST_CODE', 'LOYAL_CODE', 'MONTH_NUM'])['TXN_AMOUNT'].sum().reset_index()

loyal_with_segments = pd.merge(
    loyal_code_agg, 
    segment_map, 
    on=['CUST_CODE', 'MONTH_NUM'], 
    how='inner'
)

segment_loyal_summary = loyal_with_segments.groupby(['User_Segment', 'LOYAL_CODE'])['TXN_AMOUNT'].sum().reset_index()

segment_loyal_summary = segment_loyal_summary.sort_values(['User_Segment', 'TXN_AMOUNT'], ascending=[True, False])

segment_loyal_summary['DESC'] = segment_loyal_summary['LOYAL_CODE'].map(loyal_code_to_desc)

tab1, tab2, tab3, tab4 = st.tabs(['Methodology',"Users reached 1000 (threshold analysis)", "Under 1000 Point User Segmentation", 'User Segment Analysis'])

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
        st.metric("Low (Q25)", f"{txn_q25:.1f} гүйлгээ")
        st.metric("High (Q75)", f"{txn_q75:.1f} гүйлгээ")
        st.caption("Амжилттай хэрэглэгчдийн босго:")
        st.metric("Амжилтийн босго", f"{achievers_txn_q25:.1f} гүйлгээ", help="Bottom 25% of successful users")

    with col2:
        st.subheader("Өдөр")
        st.metric("Low (Q25)", f"{days_q25:.1f} өдөр")
        st.metric("High (Q75)", f"{days_q75:.1f} өдөр")

    with col3:
        st.subheader("Нийт оноо")
        st.metric("Low (Q25)", f"{points_q25:.1f}")
        st.metric("High (Q75)", f"{points_q75:.1f}")

    st.header("Segment Definition Logic")

    logic_data = {
        "Сегмэнт": ["Inactive", "Achiever", "High Effort", "Explorer", "Consistent", "Irregular"],
        "Шалгуур үзүүлэлтүүд": [
            "Inactive Flag = 1",
            "Points >= 1000",
            f"Transactions >= {achievers_txn_q25:.1f}",
            f"Transactions < {txn_q75:.1f} & Days <= {days_q75:.1f}",
            f"Transactions >= {txn_q75:.1f} & Days > {days_q75:.1f}",
            "Fall-through category"
        ],
        "Утга": [
            "Сард зөвхөн 1 гүйлгээ хийсэн хэрэглэгчид.",
            "1000 онооны босго давсан хэрэглэгчид.",
            "1000 оноо давсан хэрэглэгчидтэй адил гүйлгээтэй ч босго даваагүй хэрэглэгчид.",
            "Цөөн өдөр бага гүйлгээтэй туршилт хийж буй хэрэглэгчид.",
            "Олон өдрийн давтамжтай урамшуулалын гүйлгээ хийдэг хэрэглэгчид.",
            "Сегмэнтэд багтаагүй хэрэглээтэй хэрэглэгчид (жишээ: олон өдөр, бага гүйлгээ)."
        ]
    }

    st.table(pd.DataFrame(logic_data))

with tab2:
    user_reached_1000_df = df.groupby(['CUST_CODE', 'MONTH_NUM']).agg(
        {
            'TXN_AMOUNT':'sum',
            'JRNO': 'count',
            'LOYAL_CODE' : 'nunique'
        }
    ).reset_index()
    user_reached_1000_df = user_reached_1000_df[user_reached_1000_df['TXN_AMOUNT'] >= 1000]
    
    fig = make_subplots(rows = 1, cols = 2,
    subplot_titles=("Гүйлгээний тоо (Хэрэглэгчдээр)", 
                    "Ашигласан Лояал кодын тоо", ))

    fig.add_trace(
        go.Histogram(
            x = user_reached_1000_df['JRNO'],
            xbins=dict(start=0, end=400.0, size=20)
            
        ),row=1, col=1
    )

    fig.add_trace(
        go.Histogram(
            x = user_reached_1000_df['LOYAL_CODE'],
            xbins=dict(start=0, end=30, size=1)
        ),row=1, col=2
    )

    fig.update_traces(
        marker_line_width=1, 
        marker_line_color="white", 
        opacity=0.85,
    )

    fig.update_layout(
        title_text = 'Сарын 1000 онооны босгыг давсан хэрэглэгчид',
        showlegend=False
    )

    user_reached_1000_agg = users_agg_df[users_agg_df['Reached_1000_Flag'] == 1]

    fig = go.Figure()
    fig.add_trace(go.Box(
        y=user_reached_1000_agg['Transaction_Count'],
        name="Гүйлгээ",
        marker_color='#636EFA',      
        boxpoints='outliers',        
        jitter=0.3,                  
        pointpos=-1.8,
        fillcolor='rgba(99, 110, 250, 0.5)', 
        line_width=2
    ))

    fig.update_layout(
        title={
            'text': "<b>Гүйлгээний тооны тархалт</b><br><span style='font-size:12px'>1,000 онооны босго давсан хэрэглэгчид</span>",
            'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top'
        },
        yaxis_title="Гүйлгээний тоо",
        template="plotly_white", height=500, showlegend=False
    )

    mean_val = user_reached_1000_agg['Transaction_Count'].mean()
    q1_val = user_reached_1000_agg['Transaction_Count'].quantile(0.25)
    fig.add_hline(y=mean_val, line_dash="dash", line_color="red", annotation_text=f"Дундаж: {mean_val:.1f}")
    fig.add_hline(y=q1_val, line_dash="dash", line_color="red", annotation_text=f"Q1: {q1_val:.1f}")
    
    # 2. Идэвхтэй өдрийн тархалт (Box Plot)
    fig_2 = go.Figure()
    fig_2.add_trace(go.Box(
        y=user_reached_1000_agg['Active_Days'],
        name="Идэвхтэй өдөр",
        marker_color='#636EFA',      
        boxpoints='outliers',        
        jitter=0.3,                  
        pointpos=-1.8,
        fillcolor='rgba(99, 110, 250, 0.5)', 
        line_width=2
    ))

    fig_2.update_layout(
        title={
            'text': "<b>Идэвхтэй хоногийн тархалт</b><br><span style='font-size:12px'>1,000 онооны босго давсан хэрэглэгчид</span>",
            'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top'
        },
        yaxis_title="Идэвхтэй хоногийн тоо",
        template="plotly_white", height=500, showlegend=False
    )

    q1_val_days = user_reached_1000_agg['Active_Days'].quantile(0.25)
    fig_2.add_hline(y=q1_val_days, line_dash="dash", line_color="red", annotation_text=f"Q1: {q1_val_days:.1f}")
    
    fig_3 = go.Figure()
    fig_3.add_trace(go.Box(
        y=user_reached_1000_agg['Unique_Loyal_Codes'],
        name="Давтагдаагүй лояал код",
        marker_color='#636EFA',      
        boxpoints='outliers',        
        jitter=0.3,                  
        pointpos=-1.8,
        fillcolor='rgba(99, 110, 250, 0.5)', 
        line_width=2
    ))

    fig_3.update_layout(
        title={
            'text': "<b>Лояал кодын тооны тархалт</b><br><span style='font-size:12px'>1,000 онооны босго давсан хэрэглэгчид</span>",
            'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top'
        },
        yaxis_title="Кодын тоо",
        template="plotly_white", height=500, showlegend=False
    )

    q1_val_loy = user_reached_1000_agg['Unique_Loyal_Codes'].quantile(0.25)
    fig_3.add_hline(y=q1_val_loy, line_dash="dash", line_color="red", annotation_text=f"Q1: {q1_val_loy:.1f}")

    # Багануудыг байршуулах
    col1, col2, col3 = st.columns([0.33, 0.33, 0.33])
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.plotly_chart(fig_2, use_container_width=True)
    with col3:
        st.plotly_chart(fig_3, use_container_width=True)

    # Дүн шинжилгээний хэсэг
    st.header("3. Боломжит хамгийн бага идэвх (Доод квартил = 25%)")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### 25 дахь перцентиль \n*(Амжилттай хэрэглэгчдийн доод 25%)*")

    with col2:
        mve_data = {
            "Үзүүлэлт": ["Гүйлгээний тоо", "Идэвхтэй хоног", "Нийт оноо"],
            "Дүн": [57, 5, 1000],
            "Утга": ["Хамгийн бага идэвхтэй хэрэглэгчид дунджаар ~57 гүйлгээ хийсэн", "Тэд хамгийн багадаа 5 өөр өдөр идэвхтэй байсан", "Босго оноог арай ядан давсан"]
        }
        st.table(pd.DataFrame(mve_data))

    st.markdown("""
    **Дүгнэлт:**
    **~57-оос бага** гүйлгээ хийсэн эсвэл **~5-аас цөөн** өдөр идэвхтэй байсан хэрэглэгч 1000 оноонд хүрэх магадлал маш бага байна.
    """)

    st.markdown("---")

    st.header("4. Дундаж амжилттай хэрэглэгчийн зан төлөв (50%)")
    m1, m2, m3 = st.columns(3)
    m1.metric("Гүйлгээний тоо", "102")
    m2.metric("Идэвхтэй хоног", "10")
    m3.metric("Нийт оноо", "1,005")

    st.markdown("""
        Ердийн амжилттай хэрэглэгч сарын **гуравны нэгт** нь идэвхтэй байж, **~100 гүйлгээ** хийдэг байна.
    """)

    st.markdown("---")

    st.header("5. Өндөр идэвхтэй хэрэглэгчид (75%)")
    strong_data = {
        "Үзүүлэлт": ["Гүйлгээний тоо", "Идэвхтэй хоног"],
        "75 дахь перцентиль": [158, 19]
    }
    st.dataframe(pd.DataFrame(strong_data), use_container_width=True,hide_index=True)

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
            title="<b>User Segmentation Map</b><br><sup>Visualizing segments based on Active Days and Transaction thresholds</sup>",
        labels={"Active_Days": "Consistency (Active Days)", "Transaction_Count": "Intensity (Transactions)"},
        opacity=0.5,
        category_orders={"User_Segment": ["High_Effort", "Consistent", "Irregular_Participant", "Explorer"]},
    )


    line_style = dict(color="#666666", width=2, dash="dash")


    for val in [days_q25, days_q75]:
        fig.add_vline(x=val, line=line_style)

    for val in [txn_q25, txn_q75, achievers_txn_q25]:
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
        font=dict(family="Arial", size=14, color="#374151")
    )

    st.plotly_chart(fig, use_container_width=True)

    st.caption('Inactive болон 1000 оноо давсан хэрэглэгчдээс бусад сегмэнтийн тархалтыг харуулав')


    st.divider()
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
    st.plotly_chart(fig, use_container_width=True)
   
    st.caption('Сегмэнтэлсэн хэрэглэгчдийн бүлгийн тахацийг харуулав')
    
with tab4:

    with st.expander('Monthly User Distibution by Segment',expanded=False):
        fig = px.line(
        user_segment_monthly_df,
        x='MONTH_NUM',
        markers=True,
        y='count',
        color='User_Segment',    
        title="<b>Monthly User Distribution by Segment</b><br><sup>Comparing total user volume across Months</sup>",
        labels={'count': 'Number of Users', 'MONTH_NUM': 'Month'},
        template="plotly_white"
        )

        fig.update_yaxes(matches='y', showgrid=True) 
        fig.update_xaxes(tickmode='linear')          

        fig.update_layout(
            showlegend=True,            
            margin=dict(t=100, b=50, l=50, r=50),
            font=dict(family="Arial", size=12),
        )

        st.plotly_chart(fig, use_container_width=True)

    with st.expander('Monthly User Point Distribution by Segment',expanded=False):
        user_segment_points_df = users_agg_df.groupby(['User_Segment', 'MONTH_NUM'])['Total_Points'].sum().reset_index()

        fig = px.line(
            user_segment_points_df,
            x='MONTH_NUM',
            markers=True,
            y='Total_Points',
            color='User_Segment',    
            title="<b>Monthly User Point Distribution by Segment</b><br><sup>Comparing total Points across Months</sup>",
            labels={'count': 'Number of Users', 'MONTH_NUM': 'Month'},
            template="plotly_white",
            #log_y=True
        )

        fig.update_yaxes(matches='y', showgrid=True) 
        fig.update_xaxes(tickmode='linear')          

        fig.update_layout(
            showlegend=True,            
            margin=dict(t=100, b=50, l=50, r=50),
            font=dict(family="Arial", size=12),
            height = 500
        )
        st.plotly_chart(fig, use_container_width=True)

    with st.expander('Monthly Average User Point Distribution by Segment',expanded=False):

        user_segment_points_df = users_agg_df.groupby(['User_Segment', 'MONTH_NUM']).agg({
        'Total_Points':'sum',
        'CUST_CODE' : 'count'
        }).reset_index()

        user_segment_points_df['avg_point_per_user'] = (user_segment_points_df['Total_Points'] / user_segment_points_df['CUST_CODE']).round(2)
        
        fig = px.line(
        user_segment_points_df,
        x='MONTH_NUM',
        markers=True,
        y='avg_point_per_user',
        color='User_Segment',    
        title="<b>Monthly Average User Point Distribution by Segment</b><br><sup>Comparing Average Points across Months</sup>",
        labels={'count': 'Number of Users', 'MONTH_NUM': 'Month'},
        template="plotly_white",
        category_orders={"User_Segment": ['Achiever',"High_Effort",  "Consistent", "Irregular_Participant", "Explorer", 'Inactive']},
        #log_y=True
        )

        fig.update_yaxes(matches='y', showgrid=True) 
        fig.update_xaxes(tickmode='linear')          

        fig.update_layout(
            showlegend=True,            
            margin=dict(t=100, b=50, l=50, r=50),
            font=dict(family="Arial", size=12),
            height = 500
        )
        st.plotly_chart(fig, use_container_width=True)

    with st.expander('Top 3 Loyal Codes by User Segment',expanded=False):
        ordered_segments = ['Achiever', 'High_Effort', 'Consistent', 'Irregular_Participant', 'Explorer', 'Inactive']
        segment_loyal_summary['User_Segment'] = pd.Categorical(
            segment_loyal_summary['User_Segment'], 
            categories=ordered_segments, 
            ordered=True
        )

        segment_loyal_summary = segment_loyal_summary.sort_values(
            by=['User_Segment', 'TXN_AMOUNT'], 
            ascending=[True, False]
        )

        top_3_per_seg = segment_loyal_summary.groupby('User_Segment').head(3)

        fig = px.bar(
            top_3_per_seg,
            x='User_Segment',
            y='TXN_AMOUNT',
            color='DESC',
            barmode='group',
            title="<b>Top 3 Loyal Codes by User Segment</b><br><sup>by Spend Volume</sup>",
            template="plotly_white"
        )
        fig.update_layout(
            bargap=0.15,
            bargroupgap=0.1
        )
        st.plotly_chart(fig, use_container_width=True)

    with st.expander('Top 3 Loyal Codes by User Segment Points per Transaction',expanded=False):
        
        loyal_code_agg = df.groupby(['CUST_CODE', 'LOYAL_CODE', 'MONTH_NUM']).agg({
            'JRNO' : 'count',
            'TXN_AMOUNT':'sum'
        }) .reset_index()

        loyal_with_segments = pd.merge(
            loyal_code_agg, 
            segment_map, 
            on=['CUST_CODE', 'MONTH_NUM'], 
            how='inner'
        )
        
        segment_loyal_summary = loyal_with_segments.groupby(['User_Segment', 'LOYAL_CODE']).agg({
            'TXN_AMOUNT':'sum',
            'JRNO': 'sum'
        }) .reset_index()
        segment_loyal_summary['avg_point_per_transaction'] = (segment_loyal_summary['TXN_AMOUNT'] / segment_loyal_summary['JRNO']).round(2)
        segment_loyal_summary.sort_values(['JRNO','avg_point_per_transaction'], ascending=[False,False])
        ordered_segments = ['Achiever', 'High_Effort', 'Consistent', 'Irregular_Participant', 'Explorer', 'Inactive']
        segment_loyal_summary['User_Segment'] = pd.Categorical(
            segment_loyal_summary['User_Segment'], 
            categories=ordered_segments, 
            ordered=True
        )

        segment_loyal_summary = segment_loyal_summary.sort_values(
            by=['User_Segment', 'TXN_AMOUNT'], 
            ascending=[True, False]
        )

        segment_loyal_summary['DESC'] = segment_loyal_summary['LOYAL_CODE'].map(loyal_code_to_desc)

        top_3_per_seg = segment_loyal_summary.groupby('User_Segment').head(3)

        fig = px.bar(
            top_3_per_seg,
            x='User_Segment',
            y='avg_point_per_transaction',
            color='DESC',
            barmode='group',
            title="<b>Top 3 Loyal Codes by User Segment</b><br><sup>by Points per Transaction</sup>",
            template="plotly_white"
        )
        fig.update_layout(
            bargap=0.15,
            bargroupgap=0.1
        )
        st.plotly_chart(fig,use_container_width=True)
        