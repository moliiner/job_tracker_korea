import sys

import streamlit as st
import pandas as pd
import re
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "model"))
from match_score import calculate_match_score, clean_technologies

st.set_page_config(layout="wide")
st.title("JOB TRACKER — Seoul")

df = pd.read_csv("data/processed/processed_offers.csv")
df["publication_date"] = pd.to_datetime(df["publication_date"], errors="coerce")


TECHNOLOGIES = ["Python", "SQL", "Tableau", "AWS"]
PREFERRED_ROLE = "analyst"
PREFERRED_DISTRICTS = ["Gangnam", "Pangyo", "Seongsu"]
MINIMUM_ACCEPTABLE_SALARY = 30000000  # 30 million KRW

df["match_score"] = df.apply(
    lambda row: calculate_match_score(
        row, TECHNOLOGIES, PREFERRED_ROLE, PREFERRED_DISTRICTS, MINIMUM_ACCEPTABLE_SALARY
    ),
    axis=1
)

def clean_technologies(value):
    if pd.isna(value):
        return []
    limpio = re.sub(r"[\[\]']", "", str(value))
    return [t.strip() for t in limpio.split(",") if t.strip()]

technologies_per_offer = df["technologies"].apply(clean_technologies)

# --- upper KPIs, always visible ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Tracked offers", len(df))
col2.metric("Mentions visa", f"{df['mentions_visa'].mean()*100:.0f}%")
col3.metric("Unique companies", df["company"].nunique())
col4.metric("Last update", df["publication_date"].max().strftime("%d/%m/%Y") if df["publication_date"].notna().any() else "N/D")

tab1, tab2, tab3, tab4 = st.tabs(["Technologies", "Trends", "Location and salary", "Filterable table"])

with tab1:
    st.subheader("Most used technologies")
    st.bar_chart(technologies_per_offer.explode().value_counts())

    st.subheader("Technologies most associated with visa-mentioned offers")
    df_visa = df[df["mentions_visa"] == True]
    tech_visa = df_visa["technologies"].apply(clean_technologies).explode().value_counts()
    st.bar_chart(tech_visa)

with tab2:
    st.subheader("Tracked offers by week")
    offers_per_week = df.set_index("publication_date").resample("W").size()
    st.line_chart(offers_per_week)

    st.subheader("% of offers with visa mention by source")
    if "source" in df.columns:
        visa_per_source = df.groupby("source")["mentions_visa"].mean() * 100
        st.bar_chart(visa_per_source)

with tab3:    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Tracked offers by district")
        if "location" in df.columns:
            st.bar_chart(df["location"].value_counts())
    with col_b:
        st.subheader("Salary distribution (hour KRW)")
        if "min_salary/max_salary" in df.columns:
            # Separamos el texto "40000000-55000000" en dos columnas numéricas
            separated_salaries = df["min_salary/max_salary"].str.split("/", expand=True)
            separated_salaries.columns = ["min_salary", "max_salary"]

            # Convertimos a número; lo que no se pueda convertir queda como NaN
            separated_salaries["min_salary"] = pd.to_numeric(separated_salaries["min_salary"], errors="coerce")
            separated_salaries["max_salary"] = pd.to_numeric(separated_salaries["max_salary"], errors="coerce")

            st.bar_chart(separated_salaries[["min_salary", "max_salary"]].mean())

with tab4:
    st.subheader("Explore the tracked offers")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        role_filter = st.multiselect("Role category", df["role_category"].dropna().unique() if "role_category" in df.columns else [])
    with col_f2:
        visa_filter = st.checkbox("Only offers with visa mention")

    df_filtrado = df.copy()
    if role_filter:
        df_filtrado = df_filtrado[df_filtrado["role_category"].isin(role_filter)]
    if visa_filter:
        df_filtrado = df_filtrado[df_filtrado["mentions_visa"] == True]

    st.dataframe(df_filtrado, use_container_width=True)