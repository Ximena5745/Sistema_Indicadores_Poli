import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_app.utils.cmi_helpers import linea_color
from streamlit_app.components.cmi_tabs.modal_ficha import render_modal_ficha
from services.strategic_indicators import load_cierres

def _render_subtab_resumen(df_linea, linea, color):
    col1, col2, col3 = st.columns(3)
    cump = df_linea["cumplimiento_pct"].mean()
    if pd.isna(cump): cump = 0
    n_ind = len(df_linea)
    n_obj = df_linea["Objetivo"].nunique()
    
    # HTML cards for subtab
    st.markdown(f"""
    <div style="display: flex; gap: 15px; margin-bottom: 20px;">
        <div style="flex: 1; background-color: #F8F9FA; border-top: 4px solid {color}; padding: 15px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <p style="margin: 0; font-size: 0.9rem; color: #555;">Cumplimiento Promedio</p>
            <h3 style="margin: 0; color: {color};">{cump:.1f}%</h3>
        </div>
        <div style="flex: 1; background-color: #F8F9FA; border-top: 4px solid #1A3A5C; padding: 15px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <p style="margin: 0; font-size: 0.9rem; color: #555;">Objetivos Estratégicos</p>
            <h3 style="margin: 0; color: #1A3A5C;">{n_obj}</h3>
        </div>
        <div style="flex: 1; background-color: #F8F9FA; border-top: 4px solid #43A047; padding: 15px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <p style="margin: 0; font-size: 0.9rem; color: #555;">Total Indicadores PDI</p>
            <h3 style="margin: 0; color: #43A047;">{n_ind}</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sunburst Chart for this Line
    df_sunburst = df_linea.copy()
    df_sunburst['Objetivo'] = df_sunburst['Objetivo'].fillna("Sin Objetivo")
    df_sunburst['Indicador'] = df_sunburst['Indicador'].fillna("Sin Nombre")
    
    fig_sunburst = px.sunburst(
        df_sunburst,
        path=['Objetivo', 'Indicador'],
        color_discrete_sequence=[color, "#E1E1E1"],
        maxdepth=2,
        title=f"Distribución de Objetivos - {linea}"
    )
    fig_sunburst.update_layout(margin=dict(t=30, l=10, r=10, b=10), height=300)
    st.plotly_chart(fig_sunburst, use_container_width=True, key=f"sunburst_{linea}")

def _render_subtab_objetivos(df_linea, linea):
    st.markdown(f"**Indicadores asociados a {linea}**")
    
    # Filtro opcional por objetivo
    objs_disp = ["Todos"] + sorted(df_linea['Objetivo'].dropna().unique().tolist())
    sel_obj = st.selectbox("Filtrar por Objetivo:", objs_disp, key=f"obj_sel_{linea}")
    
    df_vista = df_linea.copy()
    if sel_obj != "Todos":
        df_vista = df_vista[df_vista['Objetivo'] == sel_obj]
        
    cols_tabla = ["Id", "Indicador", "Objetivo", "Meta", "Ejecucion", "cumplimiento_pct", "Nivel de cumplimiento"]
    df_tabla = df_vista[[c for c in cols_tabla if c in df_vista.columns]].copy()
    
    # Selector y botón Modal
    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        sel_ind = st.selectbox("Seleccionar Indicador para Ver Ficha:", [""] + df_tabla["Indicador"].tolist(), key=f"ficha_sel_{linea}")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if sel_ind:
            ind_data = df_vista[df_vista["Indicador"] == sel_ind].iloc[0]
            if st.button(f"Abrir Ficha Técnica", type="primary", key=f"btn_ficha_{linea}"):
                render_modal_ficha(ind_data)
                
    # Aplicar Inyección Estética HTML
    from streamlit_app.utils.cmi_styles import render_sparkbar, format_nivel_badge
    if "cumplimiento_pct" in df_tabla.columns and "Nivel de cumplimiento" in df_tabla.columns:
        df_tabla["Cumplimiento %"] = df_tabla.apply(lambda row: render_sparkbar(row["cumplimiento_pct"], row["Nivel de cumplimiento"]), axis=1)
        df_tabla["Estado"] = df_tabla["Nivel de cumplimiento"].apply(format_nivel_badge)
        df_tabla = df_tabla.drop(columns=["cumplimiento_pct", "Nivel de cumplimiento"])
    
    # Usar to_html para permitir el renderizado CSS custom
    st.markdown(
        df_tabla.to_html(escape=False, index=False, classes='table table-hover', border=0).replace('<th>', '<th style="text-align: left; background-color: #f8f9fa; padding: 10px; border-bottom: 2px solid #dee2e6;">').replace('<td>', '<td style="padding: 10px; border-bottom: 1px solid #e9ecef; vertical-align: middle;">'),
        unsafe_allow_html=True
    )

@st.cache_data(ttl=3600, show_spinner=False)
def _get_ai_linea(linea, cump, n_ind, n_riesgo, df_json):
    from services.ai_analysis import analizar_linea_cmi
    return analizar_linea_cmi(linea, str(cump), n_ind, n_riesgo, df_json)

def _render_subtab_analisis(df_linea, linea, color):
    cierres = load_cierres()
    if not cierres.empty:
        ids = df_linea["Id"].unique()
        hist = cierres[cierres["Id"].isin(ids)].copy()
        
        if not hist.empty:
            hist["Periodo"] = hist["Anio"].astype(str) + "-" + hist["Mes"].astype(str).str.zfill(2)
            hist_agrupado = hist.groupby("Periodo")["cumplimiento_pct"].mean().reset_index()
            
            fig_hist = px.line(
                hist_agrupado, 
                x="Periodo", 
                y="cumplimiento_pct", 
                markers=True,
                title=f"Tendencia de Cumplimiento Histórico",
                color_discrete_sequence=[color]
            )
            fig_hist.update_layout(margin=dict(t=30, b=10, l=10, r=10), height=300)
            st.plotly_chart(fig_hist, use_container_width=True, key=f"hist_{linea}")
        else:
            st.info("No hay histórico para esta línea.")
    
    # Análisis IA Real
    st.markdown("#### Análisis Estratégico Automático")
    
    n_ind = len(df_linea)
    n_riesgo = len(df_linea[df_linea["Nivel de cumplimiento"].isin(["Peligro", "Alerta"])])
    cump_val = df_linea["cumplimiento_pct"].mean()
    if pd.isna(cump_val): cump_val = 0
    
    cols_ai = ["Indicador", "Objetivo", "Meta", "Ejecucion", "cumplimiento_pct", "Nivel de cumplimiento"]
    df_ai = df_linea[[c for c in cols_ai if c in df_linea.columns]].copy()
    tabla_json = df_ai.to_json(orient="records", force_ascii=False)
    
    with st.spinner("Generando análisis táctico automático..."):
        ai_resp = _get_ai_linea(linea, round(cump_val, 1), n_ind, n_riesgo, tabla_json)
        
    if ai_resp:
        st.markdown(f"""
        <div style='padding: 15px; background-color: #F8F9FA; border-left: 5px solid {color}; border-radius: 5px; margin-bottom: 20px;'>
            <h5 style='margin-top: 0; color: #1A3A5C;'>🧠 Insights y Directrices Estratégicas</h5>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(ai_resp)
    else:
        st.info("El análisis automatizado con IA no está disponible en este momento (Falta configurar ANTHROPIC_API_KEY).")

def render_tab_lineas(df):
    st.markdown("### Líneas Estratégicas y Objetivos")
    if df.empty:
        st.info("No hay datos para mostrar.")
        return
        
    lineas = sorted([l for l in df["Linea"].dropna().unique() if str(l).strip()])
    
    # Check si venimos del dashboard (Resumen)
    linea_abierta = st.session_state.get("cmi_tab_linea_expand", None)
    
    for linea in lineas:
        df_linea = df[df["Linea"] == linea].copy()
        cump_mean = df_linea["cumplimiento_pct"].mean()
        cump_val = cump_mean if pd.notna(cump_mean) else 0
        color = linea_color(linea)
        
        is_expanded = (linea == linea_abierta)
        
        # Símbolo visual de estado para el título del acordeón
        estado_emoji = "🟢" if cump_val >= 100 else ("🟡" if cump_val >= 80 else "🔴")
        
        header_text = f"{estado_emoji} Línea: {linea} | Cumplimiento: {cump_val:.1f}% | {len(df_linea)} Indicadores"
        
        with st.expander(header_text, expanded=is_expanded):
            subtabs = st.tabs(["📊 Resumen de Línea", "🎯 Objetivos e Indicadores", "📈 Análisis y Tendencia"])
            
            with subtabs[0]:
                _render_subtab_resumen(df_linea, linea, color)
                
            with subtabs[1]:
                _render_subtab_objetivos(df_linea, linea)
                
            with subtabs[2]:
                _render_subtab_analisis(df_linea, linea, color)
                
    # Limpiar estado de expansión para que no quede trabado
    if "cmi_tab_linea_expand" in st.session_state:
        del st.session_state["cmi_tab_linea_expand"]
