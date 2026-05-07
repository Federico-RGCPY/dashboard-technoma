import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

# 1. Configuración de la App
st.set_page_config(page_title="RGC Seguimiento - Technoma", layout="wide")

# URL del nuevo Sheet actualizado
SHEET_URL = "https://docs.google.com/spreadsheets/d/1L2kKpbx3u-bGehPZqce0Y7MVTKRK0fW9xEqkv5IZ2PQ/edit?usp=sharing"

# Estilo visual
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    [data-testid="stMetricValue"] { color: #800020 !important; font-weight: 800; }
    .stMetric { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 20px; border-radius: 10px; }
    .header-mes { background-color: #800020; color: white; padding: 8px 15px; border-radius: 5px; margin-top: 25px; font-size: 1.2rem; font-weight: bold; }
    .alerta-roja { background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; border-left: 5px solid #dc3545; }
    </style>
    """, unsafe_allow_html=True)

st.title("📋 Seguimiento de Oportunidades RGC")

# 2. Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        # Intentamos leer la primera hoja disponible
        return conn.read(spreadsheet=SHEET_URL, ttl=0).dropna(how="all")
    except Exception:
        return pd.DataFrame(columns=['ID', 'Fecha Creación', 'Último Movimiento', 'Ejecutivo Comercial', 'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status', 'Cierre Estimado'])

def guardar_datos(dataframe):
    try:
        # Limpieza de nulos para evitar errores de Google
        df_limpio = dataframe.fillna("")
        # Intentamos guardar. La librería buscará la pestaña principal.
        conn.update(spreadsheet=SHEET_URL, data=df_limpio)
        st.toast("✅ Sincronizado en la Nube")
    except Exception as e:
        st.error("❌ Error de Escritura: Verifica que el Sheet esté compartido como 'Cualquier persona con el enlace' en modo EDITOR.")
        st.code(str(e))

# Cargar datos iniciales
df = cargar_datos()

# --- SIDEBAR: REGISTRO ---
with st.sidebar:
    st.header("⚙️ Registro")
    with st.form("form_registro", clear_on_submit=True):
        eje = st.text_input("Ejecutivo Comercial")
        cli = st.text_input("Cliente")
        sol = st.text_input("Equipo / Solución")
        mon = st.number_input("Monto ($)", min_value=0)
        cie = st.date_input("Cierre Estimado")
        
        if st.form_submit_button("Registrar Oportunidad"):
            if eje and cli:
                nueva_fila = pd.DataFrame([{
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
                df = pd.concat([df, nueva_fila], ignore_index=True)
                guardar_datos(df)
                st.rerun()

# --- PANEL PRINCIPAL ---
if not df.empty:
    # Procesamiento de fechas para visualización
    df['Cierre Estimado'] = pd.to_datetime(df['Cierre Estimado'], errors='coerce')
    df['Mes_Txt'] = df['Cierre Estimado'].dt.strftime('%B %Y')
    df = df.sort_values(by='Cierre Estimado')

    activos = df[df['Status'].isin(['Negociando', 'Bajo', 'Medio'])]
    
    # Métricas
    m1, m2, m3 = st.columns(3)
    m1.metric("Pipeline Total", f"${activos['Monto Est.'].sum():,.0f}")
    m2.metric("Oportunidades", len(activos))
    m3.metric("Equipos Distintos", activos['Tipo de Solución'].nunique())

    st.divider()

    # Pipeline agrupado por meses (Junio 2026, etc)
    for mes in activos['Mes_Txt'].unique():
        st.markdown(f'<div class="header-mes">{mes.upper()}</div>', unsafe_allow_html=True)
        items = activos[activos['Mes_Txt'] == mes]
        
        for i, row in items.iterrows():
            with st.expander(f"📌 {row['Cliente']} | {row['Tipo de Solución']} (${row['Monto Est.']:,})"):
                # Lógica de Alarma
                fecha_u = pd.to_datetime(row['Último Movimiento']).date()
                dias = (date.today() - fecha_u).days
                if dias >= 10:
                    st.markdown(f'<div class="alerta-roja">🚨 {dias} días sin seguimiento</div>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Ejecutivo:** {row['Ejecutivo Comercial']}")
                    st.write(f"**Creado:** {row['Fecha Creación']}")
                
                with col2:
                    opciones = ["Negociando", "Bajo", "Medio", "Ganado", "Perdido", "Postergado"]
                    # Asegurar que el index coincida con el status actual
                    try:
                        idx_actual = opciones.index(row['Status'])
                    except:
                        idx_actual = 0
                        
                    nuevo_st = st.selectbox("Actualizar Estado", opciones, index=idx_actual, key=f"st_{row['ID']}")
                    
                    if nuevo_st != row['Status']:
                        df.loc[df['ID'] == row['ID'], 'Status'] = nuevo_st
                        df.loc[df['ID'] == row['ID'], 'Último Movimiento'] = str(date.today())
                        guardar_datos(df)
                        st.rerun()

    # Listado de equipos a la derecha (opcional, como resumen)
    with st.sidebar:
        st.divider()
        st.subheader("🛠️ Resumen Equipos")
        st.write(activos['Tipo de Solución'].value_counts())
else:
    st.info("👋 ¡Bienvenido! Registra tu primera oportunidad en el panel de la izquierda para comenzar.")
