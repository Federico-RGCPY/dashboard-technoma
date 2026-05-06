import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuración de Marca Technoma
st.set_page_config(page_title="Technoma Intelligence", layout="wide")

# Estilo CSS - Alta Visibilidad y Profesionalismo
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    [data-testid="stMetricValue"] { color: #800020 !important; font-weight: 800; }
    .stMetric { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 20px; border-radius: 10px; }
    div[data-testid="stSidebar"] { background-color: #f1f3f5; border-right: 1px solid #dee2e6; }
    .stButton>button { border-radius: 5px; font-weight: bold; }
    /* Estilo de tablas */
    .stDataFrame { border: 1px solid #eee; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Technoma Intelligence: Pipeline & CRM")

# --- INICIALIZACIÓN DE BASE DE DATOS TEMPORAL ---
if 'ventas' not in st.session_state:
    st.session_state.ventas = pd.DataFrame(columns=[
        'ID', 'Fecha', 'Ejecutivo Comercial', 'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status'
    ])

# --- SIDEBAR: REGISTRO DE OPORTUNIDAD ---
with st.sidebar:
    st.header("🚀 Nueva Oportunidad")
    with st.form("registro_form", clear_on_submit=True):
        ejecutivo = st.text_input("Ejecutivo Comercial")
        cliente = st.text_input("Cliente")
        solucion = st.text_input("Tipo de Solución")
        monto = st.number_input("Monto Estimado ($)", min_value=0)
        status_inicial = st.selectbox("Estado Inicial", ["Bajo", "Medio", "Cerrado"])
        
        if st.form_submit_button("Registrar en Sistema"):
            if ejecutivo and cliente and solucion:
                nuevo_id = len(st.session_state.ventas) + 1
                nueva_fila = {
                    'ID': nuevo_id,
                    'Fecha': datetime.now().strftime("%d/%m/%Y"),
                    'Ejecutivo Comercial': ejecutivo,
                    'Cliente': cliente,
                    'Tipo de Solución': solucion,
                    'Monto Est.': monto,
                    'Status': status_inicial
                }
                st.session_state.ventas = pd.concat([st.session_state.ventas, pd.DataFrame([nueva_fila])], ignore_index=True)
                st.success("Oportunidad Sincronizada")
            else:
                st.error("Complete los campos obligatorios.")

# --- SEPARACIÓN DE DATOS (ACTIVOS VS HISTORIAL) ---
df = st.session_state.ventas
activos = df[~df['Status'].isin(['Perdido', 'Postergado'])]
historial = df[df['Status'].isin(['Perdido', 'Postergado'])]

# --- DASHBOARD DE MÉTRICAS (SOLO ACTIVOS) ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("PIPELINE ACTIVO", f"${activos['Monto Est.'].sum():,.0f}")
col2.metric("PROYECTOS VIVOS", len(activos))
col3.metric("CIERRES", len(activos[activos['Status'] == 'Cerrado']))
col4.metric("PERDIDOS/POST.", len(historial))

st.divider()

# --- GESTIÓN DE OPORTUNIDADES ACTIVAS ---
st.subheader("📋 Gestión de Pipeline Activo")
if not activos.empty:
    for i, row in activos.iterrows():
        with st.expander(f"📌 {row['Cliente']} - {row['Tipo de Solución']} (${row['Monto Est.']:,})"):
            c1, c2, c3, c4 = st.columns([2,2,1,1])
            c1.write(f"**Ejecutivo:** {row['Ejecutivo Comercial']}")
            c2.write(f"**Creado el:** {row['Fecha']}")
            
            # Botones de cambio de estado
            if c3.button("❌ Marcar Perdido", key=f"p_{row['ID']}"):
                st.session_state.ventas.at[i, 'Status'] = 'Perdido'
                st.rerun()
            if c4.button("⏳ Postergar", key=f"s_{row['ID']}"):
                st.session_state.ventas.at[i, 'Status'] = 'Postergado'
                st.rerun()

    # Gráfico Profesional
    st.subheader("📈 Análisis de Oportunidades")
    fig = px.bar(activos, x='Ejecutivo Comercial', y='Monto Est.', color='Status',
                 color_discrete_map={'Bajo': '#A9A9A9', 'Medio': '#4682B4', 'Cerrado': '#800020'},
                 template="plotly_white", barmode='group')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay oportunidades activas en el pipeline.")

st.divider()

# --- HISTORIAL (ABAJO) ---
st.subheader("📂 Historial de Oportunidades (Perdidas/Postergadas)")
if not historial.empty:
    st.dataframe(historial, use_container_width=True)
    
    # Opción para recuperar
    opcion_recuperar = st.selectbox("Seleccione Cliente para reactivar:", historial['Cliente'].unique())
    if st.button("♻️ Reactivar Oportunidad"):
        idx = df[df['Cliente'] == opcion_recuperar].index
        st.session_state.ventas.at[idx[0], 'Status'] = 'Medio'
        st.success(f"Oportunidad de {opcion_recuperar} devuelta al pipeline.")
        st.rerun()
else:
    st.write("El historial está vacío.")
