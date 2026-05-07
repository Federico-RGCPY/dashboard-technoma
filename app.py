import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

# 1. CONFIGURACIÓN
st.set_page_config(page_title="RGC Seguimiento Profesional", layout="wide")
URL_SHEET = "https://docs.google.com/spreadsheets/d/1L2kKpbx3u-bGehPZqce0Y7MVTKRK0fW9xEqkv5IZ2PQ/edit?usp=sharing"

# Estilos visuales
st.markdown("""
    <style>
    .header-mes { background-color: #800020; color: white; padding: 10px; border-radius: 8px; margin-top: 20px; font-weight: bold; }
    .stMetric { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 15px; border-radius: 10px; }
    .alerta-roja { background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; border-left: 5px solid #dc3545; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        df = conn.read(spreadsheet=URL_SHEET, ttl=0).dropna(how="all")
        df['Cierre Estimado'] = pd.to_datetime(df['Cierre Estimado'], errors='coerce')
        df['Último Movimiento'] = pd.to_datetime(df['Último Movimiento'], errors='coerce')
        return df
    except:
        return pd.DataFrame(columns=['ID', 'Fecha Creación', 'Último Movimiento', 'Ejecutivo Comercial', 'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status', 'Cierre Estimado'])

def guardar_datos(df_save):
    # Convertir a string para Google Sheets
    df_to_push = df_save.copy()
    df_to_push['Cierre Estimado'] = df_to_push['Cierre Estimado'].dt.strftime('%Y-%m-%d')
    df_to_push['Último Movimiento'] = df_to_push['Último Movimiento'].dt.strftime('%Y-%m-%d')
    conn.update(spreadsheet=URL_SHEET, data=df_to_push.astype(str))

# --- INICIO APP ---
df = cargar_datos()
opciones_status = ["Negociando", "Bajo", "Medio", "Ganado", "Perdido", "Postergado"]

st.title("📋 Pipeline de Ventas RGC")

# SIDEBAR: REGISTRO
with st.sidebar:
    st.header("📝 Nueva Oportunidad")
    with st.form("reg", clear_on_submit=True):
        vendedor = st.text_input("Ejecutivo")
        cliente = st.text_input("Cliente")
        equipo = st.text_input("Equipo")
        monto = st.number_input("Monto ($)", min_value=0)
        cierre = st.date_input("Cierre Estimado")
        if st.form_submit_button("Registrar"):
            if vendedor and cliente:
                nueva_fila = pd.DataFrame([{
                    "ID": str(int(datetime.now().timestamp())),
                    "Fecha Creación": date.today().strftime('%Y-%m-%d'),
                    "Último Movimiento": pd.to_datetime(date.today()),
                    "Ejecutivo Comercial": vendedor,
                    "Cliente": cliente,
                    "Tipo de Solución": equipo,
                    "Monto Est.": monto,
                    "Status": "Negociando",
                    "Cierre Estimado": pd.to_datetime(cierre)
                }])
                df = pd.concat([df, nueva_fila], ignore_index=True)
                guardar_datos(df)
                st.rerun()

# MÉTRICAS
activos = df[df['Status'].isin(["Negociando", "Bajo", "Medio"])].copy()
m1, m2, m3 = st.columns(3)
m1.metric("Pipeline Activo", f"${pd.to_numeric(activos['Monto Est.'], errors='coerce').sum():,.0f}")
m2.metric("Oportunidades", len(activos))
m3.metric("Equipos", activos['Tipo de Solución'].nunique())

# PANEL PRINCIPAL: PIPELINE ACTIVO
st.subheader("🚀 Oportunidades en Gestión")
if not activos.empty:
    activos['Mes_Txt'] = activos['Cierre Estimado'].dt.strftime('%B %Y')
    for mes in activos.sort_values('Cierre Estimado')['Mes_Txt'].unique():
        st.markdown(f'<div class="header-mes">{mes.upper()}</div>', unsafe_allow_html=True)
        items = activos[activos['Mes_Txt'] == mes]
        for i, row in items.iterrows():
            with st.expander(f"📌 {row['Cliente']} | {row['Tipo de Solución']} (${float(row['Monto Est.']):,.0f})"):
                # Alarma 10 días
                dias = (date.today() - row['Último Movimiento'].date()).days
                if dias >= 10:
                    st.markdown(f'<div class="alerta-roja">🚨 {dias} días sin seguimiento</div>', unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Ejecutivo:** {row['Ejecutivo Comercial']}")
                with c2:
                    nuevo_st = st.selectbox("Actualizar Estado", opciones_status, 
                                          index=opciones_status.index(row['Status']), 
                                          key=f"act_{row['ID']}")
                    if nuevo_st != row['Status']:
                        df.loc[df['ID'] == row['ID'], 'Status'] = nuevo_st
                        df.loc[df['ID'] == row['ID'], 'Último Movimiento'] = pd.to_datetime(date.today())
                        guardar_datos(df)
                        st.rerun()
else:
    st.info("No hay oportunidades activas.")

st.divider()

# SECCIÓN DE RECUPERACIÓN: POSTERGADOS, GANADOS Y PERDIDOS
st.subheader("📂 Archivo Histórico (Recuperar Postergados/Ganados/Perdidos)")
historico = df[~df['Status'].isin(["Negociando", "Bajo", "Medio"])].copy()

if not historico.empty:
    for st_tipo in ["Postergado", "Ganado", "Perdido"]:
        filtro = historico[historico['Status'] == st_tipo]
        if not filtro.empty:
            with st.expander(f"Ver {st_tipo}s ({len(filtro)})"):
                for i, row in filtro.iterrows():
                    col_a, col_b = st.columns([3, 1])
                    col_a.write(f"**{row['Cliente']}** - {row['Tipo de Solución']} (${float(row['Monto Est.']):,.0f})")
                    # El selectbox aquí permite "Recuperar" enviándolo de vuelta a Negociando
                    nuevo_st_h = col_b.selectbox("Reactivar / Cambiar", opciones_status, 
                                               index=opciones_status.index(row['Status']), 
                                               key=f"hist_{row['ID']}")
                    if nuevo_st_h != row['Status']:
                        df.loc[df['ID'] == row['ID'], 'Status'] = nuevo_st_h
                        df.loc[df['ID'] == row['ID'], 'Último Movimiento'] = pd.to_datetime(date.today())
                        guardar_datos(df)
                        st.success(f"Movido: {row['Cliente']} -> {nuevo_st_h}")
                        st.rerun()
else:
    st.write("El historial está vacío.")
