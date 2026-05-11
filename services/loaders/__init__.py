"""
services/loaders/__init__.py — PACKAGE DE CARGADORES

Módulos de carga de datos con soporte para caché Streamlit.

Subpaquetes:
- utils: Utilidades (normalización, renombramiento, conversión)
- excel: Cargadores de archivos Excel
- pipeline: ETL pipeline (5 fases)

IMPORTAR:
  from services.loaders.utils import renombrar_columnas, id_a_str
  from services.loaders.excel import cargar_om, cargar_plan_accion
"""

from .utils import (
    ascii_lower,
    renombrar_columnas,
    id_a_str,
    obtener_rename_map,
)

__all__ = [
    "ascii_lower",
    "renombrar_columnas",
    "id_a_str",
    "obtener_rename_map",
]
