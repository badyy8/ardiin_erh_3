import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data_loader import load_data

#[theme]
#base="dark"
#backgroundColor="#484848"


# Functions 

@st.cache_data(show_spinner=False)
def get_monthly_customer_points(df):
    monthly_customer_points = (
        df.groupby(
            ['MONTH_NUM', 'MONTH_NAME', 'CUST_CODE'],
            observed=True
        )['TXN_AMOUNT']
        .sum()
        .reset_index()
    )
    monthly_customer_points.rename(columns={'TXN_AMOUNT' : 'Total_Points'}, inplace=True)

    return monthly_customer_points

@st.cache_data(show_spinner=False)
def get_freq(df):

    cust_freq = df.groupby(
            ['MONTH_NUM', 'MONTH_NAME', 'CUST_CODE'],
            observed=True
        )['JRNO'].count().reset_index()
    
    cust_freq.rename(columns={'JRNO' : 'Total_Freq'}, inplace=True)

    return cust_freq     

@st.cache_data(show_spinner=False)
def get_reached_1000_df(monthly_customer_points):
    monthly_customer_points = monthly_customer_points.copy()
    monthly_customer_points['REACHED_1000'] = monthly_customer_points['Total_Points'] >= 1000
    monthly_customer_points['DID_NOT_REACH_1000'] = monthly_customer_points['Total_Points'] < 1000

    # 2. Group by month and sum the flags to get the counts
    reached_1000_df = monthly_customer_points.groupby(['MONTH_NAME'],as_index=False).agg({
        'REACHED_1000': 'sum',
        'DID_NOT_REACH_1000': 'sum'
    }).rename(columns={
        'REACHED_1000': '1000 оноо хүрсэн',
        'DID_NOT_REACH_1000': '1000 оноо хүрээгүй'
    })

    month_order = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 
                'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    
    reached_1000_df['MONTH_NAME'] = pd.Categorical(
        reached_1000_df['MONTH_NAME'],
        categories=month_order, 
        ordered= True
    )
    
    reached_1000_df = reached_1000_df.sort_values('MONTH_NAME')
    reached_1000_df = reached_1000_df.rename(columns={'MONTH_NAME' : 'Сар'})
    return reached_1000_df

def bar_plot_h(df, x, y, selected_month):
    fig = px.bar(
        df,
        x=x, 
        y=y,
        orientation='h',
        labels={x: 'Value', y: 'Category'}, 
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
            text=f'<b>{selected_month}-р сарын хэрэглэгчдийн онооны хувиарлалт </b>',
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

# Data Load 
df = load_data()
monthly_customer_points = get_monthly_customer_points(df)
cust_freq = get_freq(df)
reached_1000_df = get_reached_1000_df(monthly_customer_points)

# Global widgets 
months = (
    monthly_customer_points
    .sort_values('MONTH_NUM')
    [['MONTH_NUM', 'MONTH_NAME']]
    .drop_duplicates()
)

tab1, tab2, tab3 = st.tabs(['САР БҮРИЙН ОНООНЫ ТАРХАЛТ', "ХЭРЭГЛЭГЧДИЙН ОНООНЫ БҮЛЭГ", "1000 ОНООНЫ БОСГО ДАВСАН ХЭРЭГЛЭГЧИД",])

with tab3:

    reached_1000_df['Total'] = reached_1000_df['1000 оноо хүрсэн'] + reached_1000_df['1000 оноо хүрээгүй']
    reached_1000_df['Percentage'] = (reached_1000_df['1000 оноо хүрсэн'] / reached_1000_df['Total'] * 100).round(2)

    
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=reached_1000_df['Сар'], 
            y=reached_1000_df['1000 оноо хүрээгүй'], 
            name="1000 хүрээгүй", 
            marker_color='lightgrey'
        ),
        secondary_y=False,
    )

    #top (above 1000)
    fig.add_trace(
        go.Bar(
            x=reached_1000_df['Сар'], 
            y=reached_1000_df['1000 оноо хүрсэн'], 
            name="1000 хүрсэн", 
            marker_color='blue'
        ),
        secondary_y=False,
    )

    # line chart red
    fig.add_trace(
        go.Scatter(
            x=reached_1000_df['Сар'], 
            y=reached_1000_df['Percentage'], 
            name="Амжилтын хувь (%)", 
            line=dict(color='red', width=3),
            mode='lines+markers+text',
            text=reached_1000_df['Percentage'].astype(str) + '%',
            textposition="top center"
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title_text="Сар бүрийн хэрэглэгчдийн онооны гүйцэтгэл (1000 онооны босго)",
        barmode='stack', # bar stack
        xaxis_title="Сар",
        legend=dict(x=1.1, y=1), # legend right side
        template="plotly_white",
            title={
                'xanchor': 'center',
                'x' : 0.5
            },
    )


    fig.update_yaxes(title_text="Хэрэглэгчийн тоо", secondary_y=False)
    max_pct = reached_1000_df['Percentage'].max()
    fig.update_yaxes(secondary_y=True, range=[0, max_pct * 1.2])

    st.subheader("2025 ОНЫ 1000 ОНООНЫ БОСГО ДАВСАН ХЭРЭГЛЭГЧДИЙН ШИНЖИЛГЭЭ")
    st.plotly_chart(fig)

    with st.expander(expanded=True,label= 'Тайлбар:'):

        st.subheader("Ерөнхий тойм")

        st.markdown(f"""
        - 2025 оны нийт **54,630** хэрэглэгч урамшууллын хөтөлбөрт хамрагдсан
        - Сард дунджаар **649** хэрэглэгч 1000 онооны босгыг давсан нь,
        сарын нийт оролцогчдын **{reached_1000_df['Percentage'].mean():.2f}%**-ийг эзэлж байна.
        """)

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Хамгийн өндөр идэвхтэй сар: 4-р сар")

            st.markdown("""
            - **1000 оноо давсан хэрэглэгч:** 1,262  
            - **Амжилтын хувь:** 6.16%  
            - **Нийт оролцогчид:** 19,210 (2025 оны хамгийн өндөр)
            """)

            st.info(
                "Энэхүү өсөлт нь 4–5-р сард зохион байгуулагдсан "
                "**“Investor Week”** зэрэг маркетингийн ажлуудтай "
                "холбоотой байх магадлалтай."
            )

        with col2:
            st.subheader("Хамгийн бага идэвхтэй сар: 8-р сар")

            st.markdown("""
            - **1000 оноо давсан хэрэглэгч:** 219  
            - **Амжилтын хувь:** 1.62% (жилийн хамгийн доод)  
            - **Нийт оролцогчид:** 13,304
            """)

            st.info(
                "Энэ нь данс нээсний болон даатгалтай холбоотой оноо өгөхийг зогсоосонтой "
                "холбоотой байх магадлалтай."
            )

        st.divider()

        st.subheader("Амжилтын хувийн онцгой үзүүлэлт: 10-р сар")

        st.markdown("""
        - **Нийт оролцогчид:** 11,950  
        - **1000 оноо давсан хэрэглэгч:** 906  
        - **Амжилтын хувь:** **7.05%** (2025 оны хамгийн өндөр)
        """)

        st.info(
            "Нийт хэрэглэгчийн тоо харьцангуй бага байсан хэдий ч "
            "зорилтот хэрэглэгчдэд чиглэсэн илүү үр дүнтэй урамшуулал "
            "хэрэгжсэн байж болзошгүйг харуулж байна."
        )

        st.divider()

        st.subheader("Дүгнэлт")

        st.markdown("""
        - **Хэлбэлзэл:** Сар бүрийн нийт оролцогчдын тоо харьцангуй тогтвортой
        **(11,000 – 20,000)** боловч 1000 оноо давсан хэрэглэгчдийн тоо
        **219 – 1,262** хүртэл огцом хэлбэлзэж байна.

        - **Боломж:** **7–8-р сарууд** амжилтын хувь хамгийн бага байгаа тул
        эдгээр саруудад зориулсан тусгай урамшуулал, богино хугацааны
        идэвхжүүлэлтийн аян хэрэгжүүлэх нь үр дүнтэй байх боломжтой.
        """)


    with st.expander("Хэрэглэгчдийн онооны тархалтыг харах:", expanded=False):
        y_max = monthly_customer_points.groupby('MONTH_NAME') \
            .size().max()
        
        fig = px.histogram(
            #filtered_df,
            monthly_customer_points, 
            x='Total_Points',
            #nbins=30, 
            log_y=True,
            title=f'<b>Хэрэглэгчдийн Онооны Тархалт (Сараар)</b>',
            labels={'Total_Points': 'Total Points Accumulated', 'count': 'Number of Customers'},
            color_discrete_sequence=['#636EFA'], 
            template='plotly_white',
            #animation_group='Total_Points',
            animation_frame='MONTH_NAME',
            
        )
        

        # Refine the visual polish
        fig.update_traces(
            marker_line_width=1, 
            marker_line_color="white", # Separation between bars
            opacity=0.85,
            xbins=dict(start=0, end=3500.0, size=25)
        )

        fig.update_layout(
            bargap=0.05,              # Small gap 
            xaxis_title="<b>Оноо</b>",
            yaxis_title="<b>Хэрэглэгчдийн нийт тоо (Log Scale)</b>",
            hovermode='x unified',
            height = 500,
            autosize=False,
            #frame={'duration': 800, 'redraw': False},
            transition={'duration': 1000},
            title={
                'text': '<b>Хэрэглэгчдийн Онооны Тархалт (Сараар)</b>',
                'y': 0.95,           # Vertically adjusts (1.0 is top)
                'x': 0.5,            # Horizontally sets to 50%
                'xanchor': 'center', # Anchors the title's center to the x coordinate
                'yanchor': 'top',
                'font': dict(size=24)
            },
            xaxis=dict(
                title_font=dict(size=18),
                tickfont=dict(size=14)
            ),
            yaxis=dict(
                title_font=dict(size=18),
                tickfont=dict(size=14)
            )
        )

        # Add shapes
        fig.add_shape(type="rect",
            xref="x", yref="y",
            x0=1000, y0=10000,
            x1=3500, y1=0,
            line=dict(
                color="darkgreen",
                width=3,
            ),
            fillcolor="darkseagreen",
            opacity=0.2
        )

        fig.add_shape(type="rect",
            xref="x", yref="y",
            x0=1000, y0=10000,
            x1=3500, y1=0,
            line=dict(
                color="darkgreen",
                width=3,
            ),
            fillcolor="darkseagreen",
            opacity=0.05,
            label=dict(text="1000 оноо хүрсэн", textposition="top right", font=dict(size=20)),

        )
        
        fig.update_yaxes(
        type="log",
        range=[0, np.log10(y_max) + 0.5],
        autorange=False,
        fixedrange=True
        )

        fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 800
        fig.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 1000

        st.plotly_chart(fig, use_container_width=True)


    with st.expander(label='Хүснэгт харах:', expanded=False):
        st.dataframe(reached_1000_df, hide_index=True, use_container_width=True)


with tab2:

    bins = [0, 200, 500, 1000, monthly_customer_points['Total_Points'].max() + 1]
    labels = ['0-199', '200-499', '500-999', '1000+']
    segments_all_month = monthly_customer_points.copy()

    segments_all_month['Segment'] = pd.cut(
        segments_all_month['Total_Points'],
        bins=bins,
        labels=labels,
        right=False
    )

    segment_counts_all = (
        segments_all_month
        .groupby(['MONTH_NUM', 'Segment'])
        .size()
        .reset_index(name='Counts')
    )
    segment_counts_all['Total_Counts_Monthly'] = (
        segment_counts_all
            .groupby('MONTH_NUM')['Counts']
            .transform('sum')
    )

    segment_counts_all['Percent'] = ((
        segment_counts_all['Counts']/ 
        segment_counts_all['Total_Counts_Monthly']) * 100).round(2)


    heatmap_df = segment_counts_all.pivot(
        index="Segment",
        columns="MONTH_NUM",
        values="Percent"
    )

    heat_fig = px.imshow(
        heatmap_df,
        text_auto=".1f",
        aspect="auto",
        labels=dict(color="Percentage"),
        title="Хэрэглэгчдийн Онооны Бүлэг (%)",
    )
    heat_fig.update_layout(
        xaxis=dict(tickmode="linear", dtick=1),
        title={
            #'text':"Сар Бүрийн Нийт Тараагдсан Оноо болон Нийт Оролцогчид",
            'xanchor': 'center',
            'x' : 0.5
        },
    )
    st.plotly_chart(heat_fig, use_container_width=True)

    with st.expander("Тайлбар", expanded=True):

        st.subheader("2025 ОНЫ ХЭРЭГЛЭГЧДИЙН ОНООНЫ ХЭСЭГЧИЛСЭН ШИНЖИЛГЭЭ")
        st.caption("Онооны ангилал: 0–199 | 200–499 | 500–999 | 1000+")

        st.divider()

        # Зорилго
        st.markdown("#### Зорилго")
        st.write(
            "2025 оны хэрэглэгчдийн урамшууллын онооны тархалтыг "
            "4 сегментээр задлан шинжилж, **идэвхжил, хэлбэлзэл болон "
            "шилжилтийг** тодорхойлох."
        )

        st.divider()

        # Ерөнхий тархалт
        st.subheader("Ерөнхий тархалт (саруудын интервал)")
        st.markdown(
            """
            - **0–199 оноо:** **78.4% – 85.5%** – давамгай сегмент, бага идэвхитэй  
            - **200–499 оноо:** **7.6% – 9.6%** – тогтвортой дунд сегмент  
            - **500–999 оноо:** **2.25% – 8.24%** – өсөх боломжтой сегмент  
            - **1000+ оноо:** **1.62% – 7.05%** – цөөн боловч өндөр үнэ цэнэтэй
            """
        )

        st.divider()

        # Онцлох сарууд
        st.subheader("Онцлох сарууд")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**4–5-р сар (идэвхжилт)**")
            st.write(
                "- 4-р сар: **1000+ : 6.16%** (эхний том оргил)\n"
                "- 5-р сар: **1000+ : 5.34%**"
            )
            st.caption(
                "Кампанит нөлөө (жишээ нь Investor Week) өндөр онооны сегментэд эерэг нөлөөлсөн."
            )
        with col2:
            st.markdown("**9–12-р сар (тэлэлт)**")
            st.write(
                "- 10-р сар: **1000+ : 7.05%** (жилийн дээд)\n"
                "- 12-р сар: **500–999 : 8.2%** (жилийн дээд)"
            )
            st.caption(
                "Дунд сегментээс өндөр сегмент рүү шилжилт эрчимжсэн."
            )

        st.divider()

        # Гол ажиглалт
        st.markdown("#### Гол ажиглалт")
        st.markdown(
            """
            - Хэрэглэгчдийн дийлэнх нь урамшууллыг **тогтмол бус, бага түвшинд** ашиглаж байна  
            - **500–999 онооны сегмент** нь **1000+ руу шилжих хамгийн боломжит бүлэг**  
            - Жилийн сүүлээр онооны хуримтлал огцом нэмэгдсэн
            """
        )

        # st.divider()

        # # Дүгнэлт
        # st.markdown("#### Дүгнэлт")
        # st.markdown(
        #     """
        #     - Өндөр онооны сегмент нь цөөн боловч **стратегийн ач холбогдол өндөр**  
        #     - Дунд сегментэд чиглэсэн идэвхжүүлэлт **хамгийн өндөр өгөөжтэй**
        #     """
        # )

    
    with st.expander('Сар тус бүрээр харах:', expanded=False):
        
        selected_month = st.selectbox(
            'Choose a month to analyze',
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

    with st.expander(label = 'Хүснэгт харах:',expanded=False):
        st.dataframe(segment_counts_all, hide_index=True, use_container_width=True)

with tab1:
    #st.dataframe(cust_freq)
    monthly_total_points_df = monthly_customer_points.groupby(['MONTH_NUM','MONTH_NAME'])['Total_Points'].sum().reset_index()
    #monthly_total_points_df['Total_Points'] = monthly_total_points_df['Total_Points'].round(0)
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Bar: Total Points (left axis)
    fig.add_trace(
        go.Bar(
            x=monthly_total_points_df['MONTH_NAME'],
            y=monthly_total_points_df['Total_Points'],
            name="Total Reward Points",
            text=monthly_total_points_df['Total_Points'],
            texttemplate="%{y:,.0f}",
            textposition="inside",
            hovertemplate=(
                "<b>Нийт Оноо:</b> %{y:,.0f}<br>"
                "<extra></extra>"
            ),
        ),
        secondary_y=False
    )

    # Line: Unique Users (right axis)
    monthly_user_num = (
        df
        .groupby(['MONTH_NUM', 'MONTH_NAME'])['CUST_CODE']
        .nunique()
        .reset_index()
    )

    fig.add_trace(
        go.Scatter(
            x=monthly_user_num['MONTH_NAME'],
            y=monthly_user_num['CUST_CODE'],
            name="Unique Users",
            mode="lines+markers",
            line=dict(width=3),
            hovertemplate=(
                "<b>Оролцогчид (unique):</b> %{y}<br>"
                "<extra></extra>"
            ),
        ),
        secondary_y=True
    )

    fig.update_layout(
        xaxis=dict(tickmode="linear", dtick=1),
        height=500,
        title={
            'text':"Сар Бүрийн Нийт Тараагдсан Оноо болон Нийт Оролцогчид",
            'xanchor': 'center',
            'x' : 0.5
        },
        title_x=0.5,
        template="plotly_white",
        hovermode= 'x unified'
    )

    fig.update_yaxes(
        title_text="Нийт Оноо",
        tickformat=",",
        secondary_y=False
    )

    fig.update_yaxes(
        title_text="Нийт Оролцогчид",
        secondary_y=True,
        rangemode='tozero'

    )

    st.plotly_chart(fig, use_container_width=True)

    merged_monthly_user_point = pd.merge(
            left=monthly_total_points_df,
            right=monthly_user_num,
            on = 'MONTH_NAME'
        )
    merged_monthly_user_point = merged_monthly_user_point[['MONTH_NAME', 'Total_Points', 'CUST_CODE']]   
    merged_monthly_user_point['Хэрэглэгчид_оногдох_оноо'] =( 
    merged_monthly_user_point['Total_Points']/merged_monthly_user_point['CUST_CODE']).round(2)
    
    with st.expander(expanded=True, label='Тайлбар:'):

        st.subheader("Ерөнхий тойм")

        st.markdown(f"""
        - 2025 оны **1–12** дугаар саруудад нийт **54,630** хэрэглэгч урамшууллын хөтөлбөрт хамрагдсан байна.
        - Сард дунджаар **16,095** хэрэглэгч урамшуулалд оролцсон байна.
        """)

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Хамгийн өндөр үзүүлэлттэй сар: 4-р сар")

            st.markdown("""
            - **Нийт тараагдсан оноо:** 3,198,276 (2025 оны хамгийн өндөр)
            - **Нэгж хүнд оногдох оноо:** 156.23  
            - **Нийт оролцогчид:** 20,472 (2025 оны хамгийн өндөр)
            """)

            st.info(
                "Энэхүү өсөлт нь 4–5-р сард зохион байгуулагдсан "
                "**“Investor Week”** зэрэг маркетингийн ажлуудтай "
                "холбоотой байх магадлалтай."
            )

        with col2:
            st.subheader("Хамгийн бага идэвхтэй сар: 8-р сар")

            st.markdown("""
            - **Нийт тараагдсан оноо:** 1,467,130 (2025 оны хамгийн бага)
            - **Нэгж хүнд оногдох оноо:** 108.49  
            - **Нийт оролцогчид:** 13,523
            """)

            st.info(
                "Энэ нь данс нээсний болон даатгалтай холбоотой оноо өгөхийг зогсоосонтой "
                "холбоотой байх магадлалтай."
            )

        st.divider()

        st.subheader("Нэг оролцогчид оногдох онооны онцгой үзүүлэлт: 10-р сар")

        st.markdown("""
            - **Нийт тараагдсан оноо:** 2,341,692 
            - **Нэгж хүнд оногдох оноо:** 182.15  (2025 оны хамгийн өндөр)
            - **Нийт оролцсон хэрэглэгчид:** 12,856
        """)

        st.info(
            "Нийт хэрэглэгчийн тоо харьцангуй бага байсан хэдий ч "
            "зорилтот хэрэглэгчдэд чиглэсэн илүү үр дүнтэй урамшуулал "
            "хэрэгжсэн байж болзошгүйг, харуулж байна."
        )

        st.divider()

        st.subheader("Дүгнэлт")

        st.markdown("""
        - **Хэрэглэгчдийн уналт:** Сар бүрийн нийт оролцогчдын тоо эхний 3 сар харьцангуй тогтвортой
        **(19,300 – 18,400)** байсан боловч 4-р сард огцом өссөний дараа тогтвортойгоор унасаар 10-р сард **12,800** хүрсэн байна.
        - **Боломж:** Хэрэглэгчийн тоо багассан ч эсрэгээрээ нийт цуглуулж буй оноо өсөж байгаа нь чанартай хэрэглэгчдийн тоо ихсэж байгааг харуулж байна.
        """)

    with st.expander(expanded=False, label = 'Хүснэгт харах:'):
        merged_monthly_user_point.columns = ['Сар','Нийт Оноо', 'Нийт Оролцогчид', 'Нэг Хэрэглэгчид оногдох оноо']
        st.dataframe(merged_monthly_user_point, use_container_width=True, hide_index=True)



    