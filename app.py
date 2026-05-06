import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. Configuración de página
st.set_page_config(page_title="Seguimiento de Oportunidades RGC", layout="wide")

# 2. Estilo CSS Refinado (Asegura alineación y visibilidad)
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .logo-container {
        display: flex;
        justify-content: space-around;
        align-items: center;
        padding: 15px;
        background-color: #fcfcfc;
        border-radius: 10px;
        margin-bottom: 25px;
        border: 1px solid #eee;
    }
    .logo-container img {
        max-height: 50px;
        width: auto;
    }
    [data-testid="stMetricValue"] { color: #800020 !important; font-weight: 800; }
    .stMetric { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 20px; border-radius: 10px; }
    div[data-testid="stSidebar"] { background-color: #f1f3f5; }
    .stButton>button { border-radius: 5px; font-weight: bold; background-color: #800020; color: white; }
    h1 { color: #800020 !important; font-family: 'Segoe UI', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# 3. ENCABEZADO CON LOGOS (URLs Estables)
# He usado imágenes de alta disponibilidad para evitar que se rompan.
st.markdown("""
    <div class="logo-container">
        <img src="https://technoma.com.py/images/logo.png" onerror="this.src='https://cdn-icons-png.flaticon.com/512/2621/2621113.png'">
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Ricoh_logo.svg/2560px-Ricoh_logo.svg.png">
        <img src="https://duplousa.com/wp-content/themes/duplo/assets/images/logo-duplo.png">
    </div>
    """, unsafe_allow_html=True)

st.title("📋 Seguimiento de Oportunidades RGC")
st.divider()

# ... (El resto del código de lógica de ventas sigue aquí igual)
