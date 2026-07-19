import streamlit as st
import pandas as pd
import re

st.set_page_config(layout="wide")
st.title("JOB TRACKER — Seoul")

df = pd.read_csv("data/processed/processed_offers.csv")

# publication_date puede no estar disponible según lo que devuelva Jooble;
# lo tratamos como opcional en vez de asumir que siempre existe
if "publication_date" in df.columns:
    df["publication_date"] = pd.to_datetime(df["publication_date"], errors="coerce")

def clean_technologies(value):
    """
    'technologies_found' llega del LLM como lista de Python, pero al pasar
    por CSV se guarda como texto tipo "['Python', 'SQL']" — esta función
    limpia ese formato para poder explotarla en el gráfico.
    """
    if pd.isna(value):
        return []
    limpio = re.sub(r"[\[\]']", "", str(value))
    return [t.strip() for t in limpio.split(",") if t.strip()]

technologies_per_offer = df["technologies_found"].apply(clean_technologies)

# --- KPIs superiores, siempre visibles ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Tracked offers", len(df))
col2.metric("Avg. visa likelihood", f"{df['visa_sponsorship_likelihood'].mean():.0f}%")
col3.metric("Unique companies", df["company"].nunique())
if "publication_date" in df.columns and df["publication_date"].notna().any():
    col4.metric("Last update", df["publication_date"].max().strftime("%d/%m/%Y"))
else:
    col4.metric("Last update", "N/D")

tab1, tab2, tab3, tab4 = st.tabs(["Technologies", "Trends", "Location and salary", "Filterable table"])

with tab1:
    st.subheader("Most used technologies")
    st.bar_chart(technologies_per_offer.explode().value_counts())

    st.subheader("Technologies most associated with high visa-likelihood offers")
    # Ya no existe un booleano "mentions_visa"; usamos un umbral sobre
    # la probabilidad estimada por el LLM (0-100) como proxy de "positivo"
    df_high_visa = df[df["visa_sponsorship_likelihood"] >= 50]
    tech_visa = df_high_visa["technologies_found"].apply(clean_technologies).explode().value_counts()
    st.bar_chart(tech_visa)

with tab2:
    if "publication_date" in df.columns:
        st.subheader("Tracked offers by week")
        offers_per_week = df.set_index("publication_date").resample("W").size()
        st.line_chart(offers_per_week)

    st.subheader("Avg. visa likelihood by source")
    if "source" in df.columns:
        visa_per_source = df.groupby("source")["visa_sponsorship_likelihood"].mean()
        st.bar_chart(visa_per_source)

with tab3:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Tracked offers by district")
        if "location" in df.columns:
            st.bar_chart(df["location"].value_counts())
    with col_b:
        st.subheader("Salary distribution (yearly KRW)")
        if "min_salary/max_salary" in df.columns:
            separated_salaries = df["min_salary/max_salary"].str.split("/", expand=True)
            separated_salaries.columns = ["min_salary", "max_salary"]
            separated_salaries["min_salary"] = pd.to_numeric(separated_salaries["min_salary"], errors="coerce")
            separated_salaries["max_salary"] = pd.to_numeric(separated_salaries["max_salary"], errors="coerce")
            st.bar_chart(separated_salaries[["min_salary", "max_salary"]].mean())

with tab4:
    st.subheader("Explore the tracked offers, ranked by match score")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        role_filter = st.multiselect(
            "Role category",
            df["role_category"].dropna().unique() if "role_category" in df.columns else []
        )
    with col_f2:
        min_visa_likelihood = st.slider("Minimum visa likelihood (%)", 0, 100, 0)

    df_filtered = df.sort_values("match_score", ascending=False).copy()
    if role_filter:
        df_filtered = df_filtered[df_filtered["role_category"].isin(role_filter)]
    df_filtered = df_filtered[df_filtered["visa_sponsorship_likelihood"] >= min_visa_likelihood]

    st.dataframe(df_filtered, use_container_width=True)