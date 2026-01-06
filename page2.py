import streamlit as st
from data_loader import load_data, get_lookup
from page1 import bar_plot_h
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import math

df = load_data()

tab1, tab2, tab3, tab4 = st.tabs(["Methodology", "ГҮЙЛГЭЭНИЙ ОНООНЫ ТАРХАЦ", 'ГҮЙЛГЭЭНИЙ ТӨРЛИЙН ШИНЖИЛГЭЭ (БҮЛЭГЛЭСЭН)', 'ГҮЙЛГЭЭНИЙ ШИНЖИЛГЭЭ'])
month_order = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 
               'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']


# Total Points by Reward group
def get_grouped_reward():
    grouped_reward = df.groupby(['CODE_GROUP','MONTH_NUM', 'MONTH_NAME'])['TXN_AMOUNT'].sum().reset_index()
    grouped_reward.rename(columns = {'TXN_AMOUNT': 'TOTAL_AMOUNT'}, inplace=True)
    return grouped_reward

grouped_reward = get_grouped_reward()


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

with tab1:
    with st.expander("Гүйлгээний ангиллын аргачлал", expanded=True):
        st.markdown(
            """
            ### Гүйлгээний ангиллын тайлбар

            Энэхүү хуудсанд харуулах гүйлгээнүүдийн ангилалыг датасетын **`LOYAL_CODE`** дээр үндэслэн бизнесийн утга агуулгаар нь бүлэглэн ангилав.
            Ангиллын зорилго нь хэрэглэгчдийн оноо цуглуулах үйл ажиллагааг **товчоор, ойлгомжтой** байдлаар нэгтгэхэд оршино.

            #### Ангиллын үндсэн зарчим

            **1. Санхүүгийн гүйлгээ (Financial Transactions)**  
            Мөнгө шилжүүлэлт, төлбөр, зээлийн эргэн төлөлт болон картын гүйлгээнүүд.  

            **2. Данс нээлт (Account Opening)**  
            Хадгаламж, үнэт цаас, тэтгэврийн болон бусад данс нээхтэй холбоотой урамшууллууд.  

            **3. Хөрөнгө оруулалт ба үнэт цаас (Investments & Securities)**  
            Хувьцаа, crypto, арилжаа, 1072 хувьцаа болон хөрөнгө оруулалтын гүйлгээнүүд.  

            **4. Худалдаа, өдөр тутмын хэрэглээ (Merchant & Lifestyle)**  
            Худалдааны түнш, сугалаа, бараа үйлчилгээтэй холбоотой гүйлгээнүүд.  

            **5. Даатгал (Insurance)**  
            Даатгалын бүтээгдэхүүн болон даатгалтай холбоотой урамшуулалууд.  

            **6. Урамшуулалын аян, арга хэмжээ (Campaigns & Events)**  
            Маркетингийн кампанит ажил, Investor Week, сургалт, эвентүүд.  

            **7. Social оролцоо (Social & Engagement)**  
            Сошиал идэвхжил, мэдээлэл унших, селфи, контент хуваалцах үйлдлүүд.  

            **8. Бүс нутгийн аян (Geographic Campaigns)**  
            Тодорхой аймаг, хотод чиглэсэн кампанит ажлууд.
            """,
    )
        st.dataframe(df.groupby('CODE_GROUP')['LOYAL_CODE'].unique(), use_container_width=True)
    
with tab2:
    loyal_code_to_desc = get_lookup()

    # Scatter Plot
    transaction_summary = df.groupby(['LOYAL_CODE', 'MONTH_NAME','MONTH_NUM', 'CODE_GROUP']).agg({
        'JRNO': 'count',
        'CUST_CODE' : 'nunique',
        'TXN_AMOUNT':'sum'
    }).reset_index()


    transaction_summary.columns = ['LOYAL_CODE', 'MONTH_NAME', 'MONTH_NUM','GROUP','Transaction_Freq','Total_Users', 'Total_Amount']
    transaction_summary['DESC'] = transaction_summary['LOYAL_CODE'].map(loyal_code_to_desc)

    significant_movers = [
        '10K_TRANSACTION_CARD',
        '10K_CHARGE_SAVINGS2',
        '10K_GET_LOTTO',
        '10K_CHARGE_LIFE_OLD',
    ]

    transaction_summary['MOVERS'] = transaction_summary['LOYAL_CODE'].isin(significant_movers)
    movers_df = transaction_summary[transaction_summary['MOVERS'] == True]

    fig = px.scatter(transaction_summary, 
            x = 'Total_Users', 
            y = 'Total_Amount', 
            size = 'Transaction_Freq',
            size_max = 55, 
            hover_name='DESC',
            color = 'GROUP',
            log_y=True,
            log_x=True,
            animation_frame='MONTH_NAME',
            category_orders={'MONTH_NAME': month_order},
            animation_group='LOYAL_CODE',
            color_discrete_sequence=px.colors.qualitative.Vivid,
    )
    fig.update_traces(
        marker=dict(
            line=dict(width=1, color='white'),
            opacity=0.8
        )
    )



    # Animation Smoothness 
    fig.update_layout(
        updatemenus=[{
            "buttons": [
                {
                    "args": [None, {"frame": {"duration": 1000, "redraw": False},
                                    "fromcurrent": True, 
                                    "transition": {"duration": 600, "easing": "quadratic-in-out"}}],
                    "label": "Play",
                    "method": "animate"
                },
                {
                    "args": [[None], {"frame": {"duration": 0, "redraw": False},
                                    "mode": "immediate",
                                    "transition": {"duration": 0}}],
                    "label": "Pause",
                    "method": "animate"
                }
            ],
            "direction": "left",
            "pad": {"r": 10, "t": 87},
            "showactive": False,
            "type": "buttons",
            "x": 0.1,
            "xanchor": "right",
            "y": 0,
            "yanchor": "top"
        }],
        height = 600,

        coloraxis_showscale=False,
        margin=dict(r=100), 
        title=dict(
            text=f'<b> Сарын Гүйлгээний Онооны Тархац </b>',
            xanchor='center',
            x = 0.5,
            #font=dict(size=24)
        ),
        xaxis=dict(
            title_text="<b>Нийт давтагдаагүй хэрэглэгчдийн тоо (Log Scale)</b>",
            title_font=dict(size=18),
            tickfont=dict(size=14)
        ),
        yaxis=dict(
            title_text="<b>Нийт цуглуулсан оноо (Log scale)</b>",
            title_font=dict(size=18),
            tickfont=dict(size=14)
        )
    )
    
    fig.add_annotation(
        text= 'Гүйлгээний давтамжийн тоог дүрсийн хэмжээгээр илэрхийлэв',
        showarrow=False,
        x=math.log10(10000),
        y=math.log10(1500),
        font=dict(
            size=15,
            color="grey"
        )
    )
    st.plotly_chart(fig, use_container_width=True)

        
    #st.dataframe(transaction_summary)
    with st.expander(expanded=True, label = 'Тайлбар:'):
        col1, col2 = st.columns([0.4,0.6])  
        with col1:
            st.subheader('Графикыг тайлбар:')
            st.markdown("""
                - **X axis (log)** – Хэрэглэгчийн тоо 
                - **Y axis (log)** – Нийт мөнгөн дүн 
                - **Bubble хэмжээ** – Гүйлгээний давтамж
                - **Өнгө** – Урамшууллын бүлэг 
                - **Animation** – Сарын өөрчлөлт 
                        
                | Харагдац | Утга |
                |---------|------|
                | Баруун дээд, том bubble | Үндсэн орлогын эх үүсвэр |
                | Дээд, зүүн хэсэг | Өндөр дүн, цөөн хэрэглэгч |
                | Дунд бүс | Оролцоо нэмэгч урамшууллууд |
                | Түр гарч ирэх | Кампанит ажил |
            """) 
        
        with col2:
            st.subheader("Ерөнхий тойм")
            
            st.markdown(f"""
                - 2025 оны **1–12** дугаар саруудад нийт **{df['LOYAL_CODE'].nunique()}** төрлийн урамшуулал олгогдсон байна.
                - 4-р сард **54** төрлийн урамшуулал олгогдсон нь хамгийн олон төрлийн урамшуулал олгосон сар болсон байна.
                - Графикийн баруун дээд хэсэгт дараах урамшууллууд тогтвортой байрлаж байна:
                    -   **1к эрхийн гүйлгээний**
                    -   **Тэтгэврийн хуримтлал цэнэглэлтийн**
                    -   **Хугацаатай хадгаламж / Итгэлцэл нээсэн**
                    -   Эдгээр нь олон хэрэглэгчтэй, нийт дүн өндөр, давтамж өндөр урамшууллуудыг илтгэнэ.
                -   2025 оны 6-р сард **1к эрхийн гүйлгээний** урамшуулалд хамгийн их оноо тараагдсан **(1,283,002)** мөн хамгийн олон оролцогчид оролцсон **(16,022)** байна.  
            """)
            st.caption('Үндсэн, тогтмол орлого бүрдүүлэгч урамшуулал гэж дүгнэж болно.')

        st.divider()

        movers_df = movers_df.sort_values(['DESC', 'MONTH_NUM']) 


        fig = px.scatter(
            movers_df,
            x='Total_Users', 
            y='Total_Amount', 
            size='Transaction_Freq',
            color='DESC',
            size_max=30, 
            hover_name='LOYAL_CODE',
            hover_data=['MONTH_NAME'],
            
        )
        fig.update_traces(marker=dict(sizemode='area'))


        # 3. Add arrows for each group (DESC)
        for desc in movers_df['DESC'].unique():
            df_sub = movers_df[movers_df['DESC'] == desc]
            n = len(df_sub) - 1

            for i in range(n):
                alpha = 0.05 + (0.8 * (i / n))

                fig.add_annotation(
                    x=df_sub.iloc[i+1]['Total_Users'],  # Arrow head x
                    y=df_sub.iloc[i+1]['Total_Amount'], # Arrow head y
                    ax=df_sub.iloc[i]['Total_Users'],   # Arrow tail x
                    ay=df_sub.iloc[i]['Total_Amount'],  # Arrow tail y
                    xref="x", yref="y",
                    axref="x", ayref="y",
                    showarrow=True,
                    arrowhead=1,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor=f"rgba(34,139,34 {alpha})"
                )

        st.subheader('Ажиглалтууд: Өндөр өсөлттэй урамшууллууд')
        st.plotly_chart(fig,use_container_width=True)

        col1,col2 = st.columns(2)
        with col1:
            st.markdown(f"""
                ##### Картын гүйлгээний урамшуулал:
                - 2025 оны эхэнд зүүн доор байрлалтай байсан бол тогтвортойгоор баруун дээд булан руу өгсөж байгаа нь 
                нийт урамшууллын дүн **(2,094 - 164,912)** болон нийт оролцогчдын тоо **(262 - 1,204)** ихэссэн байгааг 
                илтгэж байна. 
                - Ингэснээр 2025 оны хамгийн өндөр өсөлттэй **(1-р сараас хойш 70.7 дахин өсөлттэй, сарын дундаж өсөлт 70%)** урамшуулал болсон байна.      
            """)

        with col2:
            st.markdown("""
                ##### Хэрэглэгчийн өсөлт:
                - Хамгийн өндөр өсөлттэй урамшууллуудаас харахад **4-р сард** хэрэглэгчийн тоо хамгийн өндөр байна. 
                - **4-р сард лотто** авсан хэрэглэгчдийн тоо бусад бүх саруудаасаа **44% - 82%** аар илүү байна.
            """)
        
        st.divider()

        st.markdown(f"""
            ##### Гүйлгээний Урамшуулал:  
            - 2025 оны бүх сард хамгийн өндөр урамшууллын оноо тараагдсан мөн хамгийн олон оролцогчид оролцсон төрөл.
            - 2025 онд нийт **{df[df['CODE_GROUP'] == 'Financial Transactions']['CUST_CODE'].nunique():,}** хэрэглэгчид урамшуулал авж **{df[df['CODE_GROUP'] == 'Financial Transactions']['TXN_AMOUNT'].sum():,.0f}** оноо тараагдсан.
        """)




    with st.expander(expanded=False, label = 'Хүснэгт харах:'):
        #st.dataframe(movers_df, use_container_width=True)
        st.dataframe(transaction_summary, use_container_width=True)
        #st.text(transaction_summary.GROUP.unique())
        #transaction_summary.to_clipboard()


with tab3:
  
    line_chart_df = grouped_reward.groupby(['CODE_GROUP','MONTH_NUM'])['TOTAL_AMOUNT'].sum().reset_index()
    line_chart_df = line_chart_df.sort_values('MONTH_NUM')

    line_chart_fig = px.line(line_chart_df, 
            x = 'MONTH_NUM', 
            y = 'TOTAL_AMOUNT', 
            #log_y= True,
            color = 'CODE_GROUP',
            markers=True,
            title='Урамшууллын Бүлгийн Чиг Хандлага Сараар',
            labels={'MONTH_NUM': 'Сар', 'TOTAL_AMOUNT': 'Нийт Оноо'}
    )
    line_chart_fig.update_layout(xaxis=dict(tickmode='linear'), 
        title=dict(
            xanchor = 'center',
            x = 0.5
        ),    
        #hovermode= 'x unified' 
    )
    line_chart_fig.update_traces(
        mode="lines+markers",
        hovertemplate="<b>%{fullData.name}</b><br>Month: %{x}<br>Total: %{y:,.0f}<extra></extra>"
    )

    line_chart_fig.add_vline(x=4, 
              line_dash="dash", 
              line_color="red",
              line_width = 2, 
              annotation_text="Inverstor Week",
              opacity=0.3
    )
    
    st.plotly_chart(line_chart_fig, use_container_width=True)
    st.subheader('2025 ОНЫ ХЭРЭГЛЭГЧДИЙН ГҮЙЛГЭЭНИЙ ТӨРЛИЙН ШИНЖИЛГЭЭ')

    with st.expander(expanded=True, label= 'Тайлбар:'):

        st.markdown("""
            #### Бүлэглэсэн гүйлгээний шинжилгээ
            -   Сар бүр **"Гүйлгээний Урамшуулал"** нь хамгийн өндөр хувийг эзэлсэн байна
                -   8-р сард нийт олгогдсон урамшууллын онооны **92.5%-ыг** эзэлсэн нь хамгийн өндөр хувь эзэлсэн сар болсон. 
                -   Харин эсрэгээрээ 4-р сард нийт олгогдсон урамшууллын онооны **49.3%-ыг** эзэлсэн нь энэ бүлгийн хамгийн бага хувь эзэлсэн сар болсон байна
            -   4,5 -р сар хамгийн олон урамшууллын  бүлгүүд ашиглагдсан сар байсан буюу урамшууллын 8 ангиллаас **7** нь ашиглагдсан байна
            -   **"Орон Нутгийн"** урамшууллын гүйлгээ зөвхөн 6-р сард олгогдсон ч тухайн сарын нийт онооны **6.2%** ийг эзэлсэн нь орон нутаг руу чиглэсэн кампанит ажлууд амжилттай байсныг илтгэж байна     
            -   **Мерчантын** урамшууллын оноо эхний 5 сар **240,000-аас 270,000** хооронд байсан бол 8 сар хүртэл тогтмол унасаар **170,000** болсон байна
            -   **Данс Нээсний** урамшууллын оноо мөн адил эхний 5 сар өсөлттэй байсан ч 6,7-р сард унаснаар **5,000** хүрэн үүнээс хойш данс нээсний урамшуулал олгогдоогүй байна                 
            -   **Даатгалын** урамшуулал 4-р сард хамгийн өндөр үзүүлэлттэй байсан буюу тухайн сарын бүх онооны **13.9%** ийг эзэлж, нийт оноо нь өмнө сараас **34%** өссөн байна
                -   Үүнээс хойш тогтмол унасаар **Данс Нээсний** урамшуулалтай адил 7-р сар хүрээд дахиж оноо тараагдаагүй байна     
        """)
        
    with st.expander('Сар тус бүрээр харах:', expanded=False):
        available_months = grouped_reward['MONTH_NAME'].unique()
        final_options = [m for m in month_order if m in available_months]
        selected_month = st.selectbox(
            'Choose a month to analyze',
            options=final_options,
        )
        monthly_grouped_reward = grouped_reward[grouped_reward['MONTH_NAME'] == selected_month]

        fig = donut_plot(
            monthly_grouped_reward, 
            'CODE_GROUP', 
            'TOTAL_AMOUNT',
            f'Percentage of Total Points by Transaction Group in {selected_month}'
        )

        st.plotly_chart(fig, use_container_width=True)


    
    with st.expander("Хүснэгт харах:", expanded=False):
        st.dataframe(monthly_grouped_reward, use_container_width=True)


with tab4:

    transaction_summary_year = transaction_summary.groupby('LOYAL_CODE')['Total_Amount'].sum().reset_index()
    top5_transaction = transaction_summary_year.nlargest(5,columns='Total_Amount')

    other_total = transaction_summary_year['Total_Amount'].sum() - top5_transaction['Total_Amount'].sum()

    other_row = pd.DataFrame({'LOYAL_CODE': ['Бусад'], 'Total_Amount': [other_total]})

    transaction_summary_year_top5 = pd.concat([top5_transaction, other_row], ignore_index=True)        
    transaction_summary_year_top5['DESC'] = transaction_summary_year_top5['LOYAL_CODE'].map(loyal_code_to_desc)
    transaction_summary_year_top5['DESC'] = transaction_summary_year_top5['DESC'].fillna('Бусад')
    fig = donut_plot(
        transaction_summary_year_top5,
        labels_col='DESC' ,
        values_col='Total_Amount',
        title_text=f'Урамшууллын Эзлэх Хувь Жилийн Дунджаар (Топ 5 болон бусад)'
    )
    fig.update_traces(
        customdata = transaction_summary_year_top5[['DESC']],
        hovertemplate="<b>%{label}</b><br>Description: %{customdata[0]}<br>Amount: %{value}<br>Percent: %{percent}" 
    )
    fig.update_layout(
        title = dict(
            font=dict(size=15),
            x=0.3,
            y=0.9
        )
    ) 

    st.plotly_chart(fig, use_container_width=True)

    transaction_bar_plot_df = df.groupby('LOYAL_CODE').agg({
        'TXN_AMOUNT': 'sum',
        'JRNO': 'count'
    })
    transaction_bar_plot_df['AVG'] = (transaction_bar_plot_df['TXN_AMOUNT'] / transaction_bar_plot_df['JRNO']).round(2)
    transaction_bar_plot_df['PERCENTAGE'] =(( transaction_bar_plot_df['TXN_AMOUNT']/transaction_bar_plot_df['TXN_AMOUNT'].sum() )* 100).round(2)
    transaction_bar_plot_df = transaction_bar_plot_df[transaction_bar_plot_df['PERCENTAGE']>2].reset_index()
    transaction_bar_plot_df = transaction_bar_plot_df.sort_values(by='AVG')
    transaction_bar_plot_df['DESC'] = transaction_bar_plot_df['LOYAL_CODE'].map(loyal_code_to_desc)


    fig = px.bar(
        transaction_bar_plot_df,
        x='AVG',
        y='DESC',
        color = 'AVG',
        text = 'AVG',
        labels= {
            'DESC': 'ГҮЙЛГЭЭНИЙ НЭР',
            'AVG': 'ДУНДАЖ ОНОО',
            'PERCENTAGE': 'Эзлэх Хувь'
        }
    )

    fig.update_layout(
        title=dict(
            text = 'Нэгж гүйлгээний дундаж урамшууллын оноо',
            xanchor = 'center',
            x = 0.5
        ),
    )
    fig.update_traces(textposition='outside')

    with st.expander(expanded=False, label='Тайлбар:'):
        st.markdown(f"""
            #### Гүйлгээний шинжилгээ
            -	2025 онд **Топ 5** гүйлгээний төрөл нийлээд **65.3%** буюу нийт онооны талаас их хувийг бүрдүүлж байна.
            -	Бүх гүйлгээний төрлүүдийн **10%** (9/84) нь нийт онооны **80%** ийг бүрдүүлж байна.
                    
            #### 1к эрхийн гүйлгээний урамшуулал:  
            - 2025 оны бүх сард хамгийн өндөр урамшууллын оноо тараагдсан мөн хамгийн олон оролцогчид оролцсон төрөл.
            - 2025 онд нийт **{df[df['LOYAL_CODE'] == '10K_TRANSACTION']['CUST_CODE'].nunique():,}** хэрэглэгчдэд **{df[df['LOYAL_CODE'] == '10K_TRANSACTION']['TXN_AMOUNT'].sum():,.0f}** оноо тараагдсан.
        """)
    
    st.divider()

    st.subheader("Нэгж гүйлгээний дундаж урамшууллын онооны шинжилгээ")
    st.plotly_chart(fig)
    st.caption('Нийт оноонд 1% аас илүү хувь нэмэр оруулсан гүйлгээнүүдийг жагсаав.')
     
    with st.expander(expanded=False, label='Тайлбар:'):


        st.markdown("""
        ### Графикийн тайлбар
        -   Гүйлгээний төрлүүдийг **нэг гүйлгээнд ногдох дундаж урамшууллын оноогоор** харьцуулсан  
        -   **Багана:** Дундаж онооны хэмжээ
        -   **Баганан дээрх хувь:** Гүйлгээний нийт оноонд эзлэх хувь
        """)

        st.markdown("""
        ### Гол ажиглалтууд
        - **Даатгал, хадгаламж, тэтгэврийн хуримтлал** зэрэг гүйлгээнүүд:
        - Нэг удаад **өндөр оноо** олгодог
            - Нийт оноонд эзлэх хувь **харьцангуй бага**
        - **Ердийн гүйлгээ**:
            - Дундаж оноо **бага** харин нийт оноонд эзлэх хувь **хамгийн өндөр**
        """)

        st.markdown("""
        ### Зан төлөвийн ялгаа
        - **Дундаж оноо өндөр + эзлэх хувь бага**  
            -   Өндөр үнэ цэнтэй, ховор хийгддэг гүйлгээ  
        - **Дундаж оноо бага + эзлэх хувь өндөр**  
            -  Өдөр тутмын, олон давтамжтай гүйлгээ
        """)

    with st.expander(expanded=False, label=('Хүснэгт харах:')):
        st.dataframe(transaction_summary_year,use_container_width=True)