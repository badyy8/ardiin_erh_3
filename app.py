import streamlit as st

st.set_page_config(page_title="Ардын Эрх Онооны Тайлан", layout="wide")

pages = {
    "Эхлэл": [
        st.Page("home.py", title="ДАТАСЕТ ТОВЧ ТАЙЛАН"),
    ],
    "2025 он": [
        st.Page("page1.py", title="ХЭРЭГЛЭГЧДИЙН ОНООНЫ ТАРХАЦ"),
        st.Page("page2.py", title="УРАМШУУЛАЛЫН ТӨРӨЛ"),
        st.Page("page3.py", title="ОНЦЛОХ САР"),
        st.Page("page4.py", title="ХЭРЭГЛЭГЧДИЙН СЕГМЭНТЧЛЭЛ"),
        st.Page("page5.py", title="НЭМЭЛТ"),
    ],
}

pg = st.navigation(pages)
pg.run()