import os
from datetime import date, timedelta

import pandas as pd
import psycopg2
import pydeck as pdk
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Emergencias Bomberos Peru", layout="wide")


def get_database_url():
    try:
        return st.secrets["DATABASE_URL"]
    except Exception:
        return os.environ["DATABASE_URL"]


@st.cache_resource
def get_connection():
    return psycopg2.connect(get_database_url())


def run_query(sql, params=None):
    return pd.read_sql(sql, get_connection(), params=params)


st.title("Emergencias - Cuerpo General de Bomberos del Peru")

rango = run_query("select min(fecha_hora) as min_fecha, max(fecha_hora) as max_fecha from reports")
fecha_min = rango["min_fecha"][0].date() if pd.notna(rango["min_fecha"][0]) else date.today() - timedelta(days=30)
fecha_max = rango["max_fecha"][0].date() if pd.notna(rango["max_fecha"][0]) else date.today()

col1, col2 = st.columns(2)
with col1:
    desde = st.date_input("Desde", value=fecha_min, min_value=fecha_min, max_value=fecha_max)
with col2:
    hasta = st.date_input("Hasta", value=fecha_max, min_value=fecha_min, max_value=fecha_max)

reports = run_query(
    """
    select nro_parte, fecha_hora, direccion, lat, lon, tipo, estado, unidades
    from reports
    where fecha_hora::date between %(desde)s and %(hasta)s
    order by fecha_hora desc
    """,
    {"desde": desde, "hasta": hasta},
)

st.metric("Emergencias en el rango seleccionado", len(reports))

exploded = reports.explode("unidades").rename(columns={"unidades": "unidad"}).dropna(subset=["unidad"])
exploded["cia_num"] = exploded["unidad"].str.extract(r"(\d+)")

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Companias con mas salidas")
    cia_rank = (
        exploded.dropna(subset=["cia_num"])
        .groupby("cia_num")["nro_parte"]
        .nunique()
        .sort_values(ascending=False)
        .head(15)
    )
    cia_rank.index = "Cia " + cia_rank.index
    st.bar_chart(cia_rank)

with col_b:
    st.subheader("Unidades mas operativas")
    unidad_rank = (
        exploded.groupby("unidad")["nro_parte"]
        .nunique()
        .sort_values(ascending=False)
        .head(15)
    )
    st.bar_chart(unidad_rank)

st.subheader("Mapa de calor de emergencias")
mapa_df = reports.dropna(subset=["lat", "lon"])
if not mapa_df.empty:
    layer = pdk.Layer(
        "HeatmapLayer",
        data=mapa_df,
        get_position="[lon, lat]",
        aggregation="MEAN",
    )
    view_state = pdk.ViewState(latitude=mapa_df["lat"].mean(), longitude=mapa_df["lon"].mean(), zoom=9)
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))
else:
    st.info("No hay coordenadas registradas en el rango seleccionado.")

st.subheader("Detalle de emergencias")
st.dataframe(reports, use_container_width=True)
