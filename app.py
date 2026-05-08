import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
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

# Estilos CSS para personalización visual
st.markdown("""
    <style>
    .header-mes { background-color: #800020; color: white; padding: 12px; border-radius: 8px; margin-top: 25px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; }
    .stMetric { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    h1 { color: #800020 !important; font-weight: 800; }
    .stButton>button { background-color: #800020; color: white; border-radius: 5px; width: 100%; }
    .stExpander { border: 1px solid #dee2e6; border-radius: 10px; background-color: white; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN Y FUNCIONES DE DATOS
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        # Leemos sin caché para ver cambios al instante
        df = conn.read(spreadsheet=URL_SHEET, ttl=0).dropna(how="all")
        # Aseguramos formatos correctos
        df['Cierre Estimado'] = pd.to_datetime(df['Cierre Estimado'], errors='coerce')
        df['Último Movimiento'] = pd.to_datetime(df['Último Movimiento'], errors='coerce')
        df['Monto Est.'] = pd.to_numeric(df['Monto Est.'], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame(columns=['ID', 'Fecha Creación', 'Último Movimiento', 'Ejecutivo Comercial', 'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status', 'Cierre Estimado'])

def guardar_datos(df_save):
    # Formateamos antes de enviar a Google Sheets
    df_to_push = df_save.copy()
    df_to_push['Cierre Estimado'] = df_to_push['Cierre Estimado'].dt.strftime('%Y-%m-%d')
    df_to_push['Último Movimiento'] = df_to_push['Último Movimiento'].dt.strftime('%Y-%m-%d')
    conn.update(spreadsheet=URL_SHEET, data=df_to_push.astype(str))

# --- INICIO DE LA LÓGICA DE LA APP ---
df = cargar_datos()
opciones_status = ["Negociando", "Bajo", "Medio", "Ganado", "Perdido", "Postergado"]

st.title("📋 Pipeline Estratégico RGC")

# 3. BARRA LATERAL (REGISTRO Y EXPORTACIÓN)
with st.sidebar:
    st.header("📝 Registro de Oportunidad")
    with st.form("registro_nuevo", clear_on_submit=True):
        vendedor = st.text_input("Ejecutivo Comercial")
        cliente = st.text_input("Cliente / Empresa")
        equipo = st.text_input("Equipo / Solución")
        monto = st.number_input("Monto Estimado ($)", min_value=0.0, format="%.2f")
        cierre_form = st.date_input("Fecha Estimada de Cierre")
        
        if st.form_submit_button("Registrar en Pipeline"):
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
                st.success("¡Oportunidad registrada!")
                st.rerun()
    
    if not df.empty:
        st.divider()
        towrite = io.BytesIO()
        df.to_excel(towrite, index=False, engine='xlsxwriter')
        st.download_button(label="📥 Descargar Base de Datos (Excel)", data=towrite.getvalue(), file_name=f"Pipeline_RGC_{date.today()}.xlsx")

# 4. MÉTRICAS PRINCIPALES (KPIs)
activos = df[df['Status'].isin(["Negociando", "Bajo", "Medio"])].copy()
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("PIPELINE ACTIVO", f"${activos['Monto Est.'].sum():,.0f}")
with m2:
    st.metric("OPORTUNIDADES", len(activos))
with m3:
    st.metric("EQUIPOS EN NEG.", activos['Tipo de Solución'].nunique())

st.divider()

# 5. CUERPO PRINCIPAL: GESTIÓN Y GRÁFICOS
col_izq, col_der = st.columns([2, 1.3])

with col_izq:
    st.subheader("🚀 Seguimiento de Clientes")
    if not activos.empty:
        # Preparar visualización por meses en español
        activos['Mes_Nombre'] = activos['Cierre Estimado'].dt.strftime('%B')
        activos['Anio'] = activos['Cierre Estimado'].dt.strftime('%Y')
        activos['Mes_ES'] = activos['Mes_Nombre'].map(MESES_ES) + " " + activos['Anio']
        
        meses_ordenados = activos.sort_values('Cierre Estimado')['Mes_ES'].unique()
        
        for mes in meses_ordenados:
            st.markdown(f'<div class="header-mes">{mes}</div>', unsafe_allow_html=True)
            items = activos[activos['Mes_ES'] == mes]
            
            for i, row in items.iterrows():
                # Fecha legible DD/MM/AAAA
                f_cierre_vis = row['Cierre Estimado'].strftime('%d/%m/%Y')
                
                with st.expander(f"📌 {row['Cliente']} | {row['Tipo de Solución']} (${row['Monto Est.']:,.0f})"):
                    with st.form(key=f"form_edit_{row['ID']}"):
                        c1, c2 = st.columns(2)
                        with c1:
                            edit_ejecutivo = st.text_input("Ejecutivo", value=row['Ejecutivo Comercial'])
                            edit_monto = st.number_input("Monto ($)", value=float(row['Monto Est.']))
                        with c2:
                            edit_fecha = st.date_input("Fecha de Cierre", value=row['Cierre Estimado'].date())
                            edit_status = st.selectbox("Estado", opciones_status, index=opciones_status.index(row['Status']))
                        
                        if st.form_submit_button("Guardar Cambios"):
                            idx_global = df[df['ID'] == row['ID']].index[0]
                            df.at[idx_global, 'Ejecutivo Comercial'] = edit_ejecutivo
                            df.at[idx_global, 'Monto Est.'] = edit_monto
                            df.at[idx_global, 'Cierre Estimado'] = pd.to_datetime(edit_fecha)
                            df.at[idx_global, 'Status'] = edit_status
                            df.at[idx_global, 'Último Movimiento'] = pd.to_datetime(date.today())
                            guardar_datos(df)
                            st.rerun()
    else:
        st.info("No hay oportunidades activas registradas.")

with col_der:
    st.subheader("📊 Gráfico de Desempeño")
    if not activos.empty:
        # Gráfico de Dona Moderno con etiquetas externas
        df_graf = activos.groupby('Ejecutivo Comercial')['Monto Est.'].sum().reset_index()
        
        fig = px.pie(
            df_graf, values='Monto Est.', names='Ejecutivo Comercial', 
            hole=0.5, color_discrete_sequence=px.colors.qualitative.Bold
        )
        
        fig.update_traces(
            textposition='outside', 
            textinfo='label+percent',
            textfont_size=13,
            pull=[0.05] * len(df_graf),
            marker=dict(line=dict(color='#FFFFFF', width=2))
        )
        
        fig.update_layout(
            showlegend=False,
            margin=dict(t=30, b=30, l=80, r=80),
            height=450
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        st.markdown("**Resumen por Vendedor:**")
        for idx, r in df_graf.sort_values(by='Monto Est.', ascending=False).iterrows():
            st.write(f"👤 {r['Ejecutivo Comercial']}: **${r['Monto Est.']:,.0f}**")
        
        st.divider()
        st.markdown("**Mezcla de Equipos:**")
        por_equipo = activos['Tipo de Solución'].value_counts()
        for eq, cant in por_equipo.items():
            st.write(f"🛠️ {cant}x {eq}")
    else:
        st.write("Registra datos para generar gráficos.")

# 6. ARCHIVO HISTÓRICO (RECUPERACIÓN)
st.divider()
st.subheader("📂 Archivo Histórico")
historico = df[~df['Status'].isin(["Negociando", "Bajo", "Medio"])].copy()

if not historico.empty:
    for st_tipo in ["Postergado", "Ganado", "Perdido"]:
        filtro = historico[historico['Status'] == st_tipo]
        if not filtro.empty:
            with st.expander(f"Ver {st_tipo}s ({len(filtro)})"):
                for i, row in filtro.iterrows():
                    col_t, col_s = st.columns([3, 1])
                    f_h = row['Cierre Estimado'].strftime('%d/%m/%Y')
                    col_t.write(f"**{row['Cliente']}** - {row['Tipo de Solución']} (Vendedor: {row['Ejecutivo Comercial']} | Cierre: {f_h})")
                    
                    nuevo_st_h = col_s.selectbox("Reactivar", opciones_status, index=opciones_status.index(row['Status']), key=f"hist_{row['ID']}")
                    if nuevo_st_h != row['Status']:
                        df.loc[df['ID'] == row['ID'], 'Status'] = nuevo_st_h
                        df.loc[df['ID'] == row['ID'], 'Último Movimiento'] = pd.to_datetime(date.today())
                        guardar_datos(df)
                        st.rerun()
else:
    st.write("El historial está vacío.")
