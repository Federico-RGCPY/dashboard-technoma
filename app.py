import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

# 1. Configuración inicial
st.set_page_config(page_title="RGC Seguimiento", layout="wide")

# URL de tu Sheet
URL = "https://docs.google.com/spreadsheets/d/1L2kKpbx3u-bGehPZqce0Y7MVTKRK0fW9xEqkv5IZ2PQ/edit?usp=sharing"

st.title("📋 Seguimiento de Oportunidades RGC")
st.markdown("<style>.stMetric {background-color: #f8f9fa; border-radius: 10px; padding: 15px; border: 1px solid #eee;}</style>", unsafe_allow_html=True)

# 2. Conexión
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Carga de datos (con manejo de error si está vacío)
try:
    df = conn.read(spreadsheet=URL, ttl=0).dropna(how="all")
except Exception:
    df = pd.DataFrame(columns=['ID', 'Fecha Creación', 'Último Movimiento', 'Ejecutivo Comercial', 'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status', 'Cierre Estimado'])

# --- FORMULARIO DE REGISTRO ---
with st.sidebar:
    st.header("Nuevo Registro")
    with st.form("registro_rgc", clear_on_submit=True):
        eje = st.text_input("Ejecutivo")
        cli = st.text_input("Cliente")
        sol = st.text_input("Equipo / Solución")
        mon = st.number_input("Monto ($)", min_value=0)
        cie = st.date_input("Cierre Estimado")
        
        if st.form_submit_button("Guardar en Google Sheets"):
            if eje and cli:
                nuevo_dato = pd.DataFrame([{
                    "ID": int(datetime.now().timestamp()),
                    "Fecha Creación": str(date.today()),
                    "Último Movimiento": str(date.today()),
                    "Ejecutivo Comercial": eje,
                    "Cliente": cli,
                    "Tipo de Solución": sol,
                    "Monto Est.": mon,
                    "Status": "Negociando",
                    "Cierre Estimado": str(cie)
                }])
                df_final = pd.concat([df, nuevo_dato], ignore_index=True)
                # Actualizar Nube
                conn.update(spreadsheet=URL, data=df_final)
                st.success("¡Datos sincronizados!")
                st.rerun()

# --- VISUALIZACIÓN ---
if not df.empty:
    # Asegurar formato de fechas
    df['Cierre Estimado'] = pd.to_datetime(df['Cierre Estimado'], errors='coerce')
    df['Mes'] = df['Cierre Estimado'].dt.strftime('%B %Y')
    
    activos = df[df['Status'].isin(['Negociando', 'Bajo', 'Medio'])]
    
    # Métricas
    col1, col2 = st.columns(2)
    col1.metric("Pipeline Total", f"${activos['Monto Est.'].sum():,.0f}")
    col2.metric("Proyectos Activos", len(activos))

    # Agrupación por Mes
    for mes in activos['Mes'].unique():
        st.subheader(f"📅 {mes.upper()}")
        items = activos[activos['Mes'] == mes]
        
        for i, r in items.iterrows():
            with st.expander(f"📌 {r['Cliente']} - {r['Tipo de Solución']} (${r['Monto Est.']:,})"):
                # Alarma 10 días (comparando contra Último Movimiento)
                ultimo_mov = pd.to_datetime(r['Último Movimiento']).date()
                dias = (date.today() - ultimo_mov).days
                
                if dias >= 10:
                    st.error(f"🚨 ALERTA: {dias} días sin novedades.")
                
                # Selector de Estado
                opciones = ["Negociando", "Bajo", "Medio", "Ganado", "Perdido", "Postergado"]
                nuevo_st = st.selectbox("Actualizar Estado", opciones, index=opciones.index(r['Status']), key=f"key_{r['ID']}")
                
                if nuevo_st != r['Status']:
                    df.loc[df['ID'] == r['ID'], 'Status'] = nuevo_st
                    df.loc[df['ID'] == r['ID'], 'Último Movimiento'] = str(date.today())
                    conn.update(spreadsheet=URL, data=df)
                    st.rerun()
else:
    st.info("La base de datos está vacía. Registre la primera oportunidad para comenzar.")
