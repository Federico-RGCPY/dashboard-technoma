import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import io

# 1. Configuración de página
st.set_page_config(page_title="Seguimiento de Oportunidades RGC", layout="wide")

# 2. Enlace de tu Google Sheet (Asegúrate que termine en /edit?usp=sharing)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1L2kKpbx3u-bGehPZqce0Y7MVTKRK0fW9xEqkv5IZ2PQ/edit?usp=sharing"

# 3. Estilo CSS
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    [data-testid="stMetricValue"] { color: #800020 !important; font-weight: 800; }
    .stMetric { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 20px; border-radius: 10px; }
    div[data-testid="stSidebar"] { background-color: #f1f3f5; border-right: 1px solid #dee2e6; }
    .stButton>button { border-radius: 5px; font-weight: bold; background-color: #800020; color: white; }
    .alerta-roja { background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px; border-left: 6px solid #dc3545; margin-bottom: 15px; font-weight: bold; }
    .header-mes { background-color: #800020; color: white; padding: 8px 15px; border-radius: 5px; margin-top: 25px; font-size: 1.3rem; font-weight: bold; }
    h1 { color: #800020 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("📋 Seguimiento de Oportunidades RGC")

# 4. Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos_nube():
    try:
        # worksheet=0 fuerza a leer la primera pestaña
        return conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0).dropna(how="all")
    except Exception as e:
        st.error(f"Error al leer Google Sheets: {e}")
        return pd.DataFrame()

def guardar_datos_nube(dataframe):
    try:
        # IMPORTANTE: worksheet=0 para evitar el UnsupportedOperationError
        conn.update(spreadsheet=SHEET_URL, worksheet=0, data=dataframe)
        st.toast("✅ Sincronizado con Google Sheets")
    except Exception as e:
        st.error(f"Error al guardar: Asegúrate de que el Google Sheet esté compartido como 'Editor'. Detalle: {e}")

# Inicializar sesión
if 'ventas' not in st.session_state:
    datos = cargar_datos_nube()
    if datos.empty:
        st.session_state.ventas = pd.DataFrame(columns=[
            'ID', 'Fecha Creación', 'Último Movimiento', 'Ejecutivo Comercial', 
            'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status', 'Cierre Estimado'
        ])
    else:
        st.session_state.ventas = datos

# --- SIDEBAR: REGISTRO ---
with st.sidebar:
    st.header("⚙️ Operaciones")
    with st.form("registro_form", clear_on_submit=True):
        ejecutivo = st.text_input("Ejecutivo Comercial")
        cliente = st.text_input("Cliente")
        solucion = st.text_input("Producto / Equipo")
        monto = st.number_input("Monto ($)", min_value=0)
        cierre_est = st.date_input("Cierre Estimado", min_value=date.today())
        status_inicial = st.selectbox("Estado Inicial", ["Negociando", "Bajo", "Medio"])
        
        if st.form_submit_button("Registrar en la Nube"):
            if ejecutivo and cliente:
                nuevo_id = int(datetime.now().timestamp())
                hoy = date.today().strftime('%Y-%m-%d')
                
                nueva_fila = pd.DataFrame([{
                    'ID': nuevo_id, 'Fecha Creación': hoy, 'Último Movimiento': hoy,
                    'Ejecutivo Comercial': ejecutivo, 'Cliente': cliente, 
                    'Tipo de Solución': solucion, 'Monto Est.': monto, 
                    'Status': status_inicial, 'Cierre Estimado': cierre_est.strftime('%Y-%m-%d')
                }])
                
                st.session_state.ventas = pd.concat([st.session_state.ventas, nueva_fila], ignore_index=True)
                guardar_datos_nube(st.session_state.ventas)
                st.rerun()

# --- PROCESAMIENTO ---
df_act = st.session_state.ventas.copy()
if not df_act.empty and 'Cierre Estimado' in df_act.columns:
    df_act['Cierre Estimado'] = pd.to_datetime(df_act['Cierre Estimado'], errors='coerce')
    df_act = df_act.dropna(subset=['Cierre Estimado'])
    df_act['Mes_Año_Txt'] = df_act['Cierre Estimado'].dt.strftime('%B %Y')
    df_act = df_act.sort_values(by='Cierre Estimado')

    activos = df_act[df_act['Status'].isin(['Negociando', 'Bajo', 'Medio'])]
    finalizados = df_act[df_act['Status'].isin(['Ganado', 'Perdido', 'Postergado'])]

    # --- MÉTRICAS ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PIPELINE TOTAL", f"${activos['Monto Est.'].sum():,.0f}")
    c2.metric("PROYECTOS", len(activos))
    c3.metric("EQUIPOS", activos['Tipo de Solución'].nunique())
    c4.metric("GANADO", f"${df_act[df_act['Status']=='Ganado']['Monto Est.'].sum():,.0f}")

    st.divider()

    # --- PANEL PRINCIPAL ---
    col_p, col_r = st.columns([3, 1])
    with col_p:
        if not activos.empty:
            for mes in activos['Mes_Año_Txt'].unique():
                st.markdown(f'<div class="header-mes">{mes.upper()}</div>', unsafe_allow_html=True)
                items_mes = activos[activos['Mes_Año_Txt'] == mes]
                for i, row in items_mes.iterrows():
                    fecha_mov = pd.to_datetime(row['Último Movimiento']).date()
                    dias_at = (date.today() - fecha_mov).days
                    with st.expander(f"📌 {row['Cliente']} | {row['Tipo de Solución']}"):
                        if dias_at >= 10: st.error(f"Alerta: {dias_at} días sin cambios.")
                        
                        nuevo_st = st.selectbox("Status", ["Negociando", "Bajo", "Medio", "Ganado", "Perdido", "Postergado"], 
                                             index=["Negociando", "Bajo", "Medio", "Ganado", "Perdido", "Postergado"].index(row['Status']), 
                                             key=f"st_{row['ID']}")
                        if nuevo_st != row['Status']:
                            idx = st.session_state.ventas[st.session_state.ventas['ID'] == row['ID']].index[0]
                            st.session_state.ventas.at[idx, 'Status'] = nuevo_st
                            st.session_state.ventas.at[idx, 'Último Movimiento'] = date.today().strftime('%Y-%m-%d')
                            guardar_datos_nube(st.session_state.ventas)
                            st.rerun()
        else:
            st.info("No hay datos activos.")
    
    with col_r:
        st.subheader("🛠️ Equipos")
        st.write(activos['Tipo de Solución'].value_counts())
else:
    st.info("💡 Base de datos vacía o configurando...")
