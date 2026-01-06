import streamlit as st
import pandas as pd

@st.cache_data(show_spinner=True)
def get_df():
    df = pd.read_parquet(
        "ardiin_erh_code_grouped.pqt"
    )
    return df


def load_data():
    df = get_df()

    df = df.loc[df["TXN_DATE"] >= "2025-01-01"].copy()

    return df



def get_lookup():

    lookup_df = pd.read_csv("loyalty_lookup_2.csv")
    loyal_code_to_desc = dict(
        zip(lookup_df["LOYAL_CODE"], lookup_df["TXN_DESC"].str.capitalize())
    )
    return loyal_code_to_desc