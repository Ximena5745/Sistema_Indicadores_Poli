"""
core/domain/health_metrics.py — CÁLCULOS DE MÉTRICAS DE SALUD

PROPÓSITO:
  Lógica de recálculo de cumplimiento cuando faltan datos.
  Centraliza la duplicación que existía en 3 módulos diferentes.

PROBLEMA SOLUCIONADO (#2):
  Antes: 3 implementaciones divergentes
  - services/data_loader.py líneas 248-276 (defectuosa)
  - services/strategic_indicators.py load_cierres() (defectuosa)
  - scripts/etl/cumplimiento.py (CORRECTA)
  
  Ahora: 1 lógica oficial global

IMPORTAR:
  from core.domain.health_metrics import recalcular_cumplimiento_faltante
"""

import pandas as pd
import logging

# Importar configuración
from core.config import (
    IDS_PLAN_ANUAL,
    IDS_TOPE_100,
)

logger = logging.getLogger(__name__)


def recalcular_cumplimiento_faltante(meta, ejecucion, sentido="Positivo", id_indicador=None):
    """
    Recalcula cumplimiento cuando falta: ejecución / meta (o meta / ejecución según sentido).

    PROPÓSITO:
        Centralizar la lógica de recálculo que estaba duplicada en 3 lugares.

    CASOS ESPECIALES (PROBLEMA #2):
        - Meta=0 & Ejec=0 → 1.0 (éxito perfecto, cero es logro)
        - Negativo & Ejec=0 → 1.0 (cero es perfecto en indicadores de "menos es mejor")

    LÓGICA:
        1. Validar meta y ejecucion no sean None
        2. Convertir a float
        3. CASOS ESPECIALES:
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
    # CASOS ESPECIALES (PROBLEMA #2)
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
    es_tope_100 = False
    if id_indicador is not None:
        id_str = str(id_indicador).strip()
        es_plan_anual = id_str in IDS_PLAN_ANUAL
        es_tope_100 = id_str in IDS_TOPE_100

    tope = 1.0 if (es_plan_anual or es_tope_100) else 1.3

    # Retornar acotado [0, tope]
    resultado = min(max(raw, 0.0), tope)
    logger.debug(
        f"Recalc cumpl: meta={m}, ejec={e}, sentido={sentido_str}, "
        f"PA={es_plan_anual}, raw={raw:.3f}, resultado={resultado:.3f}"
    )

    return resultado


def cumplimiento_por_bandas_kawak(resultado, sentido, alerta, cumplimiento, exceso, peligro=None):
    """
    Cumplimiento proporcional a partir de los rangos de semáforo parametrizados
    en Kawak (peligro/alerta/cumplimiento/exceso), en vez del ratio Meta/Ejecución.

    USO: exclusivamente para indicadores con Meta=0, donde la fórmula estándar
    (recalcular_cumplimiento_faltante) da un "acantilado" binario 0%/100% —
    Negativo & Ejecución>0 siempre da 0% sin importar cuán cerca esté de cero
    (ej. Ejecución=0.01 con Meta=0 → 0%, igual que Ejecución=1000).

    Kawak define 4 puntos de corte por indicador y período (los límites pueden
    cambiar entre períodos). Regla de negocio (dada por el usuario):
      - en/mejor que exceso            → Sobrecumplimiento
      - entre cumplimiento y exceso     → Cumplimiento
      - entre alerta y cumplimiento     → Alerta
      - en/peor que alerta (hasta peligro y más allá) → Peligro

    IMPORTANTE sobre el 100%: el 100% representa el punto "exceso" (el mejor
    posible), no toda la zona "Cumplimiento". Un resultado que cae dentro de
    la zona Cumplimiento pero no es exactamente el punto perfecto (ej.
    Ejecución=0.22 con exceso=0) queda PROPORCIONALMENTE por debajo de 100%,
    nunca por encima — solo un resultado igual o mejor que "exceso" alcanza o
    supera el 100%. Por esto esta función devuelve la categoría directamente
    en vez de delegar en categorizar_cumplimiento: esa función universal
    define "Cumplimiento" como 100-105%, lo que empujaría estos valores (que
    aquí quedan bajo el 90-100%) a la categoría "Alerta" incorrectamente.

    Parámetros
    ----------
    resultado : float — valor ejecutado real (mismo campo que "Ejecucion")
    sentido : str — "Positivo" (más es mejor) o "Negativo" (menos es mejor)
    alerta, cumplimiento, exceso : float — cortes parametrizados en Kawak
    peligro : float, opcional — cota adicional usada solo para escalar la
        zona de Peligro; si no está disponible se usa una caída proporcional
        simple hacia 0.

    Retorna
    -------
    tuple[float, str] — (cumplimiento normalizado en escala 0–1.3 donde
    1.0=100%, categoría). (NaN, "Sin dato") si faltan datos o los rangos son
    inválidos (ej. alerta/cumplimiento/exceso no numéricos).
    """
    try:
        r = float(resultado)
        a = float(alerta)
        c = float(cumplimiento)
        e = float(exceso)
    except (TypeError, ValueError):
        return float("nan"), "Sin dato"

    if pd.isna(r) or pd.isna(a) or pd.isna(c) or pd.isna(e):
        return float("nan"), "Sin dato"

    p = None
    if peligro is not None:
        try:
            p_val = float(peligro)
            if not pd.isna(p_val):
                p = p_val
        except (TypeError, ValueError):
            p = None

    es_negativo = str(sentido).strip().lower() == "negativo"

    # Normalizar a orientación "más alto = mejor" para tratar Positivo/Negativo
    # con la misma lógica (invierte signo cuando es Negativo).
    if es_negativo:
        r, a, c, e = -r, -a, -c, -e
        p = -p if p is not None else None
    # Tras normalizar, el orden esperado es a <= c <= e (peor a mejor).

    # Anclas elegidas para que 1.00 (100%) sea el punto "exceso" — no la zona
    # "Cumplimiento" completa — y así un resultado peor que exceso (aunque
    # esté dentro de la zona Cumplimiento) quede siempre bajo el 100%.
    TOPE_PELIGRO_ = 0.70
    TOPE_ALERTA_ = 0.90
    TOPE_CUMPLIMIENTO_ = 1.00
    TOPE_MAX = 1.30

    def _interp(x, x0, x1, y0, y1):
        if x1 == x0:
            return y1
        frac = (x - x0) / (x1 - x0)
        return y0 + max(0.0, min(1.0, frac)) * (y1 - y0)

    if r < a:
        # Peor que alerta → zona Peligro. Escala hacia 0 usando 'peligro' si
        # está disponible; si no, cae proporcionalmente sin cota inferior dura.
        if p is not None and p != a:
            valor = max(0.0, _interp(r, p, a, 0.0, TOPE_PELIGRO_))
        elif a == 0:
            valor = 0.0
        else:
            valor = max(0.0, min(TOPE_PELIGRO_, TOPE_PELIGRO_ * (r / a)))
        return valor, "Peligro"
    if r < c:
        return _interp(r, a, c, TOPE_PELIGRO_, TOPE_ALERTA_), "Alerta"
    if r < e:
        return _interp(r, c, e, TOPE_ALERTA_, TOPE_CUMPLIMIENTO_), "Cumplimiento"

    # Mejor o igual que exceso → Sobrecumplimiento, escalado sin cota dura
    # (usa el ancho cumplimiento→exceso como referencia de escala).
    ancho = (e - c) if (e - c) != 0 else (abs(e) if e != 0 else 1.0)
    frac_extra = (r - e) / abs(ancho) if ancho != 0 else 0.0
    valor = min(TOPE_MAX, TOPE_CUMPLIMIENTO_ + max(0.0, frac_extra) * (TOPE_MAX - TOPE_CUMPLIMIENTO_))
    return valor, "Sobrecumplimiento"
