import streamlit as st
from data_loader import load_data, get_lookup
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from plotly.subplots import make_subplots


@st.cache_data(show_spinner=False)
def load_base():
    return load_data()

df = load_base()
df = df[(df.TXN_DATE >= "2025-01-01") & (df.TXN_DATE <= "2025-12-31")]
st.write("Columns:", df.columns.tolist())



st.header('ОНЦЛОХ САРЫН ШИНЖИЛГЭЭ 2025 ОН', anchor='center')

def donut_plot(df, labels_col, values_col, title_text=""):
    fig = go.Figure(data=[go.Pie(
        labels=df[labels_col], 
        values=df[values_col], 
        hole=.6,              
        marker=dict(line=dict(color='#FFFFFF', width=2)), # White borders between slices
        hoverinfo='label+percent+value',
        textinfo='percent',    
        textfont_size=16,
    )])

    fig.update_layout(
        title=dict(
            text=f"<b>{title_text}</b>",
            #x=0.5,            
            font=dict(size=24)
        ),
        height=500,            
        width=800,             
        
        # CLEANING UP
        template='plotly_white',
        showlegend=True,
        legend=dict(
            orientation="h",   
            yanchor="bottom",
            y=-0.2,            
            xanchor="center",
            x=0.5,
            font=dict(size=14)
        ),
        #"Donut Hole" text
        annotations=[dict(text='Total', x=0.5, y=0.5, font_size=20, showarrow=False)]
    )
    
    return fig

monthly_totals = (
    df
    .groupby('MONTH_NUM', as_index=False,observed=True)['TXN_AMOUNT']
    .sum()
)

barplot_month_df = pd.DataFrame({
    'Metric': ['April', 'May', 'Monthly Average'],
    'Total_Points': [
        monthly_totals.loc[monthly_totals['MONTH_NUM'] == 4, 'TXN_AMOUNT'].values[0],
        monthly_totals.loc[monthly_totals['MONTH_NUM'] == 5, 'TXN_AMOUNT'].values[0],
        monthly_totals['TXN_AMOUNT'].mean()
    ]
})

monthly_total_code = (
    df
    .groupby('MONTH_NUM', as_index=False,observed=True)['LOYAL_CODE']
    .nunique()
)

barplot_code_month_df = pd.DataFrame({
    'Metric': ['April', 'May', 'Monthly Average'],
    'Total_Points': [
        monthly_total_code.loc[monthly_total_code['MONTH_NUM'] == 4, 'LOYAL_CODE'].values[0],
        monthly_total_code.loc[monthly_total_code['MONTH_NUM'] == 5, 'LOYAL_CODE'].values[0],
        monthly_total_code['LOYAL_CODE'].mean()
    ]
})


def metric_colors(metrics, main_color):
    return ['#7f7f7f' if m == 'Monthly Average' else main_color for m in metrics]

#tab1, tab2, tab3 = st.tabs(["4,5-р САР (ХЭРЭГЛЭГЧДИЙН ӨСӨЛТ)", " 7,8-р САР (УНАЛТ) ","10,11-р САР (ХЭРЭГЛЭГЧДИЙН АМЖИЛТИЙН ӨСӨЛТ) "])
tab1, tab2 = st.tabs(["4,5-р САР (ХЭРЭГЛЭГЧДИЙН ӨСӨЛТ)", " 7,8-р САР (УНАЛТ) "])

with tab1:
    fig = make_subplots(
        specs=[[{"secondary_y": True}]]
    )

    # --- Total Points (Left Y-axis) ---
    fig.add_trace(
        go.Bar(
            x=barplot_month_df['Metric'],
            y=barplot_month_df['Total_Points'],
            name='Нийт Оноо',
            text=barplot_month_df['Total_Points'],
            texttemplate='%{text:,.0f}',
            marker_color=metric_colors(barplot_month_df['Metric'], '#368ac6'),
            offsetgroup=0
        ),
        secondary_y=False
    )

    # --- Unique LOYAL_CODE (Right Y-axis) ---
    fig.add_trace(
        go.Bar(
            x=barplot_code_month_df['Metric'],
            y=barplot_code_month_df['Total_Points'],
            name='Урамшууллын тоо',
            text=barplot_code_month_df['Total_Points'],
            texttemplate='%{text:,.0f}',
            marker_color=metric_colors(barplot_code_month_df['Metric'], '#29aa29'),
            offsetgroup=1
        ),
        secondary_y=True
    )

    # --- Layout ---
    fig.update_layout(
        height = 500,
        barmode='group',
        bargap=0.35,
        showlegend=True,
        xaxis_title='',
        title=dict(
            text = '5,6-р сар vs Сарын дундаж',
            xanchor = 'center',
            x = 0.5
        ),
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.91
        ),
        
    )

    fig.update_yaxes(
        title_text='Нийт Оноо',
        tickformat=',',
        secondary_y=False
    )

    fig.update_yaxes(
        title_text='Урамшууллын тоо',
        tickformat=',',
        secondary_y=True
    )

    fig.add_hline(y=2526892, 
                line_dash="dash", 
                line_color="red",
                line_width = 2, 
            # annotation_text="Сарын дундаж оноо",
                opacity=0.5
    )

    fig.add_hline(y=29, 
                line_dash="dash", 
                line_color="blue",
                line_width = 2, 
                #annotation_text="Сарын дундаж урамшууллын тоо",
                opacity=0.5,
                yref='y2'
    )


    col1,col2 = st.columns([0.6,0.4],gap='large')

    with col1:
        st.plotly_chart(fig,width='stretch')

    with col2:
        st.subheader('Дундаж оноо')
        st.info("""4 болон 5-р сарын оноо
            сарын дундаж оноотой харьцуулахад **544,000 - 963,000** оноогоор илүү байна.    
        """)

        st.subheader('Дундаж урамшууллын төрөл')
        st.info("""4 болон 5-р сарын урамшуулал сарын дундаж урамшуулалтай харьцуулахад **20 - 26** урамшууллаар илүү байна.    
        """)


    with st.expander(expanded=False,label='4,5-р сарын урамшууллуудыг харах:'):
        #st.subheader("4,5-р сарын урамшууллууд")

        target_months = [4, 5]

        loyal_code_months = df.groupby('LOYAL_CODE',observed=True)['MONTH_NUM'].unique()

        loyal_codes_45_only = loyal_code_months[loyal_code_months.apply(lambda months: all(m in target_months for m in months))]

        loyal_codes_45_only_list = loyal_codes_45_only.index.tolist()
        #loyal_codes_45_only_list = loyal_codes_only_in_months(df, [4, 5])
        loyal_codes_45_only = {'LOYAL_CODES' : loyal_codes_45_only_list}
        loyal_codes_45_only = pd.DataFrame({'LOYAL_CODES': [loyal_codes_45_only_list]})
        st.dataframe(loyal_codes_45_only,width = 'stretch',hide_index=True)
        st.caption(f'Бусад саруудад байхгүй зөвхөн 4,5-р сард олгогдсон нийт 28 урамшуулал байна')

    st.info(f"""
        Бүх **28** урамшуулал **Investor Week-тэй** холбоотой бөгөөд нийт **963,922** оноог тараасан нь 4,5-р сарын өсөлт **Investor Week-тэй** шууд хамааралтайг харуулж байна.
    """)
    st.divider()
    filtered_month4 = df[df['MONTH_NUM'] == 4]
    filtered_month4_loyal = filtered_month4.groupby('LOYAL_CODE',observed=True)['TXN_AMOUNT'].sum().sort_values(ascending=False).reset_index()
    investor_week_amount = filtered_month4_loyal[filtered_month4_loyal['LOYAL_CODE'].str.lower().str.contains('investor')]

    investor_week_donut_df = investor_week_amount.nlargest(n=9, columns='TXN_AMOUNT').copy()

    investor_week_sum = investor_week_amount['TXN_AMOUNT'].sum()
    investor_week_other = investor_week_sum - investor_week_donut_df['TXN_AMOUNT'].sum()

    other_row = pd.DataFrame({'LOYAL_CODE': ['OTHER'], 'TXN_AMOUNT': [investor_week_other]})

    investor_week_donut_df = pd.concat([investor_week_donut_df, other_row], ignore_index=True)

    fig = donut_plot(
                investor_week_donut_df, 
                'LOYAL_CODE', 
                'TXN_AMOUNT',
                'Investor Week Top 9 and Other'
            )
    fig.update_layout(
        title=dict(
            xanchor = 'center',
            x = 0.5
        )
    )
    st.plotly_chart(fig,)

    st.markdown(f"""
        - Investor Week: **2025-04-28-аас 2025-05-02** ын хооронд болсон.
        - Нийт **1,627** харилцагчид оролсон
            -   **4-р сарын 30 нд 724** харилцагч оролцсон нь хамгийн их харилцагчид оролцсон өдөр болсон байна.
    """)

    with st.expander(expanded=False, label = "Хүснэгт харах:"):
        st.dataframe(investor_week_amount,hide_index=True, width = 'stretch' )

with tab2:

    with st.expander(label='Шинэ Хэрэглэгчийн Шинжилгээ:', expanded=True):
        col1,col2 = st.columns([0.6,0.4])
        with col1:
            user_first_month = df.groupby('CUST_CODE',observed=True)['MONTH_NUM'].min().reset_index()
            cust_point_monthly = df.groupby(['CUST_CODE', 'MONTH_NUM'],observed=True)['TXN_AMOUNT'].sum().reset_index()
            new_user_df = pd.merge(left=user_first_month, right=cust_point_monthly, on=['CUST_CODE','MONTH_NUM'],how='left')
            new_user_df = new_user_df.groupby('MONTH_NUM',observed=True).agg({
                'CUST_CODE': 'nunique',
                'TXN_AMOUNT':'sum'
            }).reset_index()
            new_user_df = new_user_df[new_user_df['MONTH_NUM'] > 1]



            fig = make_subplots(
                    specs=[[{"secondary_y": True}]]
            )
            colors = ['lightslategray',] * 11
            colors[5:7] =['crimson', 'crimson']

            fig.add_trace(
                go.Bar(
                    x = new_user_df['MONTH_NUM'],
                    y = new_user_df['TXN_AMOUNT'],
                    name = 'Шинэ Хэрэглэгчдийн Оноо',
                    text= new_user_df['TXN_AMOUNT'],
                    textposition='inside',
                    texttemplate='%{y:,}',
                    marker_color = colors,
                    hovertemplate=("Нийт оноо %{y:,.0f}" \
                            "<extra></extra>")
                ),
                secondary_y=False
            )

            fig.add_trace(
                go.Scatter(
                    x = new_user_df['MONTH_NUM'],
                    y= new_user_df['CUST_CODE'],
                    name = 'Шинэ Хэрэглэгчдийн Тоо'
                    #labels={'MONTH_NUM': 'Сар' , 'IS_NEW_USER': 'Шинэ Хэрэглэгчдийн тоо'}

                ),
                secondary_y=True
            )
            fig.update_layout(
                xaxis=dict(
                    tickmode = 'linear'
                ),
                legend = dict(
                    yanchor = 'top',
                    xanchor='right',
                    y = 0.99,
                    x = 0.99
                ),
                    hovermode= 'x unified',
                    template="plotly_white",
                title=dict(
                    xanchor= 'center',
                    x=0.5,
                    text = 'Шинэ Хэрэглэгчдийн Тоо болон Оноо'
                )
            )
            fig.update_yaxes(
                    title_text="Нийт Оноо",
                    tickformat=",",
                    secondary_y=False
                )

            fig.update_yaxes(
                    title_text="Нийт Хэрэглэгчдийн тоо",
                    secondary_y=True,
                    rangemode='tozero'
                )
            
            
            fig.update_xaxes(
                    title_text="Сар",
                )
            fig.update_layout(legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ))
            st.plotly_chart(fig, )

        with col2:
            st.subheader('Графикийн тайлбар:')
            st.markdown("""
                Хэрэглэгчдийн хамгийн анхны гүйлгээний өдрийг ашиглан шинэ хэрэглэгч үгүйг тодорхойлсон.        
            """)
            st.info("""
                    - 7,8-р сарын уналтын 1 шалтаан нь шинэ хэрэглэгчдийн тоо багассантай холбоотой байна. 
                    - Энэ сарууд шинэ хэрэглэгчдийн сарын дундаж онооноос **(184,389 - 194,389)** -р бага оноо цуглуулсан байна.""" )
            
    st.divider()        

    with st.expander(label = 'Урамшууллын бүлэг:', expanded=True):
        code_group_acc_insur_df = df[df['CODE_GROUP'].isin(['Insurance','Investments & Securities','Account Opening'])].groupby(['MONTH_NUM', 'CODE_GROUP'],observed=True).agg({
            'JRNO': 'count',
            'TXN_AMOUNT': 'sum',
            'CUST_CODE': 'nunique'
        }).reset_index()

        monthly_total_points_df = df.groupby('MONTH_NUM',observed=True)['TXN_AMOUNT'].sum().reset_index(name='TOTAL_POINTS')

        code_group_acc_insur_df = pd.merge(left=code_group_acc_insur_df,right = monthly_total_points_df, on='MONTH_NUM')
        code_group_acc_insur_df['PERCENTAGE'] =( code_group_acc_insur_df['TXN_AMOUNT'] / code_group_acc_insur_df['TOTAL_POINTS'] * 100 ).round(2)
        fig = px.area(code_group_acc_insur_df, 
                x='MONTH_NUM', 
                y='TXN_AMOUNT', 
                color='CODE_GROUP',
                title='Нөлөө бүхий Урамшууллууд',
                labels={'MONTH_NUM': 'Сар', 'TXN_AMOUNT': 'Нийт Оноо'},
                line_group='CODE_GROUP',
                custom_data=['PERCENTAGE']
        )
        

        # Adding a "Policy Change" marker
        fig.add_vline(x=7, line_dash="dash", line_color="red")
        fig.add_annotation(
            x=7.1, 
            y=50000,
            text="Урамшуулал Зогссон", 
            showarrow=True, 
            arrowhead=1,
            ax=70, 
            ay=-70
        )
        fig.update_layout(
            xaxis=dict(
                tickmode = 'linear'
            ),
            title = dict(
                xanchor = 'center',
                x= 0.5
            )
        )
        fig.update_traces(
            hovertemplate="<b>%{fullData.name}</b><br>Оноо: %{y}<br>Хувь: %{customdata[0]}%"
        )
        
        fig.update_layout(
                legend = dict(
                    yanchor = 'top',
                    xanchor='right',
                    y = 0.99,
                    x = 0.99
                ),
                    hovermode= 'x unified',
                    template="plotly_white",
                title=dict(
                    xanchor= 'center',
                    x=0.5,
                    text = 'Шинэ Хэрэглэгчдийн Тоо болон Оноо'
                )
            )
        st.plotly_chart(fig,width='stretch')

        st.subheader('Урамшуулалтай холбоотой уналт:')
        st.info("""
                - Даатгал болон Данс нээсний урамшуулал 7-р сарын 2 нд зогссон бол Хөрөнгө оруулалтийн оноо эрс буурсан.
                - Сард дунджаар **2,200,000** оноо тараагсан нь 7-р сараас **470,000** 8-р сараас **732,000** оноогоор илүү байна.
                - Хөрөнгө оруулалт, Даатгал болон Данс нээсэнд эхний 6 сард дунджаар **456,000** (256,000 - 732,000) оноо тараагдсан байна
                - Эдгээр урамшууллууд нь сарын нийт тараагдсан онооны **13% - 23%** ийг эзэлдэг байсан.
        """)

# with tab3:
#     ...