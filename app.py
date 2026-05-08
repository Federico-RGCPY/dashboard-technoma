import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import io

# 1. CONFIGURACIÓN
st.set_page_config(page_title="RGC Dashboard VIP", layout="wide")
URL_SHEET = "https://docs.google.com/spreadsheets/d/1L2kKpbx3u-bGehPZqce0Y7MVTKRK0fW9xEqkv5IZ2PQ/edit?usp=sharing"

# Traducción de meses
MESES_ES = {
    "January": "Enero", "February": "Febrero", "March": "Marzo", "April": "Abril",
    "May": "Mayo", "June": "Junio", "July": "Julio", "August": "Agosto",
    "September": "Septiembre", "October": "Octubre", "November": "Noviembre", "December": "Diciembre"
}

# Estilos visuales
st.markdown("""
    <style>
    .header-mes { background-color: #800020; color: white; padding: 10px; border-radius: 8px; margin-top: 20px; font-weight: bold; text-transform: uppercase; }
    .stMetric { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 15px; border-radius: 10px; }
    h1 { color: #800020 !important; font-weight: 800; }
    .stButton>button { background-color: #800020; color: white; border-radius: 5px; }
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

st.title("📋 Pipeline Estratégico RGC")

# SIDEBAR
with st.sidebar:
    st.header("📝 Registro")
    with st.form("reg", clear_on_submit=True):
        vendedor = st.text_input("Ejecutivo")
        cliente = st.text_input("Cliente")
        equipo = st.text_input("Equipo")
        monto = st.number_input("Monto ($)", min_value=0.0)
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

# MÉTRICAS
activos = df[df['Status'].isin(["Negociando", "Bajo", "Medio"])].copy()
m1, m2, m3 = st.columns(3)
m1.metric("Pipeline Activo", f"${activos['Monto Est.'].sum():,.0f}")
m2.metric("Oportunidades", len(activos))
m3.metric("Equipos", activos['Tipo de Solución'].nunique())

st.divider()

# COLUMNAS PRINCIPALES
col_izq, col_der = st.columns([2, 1.2])

with col_izq:
    st.subheader("🚀 Gestión de Oportunidades")
    if not activos.empty:
        # Formateo de Meses en Español
        activos['Mes_Nombre'] = activos['Cierre Estimado'].dt.strftime('%B')
        activos['Anio'] = activos['Cierre Estimado'].dt.strftime('%Y')
        activos['Mes_ES'] = activos['Mes_Nombre'].map(MESES_ES) + " " + activos['Anio']
        
        meses_ordenados = activos.sort_values('Cierre Estimado')['Mes_ES'].unique()
        
        for mes in meses_ordenados:
            st.markdown(f'<div class="header-mes">{mes}</div>', unsafe_allow_html=True)
            items = activos[activos['Mes_ES'] == mes]
            for i, row in items.iterrows():
                fecha_formateada = row['Cierre Estimado'].strftime('%d/%m/%Y')
                
                with st.expander(f"📌 {row['Cliente']} | {row['Tipo de Solución']} (${row['Monto Est.']:,.0f})"):
                    # FORMULARIO DE EDICIÓN INTERNO
                    with st.form(key=f"edit_form_{row['ID']}"):
                        c1, c2 = st.columns(2)
                        with c1:
                            # EDITAR NOMBRE DEL EJECUTIVO
                            nuevo_ejecutivo = st.text_input("Editar Ejecutivo", value=row['Ejecutivo Comercial'])
                            # EDITAR MONTO
                            nuevo_monto = st.number_input("Editar Monto ($)", value=float(row['Monto Est.']))
                        
                        with c2:
                            # EDITAR FECHA
                            nueva_fecha = st.date_input("Cambiar Fecha Cierre", value=row['Cierre Estimado'].date())
                            # EDITAR STATUS
                            nuevo_st = st.selectbox("Estado", opciones_status, index=opciones_status.index(row['Status']))
                        
                        if st.form_submit_button("Aplicar Cambios"):
                            idx = df[df['ID'] == row['ID']].index[0]
                            df.at[idx, 'Ejecutivo Comercial'] = nuevo_ejecutivo
                            df.at[idx, 'Monto Est.'] = nuevo_monto
                            df.at[idx, 'Cierre Estimado'] = pd.to_datetime(nueva_fecha)
                            df.at[idx, 'Status'] = nuevo_st
                            df.at[idx, 'Último Movimiento'] = pd.to_datetime(date.today())
                            guardar_datos(df)
                            st.success("Cambios guardados!")
                            st.rerun()
    else:
        st.info("No hay oportunidades activas.")

with col_der:
    with col_der:
    st.subheader("📊 Desempeño")
    if not activos.empty:
        # Agrupamos por vendedor y sumamos montos
        df_vendedores = activos.groupby('Ejecutivo Comercial')['Monto Est.'].sum().reset_index()
        
        # Creamos el gráfico de Dona
        fig = px.pie(
            df_vendedores, 
            values='Monto Est.', 
            names='Ejecutivo Comercial', 
            hole=0.5,
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        
        # --- CONFIGURACIÓN PARA TEXTO EXTERIOR ---
        fig.update_traces(
            textposition='outside',        # Saca el texto de la torta
            textinfo='label+percent',      # Muestra nombre + porcentaje
            textfont_size=13,              # Tamaño de letra legible
            pull=[0.05] * len(df_vendedores), # Separa un poco las rebanadas para estética
            marker=dict(line=dict(color='#FFFFFF', width=2))
        )
        
        fig.update_layout(
            showlegend=False,              # Quitamos leyenda (ya está en las etiquetas)
            margin=dict(t=50, b=50, l=80, r=80), # Margen amplio para que no se corte el texto fuera
            height=450,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        st.markdown("**Resumen Numérico:**")
        # Listado ordenado de mayor a menor
        for i, r in df_vendedores.sort_values(by='Monto Est.', ascending=False).iterrows():
            st.write(f"👤 {r['Ejecutivo Comercial']}: **${r['Monto Est.']:,.0f}**")
        
        st.divider()
        st.markdown("**Mezcla de Equipos:**")
        por_equipo = activos['Tipo de Solución'].value_counts()
        for eq, cant in por_equipo.items():
            st.write(f"🛠️ {cant}x {eq}")
    else:
        st.write("Sin datos para graficar.")        
        # --- MEJORAS DE VISIBILIDAD ---
        fig.update_traces(
            textposition='inside', 
            textinfo='percent', # Dejamos solo el % adentro para no amontonar
            textfont_size=14,
            marker=dict(line=dict(color='#FFFFFF', width=2))
        )
        
        fig.update_layout(
            showlegend=True, # Activamos la leyenda para ver los nombres claramente
            legend=dict(
                orientation="h", # Leyenda horizontal
                yanchor="bottom",
                y=-0.5, # La bajamos un poco para que no choque con el gráfico
                xanchor="center",
                x=0.5,
                font=dict(size=14) # Nombres más grandes en la leyenda
            ),
            margin=dict(t=10, b=10, l=10, r=10),
            height=400 # Un poco más alto para que quepa la leyenda
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Resumen numérico debajo del gráfico para respaldo visual rápido
        st.write("**Detalle de Pipeline:**")
        for i, r in df_vendedores.sort_values(by='Monto Est.', ascending=False).iterrows():
            st.write(f"👤 {r['Ejecutivo Comercial']}: **${r['Monto Est.']:,.0f}**")
        
        st.divider()
        st.markdown("**Mezcla de Equipos:**")
        por_equipo = activos['Tipo de Solución'].value_counts()
        for eq, cant in por_equipo.items():
            st.write(f"🛠️ {cant}x {eq}")
    else:
        st.write("Sin datos para graficar.")

# SECCIÓN DE RECUPERACIÓN
st.subheader("📂 Archivo Histórico")
historico = df[~df['Status'].isin(["Negociando", "Bajo", "Medio"])].copy()
if not historico.empty:
    for st_tipo in ["Postergado", "Ganado", "Perdido"]:
        filtro = historico[historico['Status'] == st_tipo]
        if not filtro.empty:
            with st.expander(f"Ver {st_tipo}s ({len(filtro)})"):
                for i, row in filtro.iterrows():
                    col_txt, col_st = st.columns([3, 1])
                    fecha_h = row['Cierre Estimado'].strftime('%d/%m/%Y')
                    col_txt.write(f"**{row['Cliente']}** - {row['Tipo de Solución']} (Ejecutivo: {row['Ejecutivo Comercial']} | Cierre: {fecha_h})")
                    nuevo_st_h = col_st.selectbox("Reactivar", opciones_status, index=opciones_status.index(row['Status']), key=f"hist_{row['ID']}")
                    if nuevo_st_h != row['Status']:
                        df.loc[df['ID'] == row['ID'], 'Status'] = nuevo_st_h
                        df.loc[df['ID'] == row['ID'], 'Último Movimiento'] = pd.to_datetime(date.today())
                        guardar_datos(df)
                        st.rerun()
