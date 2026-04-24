import streamlit as st
import pandas as pd
from streamlit_app.utils.cmi_helpers import calcular_alertas

def render_tab_alertas(df):
    st.markdown("### Centro de Alertas y Notificaciones")
    if df.empty:
        st.info("No hay datos para procesar.")
        return
        
    # Calcular alertas
    df_alertas = calcular_alertas(df)
    
    if df_alertas.empty:
        st.success("🎉 ¡Excelente! No hay alertas activas en este periodo.")
        return
        
    # Tarjetas resumen de severidad
    conteo = df_alertas["Severidad"].value_counts().to_dict()
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div style="background-color: #FFCDD2; padding: 15px; border-radius: 8px; text-align: center;">
            <h3 style="margin:0; color: #C62828;">{conteo.get('Crítica', 0)}</h3>
            <span style="color: #C62828;">Alertas Críticas</span>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style="background-color: #FEF3D0; padding: 15px; border-radius: 8px; text-align: center;">
            <h3 style="margin:0; color: #F9A825;">{conteo.get('Alta', 0) + conteo.get('Media', 0)}</h3>
            <span style="color: #F9A825;">Alertas Medias/Altas</span>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div style="background-color: #E8F5E9; padding: 15px; border-radius: 8px; text-align: center;">
            <h3 style="margin:0; color: #2E7D32;">{conteo.get('Baja', 0)}</h3>
            <span style="color: #2E7D32;">Alertas Bajas</span>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    
    # Filtros para la tabla de alertas
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        sel_sev = st.selectbox("Filtrar por Severidad", ["Todas", "Crítica", "Alta", "Media", "Baja"])
    with col_f2:
        sel_tipo = st.selectbox("Filtrar por Tipo", ["Todos"] + df_alertas["Tipo"].unique().tolist())
        
    df_vista = df_alertas.copy()
    if sel_sev != "Todas":
        df_vista = df_vista[df_vista["Severidad"] == sel_sev]
    if sel_tipo != "Todos":
        df_vista = df_vista[df_vista["Tipo"] == sel_tipo]
        
    st.markdown("#### Matriz de Alertas")
    
    if df_vista.empty:
        st.info("No hay alertas que coincidan con los filtros.")
        return
        
    # Navegación a la ficha desde alertas
    sel_alerta = st.selectbox("Seleccionar Indicador para ir a Ficha:", [""] + df_vista["Indicador"].tolist(), key="tab_alerta_ficha_sel")
    if sel_alerta:
        st.session_state["cmi_ficha_indicador_sel"] = sel_alerta
        st.success(f"✅ Alerta seleccionada. Haga clic en la pestaña superior **'Ficha de Indicador'** para ver el detalle de **{sel_alerta}**.")
            
    # Mostrar dataframe
    st.dataframe(
        df_vista,
        use_container_width=True,
        hide_index=True
    )
