import streamlit as st
import pandas as pd
from data_loader import load_data, get_lookup
import time

df = load_data()

st.title('АРДЫН ЭРХ ОНООНЫ ДАТАСЕТ ТОВЧ ТАЙЛАН')
st.caption('Descriptive Analysis Report (2024.01.01 – 2025.12.31)')

# 1. Executive Summary
st.markdown("""
    ### Товч хураангуй 
    Энэхүү тайлан нь хэрэглэгчдийн хийсэн гүйлгээнээс авсан шагналын онооны түвшин, гүйлгээний төрөл, давтамж, сегментчилэл болон ерөнхий зан төлөвийг тодорхойлох зорилготой

    **Гол олдворууд:**
    * **Хэрэглэгчдийн олонх:** 1,000 оноонд хүрэхгүй байна
    * **Төвлөрөл:** Онооны тархалт нь цөөн гүйлгээний төрлүүдэд төвлөрсөн
    * **Чухал сар:** 4 болон 5-р сар бүх үзүүлэлтээр давамгайлсан сар болсон нь **Inverstor Week** -тэй холбоотой 
    ---
    """)

# 2. Dataset Overview
with st.expander('Датасетийн ерөнхий мэдээлэл', expanded=True):
    
    st.subheader('Датасетийн бүтэц')
    col1, col2, col3 = st.columns(3)
    col1.metric(f"Нийт мөрийн тоо", f"{len(df):,}")
    col2.metric("Баганы тоо", "9")
    col3.metric("Эх сурвалж", "Системийн лог")

    # Багануудын тайлбар
    var_data = {
        "Баганын нэр": ["TXN_DATE", "TXN_DESC", "JRNO", "TXN_AMOUNT", "CUST_CODE", "USER_ID", "NAME", "LOYAL_CODE", "OPER_CODE", ],
        "Тайлбар": ["Гүйлгээний өдөр", "Гүйлгээний тайлбар", "Гүйлгээний дугаар", "Гүйлгээний дүн (авсан оноо)", "Хэрэглэгчийн код", "Системийн дугаар", "Хэрэглэгчийн нэр", "Гүйлгээний код", "Төлбөрийн сонголт код",]
    }
    
    st.dataframe(pd.DataFrame(var_data),hide_index=True,width='stretch')

    st.markdown("---")
    
    # 2.2.2 Variable Analysis
    st.subheader('Нарийвчилсан задлан шинжилгээ')
    
    analysis_col1, analysis_col2 = st.columns(2)
    
    with analysis_col1:
        st.info("**TXN_AMOUNT (Нэгж Гүйлгээний Оноо)**")
        st.write(f"* **Дундаж оноо:** {df['TXN_AMOUNT'].mean():.1f}")
        st.write(f"* **70-р перцентиль:** {df['TXN_AMOUNT'].quantile(0.7)}")
        st.write(f"* **Хамгийн их:** {df['TXN_AMOUNT'].max()}")
        st.write(f"* **Хамгийн олон давтагдсан:** {df['TXN_AMOUNT'].mode()[0]}")
        
        st.info("**LOYAL_CODE**")
        st.write(f"* **Өвөрмөц код:** {df.LOYAL_CODE.nunique()}")
        st.write(f"* **Түгээмэл:** {len(df[df['LOYAL_CODE'] == '10K_TRANSACTION']):,} (10K_TRANSACTION)")

    with analysis_col2:
        st.info("**CUST_CODE & DATE**")
        st.write(f"* **Нийт өвөрмөц хэрэглэгч:** {df.CUST_CODE.nunique():,} хэрэглэгч")
        st.write(f"* **Хугацаа:** 2024.01.01 – 2025.12.31")
    


# available_years = sorted(df["year"].unique())
# selected_year = st.sidebar.selectbox("Жил сонгох", available_years, index=len(available_years)-1)

# with st.spinner("Preparing Data"):
#     start = time.perf_counter()
#     warm_year_cache(df, loyal, selected_year)
#     end = time.perf_counter()

# st.success(f"Data Ready took {end - start:.2f} seconds")


