import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
import io

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="RGC Dashboard VIP", layout="wide")

# URL de tu Google Sheet
URL_SHEET = "https://docs.google.com/spreadsheets/d/1L2kKpbx3u-bGehPZqce0Y7MVTKRK0fW9xEqkv5IZ2PQ/edit?usp=sharing"

# Diccionario para traducción de meses
MESES_ES = {
    "January": "Enero", "February": "Febrero", "March": "Marzo", "April": "Abril",
    "May": "Mayo", "June": "Junio", "July": "Julio", "August": "Agosto",
    "September": "Septiembre", "October": "Octubre", "November": "Noviembre", "December": "Diciembre"
}

# Estilos CSS
st.markdown("""
    <style>
    .header-mes { background-color: #800020; color: white; padding: 12px; border-radius: 8px; margin-top: 25px; font-weight: bold; text-transform: uppercase; }
    .stMetric { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    h1 { color: #800020 !important; font-weight: 800; }
    .stButton>button { background-color: #800020; color: white; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN Y FUNCIONES
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        df = conn.read(spreadsheet=URL_SHEET, ttl=0).dropna(how="all")
        df['Cierre Estimado'] = pd.to_datetime(df['Cierre Estimado'], errors='coerce')
        col_mov = 'Último Movimiento' if 'Último Movimiento' in df.columns else 'Últimiento Movimiento'
        df['Último Movimiento'] = pd.to_datetime(df[col_mov], errors='coerce')
        df['Monto Est.'] = pd.to_numeric(df['Monto Est.'], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame(columns=['ID', 'Fecha Creación', 'Último Movimiento', 'Ejecutivo Comercial', 'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status', 'Cierre Estimado'])

def guardar_datos(df_save):
    df_to_push = df_save.copy()
    df_to_push['Cierre Estimado'] = df_to_push['Cierre Estimado'].dt.strftime('%Y-%m-%d')
    df_to_push['Último Movimiento'] = df_to_push['Último Movimiento'].dt.strftime('%Y-%m-%d')
    conn.update(spreadsheet=URL_SHEET, data=df_to_push.astype(str))

# --- LÓGICA PRINCIPAL ---
df = cargar_datos()
opciones_status = ["Negociando", "Bajo", "Medio", "Ganado", "Perdido", "Postergado"]

st.title("📋 Pipeline Estratégico RGC")

# SIDEBAR
with st.sidebar:
    st.header("📝 Registro")
    with st.form("reg_form", clear_on_submit=True):
        vend = st.text_input("Ejecutivo")
        clie = st.text_input("Cliente")
        equi = st.text_input("Equipo")
        mont = st.number_input("Monto ($)", min_value=0.0)
        cier = st.date_input("Fecha Cierre")
        if st.form_submit_button("Registrar"):
            if vend and clie:
                nueva = pd.DataFrame([{
                    "ID": str(int(datetime.now().timestamp())),
                    "Fecha Creación": date.today().strftime('%Y-%m-%d'),
                    "Último Movimiento": pd.to_datetime(date.today()),
                    "Ejecutivo Comercial": vend,
                    "Cliente": clie,
                    "Tipo de Solución": equi,
                    "Monto Est.": mont,
                    "Status": "Negociando",
                    "Cierre Estimado": pd.to_datetime(cier)
                }])
                df = pd.concat([df, nueva], ignore_index=True)
                guardar_datos(df)
                st.rerun()
    
    if not df.empty:
        st.divider()
        towrite = io.BytesIO()
        df.to_excel(towrite, index=False)
        st.download_button(label="📥 Descargar Excel", data=towrite.getvalue(), file_name=f"Pipeline_RGC_{date.today()}.xlsx")

# KPIs
activos = df[df['Status'].isin(["Negociando", "Bajo", "Medio"])].copy()
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("PIPELINE ACTIVO", f"${activos['Monto Est.'].sum():,.0f}")
with m2:
    st.metric("OPORTUNIDADES", len(activos))
with m3:
    st.metric("EQUIPOS", activos['Tipo de Solución'].nunique())

st.divider()

col_izq, col_der = st.columns([2, 1.3])

# GESTIÓN (IZQUIERDA)
with col_izq:
    st.subheader("🚀 Seguimiento de Clientes")
    if not activos.empty:
        activos['Mes_Nombre'] = activos['Cierre Estimado'].dt.strftime('%B')
        activos['Anio'] = activos['Cierre Estimado'].dt.strftime('%Y')
        activos['Mes_ES'] = activos['Mes_Nombre'].map(MESES_ES) + " " + activos['Anio']
        
        meses_ordenados = activos.sort_values('Cierre Estimado')['Mes_ES'].unique()
        
        for mes in meses_ordenados:
            st.markdown(f'<div class="header-mes">{mes}</div>', unsafe_allow_html=True)
            items = activos[activos['Mes_ES'] == mes]
            for i, row in items.iterrows():
                with st.expander(f"📌 {row['Cliente']} | {row['Tipo de Solución']} (${row['Monto Est.']:,.0f})"):
                    with st.form(key=f"edit_{row['ID']}"):
                        c1, c2 = st.columns(2)
                        with c1:
                            new_vend = st.text_input("Ejecutivo", value=row['Ejecutivo Comercial'])
                            new_mont = st.number_input("Monto ($)", value=float(row['Monto Est.']))
                        with c2:
                            new_fech = st.date_input("Cierre", value=row['Cierre Estimado'].date())
                            new_stat = st.selectbox("Estado", opciones_status, index=opciones_status.index(row['Status']))
                        if st.form_submit_button("Guardar Cambios"):
                            idx = df[df['ID'] == row['ID']].index[0]
                            df.at[idx, 'Ejecutivo Comercial'] = new_vend
                            df.at[idx, 'Monto Est.'] = new_mont
                            df.at[idx, 'Cierre Estimado'] = pd.to_datetime(new_fech)
                            df.at[idx, 'Status'] = new_stat
                            df.at[idx, 'Último Movimiento'] = pd.to_datetime(date.today())
                            guardar_datos(df)
                            st.rerun()
    else:
        st.info("Sin registros activos.")

# GRÁFICO (DERECHA)
with col_der:
    st.subheader("📊 Desempeño por Ejecutivo")
    if not activos.empty:
        df_g = activos.groupby('Ejecutivo Comercial')['Monto Est.'].sum().reset_index()
        
        fig = go.Figure(data=[go.Pie(
            labels=df_g['Ejecutivo Comercial'],
            values=df_g['Monto Est.'],
            hole=0,
            pull=[0.1] * len(df_g),
            textinfo='label+percent',
            textposition='outside', 
            marker=dict(colors=px.colors.qualitative.Bold, line=dict(color='#FFFFFF', width=2))
        )])
        
        fig.update_layout(showlegend=False, margin=dict(t=50, b=50, l=80, r=80), height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        st.markdown("**Resumen Numérico:**")
        for idx, r in df_g.sort_values(by='Monto Est.', ascending=False).iterrows():
            st.write(f"👤 {r['Ejecutivo Comercial']}: **${r['Monto Est.']:,.0f}**")
    else:
        st.write("No hay datos para graficar.")

# HISTÓRICO
st.divider()
st.subheader("📂 Archivo Histórico")
hist = df[~df['Status'].isin(["Negociando", "Bajo", "Medio"])].copy()
if not hist.empty:
    for st_tipo in ["Postergado", "Ganado", "Perdido"]:
        filtro = hist[hist['Status'] == st_tipo]
        if not filtro.empty:
            with st.expander(f"Ver {st_tipo}s ({len(filtro)})"):
                for i, row in filtro.iterrows():
                    col_a, col_b = st.columns([3, 1])
                    f_v = row['Cierre Estimado'].strftime('%d/%m/%Y')
                    col_a.write(f"**{row['Cliente']}** - {row['Tipo de Solución']} (Vendedor: {row['Ejecutivo Comercial']} | Cierre: {f_v})")
                    new_s_h = col_b.selectbox("Reactivar", opciones_status, index=opciones_status.index(row['Status']), key=f"h_{row['ID']}")
                    if new_s_h != row['Status']:
                        df.loc[df['ID'] == row['ID'], 'Status'] = new_s_h
                        df.loc[df['ID'] == row['ID'], 'Último Movimiento'] = pd.to_datetime(date.today())
                        guardar_datos(df)
                        st.rerun()
