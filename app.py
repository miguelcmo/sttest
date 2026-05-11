import streamlit as st
import pandas as pd
from influxdb_client import InfluxDBClient
import plotly.express as px

# =========================
# CONFIGURACIÓN INFLUXDB
# =========================

URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
TOKEN = "EJwrNIOrygCc52EJm-H0NVuHwUapDRTUdEiJ4rCwz3H_cwi_APdfpViMMc9bmzfzcfg9dub8uibJw0fpekAIVQ=="
ORG = "miguelcmo"
BUCKET = "iot_telemetry_data"

# =========================
# STREAMLIT PAGE
# =========================

st.set_page_config(
    page_title="IoT Dashboard",
    layout="wide"
)

st.title("📡 IoT Telemetry Dashboard")

# =========================
# CONEXIÓN
# =========================

client = InfluxDBClient(
    url=URL,
    token=TOKEN,
    org=ORG
)

query_api = client.query_api()

# =========================
# QUERY FLUX
# =========================

query = f'''
from(bucket: "{BUCKET}")
  |> range(start: -1h)
'''

# =========================
# CONSULTAR DATOS
# =========================

try:
    tables = query_api.query_data_frame(query)

    if isinstance(tables, list):
        df = pd.concat(tables)
    else:
        df = tables

    if df.empty:
        st.warning("No hay datos disponibles.")
    else:

        # LIMPIEZA
        columns_to_remove = [
            "result",
            "table",
            "_start",
            "_stop"
        ]

        for col in columns_to_remove:
            if col in df.columns:
                df = df.drop(columns=[col])

        st.subheader("Datos Recientes")

        st.dataframe(df, use_container_width=True)

        # =========================
        # GRÁFICAS
        # =========================

        if "_time" in df.columns and "_value" in df.columns:

            fig = px.line(
                df,
                x="_time",
                y="_value",
                color="_field" if "_field" in df.columns else None,
                title="Telemetría en Tiempo Real"
            )

            st.plotly_chart(fig, use_container_width=True)

        # =========================
        # MÉTRICAS
        # =========================

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Total Registros",
                len(df)
            )

        if "_measurement" in df.columns:
            with col2:
                st.metric(
                    "Measurements",
                    df["_measurement"].nunique()
                )

        if "_field" in df.columns:
            with col3:
                st.metric(
                    "Fields",
                    df["_field"].nunique()
                )

except Exception as e:
    st.error(f"Error conectando a InfluxDB: {e}")
