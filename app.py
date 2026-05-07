import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

# 1. Configuración inicial
st.set_page_config(page_title="RGC Test Acceso", layout="wide")

# URL del nuevo Sheet que pasaste
SHEET_URL = "https://docs.google.com/spreadsheets/d/1UgAs8rEdjOOcSHPl5i1rOGZHqHmDQRhpBKDiXmpO0dQ/edit?usp=sharing"

st.title("🧪 Prueba de Conexión RGC")
st.markdown("---")

# 2. Establecer conexión
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Función de carga con manejo de error de lectura
try:
    df = conn.read(spreadsheet=SHEET_URL, ttl=0).dropna(how="all")
    st.success("✅ Lectura exitosa: Conexión establecida con el Google Sheet.")
except Exception as e:
    st.error(f"❌ Error de Lectura: No se pudo leer el archivo. Verifica los permisos de compartir. Detalle: {e}")
    df = pd.DataFrame(columns=['ID', 'Fecha Creación', 'Último Movimiento', 'Ejecutivo Comercial', 'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status', 'Cierre Estimado'])

# --- FORMULARIO DE PRUEBA DE ESCRITURA ---
st.subheader("📝 Probar Escritura (Guardado)")
with st.form("test_form"):
    st.write("Presiona el botón para intentar guardar una fila de prueba en tu Google Sheet.")
    test_cliente = st.text_input("Nombre de Cliente de Prueba", value="Test Technoma")
    test_monto = st.number_input("Monto de Prueba", value=1000)
    
    submit_test = st.form_submit_button("🚀 Probar Guardado")
    
    if submit_test:
        try:
            # Crear fila de prueba
            nueva_fila = pd.DataFrame([{
                "ID": int(datetime.now().timestamp()),
                "Fecha Creación": str(date.today()),
                "Último Movimiento": str(date.today()),
                "Ejecutivo Comercial": "Admin Test",
                "Cliente": test_cliente,
                "Tipo de Solución": "Equipo Test",
                "Monto Est.": test_monto,
                "Status": "Negociando",
                "Cierre Estimado": str(date.today())
            }])
            
            # Combinar con datos existentes
            df_final = pd.concat([df, nueva_fila], ignore_index=True)
            
            # INTENTO DE ACTUALIZACIÓN EN LA NUBE
            conn.update(spreadsheet=SHEET_URL, data=df_final)
            
            st.balloons()
            st.success("🔥 ¡CONEXIÓN TOTAL! Los datos se guardaron correctamente en Google Sheets.")
            st.info("Revisa tu archivo de Google Sheets; deberías ver la nueva fila al final.")
        except Exception as e:
            st.error("❌ Error de Escritura (UnsupportedOperationError).")
            st.warning("""
            **CÓMO SOLUCIONARLO:**
            1. Abre tu Google Sheet.
            2. Botón 'Compartir' -> Acceso General -> 'Cualquier persona con el enlace'.
            3. Cambia 'Lector' por **EDITOR**.
            4. Asegúrate de que el link en el código y en los 'Secrets' sea exactamente el mismo.
            """)
            st.code(str(e))

# --- VISTA PREVIA DE LOS DATOS ACTUALES ---
st.divider()
st.subheader("📊 Vista previa de la base de datos")
if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.write("La base de datos está vacía o no se pudo leer.")
