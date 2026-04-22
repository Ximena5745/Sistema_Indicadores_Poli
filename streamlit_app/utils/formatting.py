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


def _to_non_negative_int(v, default: int = 0) -> int:
    n = to_num(v)
    if n is None:
        return default
    try:
        return max(0, int(float(n)))
    except (ValueError, TypeError):
        return default


def _pick_first(row, candidates, default=None):
    for key in candidates:
        if key in row:
            return row.get(key)
    return default


def _formatear_valor_por_signo(signo_raw, valor_raw, dec_eje_raw, dec_raw) -> str:
    signo = "" if is_null(signo_raw) else str(signo_raw).strip()
    valor = to_num(valor_raw)
    if valor is None:
        valor = 0.0

    dec_eje = _to_non_negative_int(dec_eje_raw, default=0)
    dec = _to_non_negative_int(dec_raw, default=0)

    # 1. Estados base
    if signo == "Sin reporte":
        return "Pendiente"

    if signo == "Linea Base":
        return "Linea Base"

    # 2. Enteros
    if signo == "ENT":
        if valor == 0:
            return "0"
        return f"{round(valor):,}"

    # 3. Porcentaje o unidades tipo kWh
    if signo in ["%", "kWh"]:
        if dec_eje > 0:
            value = round(valor, dec_eje)
            return f"{value:,.{dec_eje}f}{signo}"
        return f"{round(valor):,}{signo}"

    # 4. Moneda
    if signo == "$":
        if dec > 0:
            value = round(valor, dec_eje)
            return f"${value:,.{dec_eje}f}"
        return f"${round(valor):,}"

    # 5. Decimal puro
    if signo == "DEC":
        if dec > 0:
            value = round(valor, dec_eje)
            return f"{value:,.{dec_eje}f}"
        return f"{round(valor):,}"

    # 6. Unidades con sufijo separado
    if signo in ["m3", "Kg", "tCO2e"]:
        return f"{round(valor):,} {signo}"

    # 7. Default
    if dec > 0:
        value = round(valor, dec_eje)
        return f"{value:,.{dec_eje}f}"

    return f"{round(valor):,}"


def ejecucion_his_signo(row):
    ejec_s = _pick_first(
        row,
        ["Ejecución s", "Ejecucion s", "Ejecucion_s", "Ejecucion_Signo", "EjecS", "ejec_signo"],
        default="",
    )
    ejec = _pick_first(row, ["Ejecución", "Ejecucion"], default=0)
    dec_eje = _pick_first(row, ["DecimalesEje", "Decimales_Ejecucion", "DecEjec"], default=0)
    dec = _pick_first(row, ["Decimales", "Decimales_Meta", "DecMeta"], default=0)
    return _formatear_valor_por_signo(ejec_s, ejec, dec_eje, dec)


def meta_his_signo(row):
    meta_s = _pick_first(row, ["Meta s", "Meta_Signo", "MetaS", "meta_signo"], default="")
    meta = _pick_first(row, ["Meta"], default=0)
    dec_meta = _pick_first(row, ["Decimales", "Decimales_Meta", "DecMeta"], default=0)
    dec_eje = _pick_first(row, ["DecimalesEje", "Decimales_Ejecucion", "DecEjec"], default=0)
    return _formatear_valor_por_signo(meta_s, meta, dec_eje, dec_meta)


def formatear_meta_ejecucion_df(
    df: pd.DataFrame, meta_col: str = "Meta", ejec_col: str = "Ejecucion"
) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    out = df.copy()
    if meta_col in out.columns:
        out[meta_col] = out.apply(
            lambda r: meta_his_signo({**r.to_dict(), "Meta": r.get(meta_col)}),
            axis=1,
        )
    if ejec_col in out.columns:
        out[ejec_col] = out.apply(
            lambda r: ejecucion_his_signo(
                {**r.to_dict(), "Ejecucion": r.get(ejec_col), "Ejecución": r.get(ejec_col)}
            ),
            axis=1,
        )
    return out
