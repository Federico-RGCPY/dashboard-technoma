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

# Estilos Originales RGC
st.markdown("""
    <style>
    .header-mes { background-color: #800020; color: white; padding: 12px; border-radius: 8px; margin-top: 25px; font-weight: bold; text-transform: uppercase; }
    .stMetric { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    h1 { color: #800020 !important; font-weight: 800; }
    .stButton>button { background-color: #800020; color: white; border-radius: 5px; width: 100%; }
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
    df_p = df_save.copy()
    df_p['Cierre Estimado'] = df_p['Cierre Estimado'].dt.strftime('%Y-%m-%d')
    df_p['Último Movimiento'] = df_p['Último Movimiento'].dt.strftime('%Y-%m-%d')
    conn.update(spreadsheet=URL_SHEET, data=df_p.astype(str))

# --- LÓGICA PRINCIPAL ---
df = cargar_datos()
opciones_status = ["Negociando", "Bajo", "Medio", "Ganado", "Perdido", "Postergado"]

st.title("📋 Pipeline Estratégico RGC")

# 3. SIDEBAR (REGISTRO)
with st.sidebar:
    st.header("📝 Registro")
    with st.form("reg_form", clear_on_submit=True):
        v = st.text_input("Ejecutivo")
        c = st.text_input("Cliente")
        e = st.text_input("Equipo")
        m = st.number_input("Monto ($)", min_value=0.0)
        d = st.date_input("Fecha Cierre")
        if st.form_submit_button("Registrar Oportunidad"):
            if v and c:
                nueva = pd.DataFrame([{"ID": str(int(datetime.now().timestamp())), "Fecha Creación": date.today().strftime('%Y-%m-%d'), "Último Movimiento": pd.to_datetime(date.today()), "Ejecutivo Comercial": v, "Cliente": c, "Tipo de Solución": e, "Monto Est.": m, "Status": "Negociando", "Cierre Estimado": pd.to_datetime(d)}])
                df = pd.concat([df, nueva], ignore_index=True); guardar_datos(df); st.rerun()

# 4. KPIs
activos = df[df['Status'].isin(["Negociando", "Bajo", "Medio"])].copy()
m1, m2, m3 = st.columns(3)
m1.metric("PIPELINE ACTIVO", f"${activos['Monto Est.'].sum():,.0f}")
m2.metric("OPORTUNIDADES", len(activos))
m3.metric("EQUIPOS", activos['Tipo de Solución'].nunique())

st.divider()
col_izq, col_der = st.columns([2, 1.3])

# GESTIÓN (IZQUIERDA)
with col_izq:
    st.subheader("🚀 Seguimiento de Cartera")
    if not activos.empty:
        activos['Mes_ES'] = activos['Cierre Estimado'].dt.strftime('%B').map(MESES_ES) + " " + activos['Cierre Estimado'].dt.strftime('%Y')
        for mes in activos.sort_values('Cierre Estimado')['Mes_ES'].unique():
            st.markdown(f'<div class="header-mes">{mes}</div>', unsafe_allow_html=True)
            for i, row in activos[activos['Mes_ES'] == mes].iterrows():
                with st.expander(f"📌 {row['Cliente']} | {row['Tipo de Solución']} (${row['Monto Est.']:,.0f})"):
                    with st.form(key=f"ed_{row['ID']}"):
                        ca, cb = st.columns(2)
                        nv = ca.text_input("Ejecutivo", value=row['Ejecutivo Comercial'])
                        nm = ca.number_input("Monto ($)", value=float(row['Monto Est.']))
                        nf = cb.date_input("Cierre", value=row['Cierre Estimado'].date())
                        ns = cb.selectbox("Estado", opciones_status, index=opciones_status.index(row['Status']))
                        if st.form_submit_button("Aplicar"):
                            idx = df[df['ID'] == row['ID']].index[0]
                            df.at[idx, 'Ejecutivo Comercial'], df.at[idx, 'Monto Est.'] = nv, nm
                            df.at[idx, 'Cierre Estimado'], df.at[idx, 'Status'] = pd.to_datetime(nf), ns
                            df.at[idx, 'Último Movimiento'] = pd.to_datetime(date.today())
                            guardar_datos(df); st.rerun()
    else: st.info("Sin registros activos.")

# GRÁFICO (DERECHA) - CAMBIO A DESEMPEÑO POR EJECUTIVO
with col_der:
    st.subheader("📊 Desempeño Ejecutivo") # <--- Cambio realizado aquí
    if not activos.empty:
        df_g = activos.groupby('Ejecutivo Comercial')['Monto Est.'].sum().reset_index().sort_values('Monto Est.')
        
        fig = go.Figure(go.Bar(
            y=df_g['Ejecutivo Comercial'],
            x=df_g['Monto Est.'],
            orientation='h',
            text=df_g['Monto Est.'].apply(lambda x: f"${x:,.0f}"),
            textposition='outside',
            marker=dict(
                color=df_g['Monto Est.'],
                colorscale='YlOrRd', 
                line=dict(color='#333', width=2) 
            )
        ))

        fig.update_layout(
            showlegend=False,
            height=500,
            xaxis_title="Pipeline ($)",
            yaxis_title="",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=20, b=20, l=100, r=60),
            xaxis=dict(showgrid=True, gridcolor='lightgrey'),
            bargap=0.3 
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        st.markdown("**Resumen de Ejecución:**")
        for idx, r in df_g.sort_values(by='Monto Est.', ascending=False).iterrows():
            st.write(f"👤 {r['Ejecutivo Comercial']}: **${r['Monto Est.']:,.0f}**")
    else: st.write("No hay datos activos.")

# 5. HISTÓRICO
st.divider()
st.subheader("📂 Archivo Histórico")
hist = df[~df['Status'].isin(["Negociando", "Bajo", "Medio"])].copy()
if not hist.empty:
    for t in ["Postergado", "Ganado", "Perdido"]:
        fil = hist[hist['Status'] == t]
        if not fil.empty:
            with st.expander(f"Ver {t}s ({len(fil)})"):
                for i, r in fil.iterrows():
                    ra, rb = st.columns([3, 1])
                    f_v = r['Cierre Estimado'].strftime('%d/%m/%Y')
                    ra.write(f"**{r['Cliente']}** - {r['Tipo de Solución']} ({f_v})")
                    nh = rb.selectbox("Reactivar", opciones_status, index=opciones_status.index(r['Status']), key=f"h_{r['ID']}")
                    if nh != r['Status']:
                        df.loc[df['ID'] == r['ID'], 'Status'] = nh
                        df.loc[df['ID'] == r['ID'], 'Último Movimiento'] = pd.to_datetime(date.today())
                        guardar_datos(df); st.rerun()
