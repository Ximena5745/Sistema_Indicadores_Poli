"""
Configuration and constants for seguimiento_reportes page.
"""

from pathlib import Path

# Path to seguimiento data
RUTA_SEGUIMIENTO = (
    Path(__file__).resolve().parents[2] / "data" / "output" / "Seguimiento_Reporte.xlsx"
)

# Window in months per periodicity before marking as overdue
VENTANA_MESES: dict[str, int] = {
    "mensual": 1,
    "bimestral": 2,
    "trimestral": 3,
    "semestral": 6,
    "anual": 12,
}

# Month names
MESES_OPCIONES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]

# Color mapping for estados
COLOR_ESTADO = {
    "Reportado": "#28a745",
    "Pendiente": "#ffc107",
    "No aplica": "#6c757d",
}
