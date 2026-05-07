import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="RGC Technoma", layout="wide")

# URL de tu Sheet - Verifica que sea la correcta
SHEET_URL = "https://docs.google.com/spreadsheets/d/1L2kKpbx3u-bGehPZqce0Y7MVTKRK0fW9xEqkv5IZ2PQ/edit?usp=sharing"

# --- ESTILOS ---
st.markdown("""
    <style>
    .header-mes { background-color: #800020; color: white; padding: 10px; border-radius: 5px; font-weight: bold; margin: 15px 0; }
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Error al configurar la conexión de Google Sheets.")
    st.stop()

# --- FUNCIONES ---
def cargar_datos():
    try:
        # ttl=0 evita que los datos se queden pegados al refrescar
        df = conn.read(spreadsheet=SHEET_URL, ttl=0)
        return df.dropna(how="all")
    except Exception as e:
        st.warning("No se pudo leer la base de datos o está vacía.")
        return pd.DataFrame(columns=['ID', 'Fecha Creación', 'Último Movimiento', 'Ejecutivo Comercial', 'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status', 'Cierre Estimado'])

def guardar_datos(df_nuevo):
    try:
        # Convertimos a strings y limpiamos nulos
        df_save = df_nuevo.astype(str).replace("nan", "")
        
        # Intentamos actualizar usando el método directo del cliente
        # Esto a veces bypasses la restricción de la conexión estándar
        conn.update(spreadsheet=SHEET_URL, data=df_save)
        st.toast("✅ Sincronizado")
        return True
    except Exception as e:
        st.error("🔒 Error de Autenticación de Google")
        st.info("""
        **Para solucionar esto definitivamente:**
        1. En tu Google Sheet, ve a **Compartir**.
        2. Si tienes un correo de cuenta de servicio (ej: `tu-app@...gserviceaccount.com`), agrégalo como Editor.
        3. Si no, asegúrate de que el enlace esté en **'Cualquier persona con el enlace'** Y **'Editor'**.
        """)
        return False

# --- LÓGICA PRINCIPAL ---
st.title("📋 Seguimiento de Oportunidades RGC")

# Carga forzada en cada ejecución
df = cargar_datos()

# Sidebar: Registro
with st.sidebar:
    st.header("📝 Nuevo Registro")
    with st.form("registro", clear_on_submit=True):
        eje = st.text_input("Ejecutivo")
        cli = st.text_input("Cliente")
        sol = st.text_input("Solución/Equipo")
        mon = st.number_input("Monto ($)", min_value=0)
        cie = st.date_input("Cierre Estimado")
        
        if st.form_submit_button("Guardar"):
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
                df_final = pd.concat([df, nueva_fila], ignore_index=True)
                if guardar_datos(df_final):
                    st.success("Guardado correctamente")
                    st.rerun()

# Panel de Visualización
if not df.empty:
    # Formateo de datos
    df['Cierre Estimado'] = pd.to_datetime(df['Cierre Estimado'], errors='coerce')
    df['Mes_Año'] = df['Cierre Estimado'].dt.strftime('%B %Y')
    
    activos = df[df['Status'].isin(['Negociando', 'Bajo', 'Medio'])].sort_values('Cierre Estimado')
    
    # Métricas
    c1, c2 = st.columns(2)
    monto_total = pd.to_numeric(activos['Monto Est.'], errors='coerce').sum()
    c1.metric("Pipeline Total", f"${monto_total:,.0f}")
    c2.metric("Oportunidades", len(activos))
    
    st.divider()

    # Despliegue por Meses
    for mes in activos['Mes_Año'].unique():
        st.markdown(f'<div class="header-mes">{mes.upper()}</div>', unsafe_allow_html=True)
        items = activos[activos['Mes_Año'] == mes]
        
        for i, row in items.iterrows():
            with st.expander(f"📌 {row['Cliente']} | {row['Tipo de Solución']}"):
                # Alarma 10 días
                u_mov = pd.to_datetime(row['Último Movimiento']).date()
                atraso = (date.today() - u_mov).days
                if atraso >= 10:
                    st.error(f"🚨 {atraso} días sin seguimiento")
                
                opciones = ["Negociando", "Bajo", "Medio", "Ganado", "Perdido", "Postergado"]
                nuevo_st = st.selectbox("Estado", opciones, index=opciones.index(row['Status']) if row['Status'] in opciones else 0, key=f"st_{row['ID']}")
                
                if nuevo_st != row['Status']:
                    df.loc[df['ID'] == row['ID'], 'Status'] = nuevo_st
                    df.loc[df['ID'] == row['ID'], 'Último Movimiento'] = str(date.today())
                    if guardar_datos(df):
                        st.rerun()
else:
    st.info("No hay datos cargados. Registra uno nuevo para empezar.")
