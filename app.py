import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# URL exacta de tu Sheet (asegúrate que termine en /edit?usp=sharing)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1L2kKpbx3u-bGehPZqce0Y7MVTKRK0fW9xEqkv5IZ2PQ/edit?usp=sharing"

# Conexión
conn = st.connection("gsheets", type=GSheetsConnection)

# Función de carga ultra-robusta
def cargar_datos_seguro():
    try:
        # ttl=0 obliga a la app a buscar datos nuevos en Google, ignorando el cache
        data = conn.read(spreadsheet=SHEET_URL, ttl=0)
        if data is not None and not data.empty:
            return data.dropna(how="all")
        return pd.DataFrame(columns=['ID', 'Fecha Creación', 'Último Movimiento', 'Ejecutivo Comercial', 'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status', 'Cierre Estimado'])
    except Exception as e:
        st.error(f"Error de conexión con Google: {e}")
        return pd.DataFrame()

# REGLA DE ORO: Siempre recargar al refrescar
st.session_state.ventas = cargar_datos_seguro()
