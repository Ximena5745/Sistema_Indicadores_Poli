"""
services/strategic_indicators/ — Indicadores estratégicos (PDI, CNA)

Refactorización PHASE 2 (538L → 3 módulos):
  - loaders.py: Carga de datos desde Excel (240L)
  - processors.py: Transformaciones (150L)
  - utils.py: Utilidades compartidas (60L)

Responsabilidad única de cada módulo:
  - loaders: Lectura de catálogos y cierres con caché
  - processors: Filtrado, agregación, enriquecimiento
  - utils: Normalización, caché manual, búsqueda de columnas
"""

from pathlib import Path
from core.config import NIVEL_COLOR

# Re-export para backward compatibility
from .loaders import (
    load_pdi_catalog,
    load_cna_catalog,
    load_worksheet_flags,
    load_cierres,
    load_proyectos_consolidados,
    RAW_XLSX,
    OUT_XLSX,
)
from .processors import (
    cierre_por_corte,
    preparar_pdi_con_cierre,
    preparar_cna_con_cierre,
)
from .utils import (
    NO_APLICA,
    PENDIENTE,
    METRICA,
    SOBRECUMPLIMIENTO,
)

# Mapeo de colores extendido
NIVEL_COLOR_EXT = {
    **NIVEL_COLOR,
    NO_APLICA: "#78909C",
    PENDIENTE: "#BDBDBD",
}

__all__ = [
    "load_pdi_catalog",
    "load_cna_catalog",
    "load_worksheet_flags",
    "load_cierres",
    "load_proyectos_consolidados",
    "cierre_por_corte",
    "preparar_pdi_con_cierre",
    "preparar_cna_con_cierre",
    "NIVEL_COLOR_EXT",
    "NO_APLICA",
    "PENDIENTE",
    "METRICA",
    "SOBRECUMPLIMIENTO",
    "RAW_XLSX",
    "OUT_XLSX",
]
