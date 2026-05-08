import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
import io

# 1. CONFIGURACIÓN
st.set_page_config(page_title="RGC Dashboard VIP", layout="wide")
URL_SHEET = "https://docs.google.com/spreadsheets/d/1L2kKpbx3u-bGehPZqce0Y7MVTKRK0fW9xEqkv5IZ2PQ/edit?usp=sharing"

MESES_ES = {
    "January": "Enero", "February": "Febrero", "March": "Marzo", "April": "Abril",
    "May": "Mayo", "June": "Junio", "July": "Julio", "August": "Agosto",
    "September": "Septiembre", "October": "Octubre", "November": "Noviembre", "December": "Diciembre"
}

st.markdown("""
    <style>
    .header-mes { background-color: #800020; color: white; padding: 10px; border-radius: 8px; margin-top: 20px; font-weight: bold; text-transform: uppercase; }
    .stMetric { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 15px; border-radius: 10px; }
    h1 { color: #800020 !important; font-weight: 800; }
    .stButton>button { background-color: #800020; color: white; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN Y DATOS
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

# --- LÓGICA ---
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
                nueva = pd.DataFrame([{"ID": str(int(datetime.now().timestamp())), "Fecha Creación": date.today().strftime('%Y-%m-%d'), "Último Movimiento": pd.to_datetime(date.today()), "Ejecutivo Comercial": vend, "Cliente": clie, "Tipo de Solución": equi, "Monto Est.": mont, "Status": "Negociando", "Cierre Estimado": pd.to_datetime(cier)}])
                df = pd.concat([df, nueva], ignore_index=True)
                guardar_datos(df)
                st.rerun()

# KPIs
activos = df[df['Status'].isin(["Negociando", "Bajo", "Medio"])].copy()
m1, m2, m3 = st.columns(3)
m1.metric("PIPELINE ACTIVO", f"${activos['Monto Est.'].sum():,.0f}")
m2.metric("OPORTUNIDADES", len(activos))
m3.metric("EQUIPOS", activos['Tipo de Solución'].nunique())

st.divider()
c_izq, c_der = st.columns([2, 1.3])

# GESTIÓN (IZQUIERDA)
with c_izq:
    st.subheader("🚀 Seguimiento")
    if not activos.empty:
        activos['Mes_ES'] = activos['Cierre Estimado'].dt.strftime('%B').map(MESES_ES) + " " + activos['Cierre Estimado'].dt.strftime('%Y')
        for mes in activos.sort_values('Cierre Estimado')['Mes_ES'].unique():
            st.markdown(f'<div class="header-mes">{mes}</div>', unsafe_allow_html=True)
            for i, row in activos[activos['Mes_ES'] == mes].iterrows():
                with st.expander(f"📌 {row['Cliente']} | {row['Tipo de Solución']} (${row['Monto Est.']:,.0f})"):
                    with st.form(key=f"ed_{row['ID']}"):
                        col1, col2 = st.columns(2)
                        new_v = col1.text_input("Ejecutivo", value=row['Ejecutivo Comercial'])
                        new_m = col1.number_input("Monto ($)", value=float(row['Monto Est.']))
                        new_f = col2.date_input("Cierre", value=row['Cierre Estimado'].date())
                        new_s = col2.selectbox("Estado", opciones_status, index=opciones_status.index(row['Status']))
                        if st.form_submit_button("Guardar"):
                            idx = df[df['ID'] == row['ID']].index[0]
                            df.at[idx, 'Ejecutivo Comercial'], df.at[idx, 'Monto Est.'] = new_v, new_m
                            df.at[idx, 'Cierre Estimado'], df.at[idx, 'Status'] = pd.to_datetime(new_f), new_s
                            df.at[idx, 'Último Movimiento'] = pd.to_datetime(date.today())
                            guardar_datos(df)
                            st.rerun()
    else:
        st.info("Sin registros activos.")

# GRÁFICOS (DERECHA)
with c_der:
    if not activos.empty:
        st.subheader("📊 Desempeño")
        df_g = activos.groupby('Ejecutivo Comercial')['Monto Est.'].sum().reset_index()
        fig_p = go.Figure(data=[go.Pie(labels=df_g['Ejecutivo Comercial'], values=df_g['Monto Est.'], pull=[0.1]*len(df_g), textinfo='label+percent', textposition='outside', marker=dict(colors=px.colors.qualitative.Bold, line=dict(color='#FFFFFF', width=2)))])
        fig_p.update_layout(showlegend=False, margin=dict(t=30,b=30,l=80,r=80), height=380)
        st.plotly_chart(fig_p, use_container_width=True)
        
        st.subheader("🌪️ Embudo")
        df_f = activos['Status'].value_counts().reset_index()
        df_f.columns = ['Etapa', 'Cant']
        fig_f = px.funnel(df_f, x='Cant', y='Etapa', color='Etapa', color_discrete_sequence=px.colors.sequential.RdBu_r)
        fig_f.update_layout(showlegend=False, height=350, margin=dict(t=20,b=20,l=20,r=20))
        st.plotly_chart(fig_f, use_container_width=True)
    else:
        st.write("Sin datos.")

# HISTÓRICO
st.divider()
st.subheader("📂 Archivo Histórico")
hist = df[~df['Status'].isin(["Negociando", "Bajo", "Medio"])].copy()
if not hist.empty:
    for st_t in ["Postergado", "Ganado", "Perdido"]:
        f_h = hist[hist['Status'] == st_t]
        if not f_h.empty:
            with st.expander(f"Ver {st_t}s ({len(f_h)})"):
                for i, r in f_h.iterrows():
                    c_a, c_b = st.columns([3, 1])
                    c_a.write(f"**{r['Cliente']}** - {r['Tipo de Solución']} ({r['Cierre Estimado'].strftime('%d/%m/%Y')})")
                    new_h = c_b.selectbox("Reactivar", opciones_status, index=opciones_status.index(r['Status']), key=f"h_{r['ID']}")
                    if new_h != r['Status']:
                        df.loc[df['ID'] == r['ID'], 'Status'] = new_h
                        df.loc[df['ID'] == r['ID'], 'Último Movimiento'] = pd.to_datetime(date.today())
                        guardar_datos(df)
                        st.rerun()
