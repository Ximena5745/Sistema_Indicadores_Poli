"""
Dashboard configuration module.
"""
from .kpi_definitions import KPI_DEFINITIONS, DATA_IRIP, DATA_ANOMALIAS, DATA_CMI, render_kpis
from .visualizations import render_irip_chart, render_anomalies_chart, render_cmi_chart

__all__ = [
    "KPI_DEFINITIONS",
    "DATA_IRIP",
    "DATA_ANOMALIAS",
    "DATA_CMI",
    "render_kpis",
    "render_irip_chart",
    "render_anomalies_chart",
    "render_cmi_chart",
]
