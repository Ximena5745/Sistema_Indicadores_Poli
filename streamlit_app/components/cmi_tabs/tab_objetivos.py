import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_app.utils.cmi_helpers import linea_color

def render_tab_objetivos(df):
    st.markdown("### Objetivos e Indicadores")
    if df.empty:
        st.info("No hay datos para mostrar.")
        return
        
    st.markdown("#### Vista Jerárquica: Línea → Objetivo → Indicador")
    
    # Preparar datos para el sunburst
    df_sunburst = df.copy()
    # Si hay indicadores sin línea u objetivo, los rellenamos para evitar errores
    df_sunburst['Linea'] = df_sunburst['Linea'].fillna("Sin Línea")
    df_sunburst['Objetivo'] = df_sunburst['Objetivo'].fillna("Sin Objetivo")
    df_sunburst['Indicador'] = df_sunburst['Indicador'].fillna("Sin Nombre")
    df_sunburst['Nivel'] = df_sunburst['Nivel de cumplimiento'].fillna("Pendiente de reporte")
    
    fig_sunburst = px.sunburst(
        df_sunburst,
        path=['Linea', 'Objetivo', 'Indicador'],
        color='Linea',
        color_discrete_map={linea: linea_color(linea) for linea in df_sunburst['Linea'].unique()},
        maxdepth=2
    )
    fig_sunburst.update_layout(margin=dict(t=10, l=10, r=10, b=10))
    st.plotly_chart(fig_sunburst, use_container_width=True)
    
    st.markdown("#### Detalle por Objetivo")
    
    # Selector de línea y objetivo para la tabla interactiva
    col1, col2 = st.columns(2)
    with col1:
        lineas_disp = sorted(df['Linea'].dropna().unique().tolist())
        sel_linea = st.selectbox("Seleccione Línea (Tabla)", ["Todas"] + lineas_disp, key="tab_obj_linea")
        
    df_obj = df.copy()
    if sel_linea != "Todas":
        df_obj = df_obj[df_obj['Linea'] == sel_linea]
        
    with col2:
        objs_disp = sorted(df_obj['Objetivo'].dropna().unique().tolist())
        sel_obj = st.selectbox("Seleccione Objetivo (Tabla)", ["Todos"] + objs_disp, key="tab_obj_objetivo")
        
    if sel_obj != "Todos":
        df_obj = df_obj[df_obj['Objetivo'] == sel_obj]
        
    if df_obj.empty:
        st.info("No hay indicadores para la selección actual.")
        return
        
    # Renderizar tabla
    cols_tabla = ["Indicador", "Linea", "Objetivo", "Meta", "Ejecucion", "cumplimiento_pct", "Nivel de cumplimiento"]
    df_vista = df_obj[[c for c in cols_tabla if c in df_obj.columns]].copy()
    
    def format_nivel(nivel):
        if pd.isna(nivel) or nivel == "Pendiente de reporte":
            return "⚪ Pendiente"
        elif nivel == "Peligro":
            return "🔴 Peligro"
        elif nivel == "Alerta":
            return "🟠 Alerta"
        elif nivel == "Cumplimiento":
            return "🟢 Cumplimiento"
        elif nivel == "Sobrecumplimiento":
            return "🔵 Sobrecumplimiento"
        else:
            return f"⚪ {nivel}"
            
    if "Nivel de cumplimiento" in df_vista.columns:
        df_vista["Estado"] = df_vista["Nivel de cumplimiento"].apply(format_nivel)
        df_vista = df_vista.drop(columns=["Nivel de cumplimiento"])
        
    if "cumplimiento_pct" in df_vista.columns:
        df_vista["Cumplimiento %"] = df_vista["cumplimiento_pct"].round(1)
        df_vista = df_vista.drop(columns=["cumplimiento_pct"])
        
    st.dataframe(df_vista, use_container_width=True, hide_index=True)
