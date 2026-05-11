"""
core/domain/categorization.py — CATEGORIZACIÓN DE CUMPLIMIENTO

PROPÓSITO:
  Lógica de decisión sobre categorías de cumplimiento para garantizar
  consistencia en todo el sistema.

  Soporta:
  - Plan Anual: umbral 95%, máximo 100%
  - Regular:    umbral 100%, máximo 130%

IMPORTAR:
  from core.domain.categorization import (
      CategoriaCumplimiento,
      categorizar_cumplimiento,
      nivel_desde_cumplimiento,
  )
"""

from enum import Enum
import pandas as pd
import logging

# Importar configuración (IDS_PLAN_ANUAL y umbrales dinámicos)
from core.config import (
    IDS_PLAN_ANUAL,
    UMBRAL_PELIGRO,
    UMBRAL_ALERTA,
    UMBRAL_SOBRECUMPLIMIENTO,
    UMBRAL_ALERTA_PA,
    UMBRAL_SOBRECUMPLIMIENTO_PA,
)

logger = logging.getLogger(__name__)


class CategoriaCumplimiento(Enum):
    """
    Categorías oficiales de cumplimiento.

    Reemplaza strings literales para garantizar tipo-seguridad.
    """

    PELIGRO = "Peligro"
    ALERTA = "Alerta"
    CUMPLIMIENTO = "Cumplimiento"
    SOBRECUMPLIMIENTO = "Sobrecumplimiento"
    SIN_DATO = "Sin dato"


def categorizar_cumplimiento(cumplimiento, id_indicador=None):
    """
    Lógica ÚNICA y oficial de categorización de cumplimiento.

    Soporta:
    - Plan Anual: umbral 95%, máximo 100%
    - Regular:    umbral 100%, máximo 130%

    IDs Plan Anual se cargan DINÁMICAMENTE del Excel.

    Parámetros
    ----------
    cumplimiento : float, str, NaN
        Cumplimiento normalizado (0.0 a 1.3, donde 1.0 = 100%)
        Acepta strings con "%" (ej: "95%") y formatos latinoamericanos.

    id_indicador : str, int, opcional
        ID del indicador para auto-detectar si es Plan Anual.
        Si None, se asume régimen Regular.

    Retorna
    -------
    str
        Una de: "Peligro", "Alerta", "Cumplimiento", "Sobrecumplimiento", "Sin dato"

    Ejemplos
    --------
    >>> categorizar_cumplimiento(0.95, id_indicador="373")  # Plan Anual
    'Cumplimiento'

    >>> categorizar_cumplimiento(0.95, id_indicador="123")  # Regular
    'Alerta'

    >>> categorizar_cumplimiento(1.05, id_indicador="373")  # PA no tiene sobrecump
    'Cumplimiento'
    """
    # Validar NaN - manejar tipos complejos
    try:
        if pd.isna(cumplimiento):
            return CategoriaCumplimiento.SIN_DATO.value
    except (ValueError, TypeError):
        # pd.isna falla con arrays, dicts, etc.
        logger.debug(f"Tipo inválido para pd.isna: {type(cumplimiento)}")
        return CategoriaCumplimiento.SIN_DATO.value

    # Auto-detectar si es Plan Anual
    es_plan_anual = False
    if id_indicador is not None:
        es_plan_anual = str(id_indicador).strip() in IDS_PLAN_ANUAL

    # Convertir a float - incluye manejo de strings
    try:
        # Si es string, limpiar y convertir
        if isinstance(cumplimiento, str):
            cumpl_clean = cumplimiento.replace("%", "").strip()

            # Detectar formato:
            # - Si tiene coma, es latinoamericano: "0,95" o "1.234,56"
            # - Si no tiene coma, es formato decimal directo (English): "0.95" o "1234.56"
            if "," in cumpl_clean:
                # Formato latinoamericano: remove "." (thousands), replace "," with "."
                cumpl_clean = cumpl_clean.replace(".", "").replace(",", ".")
            # else: formato English, usar como está

            c = float(cumpl_clean)
        else:
            c = float(cumplimiento)
    except (TypeError, ValueError):
        logger.debug(f"No se pudo convertir cumplimiento '{cumplimiento}' a float")
        return CategoriaCumplimiento.SIN_DATO.value

    # Aplicar lógica según tipo de indicador
    if es_plan_anual:
        # ═══ PLAN ANUAL: umbral 95%, máximo 100% ════════════════════════════════
        if c < UMBRAL_PELIGRO:
            return CategoriaCumplimiento.PELIGRO.value
        elif c < UMBRAL_ALERTA_PA:
            return CategoriaCumplimiento.ALERTA.value
        elif c <= UMBRAL_SOBRECUMPLIMIENTO_PA:
            return CategoriaCumplimiento.CUMPLIMIENTO.value
        else:
            # Los PA no pueden sobrecumplir (máximo 100%)
            return CategoriaCumplimiento.SOBRECUMPLIMIENTO.value
    else:
        # ═══ REGULAR: umbral 100%, máximo 130% ═════════════════════════════════
        if c < UMBRAL_PELIGRO:
            return CategoriaCumplimiento.PELIGRO.value
        elif c < UMBRAL_ALERTA:
            return CategoriaCumplimiento.ALERTA.value
        elif c < UMBRAL_SOBRECUMPLIMIENTO:
            return CategoriaCumplimiento.CUMPLIMIENTO.value
        else:
            return CategoriaCumplimiento.SOBRECUMPLIMIENTO.value


def nivel_desde_cumplimiento(cumplimiento, id_indicador=None):
    """
    DEPRECATED: Usar categorizar_cumplimiento() en su lugar.

    Se mantiene para compatibilidad con código antiguo.
    """
    logger.warning(
        "nivel_desde_cumplimiento() está DEPRECATED. "
        "Usar categorizar_cumplimiento() en su lugar."
    )
    return categorizar_cumplimiento(cumplimiento, id_indicador)
