"""
utils/niveles.py — Niveles de cumplimiento centralizados.

Umbrales FIJOS (aplican en todas las vistas):
  > 105%   → Sobrecumplimiento  (azul oscuro #1A3A5C)
  100–105% → Cumplimiento       (azul claro  #1FB2DE)
   80–99%  → Alerta             (amarillo    #FBAF17)
    < 80%  → Peligro            (rosa        #EC0677)
"""

# ── Umbrales en escala porcentual (0-100+) ─────────────────────────────────────
UMBRAL_PELIGRO_PCT           = 80.0
UMBRAL_ALERTA_PCT            = 100.0
UMBRAL_SOBRECUMPLIMIENTO_PCT = 105.0

# ── Umbrales en escala decimal (0-1+) ──────────────────────────────────────────
UMBRAL_PELIGRO_DEC           = 0.80
UMBRAL_ALERTA_DEC            = 1.00
UMBRAL_SOBRECUMPLIMIENTO_DEC = 1.05

# ── Colores de referencia (sólido) ─────────────────────────────────────────────
NIVEL_COLOR = {
    "Peligro":           "#D32F2F",
    "Alerta":            "#FBAF17",
    "Cumplimiento":      "#43A047",
    "Sobrecumplimiento": "#1A3A5C",
    "Sin dato":          "#BDBDBD",
}

# ── Colores de fondo (celdas de tabla) ─────────────────────────────────────────
NIVEL_BG = {
    "Peligro":           "#FFCDD2",
    "Alerta":            "#FEF3D0",
    "Cumplimiento":      "#E8F5E9",
    "Sobrecumplimiento": "#D0E4FF",
    "Sin dato":          "#F5F5F5",
}

# ── Orden canónico (de peor a mejor) ───────────────────────────────────────────
NIVEL_ORDEN = ["Peligro", "Alerta", "Cumplimiento", "Sobrecumplimiento", "Sin dato"]

# ── Íconos ─────────────────────────────────────────────────────────────────────
NIVEL_ICON = {
    "Peligro":           "🔴",
    "Alerta":            "🟡",
    "Cumplimiento":      "🔵",
    "Sobrecumplimiento": "🔵",
    "Sin dato":          "⚪",
}


def nivel_desde_pct(pct) -> str:
    """Clasifica un valor de cumplimiento en escala porcentual (0-100+)."""
    try:
        c = float(pct)
    except (TypeError, ValueError):
        return "Sin dato"
    if c < UMBRAL_PELIGRO_PCT:
        return "Peligro"
    if c < UMBRAL_ALERTA_PCT:
        return "Alerta"
    if c <= UMBRAL_SOBRECUMPLIMIENTO_PCT:
        return "Cumplimiento"
    return "Sobrecumplimiento"


def nivel_desde_decimal(dec) -> str:
    """Clasifica un valor de cumplimiento en escala decimal (0-1+)."""
    try:
        c = float(dec)
    except (TypeError, ValueError):
        return "Sin dato"
    return nivel_desde_pct(c * 100)
