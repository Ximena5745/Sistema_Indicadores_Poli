"""
services/strategic_indicators/ — Refactorización PHASE 2

Responsabilidad única de cada módulo:
  - loaders.py: Carga de catálogos y datos desde Excel
  - processors.py: Transformaciones y agregaciones (cierre, filtrado)
  - utils.py: Utilidades compartidas (caché, normalización)
"""

# Re-export para backward compatibility
from .loaders import (
    load_pdi_catalog,
    load_cna_catalog,
    load_worksheet_flags,
    load_cierres,
)
from .processors import (
    cierre_por_corte,
    preparar_pdi_con_cierre,
    preparar_cna_con_cierre,
)

__all__ = [
    "load_pdi_catalog",
    "load_cna_catalog",
    "load_worksheet_flags",
    "load_cierres",
    "cierre_por_corte",
    "preparar_pdi_con_cierre",
    "preparar_cna_con_cierre",
]
