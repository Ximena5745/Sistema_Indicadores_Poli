"""
core/semantica.py — MÓDULO ÚNICO DE CATEGORIZACIÓN DE CUMPLIMIENTO

PROPÓSITO:
  Centralizar la lógica de decisión sobre categorías de cumplimiento
  para garantizar consistencia en todo el sistema.

  Reemplaza 8 copias del mismo código repartidas por diferentes módulos.

CRITERIO OFICIAL (21 abr 2026):
  - Plan Anual: cumplimiento ≥ 95% = Cumplimiento | máximo 100%
  - Regular:    cumplimiento ≥ 100% = Cumplimiento | máximo 130%

  Los IDs Plan Anual se cargan DINÁMICAMENTE del Excel:
  "Indicadores por CMI.xlsx" (columnas "Plan anual"=1 OR "Proyecto"=1)

IMPORTAR:
  from core.semantica import categorizar_cumplimiento, CategoriaCumplimiento
"""

from enum import Enum
import pandas as pd
import numpy as np
import logging

# Importar configuración (incluyendo IDS_PLAN_ANUAL ahora dinámico)
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


def obtener_color_categoria(categoria):
    """
    Retorna el color hex para una categoría.

    Parámetros
    ----------
    categoria : str
        Una de: "Peligro", "Alerta", "Cumplimiento", "Sobrecumplimiento", "Sin dato"

    Retorna
    -------
    str
        Color hex (ej: "#D32F2F")
    """
    from core.config import COLOR_CATEGORIA

    return COLOR_CATEGORIA.get(categoria, COLOR_CATEGORIA.get("Sin dato"))


def obtener_icono_categoria(categoria):
    """
    Retorna el ícono (emoji) para una categoría.

    Parámetros
    ----------
    categoria : str
        Una de: "Peligro", "Alerta", "Cumplimiento", "Sobrecumplimiento", "Sin dato"

    Retorna
    -------
    str
        Emoji (ej: "🔴")
    """
    from core.config import ICONOS_CATEGORIA

    return ICONOS_CATEGORIA.get(categoria, "⚪")


# ═══════════════════════════════════════════════════════════════════════════════
# RECALCULAR CUMPLIMIENTO FALTANTE (Problema #4)
# ═══════════════════════════════════════════════════════════════════════════════


def recalcular_cumplimiento_faltante(meta, ejecucion, sentido="Positivo", id_indicador=None):
    """
    Recalcula cumplimiento cuando falta: ejecución / meta (o meta / ejecución según sentido).

    PROPÓSITO:
        Centralizar la lógica de recálculo que estaba duplicada en 3 lugares:
        1. services/data_loader.py líneas 248-276 (defectuosa)
        2. services/strategic_indicators.py load_cierres() (defectuosa)
        3. scripts/etl/cumplimiento.py (CORRECTA, ahora centralizada)

    SOLUCIÓN PROBLEMA #2:
        Unifica 3 implementaciones divergentes en 1 lógica oficial global.
        Implementa casos especiales correctamente:
        - Meta=0 & Ejec=0 → 1.0 (éxito perfecto, cero es logro)
        - Negativo & Ejec=0 → 1.0 (cero es perfecto en indicadores de "menos es mejor")

    LÓGICA:
        1. Validar meta y ejecucion no sean None
        2. Convertir a float
        3. CASOS ESPECIALES (nuevos en Problema #2):
           - Si Meta=0 y Ejec=0: retorna 1.0 (éxito)
           - Si Sentido=Negativo y Ejec=0 (Meta>0): retorna 1.0 (perfecto)
        4. Cálculo estándar:
           - Si sentido="Positivo": cumplimiento = ejecucion / meta
           - Si sentido="Negativo": cumplimiento = meta / ejecucion
        5. Aplicar tope según tipo de indicador:
           - Plan Anual: [0, 1.0]
           - Regular: [0, 1.3]

    Parámetros
    ----------
    meta : float, int, str
        Meta del período

    ejecucion : float, int, str
        Ejecución del período

    sentido : str, default "Positivo"
        "Positivo": más es mejor (cumpl = ejec/meta)
        "Negativo": menos es mejor (cumpl = meta/ejec)

    id_indicador : str, int, optional
        ID del indicador para detectar Plan Anual y aplicar tope correcto

    Retorna
    -------
    float
        Cumplimiento recalculado: [0, 1.0] para PA, [0, 1.3] para regular
        Retorna NaN si no se puede calcular (entrada inválida, meta=0 pero ejec≠0, etc.)

    Ejemplos
    --------
    >>> recalcular_cumplimiento_faltante(100, 50)  # Regular, Positivo
    0.5

    >>> recalcular_cumplimiento_faltante(100, 150, sentido="Positivo")  # Sobrecump
    1.3  # Tope aplicado

    >>> recalcular_cumplimiento_faltante(100, 150, sentido="Positivo", id_indicador="45")  # PA
    1.0  # Tope PA más restrictivo

    >>> recalcular_cumplimiento_faltante(0, 0, sentido="Positivo")  # CASO ESPECIAL
    1.0  # Meta=0 & Ejec=0 = éxito perfecto

    >>> recalcular_cumplimiento_faltante(1.6, 0, sentido="Negativo")  # CASO ESPECIAL
    1.0  # Negativo & Ejec=0 = cero es perfecto
    """
    # Validar entradas
    if meta is None or ejecucion is None:
        logger.debug(f"Meta o Ejecucion es None: meta={meta}, ejec={ejecucion}")
        return float("nan")

    # Convertir a float
    try:
        m = float(meta)
        e = float(ejecucion)
    except (TypeError, ValueError):
        logger.debug(f"No se pudo convertir meta={meta} o ejecucion={ejecucion} a float")
        return float("nan")

    # Validar no sean NaN
    if pd.isna(m) or pd.isna(e):
        logger.debug(f"Meta o Ejecucion es NaN: meta={m}, ejec={e}")
        return float("nan")

    # Normalizar sentido
    sentido_str = str(sentido).strip().lower() if sentido else "positivo"

    # ════════════════════════════════════════════════════════════════════════════
    # CASOS ESPECIALES (PROBLEMA #2 - Nuevos)
    # ════════════════════════════════════════════════════════════════════════════

    # CASO ESPECIAL 1: Meta=0 & Ejecución=0 → 1.0 (100% éxito perfecto)
    # Interpretación: "Meta de cero logros (muertes, accidentes), cero logrados = perfecto"
    # Ejemplo: Mortalidad Laboral (meta=0 muertes, ejecutado=0 muertes)
    if m == 0 and e == 0:
        logger.debug("CASO ESPECIAL: Meta=0 y Ejec=0 → 100% (éxito perfecto)")
        return 1.0

    # CASO ESPECIAL 2: Sentido Negativo & Ejecución=0 (Meta>0) → 1.0 (100% perfecto)
    # Interpretación: "Indicador donde menos es mejor, cero logrado es perfecto"
    # Ejemplo: Accidentalidad (meta=1.6 accidentes permitidos, ejecutado=0 accidentes = perfecto)
    if sentido_str == "negativo" and e == 0 and m > 0:
        logger.debug("CASO ESPECIAL Negativo: Ejec=0 y Meta>0 → 100% (cero es perfecto)")
        return 1.0

    # ════════════════════════════════════════════════════════════════════════════
    # CÁLCULO ESTÁNDAR
    # ════════════════════════════════════════════════════════════════════════════

    try:
        if sentido_str == "positivo":
            # Más es mejor: cumplimiento = ejecución / meta
            if m == 0:
                logger.debug("Positivo & Meta=0 & Ejec≠0: no se puede dividir")
                return float("nan")
            raw = e / m
        elif sentido_str == "negativo":
            # Menos es mejor: cumplimiento = meta / ejecución
            if e == 0:
                logger.debug("Negativo & Ejec=0 & Meta=0: ya fue manejado como caso especial")
                return float("nan")
            raw = m / e
        else:
            logger.warning(f"Sentido desconocido: {sentido}, asumiendo Positivo")
            if m == 0:
                return float("nan")
            raw = e / m
    except ZeroDivisionError:
        logger.debug(f"División por cero: meta={m}, ejecucion={e}")
        return float("nan")

    # Validar resultado
    if pd.isna(raw):
        return float("nan")

    # Aplicar tope según tipo de indicador
    es_plan_anual = False
    if id_indicador is not None:
        es_plan_anual = str(id_indicador).strip() in IDS_PLAN_ANUAL

    tope = 1.0 if es_plan_anual else 1.3

    # Retornar acotado [0, tope]
    resultado = min(max(raw, 0.0), tope)
    logger.debug(
        f"Recalc cumpl: meta={m}, ejec={e}, sentido={sentido_str}, "
        f"PA={es_plan_anual}, raw={raw:.3f}, resultado={resultado:.3f}"
    )

    return resultado


# ═══════════════════════════════════════════════════════════════════════════════
# NORMALIZACIÓN DE VALORES
# ═══════════════════════════════════════════════════════════════════════════════


def normalizar_valor_a_porcentaje(valor, tiene_porcentaje=None):
    """
    Normaliza un valor numérico a porcentaje (0-100, 0-130, etc).

    Problema #9 FIX: Detecta si el valor tiene símbolo % o no para normalizar.

    LÓGICA:
      - Si tiene_porcentaje=True: valor es porcentaje → retorna como está
      - Si tiene_porcentaje=False: valor es decimal (0-1.3) → multiplica por 100
      - Si tiene_porcentaje=None: intenta detectar automáticamente del string

    PARÁMETROS:
      valor: float, int, str, NaN
        Valor a normalizar
      tiene_porcentaje: None, True, False
        Si True: es porcentaje, mantener
        Si False: es decimal, multiplicar por 100
        Si None: detectar del string si tiene "%"

    RETORNA:
      float: Valor normalizado a porcentaje (0-130), o NaN si inválido

    EJEMPLOS:
      >>> normalizar_valor_a_porcentaje(0.95, tiene_porcentaje=False)  # decimal
      95.0

      >>> normalizar_valor_a_porcentaje(95.0, tiene_porcentaje=True)   # porcentaje
      95.0

      >>> normalizar_valor_a_porcentaje("85%")  # detecta % automáticamente
      85.0

      >>> normalizar_valor_a_porcentaje("0.85")  # sin %, es decimal
      85.0
    """
    import math

    # Manejo de NaN
    try:
        if pd.isna(valor):
            return np.nan
    except (ValueError, TypeError):
        return np.nan

    # Detectar % en string original si no se especifica tiene_porcentaje
    tiene_pct_detectado = False
    if isinstance(valor, str):
        valor_str = valor.strip()
        if valor_str.endswith("%"):
            tiene_pct_detectado = True
            valor_str = valor_str[:-1]
        try:
            valor = float(valor_str)
        except ValueError:
            return np.nan

    # Convertir a float
    try:
        valor = float(valor)
    except (ValueError, TypeError):
        return np.nan

    # Validar NaN
    if math.isnan(valor):
        return np.nan

    # Usar hint explícito si se proporciona, sino usar detección automática
    if tiene_porcentaje is None:
        tiene_porcentaje = tiene_pct_detectado

    # Aplicar lógica: si tiene %, mantener; si no, multiplicar por 100
    if tiene_porcentaje:
        return valor
    else:
        # Es decimal (0-1.3), convertir a porcentaje (0-130)
        return valor * 100.0


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN WRAPPER: NORMALIZACIÓN + CATEGORIZACIÓN EN UNA SOLA LLAMADA
# ═══════════════════════════════════════════════════════════════════════════════


def normalizar_y_categorizar(valor, es_porcentaje=None, id_indicador=None, sentido="Positivo"):
    """
    Wrapper que combina normalización de cumplimiento + categorización en una sola función.

    PROPÓSITO:
      - Centralizar la lógica de conversión automática
      - Reemplazar conversiones manuales repetidas en dashboards
      - Garantizar consistencia en formato de entrada/salida

    PARÁMETROS
    ----------
    valor : float, str, NaN
        Valor de cumplimiento (puede ser porcentaje o decimal)

    es_porcentaje : None, True, False
        Hint sobre el formato del valor:
        - None: detectar automáticamente (si tiene "%" en string)
        - True: es porcentaje (0-130)
        - False: es decimal (0-1.3)

    id_indicador : str, int, opcional
        ID del indicador para auto-detectar Plan Anual

    sentido : str
        "Positivo" o "Negativo" (para futuros usos en recalcular_cumplimiento_faltante)

    RETORNA
    -------
    str
        Categoría: "Peligro" | "Alerta" | "Cumplimiento" | "Sobrecumplimiento" | "Sin dato"

    EJEMPLOS
    --------
    >>> normalizar_y_categorizar(95, es_porcentaje=True, id_indicador="373")
    'Cumplimiento'

    >>> normalizar_y_categorizar(0.95, es_porcentaje=False, id_indicador="123")
    'Alerta'

    >>> normalizar_y_categorizar("95%", id_indicador="373")
    'Cumplimiento'

    >>> normalizar_y_categorizar(105, es_porcentaje=True)
    'Sobrecumplimiento'

    PROBLEMAS SOLUCIONADOS
    ----------------------
    Reemplaza el antipatrón repetido en 4+ dashboards:

    ANTES (código duplicado):
        cumpl_decimal = pct / 100.0  # Conversión manual
        categoria = categorizar_cumplimiento(cumpl_decimal, id_indicador=id_ind)

    DESPUÉS (centralizado):
        categoria = normalizar_y_categorizar(pct, es_porcentaje=True, id_indicador=id_ind)
    """
    # Paso 1: Normalizar a decimal (0-1.3)
    valor_decimal = normalizar_valor_a_porcentaje(valor, tiene_porcentaje=es_porcentaje)

    # Si el valor normalizado es un porcentaje (0-130), convertir a decimal
    # Lógica: normalizar_valor_a_porcentaje retorna porcentaje (0-130)
    # categorizar_cumplimiento espera decimal (0-1.3)
    if pd.notna(valor_decimal) and valor_decimal > 1.3:
        # Es un porcentaje que necesita conversión a decimal
        valor_decimal = valor_decimal / 100.0

    # Paso 2: Categorizar usando lógica oficial
    categoria = categorizar_cumplimiento(valor_decimal, id_indicador=id_indicador)

    return categoria


# ═══════════════════════════════════════════════════════════════════════════════
# DEPRECATED: Mantener para compatibilidad heredada (con warnings)
# ═══════════════════════════════════════════════════════════════════════════════


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
