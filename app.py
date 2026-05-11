# app.py

import streamlit as st
import pandas as pd
import numpy as np
from influxdb_client import InfluxDBClient
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# =========================================================
# CONFIG PAGE
# =========================================================

st.set_page_config(
    page_title="Industrial IoT SCADA",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

html, body, [class*="css"] {
    font-family: 'Segoe UI', sans-serif;
}

.stApp {
    background-color: #0E1117;
    color: white;
}

section[data-testid="stSidebar"] {
    background-color: #161B22;
}

.metric-card {
    background: linear-gradient(145deg,#161B22,#1E2633);
    padding: 20px;
    border-radius: 18px;
    border: 1px solid #2D3748;
    box-shadow: 0px 0px 12px rgba(0,0,0,0.4);
}

.block-container {
    padding-top: 1rem;
}

h1, h2, h3 {
    color: white;
}

div[data-testid="metric-container"] {
    background-color: #161B22;
    border: 1px solid #2D3748;
    padding: 15px;
    border-radius: 16px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# INFLUX CONFIG
# =========================================================

URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
TOKEN = "TU_TOKEN"
ORG = "miguelcmo"
BUCKET = "iot_telemetry_data"

# =========================================================
# CONNECT
# =========================================================

client = InfluxDBClient(
    url=URL,
    token=TOKEN,
    org=ORG
)

query_api = client.query_api()

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("⚙️ Control Industrial")

time_range = st.sidebar.selectbox(
    "Rango de tiempo",
    [
        "-15m",
        "-1h",
        "-6h",
        "-12h",
        "-24h",
        "-7d"
    ],
    index=1
)

refresh = st.sidebar.slider(
    "Auto Refresh (segundos)",
    5,
    120,
    30
)

show_raw = st.sidebar.checkbox("Mostrar Datos Crudos")

selected_measurements = st.sidebar.multiselect(
    "Measurements",
    [
        "environment",
        "mpu6050"
    ],
    default=["environment", "mpu6050"]
)

# =========================================================
# TITLE
# =========================================================

st.title("🏭 Industrial Drying Oven SCADA")
st.caption("Sistema Industrial de Monitoreo y Telemetría")

# =========================================================
# QUERY FUNCTION
# =========================================================

def load_measurement(measurement):

    query = f'''
    from(bucket: "{BUCKET}")
      |> range(start: {time_range})
      |> filter(fn: (r) => r["_measurement"] == "{measurement}")
    '''

    df = query_api.query_data_frame(query)

    if isinstance(df, list):
        df = pd.concat(df)

    if df.empty:
        return pd.DataFrame()

    remove_cols = [
        "result",
        "table",
        "_start",
        "_stop"
    ]

    for col in remove_cols:
        if col in df.columns:
            df = df.drop(columns=[col])

    return df

# =========================================================
# LOAD DATA
# =========================================================

env_df = load_measurement("environment")
mpu_df = load_measurement("mpu6050")

# =========================================================
# ENVIRONMENT SECTION
# =========================================================

if "environment" in selected_measurements:

    st.header("🌡️ Environmental Monitoring")

    if not env_df.empty:

        humidity_df = env_df[env_df["_field"] == "humidity"]
        temperature_df = env_df[env_df["_field"] == "temperature"]

        col1, col2, col3, col4 = st.columns(4)

        latest_temp = temperature_df["_value"].iloc[-1] if not temperature_df.empty else 0
        latest_humidity = humidity_df["_value"].iloc[-1] if not humidity_df.empty else 0

        with col1:
            st.metric(
                "Temperatura Horno",
                f"{latest_temp:.2f} °C"
            )

        with col2:
            st.metric(
                "Humedad",
                f"{latest_humidity:.2f} %"
            )

        with col3:
            st.metric(
                "Máxima Temp",
                f"{temperature_df['_value'].max():.2f} °C"
            )

        with col4:
            st.metric(
                "Promedio Humedad",
                f"{humidity_df['_value'].mean():.2f} %"
            )

        # TEMPERATURE CHART

        fig_temp = px.line(
            temperature_df,
            x="_time",
            y="_value",
            title="Temperatura del Horno"
        )

        fig_temp.update_layout(
            template="plotly_dark",
            height=400
        )

        st.plotly_chart(fig_temp, use_container_width=True)

        # HUMIDITY CHART

        fig_hum = px.area(
            humidity_df,
            x="_time",
            y="_value",
            title="Humedad Ambiental"
        )

        fig_hum.update_layout(
            template="plotly_dark",
            height=400
        )

        st.plotly_chart(fig_hum, use_container_width=True)

        # GAUGE

        gauge_fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=float(latest_temp),
            title={'text': "Temperatura Actual"},
            gauge={
                'axis': {'range': [0, 300]},
                'bar': {'color': "orange"},
                'steps': [
                    {'range': [0, 100], 'color': "green"},
                    {'range': [100, 200], 'color': "yellow"},
                    {'range': [200, 300], 'color': "red"},
                ]
            }
        ))

        gauge_fig.update_layout(
            template="plotly_dark",
            height=350
        )

        st.plotly_chart(gauge_fig, use_container_width=True)

# =========================================================
# MPU6050 SECTION
# =========================================================

if "mpu6050" in selected_measurements:

    st.header("⚙️ Agitation & Vibration Analysis")

    if not mpu_df.empty:

        accel_fields = [
            "accel_x",
            "accel_y",
            "accel_z"
        ]

        gyro_fields = [
            "gyro_x",
            "gyro_y",
            "gyro_z"
        ]

        accel_df = mpu_df[mpu_df["_field"].isin(accel_fields)]
        gyro_df = mpu_df[mpu_df["_field"].isin(gyro_fields)]

        # ACCELERATION CHART

        fig_accel = px.line(
            accel_df,
            x="_time",
            y="_value",
            color="_field",
            title="Aceleración del Sistema de Agitación"
        )

        fig_accel.update_layout(
            template="plotly_dark",
            height=500
        )

        st.plotly_chart(fig_accel, use_container_width=True)

        # GYRO CHART

        fig_gyro = px.line(
            gyro_df,
            x="_time",
            y="_value",
            color="_field",
            title="Velocidad Angular / Vibración"
        )

        fig_gyro.update_layout(
            template="plotly_dark",
            height=500
        )

        st.plotly_chart(fig_gyro, use_container_width=True)

        # HEATMAP

        pivot_df = gyro_df.pivot_table(
            index="_time",
            columns="_field",
            values="_value"
        )

        heatmap = go.Figure(data=go.Heatmap(
            z=pivot_df.T.values,
            x=pivot_df.index,
            y=pivot_df.columns
        ))

        heatmap.update_layout(
            template="plotly_dark",
            title="Mapa Térmico de Vibraciones",
            height=400
        )

        st.plotly_chart(heatmap, use_container_width=True)

        # STATS

        st.subheader("📈 Estadísticas Industriales")

        stats = mpu_df.groupby("_field")["_value"].agg([
            "mean",
            "max",
            "min",
            "std"
        ])

        st.dataframe(
            stats,
            use_container_width=True
        )

# =========================================================
# ALERT SYSTEM
# =========================================================

st.header("🚨 Alertas Industriales")

alerts = []

if not env_df.empty:

    temp_now = temperature_df["_value"].iloc[-1]

    if temp_now > 200:
        alerts.append("🔥 Temperatura crítica en horno")

    if temp_now < 40:
        alerts.append("⚠️ Temperatura demasiado baja")

if not mpu_df.empty:

    accel_peak = accel_df["_value"].abs().max()

    if accel_peak > 15:
        alerts.append("⚠️ Vibración excesiva detectada")

if len(alerts) == 0:
    st.success("Sistema operando normalmente")
else:
    for alert in alerts:
        st.error(alert)

# =========================================================
# RAW DATA
# =========================================================

if show_raw:

    st.header("🧾 Datos Crudos")

    if not env_df.empty:
        st.subheader("Environment")
        st.dataframe(env_df, use_container_width=True)

    if not mpu_df.empty:
        st.subheader("MPU6050")
        st.dataframe(mpu_df, use_container_width=True)

# =========================================================
# FOOTER
# =========================================================

st.caption(
    f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
