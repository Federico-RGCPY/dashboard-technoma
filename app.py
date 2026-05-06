import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de Marca Technoma - Versión Alta Claridad
st.set_page_config(page_title="Technoma Intelligence", layout="wide")

# Estilo CSS - Fondo Claro y Contraste Bordó
st.markdown("""
    <style>
    /* Fondo principal y textos */
    .main { background-color: #ffffff; color: #1a1a1a; }
    
    /* Indicadores numéricos (Métricas) */
    [data-testid="stMetricValue"] {
        color: #800020 !important;
        font-weight: 800;
        font-size: 3rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: #4a4a4a !important;
        font-size: 1.1rem !important;
        letter-spacing: 1px;
    }
    .stMetric {
        background-color: #fcfcfc;
        border: 1px solid #e0e0e0;
        padding: 25px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    
    /* Sidebar */
    div[data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #dee2e6;
    }
    
    /* Botones */
    .stButton>button {
        background-color: #800020;
        color: white;
        border-radius: 4px;
        padding: 10px;
        font-weight: bold;
        border: none;
    }
    
    /* Títulos */
    h1, h2, h3 { color: #800020 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Technoma Intelligence")
st.markdown("### Control de Gestión y Pipeline de Soluciones")

# --- LÓGICA DE DATOS ---
if 'ventas' not in st.session_state:
    # Datos iniciales vacíos
    st.session_state.ventas = pd.DataFrame(columns=['Ejecutivo Comercial', 'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status'])

# --- SIDEBAR: REGISTRO ---
with st.sidebar:
    st.header("🖊️ Nueva Oportunidad")
    with st.form("registro_form"):
        ejecutivo = st.text_input("Nombre del Ejecutivo Comercial")
        cliente = st.text_input("Nombre del Cliente")
        solucion = st.text_input("Tipo de Solución (Producto)") # Campo libre personalizado
        monto = st.number_input("Monto Estimado ($)", min_value=0)
        status = st.select_slider("Estado de Negociación", options=["Bajo", "Medio", "Cerrado"])
        
        submit = st.form_submit_button("Registrar en Pipeline")
        
        if submit:
            if ejecutivo and cliente and solucion:
                nueva_fila = {
                    'Ejecutivo Comercial': ejecutivo,
                    'Cliente': cliente,
                    'Tipo de Solución': solucion,
                    'Monto Est.': monto,
                    'Status': status
                }
                st.session_state.ventas = pd.concat([st.session_state.ventas, pd.DataFrame([nueva_fila])], ignore_index=True)
                st.toast("Operación cargada con éxito")
            else:
                st.error("Por favor, complete todos los campos.")

# --- DASHBOARD DE MÉTRICAS ---
col1, col2, col3 = st.columns(3)
total_pipeline = st.session_state.ventas['Monto Est.'].sum()
conteo_proyectos = len(st.session_state.ventas)
total_cerrados = len(st.session_state.ventas[st.session_state.ventas['Status'] == 'Cerrado'])

col1.metric("PIPELINE TOTAL", f"${total_pipeline:,.0f}")
col2.metric("OPORTUNIDADES", conteo_proyectos)
col3.metric("CIERRES LOGRADOS", total_cerrados)

st.divider()

# --- LISTADO DINÁMICO DE EQUIPOS ---
if not st.session_state.ventas.empty:
    col_izq, col_der = st.columns([2, 1])
    
    with col_izq:
        st.subheader("📋 Detalle de Oportunidades")
        st.dataframe(st.session_state.ventas, use_container_width=True)
        
    with col_der:
        st.subheader("🛠️ Equipos en Negociación")
        # Mostrar lista única de soluciones cargadas
        lista_equipos = st.session_state.ventas['Tipo de Solución'].unique()
        for eq in lista_equipos:
            st.markdown(f"- **{eq}**")
            
    # Gráfico de barras con colores contrastados
    st.subheader("📈 Volumen por Ejecutivo")
    fig = px.bar(st.session_state.ventas, 
                 x='Ejecutivo Comercial', 
                 y='Monto Est.', 
                 color='Status',
                 color_discrete_map={'Bajo': '#FFC107', 'Medio': '#E91E63', 'Cerrado': '#800020'},
                 template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("El sistema está a la espera de la carga de la primera oportunidad comercial.")
