import os
from datetime import date, timedelta

import altair as alt
import folium
import pandas as pd
import psycopg2
import streamlit as st
from dotenv import load_dotenv
from folium.plugins import HeatMap
from streamlit_folium import st_folium

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


def bar_chart_ordenado(serie, x_label, y_label, sort="-y", x_type="N"):
    df = serie.reset_index()
    df.columns = [x_label, y_label]
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X(f"{x_label}:{x_type}", sort=sort),
            y=alt.Y(y_label),
            tooltip=[x_label, y_label],
        )
    )
    st.altair_chart(chart, use_container_width=True)


st.subheader("Tendencia diaria")
diaria = reports.groupby(reports["fecha_hora"].dt.date).size().reset_index()
diaria.columns = ["fecha", "emergencias"]
linea = alt.Chart(diaria).mark_line(point=True).encode(
    x=alt.X("fecha:T", axis=alt.Axis(format="%d %b", tickCount="day")),
    y="emergencias:Q",
    tooltip=["fecha", "emergencias"],
)
st.altair_chart(linea, use_container_width=True)

col_h, col_d = st.columns(2)

with col_h:
    st.subheader("Por hora del dia")
    por_hora = (
        reports.groupby(reports["fecha_hora"].dt.hour)
        .size()
        .reindex(range(24), fill_value=0)
    )
    bar_chart_ordenado(por_hora, "hora", "emergencias", sort=list(range(24)), x_type="O")

with col_d:
    st.subheader("Por dia de la semana")
    dias_es = {0: "Lunes", 1: "Martes", 2: "Miercoles", 3: "Jueves", 4: "Viernes", 5: "Sabado", 6: "Domingo"}
    dias_orden = list(dias_es.values())
    por_dia = reports["fecha_hora"].dt.dayofweek.map(dias_es).value_counts().reindex(dias_orden, fill_value=0)
    bar_chart_ordenado(por_dia, "dia", "emergencias", sort=dias_orden)

col_t, col_z = st.columns(2)

with col_t:
    st.subheader("Categoria de emergencia")
    categoria_rank = reports["tipo"].str.split("/").str[0].str.strip().value_counts()
    bar_chart_ordenado(categoria_rank, "categoria", "emergencias")

with col_z:
    st.subheader("Distritos con mas emergencias")
    distrito_rank = reports["direccion"].str.rsplit(" - ", n=1).str[-1].str.strip().value_counts().head(15)
    bar_chart_ordenado(distrito_rank, "distrito", "emergencias")

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
    bar_chart_ordenado(cia_rank, "compania", "salidas")

with col_b:
    st.subheader("Unidades mas operativas")
    unidad_rank = (
        exploded.groupby("unidad")["nro_parte"]
        .nunique()
        .sort_values(ascending=False)
        .head(15)
    )
    bar_chart_ordenado(unidad_rank, "unidad", "salidas")

st.subheader("Mapa de calor de emergencias")
mapa_df = reports.dropna(subset=["lat", "lon"])
if not mapa_df.empty:
    centro = [mapa_df["lat"].mean(), mapa_df["lon"].mean()]
    mapa = folium.Map(location=centro, zoom_start=10, tiles="cartodbpositron")
    HeatMap(mapa_df[["lat", "lon"]].values.tolist()).add_to(mapa)
    st_folium(mapa, height=500, use_container_width=True, returned_objects=[])
else:
    st.info("No hay coordenadas registradas en el rango seleccionado.")

st.subheader("Detalle de emergencias")
st.dataframe(reports, use_container_width=True)
