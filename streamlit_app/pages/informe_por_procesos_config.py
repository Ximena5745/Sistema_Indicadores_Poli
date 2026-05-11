"""Configuration for informe_por_procesos page."""

from pathlib import Path

# Month options
MESES_OPCIONES = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]

# Source styling for proposed indicators
SOURCE_STYLE = {
    "Retos": {"bg": "#e8f5e9", "border": "#66bb6a", "title": "#1b5e20"},
    "Proyectos": {"bg": "#e3f2fd", "border": "#42a5f5", "title": "#0d47a1"},
    "Plan de mejoramiento": {"bg": "#fff3e0", "border": "#ffb74d", "title": "#e65100"},
    "Calidad": {"bg": "#f3e5f5", "border": "#ba68c8", "title": "#4a148c"},
}

# Order of sources to display
SOURCE_ORDER = ["Retos", "Proyectos", "Plan de mejoramiento", "Calidad"]

# Tab names
TAB_NAMES = [
    "Indicadores",
    "Evolución",
    "Calidad",
    "Auditoría",
    "Propuestas",
    "Análisis IA",
]

# Excel configuration for proposed indicators
EXCEL_SHEETS = {
    "Retos": {
        "sheet": "Retos",
        "filter_col": "Aplica Desempeño",
        "select_cols": ["Proceso", "Subproceso", "Indicador Propuesto"],
    },
    "Proyectos": {
        "sheet": "Proyectos",
        "filter_col": "Propuesta",
        "select_cols": ["Proceso", "Subproceso", "Nombre del Indicador Propuesto"],
        "rename": {"Nombre del Indicador Propuesto": "Indicador Propuesto"},
    },
    "Plan": {
        "sheet": "Plan de mejoramiento",
        "header": 1,
        "filter_col": "Propuesta Indicador",
        "select_cols": ["Proceso", "Subproceso", "INDICADOR DE RESULTADO O IMPACTO"],
        "rename": {"INDICADOR DE RESULTADO O IMPACTO": "Indicador Propuesto"},
    },
    "Calidad": {
        "sheet": "Calidad",
        "select_cols": ["Proceso", "Subroceso", "Propuesta SGC (Indicadores)"],
        "rename": {
            "Subroceso": "Subproceso",
            "Propuesta SGC (Indicadores)": "Indicador Propuesto",
        },
    },
}


def get_excel_path() -> Path:
    """Get the path to the proposed indicators Excel file."""
    return (
        Path(__file__).parents[2]
        / "data"
        / "raw"
        / "Propuesta Indicadores"
        / "Indicadores Propuestos.xlsx"
    )
