"""
services/cmi_filters/utils.py
============================

Utility functions for normalization and ID cleaning.

Responsibility: Normalize flag values and ID formats.
"""

import pandas as pd


def _normalize_flag_series(series: pd.Series) -> pd.Series:
    """
    Normaliza una serie de valores booleanos/flags a 0 o 1.
    
    Acepta: números, strings ("si"/"no", "true"/"false", "x"), etc.
    """
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.isna().any():
        raw = series.astype(str).str.strip().str.lower()
        mapped = raw.map(
            {
                "1": 1,
                "1.0": 1,
                "si": 1,
                "true": 1,
                "x": 1,
                "0": 0,
                "0.0": 0,
                "no": 0,
                "false": 0,
                "": 0,
            }
        )
        numeric = numeric.fillna(mapped)
    return numeric


def _normalize_id_value(val) -> str:
    """
    Normaliza un valor de ID a string.
    
    Maneja: NaN, int, float, string
    Convierte floats a ints si es posible (ej. 100.0 → "100")
    """
    if pd.isna(val):
        return ""
    if isinstance(val, int):
        return str(val)
    if isinstance(val, float):
        return str(int(val)) if val.is_integer() else str(val).strip()
    text = str(val).strip()
    try:
        num = float(text)
        if num.is_integer():
            return str(int(num))
    except Exception:
        return text
    return text
