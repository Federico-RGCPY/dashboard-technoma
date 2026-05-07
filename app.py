import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import io

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="RGC - Dashboard de Oportunidades", layout="wide")

# URL de tu Sheet
URL_SHEET = "https://docs.google.com/spreadsheets/d/1L2kKpbx3u-bGehPZqce0Y7MVTKRK0fW9xEqkv5IZ2PQ/edit?usp=sharing"

# 2. ESTILO CSS PROFESIONAL (Color Guinda RGC)
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    [data-testid="stMetricValue"] { color: #800020 !important; font-weight: 800; font-size: 2.5rem; }
    .stMetric { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 20px; border-radius: 12px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    div[data-testid="stSidebar"] { background-color: #f1f3f5; }
    .stButton>button { border-radius: 5px; font-weight: bold; background-color: #800020; color: white; width: 100%; border: none; padding: 10px; }
    .stButton>button:hover { background-color: #a00020; color: white; }
    .alerta-roja { background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px; border-left: 6px solid #dc3545; margin-bottom: 15px; font-weight: bold; }
    .header-mes { background-color: #800020; color: white; padding: 10px 20px; border-radius: 8px; margin-top: 30px; font-size: 1.4rem; font-weight: bold; letter-spacing: 1px; }
    h1 { color: #800020 !important; font-family: 'Segoe UI', sans-serif; font-weight: 800 !important; }
    h3 { color: #495057; font-weight: 700; }
    .stExpander { border: 1px solid #dee2e6; border-radius: 10px; background-color: white; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 3. CONEXIÓN Y FUNCIONES DE DATOS
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        # ttl=0 para lectura en tiempo real sin caché
        df = conn.read(spreadsheet=URL_SHEET, ttl=0).dropna(how="all")
        # Asegurar formatos de fecha
        df['Cierre Estimado'] = pd.to_datetime(df['Cierre Estimado'], errors='coerce')
        df['Último Movimiento'] = pd.to_datetime(df['Último Movimiento'], errors='coerce')
        return df
    except:
        return pd.DataFrame(columns=['ID', 'Fecha Creación', 'Último Movimiento', 'Ejecutivo Comercial', 'Cliente', 'Tipo de Solución', 'Monto Est.', 'Status', 'Cierre Estimado'])

def guardar_datos(df_actualizado):
    # Convertir todo a string para evitar conflictos de tipos en Google
    df_save = df_actualizado.copy()
    df_save['Cierre Estimado'] = df_save['Cierre Estimado'].dt.strftime('%Y-%m-%d')
    df_save['Último Movimiento'] = df_save['Último Movimiento'].dt.strftime('%Y-%m-%d')
    conn.update(spreadsheet=URL_SHEET, data=df_save.astype(str))

# --- APP START ---
df = cargar_datos()

st.title("📋 Seguimiento Estratégico de Oportunidades")

# 4. SIDEBAR: REGISTRO Y FILTROS
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3209/3209265.png", width=80)
    st.header("Menú de Gestión")
    
    with st.form("registro_oportunidad", clear_on_submit=True):
        st.subheader("📝 Nueva Oportunidad")
        vendedor = st.text_input("Ejecutivo Comercial")
        cliente = st.text_input("Cliente")
        equipo = st.text_input("Equipo / Solución")
        monto = st.number_input("Monto Estimado ($)", min_value=0)
        cierre = st.date_input("Fecha Estimada de Cierre", min_value=date.today())
        prioridad = st.selectbox("Status Inicial", ["Negociando", "Bajo", "Medio"])
        
        if st.form_submit_button("Registrar en Pipeline"):
            if vendedor and cliente and equipo:
                nueva_fila = pd.DataFrame([{
                    "ID": str(int(datetime.now().timestamp())),
                    "Fecha Creación": date.today().strftime('%Y-%m-%d'),
                    "Último Movimiento": pd.to_datetime(date.today()),
                    "Ejecutivo Comercial": vendedor,
                    "Cliente": cliente,
                    "Tipo de Solución": equipo,
                    "Monto Est.": monto,
                    "Status": prioridad,
                    "Cierre Estimado": pd.to_datetime(cierre)
                }])
                df = pd.concat([df, nueva_fila], ignore_index=True)
                guardar_datos(df)
                st.success("¡Oportunidad Sincronizada!")
                st.rerun()
    
    st.divider()
    # Botón para descargar Excel de respaldo
    if not df.empty:
        towrite = io.BytesIO()
        df.to_excel(towrite, index=False, engine='xlsxwriter')
        st.download_button(label="📥 Descargar Reporte Excel", data=towrite.getvalue(), file_name=f"Reporte_RGC_{date.today()}.xlsx", mime="application/vnd.ms-excel")

# 5. PROCESAMIENTO PARA VISUALIZACIÓN
if not df.empty:
    # Clasificación de oportunidades
    activos_mask = df['Status'].isin(['Negociando', 'Bajo', 'Medio'])
    activos = df[activos_mask].copy()
    historial = df[~activos_mask].copy()

    # MÉTRICAS TOP (KPIs)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        total_monto = pd.to_numeric(activos['Monto Est.'], errors='coerce').sum()
        st.metric("PIPELINE VALOR", f"${total_monto:,.0f}")
    with m2:
        st.metric("OPORTUNIDADES", len(activos))
    with m3:
        ganados = df[df['Status'] == "Ganado"]
        monto_ganado = pd.to_numeric(ganados['Monto Est.'], errors='coerce').sum()
        st.metric("CIERRES GANADOS", f"${monto_ganado:,.0f}")
    with m4:
        equipos_distintos = activos['Tipo de Solución'].nunique()
        st.metric("TIPOS DE EQUIPOS", equipos_distintos)

    st.divider()

    # 6. PANEL DE CONTROL (PIPELINE POR MESES)
    col_main, col_summary = st.columns([3, 1])

    with col_main:
        st.subheader("📅 Cronograma de Cierres Próximos")
        
        if not activos.empty:
            # Crear etiqueta Mes Año para agrupar
            activos['Mes_Txt'] = activos['Cierre Estimado'].dt.strftime('%B %Y')
            activos = activos.sort_values(by='Cierre Estimado')
            
            for mes in activos['Mes_Txt'].unique():
                st.markdown(f'<div class="header-mes">{mes.upper()}</div>', unsafe_allow_html=True)
                
                items_mes = activos[activos['Mes_Txt'] == mes]
                for i, row in items_mes.iterrows():
                    # Cálculo de Alarma de Seguimiento (10 días)
                    dias_inactivo = (date.today() - row['Último Movimiento'].date()).days
                    
                    # Título del Expander con información clave
                    titulo_card = f"📌 {row['Cliente']} | {row['Tipo de Solución']} | ${row['Monto Est.']:,.0f}"
                    
                    with st.expander(titulo_card):
                        if dias_inactivo >= 10:
                            st.markdown(f'<div class="alerta-roja">🚨 ALERTA: {dias_inactivo} días sin actualización de estado.</div>', unsafe_allow_html=True)
                        
                        c_info, c_status = st.columns([2, 1])
                        
                        with c_info:
                            st.write(f"👤 **Vendedor:** {row['Ejecutivo Comercial']}")
                            st.write(f"📅 **Fecha de Cierre:** {row['Cierre Estimado'].strftime('%d/%m/%Y')}")
                            st.write(f"⏳ **Días en Negociación:** {(date.today() - pd.to_datetime(row['Fecha Creación']).date()).days} días")

                        with c_status:
                            opciones = ["Negociando", "Bajo", "Medio", "Ganado", "Perdido", "Postergado"]
                            # Manejar index por si el status no está en la lista
                            try:
                                idx_st = opciones.index(row['Status'])
                            except:
                                idx_st = 0
                                
                            nuevo_st = st.selectbox("Cambiar Estado", opciones, index=idx_st, key=f"sel_{row['ID']}")
                            
                            if nuevo_st != row['Status']:
                                # Actualizar en el DF principal
                                idx_global = df[df['ID'] == row['ID']].index[0]
                                df.at[idx_global, 'Status'] = nuevo_st
                                df.at[idx_global, 'Último Movimiento'] = pd.to_datetime(date.today())
                                guardar_datos(df)
                                st.toast(f"Actualizado: {row['Cliente']}")
                                st.rerun()
        else:
            st.info("No hay oportunidades activas en este momento.")

    with col_summary:
        st.subheader("📊 Resumen")
        
        # Resumen de Equipos en negociación
        if not activos.empty:
            st.markdown("**Inventario en Pipeline:**")
            resumen_eq = activos['Tipo de Solución'].value_counts()
            for eq, cant in resumen_eq.items():
                st.write(f"✅ **{cant}x** {eq}")
        
        st.divider()
        
        # Resumen por Vendedor
        st.markdown("**Desempeño por Ejecutivo:**")
        vendedores = activos.groupby('Ejecutivo Comercial')['Monto Est.'].sum().sort_values(ascending=False)
        for vend, monto in vendedores.items():
            st.write(f"👤 **{vend}:** ${monto:,.0f}")

    # 7. SECCIÓN DE HISTORIAL (GANADOS/PERDIDOS)
    st.divider()
    with st.expander("📂 Ver Historial de Resultados (Ganados, Perdidos, Postergados)"):
        if not historial.empty:
            # Mostrar tabla limpia
            st.dataframe(historial[['Cliente', 'Ejecutivo Comercial', 'Tipo de Solución', 'Monto Est.', 'Status', 'Cierre Estimado']], use_container_width=True)
        else:
            st.write("No hay registros en el historial todavía.")

else:
    st.info("👋 Bienvenido. Para comenzar, registra la primera oportunidad en el panel lateral.")
    st.image("https://cdn-icons-png.flaticon.com/512/4076/4076402.png", width=200)
