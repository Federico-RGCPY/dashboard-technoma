import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

st.set_page_config(page_title="RGC - Persistencia Total", layout="wide")

# URL de tu Sheet
URL_SHEET = "https://docs.google.com/spreadsheets/d/1L2kKpbx3u-bGehPZqce0Y7MVTKRK0fW9xEqkv5IZ2PQ/edit?usp=sharing"

# Conexión
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNCIÓN DE CARGA ---
def cargar():
    try:
        # ttl=0 es vital para que al refrescar lea lo nuevo de Google
        df = conn.read(spreadsheet=URL_SHEET, ttl=0)
        return df.dropna(how="all")
    except:
        return pd.DataFrame(columns=['ID', 'Fecha Creación', 'Último Movimiento', 'Ejecutivo Comercial', 'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status', 'Cierre Estimado'])

# --- FUNCIÓN DE GUARDADO (Corregida para evitar error de Auth) ---
def guardar(dataframe):
    try:
        # Limpieza de datos: Convertimos todo a texto y quitamos valores vacíos extraños
        df_limpio = dataframe.astype(str).replace("nan", "")
        
        # Intentamos el guardado especificando que es la primera pestaña
        # Si tu pestaña se llama distinto a "Hoja 1", cámbialo aquí:
        conn.update(spreadsheet=URL_SHEET, worksheet="Hoja 1", data=df_limpio)
        st.toast("✅ Sincronizado con Google Sheets")
        return True
    except Exception as e:
        # Si falla por nombre de hoja, intentamos el método genérico
        try:
            conn.update(spreadsheet=URL_SHEET, data=df_limpio)
            st.toast("✅ Sincronizado (Método 2)")
            return True
        except Exception as e2:
            st.error("Error de Autenticación persistente.")
            st.info("Intenta esto: En el Excel, escribe algo en la celda A1 y bórralo. Luego reinicia la App.")
            st.code(str(e2))
            return False

# Ejecución principal
st.title("📋 Seguimiento RGC")
df_actual = cargar()

# Formulario lateral
with st.sidebar:
    st.header("Nuevo Registro")
    with st.form("form_nuevo", clear_on_submit=True):
        eje = st.text_input("Ejecutivo")
        cli = st.text_input("Cliente")
        sol = st.text_input("Equipo")
        mon = st.number_input("Monto", min_value=0)
        if st.form_submit_button("Registrar"):
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
                    "Cierre Estimado": str(date.today())
                }])
                df_final = pd.concat([df_actual, nueva_fila], ignore_index=True)
                if guardar(df_final):
                    st.rerun()

# Mostrar datos
if not df_actual.empty:
    st.dataframe(df_actual, use_container_width=True)
else:
    st.info("Base de datos vacía en Google Sheets.")
