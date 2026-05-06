import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de Marca Technoma - Bordó y Gris Espacial
st.set_page_config(page_title="Technoma OS", layout="wide")

# Estilo CSS Personalizado (Tema Bordó Futurista)
st.markdown("""
    <style>
    .main { background-color: #1a0000; color: #f5f5f5; }
    .stMetric { 
        background-color: #2b0000; 
        border: 2px solid #800020; 
        padding: 20px; 
        border-radius: 12px; 
        box-shadow: 0 0 15px rgba(128, 0, 32, 0.4);
    }
    div[data-testid="stSidebar"] {
        background-color: #120000;
        border-right: 1px solid #800020;
    }
    .stButton>button {
        background-color: #800020;
        color: white;
        border-radius: 8px;
        border: none;
        width: 100%;
        font-weight: bold;
    }
    h1, h2, h3 { color: #f5f5f5 !important; font-family: 'Orbitron', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

st.title("🍷 Technoma Intelligence: Gestión Estratégica")

# --- LÓGICA DE DATOS ---
if 'ventas' not in st.session_state:
    st.session_state.ventas = pd.DataFrame(columns=['Ejecutivo Comercial', 'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status'])

# --- SIDEBAR: CARGA DE DATOS ---
with st.sidebar:
    st.header("⚡ Registro de Operación")
    with st.form("nueva_venta"):
        ejecutivo = st.text_input("Ejecutivo Comercial")
        cliente = st.text_input("Cliente")
        solucion = st.selectbox("Tipo de Solución", [
            "Ricoh Pro Z75 (Hoja B2+)", 
            "Serie Pro VC (Continua)", 
            "QuickLabel (Etiquetas)", 
            "Software de Automatización"
        ])
        monto = st.number_input("Monto Estimado ($)", min_value=0)
        status = st.select_slider("Estado de Negociación", options=["Bajo", "Medio", "Cerrado"])
        
        if st.form_submit_button("Sincronizar con Technoma"):
            if ejecutivo and cliente:
                nueva_fila = {
                    'Ejecutivo Comercial': ejecutivo, 
                    'Cliente': cliente, 
                    'Tipo de Solución': solucion, 
                    'Monto Est.': monto, 
                    'Status': status
                }
                st.session_state.ventas = pd.concat([st.session_state.ventas, pd.DataFrame([nueva_fila])], ignore_index=True)
                st.success("Operación registrada en el sistema.")
            else:
                st.error("Por favor complete Ejecutivo y Cliente.")

# --- DASHBOARD DINÁMICO ---
col1, col2, col3 = st.columns(3)
total_monto = st.session_state.ventas['Monto Est.'].sum()
proyectos_activos = len(st.session_state.ventas)
cerrados = len(st.session_state.ventas[st.session_state.ventas['Status'] == 'Cerrado'])

col1.metric("PIPELINE TOTAL", f"${total_monto:,}")
col2.metric("PROYECTOS EN CURSO", proyectos_activos)
col3.metric("NEGOCIOS CERRADOS", cerrados)

# Gráfico de Desempeño
if not st.session_state.ventas.empty:
    st.subheader("📊 Análisis de Rendimiento por Solución")
    fig = px.bar(st.session_state.ventas, x='Tipo de Solución', y='Monto Est.', color='Status', 
                 template="plotly_dark",
                 color_discrete_map={'Bajo': '#4a0000', 'Medio': '#800020', 'Cerrado': '#c00000'})
    fig.update_layout(paper_bgcolor="#1a0000", plot_bgcolor="#1a0000")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Registro de Operaciones")
    st.dataframe(st.session_state.ventas, use_container_width=True)
else:
    st.info("Sistema listo. Ingrese datos en el panel izquierdo para visualizar métricas.")
