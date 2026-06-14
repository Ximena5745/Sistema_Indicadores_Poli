"""Utilidades de carga Excel — portado desde services/loaders/utils.py."""

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
    return unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode().lower()


def renombrar_columnas(df: pd.DataFrame, mapa: dict | None = None) -> pd.DataFrame:
    if mapa is None:
        mapa = _RENAME

    df.columns = [str(c).strip() for c in df.columns]
    mapping: dict[str, str] = {}
    for col in df.columns:
        for orig, dest in mapa.items():
            if ascii_lower(col) == ascii_lower(orig):
                mapping[col] = dest
                break
    return df.rename(columns=mapping)


def id_a_str(x) -> str:
    if pd.isna(x):
        return ""
    try:
        f = float(x)
        return str(int(f)) if f == int(f) else str(f)
    except (ValueError, TypeError):
        return str(x)


def obtener_rename_map() -> dict:
    return _RENAME.copy()


def find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols_norm = {ascii_lower(c): c for c in df.columns}
    for name in candidates:
        hit = cols_norm.get(ascii_lower(name))
        if hit:
            return hit
    return None
