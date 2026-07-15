"""
services/strategic_indicators/utils.py — Utilidades compartidas

Responsabilidad única:
  - Gestión de caché manual (fallback cuando st.cache_data no está disponible)
  - Normalización de text y búsqueda de columnas
  - Conversión de IDs
"""

import unicodedata
import time
import pandas as pd


# Caché manual simple (fallback para contextos sin Streamlit)
_CACHE_MANUAL = {}
_CACHE_TTL_MANUAL = 300  # segundos


def _get_cached(key: str) -> pd.DataFrame | None:
    """Obtener del caché manual si está disponible y no expirado."""
    if key in _CACHE_MANUAL:
        data, timestamp = _CACHE_MANUAL[key]
        if time.time() - timestamp < _CACHE_TTL_MANUAL:
            return data
        else:
            del _CACHE_MANUAL[key]
    return None


def _set_cached(key: str, data: pd.DataFrame) -> None:
    """Guardar en caché manual con timestamp."""
    _CACHE_MANUAL[key] = (data, time.time())


def _validate_cached_result(df: pd.DataFrame, context: str) -> bool:
    """
    Valida que caché no retorne DataFrame vacío corrupto.
    
    Retorna: True si el DataFrame es válido, False si está vacío.
    """
    if df.empty:
        # Log para debugging
        import sys
        print(f"WARNING: Caché vacío en {context}, invalidando...", file=sys.stderr)
        return False
    return True


def _norm_text(value: str) -> str:
    """
    Normaliza texto a ASCII lowercase sin acentos.
    
    Ejemplo: "Ejecución" → "ejecucion"
    """
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


def _find_col(df: pd.DataFrame, names: list[str]) -> str | None:
    """
    Busca columna en DataFrame con variantes de nombre (acentos, mayúsculas, etc).
    
    Parámetros:
      df: DataFrame donde buscar
      names: Lista de nombres posibles para la columna
      
    Retorna: Nombre de columna encontrado, o None si no existe
    """
    lookup = {_norm_text(c): c for c in df.columns}
    for name in names:
        hit = lookup.get(_norm_text(name))
        if hit:
            return hit
    return None


def _id_limpio(x) -> str:
    """
    Convierte valores de ID a string normalizado.
    
    Ejemplos:
      100.0 → "100"
      100.5 → "100.5"
      "100" → "100"
      NaN → ""
    """
    if pd.isna(x):
        return ""
    try:
        f = float(x)
        return str(int(f)) if f == int(f) else str(f)
    except (ValueError, TypeError):
        return str(x).strip()


# Constantes de catálogos
SOBRECUMPLIMIENTO = "Sobrecumplimiento"
NO_APLICA = "No aplica"
PENDIENTE = "Pendiente de reporte"
METRICA = "Metrica"


# El archivo fuente "Catalogo de Indicadores.xlsx" tiene celdas de "Linea" con
# el caracter de reemplazo Unicode (�) en lugar de tildes, producto de una
# corrupción de encoding ocurrida antes de que los datos entraran al repo (la
# información original de la tilde ya no existe en el archivo). Sin este
# arreglo, "Expansi�n" y "Educaci�n_para_toda_la_vida" no calzan contra las
# claves normalizadas ("expansion", "educacion...") usadas para agrupar/mostrar
# cumplimiento por línea estratégica, y esas líneas se muestran en 0.0% pese a
# tener indicadores con resultados.
_LINEA_REPAIR_MAP = {
    "Expansi�n": "Expansión",
    "Transformaci�n_Organizacional": "Transformación_Organizacional",
    "Educaci�n_para_toda_la_vida": "Educación_para_toda_la_vida",
}


def _repair_linea_encoding(series: pd.Series) -> pd.Series:
    """Corrige valores de 'Linea' con el caracter de reemplazo Unicode conocido."""
    return series.replace(_LINEA_REPAIR_MAP)
