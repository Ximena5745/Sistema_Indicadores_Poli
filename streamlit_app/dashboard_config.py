"""
Dashboard configuration - Backward compatibility wrapper.

This module maintains backward compatibility by re-exporting dashboard components
from the refactored dashboard_modules package.

For new code, import directly from dashboard_modules:
    from dashboard_modules import render_kpis, DATA_IRIP
"""
from dashboard_modules import (
    KPI_DEFINITIONS,
    DATA_IRIP,
    DATA_ANOMALIAS,
    DATA_CMI,
    render_kpis,
    render_irip_chart,
    render_anomalies_chart,
    render_cmi_chart,
)

# Backward compatibility - old function name
mostrar_kpis = render_kpis

__all__ = [
    "KPI_DEFINITIONS",
    "DATA_IRIP",
    "DATA_ANOMALIAS",
    "DATA_CMI",
    "render_kpis",
    "mostrar_kpis",
    "render_irip_chart",
    "render_anomalies_chart",
    "render_cmi_chart",
]
