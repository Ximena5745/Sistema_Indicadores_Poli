"""Visualization functions (Plotly charts) for resumen_general page."""

import pandas as pd
import plotly.graph_objects as go
from streamlit_app.pages.resumen_general_config import LINEA_COLORS


def _build_sunburst(pdi_df: pd.DataFrame) -> go.Figure:
    """Build interactive sunburst chart for strategic lines and objectives.
    
    Hierarchy:
    - Center: Strategic Lines
    - Outer ring: Strategic Objectives
    """
    df = pdi_df.copy() if not pdi_df.empty else pd.DataFrame()
    
    if df.empty or "Linea" not in df.columns or "Objetivo" not in df.columns:
        # Return empty chart
        return go.Figure(data=[go.Sunburst(
            labels=["Sin datos"],
            parents=[""],
            values=[1],
            marker=dict(colors=["#6B728E"])
        )]).update_layout(height=400)
    
    # Prepare data for sunburst
    df = df[df["Linea"].notna() & df["Objetivo"].notna()].copy()
    df = df[df["Linea"].astype(str).str.strip() != ""]
    df = df[df["Objetivo"].astype(str).str.strip() != ""]
    
    if "cumplimiento_pct" in df.columns:
        df["cumplimiento_pct"] = pd.to_numeric(df["cumplimiento_pct"], errors="coerce")
        df = df[df["cumplimiento_pct"].notna()]
    
    if df.empty:
        return go.Figure(data=[go.Sunburst(
            labels=["Sin datos"],
            parents=[""],
            values=[1],
            marker=dict(colors=["#6B728E"])
        )]).update_layout(height=400)
    
    # Aggregate by line and objective
    lines = df.groupby("Linea", dropna=False)["cumplimiento_pct"].mean().reset_index()
    objectives = df.groupby(["Linea", "Objetivo"], dropna=False)["cumplimiento_pct"].mean().reset_index()
    
    labels = []
    parents = []
    values = []
    colors = []
    
    # Add lines (center)
    for _, row in lines.iterrows():
        linea = str(row["Linea"]).strip()
        labels.append(linea)
        parents.append("")
        values.append(1)
        colors.append(LINEA_COLORS.get(linea, "#6B728E"))
    
    # Add objectives (outer ring)
    for _, row in objectives.iterrows():
        linea = str(row["Linea"]).strip()
        objetivo = str(row["Objetivo"]).strip()
        labels.append(objetivo)
        parents.append(linea)
        values.append(1)
        colors.append(LINEA_COLORS.get(linea, "#6B728E"))
    
    fig = go.Figure(data=[go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors),
        branchvalues="total"
    )])
    
    fig.update_layout(height=400)
    return fig


def _build_gantt_for_proyectos(pdi_estrategico: pd.DataFrame, 
                               linea_summary: pd.DataFrame) -> go.Figure:
    """Build Gantt chart for projects by strategic line."""
    if linea_summary.empty or "Linea" not in linea_summary.columns:
        return go.Figure()
    
    # Create simple horizontal bar chart (Gantt-like)
    fig = go.Figure(data=[
        go.Bar(
            y=linea_summary["Linea"],
            x=linea_summary.get("N_Proyectos", 0),
            orientation='h',
            marker=dict(color="#1FB2DE")
        )
    ])
    
    fig.update_layout(
        title="Proyectos por Línea Estratégica",
        xaxis_title="Número de Proyectos",
        yaxis_title="Línea",
        height=300
    )
    
    return fig
