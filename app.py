import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

# 1. Configuración de página
st.set_page_config(page_title="RGC Seguimiento", layout="wide")

# URL de tu Sheet (Asegúrate que termine en /edit?usp=sharing)
URL = "https://docs.google.com/spreadsheets/d/1L2kKpbx3u-bGehPZqce0Y7MVTKRK0fW9xEqkv5IZ2PQ/edit?usp=sharing"

st.title("📋 Seguimiento de Oportunidades RGC")

# 2. Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Función de carga segura
def load_data():
    try:
        # worksheet=0 fuerza a usar la primera pestaña
        return conn.read(spreadsheet=URL, worksheet=0, ttl=0).dropna(how="all")
    except:
        return pd.DataFrame(columns=['ID', 'Fecha Creación', 'Último Movimiento', 'Ejecutivo Comercial', 'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status', 'Cierre Estimado'])

df = load_data()

# --- SIDEBAR: REGISTRO ---
with st.sidebar:
    st.header("Nuevo Registro")
    with st.form("f_registro", clear_on_submit=True):
        eje = st.text_input("Ejecutivo")
        cli = st.text_input("Cliente")
        equ = st.text_input("Equipo / Solución")
        mon = st.number_input("Monto ($)", min_value=0)
        cie = st.date_input("Cierre Estimado")
        
        if st.form_submit_button("Guardar en Nube"):
            if eje and cli:
                nuevo = pd.DataFrame([{
                    "ID": int(datetime.now().timestamp()),
                    "Fecha Creación": str(date.today()),
                    "Último Movimiento": str(date.today()),
                    "Ejecutivo Comercial": eje,
                    "Cliente": cli,
                    "Tipo de Solución": equ,
                    "Monto Est.": mon,
                    "Status": "Negociando",
                    "Cierre Estimado": str(cie)
                }])
                df_final = pd.concat([df, nuevo], ignore_index=True)
                # Intento de actualización
                try:
                    conn.update(spreadsheet=URL, worksheet=0, data=df_final)
                    st.success("¡Sincronizado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error de permisos: Asegúrate de que el Google Sheet esté compartido como 'Editor'.")

# --- VISUALIZACIÓN ---
if not df.empty:
    # Convertir fechas para filtros
    df['Cierre Estimado'] = pd.to_datetime(df['Cierre Estimado'], errors='coerce')
    df['Mes'] = df['Cierre Estimado'].dt.strftime('%B %Y')
    
    activos = df[df['Status'].isin(['Negociando', 'Bajo', 'Medio'])]
    
    # Métricas
    c1, c2 = st.columns(2)
    c1.metric("Pipeline Activo", f"${activos['Monto Est.'].sum():,.0f}")
    c2.metric("Proyectos", len(activos))

    # Agrupación por Mes
    for mes in activos['Mes'].unique():
        st.subheader(f"📅 {mes.upper()}")
        items = activos[activos['Mes'] == mes]
        
        for i, r in items.iterrows():
            with st.expander(f"📌 {r['Cliente']} - {r['Tipo de Solución']}"):
                # Alarma 10 días
                u_mov = pd.to_datetime(r['Último Movimiento']).date()
                dias = (date.today() - u_mov).days
                if dias >= 10: st.warning(f"⚠️ {dias} días sin cambios.")
                
                # Update Status
                op = ["Negociando", "Bajo", "Medio", "Ganado", "Perdido", "Postergado"]
                nuevo_st = st.selectbox("Estado", op, index=op.index(r['Status']), key=f"s{r['ID']}")
                
                if nuevo_st != r['Status']:
                    df.loc[df['ID'] == r['ID'], 'Status'] = nuevo_st
                    df.loc[df['ID'] == r['ID'], 'Último Movimiento'] = str(date.today())
                    conn.update(spreadsheet=URL, worksheet=0, data=df)
                    st.rerun()
else:
    st.info("No hay datos en la nube. Registra la primera oportunidad.")
