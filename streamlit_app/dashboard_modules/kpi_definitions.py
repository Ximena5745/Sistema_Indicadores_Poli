"""
KPI definitions and data structures for dashboard.

Contains KPI data, their values, and rendering logic for dashboard metrics display.
"""
import pandas as pd
import streamlit as st


# ─── KPI Definitions ───────────────────────────────────────────────────────────
KPI_DEFINITIONS = [
    {
        "label": "Total indicadores",
        "valor": 387,
        "subtexto": "Kawak + API",
        "color": "#00b8d4"
    },
    {
        "label": "En peligro",
        "valor": 20,
        "subtexto": "+19 vs ant. · 5.2%",
        "color": "#ff3b30"
    },
    {
        "label": "En alerta",
        "valor": 24,
        "subtexto": "+21 vs ant. · 6.2%",
        "color": "#ffab00"
    },
    {
        "label": "Cumplimiento",
        "valor": 85,
        "subtexto": "+70 vs ant. · 22%",
        "color": "#00c853"
    },
    {
        "label": "Sobrecumplimiento",
        "valor": 115,
        "subtexto": "+108 vs ant. · 29.7%",
        "color": "#00b8d4"
    },
]

# ─── Simulation Data ───────────────────────────────────────────────────────────

DATA_IRIP = pd.DataFrame(
    {
        "Indicador": [
            "Graduación oportuna",
            "Cobertura banda ancha",
            "Publicaciones indexadas",
            "Tasa retención",
            "Financiación externa",
        ],
        "Riesgo": [87, 82, 79, 73, 71],
    }
)

DATA_ANOMALIAS = pd.DataFrame(
    {
        "Fecha": pd.date_range(start="2026-01-01", periods=10, freq="M"),
        "Anomalías": [3, 5, 2, 4, 6, 3, 7, 5, 4, 6],
    }
)

DATA_CMI = pd.DataFrame(
    {
        "Perspectiva": ["Formación", "Investigación", "Extensión", "Internacionalización"],
        "Cumplimiento": [85, 78, 92, 88],
    }
)

# ─── KPI Rendering ───────────────────────────────────────────────────────────

def render_kpis(kpi_definitions: list = None):
    """
    Renderiza filas de métricas KPI usando Streamlit columns y st.metric.
    
    Args:
        kpi_definitions: Lista de diccionarios con keys: label, valor, subtexto, color.
                        Por defecto: KPI_DEFINITIONS
    """
    if kpi_definitions is None:
        kpi_definitions = KPI_DEFINITIONS

    cols = st.columns(len(kpi_definitions))
    for col, kpi in zip(cols, kpi_definitions):
        col.metric(label=kpi["label"], value=kpi["valor"], delta=kpi["subtexto"])
