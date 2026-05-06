import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import io

# Configuración de página
st.set_page_config(page_title="Seguimiento de Oportunidades RGC", layout="wide")

# Estilo CSS optimizado
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    [data-testid="stMetricValue"] { color: #800020 !important; font-weight: 800; }
    .stMetric { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 20px; border-radius: 10px; }
    div[data-testid="stSidebar"] { background-color: #f1f3f5; border-right: 1px solid #dee2e6; }
    .stButton>button { border-radius: 5px; font-weight: bold; }
    .alerta-diez { background-color: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; border-left: 5px solid #ffeeba; margin-bottom: 10px; font-weight: bold; }
    h1 { color: #800020 !important; font-family: 'Segoe UI', sans-serif; font-size: 2.2rem !important; }
    </style>
    """, unsafe_allow_html=True)

# Título principal
st.title("📋 Seguimiento de Oportunidades RGC")

# --- INICIALIZACIÓN DE DATOS ---
if 'ventas' not in st.session_state:
    st.session_state.ventas = pd.DataFrame(columns=[
        'ID', 'Fecha Creación', 'Ejecutivo Comercial', 'Cliente', 
        'Tipo de Solución', 'Monto Est.', 'Status', 'Cierre Estimado'
    ])

# --- FUNCIÓN PARA EXCEL ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Oportunidades')
    return output.getvalue()

# --- SIDEBAR: REGISTRO Y EXPORTAR ---
with st.sidebar:
    st.header("🚀 Gestión RGC")
    
    # Botón de Descarga Excel
    if not st.session_state.ventas.empty:
        st.subheader("📥 Exportar Datos")
        excel_data = to_excel(st.session_state.ventas)
        st.download_button(
            label="📊 Descargar Excel (.xlsx)",
            data=excel_data,
            file_name=f"RGC_Reporte_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.divider()

    # Formulario de Registro
    st.subheader("📝 Nueva Oportunidad")
    with st.form("registro_form", clear_on_submit=True):
        ejecutivo = st.text_input("Ejecutivo Comercial")
        cliente = st.text_input("Cliente")
        solucion = st.text_input("Tipo de Solución")
        monto = st.number_input("Monto Estimado ($)", min_value=0)
        cierre_est = st.date_input("Fecha de Cierre Estimada", min_value=date.today())
        status_inicial = st.selectbox("Estado", ["Bajo", "Medio", "Cerrado"])
        
        if st.form_submit_button("Guardar Oportunidad"):
            if ejecutivo and cliente and solucion:
                nuevo_id = len(st.session_state.ventas) + 1
                nueva_fila = {
                    'ID': nuevo_id,
                    'Fecha Creación': date.today(),
                    'Ejecutivo Comercial': ejecutivo,
                    'Cliente': cliente,
                    'Tipo de Solución': solucion,
                    'Monto Est.': monto,
                    'Status': status_inicial,
                    'Cierre Estimado': cierre_est
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
c4.metric("HISTORIAL", len(historial))

st.divider()

# --- PANEL PRINCIPAL ---
col_main, col_list = st.columns([2, 1])

with col_main:
    st.subheader("📈 Análisis de Pipeline")
    if not activos.empty:
        fig = px.bar(activos, x='Ejecutivo Comercial', y='Monto Est.', color='Status',
                     color_discrete_map={'Bajo': '#A9A9A9', 'Medio': '#4682B4', 'Cerrado': '#800020'},
                     template="plotly_white", barmode='group')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sin datos para graficar.")

with col_list:
    st.subheader("🛠️ Soluciones Activas")
    for s in activos['Tipo de Solución'].unique():
        st.markdown(f"🔹 {s}")

# --- GESTIÓN INDIVIDUAL CON ALERTAS ---
st.subheader("📂 Control de Casos Activos")
for i, row in activos.iterrows():
    # Cálculo de días desde la creación
    dias_transcurridos = (date.today() - row['Fecha Creación']).days
    
    with st.expander(f"📌 {row['Cliente']} | {row['Tipo de Solución']} (Ingreso: {row['Fecha Creación']})"):
        
        # ALERTA: Si tiene más de 10 días y no es un cierre
        if dias_transcurridos >= 10 and row['Status'] != 'Cerrado':
            st.markdown(f'<div class="alerta-diez">⚠️ ATENCIÓN: Esta oportunidad tiene {dias_transcurridos} días abierta.</div>', unsafe_allow_html=True)
        
        ca, cb, cc, cd = st.columns([2,2,1,1])
        ca.write(f"**Ejecutivo:** {row['Ejecutivo Comercial']}")
        ca.write(f"**Cierre Estimado:** {row['Cierre Estimado']}")
        cb.write(f"**Monto:** ${row['Monto Est.']:,}")
        cb.write(f"**Estado Actual:** {row['Status']}")
        
        if cc.button("❌ Perdido", key=f"per_{row['ID']}"):
            st.session_state.ventas.at[i, 'Status'] = 'Perdido'
            st.rerun()
        if cd.button("⏳ Postergar", key=f"post_{row['ID']}"):
            st.session_state.ventas.at[i, 'Status'] = 'Postergado'
            st.rerun()

st.divider()

# --- HISTORIAL ---
st.subheader("📚 Historial")
if not historial.empty:
    st.dataframe(historial[['Fecha Creación', 'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status']], use_container_width=True)
