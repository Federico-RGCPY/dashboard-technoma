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
    
    # Exportación
    if not st.session_state.ventas.empty:
        excel_data = to_excel(st.session_state.ventas)
        st.download_button(
            label="📥 Descargar Reporte Excel",
            data=excel_data,
            file_name=f"RGC_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.divider()

    # Formulario
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
                st.toast("Sincronizado con éxito")
                st.rerun()

# --- FILTRADO POR CATEGORÍAS ---
df = st.session_state.ventas
# Activos son los que están en proceso
activos = df[df['Status'].isin(['Negociando', 'Bajo', 'Medio'])]
# Finalizados son los resultados finales o pausados
finalizados = df[df['Status'].isin(['Ganado', 'Perdido', 'Postergado'])]

# --- MÉTRICAS ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("PIPELINE NEGOCIANDO", f"${activos[activos['Status']=='Negociando']['Monto Est.'].sum():,.0f}")
c2.metric("PROYECTOS ACTIVOS", len(activos))
c3.metric("TOTAL GANADO", f"${df[df['Status']=='Ganado']['Monto Est.'].sum():,.0f}")
c4.metric("POSTERGADOS", len(df[df['Status']=='Postergado']))

st.divider()

# --- PANEL DE CONTROL DE ACTIVOS ---
st.subheader("🔥 Gestión de Pipeline Activo")
if not activos.empty:
    for i, row in activos.iterrows():
        # Cálculo de alarma (10 días desde el último movimiento)
        dias_inactivo = (date.today() - row['Último Movimiento']).days
        
        with st.expander(f"📌 {row['Cliente']} | {row['Tipo de Solución']} (Inactivo: {dias_inactivo} días)"):
            
            if dias_inactivo >= 10:
                st.markdown(f'<div class="alerta-roja">🚨 ALERTA: Sin movimientos en los últimos {dias_inactivo} días. Revisar urgencia.</div>', unsafe_allow_html=True)
            
            col_info, col_edit = st.columns([2, 1])
            
            with col_info:
                st.write(f"**Ejecutivo:** {row['Ejecutivo Comercial']}")
                st.write(f"**Monto:** ${row['Monto Est.']:,}")
                st.write(f"**Creado:** {row['Fecha Creación']}")
                st.write(f"**Expectativa de Cierre:** {row['Cierre Estimado']}")
            
            with col_edit:
                # CAMBIO DE ESTADO EN TIEMPO REAL
                nuevo_estado = st.selectbox(
                    "Actualizar Estado", 
                    ["Negociando", "Bajo", "Medio", "Ganado", "Perdido", "Postergado"],
                    index=["Negociando", "Bajo", "Medio", "Ganado", "Perdido", "Postergado"].index(row['Status']),
                    key=f"edit_{row['ID']}"
                )
                
                if nuevo_estado != row['Status']:
                    st.session_state.ventas.at[i, 'Status'] = nuevo_estado
                    st.session_state.ventas.at[i, 'Último Movimiento'] = date.today()
                    st.success("Estado actualizado")
                    st.rerun()

    # Gráfico Profesional
    st.subheader("📊 Gráfico de Pipeline")
    fig = px.bar(activos, x='Ejecutivo Comercial', y='Monto Est.', color='Status',
                 color_discrete_map={'Negociando': '#4682B4', 'Medio': '#800020', 'Bajo': '#A9A9A9'},
                 template="plotly_white", barmode='stack')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay oportunidades activas actualmente.")

st.divider()

# --- HISTORIAL DE RESULTADOS ---
st.subheader("📂 Historial de Resultados (Ganados / Perdidos / Postergados)")
if not finalizados.empty:
    st.dataframe(finalizados[['Fecha Creación', 'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status', 'Último Movimiento']], use_container_width=True)
    
    # Recuperación
    rec_col1, rec_col2 = st.columns([2, 1])
    op_rec = rec_col1.selectbox("Reactivar oportunidad de:", finalizados['Cliente'].unique())
    if rec_col2.button("♻️ Devolver a Negociación"):
        idx = df[df['Cliente'] == op_rec].index
        st.session_state.ventas.at[idx[0], 'Status'] = 'Negociando'
        st.session_state.ventas.at[idx[0], 'Último Movimiento'] = date.today()
        st.rerun()
