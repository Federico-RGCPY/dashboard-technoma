with col_der:
    st.subheader("📊 Desempeño")
    if not activos.empty:
        # Agrupamos por vendedor y sumamos montos
        df_vendedores = activos.groupby('Ejecutivo Comercial')['Monto Est.'].sum().reset_index()
        
        # Creamos el gráfico con Plotly
        fig = px.pie(
            df_vendedores, 
            values='Monto Est.', 
            names='Ejecutivo Comercial', 
            hole=0.5,
            color_discrete_sequence=px.colors.qualitative.Bold # Colores más fuertes para mejor contraste
        )
        
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
