import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import io

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="RGC Dashboard VIP", layout="wide")

# URL de tu Google Sheet
URL_SHEET = "https://docs.google.com/spreadsheets/d/1L2kKpbx3u-bGehPZqce0Y7MVTKRK0fW9xEqkv5IZ2PQ/edit?usp=sharing"

# Diccionario para traducción de meses
MESES_ES = {
    "January": "Enero", "February": "Febrero", "March": "Marzo", "April": "Abril",
    "May": "Mayo", "June": "Junio", "July": "Julio", "August": "Agosto",
    "September": "Septiembre", "October": "Octubre", "November": "Noviembre", "December": "Diciembre"
}

# Estilos CSS para personalización visual
st.markdown("""
    <style>
    .header-mes { background-color: #800020; color: white; padding: 12px; border-radius: 8px; margin-top: 25px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; }
    .stMetric { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    h1 { color: #800020 !important; font-weight: 800; }
    .stButton>button { background-color: #800020; color: white; border-radius: 5px; width: 100%; }
    .stExpander { border: 1px solid #dee2e6; border-radius: 10px; background-color: white; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN Y FUNCIONES DE DATOS
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        # Leemos sin caché para ver cambios al instante
        df = conn.read(spreadsheet=URL_SHEET, ttl=0).dropna(how="all")
        # Aseguramos formatos correctos
        df['Cierre Estimado'] = pd.to_datetime(df['Cierre Estimado'], errors='coerce')
        df['Último Movimiento'] = pd.to_datetime(df['Último Movimiento'], errors='coerce')
        df['Monto Est.'] = pd.to_numeric(df['Monto Est.'], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame(columns=['ID', 'Fecha Creación', 'Último Movimiento', 'Ejecutivo Comercial', 'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status', 'Cierre Estimado'])

def guardar_datos(df_save):
    # Formateamos antes de enviar a Google Sheets
    df_to_push = df_save.copy()
    df_to_push['Cierre Estimado'] = df_to_push['Cierre Estimado'].dt.strftime('%Y-%m-%d')
    df_to_push['Último Movimiento'] = df_to_push['Último Movimiento'].dt.strftime('%Y-%m-%d')
    conn.update(spreadsheet=URL_SHEET, data=df_to_push.astype(str))

# --- INICIO DE LA LÓGICA DE LA APP ---
df = cargar_datos()
opciones_status = ["Negociando", "Bajo", "Medio", "Ganado", "Perdido", "Postergado"]

st.title("📋 Pipeline Estratégico RGC")

# 3. BARRA LATERAL (REGISTRO Y EXPORTACIÓN)
with st.sidebar:
    st.header("📝 Registro de Oportunidad")
    with st.form("registro_nuevo", clear_on_submit=True):
        vendedor = st.text_input("Ejec
