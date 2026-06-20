"""
services/ficha_pdf/utils.py
==========================

Utilities for PDF generation (colors, helpers, constants).

Responsibility: Define color palette and formatting utilities.
"""

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

# ── Paleta institucional ──────────────────────────────────────────────────────
PRIMARIO = colors.HexColor("#1A3A5C")
GRIS = colors.HexColor("#64748B")
FONDO = colors.HexColor("#F8FAFC")
BORDE = colors.HexColor("#E2E8F0")
BLANCO = colors.white

NIVEL_COLORS = {
    "Peligro": colors.HexColor("#D32F2F"),
    "Alerta": colors.HexColor("#FBAF17"),
    "Cumplimiento": colors.HexColor("#43A047"),
    "Sobrecumplimiento": colors.HexColor("#6699FF"),
}

MARGIN = 1.8 * cm
PAGE_W, PAGE_H = A4


def nivel_color(nivel: str):
    """Get color for compliance level."""
    return NIVEL_COLORS.get(nivel, GRIS)


def safe(v) -> str:
    """Safely convert value to string, handling NaN and None."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    s = str(v).strip()
    return s if s and s not in ("nan", "None") else "—"


def fmt_valor_signo(valor, signo, decimales=0) -> str:
    """Formatea un valor numérico según signo y decimales (réplica de _formatear_valor_por_signo)."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return "—"
    try:
        num = float(valor)
    except (TypeError, ValueError):
        return safe(valor)
    import math
    if math.isnan(num):
        return "—"

    s = str(signo).strip() if signo is not None and not (isinstance(signo, float) and pd.isna(signo)) else "%"
    try:
        dec = max(0, int(float(decimales))) if decimales is not None else 0
    except (TypeError, ValueError):
        dec = 0

    if s == "Sin reporte":
        return "Pendiente"
    if s == "Linea Base":
        return "Linea Base"
    if s == "ENT":
        return "0" if num == 0 else f"{round(num):,}"
    if s in ("%", "kWh"):
        if dec > 0:
            return f"{num:,.{dec}f}{s}"
        return f"{round(num):,}{s}"
    if s == "$":
        if dec > 0:
            formatted = f"{num:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            formatted = f"{round(num):,}".replace(",", ".")
        return f"${formatted}"
    if s == "DEC":
        if dec > 0:
            return f"{num:,.{dec}f}"
        return f"{round(num):,}"
    su = s.upper()
    if su in ("NO APLICA", "SIN REPORTE", "NA"):
        if dec > 0:
            return f"{num:,.{dec}f}"
        return f"{round(num):,}"
    if s in ("m3", "Kg", "tCO2e"):
        return f"{round(num):,} {s}"
    if dec > 0:
        return f"{num:,.{dec}f} {s}".strip()
    return f"{round(num):,}{(' ' + s) if s else ''}".strip()


def fmt_meta_from_dict(data: dict) -> str:
    """Formatea Meta a partir de un dict/row de indicador."""
    signo = data.get("Meta_Signo") or data.get("Meta s") or data.get("meta_signo") or "%"
    dec = data.get("Decimales_Meta") or data.get("dec_meta") or 0
    return fmt_valor_signo(data.get("Meta"), signo, dec)


def fmt_ejec_from_dict(data: dict) -> str:
    """Formatea Ejecucion a partir de un dict/row de indicador."""
    signo = (data.get("Ejecucion_s") or data.get("EjecS") or
             data.get("Ejecucion_Signo") or data.get("ejec_signo") or "%")
    dec = data.get("Decimales_Ejecucion") or data.get("dec_ejec") or 0
    return fmt_valor_signo(data.get("Ejecucion"), signo, dec)
