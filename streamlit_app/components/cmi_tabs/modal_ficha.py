import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core.config import UMBRAL_PELIGRO, UMBRAL_ALERTA, UMBRAL_SOBRECUMPLIMIENTO, COLOR_CATEGORIA_CLARO, COLORES
from streamlit_app.components.interactive_cards import render_indicator_status_card, render_expandable_card
from services.strategic_indicators import load_cierres

@st.cache_data(ttl=3600, show_spinner=False)
def _get_ai_ficha(nombre, linea, obj, meta, eje, nivel, cump):
    from services.ai_analysis import analizar_ficha_cmi
    return analizar_ficha_cmi(nombre, linea, obj, str(meta), str(eje), nivel, str(cump))

@st.dialog("Ficha Técnica del Indicador", width="large")
def render_modal_ficha(ind_data: pd.Series):
    """
    Renderiza la ficha técnica detallada de un indicador en formato Modal (emergente).
    Se abre sobre la tabla de indicadores sin perder el contexto de la vista "Por Línea".
    """
    sel_ind = ind_data.get("Indicador", "Sin nombre")
    id_ind = ind_data.get("Id", "")
    
    # 1. Encabezado
    st.markdown(f"**Línea:** {ind_data.get('Linea', 'N/A')} | **Objetivo:** {ind_data.get('Objetivo', 'N/A')}")
    
    # 2. Status Card y Gauge Chart
    col1, col2 = st.columns([1, 1])
    
    cump = ind_data.get("cumplimiento_pct", 0)
    if pd.isna(cump):
        cump = 0
        
    with col1:
        card_data = {
            "codigo": id_ind,
            "nombre": sel_ind,
            "cumplimiento": cump,
            "meta": ind_data.get("Meta", 0),
            "ejecucion": ind_data.get("Ejecucion", 0),
            "estado": ind_data.get("Nivel de cumplimiento", "Sin dato"),
            "linea": ind_data.get("Linea", "")
        }
        render_indicator_status_card(card_data)
        
    with col2:
        # Gauge Chart (corregido usando core/config.py)
        p_peligro = UMBRAL_PELIGRO * 100
        p_alerta = UMBRAL_ALERTA * 100
        p_sobre = UMBRAL_SOBRECUMPLIMIENTO * 100
        
        # Colores pastel basados en core/config.py
        color_peligro = COLOR_CATEGORIA_CLARO.get("Peligro", "#FFCDD2")
        color_alerta = COLOR_CATEGORIA_CLARO.get("Alerta", "#FEF3D0")
        color_cump = COLOR_CATEGORIA_CLARO.get("Cumplimiento", "#E8F5E9")
        color_sobre = COLOR_CATEGORIA_CLARO.get("Sobrecumplimiento", "#D0E4FF")

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=cump,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Cumplimiento (%)", 'font': {'size': 14}},
            gauge={
                'axis': {'range': [None, max(130, cump)], 'tickwidth': 1},
                'bar': {'color': COLORES.get("primario", "#1A3A5C")},
                'steps': [
                    {'range': [0, p_peligro], 'color': color_peligro},
                    {'range': [p_peligro, p_alerta], 'color': color_alerta},
                    {'range': [p_alerta, p_sobre], 'color': color_cump},
                    {'range': [p_sobre, max(130, cump)], 'color': color_sobre}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 2},
                    'thickness': 0.75,
                    'value': 100
                }
            }
        ))
        fig_gauge.update_layout(margin=dict(t=30, b=10, l=10, r=10), height=250)
        st.plotly_chart(fig_gauge, use_container_width=True)
        
    # 3. Histórico
    st.markdown("#### Histórico de Cumplimiento")
    cierres = load_cierres()
    if not cierres.empty:
        # Filtrar por Id asegurando que sea string
        hist = cierres[cierres["Id"].astype(str) == str(id_ind)].copy()
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
                fig_hist.add_hline(y=100, line_dash="dot", line_color="green", annotation_text="Meta (100%)")
                fig_hist.update_layout(margin=dict(t=30, b=10, l=10, r=10))
                st.plotly_chart(fig_hist, use_container_width=True)
            with hc2:
                st.dataframe(hist[["Periodo", "Meta", "Ejecucion", "cumplimiento_pct"]], hide_index=True, use_container_width=True)
        else:
            st.info("No hay datos históricos para este indicador.")
            
    # 4. Metadatos
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
    
    # 5. Análisis y Gestión de Mejoramiento (IA Phase 2)
    st.markdown("#### Análisis Estratégico (IA)")
    
    with st.spinner("Generando diagnóstico con IA..."):
        ai_resp = _get_ai_ficha(
            sel_ind, 
            ind_data.get('Linea', ''), 
            ind_data.get('Objetivo', ''), 
            ind_data.get('Meta', ''), 
            ind_data.get('Ejecucion', ''), 
            ind_data.get('Nivel de cumplimiento', ''), 
            cump
        )
        
    if ai_resp:
        # Convertir Markdown a HTML básico de forma rudimentaria para inyectarlo en el div o usar st.markdown nativo
        # Es mejor usar st.markdown directo dentro del contenedor
        st.markdown(f"""
        <div style='padding: 15px; background-color: #F4F6F9; border-left: 5px solid #1A3A5C; border-radius: 5px; margin-bottom: 20px;'>
            <h5 style='margin-top: 0; color: #1A3A5C;'>🧠 Diagnóstico y Recomendaciones (Claude AI)</h5>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(ai_resp)
    else:
        st.info("El análisis automatizado con IA no está disponible en este momento (Falta API Key).")
