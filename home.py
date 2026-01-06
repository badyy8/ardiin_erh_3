import streamlit as st
import pandas as pd
from data_loader import load_data, get_df

df = load_data()

st.title('АРДЫН ЭРХ ОНООНЫ ДАТАСЕТ ТОВЧ ТАЙЛАН')
st.caption('Descriptive Analysis Report (2025.01.01 – 2025.12.23)')

# 1. Executive Summary
st.markdown("""
### Товч хураангуй 
Энэхүү тайлан нь хэрэглэгчдийн хийсэн гүйлгээнээс авсан шагналын онооны түвшин, гүйлгээний төрөл, давтамж, сегментчилэл болон ерөнхий зан төлөвийг тодорхойлох зорилготой

**Гол олдворууд:**
* **Хэрэглэгчдийн олонх:** 1,000 оноонд хүрэхгүй байна
* **Төвлөрөл:** Онооны тархалт нь цөөн гүйлгээний төрлүүдэд төвлөрөх хандлагатай
* **Чухал сар:** 4 болон 5-р сар бүх үзүүлэлтээр давамгайлсан сар болсон нь **Inverstor Week** -тэй холбоотой 
---
""")

# 2. Dataset Overview
with st.expander('Датасетийн ерөнхий мэдээлэл', expanded=True):
    
    st.subheader('Датасетийн бүтэц')
    col1, col2, col3 = st.columns(3)
    col1.metric(f"Нийт мөрийн тоо", "4,906,931")
    col2.metric("Баганы тоо", "9")
    col3.metric("Эх сурвалж", "Системийн лог")

    # Багануудын тайлбар
    var_data = {
        "Баганын нэр": ["TXN_DATE", "TXN_DESC", "JRNO", "TXN_AMOUNT", "CUST_CODE", "USER_ID", "NAME", "LOYAL_CODE", "OPER_CODE", ],
        "Тайлбар": ["Гүйлгээний өдөр", "Гүйлгээний тайлбар", "Гүйлгээний дугаар", "Гүйлгээний дүн (авсан оноо)", "Хэрэглэгчийн код", "Системийн дугаар", "Хэрэглэгчийн нэр", "Гүйлгээний код", "Төлбөрийн сонголт код",]
    }
    
    st.dataframe(pd.DataFrame(var_data),hide_index=True, use_container_width=True )

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
        st.write(f"* **Түгээмэл:** 10K_TRANSACTION (3,127,373)")

    with analysis_col2:
        st.info("**CUST_CODE & DATE**")
        st.write(f"* **Нийт өвөрмөц хэрэглэгч:** {df.CUST_CODE.nunique():,} хэрэглэгч")
        st.write(f"* **Хугацаа:** 2024.01.01 – 2025.12.23")
        
        st.info("**OPER_CODE**")
        st.write(f"* **Нийт өвөрмөц төлбөрийн сонголт:** {df['OPER_CODE'].nunique()} төрөл")
        #st.write(f"* **Түгээмэл төлбөрийн сонголт :** {df['OPER_CODE'].value_counts().idxmax()}")

# Дата чанарын хэсэг
# 3. Data Quality
with st.expander('3. Өгөгдлийн чанарын үнэлгээ', expanded=False):
    st.warning("Датасет дээр хийгдсэн цэвэрлэгээ")
    st.markdown("""
    * **TXN_DESC:** Зарим тайлбарын багана давхардсан болон стандарт бус тексттэй байсныг зассан.
    * **Cleaning:** Зарим утгуудыг системд оруулахад бэлтгэж цэвэрлэсэн.
    * **Missing Values:** **77,004** мөр `LOYAL_CODE`-гүй байсан.
    * **Anomaly:** 
        -   Даатгал болон Данс нээгдсний гүйлгээний оноо **7-р сарын 2** ноос хойш байхгүй болсон.
        -   **3** гүйлгээ бутархай дүнтэй байсан.
    """)

# Sidebar нэмэлт мэдээлэл
# st.sidebar.title("Шүүлтүүр")
# st.sidebar.info("Энэ хэсэгт датаг шүүх тохиргоонуудыг нэмж болно.")