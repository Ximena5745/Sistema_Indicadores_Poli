"""Configuration for tablero_operativo page."""

from pathlib import Path

# Paths
ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "data" / "output" / "artifacts"

# Constants
NO_APLICA = "No aplica"
PEND = "Pendiente de reporte"

# Colors for levels
NIVEL_COLOR_EXT = {
    "Peligro": "#C62828",
    "Alerta": "#F9A825",
    "Cumplimiento": "#2E7D32",
    "Sobrecumplimiento": "#6699FF",
    "No aplica": "#6E7781",
    "Pendiente de reporte": "#9E9E9E",
}

# Background colors for levels
NIVEL_BG_EXT = {
    "Peligro": "#FFCDD2",
    "Alerta": "#FEF3D0",
    "Cumplimiento": "#E8F5E9",
    "Sobrecumplimiento": "#DCE6FF",
    "No aplica": "#F5F5F5",
    "Pendiente de reporte": "#F5F5F5",
}

# Icons for levels
NIVEL_ICON_EXT = {
    "Peligro": "🔴",
    "Alerta": "🟡",
    "Cumplimiento": "🟢",
    "Sobrecumplimiento": "🔵",
    "No aplica": "⚫",
    "Pendiente de reporte": "⚪",
}

# Kanban columns for status
KANBAN_COLS = [
    "Peligro",
    "Alerta",
    "Cumplimiento",
    "Sobrecumplimiento",
    "No aplica",
    "Pendiente de reporte",
]

# Severity ordering
ORDEN_SEV = {
    "Peligro": 1,
    "Alerta": 2,
    "Cumplimiento": 3,
    "Sobrecumplimiento": 4,
    "No aplica": 5,
    "Pendiente de reporte": 6,
}

# Months
MESES = [
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

# Month to number mapping
MES_NUM = {m: i + 1 for i, m in enumerate(MESES)}

# Periodicity to window months mapping
VENTANA_MESES = {
    "Mensual": 1,
    "Bimestral": 2,
    "Trimestral": 3,
    "Semestral": 6,
    "Anual": 12,
}
