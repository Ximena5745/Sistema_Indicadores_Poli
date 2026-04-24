import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_app.components.interactive_cards import render_indicator_status_card, render_expandable_card
from services.strategic_indicators import load_cierres

def render_tab_ficha(df):
    st.markdown("### Ficha de Indicador")
    if df.empty:
        st.info("No hay datos para mostrar.")
        return
        
    # Inicializar selección si viene de otra pestaña
    if "cmi_ficha_indicador_sel" not in st.session_state:
        st.session_state["cmi_ficha_indicador_sel"] = df["Indicador"].iloc[0]
        
    indicadores_disp = df["Indicador"].dropna().unique().tolist()
    
    # Asegurar que el seleccionado existe en la lista actual
    if st.session_state["cmi_ficha_indicador_sel"] not in indicadores_disp:
        if indicadores_disp:
            st.session_state["cmi_ficha_indicador_sel"] = indicadores_disp[0]
        else:
            st.info("Indicador no encontrado.")
            return
            
    sel_ind = st.selectbox(
        "Seleccione un Indicador", 
        indicadores_disp,
        index=indicadores_disp.index(st.session_state["cmi_ficha_indicador_sel"]) if st.session_state["cmi_ficha_indicador_sel"] in indicadores_disp else 0,
        key="cmi_ficha_selector_main"
    )
    
    # Actualizar estado si cambia
    if sel_ind != st.session_state["cmi_ficha_indicador_sel"]:
        st.session_state["cmi_ficha_indicador_sel"] = sel_ind
        
    ind_data = df[df["Indicador"] == sel_ind].iloc[0]
    
    # 1. Encabezado
    st.markdown(f"#### {ind_data.get('Id', '')} - {sel_ind}")
    st.markdown(f"**Línea:** {ind_data.get('Linea', 'N/A')} | **Objetivo:** {ind_data.get('Objetivo', 'N/A')}")
    
    # 2. Status Card y Gauge
    col1, col2 = st.columns([1, 1])
    
    cump = ind_data.get("cumplimiento_pct", 0)
    if pd.isna(cump):
        cump = 0
        
    with col1:
        card_data = {
            "codigo": ind_data.get("Id", ""),
            "nombre": sel_ind,
            "cumplimiento": cump,
            "meta": ind_data.get("Meta", 0),
            "ejecucion": ind_data.get("Ejecucion", 0),
            "estado": ind_data.get("Nivel de cumplimiento", "Sin dato"),
            "linea": ind_data.get("Linea", "")
        }
        render_indicator_status_card(card_data)
        
    with col2:
        # Gauge Chart
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = cump,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Cumplimiento (%)"},
            gauge = {
                'axis': {'range': [None, max(120, cump)]},
                'bar': {'color': "darkblue"},
                'steps' : [
                    {'range': [0, 70], 'color': "#FFCDD2"},
                    {'range': [70, 85], 'color': "#FEF3D0"},
                    {'range': [85, 100], 'color': "#E8F5E9"},
                    {'range': [100, max(120, cump)], 'color': "#D0E4FF"}
                ]
            }
        ))
        fig_gauge.update_layout(margin=dict(t=30, b=10, l=10, r=10), height=250)
        st.plotly_chart(fig_gauge, use_container_width=True)
        
    # 3. Histórico (Line chart 12 meses + tabla)
    st.markdown("#### Histórico de Cumplimiento")
    cierres = load_cierres()
    if not cierres.empty:
        hist = cierres[cierres["Id"] == ind_data.get("Id", "")].copy()
        if not hist.empty:
            hist["Periodo"] = hist["Anio"].astype(str) + "-" + hist["Mes"].astype(str).str.zfill(2)
            hist = hist.sort_values("Periodo").tail(12)
            
            hc1, hc2 = st.columns([2, 1])
            with hc1:
                fig_hist = px.line(
                    hist, 
                    x="Periodo", 
                    y="cumplimiento_pct", 
                    markers=True, 
                    title="Evolución (últimos 12 periodos)"
                )
                fig_hist.update_layout(margin=dict(t=30, b=10, l=10, r=10))
                st.plotly_chart(fig_hist, use_container_width=True)
            with hc2:
                st.dataframe(hist[["Periodo", "Meta", "Ejecucion", "cumplimiento_pct"]], hide_index=True)
        else:
            st.info("No hay datos históricos para este indicador.")
            
    # 4. Metadatos & OM Vinculadas (Usando expanders/cards)
    st.markdown("#### Detalles Adicionales")
    
    meta_html = f"""
    <ul style='line-height: 1.6;'>
        <li><b>Responsable:</b> {ind_data.get('Responsable', 'No definido')}</li>
        <li><b>Fuente:</b> {ind_data.get('Fuente', 'No definida')}</li>
        <li><b>Fórmula:</b> {ind_data.get('Formula', 'No definida')}</li>
        <li><b>Periodicidad:</b> {ind_data.get('Periodicidad', 'No definida')}</li>
    </ul>
    """
    render_expandable_card("Metadatos del Indicador", meta_html, icon="📋", default_expanded=True)
    
    om_html = """
    <div style='padding: 10px; background-color: #f9f9f9; border-radius: 5px;'>
        <i>Nota: Las Oportunidades de Mejora (OM) vinculadas a este indicador se gestionan desde el módulo correspondiente. Actualmente no hay OMs críticas activas para mostrar.</i>
    </div>
    """
    render_expandable_card("Oportunidades de Mejora (OM) Vinculadas", om_html, icon="🔧", default_expanded=False)
