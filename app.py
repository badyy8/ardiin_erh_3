import streamlit as st


st.set_page_config(page_title="Ардын Эрх Онооны Тайлан", layout="wide")

try:
    st.write("✅ Booting app...")
except Exception as e:
    st.error("❌ App crashed while starting.")
    st.exception(e)
    st.stop()

pages = {
    "Эхлэл": [
        st.Page("home.py", title="ДАТАСЕТ ТОВЧ ТАЙЛАН"),
    ],
    "Анализ": [
        st.Page("page1.py", title="ХЭРЭГЛЭГЧДИЙН ОНООНЫ ТАРХАЦ"),
        st.Page("page2.py", title="УРАМШУУЛАЛЫН ТӨРӨЛ"),
        st.Page("page4.py", title="ХЭРЭГЛЭГЧДИЙН СЕГМЭНТЧЛЭЛ"),
        st.Page("page3.py", title="ОНЦЛОХ САР"),
        st.Page("miscellaneous.py", title="ЕРӨНХИЙ"),
    ],
    "Санал": [
        st.Page("page5.py", title="RDX ХӨНГӨЛӨЛТИЙН САНАЛ"),
    ],
}

pg = st.navigation(pages)
pg.run()
