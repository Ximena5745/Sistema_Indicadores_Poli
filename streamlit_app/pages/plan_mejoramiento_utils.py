"""
pages/plan_mejoramiento_utils.py — Helpers de presentación para la vista plana
"Plan de Mejoramiento" (pestañas Indicadores / Métricas).

La lógica de datos vive en services/plan_mejoramiento_loader.py; este módulo
solo formatea texto/HTML para UI (badges, tags, tarjetas KPI).
"""

from __future__ import annotations

import pandas as pd

from streamlit_app.components.plan_mejoramiento_charts import TENDENCIA_COLORS, TENDENCIA_LABELS

PM_COLORS = {
    "navy": "#263A58",
    "blue": "#22B2DE",
    "cyan": "#15BECE",
    "gold": "#F7B400",
    "magenta": "#E4006D",
    "lime": "#B1C900",
    "bg": "#F4F6F9",
    "surface": "#FFFFFF",
    "surface_2": "#EEF1F6",
    "text": "#1D2733",
    "text_soft": "#5B6779",
    "border": "#DCE2EA",
    "up": "#4B7A00",
    "down": "#C81E5B",
    "radius": "14px",
    "shadow": "0 1px 3px rgba(38,58,88,0.08), 0 4px 14px rgba(38,58,88,0.06)",
}

_ESTADO_COLORS = {"Activo": PM_COLORS["up"], "Aprobado": PM_COLORS["gold"], "Pendiente": "#9E9E9E"}

_TIPO_STYLES = {
    "Indicador": ("rgba(34,178,222,.15)", "#0e6d8c"),
    "Metrica": ("rgba(177,201,0,.18)", "#6b7a00"),
}
_TIPO_DEFAULT_STYLE = ("rgba(228,0,109,.13)", PM_COLORS["magenta"])
_TIPO_LABELS = {"Indicador": "Indicador", "Metrica": "Métrica"}


def fmt_num_or_dash(value, decimals: int = 2, suffix: str = "") -> str:
    """Formatea un número a texto con `decimals` decimales, o "—" si es nulo.

    `st.dataframe` (esta versión de Streamlit) muestra el texto literal
    "None" para NaN en columnas numéricas — incluso con `NumberColumn` y
    formato explícito. Para lograr el guion "—" del mockup, estas columnas
    se formatean como texto antes de pasarlas a la tabla.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    try:
        return f"{float(value):.{decimals}f}{suffix}"
    except (TypeError, ValueError):
        return str(value)


def truncate_text(text, n: int) -> str:
    text = str(text or "")
    return text if len(text) <= n else text[: n - 1] + "…"


def format_ejecucion(value, unidad: str | None, decimales: int | None = None) -> str:
    """Formatea un valor de Ejecución según su unidad (ENT/$/DEC/%)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "Sin dato"

    unidad = (unidad or "ENT").strip().upper()
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)

    if unidad == "ENT":
        return f"{num:,.0f}"
    if unidad == "$":
        return f"$ {num:,.0f}"
    if unidad == "%":
        return f"{num:,.1f}%"
    if unidad == "DEC":
        dec = int(decimales) if decimales is not None and not pd.isna(decimales) else 2
        return f"{num:,.{dec}f}"
    return f"{num:,.2f}"


def format_delta(delta_abs: float | None, unidad: str | None) -> str | None:
    if delta_abs is None or pd.isna(delta_abs):
        return None
    sign = "+" if delta_abs >= 0 else ""
    return f"{sign}{format_ejecucion(delta_abs, unidad)}"


def _valor_o(value, texto_defecto: str = "N/A") -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return texto_defecto
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def tipo_tag_html(tipo: str | None) -> str:
    """Tag coloreado Indicador/Métrica/Sin clasificar — mismos colores que el mockup."""
    bg, color = _TIPO_STYLES.get(str(tipo or "").strip(), _TIPO_DEFAULT_STYLE)
    label = _TIPO_LABELS.get(str(tipo or "").strip(), "Sin clasificar")
    return (
        f'<span style="font-size:9.5px;font-weight:700;padding:2px 7px;border-radius:6px;'
        f'text-transform:uppercase;letter-spacing:.03em;display:inline-block;'
        f'background:{bg};color:{color};">{label}</span>'
    )


def estado_badge_html(estado: str) -> str:
    color = _ESTADO_COLORS.get(estado, "#9E9E9E")
    return (
        f'<span style="display:inline-flex;align-items:center;gap:4px;'
        f'background:{color}1A;color:{color};border:1px solid {color}55;'
        f'border-radius:12px;padding:2px 10px;font-size:0.78rem;font-weight:600;">'
        f'<span style="width:8px;height:8px;border-radius:50%;background:{color};"></span>'
        f"{estado}</span>"
    )


def tendencia_badge_html(tendencia: str) -> str:
    """Badge de tendencia — solo Creciente/Decreciente/Estable tienen etiqueta
    propia; "Sin suficiente historia" se muestra como un simple "—" gris,
    igual que el mockup (su `trendBadge()` solo reconoce esos 3 valores)."""
    if tendencia not in TENDENCIA_LABELS:
        return f'<span style="color:{PM_COLORS["text_soft"]};font-weight:700;">—</span>'
    color = TENDENCIA_COLORS[tendencia]
    return f'<span style="color:{color};font-weight:700;">{TENDENCIA_LABELS[tendencia]}</span>'


def fmt_variacion_or_dash(pct: float | None) -> str:
    """Texto plano '+N.N%'/'N.N%'/'—' para columnas de `st.dataframe` (sin
    color — la grilla no soporta HTML por celda, ver `variacion_html` para
    el equivalente coloreado usado en los modales)."""
    if pct is None or pd.isna(pct):
        return "—"
    sign = "+" if pct > 0 else ""
    return f"{sign}{pct:.1f}%"


def variacion_html(pct: float | None) -> str:
    """+N%/N% coloreado verde si > 0, rojo si < 0, sin color si = 0, "—" si null."""
    if pct is None or pd.isna(pct):
        return "—"
    if pct > 0:
        return f'<span style="color:{PM_COLORS["up"]};font-weight:700;">+{pct:.1f}%</span>'
    if pct < 0:
        return f'<span style="color:{PM_COLORS["down"]};font-weight:700;">{pct:.1f}%</span>'
    return f"{pct:.1f}%"


def kpi_card_html(label: str, value, sub: str, accent: str) -> str:
    """Tarjeta KPI con borde superior de color (accent) — replica `.kpi.accent-*`
    del mockup. `accent` es un color hex."""
    return (
        f'<div style="background:{PM_COLORS["surface"]};border:1px solid {PM_COLORS["border"]};'
        f'border-radius:{PM_COLORS["radius"]};padding:16px 18px;box-shadow:{PM_COLORS["shadow"]};'
        f'border-top:3px solid {accent};height:100%;">'
        f'<div style="font-size:11px;color:{PM_COLORS["text_soft"]};font-weight:600;'
        f'text-transform:uppercase;letter-spacing:.05em;">{label}</div>'
        f'<div style="font-size:25px;font-weight:800;color:{PM_COLORS["navy"]};margin-top:4px;">{value}</div>'
        f'<div style="font-size:11px;color:{PM_COLORS["text_soft"]};margin-top:2px;">{sub}</div>'
        f"</div>"
    )


def factor_badge_html(factor_num: int | None) -> str:
    """Badge corto "F{n}" — replica `.fnum-badge` del mockup."""
    n = int(factor_num) if factor_num is not None and pd.notna(factor_num) else "—"
    return (
        f'<span style="display:inline-block;font-size:10px;font-weight:800;color:#fff;'
        f'background:{PM_COLORS["navy"]};padding:1px 7px;border-radius:5px;">F{n}</span>'
    )


def build_indicador_cump_texto(row) -> str:
    """Línea combinada 'Meta / Ejecución / % Cumplimiento — 2025 y 2026' — texto
    exacto del modal de indicador (mockup: `miCump`)."""
    return (
        f"2025 — Meta: {_valor_o(row.get('Meta_num_2025'))} · "
        f"Ejecución: {_valor_o(row.get('Ejecucion_num_2025'))} · "
        f"% Cump: {_valor_o(row.get('Cump_calc_2025') * 100 if pd.notna(row.get('Cump_calc_2025')) else None, 'N/A')}"
        f"{'%' if pd.notna(row.get('Cump_calc_2025')) else ''}"
        "   |   "
        f"2026 — Meta: {_valor_o(row.get('Meta_num_2026'))} · "
        f"Ejecución: {_valor_o(row.get('Ejecucion_num_2026'))} · "
        f"% Cump: {_valor_o(row.get('Cump_calc_2026') * 100 if pd.notna(row.get('Cump_calc_2026')) else None, 'N/A')}"
        f"{'%' if pd.notna(row.get('Cump_calc_2026')) else ''}"
    )


def build_indicador_metas_futuras_texto(row) -> str:
    """Línea 'Metas 2026 – 2030' — texto exacto del modal de indicador
    (mockup: `miMetas`)."""
    partes = [f"{y}: {_valor_o(row.get(f'Meta_num_{y}'))}" for y in ("2026", "2027", "2028", "2029", "2030")]
    return " · ".join(partes)
