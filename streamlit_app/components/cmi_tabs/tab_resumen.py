import streamlit as st
import pandas as pd
import plotly.express as px
from plotly import graph_objects as go
from streamlit_app.components.interactive_cards import render_metric_card
from streamlit_app.utils.cmi_helpers import calcular_kpis, linea_color
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
        _linea_map = {lin: linea_color(lin) for lin in by_linea["Linea"].tolist()}
        
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
            
    # 3. Fichas: Vista rápida por línea - diseño profesional
    st.markdown("#### Vista rápida por línea")
    lineas = [l for l in df["Linea"].dropna().unique() if str(l).strip()]
    lineas = sorted(lineas, key=lambda x: df[df["Linea"] == x]["cumplimiento_pct"].mean(), reverse=True)
    cols_fichas = st.columns(3)
    
    for idx, linea in enumerate(lineas):
        df_l = df[df["Linea"] == linea]
        cump = df_l["cumplimiento_pct"].mean()
        if pd.isna(cump): cump = 0
        n_ind = len(df_l)
        n_obj = df_l["Objetivo"].nunique()
        color = linea_color(linea)
        
        # Color del texto según contraste
        text_color = "white" if color not in ["#FBAF17", "#42F2F2", "#FEF3D0", "#A6CE38", "#FFD56B"] else "#1A1A1A"
        
        # Color de la barra según cumplimiento
        bar_color = "#43A047" if cump >= 100 else "#FBAF17" if cump >= 80 else "#D32F2F"
        
        # Tarjeta profesional con borde izquierdo de color
        card_html = f"""
        <div style="background: linear-gradient(135deg, {color} 0%, {color}EE 100%); color: {text_color}; padding: 18px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.12); margin-bottom: 16px; border-left: 5px solid {bar_color};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-weight: 600; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 0.5px;">{linea}</span>
                <span style="font-size: 1.1rem; opacity: 0.9;">→</span>
            </div>
            <div style="text-align: center; margin-bottom: 12px;">
                <span style="font-size: 2rem; font-weight: 700; line-height: 1;">{cump:.1f}%</span>
                <div style="font-size: 0.7rem; opacity: 0.85; text-transform: uppercase; margin-top: 2px;">Cumplimiento</div>
            </div>
            <div style="display: flex; justify-content: space-around; margin-bottom: 12px; padding: 8px 0; border-top: 1px solid rgba(255,255,255,0.2); border-bottom: 1px solid rgba(255,255,255,0.2);">
                <div style="text-align: center;">
                    <div style="font-size: 1.3rem; font-weight: 600;">{n_ind}</div>
                    <div style="font-size: 0.65rem; opacity: 0.8; text-transform: uppercase;">Indicadores</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.3rem; font-weight: 600;">{n_obj}</div>
                    <div style="font-size: 0.65rem; opacity: 0.8; text-transform: uppercase;">Objetivos</div>
                </div>
            </div>
            <div style="margin-top: 8px;">
                <div style="width: 100%; background-color: rgba(255,255,255,0.25); height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="width: {min(100, cump)}%; background-color: {bar_color}; height: 100%; border-radius: 4px;"></div>
                </div>
                <div style="text-align: center; font-size: 0.7rem; margin-top: 4px; opacity: 0.8;">Meta 100%</div>
            </div>
        </div>
        """
        html_clean = "\n".join([line for line in card_html.split("\n") if line.strip()])
        with cols_fichas[idx % 3]:
            st.markdown(html_clean, unsafe_allow_html=True)
            if st.button(f"🔍 Ver Detalles", key=f"btn_nav_{linea.replace(' ', '_')}_{idx}", use_container_width=True):
                st.session_state["cmi_tab_linea_expand"] = linea
                st.success("✅ Seleccionada. Haz clic en la pestaña superior 'Líneas Estratégicas' para ver el detalle.")
            
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
