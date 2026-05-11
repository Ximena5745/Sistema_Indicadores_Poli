"""Configuration for cmi_estrategico page."""

from datetime import date as _date

# Semester mapping
CORTE_SEMESTRAL = {
    "Junio": 6,
    "Diciembre": 12,
}

# Tab names for CMI Estratégico
TAB_NAMES = [
    "Resumen",
    "Listado",
    "Líneas Estratégicas",
    "Alertas",
]

# Strategic line colors
LINEA_COLORS = {
    "Expansión": "#FBAF17",
    "Transformación organizacional": "#42F2F2",
    "Calidad": "#EC0677",
    "Experiencia": "#1FB2DE",
    "Sostenibilidad": "#A6CE38",
    "Educación para toda la vida": "#0F385A",
}

# Level icons for PDI indicators
NIVEL_ICONS_CMI = {
    "Peligro": "🚩",
    "Alerta": "⚑",
    "Cumplimiento": "🏁",
    "Sobrecumplimiento": "🎌",
    "No aplica": "🏴",
    "Pendiente de reporte": "🏳️",
}

# Level flag colors for HTML rendering
NIVEL_FLAG_COLORS = {
    "Peligro": "#C62828",
    "Alerta": "#F9A825",
    "Cumplimiento": "#2E7D32",
    "Sobrecumplimiento": "#6699FF",
    "No aplica": "#616161",
    "Pendiente de reporte": "#9E9E9E",
}

# Neon-blue style for segmented control
NEON_BLUE_STYLE = """<style>
[data-testid="stSegmentedControl"] button[aria-pressed="true"] {
    background: linear-gradient(135deg,#00B4FF 0%,#0066FF 100%) !important;
    color:#FFFFFF !important;
    border-color:#00B4FF !important;
    box-shadow:0 0 10px rgba(0,180,255,.55),0 0 3px rgba(0,180,255,.25) !important;
}
</style>"""


def get_default_anio(anios: list[int]) -> int:
    """Get default year for filtering.
    
    Args:
        anios: List of available years
    
    Returns:
        Default year (2025 if available, else latest, else current year)
    """
    if 2025 in anios:
        return 2025
    if anios:
        return anios[-1]
    return _date.today().year


def get_default_corte(anio: int | None) -> str:
    """Get default semester for year.
    
    Args:
        anio: Year (None means use current year)
    
    Returns:
        Semester name ("Junio" or "Diciembre")
    """
    if anio is None:
        return "Diciembre"

    today = _date.today()
    # Closed years: always December
    if int(anio) < today.year:
        return "Diciembre"

    # Current year not finished: use June if after July 20
    if today > _date(today.year, 7, 20):
        return "Junio"

    return "Diciembre"
