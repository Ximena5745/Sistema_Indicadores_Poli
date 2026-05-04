import streamlit as st
import pandas as pd
from streamlit_app.components.cmi_tabs.modal_ficha import render_modal_ficha
from streamlit_app.components.dashboard_components import render_alertas_criticas
from streamlit_app.utils.formatting import formatear_meta_ejecucion_df

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

    pct_col = (
        "cumplimiento_pct"
        if "cumplimiento_pct" in df_alertas.columns
        else ("Cumplimiento_pct" if "Cumplimiento_pct" in df_alertas.columns else None)
    )
    render_alertas_criticas(df_alertas, pct_col)
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
    df_tabla = df_vista[[c for c in cols_mostrar if c in df_vista.columns]].copy()

    ejec_col = "Ejecucion" if "Ejecucion" in df_tabla.columns else ("Ejecución" if "Ejecución" in df_tabla.columns else None)
    if "Meta" in df_tabla.columns and ejec_col is not None:
        df_tabla = formatear_meta_ejecucion_df(df_tabla, meta_col="Meta", ejec_col=ejec_col)

    if "cumplimiento_pct" in df_tabla.columns:
        def _fmt_pct(value):
            try:
                return f"{float(value):.1f}%"
            except Exception:
                return "—"

        df_tabla["cumplimiento_pct"] = df_tabla["cumplimiento_pct"].map(_fmt_pct)
    
    st.dataframe(
        df_tabla,
        use_container_width=True,
        hide_index=True
    )
