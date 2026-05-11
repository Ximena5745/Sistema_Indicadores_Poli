"""Configuration module for resumen_general page."""

from pathlib import Path
from core.config import DATA_OUTPUT

# Paths
PATH_CONSOLIDADO = DATA_OUTPUT / "Resultados Consolidados.xlsx"
PATH_RETOS = Path("data/raw/Retos/Plan de retos.xlsx")

# Strategic Line Colors
LINEA_COLORS = {
    "Expansión": "#FBAF17",
    "Transformación organizacional": "#42F2F2",
    "Calidad": "#EC0677",
    "Experiencia": "#1FB2DE",
    "Sostenibilidad": "#A6CE38",
    "Educación para toda la vida": "#0F385A",
}

# Badge colors (background, text)
LINEA_COLORS_BADGE = {
    "expansion": ("#FBAF17", "#FFFFFF"),
    "transformacion organizacional": ("#42F2F2", "#0A4A4A"),
    "calidad": ("#EC0677", "#FFFFFF"),
    "experiencia": ("#1FB2DE", "#FFFFFF"),
    "sostenibilidad": ("#A6CE38", "#1A2E05"),
    "educacion para toda la vida": ("#0F385A", "#FFFFFF"),
}

# Month mapping
MES_MAP = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

# Compliance thresholds
THRESHOLD_SOBRECUMPLIMIENTO = 105
THRESHOLD_CUMPLIMIENTO = 100
THRESHOLD_ALERTA = 80

# Status colors
STATUS_COLORS = {
    "Sobrecumplimiento": "#173D66",
    "Cumplimiento": "#16A34A",
    "Alerta": "#F59E0B",
    "Peligro": "#D32F2F",
    "Total": "#0B5FFF",
}

# Column names and configurations
TEXT_COLS_NORMALIZE = [
    "Linea",
    "Objetivo",
    "Meta_PDI",
    "Indicador",
    "Clasificacion",
    "Proceso",
    "Subproceso",
    "Area",
    "tipo",
    "Estado",
]

# Strategic definitions
STRATEGIC_DEFS = [
    {"key": "expansion", "alt": [], "label": "Expansion", "icon": "🚀", "color": "#FBAF17"},
    {"key": "transformacion organizacional", "alt": ["transformacion organizacional"], "label": "Transformacion organizacional", "icon": "📈", "color": "#42F2F2"},
    {"key": "calidad", "alt": [], "label": "Calidad", "icon": "🏅", "color": "#EC0677"},
    {"key": "experiencia", "alt": [], "label": "Experiencia", "icon": "💡", "color": "#1FB2DE"},
    {"key": "sostenibilidad", "alt": ["sustentabilidad"], "label": "Sostenibilidad", "icon": "🌱", "color": "#A6CE38"},
    {"key": "educacion para toda la vida", "alt": ["educacion para toda la vida"], "label": "Educacion para toda la vida", "icon": "🎓", "color": "#0F385A"},
]

# CSS classes
DASHBOARD_CSS_CLASSES = {
    "rg-header": "header gradiente azul marino",
    "rg-panel": "panel contenedor fondo claro",
    "rg-card": "cards para métricas",
    "rg-chip": "chips de métricas pequeños",
    "rg-ia": "narrativa ejecutiva (IA)",
    "rg-table": "tablas de variación",
    "rg-process-card": "cards de procesos",
}
