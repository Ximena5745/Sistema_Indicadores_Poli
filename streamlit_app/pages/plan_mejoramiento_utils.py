"""
pages/plan_mejoramiento_utils.py — Helpers de presentación para la página
Plan de Mejoramiento (formateo, breadcrumb, alertas).

La lógica de datos/tendencia vive en services/plan_mejoramiento_loader.py;
este módulo solo formatea para UI y construye estructuras de navegación.
"""

from __future__ import annotations

import pandas as pd

from streamlit_app.components.plan_mejoramiento_charts import TREND_COLORS, TREND_LABELS

_UNIDAD_LABELS = {"ENT": "", "$": "$", "DEC": "", "%": "%"}


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


def trend_badge_html(tendencia: str) -> str:
    """Chip de color (no emoji) para el estado de tendencia."""
    color = TREND_COLORS.get(tendencia, TREND_COLORS["sin_datos"])
    label = TREND_LABELS.get(tendencia, "Sin datos")
    return (
        f'<span style="display:inline-flex;align-items:center;gap:4px;'
        f'background:{color}1A;color:{color};border:1px solid {color}55;'
        f'border-radius:12px;padding:2px 10px;font-size:0.78rem;font-weight:600;">'
        f'<span style="width:8px;height:8px;border-radius:50%;background:{color};"></span>'
        f"{label}</span>"
    )


def build_breadcrumb_items(
    factor: str | None,
    caracteristica: str | None,
    indicador: str | None,
    subindicador: str | None,
) -> list[tuple[str, str, str]]:
    """Cadena de navegación como lista de (level_key, label, value).

    `level_key` coincide con las claves de session_state usadas por la
    máquina de estados de la página (pm_drill_factor, etc.).
    """
    items: list[tuple[str, str, str]] = [("pm_drill_factor", "Resumen", None)]
    if factor:
        items.append(("pm_drill_factor", factor, factor))
    if caracteristica:
        items.append(("pm_drill_caracteristica", caracteristica, caracteristica))
    if indicador:
        items.append(("pm_drill_indicador", indicador, indicador))
    if subindicador:
        items.append(("pm_drill_subindicador", subindicador, subindicador))
    return items


def build_alerts(df_trend: pd.DataFrame, min_periodos_desfavorables: int = 2) -> list[dict]:
    """Detecta indicadores/subindicadores que requieren atención.

    Marca: (a) tendencia desfavorable en el último corte, o (b) sin datos en
    el periodo más reciente pese a tener historial ("dejó de reportar").
    Retorna una lista de dicts con `level`, `message` y datos para drill-down.
    """
    if df_trend is None or df_trend.empty:
        return []

    alerts = []
    desfavorables = df_trend[df_trend["Tendencia"] == "desfavorable"]
    for _, row in desfavorables.iterrows():
        nombre = row.get("Subindicador") or row.get("Indicador")
        alerts.append(
            {
                "level": "danger",
                "message": (
                    f"<b>{nombre}</b> ({row.get('Factor')}) muestra comportamiento "
                    f"desfavorable en {row.get('ultimo_periodo')}."
                ),
                "factor": row.get("Factor"),
                "caracteristica": row.get("Caracteristica"),
                "indicador": row.get("Indicador"),
                "subindicador": row.get("Subindicador") if "Subindicador" in df_trend.columns else None,
            }
        )

    sin_datos = df_trend[(df_trend["Tendencia"] == "sin_datos") & (df_trend["n_periodos"] > 0)]
    for _, row in sin_datos.iterrows():
        nombre = row.get("Subindicador") or row.get("Indicador")
        alerts.append(
            {
                "level": "warning",
                "message": f"<b>{nombre}</b> ({row.get('Factor')}) tiene un solo periodo reportado — tendencia aún no determinable.",
                "factor": row.get("Factor"),
                "caracteristica": row.get("Caracteristica"),
                "indicador": row.get("Indicador"),
                "subindicador": row.get("Subindicador") if "Subindicador" in df_trend.columns else None,
            }
        )

    return alerts
