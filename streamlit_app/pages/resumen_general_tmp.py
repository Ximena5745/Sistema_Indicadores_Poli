"""
pages/1_Resumen_General.py — Dashboard Estratégico y Operativo PDI & Procesos.

Dashboard moderno con:
  · Indicadores PDI - CMI Estratégico con gráfico de cascada
  · Indicadores por proceso con distribución de cumplimiento
  · Filtro de año (2022-2025)
  · Insights generados dinámicamente
  · Diseño responsive y moderno
"""
import streamlit as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_HTML = ROOT / "streamlit_app" / "dashboard_estrategico.html"


def render():
    st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 1400px;
        }

        .stMarkdown h1 {
            color: #0B5FFF;
            font-weight: 700;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h1 style='color: #0B5FFF; font-size: 2.2rem; font-weight: 700; margin-bottom: 0.25rem;'>
            🏠 Sistema de Indicadores - Politécnico Grancolombiano
        </h1>
        <p style='color: #475569; font-size: 1rem; margin:0;'>
            Dashboard Estratégico y Operativo de Cumplimiento PDI & Procesos
        </p>
    </div>
    """, unsafe_allow_html=True)

    if DASHBOARD_HTML.exists():
        html_content = DASHBOARD_HTML.read_text(encoding='utf-8')
        st.components.v1.html(html_content, height=2800, scrolling=True)
    else:
        st.error(f"El archivo del dashboard no existe en la ruta esperada: `{DASHBOARD_HTML}`")

    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #64748B; font-size: 0.875rem; padding: 1rem;'>
        Dashboard Estratégico v2.0 | Actualizado: 2026 | Sistema de Indicadores - Politécnico Grancolombiano
    </div>
    """, unsafe_allow_html=True)
