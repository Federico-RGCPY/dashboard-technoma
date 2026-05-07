import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

# 1. Configuración de la App
st.set_page_config(page_title="RGC Seguimiento - Technoma", layout="wide")

# URL del Sheet (Asegúrate que los Secrets tengan esta misma URL)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1L2kKpbx3u-bGehPZqce0Y7MVTKRK0fW9xEqkv5IZ2PQ/edit?usp=sharing"

st.title("📋 Seguimiento de Oportunidades RGC")

# 2. Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        # Forzamos ttl=0 para que no use caché y lea datos reales
        return conn.read(spreadsheet=SHEET_URL, ttl=0).dropna(how="all")
    except Exception:
        # Si falla o está vacío, devolvemos el esquema base
        return pd.DataFrame(columns=[
            'ID', 'Fecha Creación', 'Último Movimiento', 'Ejecutivo Comercial', 
            'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status', 'Cierre Estimado'
        ])

def guardar_datos(dataframe):
    try:
        # Paso crítico: Convertir todo a texto para evitar errores de formato de Google
        df_para_guardar = dataframe.astype(str)
        # Usamos update sin especificar worksheet para que use la primera por defecto
        conn.update(spreadsheet=SHEET_URL, data=df_para_guardar)
        st.toast("✅ ¡Sincronizado en Google Sheets!")
        return True
    except Exception as e:
        st.error("❌ Error al escribir en Google Sheets")
        st.info("Asegúrate de que el archivo en Google esté compartido como EDITOR para cualquier persona con el enlace.")
        st.code(str(e))
        return False

# Cargar datos al inicio
if 'ventas' not in st.session_state:
    st.session_state.ventas = cargar_datos()

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
                    "ID": str(int(datetime.now().timestamp())),
                    "Fecha Creación": str(date.today()),
                    "Último Movimiento": str(date.today()),
                    "Ejecutivo Comercial": eje,
                    "Cliente": cli,
                    "Tipo de Solución": sol,
                    "Monto Est.": str(mon),
                    "Status": "Negociando",
                    "Cierre Estimado": str(cie)
                }])
                
                # Actualizar estado local
                st.session_state.ventas = pd.concat([st.session_state.ventas, nueva_fila], ignore_index=True)
                
                # Intentar guardar en la nube
                if guardar_datos(st.session_state.ventas):
                    st.success("Registrado correctamente")
                    st.rerun()

# --- PANEL PRINCIPAL ---
df = st.session_state.ventas.copy()

if not df.empty:
    # Convertir fechas para la visualización
    df['Cierre Estimado'] = pd.to_datetime(df['Cierre Estimado'], errors='coerce')
    df['Mes_Txt'] = df['Cierre Estimado'].dt.strftime('%B %Y')
    df = df.sort_values(by='Cierre Estimado')

    activos = df[df['Status'].isin(['Negociando', 'Bajo', 'Medio'])]
    
    # Métricas
    m1, m2 = st.columns(2)
    with m1:
        total = pd.to_numeric(activos['Monto Est.'], errors='coerce').sum()
        st.metric("Pipeline Total", f"${total:,.0f}")
    with m2:
        st.metric("Proyectos Activos", len(activos))

    st.divider()

    # Pipeline por meses
    if not activos.empty:
        for mes in activos['Mes_Txt'].unique():
            st.subheader(f"📅 {mes.upper()}")
            items = activos[activos['Mes_Txt'] == mes]
            
            for i, row in items.iterrows():
                with st.expander(f"📌 {row['Cliente']} | {row['Tipo de Solución']}"):
                    opciones = ["Negociando", "Bajo", "Medio", "Ganado", "Perdido", "Postergado"]
                    
                    try:
                        idx_actual = opciones.index(row['Status'])
                    except:
                        idx_actual = 0
                        
                    nuevo_st = st.selectbox("Cambiar Estado", opciones, index=idx_actual, key=f"st_{row['ID']}")
                    
                    if nuevo_st != row['Status']:
                        # Actualizar en el dataframe de la sesión
                        idx_session = st.session_state.ventas[st.session_state.ventas['ID'] == row['ID']].index[0]
                        st.session_state.ventas.at[idx_session, 'Status'] = nuevo_st
                        st.session_state.ventas.at[idx_session, 'Último Movimiento'] = str(date.today())
                        
                        # Guardar cambios
                        if guardar_datos(st.session_state.ventas):
                            st.rerun()
    else:
        st.info("No hay oportunidades activas.")
else:
    st.info("La base de datos está vacía. Usa el panel lateral para registrar.")
