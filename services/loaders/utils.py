"""
services/loaders/utils.py — UTILIDADES DE CARGA

Funciones helper para normalización de columnas, IDs y procesamiento.

IMPORTAR:
  from services.loaders.utils import (
      ascii_lower,
      renombrar_columnas,
      id_a_str,
  )
"""

import unicodedata
import pandas as pd


_RENAME = {
    "Año": "Anio",
    "Ejecución": "Ejecucion",
    "Clasificación": "Clasificacion",
    "Ejecución s": "Ejecucion_s",
    "Meta s": "Meta_Signo",
}


def ascii_lower(s: str) -> str:
    """Normaliza string a ascii lowercase para comparaciones."""
    return unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode().lower()


def renombrar_columnas(df: pd.DataFrame, mapa: dict = None) -> pd.DataFrame:
    """
    Renombra columnas del DataFrame usando mapeo case-insensitive.

    Parámetros
    ----------
    df : pd.DataFrame
        DataFrame con columnas a renombrar
    mapa : dict
        Mapeo {nombre_original: nombre_nuevo}
        Si None, usa mapeo estándar (_RENAME)

    Retorna
    -------
    pd.DataFrame
        DataFrame con columnas renombradas
    """
    if mapa is None:
        mapa = _RENAME

    df.columns = [str(c).strip() for c in df.columns]
    mapping = {}
    for col in df.columns:
        for orig, dest in mapa.items():
            if ascii_lower(col) == ascii_lower(orig):
                mapping[col] = dest
                break
    return df.rename(columns=mapping)


def id_a_str(x) -> str:
    """
    Normaliza valor de ID a string.

    - NaN → ""
    - 100.0 → "100"
    - "ABC" → "ABC"
    - Preserva formato (entero si es entero, float si es float)
    """
    if pd.isna(x):
        return ""
    try:
        f = float(x)
        return str(int(f)) if f == int(f) else str(f)
    except (ValueError, TypeError):
        return str(x)


def obtener_rename_map() -> dict:
    """Retorna el mapeo estándar de nombres de columnas."""
    return _RENAME.copy()
