import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import io

# 1. CONFIGURACIÓN
st.set_page_config(page_title="RGC Dashboard Next-Gen", layout="wide")
URL_SHEET = "https://docs.google.com/spreadsheets/d/1L2kKpbx3u-bGehPZqce0Y7MVTKRK0fW9xEqkv5IZ2PQ/edit?usp=sharing"

MESES_ES = {
    "January": "Enero", "February": "Febrero", "March": "Marzo", "April": "Abril",
    "May": "Mayo", "June": "Junio", "July": "Julio", "August": "Agosto",
    "September": "Septiembre", "October": "Octubre", "November": "Noviembre", "December": "Diciembre"
}

st.markdown("""
    <style>
    .header-mes { background-color: #800020; color: white; padding: 10px; border-radius: 8px; margin-top: 20px; font-weight: bold; text-transform: uppercase; }
    .stMetric { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 15px; border-radius: 10px; border-left: 5px solid #800020; }
    h1 { color: #800020 !important; font-weight: 800; letter-spacing: -1px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN
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
    df_p = df_save.copy()
    df_p['Cierre Estimado'] = df_p['Cierre Estimado'].dt.strftime('%Y-%m-%d')
    df_p['Último Movimiento'] = df_p['Último Movimiento'].dt.strftime('%Y-%m-%d')
    conn.update(spreadsheet=URL_SHEET, data=df_p.astype(str))

# --- LÓGICA ---
df = cargar_datos()
opciones_status = ["Negociando", "Bajo", "Medio", "Ganado", "Perdido", "Postergado"]

st.title("🚀 RGC Strategic Vision")

# SIDEBAR
with st.sidebar:
    st.header("📝 Nueva Oportunidad")
    with st.form("reg_form", clear_on_submit=True):
        v, c, e = st.text_input("Ejecutivo"), st.text_input("Cliente"), st.text_input("Equipo")
        m, d = st.number_input("Monto ($)", min_value=0.0), st.date_input("Cierre")
        if st.form_submit_button("Añadir al Pipeline"):
            if v and c:
                nueva = pd.DataFrame([{"ID": str(int(datetime.now().timestamp())), "Fecha Creación": date.today().strftime('%Y-%m-%d'), "Último Movimiento": pd.to_datetime(date.today()), "Ejecutivo Comercial": v, "Cliente": c, "Tipo de Solución": e, "Monto Est.": m, "Status": "Negociando", "Cierre Estimado": pd.to_datetime(d)}])
                df = pd.concat([df, nueva], ignore_index=True); guardar_datos(df); st.rerun()

# KPIs
activos = df[df['Status'].isin(["Negociando", "Bajo", "Medio"])].copy()
k1, k2, k3 = st.columns(3)
k1.metric("VALOR TOTAL", f"${activos['Monto Est.'].sum():,.0f}")
k2.metric("PROYECTOS", len(activos))
k3.metric("EQUIPOS", activos['Tipo de Solución'].nunique())

st.divider()
c1, c2 = st.columns([1.8, 1.2])

# GESTIÓN (IZQUIERDA)
with c1:
    st.subheader("📋 Pipeline de Seguimiento")
    if not activos.empty:
        activos['Mes_ES'] = activos['Cierre Estimado'].dt.strftime('%B').map(MESES_ES) + " " + activos['Cierre Estimado'].dt.strftime('%Y')
        for mes in activos.sort_values('Cierre Estimado')['Mes_ES'].unique():
            st.markdown(f'<div class="header-mes">{mes}</div>', unsafe_allow_html=True)
            for i, row in activos[activos['Mes_ES'] == mes].iterrows():
                with st.expander(f"🔹 {row['Cliente']} | {row['Tipo de Solución']} (${row['Monto Est.']:,.0f})"):
                    with st.form(key=f"ed_{row['ID']}"):
                        ca, cb = st.columns(2)
                        nv = ca.text_input("Ejecutivo", value=row['Ejecutivo Comercial'])
                        nm = ca.number_input("Monto ($)", value=float(row['Monto Est.']))
                        nf = cb.date_input("Cierre", value=row['Cierre Estimado'].date())
                        ns = cb.selectbox("Estado", opciones_status, index=opciones_status.index(row['Status']))
                        if st.form_submit_button("Actualizar"):
                            idx = df[df['ID'] == row['ID']].index[0]
                            df.at[idx, 'Ejecutivo Comercial'], df.at[idx, 'Monto Est.'] = nv, nm
                            df.at[idx, 'Cierre Estimado'], df.at[idx, 'Status'] = pd.to_datetime(nf), ns
                            df.at[idx, 'Último Movimiento'] = pd.to_datetime(date.today())
                            guardar_datos(df); st.rerun()
    else: st.info("No hay datos activos.")

# VISUALIZACIÓN MODERNA (DERECHA)
with c2:
    st.subheader("🎯 Análisis de Distribución")
    if not activos.empty:
        # GRAFICO TREEMAP: Tamaño por Monto, Color por Ejecutivo
        fig_tree = px.treemap(
            activos, 
            path=['Ejecutivo Comercial', 'Cliente'], # Jerarquía: Vendedor -> Cliente
            values='Monto Est.',
            color='Monto Est.',
            color_continuous_scale='RdBu', # Escala de color elegante
            custom_data=['Tipo de Solución']
        )
        fig_tree.update_traces(
            textinfo="label+value",
            hovertemplate='<b>%{label}</b><br>Monto: $%{value:,.0f}<br>Equipo: %{customdata[0]}'
        )
        fig_tree.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=500)
        st.plotly_chart(fig_tree, use_container_width=True)
        
        st.divider()
        st.markdown("**Ranking de Ejecutivos:**")
        rank = activos.groupby('Ejecutivo Comercial')['Monto Est.'].sum().sort_values(ascending=False)
        for e, m in rank.items():
            st.write(f"💼 {e}: **${m:,.0f}**")
    else: st.write("Sin datos.")

# HISTÓRICO
st.divider()
st.subheader("📂 Archivo")
hist = df[~df['Status'].isin(["Negociando", "Bajo", "Medio"])].copy()
if not hist.empty:
    for t in ["Postergado", "Ganado", "Perdido"]:
        fil = hist[hist['Status'] == t]
        if not fil.empty:
            with st.expander(f"{t}s ({len(fil)})"):
                for i, r in fil.iterrows():
                    ra, rb = st.columns([3, 1])
                    ra.write(f"**{r['Cliente']}** ({r['Cierre Estimado'].strftime('%d/%m/%Y')})")
                    nh = rb.selectbox("Mover", opciones_status, index=opciones_status.index(r['Status']), key=f"h_{r['ID']}")
                    if nh != r['Status']:
                        df.loc[df['ID'] == r['ID'], 'Status'] = nh
                        df.loc[df['ID'] == r['ID'], 'Último Movimiento'] = pd.to_datetime(date.today())
                        guardar_datos(df); st.rerun()
