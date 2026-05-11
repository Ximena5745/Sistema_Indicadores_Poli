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
