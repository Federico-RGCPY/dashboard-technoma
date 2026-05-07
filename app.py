import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import io

# 1. Configuración de página
st.set_page_config(page_title="Seguimiento de Oportunidades RGC", layout="wide")

# 2. Enlace de tu Google Sheet
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

st.title("📋 Seguimiento de Oportunidades RGC (Sincronizado)")

# 4. Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos_nube():
    # Lee la hoja de cálculo. ttl=0 para que siempre traiga datos frescos
    return conn.read(spreadsheet=SHEET_URL, ttl=0).dropna(how="all")

def guardar_datos_nube(dataframe):
    # Actualiza la hoja de cálculo completa
    conn.update(spreadsheet=SHEET_URL, data=dataframe)

# Inicializar sesión con datos de la nube
if 'ventas' not in st.session_state:
    st.session_state.ventas = cargar_datos_nube()

# --- SIDEBAR: REGISTRO ---
with st.sidebar:
    st.header("⚙️ Operaciones")
    
    # Formulario de Registro
    st.subheader("📝 Nueva Oportunidad")
    with st.form("registro_form", clear_on_submit=True):
        ejecutivo = st.text_input("Ejecutivo Comercial")
        cliente = st.text_input("Cliente")
        solucion = st.text_input("Producto / Equipo")
        monto = st.number_input("Monto ($)", min_value=0)
        cierre_est = st.date_input("Cierre Estimado", min_value=date.today())
        status_inicial = st.selectbox("Estado Inicial", ["Negociando", "Bajo", "Medio"])
        
        if st.form_submit_button("Registrar en la Nube"):
            if ejecutivo and cliente and solucion:
                nuevo_id = int(datetime.now().timestamp())
                hoy = date.today().strftime('%Y-%m-%d')
                
                nueva_fila = pd.DataFrame([{
                    'ID': nuevo_id, 
                    'Fecha Creación': hoy, 
                    'Último Movimiento': hoy,
                    'Ejecutivo Comercial': ejecutivo, 
                    'Cliente': cliente, 
                    'Tipo de Solución': solucion, 
                    'Monto Est.': monto, 
                    'Status': status_inicial, 
                    'Cierre Estimado': cierre_est.strftime('%Y-%m-%d')
                }])
                
                # Actualizar local y nube
                st.session_state.ventas = pd.concat([st.session_state.ventas, nueva_fila], ignore_index=True)
                guardar_datos_nube(st.session_state.ventas)
                st.success("¡Guardado en Google Sheets!")
                st.rerun()

# --- PROCESAMIENTO ---
df_act = st.session_state.ventas.copy()
if not df_act.empty:
    df_act['Cierre Estimado'] = pd.to_datetime(df_act['Cierre Estimado'])
    df_act['Mes_Año_Txt'] = df_act['Cierre Estimado'].dt.strftime('%B %Y')
    df_act = df_act.sort_values(by='Cierre Estimado')

activos = df_act[df_act['Status'].isin(['Negociando', 'Bajo', 'Medio'])]
finalizados = df_act[df_act['Status'].isin(['Ganado', 'Perdido', 'Postergado'])]

# --- DASHBOARD ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("PIPELINE TOTAL", f"${activos['Monto Est.'].sum():,.0f}")
c2.metric("PROYECTOS ACTIVOS", len(activos))
c3.metric("EQUIPOS", activos['Tipo de Solución'].nunique() if not activos.empty else 0)
c4.metric("TOTAL GANADO", f"${df_act[df_act['Status']=='Ganado']['Monto Est.'].sum():,.0f}")

st.divider()

# --- PANEL PRINCIPAL ---
col_p, col_r = st.columns([3, 1])

with col_p:
    st.subheader("📅 Pipeline por Mes de Cierre")
    if not activos.empty:
        for mes in activos['Mes_Año_Txt'].unique():
            st.markdown(f'<div class="header-mes">{mes.upper()}</div>', unsafe_allow_html=True)
            items_mes = activos[activos['Mes_Año_Txt'] == mes]
            
            for i, row in items_mes.iterrows():
                fecha_mov = pd.to_datetime(row['Último Movimiento']).date()
                dias_atraso = (date.today() - fecha_mov).days
                
                with st.expander(f"📌 {row['Cliente']} | {row['Tipo de Solución']} (${row['Monto Est.']:,})"):
                    if dias_atraso >= 10:
                        st.markdown(f'<div class="alerta-roja">🚨 ALERTA: {dias_atraso} días sin cambios.</div>', unsafe_allow_html=True)
                    
                    ci, ce = st.columns([2, 1])
                    with ci:
                        st.write(f"**Ejecutivo:** {row['Ejecutivo Comercial']}")
                        st.write(f"**Creado:** {pd.to_datetime(row['Fecha Creación']).strftime('%d/%m/%Y')}")
                    with ce:
                        lista_est = ["Negociando", "Bajo", "Medio", "Ganado", "Perdido", "Postergado"]
                        nuevo_st = st.selectbox("Status", options=lista_est, index=lista_est.index(row['Status']), key=f"st_{row['ID']}")
                        
                        if nuevo_st != row['Status']:
                            # Buscar índice real en la sesión
                            idx_original = st.session_state.ventas[st.session_state.ventas['ID'] == row['ID']].index[0]
                            st.session_state.ventas.at[idx_original, 'Status'] = nuevo_st
                            st.session_state.ventas.at[idx_original, 'Último Movimiento'] = date.today().strftime('%Y-%m-%d')
                            
                            guardar_datos_nube(st.session_state.ventas)
                            st.toast("Actualizado en la nube")
                            st.rerun()
    else:
        st.info("No hay oportunidades activas.")

with col_r:
    st.subheader("🛠️ Equipos")
    if not activos.empty:
        resumen = activos['Tipo de Solución'].value_counts()
        for eq, cant in resumen.items():
            st.markdown(f"**{cant}x** {eq}")

st.divider()
st.subheader("📂 Historial (Ultimos 10)")
st.table(finalizados.tail(10)[['Cliente', 'Tipo de Solución', 'Status']])
