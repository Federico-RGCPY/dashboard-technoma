import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración "Futurista"
st.set_page_config(page_title="Technoma OS", layout="wide")

# Estilo personalizado (CSS Inyectado)
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #00f2ff; }
    .stMetric { background-color: #161b22; border: 1px solid #00f2ff; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Technoma Intelligence: Pipeline de Ventas")

# --- LÓGICA DE DATOS ---
# Aquí simulamos una base de datos. En el futuro, esto se cargaría de un archivo.
if 'ventas' not in st.session_state:
    st.session_state.ventas = pd.DataFrame(columns=['Vendedor', 'Cliente', 'Equipo', 'Monto', 'Status'])

# --- SIDEBAR: INTERACTIVIDAD ---
with st.sidebar:
    st.header("🛸 Registro de Operación")
    with st.form("nueva_venta"):
        vendedor = st.selectbox("Agente", ["Carlos R.", "Ana M.", "Jorge L.", "Sofia P."])
        cliente = st.text_input("Nombre del Cliente")
        equipo = st.selectbox("Tecnología", ["Pro VC70000", "Pro VC80000", "Pro Z75", "QL-120", "QL-435"])
        monto = st.number_input("Monto Estimado ($)", min_value=0)
        status = st.select_slider("Status de Negociación", options=["Bajo", "Medio", "Cerrado"])
        
        if st.form_submit_button("Sincronizar Datos"):
            nueva_fila = {'Vendedor': vendedor, 'Cliente': cliente, 'Equipo': equipo, 'Monto': monto, 'Status': status}
            st.session_state.ventas = pd.concat([st.session_state.ventas, pd.DataFrame([nueva_fila])], ignore_index=True)
            st.success("¡Datos transmitidos al sistema!")

# --- DASHBOARD DINÁMICO ---
col1, col2, col3 = st.columns(3)
total_monto = st.session_state.ventas['Monto'].sum()
proyectos_activos = len(st.session_state.ventas)
cerrados = len(st.session_state.ventas[st.session_state.ventas['Status'] == 'Cerrado'])

col1.metric("PIPELINE TOTAL", f"${total_monto:,}")
col2.metric("PROYECTOS EN CURSO", proyectos_activos)
col3.metric("CONTRATOS CERRADOS", cerrados)

# Gráfico interactivo
if not st.session_state.ventas.empty:
    fig = px.bar(st.session_state.ventas, x='Vendedor', y='Monto', color='Status', 
                 title="Rendimiento por Agente", template="plotly_dark",
                 color_discrete_map={'Bajo': '#ff4b4b', 'Medio': '#ffa500', 'Cerrado': '#00ffcc'})
    st.plotly_chart(fig, use_container_width=True)

    # Tabla funcional
    st.subheader("📋 Registro de Operaciones")
    st.dataframe(st.session_state.ventas, use_container_width=True)
else:
    st.info("Esperando carga de datos iniciales...")
