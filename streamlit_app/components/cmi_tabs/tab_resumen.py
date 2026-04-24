import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_app.components.interactive_cards import render_metric_card
from streamlit_app.utils.cmi_helpers import calcular_kpis
from services.strategic_indicators import NIVEL_COLOR_EXT

def render_tab_resumen(df):
    st.markdown("### Resumen Desglosado")
    if df.empty:
        st.info("No hay datos para mostrar.")
        return
        
    kpis = calcular_kpis(df)
    
    # Renderizar tarjetas
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Total Indicadores", str(kpis["total"]), icon="📊", color="#1f4e79")
    with c2:
        render_metric_card("Cumplimiento Promedio", f"{kpis['promedio']:.1f}%", icon="📈", color="#2E7D32")
    with c3:
        render_metric_card("Nivel Predominante", kpis["top_nivel"], icon="🏆", color="#F9A825")
    with c4:
        render_metric_card("Con Dato", str(kpis["con_dato"]), icon="✅", color="#1565C0")
        
    st.markdown("#### Distribución de Estados y Narrativa")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Gráfico Donut
        if "Nivel de cumplimiento" in df.columns:
            niveles = df["Nivel de cumplimiento"].fillna("Pendiente de reporte").value_counts().reset_index()
            niveles.columns = ["Nivel", "Cantidad"]
            fig_niv = px.pie(
                niveles,
                names="Nivel",
                values="Cantidad",
                title="Distribución por nivel",
                color="Nivel",
                color_discrete_map=NIVEL_COLOR_EXT,
                hole=0.45,
            )
            fig_niv.update_layout(margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig_niv, use_container_width=True)
            
    with col2:
        # Panel IA
        st.markdown("""
        <div style="background-color: #F5F7FA; padding: 20px; border-radius: 10px; border-left: 5px solid #1f4e79; height: 100%;">
            <h4 style="color: #1f4e79; margin-top: 0;">💡 Insights Automáticos</h4>
            <ul style="color: #333; font-size: 1.05rem; line-height: 1.6;">
        """, unsafe_allow_html=True)
        
        peligro = kpis["conteo_estados"].get("Peligro", 0)
        alerta = kpis["conteo_estados"].get("Alerta", 0)
        cump = kpis["conteo_estados"].get("Cumplimiento", 0)
        sobre = kpis["conteo_estados"].get("Sobrecumplimiento", 0)
        
        if peligro > 0:
            st.markdown(f"<li>🚨 <b>Atención requerida:</b> Hay <b>{peligro}</b> indicadores en Peligro que requieren revisión inmediata de sus planes de acción.</li>", unsafe_allow_html=True)
        if alerta > 0:
            st.markdown(f"<li>⚠️ <b>Monitoreo:</b> <b>{alerta}</b> indicadores se encuentran en Alerta. Se sugiere hacer seguimiento cercano.</li>", unsafe_allow_html=True)
        if cump > 0 or sobre > 0:
            st.markdown(f"<li>✅ <b>Buen desempeño:</b> <b>{cump + sobre}</b> indicadores han alcanzado o superado la meta establecida.</li>", unsafe_allow_html=True)
            
        promedio = kpis["promedio"]
        if promedio >= 85:
            st.markdown(f"<li>📈 <b>Tendencia General:</b> El cumplimiento promedio de {promedio:.1f}% indica una ejecución sólida de la estrategia.</li>", unsafe_allow_html=True)
        else:
            st.markdown(f"<li>📉 <b>Oportunidad de Mejora:</b> El cumplimiento promedio de {promedio:.1f}% señala áreas de oportunidad en la ejecución de la estrategia.</li>", unsafe_allow_html=True)
            
        st.markdown("""
            </ul>
        </div>
        """, unsafe_allow_html=True)
