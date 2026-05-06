import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import io

# Configuración de página
st.set_page_config(page_title="Seguimiento de Oportunidades RGC", layout="wide")

# Estilo CSS - Alta Visibilidad
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    [data-testid="stMetricValue"] { color: #800020 !important; font-weight: 800; }
    .stMetric { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 20px; border-radius: 10px; }
    div[data-testid="stSidebar"] { background-color: #f1f3f5; border-right: 1px solid #dee2e6; }
    .stButton>button { border-radius: 5px; font-weight: bold; }
    .alerta-roja { background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; border-left: 5px solid #f5c6cb; margin-bottom: 10px; font-weight: bold; }
    .header-mes { background-color: #800020; color: white; padding: 5px 15px; border-radius: 5px; margin-top: 20px; font-size: 1.2rem; }
    h1 { color: #800020 !important; font-family: 'Segoe UI', sans-serif; font-size: 2.2rem !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("📋 Seguimiento de Oportunidades RGC")

# --- INICIALIZACIÓN DE DATOS ---
if 'ventas' not in st.session_state:
    st.session_state.ventas = pd.DataFrame(columns=[
        'ID', 'Fecha Creación', 'Último Movimiento', 'Ejecutivo Comercial', 
        'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status', 'Cierre Estimado'
    ])

# --- FUNCIÓN PARA EXCEL ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte_RGC')
    return output.getvalue()

# --- SIDEBAR: REGISTRO Y EXPORTAR ---
with st.sidebar:
    st.header("⚙️ Operaciones")
    
    if not st.session_state.ventas.empty:
        excel_data = to_excel(st.session_state.ventas)
        st.download_button(
            label="📥 Descargar Reporte Excel",
            data=excel_data,
            file_name=f"RGC_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.divider()

    st.subheader("📝 Nueva Oportunidad")
    with st.form("registro_form", clear_on_submit=True):
        ejecutivo = st.text_input("Ejecutivo Comercial")
        cliente = st.text_input("Cliente")
        solucion = st.text_input("Producto / Solución")
        monto = st.number_input("Monto ($)", min_value=0)
        cierre_est = st.date_input("Cierre Estimado", min_value=date.today())
        status_inicial = st.selectbox("Estado Inicial", ["Negociando", "Bajo", "Medio"])
        
        if st.form_submit_button("Registrar Oportunidad"):
            if ejecutivo and cliente:
                nuevo_id = len(st.session_state.ventas) + 1
                hoy = date.today()
                nueva_fila = {
                    'ID': nuevo_id,
                    'Fecha Creación': hoy,
                    'Último Movimiento': hoy,
                    'Ejecutivo Comercial': ejecutivo,
                    'Cliente': cliente,
                    'Tipo de Solución': solucion,
                    'Monto Est.': monto,
                    'Status': status_inicial,
                    'Cierre Estimado': cierre_est
                }
                st.session_state.ventas = pd.concat([st.session_state.ventas, pd.DataFrame([nueva_fila])], ignore_index=True)
                st.rerun()

# --- PROCESAMIENTO DE DATOS ---
df = st.session_state.ventas.copy()
if not df.empty:
    # Convertir a datetime para poder ordenar y agrupar
    df['Cierre Estimado'] = pd.to_datetime(df['Cierre Estimado'])
    df = df.sort_values(by='Cierre Estimado')
    # Crear etiqueta de Mes y Año (ej: Junio 2026)
    # Usamos dt.strftime para la visualización
    df['Mes_Año_Txt'] = df['Cierre Estimado'].dt.strftime('%B %Y')

# Separación por estados
activos = df[df['Status'].isin(['Negociando', 'Bajo', 'Medio'])]
finalizados = df[df['Status'].isin(['Ganado', 'Perdido', 'Postergado'])]

# --- MÉTRICAS ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("PIPELINE TOTAL", f"${activos['Monto Est.'].sum():,.0f}")
c2.metric("PROYECTOS ACTIVOS", len(activos))
c3.metric("TOTAL GANADO", f"${df[df['Status']=='Ganado']['Monto Est.'].sum():,.0f}")
c4.metric("POSTERGADOS", len(df[df['Status']=='Postergado']))

st.divider()

# --- PANEL DE CONTROL DE ACTIVOS POR MES ---
st.subheader("📅 Pipeline Activo por Fecha de Cierre")

if not activos.empty:
    # Agrupar por el texto de Mes y Año manteniendo el orden cronológico
    meses = activos['Mes_Año_Txt'].unique()
    
    for mes in meses:
        st.markdown(f'<div class="header-mes">{mes.upper()}</div>', unsafe_allow_html=True)
        
        # Filtrar registros de este mes específico
        items_mes = activos[activos['Mes_Año_Txt'] == mes]
        
        for i, row in items_mes.iterrows():
            # Cálculo de alarma (10 días desde el último movimiento)
            dias_inactivo = (date.today() - pd.to_datetime(row['Último Movimiento']).date()).days
            
            with st.expander(f"📌 {row['Cliente']} | {row['Tipo de Solución']} (${row['Monto Est.']:,})"):
                
                if dias_inactivo >= 10:
                    st.markdown(f'<div class="alerta-roja">🚨 ALERTA: {dias_inactivo} días sin cambios de estado.</div>', unsafe_allow_html=True)
                
                col_info, col_edit = st.columns([2, 1])
                with col_info:
                    st.write(f"**Ejecutivo:** {row['Ejecutivo Comercial']}")
                    st.write(f"**Creado:** {pd.to_datetime(row['Fecha Creación']).strftime('%d/%m/%Y')}")
                    st.write(f"**Cierre:** {row['Cierre Estimado'].strftime('%d/%m/%Y')}")
                
                with col_edit:
                    nuevo_estado = st.selectbox(
