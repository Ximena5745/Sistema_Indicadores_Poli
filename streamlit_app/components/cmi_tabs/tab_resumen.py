import streamlit as st
import pandas as pd
import plotly.express as px
from plotly import graph_objects as go
from streamlit_app.components.interactive_cards import render_metric_card
from streamlit_app.utils.cmi_helpers import calcular_kpis
from services.strategic_indicators import NIVEL_COLOR_EXT
try:
    from core.config import COLORES, COLOR_CATEGORIA
    # Asegurar que existe la clave primary
    if "primary" not in COLORES:
        COLORES["primary"] = COLORES.get("primario", "#1A3A5C")
except ImportError:
    COLORES = {
        "primary": "#1A3A5C", 
        "primario": "#1A3A5C",
        "success": "#43A047", 
        "warning": "#FBAF17", 
        "danger": "#D32F2F",
        "primary_light": "#2E5C8A",
    }
    COLOR_CATEGORIA = {
        "Peligro": "#D32F2F", 
        "Alerta": "#FBAF17", 
        "Cumplimiento": "#43A047", 
        "Sobrecumplimiento": "#1A3A5C"
    }

# Colores por línea estratégica (del docs/core/04_Dashboard.md)
LINEA_COLORES = {
    "Expansión": "#FBAF17",
    "Transformación organizacional": "#42F2F2",
    "Transformacion": "#42F2F2",
    "Calidad": "#EC0677",
    "Experiencia": "#1FB2DE",
    "Sostenibilidad": "#A6CE38",
    "Sustentabilidad": "#A6CE38",
    "Educación para toda la vida": "#0F385A",
    "Educacion": "#0F385A"
}

def _get_linea_color(linea):
    """Retorna el color oficial para una línea."""
    txt = str(linea or "").strip()
    for key, color in LINEA_COLORES.items():
        if key.lower() in txt.lower():
            return color
    return "#1A3A5C"  # Default


def render_tab_resumen(df):
    st.markdown("### Resumen Desglosado")
    if df.empty:
        st.info("No hay datos para mostrar.")
        return
        
    kpis = calcular_kpis(df)
    
    # 1. KPIs en tarjetas (4 principales) - usando paleta institucional
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Indicadores PDI", str(kpis["total"]), subtitle=f"Con cumplimiento: {kpis['con_dato']}", icon="📊", color=COLORES["primary"])
    with c2:
        render_metric_card("Promedio de Cumplimiento", f"{kpis['promedio']:.1f}%", subtitle="Sobre la meta institucional", icon="📈", color=COLOR_CATEGORIA["Cumplimiento"])
    with c3:
        n_top = kpis["conteo_estados"].get(kpis["top_nivel"], 0)
        nivel_color = COLOR_CATEGORIA.get(kpis["top_nivel"], COLORES["primary"])
        render_metric_card("Nivel Predominante", kpis["top_nivel"], subtitle=f"{n_top} de {kpis['total']} indicadores", icon="🏆", color=nivel_color)
    with c4:
        en_riesgo = kpis["conteo_estados"].get("Peligro", 0) + kpis["conteo_estados"].get("Alerta", 0)
        riesgo_color = COLOR_CATEGORIA["Peligro"] if en_riesgo > 0 else COLORES["success"]
        render_metric_card("Indicadores en Riesgo", str(en_riesgo), subtitle="Requieren atención", icon="⚠️", color=riesgo_color)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2. Gráficos: Bar chart (Líneas) y Donut chart (Niveles)
    col_charts1, col_charts2 = st.columns([6, 4])
    
    with col_charts1:
        st.markdown("#### Cumplimiento promedio por línea estratégica")
        by_linea = df.groupby("Linea", dropna=False)["cumplimiento_pct"].mean().fillna(0).reset_index()
        by_linea = by_linea.sort_values("cumplimiento_pct", ascending=True)
        by_linea["Linea"] = by_linea["Linea"].astype(str)
        by_linea["Cumpl_%"] = by_linea["cumplimiento_pct"].apply(lambda x: f"{x:.1f}%")
        _linea_map = {lin: _get_linea_color(lin) for lin in by_linea["Linea"].tolist()}
        
        fig_linea = px.bar(
            by_linea,
            x="cumplimiento_pct",
            y="Linea",
            orientation="h",
            labels={"cumplimiento_pct": "Cumplimiento (%)", "Linea": ""},
            color="Linea",
            color_discrete_map=_linea_map,
            text="Cumpl_%",
        )
        
        # Etiquetas fuera de las barras
        fig_linea.update_traces(
            textposition="outside",
            marker_line_color="rgba(0,0,0,0)",
            textfont={"size": 11},
        )
        
        # Línea de meta 100% con annotation
        fig_linea.add_vline(
            x=100, 
            line_dash="dash", 
            line_color="#6B7280",
            line_width=2,
        )
        fig_linea.add_annotation(
            x=100,
            y=1.05,
            text="Meta 100%",
            showarrow=False,
            font=dict(size=10, color="#6B7280"),
            xref="x",
            yref="paper",
        )
        
        # Estilos de layout profesional
        fig_linea.update_layout(
            margin=dict(l=20, r=20, t=30, b=20),
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                gridcolor="#E5E7EB",
                range=[0, max(120, by_linea["cumplimiento_pct"].max() * 1.1)],
            ),
        )
        st.plotly_chart(fig_linea, use_container_width=True)
            
    with col_charts2:
        st.markdown("#### Distribución por nivel")
        if "Nivel de cumplimiento" in df.columns:
            niveles = df["Nivel de cumplimiento"].fillna("Pendiente de reporte").value_counts().reset_index()
            niveles.columns = ["Nivel", "Cantidad"]
            total_ind = niveles["Cantidad"].sum()
            
            # Calcular porcentaje
            niveles["Porcentaje"] = (niveles["Cantidad"] / total_ind * 100).round(1)
            
            # Mapeo de colores desde config
            color_map = {
                "Sobrecumplimiento": COLOR_CATEGORIA["Sobrecumplimiento"],
                "Cumplimiento": COLOR_CATEGORIA["Cumplimiento"],
                "Alerta": COLOR_CATEGORIA["Alerta"],
                "Peligro": COLOR_CATEGORIA["Peligro"],
                "Pendiente de reporte": "#9E9E9E",
            }
            
            fig_niv = go.Figure(data=[
                go.Pie(
                    labels=niveles["Nivel"],
                    values=niveles["Cantidad"],
                    marker=dict(colors=[color_map.get(n, "#9E9E9E") for n in niveles["Nivel"]]),
                    hole=0.5,
                    textinfo="label+percent",
                    textposition="inside",
                    textfont={"size": 11},
                    hovertemplate="<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}<extra></extra>",
                )
            ])
            
            # Centro con estadísticas
            fig_niv.add_annotation(
                text=(
                    f"<b>{total_ind}</b><br>"
                    f"<span style='font-size:12px;'>indicadores</span>"
                ),
                showarrow=False,
                font=dict(size=24, color=COLORES["primary"]),
                align="center",
            )
            
            fig_niv.update_layout(
                margin=dict(l=10, r=10, t=30, b=10),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.1,
                    xanchor="center",
                    x=0.5,
                ),
            )
            st.plotly_chart(fig_niv, use_container_width=True)
            
    st.markdown("<br>", unsafe_allow_html=True)
            
    # 3. Fichas: Vista rápida por línea - diseño profesional compacta (ejemplo参考)
    # Fuente central de colores: docs/core/04_Dashboard.md
    st.markdown("#### Vista rápida por línea")
    lineas = [l for l in df["Linea"].dropna().unique() if str(l).strip()]
    lineas = sorted(lineas, key=lambda x: df[df["Linea"] == x]["cumplimiento_pct"].mean(), reverse=True)
    
    # CSS profesional para grid de tarjetas
    card_css = """
    <style>
    .linea-cards-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        margin-bottom: 24px;
    }
    @media (max-width: 1024px) {
        .linea-cards-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; }
    }
    @media (max-width: 640px) {
        .linea-cards-grid { grid-template-columns: 1fr; gap: 12px; }
    }
    .linea-card {
        background: #FFFFFF;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .linea-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .linea-card-header {
        padding: 10px 14px;
        color: #FFFFFF;
        font-weight: 700;
        font-size: 13px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .linea-card-header span:first-child {
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    .linea-card-header span:last-child {
        font-size: 11px;
        opacity: 0.9;
        font-weight: 500;
    }
    .linea-card-body {
        padding: 14px;
    }
    .cumpl-box {
        text-align: center;
        padding: 14px 10px;
        border-radius: 8px;
        margin-bottom: 12px;
    }
    .cumpl-value {
        font-size: 28px;
        font-weight: 700;
        line-height: 1.2;
    }
    .cumpl-label {
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 2px;
    }
    .metrics-row {
        display: flex;
        gap: 8px;
        margin-bottom: 12px;
    }
    .metric-box {
        flex: 1;
        text-align: center;
        padding: 8px 4px;
        background: #F8FAFC;
        border-radius: 6px;
    }
    .metric-value {
        font-size: 16px;
        font-weight: 600;
    }
    .metric-label {
        font-size: 10px;
        text-transform: uppercase;
    }
    .progress-row {
        margin-top: 8px;
    }
    .progress-header {
        display: flex;
        justify-content: space-between;
        font-size: 10px;
        margin-bottom: 4px;
    }
    .progress-bar {
        width: 100%;
        height: 6px;
        background: #E5E7EB;
        border-radius: 3px;
        overflow: hidden;
    }
    .progress-fill {
        height: 100%;
        border-radius: 3px;
    }
    .linea-card-footer {
        padding: 10px 14px;
        background: #F9FAFB;
        border-top: 1px solid #E5E7EB;
        text-align: right;
    }
    .linea-card-footer a {
        font-size: 12px;
        font-weight: 600;
        color: #1A3A5C;
        text-decoration: none;
        cursor: pointer;
    }
    .linea-card-footer a:hover {
        text-decoration: underline;
    }
    </style>
    """
    st.markdown(card_css, unsafe_allow_html=True)
    
    # Generar tarjetas
    cards_html = '<div class="linea-cards-grid">'
    
    for idx, linea in enumerate(lineas):
        df_l = df[df["Linea"] == linea]
        cump = df_l["cumplimiento_pct"].mean()
        if pd.isna(cump): cump = 0
        n_ind = len(df_l)
        n_obj = df_l["Objetivo"].nunique()
        
        # Color de línea desde fuente central
        color = _get_linea_color(linea)
        
        # Nombre limpio para mostrar (con espacios)
        linea_display = str(linea).strip()
        
        # Determinar estado
        if cump >= 100:
            estado_color = "#43A047"
            estado_label = "Meta alcanzada"
            estado_bg = "#E8F5E9"
            estado_text = "#2E7D32"
        elif cump >= 80:
            estado_color = "#FBAF17"
            estado_label = "En proceso"
            estado_bg = "#FFF8E1"
            estado_text = "#F57F17"
        else:
            estado_color = "#D32F2F"
            estado_label = "Requiere atención"
            estado_bg = "#FFEBEE"
            estado_text = "#B71C1C"
        
        # Construir tarjeta HTML
        card = f"""
        <div class="linea-card">
            <div class="linea-card-header" style="background: {color};">
                <span>{linea_display}</span>
                <span>Línea</span>
            </div>
            <div class="linea-card-body">
                <div class="cumpl-box" style="background: {estado_bg};">
                    <div class="cumpl-value" style="color: {estado_color};">{cump:.1f}%</div>
                    <div class="cumpl-label" style="color: #6B7280;">Cumplimiento</div>
                </div>
                <div class="metrics-row">
                    <div class="metric-box">
                        <div class="metric-value" style="color: #1A3A5C;">{n_ind}</div>
                        <div class="metric-label" style="color: #6B7280;">Indicadores</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-value" style="color: #1A3A5C;">{n_obj}</div>
                        <div class="metric-label" style="color: #6B7280;">Objetivos</div>
                    </div>
                </div>
                <div class="progress-row">
                    <div class="progress-header">
                        <span style="color: #6B7280;">Progreso</span>
                        <span style="font-weight: 600; color: #6B7280;">Meta 100%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {min(100, cump)}%; background: {estado_color};"></div>
                    </div>
                </div>
            </div>
        </div>
        """
        cards_html += card
    
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)
    
    # Botones de acción (debajo de las tarjetas)
    st.markdown('<div style="margin-top: 8px;">', unsafe_allow_html=True)
    for idx, linea in enumerate(lineas):
        btn_key = f"btn_linea_{idx}"
        if st.button(f"Ver Detalles: {linea}", key=btn_key):
            st.session_state["cmi_tab_linea_expand"] = linea
            st.toast(f"✅ {linea} seleccionado")
    st.markdown('</div>', unsafe_allow_html=True)
            
    st.markdown("<br>", unsafe_allow_html=True)
            
    # 4. Panel Insights - bloques profesionales
    peligro = kpis["conteo_estados"].get("Peligro", 0)
    alerta = kpis["conteo_estados"].get("Alerta", 0)
    cump = kpis["conteo_estados"].get("Cumplimiento", 0)
    sobre = kpis["conteo_estados"].get("Sobrecumplimiento", 0)
    
    # Diseño de bloques según tipo
    insights_html = '<div style="display: flex; flex-direction: column; gap: 12px; margin-top: 20px;">'
    
    if peligro > 0:
        insights_html += f"""
        <div style="background: linear-gradient(135deg, #FFCDD2 0%, #FFECB3 100%); padding: 16px; border-radius: 10px; border-left: 5px solid #D32F2F; box-shadow: 0 2px 6px rgba(211,47,47,0.15);">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.5rem;">🚨</span>
                <div>
                    <div style="font-weight: 700; color: #B71C1C; font-size: 0.95rem;">Atención requerida</div>
                    <div style="color: #424242; font-size: 0.9rem;">Hay <b style="color: #D32F2F;">{peligro}</b> indicadores en Peligro que requieren revisión inmediata.</div>
                </div>
            </div>
        </div>
        """
    
    if alerta > 0:
        insights_html += f"""
        <div style="background: linear-gradient(135deg, #FFF8E1 0%, #FFFDE7 100%); padding: 16px; border-radius: 10px; border-left: 5px solid #FBAF17; box-shadow: 0 2px 6px rgba(251,175,23,0.15);">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.5rem;">⚠️</span>
                <div>
                    <div style="font-weight: 700; color: #F57F17; font-size: 0.95rem;">Monitoreo</div>
                    <div style="color: #424242; font-size: 0.9rem;"><b style="color: #F57F17;">{alerta}</b> indicadores se encuentran en Alerta. Se sugiere seguimiento cercano.</div>
                </div>
            </div>
        </div>
        """
    
    if cump > 0 or sobre > 0:
        buen_color = COLOR_CATEGORIA["Cumplimiento"]
        buen_bg = "#E8F5E9"
        insights_html += f"""
        <div style="background: linear-gradient(135deg, {buen_bg} 0%, #E3F2FD 100%); padding: 16px; border-radius: 10px; border-left: 5px solid {buen_color}; box-shadow: 0 2px 6px rgba(67,160,71,0.15);">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.5rem;">✅</span>
                <div>
                    <div style="font-weight: 700; color: #2E7D32; font-size: 0.95rem;">Buen desempeño</div>
                    <div style="color: #424242; font-size: 0.9rem;"><b style="color: #2E7D32;">{cump + sobre}</b> indicadores han alcanzado o superado la meta institucional.</div>
                </div>
            </div>
        </div>
        """
    
    if peligro == 0 and alerta == 0:
        insights_html += f"""
        <div style="background: linear-gradient(135deg, #E8F5E9 0%, #E3F2FD 100%); padding: 16px; border-radius: 10px; border-left: 5px solid {COLOR_CATEGORIA['Cumplimiento']}; box-shadow: 0 2px 6px rgba(67,160,71,0.15);">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.5rem;">🎉</span>
                <div>
                    <div style="font-weight: 700; color: #2E7D32; font-size: 0.95rem;">Excelente</div>
                    <div style="color: #424242; font-size: 0.9rem;">Todos los indicadores están en estado favorable.</div>
                </div>
            </div>
        </div>
        """
    
    insights_html += "</div>"
    
    st.markdown(
        "<h4 style='color: #1A3A5C; margin-top: 0; margin-bottom: 10px;'>💡 Insights Automáticos</h4>" +
        insights_html,
        unsafe_allow_html=True
    )
