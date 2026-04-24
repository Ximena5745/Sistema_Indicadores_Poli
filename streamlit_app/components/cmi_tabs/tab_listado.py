import streamlit as st
import pandas as pd
import io

def render_tab_listado(df):
    st.markdown("### Listado Completo de Indicadores")
    if df.empty:
        st.info("No hay datos para mostrar.")
        return
        
    col1, col2, col3 = st.columns(3)
    with col1:
        search = st.text_input("Búsqueda Rápida", key="tab_list_search")
    with col2:
        estados_disp = ["Todos"] + df["Nivel de cumplimiento"].dropna().unique().tolist() if "Nivel de cumplimiento" in df.columns else ["Todos"]
        sel_estado = st.selectbox("Estado", estados_disp, key="tab_list_estado")
    with col3:
        # Export to excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Indicadores', index=False)
        
        st.download_button(
            label="📥 Exportar a Excel",
            data=buffer.getvalue(),
            file_name="indicadores_cmi.xlsx",
            mime="application/vnd.ms-excel",
            use_container_width=True
        )
        
    df_filtrado = df.copy()
    if search:
        df_filtrado = df_filtrado[df_filtrado["Indicador"].str.contains(search, case=False, na=False)]
    if sel_estado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Nivel de cumplimiento"] == sel_estado]
        
    if "cumplimiento_pct" in df_filtrado.columns:
        df_filtrado = df_filtrado.sort_values("cumplimiento_pct", ascending=False)
        
    cols_mostrar = ["Id", "Indicador", "Linea", "Objetivo", "Meta", "Ejecucion", "cumplimiento_pct", "Nivel de cumplimiento"]
    df_vista = df_filtrado[[c for c in cols_mostrar if c in df_filtrado.columns]].copy()
    
    # Paginate manually or let dataframe handle it
    # We will let st.dataframe handle scroll and column config
    
    st.markdown("Seleccione un indicador en la lista desplegable abajo para ver su ficha de detalle, o vaya directamente a la pestaña 'Ficha de Indicador'.")
    
    # In order to simulate "Click fila -> abre Ficha", we can provide a selectbox to pick the indicator to see in Ficha.
    sel_ind = st.selectbox("Seleccionar Indicador para Ver Ficha", [""] + df_vista["Indicador"].tolist(), key="tab_list_ficha_sel")
    if sel_ind:
        if st.button(f"Ir a Ficha: {sel_ind}", type="primary"):
            st.session_state["cmi_tab_selected"] = "Ficha de Indicador"
            st.session_state["cmi_ficha_indicador_sel"] = sel_ind
            st.rerun()
            
    st.dataframe(
        df_vista,
        use_container_width=True,
        hide_index=True,
        height=600
    )
