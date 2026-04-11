"""Funciones utilitarias de formateo/limpieza para páginas Streamlit."""

import html as _html
import math

import pandas as pd


def is_null(v) -> bool:
    if v is None:
        return True
    try:
        if pd.isna(v):
            return True
    except (TypeError, ValueError):
        pass
    try:
        f = float(str(v).strip())
        return math.isnan(f)
    except (ValueError, TypeError):
        pass
    return str(v).strip().lower() in ("", "nan", "none")


def to_num(v):
    if is_null(v):
        return None
    try:
        f = float(str(v).strip())
        return None if math.isnan(f) else f
    except (ValueError, TypeError):
        return None


def limpiar(v) -> str:
    if is_null(v):
        return ""
    return _html.unescape(str(v)).strip()


def id_limpio(x) -> str:
    if is_null(x):
        return ""
    try:
        f = float(x)
        return str(int(f)) if f == int(f) else str(f)
    except (ValueError, TypeError):
        return str(x).strip()


def fmt_num(v) -> str:
    n = to_num(v)
    if n is None:
        s = str(v).strip()
        return s if s and s.lower() not in ("nan", "none", "") else "—"
    return f"{n:,.2f}".rstrip("0").rstrip(".")


def fmt_valor(v, signo, decimales) -> str:
    n = to_num(v)
    if n is None:
        return "—"
    try:
        d = max(0, int(float(decimales))) if not is_null(decimales) else 2
    except (ValueError, TypeError):
        d = 2
    s = str(signo).strip() if not is_null(signo) else "%"
    su = s.upper()
    if s == "%":
        return f"{n:,.{d}f}%"
    if s == "$":
        formatted = f"{n:,.{d}f}"
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"${formatted}"
    if su in ("ENT", "N", "", "METRICA", "MÉTRICA"):
        return f"{int(round(n)):,}" if d == 0 else f"{n:,.{d}f}"
    if su == "DEC":
        return f"{n:,.{d}f}"
    if su in ("NO APLICA", "SIN REPORTE", "NA"):
        return f"{n:,.{d}f}" if d > 0 else f"{int(round(n)):,}"
    return f"{n:,.{d}f} {s}"
