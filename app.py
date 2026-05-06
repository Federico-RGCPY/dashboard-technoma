import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="Seguimiento de Oportunidades RGC", layout="wide")

# Estilo CSS optimizado (Sin sección de logos)
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    [data-testid="stMetricValue"] { color: #800020 !important; font-weight: 800; }
    .stMetric { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 20px; border-radius: 10px; }
    div[data-testid="stSidebar"] { background-color: #f1f3f5; border-right: 1px solid #dee2e6; }
    .stButton>button { border-radius: 5px; font-weight: bold; }
    h1 { color: #800020 !important; font-family: 'Segoe UI', sans-serif; font-size: 2.2rem !important; }
    </style>
    """, unsafe_allow_html=True)

# Título principal
st.title("📋 Seguimiento de Oportunidades RGC")
st.divider()

# --- INICIALIZACIÓN DE DATOS ---
if 'ventas' not in st.session_state:
    st.session_state.ventas = pd.DataFrame(columns=[
        'ID', 'Fecha', 'Ejecutivo Comercial', 'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status'
    ])

# --- SIDEBAR: REGISTRO ---
with st.sidebar:
    st.header("🛸 Registro RGC")
    with st.form("registro_form", clear_on_submit=True):
        ejecutivo = st.text_input("Ejecutivo Comercial")
        cliente = st.text_input("Cliente")
        solucion = st.text_input("Tipo de Solución (Producto)")
        monto = st.number_input("Monto Estimado ($)", min_value=0)
        status_inicial = st.selectbox("Estado", ["Bajo", "Medio", "Cerrado"])
        
        if st.form_submit_button("Guardar Oportunidad"):
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
                st.toast("Oportunidad registrada correctamente.")
                st.rerun()

# --- LÓGICA DE FILTRADO ---
df = st.session_state.ventas
activos = df[~df['Status'].isin(['Perdido', 'Postergado'])]
historial = df[df['Status'].isin(['Perdido', 'Postergado'])]

# --- MÉTRICAS ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("PIPELINE RGC", f"${activos['Monto Est.'].sum():,.0f}")
c2.metric("PROYECTOS", len(activos))
c3.metric("CIERRES", len(activos[activos['Status'] == 'Cerrado']))
c4.metric("FUERA DE FLUJO", len(historial))

st.divider()

# --- PANEL PRINCIPAL ---
col_main, col_list = st.columns([2, 1])

with col_main:
    st.subheader("📈 Análisis de Pipeline")
    if not activos.empty:
        fig = px.bar(activos, x='Ejecutivo Comercial', y='Monto Est.', color='Status',
                     color_discrete_map={'Bajo': '#A9A9A9', 'Medio': '#4682B4', 'Cerrado': '#800020'},
                     template="plotly_white", barmode='group',
                     labels={'Monto Est.': 'Monto ($)', 'Ejecutivo Comercial': 'Ejecutivo'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sin datos para graficar.")

with col_list:
    st.subheader("🛠️ Soluciones en Negociación")
    for s in activos['Tipo de Solución'].unique():
        st.markdown(f"🔹 {s}")

# --- GESTIÓN INDIVIDUAL ---
st.subheader("📂 Control de Casos Activos")
for i, row in activos.iterrows():
    with st.expander(f"📌 {row['Cliente']} | {row['Tipo de Solución']} (${row['Monto Est.']:,})"):
        ca, cb, cc, cd = st.columns([2,2,1,1])
        ca.write(f"**Ejecutivo:** {row['Ejecutivo Comercial']}")
        cb.write(f"**Ingreso:** {row['Fecha']}")
        if cc.button("❌ Perdido", key=f"per_{row['ID']}"):
            st.session_state.ventas.at[i, 'Status'] = 'Perdido'
            st.rerun()
        if cd.button("⏳ Postergar", key=f"post_{row['ID']}"):
            st.session_state.ventas.at[i, 'Status'] = 'Postergado'
            st.rerun()

st.divider()

# --- HISTORIAL ---
st.subheader("📚 Historial y Recuperación")
if not historial.empty:
    st.table(historial[['Fecha', 'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status']])
    
    rec_col1, rec_col2 = st.columns([2, 1])
    op_rec = rec_col1.selectbox("Seleccione oportunidad para reactivar:", historial['Cliente'].unique())
    if rec_col2.button("♻️ Traer de vuelta"):
        idx = df[df['Cliente'] == op_rec].index
        st.session_state.ventas.at[idx[0], 'Status'] = 'Medio'
        st.success(f"{op_rec} reactivado.")
        st.rerun()
else:
    st.write("No hay registros en el historial.")
