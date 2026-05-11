"""Configuration module for resumen_por_proceso page."""

from pathlib import Path

# Month configuration
MESES_OPCIONES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]

MES_MAP = {m.upper(): i + 1 for i, m in enumerate(MESES_OPCIONES)}

# Compliance level colors
NIVELES_COLORS = {
    "sobrecumplimiento": "#6699FF",
    "cumplimiento": "#2E7D32",
    "alerta": "#F9A825",
    "peligro": "#C62828",
    "sin dato": "#6E7781",
}

# Compliance level names
COMPLIANCE_LEVELS = ["Sobrecumplimiento", "Cumplimiento", "Alerta", "Peligro"]

# Compliance thresholds
THRESHOLD_SOBRECUMPLIMIENTO = 105
THRESHOLD_CUMPLIMIENTO = 100
THRESHOLD_ALERTA = 80

# Audit categories and colors
AUDIT_CATEGORIES = {
    "Fortalezas": {"color": "#2E7D32", "emoji": "✅"},
    "Oportunidades": {"color": "#1FB2DE", "emoji": "💡"},
    "Hallazgos": {"color": "#F9A825", "emoji": "🔍"},
    "No Conformidades": {"color": "#C62828", "emoji": "❌"},
    "Recomendación": {"color": "#6699FF", "emoji": "📝"},
}

# Data paths
PATH_AUDITORIA = Path("data/raw/Auditoria/auditoria_resultado.xlsx")
PATH_CALIDAD = Path("data/raw/Monitoreo/Monitoreo_Informacion_Procesos 2025.xlsx")
PATH_CONSOLIDADO_ANALISIS = Path("data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx")
PATH_INDICADORES_CMI = Path("data/raw/Indicadores por CMI.xlsx")

# Pagination settings
ITEMS_PER_PAGE = 15

# Truncation length for text summaries
TEXT_SUMMARY_CHARS = 300
