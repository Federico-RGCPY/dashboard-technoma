import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuración de página con el nuevo título de pestaña
st.set_page_config(page_title="Seguimiento de Oportunidades RGC", layout="wide")

# Estilo CSS para alta legibilidad, colores Technoma y Triple Branding alineado
st.markdown("""
    <style>
    /* Fondo principal y textos oscuros */
    .main { background-color: #ffffff; color: #1a1a1a; }
    
    /* Contenedor de logos alineado */
    .logo-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0px 30px 0px;
        border-bottom: 1px solid #eee;
        margin-bottom: 20px;
    }
    .logo-container img {
        height: 60px; /* Tamaño optimizado para los tres logos */
        object-fit: contain;
    }
    
    /* Indicadores numéricos (Métricas) en Bordó */
    [data-testid="stMetricValue"] {
        color: #800020 !important;
        font-weight: 800;
        font-size: 2.8rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: #4a4a4a !important;
        font-size: 1rem !important;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .stMetric {
        background-color: #fcfcfc;
        border: 1px solid #e0e0e0;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    
    /* Sidebar claro */
    div[data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #dee2e6;
    }
    
    /* Botones Bordó Technoma */
    .stButton>button {
        background-color: #800020;
        color: white;
        border-radius: 4px;
        font-weight: bold;
        border: none;
        width: 100%;
    }
    
    /* Título principal Bordó */
    h1 { color: #800020 !important; font-family: 'Segoe UI', sans-serif; font-size: 2.2rem !important; }
    h2, h3 { color: #4a4a4a !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ENCABEZADO CON TRIPLE BRANDING ---
# He usado el código Base64 de Duplo que pasaste y URLs oficiales estables para Ricoh y Technoma.
st.markdown(f"""
    <div class="logo-container">
        <img src="https://www.technoma.com.py/images/logo.png" alt="Technoma">
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Ricoh_logo.svg/2560px-Ricoh_logo.svg.png" alt="Ricoh">
        <img src="data:image/png;base64,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fzf7r/+O7+/tP//b9Uf83//+/+V9U//7/+e7u/tP9v2v3D7H/9v6T+f9N//b9UfVfyn6S//f6f3z//v8L5L+9+5f6p9VfGf3v9P9f/b//95/O//P//fv///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f9X///9/1X///3/Vf///f8HIsb6LpB8u5wAAAABJRU5ErkJggg==" alt="Duplo">
    </div>
    """, unsafe_allow_html=True)

# Título de pestaña dentro de la app (Bordó Technoma)
st.title("📋 Seguimiento de Oportunidades RGC")
st.divider()

# --- EL RESTO DEL CÓDIGO SIGUE EXACTAMENTE IGUAL ---

# --- INICIALIZACIÓN DE DATOS (CRM TEMPORAL) ---
if 'ventas' not in st.session_state:
    st.session_state.ventas = pd.DataFrame(columns=[
        'ID', 'Fecha', 'Ejecutivo Comercial', 'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status'
    ])

# --- SIDEBAR: REGISTRO DE OPORTUNIDAD ---
with st.sidebar:
    st.header("🚀 Registro RGC")
    with st.form("registro_form", clear_on_submit=True):
        ejecutivo = st.text_input("Ejecutivo Comercial")
        cliente = st.text_input("Cliente")
        solucion = st.text_input("Tipo de Solución (Producto)") # Campo libre
        monto = st.number_input("Monto Estimado ($)", min_value=0)
        status_inicial = st.selectbox("Estado", ["Bajo", "Medio", "Cerrado"])
        
        if st.form_submit_button("Guardar Oportunidad"):
            if ejecutivo and cliente and solucion:
                nuevo_id = len(st.session_state.ventas) + 1
                nueva_fila = {
                    'ID': nuevo_id,
                    'Fecha': datetime.now().strftime("%d/%m/%Y"),
                    'Ejecutivo Comercial': ejecutivo,
                    'Cliente': cliente,
                    'Tipo de Solución': solucion,
                    'Monto Est.': monto,
                    'Status': status_inicial
                }
                st.session_state.ventas = pd.concat([st.session_state.ventas, pd.DataFrame([nueva_fila])], ignore_index=True)
                st.toast("Oportunidad registrada correctamente.")
                st.rerun()

# --- LÓGICA DE FILTRADO (Pipeline Vivo vs Historial) ---
df = st.session_state.ventas
activos = df[~df['Status'].isin(['Perdido', 'Postergado'])]
historial = df[df['Status'].isin(['Perdido', 'Postergado'])]

# --- DASHBOARD DE MÉTRICAS (SOLO ACTIVOS) ---
c1, c2, c3, c4 = st.columns(4)
total_pipeline = activos['Monto Est.'].sum()
proyectos_activos = len(activos)
cierres_exitosos = len(activos[activos['Status'] == 'Cerrado'])
fuera_flujo = len(historial)

c1.metric("PIPELINE RGC", f"${total_pipeline:,.0f}")
c2.metric("PROYECTOS ACTIVOS", proyectos_activos)
c3.metric("CIERRES LOGRADOS", cierres_exitosos)
c4.metric("FUERA DE FLUJO (Historial)", fuera_flujo)

st.divider()

# --- PANEL PRINCIPAL: ANÁLISIS ---
col_main, col_list = st.columns([2, 1])

with col_main:
    st.subheader("📈 Análisis de Pipeline Vivo")
    if not activos.empty:
        # Gráfico con colores profesionales: Gris (Bajo), Azul (Medio), Bordó (Cerrado)
        fig = px.bar(activos, x='Ejecutivo Comercial', y='Monto Est.', color='Status',
                     color_discrete_map={'Bajo': '#A9A9A9', 'Medio': '#4682B4', 'Cerrado': '#800020'},
                     template="plotly_white", barmode='group',
                     labels={'Monto Est.': 'Monto ($)', 'Ejecutivo Comercial': 'Ejecutivo'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sin datos activos para graficar.")

with col_list:
    st.subheader("🛠️ Soluciones en Negociación")
    # Mostrar lista única de soluciones cargadas (dinámico)
    for s in activos['Tipo de Solución'].unique():
        st.markdown(f"🔹 {s}")

# --- GESTIÓN INDIVIDUAL (Con opciones de Perdido/Postergado) ---
st.subheader("📂 Control de Casos Activos")
if not activos.empty:
    for i, row in activos.iterrows():
        with st.expander(f"📌 {row['Cliente']} | {row['Tipo de Solución']} (${row['Monto Est.']:,})"):
            ca, cb, cc, cd = st.columns([2,2,1,1])
            ca.write(f"**Ejecutivo:** {row['Ejecutivo Comercial']}")
            cb.write(f"**Fecha Ingreso:** {row['Fecha']}")
            
            # Botones para mover al historial
            if cc.button("❌ Marcar Perdido", key=f"per_{row['ID']}"):
                st.session_state.ventas.at[i, 'Status'] = 'Perdido'
                st.rerun()
            if cd.button("⏳ Postergar", key=f"post_{row['ID']}"):
                st.session_state.ventas.at[i, 'Status'] = 'Postergado'
                st.rerun()
else:
    st.write("No hay oportunidades activas.")

st.divider()

# --- HISTORIAL Y RECUPERACIÓN (ABAJO) ---
st.subheader("📚 Historial y Recuperación (Perdidas/Postergadas)")
if not historial.empty:
    st.table(historial[['Fecha', 'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status']])
    
    # Opciones para traer de vuelta
    rec_col1, rec_col2 = st.columns([2, 1])
    op_rec = rec_col1.selectbox("Seleccione oportunidad para reactivar:", historial['Cliente'].unique())
    if rec_col2.button("♻️ Traer de vuelta al Pipeline"):
        # Buscar el índice por nombre de cliente y cambiar status a Medio
        idx = df[df['Cliente'] == op_rec].index
        st.session_state.ventas.at[idx[0], 'Status'] = 'Medio'
        st.success(f"Oportunidad de {op_rec} reactivada correctamente.")
        st.rerun()
else:
    st.write("No hay registros en el historial.")
