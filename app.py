import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date
import io

# 1. CONFIGURACIÓN
st.set_page_config(page_title="RGC Dashboard Profesional", layout="wide")
URL_SHEET = "https://docs.google.com/spreadsheets/d/1L2kKpbx3u-bGehPZqce0Y7MVTKRK0fW9xEqkv5IZ2PQ/edit?usp=sharing"

# Estilos visuales
st.markdown("""
    <style>
    .header-mes { background-color: #800020; color: white; padding: 10px; border-radius: 8px; margin-top: 20px; font-weight: bold; }
    .stMetric { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 15px; border-radius: 10px; }
    .alerta-roja { background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; border-left: 5px solid #dc3545; margin-bottom: 10px; }
    h1 { color: #800020 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        df = conn.read(spreadsheet=URL_SHEET, ttl=0).dropna(how="all")
        df['Cierre Estimado'] = pd.to_datetime(df['Cierre Estimado'], errors='coerce')
        df['Último Movimiento'] = pd.to_datetime(df['Último Movimiento'], errors='coerce')
        df['Monto Est.'] = pd.to_numeric(df['Monto Est.'], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame(columns=['ID', 'Fecha Creación', 'Último Movimiento', 'Ejecutivo Comercial', 'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status', 'Cierre Estimado'])

def guardar_datos(df_save):
    df_to_push = df_save.copy()
    df_to_push['Cierre Estimado'] = df_to_push['Cierre Estimado'].dt.strftime('%Y-%m-%d')
    df_to_push['Último Movimiento'] = df_to_push['Último Movimiento'].dt.strftime('%Y-%m-%d')
    conn.update(spreadsheet=URL_SHEET, data=df_to_push.astype(str))

# --- INICIO APP ---
df = cargar_datos()
opciones_status = ["Negociando", "Bajo", "Medio", "Ganado", "Perdido", "Postergado"]

st.title("📋 Pipeline de Ventas RGC")

# SIDEBAR
with st.sidebar:
    st.header("📝 Nueva Oportunidad")
    with st.form("reg", clear_on_submit=True):
        vendedor = st.text_input("Ejecutivo")
        cliente = st.text_input("Cliente")
        equipo = st.text_input("Equipo")
        monto = st.number_input("Monto ($)", min_value=0)
        cierre_form = st.date_input("Cierre Estimado")
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
                    "Cierre Estimado": pd.to_datetime(cierre_form)
                }])
                df = pd.concat([df, nueva_fila], ignore_index=True)
                guardar_datos(df)
                st.rerun()
    
    if not df.empty:
        st.divider()
        towrite = io.BytesIO()
        df.to_excel(towrite, index=False, engine='xlsxwriter')
        st.download_button(label="📥 Descargar Excel", data=towrite.getvalue(), file_name=f"Pipeline_RGC_{date.today()}.xlsx")

# MÉTRICAS
activos = df[df['Status'].isin(["Negociando", "Bajo", "Medio"])].copy()
m1, m2, m3 = st.columns(3)
m1.metric("Pipeline Activo", f"${activos['Monto Est.'].sum():,.0f}")
m2.metric("Oportunidades", len(activos))
m3.metric("Equipos", activos['Tipo de Solución'].nunique())

st.divider()

# COLUMNAS PRINCIPALES
col_izq, col_der = st.columns([2.5, 1])

with col_izq:
    st.subheader("🚀 Oportunidades en Gestión")
    if not activos.empty:
        activos['Mes_Txt'] = activos['Cierre Estimado'].dt.strftime('%B %Y')
        meses_ordenados = activos.sort_values('Cierre Estimado')['Mes_Txt'].unique()
        
        for mes in meses_ordenados:
            st.markdown(f'<div class="header-mes">{mes.upper()}</div>', unsafe_allow_html=True)
            items = activos[activos['Mes_Txt'] == mes]
            for i, row in items.iterrows():
                with st.expander(f"📌 {row['Cliente']} | {row['Tipo de Solución']} (${row['Monto Est.']:,.0f})"):
                    dias_atraso = (date.today() - row['Último Movimiento'].date()).days
                    if dias_atraso >= 10:
                        st.markdown(f'<div class="alerta-roja">🚨 {dias_atraso} días sin seguimiento</div>', unsafe_allow_html=True)
                    
                    col_info, col_edicion = st.columns(2)
                    with col_info:
                        st.write(f"👤 **Vendedor:** {row['Ejecutivo Comercial']}")
                        # Actualizar Fecha Cierre
                        nueva_fecha = st.date_input("Actualizar Fecha Cierre", value=row['Cierre Estimado'].date(), key=f"date_{row['ID']}")
                        if pd.to_datetime(nueva_fecha) != row['Cierre Estimado']:
                            idx = df[df['ID'] == row['ID']].index[0]
                            df.at[idx, 'Cierre Estimado'] = pd.to_datetime(nueva_fecha)
                            df.at[idx, 'Último Movimiento'] = pd.to_datetime(date.today())
                            guardar_datos(df)
                            st.rerun()

                    with col_edicion:
                        nuevo_st = st.selectbox("Estado", opciones_status, index=opciones_status.index(row['Status']), key=f"act_{row['ID']}")
                        if nuevo_st != row['Status']:
                            idx = df[df['ID'] == row['ID']].index[0]
                            df.at[idx, 'Status'] = nuevo_st
                            df.at[idx, 'Último Movimiento'] = pd.to_datetime(date.today())
                            guardar_datos(df)
                            st.rerun()
    else:
        st.info("No hay oportunidades activas.")

with col_der:
    st.subheader("📊 Desempeño")
    if not activos.empty:
        st.markdown("**Pipeline por Ejecutivo:**")
        por_vendedor = activos.groupby('Ejecutivo Comercial')['Monto Est.'].sum().sort_values(ascending=False)
        for vend, monto in por_vendedor.items():
            st.write(f"👤 {vend}: ${monto:,.0f}")
        st.divider()
        st.markdown("**Mezcla de Equipos:**")
        por_equipo = activos['Tipo de Solución'].value_counts()
        for eq, cant in por_equipo.items():
            st.write(f"🛠️ {cant}x {eq}")

st.divider()

# SECCIÓN DE RECUPERACIÓN
st.subheader("📂 Archivo Histórico")
historico = df[~df['Status'].isin(["Negociando", "Bajo", "Medio"])].copy()
if not historico.empty:
    for st_tipo in ["Postergado", "Ganado", "Perdido"]:
        filtro = historico[historico['Status'] == st_tipo]
        if not filtro.empty:
            with st.expander(f"Ver {st_tipo}s ({len(filtro)})"):
                for i, row in filtro.iterrows():
                    col_txt, col_fecha, col_st = st.columns([2, 1, 1])
                    col_txt.write(f"**{row['Cliente']}** - {row['Tipo de Solución']}")
                    
                    f_hist = col_fecha.date_input("Fecha Cierre", value=row['Cierre Estimado'].date(), key=f"hdate_{row['ID']}")
                    if pd.to_datetime(f_hist) != row['Cierre Estimado']:
                        df.loc[df['ID'] == row['ID'], 'Cierre Estimado'] = pd.to_datetime(f_hist)
                        guardar_datos(df)
                        st.rerun()

                    nuevo_st_h = col_st.selectbox("Reactivar", opciones_status, index=opciones_status.index(row['Status']), key=f"hist_{row['ID']}")
                    if nuevo_st_h != row['Status']:
                        df.loc[df['ID'] == row['ID'], 'Status'] = nuevo_st_h
                        df.loc[df['ID'] == row['ID'], 'Último Movimiento'] = pd.to_datetime(date.today())
                        guardar_datos(df)
                        st.rerun()
