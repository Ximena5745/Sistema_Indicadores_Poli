"""
utils/niveles.py — DEPRECADO (desde 11-abr-2026).

Uso CORRECTO:
  • Para constantes visuales: from core.config import NIVEL_COLOR, NIVEL_BG, NIVEL_ICON, NIVEL_ORDEN
  • Para categorización simple: from core.calculos import simple_categoria_desde_porcentaje
  • Para categorización completa: from core.calculos import categorizar_cumplimiento

Este archivo mantiene exports para compatibilidad heredada (será eliminado en próxima versión).
"""
# Re-exports para compatibilidad temporal
from core.config import (
    NIVEL_COLOR,
    NIVEL_BG,
    NIVEL_ICON,
    NIVEL_ORDEN,
    UMBRAL_PELIGRO,
    UMBRAL_ALERTA,
    UMBRAL_SOBRECUMPLIMIENTO,
)
from core.calculos import simple_categoria_desde_porcentaje as nivel_desde_pct

__all__ = [
    'NIVEL_COLOR', 'NIVEL_BG', 'NIVEL_ICON', 'NIVEL_ORDEN',
    'UMBRAL_PELIGRO', 'UMBRAL_ALERTA', 'UMBRAL_SOBRECUMPLIMIENTO',
    'nivel_desde_pct',
]

