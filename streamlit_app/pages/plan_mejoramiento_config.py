"""Configuration for plan_mejoramiento page."""

from datetime import date as _date

# Semester mapping
CORTE_SEMESTRAL = {
    "Junio": 6,
    "Diciembre": 12,
}

# Level icons for CNA indicators
NIVEL_ICONS_CNA = {
    "Peligro": "🔴",
    "Alerta": "🟡",
    "Cumplimiento": "🟢",
    "Sobrecumplimiento": "🔵",
    "No aplica": "⚫",
    "Pendiente de reporte": "⚪",
}

# Display columns for CNA table
COLUMNAS_CNA_BASE = [
    "Id",
    "Indicador",
    "Factor",
    "Caracteristica",
    "cumplimiento_pct",
    "Nivel de cumplimiento",
]

COLUMNAS_CNA_OPCIONALES = [
    "Meta",
    "Ejecucion",
    "Sentido",
    "Meta_Signo",
    "Meta s",
    "MetaS",
    "Decimales_Meta",
    "Decimales",
    "DecMeta",
    "Ejecucion_Signo",
    "Ejecución s",
    "Ejecucion s",
    "Ejecucion_s",
    "EjecS",
    "Decimales_Ejecucion",
    "DecimalesEje",
    "DecEjec",
    "Anio",
    "Mes",
    "Fecha",
]

# Column renaming map for display
COLUMNAS_RENAME_CNA = {
    "cumplimiento_pct": "Cumplimiento (%)",
    "Nivel de cumplimiento": "Nivel",
    "Anio": "Año cierre",
    "Mes": "Mes cierre",
    "Caracteristica": "Característica",
    "Meta": "Meta",
    "Ejecucion": "Ejecución",
}

# Streamlit column config for CNA table
STREAMLIT_COLUMN_CONFIG = {
    "Id": {"type": "text", "width": "small"},
    "Indicador": {"type": "text", "width": "large"},
    "Factor": {"type": "text", "width": "medium"},
    "Característica": {"type": "text", "width": "medium"},
    "Nivel": {"type": "text", "width": "medium"},
    "Cumplimiento (%)": {"type": "number", "format": "%.1f", "width": "small"},
    "Meta": {"type": "text", "width": "small"},
    "Ejecución": {"type": "text", "width": "small"},
    "Sentido": {"type": "text", "width": "small"},
    "Año cierre": {"type": "number", "format": "%d", "width": "small"},
    "Mes cierre": {"type": "number", "format": "%d", "width": "small"},
    "Fecha": {"type": "datetime", "width": "small"},
}


def get_default_corte(anios: list[int]) -> tuple[int, str]:
    """Get default year and semester for filtering.
    
    Args:
        anios: List of available years
    
    Returns:
        Tuple of (year, semester_name)
    """
    if 2025 in anios:
        return 2025, "Diciembre"
    if anios:
        return anios[-1], "Diciembre"
    return _date.today().year, "Diciembre"
