"""
components/plan_mejoramiento_charts.py — Gráficos (Plotly) de la vista plana
"Plan de Mejoramiento" (pestañas Indicadores / Métricas).

Paleta y specs replican el mockup de referencia `plan_mejoramiento_cna.html`
(ver docs/plan `rol-actuar-como-scalable-hollerith.md`, secciones 4 y 8):
navy #263A58, blue #22B2DE, cyan #15BECE, gold #F7B400, magenta #E4006D,
lime #B1C900.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

PM_CHART_COLORS = {
    "navy": "#263A58",
    "blue": "#22B2DE",
    "cyan": "#15BECE",
    "gold": "#F7B400",
    "magenta": "#E4006D",
    "lime": "#B1C900",
    "up": "#4B7A00",
    "down": "#C81E5B",
    "grid": "rgba(38,58,88,.08)",
    "text_soft": "#5B6779",
    "hline": "#9AA7B8",
}

# Tendencia de Métricas (serie anual completa — ver build_metricas_historico)
TENDENCIA_COLORS = {
    "Creciente": PM_CHART_COLORS["up"],
    "Decreciente": PM_CHART_COLORS["down"],
    "Estable": PM_CHART_COLORS["text_soft"],
    "Sin suficiente historia": "#BDBDBD",
}
TENDENCIA_LABELS = {
    "Creciente": "▲ Creciente",
    "Decreciente": "▼ Decreciente",
    "Estable": "● Estable",
    # "Sin suficiente historia" no tiene etiqueta propia — se muestra como "—",
    # igual que el mockup (su trendBadge() solo reconoce 3 valores).
}

_TRANSPARENT_LAYOUT = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")


def _truncate(text: str, n: int) -> str:
    text = str(text or "")
    return text if len(text) <= n else text[: n - 1] + "…"


def _empty_fig(mensaje: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(title=mensaje, height=270, **_TRANSPARENT_LAYOUT)
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Pestaña Indicadores
# ─────────────────────────────────────────────────────────────────────────────

_METAS_FUTURAS = ["2026", "2027", "2028", "2029", "2030"]
_METAS_FUTURAS_COLORS = [
    PM_CHART_COLORS["navy"],
    PM_CHART_COLORS["blue"],
    PM_CHART_COLORS["cyan"],
    PM_CHART_COLORS["gold"],
    PM_CHART_COLORS["lime"],
]


def chart_indicadores_metas_por_factor(rows: pd.DataFrame) -> go.Figure:
    """Barras agrupadas por Factor: conteo de indicadores con Meta definida
    en cada año 2026-2030 (5 series, una por año, colores exactos del mockup).
    """
    if rows is None or rows.empty:
        return _empty_fig("Sin indicadores para este filtro")

    factores = sorted(int(f) for f in rows["Factor_num"].dropna().unique())
    if not factores:
        return _empty_fig("Sin indicadores para este filtro")

    fig = go.Figure()
    for year, color in zip(_METAS_FUTURAS, _METAS_FUTURAS_COLORS):
        col = f"Meta_num_{year}"
        if col not in rows.columns:
            continue
        conteos = [int(rows.loc[rows["Factor_num"] == f, col].notna().sum()) for f in factores]
        fig.add_trace(go.Bar(name=year, x=[f"F{f}" for f in factores], y=conteos, marker_color=color))

    fig.update_layout(
        barmode="group",
        title="Indicadores con meta definida por año y factor",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=50, b=10),
        height=270,
        xaxis=dict(gridcolor=PM_CHART_COLORS["grid"]),
        yaxis=dict(gridcolor=PM_CHART_COLORS["grid"], dtick=1),
        **_TRANSPARENT_LAYOUT,
    )
    return fig


def chart_indicadores_cumplimiento(rows: pd.DataFrame) -> go.Figure:
    """Barras agrupadas por indicador: % Cumplimiento 2025 vs 2026, solo filas
    con al menos un dato. Incluye línea de referencia en 100% (mejora
    aprobada por el usuario, no está en el mockup original)."""
    if rows is None or rows.empty:
        return _empty_fig("Sin indicadores para este filtro")

    df_plot = rows[rows["Cump_calc_2025"].notna() | rows["Cump_calc_2026"].notna()].sort_values("Factor_num")
    if df_plot.empty:
        return _empty_fig("Sin datos de cumplimiento para este filtro")

    labels = [_truncate(i, 22) for i in df_plot["Indicador"]]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="% Cumplimiento 2025",
            x=labels,
            y=(df_plot["Cump_calc_2025"] * 100),
            marker_color=PM_CHART_COLORS["blue"],
        )
    )
    fig.add_trace(
        go.Bar(
            name="% Cumplimiento 2026",
            x=labels,
            y=(df_plot["Cump_calc_2026"] * 100),
            marker_color=PM_CHART_COLORS["gold"],
        )
    )
    fig.add_hline(y=100, line_dash="dash", line_color=PM_CHART_COLORS["hline"])

    fig.update_layout(
        barmode="group",
        title="% de cumplimiento por indicador",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=50, b=120),
        height=270,
        yaxis=dict(ticksuffix="%", gridcolor=PM_CHART_COLORS["grid"]),
        xaxis=dict(tickangle=-50, tickfont=dict(size=9.5)),
        **_TRANSPARENT_LAYOUT,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Pestaña Métricas
# ─────────────────────────────────────────────────────────────────────────────


def _strip_factor_prefix(factor_label: str) -> str:
    text = str(factor_label or "")
    return text.split(".", 1)[1].strip() if "." in text else text.strip()


def chart_metricas_por_factor(df_historico: pd.DataFrame) -> go.Figure:
    """Barra horizontal: conteo de métricas con histórico por factor — resumen
    global fijo (no reacciona a los filtros de la tabla, igual que el mockup).

    Mejora aprobada por el usuario (no está en el mockup, donde era puramente
    decorativo): las barras son clicables — el llamador debe usar
    `st.plotly_chart(fig, on_select="rerun")` y leer `customdata` (nombre
    completo del Factor) del punto seleccionado para aplicarlo como filtro.
    """
    if df_historico is None or df_historico.empty:
        return _empty_fig("Sin métricas con histórico")

    counts = (
        df_historico.groupby(["Factor_num", "Factor"], dropna=False)
        .size()
        .reset_index(name="n")
        .sort_values("Factor_num")
    )
    labels = [_truncate(_strip_factor_prefix(f), 26) for f in counts["Factor"]]

    fig = go.Figure(
        go.Bar(
            x=counts["n"],
            y=labels,
            orientation="h",
            marker_color=PM_CHART_COLORS["cyan"],
            customdata=counts["Factor"],
            hovertemplate="<b>%{y}</b><br>%{x} métrica(s)<extra></extra>",
        )
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=280,
        xaxis=dict(gridcolor=PM_CHART_COLORS["grid"]),
        **_TRANSPARENT_LAYOUT,
    )
    return fig


def chart_metrica_detalle(historico_row: pd.Series) -> go.Figure:
    """Línea de Ejecución (área rellena) + línea punteada de Meta — solo si
    algún punto de la serie tiene Meta no nula — para el modal de métrica."""
    serie = historico_row.get("serie") or []
    if not serie:
        return _empty_fig("Sin datos de la serie")

    anios = [p["anio"] for p in serie]
    ejecucion = [p["ejecucion"] for p in serie]
    metas = [p["meta"] for p in serie]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=anios,
            y=ejecucion,
            mode="lines+markers",
            name="Resultado",
            line=dict(color=PM_CHART_COLORS["blue"], width=2),
            marker=dict(size=7, color=PM_CHART_COLORS["blue"]),
            fill="tozeroy",
            fillcolor="rgba(34,178,222,.12)",
        )
    )
    if any(m is not None and pd.notna(m) for m in metas):
        fig.add_trace(
            go.Scatter(
                x=anios,
                y=metas,
                mode="lines",
                name="Meta",
                line=dict(color=PM_CHART_COLORS["gold"], width=2, dash="dash"),
            )
        )

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=30, b=10),
        height=240,
        yaxis=dict(gridcolor=PM_CHART_COLORS["grid"]),
        **_TRANSPARENT_LAYOUT,
    )
    fig.update_xaxes(type="category")
    return fig
