import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime, date

# 1. Configuración de página
st.set_page_config(page_title="RGC Tracking", layout="wide")

# 2. Enlace de tu Google Sheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/1L2kKpbx3u-bGehPZqce0Y7MVTKRK0fW9xEqkv5IZ2PQ/edit?usp=sharing"

# 3. Conexión
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNCIONES DE PERSISTENCIA ---
def cargar_datos():
    # ttl=0 obliga a leer datos nuevos siempre, sin caché
    return conn.read(spreadsheet=SHEET_URL, ttl=0).dropna(how="all")

def guardar_datos(df_nuevo):
    # Esto sobreescribe la hoja con los nuevos datos
    conn.update(spreadsheet=SHEET_URL, data=df_nuevo)

# CARGA INICIAL
df_original = cargar_datos()

# 4. Estilo Visual
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { color: #800020 !important; }
    .header-mes { background-color: #800020; color: white; padding: 10px; border-radius: 5px; margin: 15px 0; font-weight: bold; }
    .stButton>button { background-color: #800020; color: white; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

st.title("📋 Seguimiento de Oportunidades RGC")

# --- BARRA LATERAL: REGISTRO ---
with st.sidebar:
    st.header("📝 Nuevo Registro")
    with st.form("form_registro", clear_on_submit=True):
        ejecutivo = st.text_input("Ejecutivo")
        cliente = st.text_input("Cliente")
        equipo = st.text_input("Equipo / Solución")
        monto = st.number_input("Monto ($)", min_value=0)
        cierre = st.date_input("Fecha Cierre Est.")
        status_ini = st.selectbox("Status", ["Negociando", "Bajo", "Medio"])
        
        if st.form_submit_button("Guardar en Nube"):
            if ejecutivo and cliente:
                nueva_fila = pd.DataFrame([{
                    'ID': int(datetime.now().timestamp()),
                    'Fecha Creación': date.today().strftime('%Y-%m-%d'),
                    'Último Movimiento': date.today().strftime('%Y-%m-%d'),
                    'Ejecutivo Comercial': ejecutivo,
                    'Cliente': cliente,
                    'Tipo de Solución': equipo,
                    'Monto Est.': monto,
                    'Status': status_ini,
                    'Cierre Estimado': cierre.strftime('%Y-%m-%d')
                }])
                
                # Combinar datos viejos con el nuevo
                df_actualizado = pd.concat([df_original, nueva_fila], ignore_index=True)
                guardar_datos(df_actualizado)
                st.success("✅ Sincronizado con Google Sheets")
                st.rerun()

# --- CUERPO PRINCIPAL ---
if not df_original.empty:
    # Preparar datos para visualización
    df_viz = df_original.copy()
    df_viz['Cierre Estimado'] = pd.to_datetime(df_viz['Cierre Estimado'])
    df_viz['Mes_Año'] = df_viz['Cierre Estimado'].dt.strftime('%B %Y')
    df_viz = df_viz.sort_values('Cierre Estimado')

    # Filtros para el Pipeline
    activos = df_viz[df_viz['Status'].isin(['Negociando', 'Bajo', 'Medio'])]
    
    # Métricas
    m1, m2, m3 = st.columns(3)
    m1.metric("Pipeline Activo", f"${activos['Monto Est.'].sum():,.0f}")
    m2.metric("Oportunidades", len(activos))
    m3.metric("Equipos en Neg.", activos['Tipo de Solución'].nunique())

    st.divider()

    # Listado por Meses
    col_main, col_summary = st.columns([3, 1])
    
    with col_main:
        for mes in activos['Mes_Año'].unique():
            st.markdown(f'<div class="header-mes">{mes.upper()}</div>', unsafe_allow_html=True)
            items = activos[activos['Mes_Año'] == mes]
            
            for i, row in items.iterrows():
                # Alarma 10 días
                dias = (date.today() - pd.to_datetime(row['Último Movimiento']).date()).days
                label_alerta = f"⚠️ {dias} días sin cambios" if dias >= 10 else f"✅ {dias} días"
                
                with st.expander(f"{row['Cliente']} | {row['Tipo de Solución']} ({label_alerta})"):
                    c_edit1, c_edit2 = st.columns(2)
                    
                    nuevo_st = c_edit1.selectbox("Cambiar Estado", 
                                               ["Negociando", "Bajo", "Medio", "Ganado", "Perdido", "Postergado"],
                                               index=["Negociando", "Bajo", "Medio", "Ganado", "Perdido", "Postergado"].index(row['Status']),
                                               key=f"st_{row['ID']}")
                    
                    if nuevo_st != row['Status']:
                        # Actualizar en el DataFrame original
                        df_original.loc[df_original['ID'] == row['ID'], 'Status'] = nuevo_st
                        df_original.loc[df_original['ID'] == row['ID'], 'Último Movimiento'] = date.today().strftime('%Y-%m-%d')
                        guardar_datos(df_original)
                        st.rerun()

    with col_summary:
        st.subheader("🛠️ Inventario Negoc.")
        st.write(activos['Tipo de Solución'].value_counts())

else:
    st.info("Aún no hay datos en Google Sheets. Usa el panel de la izquierda para registrar.")
