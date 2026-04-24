import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_app.components.interactive_cards import render_metric_card
from streamlit_app.utils.cmi_helpers import calcular_kpis, linea_color
from services.strategic_indicators import NIVEL_COLOR_EXT

def render_tab_resumen(df):
    st.markdown("### Resumen Desglosado")
    if df.empty:
        st.info("No hay datos para mostrar.")
        return
        
    kpis = calcular_kpis(df)
    
    # 1. KPIs en tarjetas (4 principales)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Indicadores PDI", str(kpis["total"]), subtitle=f"Con cumplimiento: {kpis['con_dato']}", icon="📊", color="#1f4e79")
    with c2:
        render_metric_card("Promedio de Cumplimiento", f"{kpis['promedio']:.1f}%", subtitle="Sobre la meta institucional", icon="📈", color="#2E7D32")
    with c3:
        n_top = kpis["conteo_estados"].get(kpis["top_nivel"], 0)
        render_metric_card("Nivel Predominante", kpis["top_nivel"], subtitle=f"{n_top} de {kpis['total']} indicadores", icon="🏆", color="#F9A825")
    with c4:
        en_riesgo = kpis["conteo_estados"].get("Peligro", 0) + kpis["conteo_estados"].get("Alerta", 0)
        render_metric_card("Indicadores en Riesgo", str(en_riesgo), subtitle="Requieren atención", icon="⚠️", color="#C62828")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2. Gráficos: Bar chart (Líneas) y Donut chart (Niveles)
    col_charts1, col_charts2 = st.columns([6, 4])
    
    with col_charts1:
        st.markdown("#### Cumplimiento promedio por línea estratégica")
        by_linea = df.groupby("Linea", dropna=False)["cumplimiento_pct"].mean().fillna(0).reset_index()
        by_linea = by_linea.sort_values("cumplimiento_pct", ascending=True)
        by_linea["Linea"] = by_linea["Linea"].astype(str)
        _linea_map = {lin: linea_color(lin) for lin in by_linea["Linea"].tolist()}
        
        fig_linea = px.bar(
            by_linea,
            x="cumplimiento_pct",
            y="Linea",
            orientation="h",
            labels={"cumplimiento_pct": "Cumplimiento (%)", "Linea": ""},
            color="Linea",
            color_discrete_map=_linea_map,
            text_auto=".1f"
        )
        fig_linea.update_layout(margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
        st.plotly_chart(fig_linea, use_container_width=True)
            
    with col_charts2:
        st.markdown("#### Distribución por nivel")
        if "Nivel de cumplimiento" in df.columns:
            niveles = df["Nivel de cumplimiento"].fillna("Pendiente de reporte").value_counts().reset_index()
            niveles.columns = ["Nivel", "Cantidad"]
            fig_niv = px.pie(
                niveles,
                names="Nivel",
                values="Cantidad",
                color="Nivel",
                color_discrete_map=NIVEL_COLOR_EXT,
                hole=0.45,
            )
            fig_niv.update_layout(margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_niv, use_container_width=True)
            
    st.markdown("<br>", unsafe_allow_html=True)
            
    # 3. Fichas: Vista rápida por línea
    st.markdown("#### Vista rápida por línea")
    lineas = [l for l in df["Linea"].dropna().unique() if str(l).strip()]
    cols_fichas = st.columns(3)
    
    for idx, linea in enumerate(lineas):
        df_l = df[df["Linea"] == linea]
        cump = df_l["cumplimiento_pct"].mean()
        if pd.isna(cump): cump = 0
        n_ind = len(df_l)
        n_obj = df_l["Objetivo"].nunique()
        color = linea_color(linea)
        
        # Color del texto según el fondo para contraste (simplificado: blanco)
        text_color = "white" if color not in ["#FBAF17", "#42F2F2", "#FEF3D0", "#A6CE38"] else "#1A1A1A"
        
        card_html = f"""
        <div style="background-color: {color}; color: {text_color}; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h4 style="margin-top: 0; margin-bottom: 15px; color: {text_color}; display: flex; justify-content: space-between;">
                <span>{linea}</span>
                <span>→</span>
            </h4>
            <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                <div style="text-align: center;">
                    <div style="font-size: 1.6rem; font-weight: 900;">{cump:.1f}%</div>
                    <div style="font-size: 0.75rem; opacity: 0.9; text-transform: uppercase;">Cumplimiento</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.6rem; font-weight: 900;">{n_ind}</div>
                    <div style="font-size: 0.75rem; opacity: 0.9; text-transform: uppercase;">Indicadores</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.6rem; font-weight: 900;">{n_obj}</div>
                    <div style="font-size: 0.75rem; opacity: 0.9; text-transform: uppercase;">Objetivos</div>
                </div>
            </div>
            <div style="width: 100%; background-color: rgba(255,255,255,0.3); height: 6px; border-radius: 3px;">
                <div style="width: {min(100, cump)}%; background-color: {text_color}; height: 100%; border-radius: 3px;"></div>
            </div>
        </div>
        """
        html_clean = "\n".join([line for line in card_html.split("\n") if line.strip()])
        with cols_fichas[idx % 3]:
            st.markdown(html_clean, unsafe_allow_html=True)
            
    st.markdown("<br>", unsafe_allow_html=True)
            
    # 4. Panel IA
    html_insights = """
    <div style="background-color: #F5F7FA; padding: 20px; border-radius: 10px; border-left: 5px solid #1f4e79;">
        <h4 style="color: #1f4e79; margin-top: 0;">💡 Insights Automáticos</h4>
        <ul style="color: #333; font-size: 1.05rem; line-height: 1.6; margin-bottom: 0;">
    """
    
    peligro = kpis["conteo_estados"].get("Peligro", 0)
    alerta = kpis["conteo_estados"].get("Alerta", 0)
    cump = kpis["conteo_estados"].get("Cumplimiento", 0)
    sobre = kpis["conteo_estados"].get("Sobrecumplimiento", 0)
    
    if peligro > 0:
        html_insights += f"<li>🚨 <b>Atención requerida:</b> Hay <b>{peligro}</b> indicadores en Peligro que requieren revisión inmediata.</li>"
    if alerta > 0:
        html_insights += f"<li>⚠️ <b>Monitoreo:</b> <b>{alerta}</b> indicadores se encuentran en Alerta. Se sugiere hacer seguimiento cercano.</li>"
    if cump > 0 or sobre > 0:
        html_insights += f"<li>✅ <b>Buen desempeño:</b> <b>{cump + sobre}</b> indicadores han alcanzado o superado la meta establecida.</li>"
        
    html_insights += """
        </ul>
    </div>
    """
    st.markdown("\n".join([line for line in html_insights.split("\n") if line.strip()]), unsafe_allow_html=True)
