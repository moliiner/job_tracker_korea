import streamlit as st
import pandas as pd

st.title("JOB TRACKER - Seoul")
df = pd.read_csv("data/processed/processed_offers.csv")

col1, col2, col3 = st.columns(3)

col1.metric("Tracked offers", len(df))
col2.metric("Mentions visa", f"{df['mentions_visa'].mean()*100:.0F}%")
col3.metric("Unique companies", df["company"].nunique())

st.bar_chart(df["technologies"].explode().value_counts())
st.dataframe(df)