"""Visualization builders (Plotly charts) for resumen_por_proceso page."""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from streamlit_app.pages.resumen_por_proceso_config import NIVELES_COLORS


def _render_cmi_por_cmi_summary_charts(df: pd.DataFrame) -> tuple:
    """Build Periodicidad and Tipo Indicador summary charts."""
    
    # Chart 1: Pie chart by Periodicidad
    fig_period = go.Figure()
    
    if not df.empty and "Periodicidad" in df.columns:
        period_counts = df["Periodicidad"].value_counts()
        fig_period = go.Figure(data=[go.Pie(
            labels=period_counts.index,
            values=period_counts.values,
            hole=0.3
        )])
        fig_period.update_layout(title="Indicadores por Periodicidad", height=300)
    
    # Chart 2: Bar chart by Tipo Indicador
    fig_tipo = go.Figure()
    
    if not df.empty and "Tipo indicador" in df.columns:
        tipo_counts = df["Tipo indicador"].value_counts()
        fig_tipo = go.Figure(data=[go.Bar(
            y=tipo_counts.index,
            x=tipo_counts.values,
            orientation='h',
            marker_color="#0B5FFF"
        )])
        fig_tipo.update_layout(
            title="Indicadores por Tipo",
            xaxis_title="Cantidad",
            yaxis_title="Tipo",
            height=300
        )
    
    return fig_period, fig_tipo


def _build_processo_compliance_chart(df: pd.DataFrame, proceso_col: str = "Proceso_padre") -> go.Figure:
    """Build horizontal bar chart of processes by compliance."""
    
    if df.empty or proceso_col not in df.columns:
        return go.Figure()
    
    # Group by process and calculate compliance
    proceso_summary = df.groupby(proceso_col).agg({
        "cumplimiento_pct": "mean"
    }).reset_index().sort_values("cumplimiento_pct")
    
    fig = go.Figure(data=[go.Bar(
        y=proceso_summary[proceso_col],
        x=proceso_summary["cumplimiento_pct"],
        orientation='h',
        marker_color="#2E7D32",
        text=proceso_summary["cumplimiento_pct"].apply(lambda x: f"{x:.1f}%"),
        textposition="auto"
    )])
    
    fig.update_layout(
        title="Cumplimiento por Proceso",
        xaxis_title="Cumplimiento (%)",
        yaxis_title="Proceso",
        height=400
    )
    
    return fig


def _build_level_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """Build pie chart of compliance level distribution."""
    
    if df.empty or "Nivel de cumplimiento" not in df.columns:
        return go.Figure()
    
    nivel_counts = df["Nivel de cumplimiento"].value_counts()
    
    colors_list = [NIVELES_COLORS.get(n.lower(), "#6E7781") for n in nivel_counts.index]
    
    fig = go.Figure(data=[go.Pie(
        labels=nivel_counts.index,
        values=nivel_counts.values,
        marker=dict(colors=colors_list)
    )])
    
    fig.update_layout(
        title="Distribución por Nivel de Cumplimiento",
        height=300
    )
    
    return fig
