"""
components/plan_mejoramiento_charts.py — Gráficos de tendencia CNA (Plotly)

Todos los gráficos codifican COLOR = TENDENCIA (favorable/desfavorable/
estable), nunca identidad de Factor — la identidad de Factor la da el ícono
CNA (ver utils/cna_icons.py). Sin Meta/Cumplimiento: no hay bandas de umbral,
solo dirección de Ejecución respecto al periodo anterior.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from core.config import SENTIDO_NEGATIVO, SENTIDO_POSITIVO
from streamlit_app.styles.design_system import COLORS

TREND_COLORS = {
    "favorable": COLORS["success"],
    "desfavorable": COLORS["danger"],
    "estable": COLORS["info"],
    "sin_datos": COLORS["gray_400"],
}

TREND_LABELS = {
    "favorable": "Favorable",
    "desfavorable": "Desfavorable",
    "estable": "Estable",
    "sin_datos": "Sin datos",
}


def chart_trend_ranking(
    df_agg: pd.DataFrame,
    category_col: str,
    title: str = "",
    category_order: list[str] | None = None,
) -> go.Figure:
    """Barra horizontal 100%-apilada (favorable/estable/desfavorable/sin dato).

    Cada barra suma siempre 100%, así las categorías son comparables sin
    importar cuántos indicadores tenga cada una (una con 2 indicadores no
    queda invisible frente a una con 25). El conteo real va en el hover y
    como texto dentro del segmento favorable.

    Deliberadamente NO es un ranking por desempeño: los Factores/
    Características agrupan métricas de naturaleza distinta (unidades,
    escalas, significado), así que ordenarlos por "% favorable" sugeriría
    una comparación que los datos no respaldan. `category_order` fija el
    orden canónico (p.ej. Factor 1→12); si no se provee, se usa el orden de
    aparición en `df_agg`.

    `df_agg`: salida de `aggregate_trend_by` (columnas n_favorable,
    n_estable, n_desfavorable, n_sin_datos, n_total).
    `category_col`: "Factor" o "Caracteristica".
    """
    if df_agg is None or df_agg.empty:
        fig = go.Figure()
        fig.update_layout(title="Sin datos disponibles")
        return fig

    df_plot = df_agg.copy()
    if category_order:
        orden = [c for c in category_order if c in df_plot[category_col].values]
        orden += [c for c in df_plot[category_col] if c not in orden]
        df_plot[category_col] = pd.Categorical(df_plot[category_col], categories=orden, ordered=True)
        df_plot = df_plot.sort_values(category_col)
    # Plotly dibuja el primer elemento del arreglo ABAJO; se invierte para
    # que el primero del orden solicitado quede arriba, como una lista.
    df_plot = df_plot.iloc[::-1]
    categorias = df_plot[category_col].astype(str).tolist()
    total_seguro = df_plot["n_total"].replace(0, 1)

    fig = go.Figure()
    for key in ("desfavorable", "estable", "favorable", "sin_datos"):
        pct = (df_plot[f"n_{key}"] / total_seguro * 100).round(1)
        counts = df_plot[f"n_{key}"]
        text = [f"{p:.0f}%" if key == "favorable" and p >= 10 else "" for p in pct]
        fig.add_trace(
            go.Bar(
                y=categorias,
                x=pct,
                name=TREND_LABELS[key],
                orientation="h",
                marker_color=TREND_COLORS[key],
                text=text,
                textposition="inside",
                textfont=dict(color="white", size=11),
                customdata=counts,
                hovertemplate=(
                    f"<b>%{{y}}</b><br>{TREND_LABELS[key]}: %{{customdata}} indicador(es) "
                    f"(%{{x:.0f}}%)<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        barmode="stack",
        title=title,
        xaxis_title="% de indicadores",
        yaxis_title="",
        xaxis=dict(range=[0, 100], ticksuffix="%"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=50, b=10),
        height=max(220, 40 * len(categorias) + 80),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    for cat, n_total in zip(categorias, df_plot["n_total"]):
        if n_total == 0:
            fig.add_annotation(
                x=50,
                y=cat,
                text="Sin indicadores con datos en el rango seleccionado",
                showarrow=False,
                font=dict(size=10, color=COLORS["gray_600"]),
            )
    return fig


def chart_evolucion_agregada(
    df_trend_series: pd.DataFrame,
    title: str = "",
    compact: bool = False,
) -> go.Figure:
    """Línea de % de indicadores favorables por Periodo (tendencia agregada).

    `df_trend_series`: DataFrame con columnas [Periodo, Periodo_anio,
    Periodo_sem, pct_favorable] — una fila por periodo evaluado.
    """
    fig = go.Figure()
    if df_trend_series is None or df_trend_series.empty:
        fig.update_layout(title="Sin datos suficientes para evolución")
        return fig

    df_plot = df_trend_series.sort_values(["Periodo_anio", "Periodo_sem"])
    fig.add_trace(
        go.Scatter(
            x=df_plot["Periodo"],
            y=df_plot["pct_favorable"],
            mode="lines+markers",
            line=dict(color=COLORS["primary"], width=2),
            marker=dict(size=8, color=COLORS["primary"]),
            hovertemplate="<b>%{x}</b><br>% Favorable: %{y:.1f}%<extra></extra>",
            showlegend=False,
        )
    )

    fig.update_layout(
        title=title,
        margin=dict(l=10, r=10, t=40 if title else 10, b=10),
        height=120 if compact else 320,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(type="category", visible=not compact)
    fig.update_yaxes(visible=not compact, ticksuffix="%" if not compact else None)
    if compact:
        fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig


def chart_trend_detail(df_serie: pd.DataFrame, titulo: str, sentido: str) -> go.Figure:
    """Línea + marcadores de Ejecución por Periodo para un indicador/subindicador.

    Eje x categórico (no temporal) por periodicidad irregular (Anual vs.
    Semestral). Color de marcador = tendencia del paso hacia ese punto.
    """
    fig = go.Figure()
    if df_serie is None or df_serie.empty:
        fig.update_layout(title="Sin datos disponibles")
        return fig

    df_plot = df_serie.sort_values(["Periodo_anio", "Periodo_sem"]).copy()
    valores = df_plot["Ejecucion_num"]

    positivo = str(SENTIDO_POSITIVO).strip().lower()
    negativo = str(SENTIDO_NEGATIVO).strip().lower()
    sentido_norm = str(sentido or "").strip().lower()
    sube_es_bueno = sentido_norm == positivo if sentido_norm in (positivo, negativo) else None

    marker_colors = [TREND_COLORS["sin_datos"]]
    for i in range(1, len(valores)):
        prev, curr = valores.iloc[i - 1], valores.iloc[i]
        if pd.isna(prev) or pd.isna(curr):
            marker_colors.append(TREND_COLORS["sin_datos"])
        elif curr == prev:
            marker_colors.append(TREND_COLORS["estable"])
        elif sube_es_bueno is None:
            marker_colors.append(TREND_COLORS["estable"])
        else:
            favorable = (curr > prev) == sube_es_bueno
            marker_colors.append(TREND_COLORS["favorable"] if favorable else TREND_COLORS["desfavorable"])

    fig.add_trace(
        go.Scatter(
            x=df_plot["Periodo"],
            y=valores,
            mode="lines+markers+text",
            line=dict(color="#455A64", width=2),
            marker=dict(size=12, color=marker_colors, line=dict(width=2, color="white")),
            text=[f"{v:,.0f}" if pd.notna(v) else "" for v in valores],
            textposition="top center",
            textfont=dict(size=9),
            hovertemplate="<b>%{x}</b><br>Ejecución: %{y:,.2f}<extra></extra>",
            showlegend=False,
        )
    )

    fig.update_layout(
        title=titulo,
        margin=dict(l=10, r=10, t=50, b=10),
        height=340,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(type="category")
    return fig


def _bucket_pct(pct: float | None) -> int:
    """Mismos umbrales que las píldoras de Factor: 0=sin dato, 1=desfavorable, 2=estable, 3=favorable."""
    if pct is None or pd.isna(pct):
        return 0
    if pct < 35:
        return 1
    if pct < 60:
        return 2
    return 3


_BUCKET_KEY = {0: "sin_datos", 1: "desfavorable", 2: "estable", 3: "favorable"}
# Colorscale en 4 bandas SÓLIDAS (sin degradado) — mismo semáforo que el
# resto de la página: rojo/azul/verde, nunca un tono intermedio confuso.
_BUCKET_COLORSCALE = [
    [0.00, TREND_COLORS["sin_datos"]], [0.25, TREND_COLORS["sin_datos"]],
    [0.25, TREND_COLORS["desfavorable"]], [0.50, TREND_COLORS["desfavorable"]],
    [0.50, TREND_COLORS["estable"]], [0.75, TREND_COLORS["estable"]],
    [0.75, TREND_COLORS["favorable"]], [1.00, TREND_COLORS["favorable"]],
]


def chart_heatmap_periodo(
    df_seg: pd.DataFrame,
    segment_col: str,
    title: str = "",
    row_order: list[str] | None = None,
) -> go.Figure:
    """Heatmap segmento × periodo — dónde y cuándo mejoró o se estancó cada uno.

    Cada celda se clasifica en las MISMAS 4 categorías (y colores sólidos)
    que el resto de la página — favorable/estable/desfavorable/sin dato —
    en vez de un degradado continuo, que con muestras pequeñas por celda
    genera tonos intermedios confusos y no dice nada de un vistazo.

    `row_order`: orden de filas de arriba hacia abajo (p.ej. el mismo orden
    del ranking de Factores) — mantiene consistencia visual con el resto de
    la página en vez de un orden propio que contradiga lo ya mostrado.
    """
    if df_seg is None or df_seg.empty:
        fig = go.Figure()
        fig.update_layout(title="Sin datos suficientes para el heatmap")
        return fig

    pivot = df_seg.pivot_table(index=segment_col, columns="Periodo", values="pct_favorable", aggfunc="mean")
    orden_periodo = (
        df_seg[["Periodo", "Periodo_anio", "Periodo_sem"]]
        .drop_duplicates()
        .sort_values(["Periodo_anio", "Periodo_sem"])["Periodo"]
        .tolist()
    )
    pivot = pivot.reindex(columns=orden_periodo)

    if row_order:
        orden_filas = [r for r in row_order if r in pivot.index] + [r for r in pivot.index if r not in row_order]
    else:
        orden_filas = sorted(pivot.index.tolist())
    # Plotly dibuja la primera fila del arreglo ABAJO; se invierte para que
    # el orden solicitado (mejor primero) quede arriba, como una lista.
    pivot = pivot.loc[list(reversed(orden_filas))]

    z = pivot.map(_bucket_pct)

    fig = go.Figure(
        go.Heatmap(
            z=z.values,
            x=pivot.columns,
            y=[str(i) for i in pivot.index],
            customdata=pivot.values,
            colorscale=_BUCKET_COLORSCALE,
            zmin=0,
            zmax=3,
            showscale=False,
            xgap=3,
            ygap=3,
            hovertemplate=(
                "<b>%{y}</b><br>%{x}: %{customdata:.0f}% favorable<extra></extra>"
            ),
            hoverongaps=False,
        )
    )
    fig.update_layout(
        title=title,
        margin=dict(l=10, r=10, t=50 if title else 10, b=10),
        height=max(240, 34 * len(pivot.index) + 100),
        xaxis=dict(type="category", side="bottom"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def chart_global_donut(agg_factor: pd.DataFrame) -> go.Figure:
    """Dona de composición global favorable/estable/desfavorable/sin dato."""
    fig = go.Figure()
    if agg_factor is None or agg_factor.empty:
        fig.update_layout(title="Sin datos disponibles")
        return fig

    totales = {
        key: int(agg_factor[f"n_{key}"].sum()) for key in ("favorable", "estable", "desfavorable", "sin_datos")
    }
    fig.add_trace(
        go.Pie(
            labels=[TREND_LABELS[k] for k in totales],
            values=list(totales.values()),
            hole=0.62,
            marker=dict(colors=[TREND_COLORS[k] for k in totales]),
            textinfo="percent",
            hovertemplate="<b>%{label}</b>: %{value} indicadores (%{percent})<extra></extra>",
        )
    )
    total_con_dato = totales["favorable"] + totales["estable"] + totales["desfavorable"]
    pct_fav = (totales["favorable"] / total_con_dato * 100) if total_con_dato else 0
    fig.add_annotation(
        text=f"<b>{pct_fav:.0f}%</b><br><span style='font-size:11px'>Favorable</span>",
        showarrow=False,
        font=dict(size=22, color=TREND_COLORS["favorable"] if pct_fav >= 50 else TREND_COLORS["desfavorable"]),
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        margin=dict(l=10, r=10, t=20, b=10),
        height=280,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def chart_sunburst_jerarquia(df_trend: pd.DataFrame, title: str = "") -> go.Figure:
    """Mapa jerárquico Factor→Característica→Indicador, coloreado por tendencia.

    `df_trend`: salida de `compute_trend_table(level="indicador")`, con una
    fila agregada `trend_score` (-1 desfavorable, 0 estable, 1 favorable) ya
    calculada por el llamador. Tamaño de cada segmento = conteo (1 por
    indicador); color = trend_score promedio del segmento.
    """
    if df_trend is None or df_trend.empty:
        fig = go.Figure()
        fig.update_layout(title="Sin datos disponibles")
        return fig

    df_plot = df_trend.copy()
    df_plot["peso"] = 1

    fig = px.sunburst(
        df_plot,
        path=["Factor", "Caracteristica", "Indicador"],
        values="peso",
        color="trend_score",
        color_continuous_scale=[[0, TREND_COLORS["desfavorable"]], [0.5, TREND_COLORS["estable"]], [1, TREND_COLORS["favorable"]]],
        range_color=[-1, 1],
        title=title,
    )
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=560)
    return fig
