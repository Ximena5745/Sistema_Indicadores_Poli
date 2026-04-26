import streamlit as st
import pandas as pd
from streamlit_app.components.cmi_tabs.modal_ficha import render_modal_ficha

def render_tab_alertas(df):
    st.markdown("### Centro de Alertas y Notificaciones")
    if df.empty:
        st.info("No hay datos para procesar.")
        return
        
    # Filtrar directamente los datos oficiales de SGIND
    if "Nivel de cumplimiento" not in df.columns:
        st.warning("El dataset no contiene la columna 'Nivel de cumplimiento'.")
        return
        
    df_alertas = df[df["Nivel de cumplimiento"].isin(["Peligro", "Alerta"])].copy()
    
    if df_alertas.empty:
        st.success("🎉 ¡Excelente! No hay alertas activas (Peligro o Alerta) en este periodo.")
        return
        
    # Tarjetas resumen de severidad
    conteo = df_alertas["Nivel de cumplimiento"].value_counts().to_dict()
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div style="background-color: #FFCDD2; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h3 style="margin:0; color: #C62828;">{conteo.get('Peligro', 0)}</h3>
            <span style="color: #C62828; font-weight: bold;">En Peligro Crítico (< 80%)</span>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style="background-color: #FEF3D0; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h3 style="margin:0; color: #F9A825;">{conteo.get('Alerta', 0)}</h3>
            <span style="color: #F9A825; font-weight: bold;">En Alerta (80% - 99%)</span>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    
    # Filtros para la tabla de alertas
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        sel_sev = st.selectbox("Filtrar por Nivel", ["Todos", "Peligro", "Alerta"])
    with col_f2:
        lineas_disp = ["Todas"] + sorted(df_alertas["Linea"].dropna().astype(str).unique().tolist())
        sel_linea = st.selectbox("Filtrar por Línea", lineas_disp)
        
    df_vista = df_alertas.copy()
    if sel_sev != "Todos":
        df_vista = df_vista[df_vista["Nivel de cumplimiento"] == sel_sev]
    if sel_linea != "Todas":
        df_vista = df_vista[df_vista["Linea"] == sel_linea]
        
    st.markdown("#### Matriz de Alertas")
    
    if df_vista.empty:
        st.info("No hay alertas que coincidan con los filtros.")
        return
        
    # Navegación a la ficha desde alertas (usando modal)
    sel_alerta = st.selectbox("Seleccionar Indicador para Ver Detalle (Modal):", [""] + df_vista["Indicador"].tolist(), key="tab_alerta_ficha_sel")
    if sel_alerta:
        ind_data = df_vista[df_vista["Indicador"] == sel_alerta].iloc[0]
        if st.button(f"Abrir Ficha de Alerta: {sel_alerta}", type="primary"):
            render_modal_ficha(ind_data)
            
    # Mostrar dataframe con columnas seleccionadas
    cols_mostrar = ["Id", "Indicador", "Linea", "Meta", "Ejecucion", "cumplimiento_pct", "Nivel de cumplimiento"]
    df_tabla = df_vista[[c for c in cols_mostrar if c in df_vista.columns]]
    
    st.dataframe(
        df_tabla,
        use_container_width=True,
        hide_index=True
    )
