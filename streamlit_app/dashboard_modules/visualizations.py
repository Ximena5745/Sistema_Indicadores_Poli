"""
Dashboard visualization components.

Handles chart creation and rendering for IRIP prediction, anomaly detection,
and CMI strategic indicators visualization.
"""
import streamlit as st
import plotly.express as px
from .kpi_definitions import DATA_IRIP, DATA_ANOMALIAS, DATA_CMI


def render_irip_chart():
    """
    Renderiza el módulo IRIP Predictivo con gráfico de barras de riesgo.
    
    Muestra ranking de indicadores con riesgo alto de incumplimiento (IRIP >70%).
    """
    st.subheader("Módulo IRIP Predictivo")
    
    fig_irip = px.bar(
        DATA_IRIP,
        x="Riesgo",
        y="Indicador",
        orientation="h",
        color="Riesgo",
        color_continuous_scale="reds",
        title="Ranking de Riesgo IRIP",
    )
    
    try:
        from ..components.renderers import render_echarts
    except ImportError:
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from components.renderers import render_echarts
        except ImportError:
            render_echarts = None

    if render_echarts:
        try:
            labels = DATA_IRIP["Indicador"].astype(str).tolist()
            vals = [int(v) for v in DATA_IRIP["Riesgo"].tolist()]
            option = {
                "tooltip": {"trigger": "axis"},
                "xAxis": {"type": "value"},
                "yAxis": {"type": "category", "data": labels},
                "series": [{"type": "bar", "data": vals}],
            }
            render_echarts(option, height=260)
        except Exception:
            st.plotly_chart(fig_irip)
    else:
        st.plotly_chart(fig_irip)


def render_anomalies_chart():
    """
    Renderiza el módulo DAD / Detector de anomalías.
    
    Muestra tendencia de anomalías detectadas en el tiempo.
    """
    st.subheader("Módulo DAD / Detector de anomalías")
    
    fig_anomalias = px.line(
        DATA_ANOMALIAS,
        x="Fecha",
        y="Anomalías",
        markers=True,
        title="Tendencia de Anomalías Detectadas",
    )
    
    try:
        from ..components.renderers import render_echarts
    except ImportError:
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from components.renderers import render_echarts
        except ImportError:
            render_echarts = None

    if render_echarts:
        try:
            xs = [str(d.date()) for d in DATA_ANOMALIAS["Fecha"].tolist()]
            ys = [int(v) for v in DATA_ANOMALIAS["Anomalías"].tolist()]
            option = {
                "tooltip": {"trigger": "axis"},
                "xAxis": {"type": "category", "data": xs},
                "yAxis": {"type": "value"},
                "series": [{"type": "line", "data": ys, "showSymbol": True}],
            }
            render_echarts(option, height=300)
        except Exception:
            st.plotly_chart(fig_anomalias)
    else:
        st.plotly_chart(fig_anomalias)


def render_cmi_chart():
    """
    Renderiza el módulo CMI Estratégico.
    
    Muestra cumplimiento por perspectiva (Formación, Investigación, etc.).
    """
    st.subheader("Módulo CMI Estratégico")
    
    fig_cmi = px.bar(
        DATA_CMI,
        x="Perspectiva",
        y="Cumplimiento",
        color="Cumplimiento",
        color_continuous_scale="blues",
        title="Cumplimiento por Perspectiva CMI",
    )
    
    try:
        from ..components.renderers import render_echarts
    except ImportError:
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from components.renderers import render_echarts
        except ImportError:
            render_echarts = None

    if render_echarts:
        try:
            labels = DATA_CMI["Perspectiva"].astype(str).tolist()
            vals = [int(v) for v in DATA_CMI["Cumplimiento"].tolist()]
            option = {
                "tooltip": {"trigger": "axis"},
                "xAxis": {"type": "category", "data": labels},
                "yAxis": {"type": "value"},
                "series": [{"type": "bar", "data": vals}],
            }
            render_echarts(option, height=280)
        except Exception:
            st.plotly_chart(fig_cmi)
    else:
        st.plotly_chart(fig_cmi)
