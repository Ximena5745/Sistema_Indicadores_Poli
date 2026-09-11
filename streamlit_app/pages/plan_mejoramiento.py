"""
pages/plan_mejoramiento.py — Medición del Plan de Mejoramiento CNA

Dos módulos independientes (sin join a nivel indicador):

**P = Indicadores del Plan:** Meta → Ejecución → % Cumplimiento → Estado
  Fuente: Indicadores Plan de Mejoramiento.xlsx (66 indicadores)

**M = Métricas CNA:** Ejecución → Histórico → Dirección
  Fuente: Resultados_Consolidados_CNA_actualizado.xlsx (1142 registros)

Narrativa: Estado → Cumplimiento → Factor → Indicadores/Métricas → Tendencia
→ Avances, brechas y comportamiento.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from services.plan_mejoramiento_loader import (
    aggregate_plan_estado_by,
    aggregate_trend_by,
    build_indicador_series,
    compute_evolucion_agregada,
    compute_evolucion_por_segmento,
    compute_plan_cumplimiento_by_factor,
    compute_trend_table,
    get_caracteristicas_for_factor,
    get_factor_options,
    load_metricas_raw,
    load_plan_indicadores,
)
from streamlit_app.components.plan_mejoramiento_charts import (
    chart_evolucion_agregada,
    chart_global_donut,
    chart_heatmap_periodo,
    chart_sunburst_jerarquia,
    chart_trend_detail,
    chart_trend_ranking,
)
from streamlit_app.components.renderers import kpi_card, render_alert_strip
from streamlit_app.pages.plan_mejoramiento_utils import (
    build_alerts,
    build_breadcrumb_items,
    format_delta,
    format_ejecucion,
    trend_badge_html,
    trend_legend_html,
)
from streamlit_app.utils.cna_icons import factor_icon_data_uri, factor_icon_html

DRILL_KEYS = [
    "pm_drill_factor",
    "pm_drill_caracteristica",
    "pm_drill_indicador",
    "pm_drill_subindicador",
]


def _go(level_key: str, value) -> None:
    idx = DRILL_KEYS.index(level_key)
    for key in DRILL_KEYS[idx:]:
        st.session_state[key] = None
    st.session_state[level_key] = value


def _init_state() -> None:
    for key in DRILL_KEYS:
        st.session_state.setdefault(key, None)


def _short(text: str, n: int = 30) -> str:
    text = str(text or "")
    return text if len(text) <= n else text[: n - 1] + "…"


def _current_level() -> tuple[str, str | None, str | None, str | None, str | None]:
    factor = st.session_state["pm_drill_factor"]
    caracteristica = st.session_state["pm_drill_caracteristica"]
    indicador = st.session_state["pm_drill_indicador"]
    subindicador = st.session_state["pm_drill_subindicador"]

    if subindicador:
        level = "subindicador"
    elif indicador:
        level = "indicador"
    elif caracteristica:
        level = "caracteristica"
    elif factor:
        level = "factor"
    else:
        level = "resumen"
    return level, factor, caracteristica, indicador, subindicador


def render_breadcrumb(factor, caracteristica, indicador, subindicador) -> None:
    items = build_breadcrumb_items(factor, caracteristica, indicador, subindicador)
    cols = st.columns(len(items))
    for i, (level_key, label, value) in enumerate(items):
        with cols[i]:
            is_last = i == len(items) - 1
            short_label = _short(label, 24)
            if is_last:
                st.markdown(f"**{short_label}**")
            else:
                st.button(
                    short_label,
                    key=f"pm_bc_{i}_{level_key}_{label}",
                    on_click=_go,
                    args=(level_key, value),
                    use_container_width=True,
                )


def _period_range_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Filtro de rango de periodos (solo para Métricas M)."""
    if "Periodo" not in df.columns:
        return df
    periodo_order = (
        df[["Periodo", "Periodo_anio", "Periodo_sem"]]
        .drop_duplicates()
        .sort_values(["Periodo_anio", "Periodo_sem"])["Periodo"]
        .tolist()
    )
    if len(periodo_order) < 2:
        return df

    desde, hasta = st.select_slider(
        "Rango de periodos",
        options=periodo_order,
        value=(periodo_order[0], periodo_order[-1]),
        key="pm_periodo_range",
    )
    i0, i1 = periodo_order.index(desde), periodo_order.index(hasta)
    seleccionados = set(periodo_order[i0 : i1 + 1])
    return df[df["Periodo"].isin(seleccionados)]


def _quick_filter_panel() -> None:
    """Acceso directo por Factor/Característica."""
    factor = st.session_state["pm_drill_factor"]
    caracteristica = st.session_state["pm_drill_caracteristica"]

    factores = get_factor_options()
    opciones_factor = ["Todos los factores"] + [f["label"] for f in factores]
    idx_factor = opciones_factor.index(factor) if factor in opciones_factor else 0

    with st.container(border=True):
        cols = st.columns(2)
        with cols[0]:
            sel_factor = st.selectbox(
                "Ir directamente a un Factor",
                opciones_factor,
                index=idx_factor,
                key=f"pm_quick_factor_select_{factor}",
            )

        opciones_car = ["Todas las características"]
        if sel_factor != "Todos los factores":
            opciones_car += get_caracteristicas_for_factor(sel_factor)
        idx_car = opciones_car.index(caracteristica) if caracteristica in opciones_car else 0
        with cols[1]:
            sel_car = st.selectbox(
                "Ir directamente a una Característica",
                opciones_car,
                index=idx_car,
                disabled=sel_factor == "Todos los factores",
                key=f"pm_quick_car_select_{sel_factor}_{caracteristica}",
            )

    if sel_factor == "Todos los factores" and factor is not None:
        _go("pm_drill_factor", None)
    elif sel_factor != "Todos los factores" and sel_factor != factor:
        _go("pm_drill_factor", sel_factor)
    elif sel_car != "Todas las características" and sel_car != caracteristica:
        _go("pm_drill_caracteristica", sel_car)
    elif sel_car == "Todas las características" and caracteristica is not None and sel_factor == factor:
        _go("pm_drill_caracteristica", None)


# ─────────────────────────────────────────────────────────────────────────────
# helpers de presentación Plan
# ─────────────────────────────────────────────────────────────────────────────

_CUMP_COLORS = {
    "alto": "#43A047",
    "medio": "#FBAF17",
    "bajo": "#D32F2F",
    "sin_dato": "#BDBDBD",
}


def _cump_color(pct: float | None) -> str:
    if pct is None or pd.isna(pct):
        return _CUMP_COLORS["sin_dato"]
    if pct >= 0.90:
        return _CUMP_COLORS["alto"]
    if pct >= 0.60:
        return _CUMP_COLORS["medio"]
    return _CUMP_COLORS["bajo"]


def _cump_badge_html(pct: float | None, n_con_dato: int = 0, n_total: int = 0) -> str:
    """Badge de cumplimiento con color semáforo."""
    color = _cump_color(pct)
    if pct is None or pd.isna(pct):
        texto = "Sin dato"
    else:
        texto = f"{pct:.1%}"
    sub = f"({n_con_dato}/{n_total} con dato)" if n_total > 0 else ""
    return (
        f'<span style="display:inline-flex;align-items:center;gap:4px;'
        f'background:{color}1A;color:{color};border:1px solid {color}55;'
        f'border-radius:12px;padding:2px 10px;font-size:0.82rem;font-weight:600;">'
        f'<span style="width:8px;height:8px;border-radius:50%;background:{color};"></span>'
        f"{texto}</span>"
        f'<span style="font-size:0.72rem;color:#757575;margin-left:4px;">{sub}</span>'
    )


def _render_alerts(trend_ind: pd.DataFrame) -> None:
    alerts = build_alerts(trend_ind)
    disminuciones = [a for a in alerts if a["level"] == "info"]
    if disminuciones:
        render_alert_strip(
            f"{len(disminuciones)} indicador(es) disminuyeron en el último periodo reportado.",
            level="info",
        )


def _narrative_insight(pct_aumento: float, pct_disminucion: float, n_factores_mas_disminucion: int) -> str:
    texto = (
        f"Del total de indicadores con dato en el rango seleccionado, "
        f"<b>{pct_aumento:.0f}%</b> aumentó y <b>{pct_disminucion:.0f}%</b> disminuyó "
        f"respecto al periodo anterior."
    )
    if n_factores_mas_disminucion:
        texto += (
            f" En <b>{n_factores_mas_disminucion}</b> de los 12 factores, más indicadores "
            "disminuyeron que aumentaron en su último corte."
        )
    return texto


def _inject_factor_pill_css(factores: list[dict], agg_factor: pd.DataFrame, plan_cump: pd.DataFrame | None = None) -> None:
    """CSS por factor: píldora con imagen + badge %Cump (Plan) o % en aumento (M)."""
    agg_lookup = agg_factor.set_index("Factor") if agg_factor is not None and not agg_factor.empty else pd.DataFrame()
    cump_lookup = plan_cump.set_index("Factor") if plan_cump is not None and not plan_cump.empty else pd.DataFrame()
    rules = []
    for f in factores:
        key = f"pm_factor_btn_{f['num']}"
        uri = factor_icon_data_uri(f["num"])
        bg_rule = f"background-image:url({uri});" if uri else "background:#1A3A5C;"

        # Badge: preferir %Cump del Plan, si no hay usar % en aumento de Métricas
        if f["label"] in cump_lookup.index and pd.notna(cump_lookup.loc[f["label"], "cump_promedio"]):
            badge = f'{cump_lookup.loc[f["label"], "cump_promedio"]:.0%} cumplimiento'
        elif f["label"] in agg_lookup.index:
            badge = f'{agg_lookup.loc[f["label"], "pct_aumento"]:.0f}% en aumento'
        else:
            badge = "Sin dato"

        rules.append(
            f".st-key-{key} button {{"
            f"{bg_rule}"
            f"background-size:cover;background-position:center;background-repeat:no-repeat;"
            f"aspect-ratio:4/1;height:auto !important;min-height:0 !important;"
            f"border:none !important;border-radius:999px !important;width:100% !important;"
            f"padding:0 !important;position:relative;overflow:hidden;"
            f"box-shadow:0 2px 10px rgba(0,0,0,0.16) !important;"
            f"transition:transform .12s ease, box-shadow .12s ease !important;"
            f"}}"
            f".st-key-{key} button:hover {{"
            f"transform:translateY(-2px);box-shadow:0 8px 18px rgba(0,0,0,0.24) !important;"
            f"}}"
            f".st-key-{key} button p {{"
            f"position:absolute !important;width:1px !important;height:1px !important;padding:0 !important;"
            f"margin:-1px !important;overflow:hidden !important;clip:rect(0,0,0,0) !important;"
            f"white-space:nowrap !important;border:0 !important;"
            f"}}"
            f".st-key-{key} button::after {{"
            f'content:"{badge}";position:absolute;top:8px;right:14px;'
            f"background:rgba(255,255,255,0.94);color:#1A2B3C;font-size:0.66rem;font-weight:700;"
            f"padding:2px 9px;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,0.2);"
            f"}}"
        )
    st.markdown(f"<style>{''.join(rules)}</style>", unsafe_allow_html=True)


def _render_factor_pill_grid(factores: list[dict], agg_factor: pd.DataFrame, plan_cump: pd.DataFrame | None = None) -> None:
    _inject_factor_pill_css(factores, agg_factor, plan_cump)

    n_cols = 3
    for i in range(0, len(factores), n_cols):
        fila = factores[i : i + n_cols]
        cols = st.columns(len(fila))
        for col, f in zip(cols, fila):
            with col:
                st.button(
                    f["nombre"],
                    key=f"pm_factor_btn_{f['num']}",
                    on_click=_go,
                    args=("pm_drill_factor", f["label"]),
                    use_container_width=True,
                )


# ─────────────────────────────────────────────────────────────────────────────
# NIVEL 0 — Resumen Ejecutivo
# ─────────────────────────────────────────────────────────────────────────────

def section_resumen(df_m: pd.DataFrame, df_p: pd.DataFrame, periodo_filtered: pd.DataFrame) -> None:
    factores = get_factor_options()

    # ── Datos Plan (P) ──────────────────────────────────────────────
    estado_agg = aggregate_plan_estado_by(df_p)
    cump_factor = compute_plan_cumplimiento_by_factor(df_p)
    n_total = len(df_p)
    n_activo = int(estado_agg["n_Activo"].sum()) if not estado_agg.empty else 0
    n_aprobado = int(estado_agg["n_Aprobado"].sum()) if not estado_agg.empty else 0
    n_pendiente = int(estado_agg["n_Pendiente"].sum()) if not estado_agg.empty else 0

    vals_cump = cump_factor["cump_promedio"].dropna() if not cump_factor.empty else pd.Series(dtype=float)
    cump_general = float(vals_cump.mean()) if not vals_cump.empty else None
    n_con_dato_cump = int(cump_factor["n_con_dato"].sum()) if not cump_factor.empty else 0
    n_total_cump = int(cump_factor["n_total"].sum()) if not cump_factor.empty else 0

    # ── Datos Métricas (M) ──────────────────────────────────────────
    trend_ind = compute_trend_table(periodo_filtered, level="indicador")
    agg_factor = aggregate_trend_by(trend_ind, "Factor")
    con_dato = trend_ind[trend_ind["Tendencia"] != "sin_datos"] if not trend_ind.empty else trend_ind
    pct_aumento = (con_dato["Tendencia"] == "aumento").mean() * 100 if not con_dato.empty else 0.0
    pct_disminucion = (con_dato["Tendencia"] == "disminucion").mean() * 100 if not con_dato.empty else 0.0
    n_factores_mas_disminucion = (
        int((agg_factor["n_disminucion"] > agg_factor["n_aumento"]).sum()) if not agg_factor.empty else 0
    )

    # ── Hero: narrativa + dona ──────────────────────────────────────
    hero_cols = st.columns([3, 2])
    with hero_cols[0]:
        # Narrativa Plan
        cump_text = ""
        if cump_general is not None:
            cump_text = f"Cumplimiento general: <b>{cump_general:.1%}</b> ({n_con_dato_cump}/{n_total_cump} con dato). "
        st.markdown(
            f"<div style='background:linear-gradient(135deg,#EFF6FF 0%,#F8FAFF 100%);"
            f"border:1px solid #DCE8FA;border-radius:14px;padding:20px 22px;height:100%;"
            f"font-size:1.05rem;line-height:1.55;color:#1A2B3C;'>"
            f"{cump_text}"
            f"{_narrative_insight(pct_aumento, pct_disminucion, n_factores_mas_disminucion)}</div>",
            unsafe_allow_html=True,
        )
    with hero_cols[1]:
        st.plotly_chart(chart_global_donut(agg_factor), use_container_width=True)

    _render_alerts(trend_ind)

    # ── KPIs Estado (P) ────────────────────────────────────────────
    st.subheader("Estado del Plan de Mejoramiento")
    kpi_cols = st.columns(5)
    with kpi_cols[0]:
        kpi_card("Total Indicadores", n_total, show_progress=False)
    with kpi_cols[1]:
        kpi_card("Activos", n_activo, show_progress=False)
    with kpi_cols[2]:
        kpi_card("Aprobados", n_aprobado, show_progress=False)
    with kpi_cols[3]:
        kpi_card("Pendientes", n_pendiente, show_progress=False)
    with kpi_cols[4]:
        st.markdown("**Cumplimiento General**")
        st.markdown(_cump_badge_html(cump_general, n_con_dato_cump, n_total_cump), unsafe_allow_html=True)

    # ── Barras por factor: Cumplimiento (P) ─────────────────────────
    if not cump_factor.empty:
        cump_sorted = cump_factor.sort_values("Factor_num")
        st.subheader("Cumplimiento por Factor (Plan)")
        st.caption("Promedio de %Cump por factor — solo indicadores con Meta y Ejecución numéricas")
        fig_cump = _chart_cump_por_factor(cump_sorted)
        st.plotly_chart(fig_cump, use_container_width=True)

    # ── Los 12 Factores CNA — grid de píldoras ─────────────────────
    st.subheader("Los 12 Factores CNA")
    st.caption("Haz clic en un factor para explorar sus características, indicadores y métricas.")
    _render_factor_pill_grid(factores, agg_factor, cump_factor)

    # ── Heatmap Factor × Periodo (M) ────────────────────────────────
    st.subheader("Evolución por Factor y Periodo")
    st.caption("Cada celda resume el comportamiento de ese factor en ese periodo — orden 1 a 12.")
    evo_factor = compute_evolucion_por_segmento(periodo_filtered, "Factor")
    orden_factores = [f["label"] for f in factores]
    st.plotly_chart(chart_heatmap_periodo(evo_factor, "Factor", row_order=orden_factores), use_container_width=True)
    st.markdown(trend_legend_html(), unsafe_allow_html=True)

    # ── Tendencia histórica separada P y M ─────────────────────────
    with st.expander("Evolución de cumplimiento por periodo (Plan)"):
        evo_cump = _compute_evo_cump_por_periodo(df_p)
        if not evo_cump.empty:
            st.plotly_chart(_chart_evo_cump(evo_cump), use_container_width=True)
        else:
            st.info("Sin datos de cumplimiento en el rango seleccionado.")

    with st.expander("Evolución de dirección por periodo (Métricas)"):
        evo_dir = compute_evolucion_agregada(periodo_filtered)
        st.plotly_chart(chart_evolucion_agregada(evo_dir, "% en aumento por periodo"), use_container_width=True)

    with st.expander("Ver detalle en barras por Factor"):
        st.plotly_chart(chart_trend_ranking(agg_factor, "Factor", category_order=orden_factores), use_container_width=True)

    with st.expander("Ver mapa jerárquico completo"):
        _render_sunburst(trend_ind)


def _chart_cump_por_factor(cump_df: pd.DataFrame):
    """Barras horizontales de %Cump por factor con color semáforo."""
    import plotly.graph_objects as go

    if cump_df.empty:
        fig = go.Figure()
        fig.update_layout(title="Sin datos de cumplimiento")
        return fig

    df_plot = cump_df.copy().sort_values("Factor_num")
    df_plot = df_plot.iloc[::-1]  # invertir para que Factor 1 quede arriba

    colors = [_cump_color(v) for v in df_plot["cump_promedio"]]
    labels = [_short(f, 40) for f in df_plot["Factor"]]

    fig = go.Figure(
        go.Bar(
            y=labels,
            x=df_plot["cump_promedio"].fillna(0) * 100,
            orientation="h",
            marker_color=colors,
            text=[f"{v:.1%}" if pd.notna(v) else "Sin dato" for v in df_plot["cump_promedio"]],
            textposition="inside",
            textfont=dict(color="white", size=11),
            customdata=df_plot[["n_con_dato", "n_total"]].values,
            hovertemplate=(
                "<b>%{y}</b><br>%Cump: %{x:.1f}%<br>"
                "Con dato: %{customdata[0]}/%{customdata[1]}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=max(240, 34 * len(df_plot) + 40),
        xaxis=dict(range=[0, max(130, (df_plot["cump_promedio"].fillna(0).max() * 100 * 1.1))], ticksuffix="%"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _compute_evo_cump_por_periodo(df_p: pd.DataFrame) -> pd.DataFrame:
    """Serie de %Cump promedio por periodo (2025, 2026)."""
    rows = []
    for year in ("2025", "2026"):
        meta_col = f"Meta_num_{year}"
        ejec_col = f"Ejecucion_num_{year}"
        if meta_col not in df_p.columns or ejec_col not in df_p.columns:
            continue
        mask = df_p[meta_col].notna() & df_p[ejec_col].notna() & (df_p[meta_col] != 0)
        if mask.sum() == 0:
            continue
        vals = df_p.loc[mask, ejec_col] / df_p.loc[mask, meta_col]
        vals = vals.clip(upper=1.3)
        rows.append({
            "Periodo": f"{year}-2",
            "Periodo_anio": int(year),
            "Periodo_sem": 2,
            "pct_cumplimiento": float(vals.mean()) * 100,
            "n": int(mask.sum()),
        })
    return pd.DataFrame(rows)


def _chart_evo_cump(evo: pd.DataFrame):
    """Línea de %Cump promedio por periodo."""
    import plotly.graph_objects as go
    from streamlit_app.styles.design_system import COLORS

    fig = go.Figure()
    df_plot = evo.sort_values(["Periodo_anio", "Periodo_sem"])
    fig.add_trace(
        go.Scatter(
            x=df_plot["Periodo"],
            y=df_plot["pct_cumplimiento"],
            mode="lines+markers+text",
            line=dict(color=COLORS["primary"], width=2),
            marker=dict(size=10, color=COLORS["primary"]),
            text=[f"{v:.1f}%" for v in df_plot["pct_cumplimiento"]],
            textposition="top center",
            textfont=dict(size=10),
            hovertemplate="<b>%{x}</b><br>%Cump: %{y:.1f}%<br>n: %{customdata}<extra></extra>",
            customdata=df_plot["n"],
            showlegend=False,
        )
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        height=280,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(type="category")
    fig.update_yaxes(ticksuffix="%")
    return fig


def _render_sunburst(trend_ind: pd.DataFrame) -> None:
    if trend_ind.empty:
        st.info("Sin datos suficientes para el mapa jerárquico.")
        return
    trend_score = {"aumento": 1, "estable": 0, "disminucion": -1}
    df_plot = trend_ind.copy()
    df_plot["trend_score"] = df_plot["Tendencia"].map(trend_score)
    df_plot = df_plot.dropna(subset=["trend_score", "Factor", "Caracteristica", "Indicador"])
    if df_plot.empty:
        st.info("Sin datos suficientes para el mapa jerárquico.")
        return
    fig = chart_sunburst_jerarquia(df_plot, title="Factor → Característica → Indicador")
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# NIVEL 1 — Factor Seleccionado (tabs A: Indicadores / B: Métricas)
# ─────────────────────────────────────────────────────────────────────────────

def section_factor(df_m: pd.DataFrame, df_p: pd.DataFrame, periodo_filtered: pd.DataFrame, factor: str) -> None:
    # ── Header Factor ──────────────────────────────────────────────
    factor_nums = df_m[df_m["Factor"] == factor]["Factor_num"].dropna() if not df_m.empty else pd.Series()
    if factor_nums.empty and not df_p.empty:
        factor_nums = df_p[df_p["Factor"] == factor]["Factor_num"].dropna()
    factor_num = int(factor_nums.iloc[0]) if not factor_nums.empty else None

    header_cols = st.columns([1, 6])
    with header_cols[0]:
        if factor_num:
            st.markdown(factor_icon_html(factor_num, size=64), unsafe_allow_html=True)
    with header_cols[1]:
        st.subheader(factor)

    # ── KPIs Factor ────────────────────────────────────────────────
    # Plan (P)
    df_p_factor = df_p[df_p["Factor"] == factor] if not df_p.empty else pd.DataFrame()
    cump_f = compute_plan_cumplimiento_by_factor(df_p_factor)
    n_ind_p = len(df_p_factor)
    cump_f_val = float(cump_f["cump_promedio"].iloc[0]) if not cump_f.empty and pd.notna(cump_f["cump_promedio"].iloc[0]) else None
    n_brecha = int(cump_f["n_en_brecha"].iloc[0]) if not cump_f.empty else 0
    n_con_dato_f = int(cump_f["n_con_dato"].iloc[0]) if not cump_f.empty else 0

    # Métricas (M)
    df_m_factor = periodo_filtered[periodo_filtered["Factor"] == factor] if not periodo_filtered.empty else pd.DataFrame()
    trend_ind = compute_trend_table(df_m_factor, level="indicador")
    con_dato = trend_ind[trend_ind["Tendencia"] != "sin_datos"] if not trend_ind.empty else trend_ind
    pct_aumento = (con_dato["Tendencia"] == "aumento").mean() * 100 if not con_dato.empty else 0.0
    n_disminucion = int((trend_ind["Tendencia"] == "disminucion").sum()) if not trend_ind.empty else 0
    n_ind_m = trend_ind["Indicador"].nunique() if not trend_ind.empty else 0

    kpi_cols = st.columns(6)
    with kpi_cols[0]:
        kpi_card("Indicadores (P)", n_ind_p, show_progress=False)
    with kpi_cols[1]:
        st.markdown("**%Cump (P)**")
        st.markdown(_cump_badge_html(cump_f_val, n_con_dato_f, n_ind_p), unsafe_allow_html=True)
    with kpi_cols[2]:
        kpi_card("En brecha (P)", n_brecha, show_progress=False)
    with kpi_cols[3]:
        kpi_card("Métricas (M)", n_ind_m, show_progress=False)
    with kpi_cols[4]:
        kpi_card("% en aumento (M)", f"{pct_aumento:.0f}%", show_progress=False)
    with kpi_cols[5]:
        kpi_card("En disminución (M)", n_disminucion, show_progress=False)

    _render_alerts(trend_ind)

    # ── Tabs A/B ───────────────────────────────────────────────────
    tab_a, tab_b = st.tabs(["Indicadores del Plan (P)", "Métricas CNA (M)"])

    with tab_a:
        _render_tab_a_indicadores(df_p_factor, factor)

    with tab_b:
        _render_tab_b_metricas(df_m_factor, factor, periodo_filtered)


def _render_tab_a_indicadores(df_p_factor: pd.DataFrame, factor: str) -> None:
    """Tab A: Indicadores del Plan — Meta, Ejecución, %Cump, tendencia."""
    if df_p_factor.empty:
        st.info("Sin indicadores del Plan para este factor.")
        return

    st.caption("Indicadores del Plan de Mejoramiento — Meta → Ejecución → % Cumplimiento")

    # Características del factor
    caracteristicas = get_caracteristicas_for_factor(factor)

    for car in caracteristicas:
        df_car = df_p_factor[df_p_factor["Caracteristica"] == car]
        if df_car.empty:
            continue

        with st.expander(f"**{car}** ({len(df_car)} indicadores)", expanded=True):
            for _, row in df_car.iterrows():
                ind_name = row.get("Indicador", "")
                estado = row.get("Estado_final", "")
                tiene_med = row.get("tiene_medicion", False)

                # Calcular cumplimiento más reciente
                cump_val = None
                meta_val = None
                ejec_val = None
                periodo = None
                for year in ("2026", "2025"):
                    m = row.get(f"Meta_num_{year}")
                    e = row.get(f"Ejecucion_num_{year}")
                    if pd.notna(m) and pd.notna(e) and m != 0:
                        cump_val = min(e / m, 1.3)
                        meta_val = m
                        ejec_val = e
                        periodo = year
                        break

                with st.container(border=True):
                    cols = st.columns([3, 1, 1, 1])
                    with cols[0]:
                        st.markdown(f"**{ind_name}**")
                        if tiene_med:
                            st.caption(f"Estado: {estado}")
                        else:
                            st.caption(f"Estado: {estado} · Pendiente medición")
                    with cols[1]:
                        if meta_val is not None:
                            st.markdown("**Meta**")
                            st.caption(f"{meta_val:,.2f}")
                        else:
                            st.markdown("*Sin meta*")
                    with cols[2]:
                        if ejec_val is not None:
                            st.markdown("**Ejecución**")
                            st.caption(f"{ejec_val:,.2f} ({periodo})")
                        else:
                            st.markdown("*Sin ejecución*")
                    with cols[3]:
                        if cump_val is not None:
                            st.markdown("**%Cump**")
                            st.markdown(_cump_badge_html(cump_val), unsafe_allow_html=True)
                        else:
                            st.markdown("**%Cump**")
                            st.markdown(_cump_badge_html(None), unsafe_allow_html=True)


def _render_tab_b_metricas(df_m_factor: pd.DataFrame, factor: str, periodo_filtered: pd.DataFrame) -> None:
    """Tab B: Métricas CNA — Ejecución, histórico, dirección."""
    if df_m_factor.empty:
        st.info("Sin métricas CNA para este factor.")
        return

    st.caption("Métricas CNA — Ejecución por Periodo (sin Meta/Cumplimiento)")

    # Características del factor (desde catálogo canónico)
    caracteristicas = get_caracteristicas_for_factor(factor)
    agg_car = aggregate_trend_by(
        compute_trend_table(df_m_factor, level="indicador"), "Caracteristica"
    )

    if not agg_car.empty:
        st.subheader("Características")
        st.plotly_chart(
            chart_trend_ranking(agg_car, "Caracteristica", category_order=caracteristicas),
            use_container_width=True,
        )

    # Botones de drill-down por característica
    st.caption("Selecciona una característica para ver sus indicadores")
    n_cols = 3
    for i in range(0, len(caracteristicas), n_cols):
        fila = caracteristicas[i : i + n_cols]
        cols = st.columns(len(fila))
        for col, car in zip(cols, fila):
            with col:
                st.button(
                    _short(car, 40),
                    key=f"pm_car_btn_{car}",
                    on_click=_go,
                    args=("pm_drill_caracteristica", car),
                    use_container_width=True,
                )

    # Heatmap Característica × Periodo
    st.subheader("Evolución por Característica y Periodo")
    evo_car = compute_evolucion_por_segmento(df_m_factor, "Caracteristica")
    st.plotly_chart(chart_heatmap_periodo(evo_car, "Caracteristica", row_order=caracteristicas), use_container_width=True)
    st.markdown(trend_legend_html(), unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# NIVEL 2 — Característica / Indicador / Subindicador (Métricas existentes)
# ─────────────────────────────────────────────────────────────────────────────

def section_caracteristica(df_m: pd.DataFrame, periodo_filtered: pd.DataFrame, factor: str, caracteristica: str) -> None:
    df_car = periodo_filtered[(periodo_filtered["Factor"] == factor) & (periodo_filtered["Caracteristica"] == caracteristica)]
    st.subheader(caracteristica)

    trend_ind = compute_trend_table(df_car, level="indicador")
    con_dato = trend_ind[trend_ind["Tendencia"] != "sin_datos"] if not trend_ind.empty else trend_ind
    pct_aumento = (con_dato["Tendencia"] == "aumento").mean() * 100 if not con_dato.empty else 0.0
    n_disminucion = int((trend_ind["Tendencia"] == "disminucion").sum()) if not trend_ind.empty else 0

    kpi_cols = st.columns(3)
    with kpi_cols[0]:
        kpi_card("Indicadores", trend_ind["Indicador"].nunique() if not trend_ind.empty else 0, show_progress=False)
    with kpi_cols[1]:
        kpi_card("% en aumento", f"{pct_aumento:.0f}%", show_progress=False)
    with kpi_cols[2]:
        kpi_card("En disminución", n_disminucion, show_progress=False)

    _render_alerts(trend_ind)

    st.caption("Indicadores")
    if trend_ind.empty:
        st.info("Sin indicadores con datos para esta característica en el rango de periodos seleccionado.")
    else:
        n_cols = 2
        registros = trend_ind.to_dict("records")
        for i in range(0, len(registros), n_cols):
            fila = registros[i : i + n_cols]
            cols = st.columns(len(fila))
            for col, item in zip(cols, fila):
                with col:
                    with st.container(border=True):
                        st.markdown(f"**{item['Indicador']}**")
                        st.markdown(trend_badge_html(item["Tendencia"]), unsafe_allow_html=True)
                        st.caption(
                            f"Último: {format_ejecucion(item['ultimo_valor'], item['unidad'])} · {item['ultimo_periodo']}"
                        )
                        st.button(
                            "Ver detalle",
                            key=f"pm_ind_btn_{item['Indicador']}",
                            on_click=_go,
                            args=("pm_drill_indicador", item["Indicador"]),
                            use_container_width=True,
                        )

    evo = compute_evolucion_agregada(df_car)
    st.plotly_chart(chart_evolucion_agregada(evo, f"Evolución — {caracteristica}"), use_container_width=True)


def section_indicador(df_m: pd.DataFrame, periodo_filtered: pd.DataFrame, factor: str, indicador: str) -> None:
    df_ind_all = df_m[(df_m["Factor"] == factor) & (df_m["Indicador"] == indicador)]
    df_ind_filtered = periodo_filtered[(periodo_filtered["Factor"] == factor) & (periodo_filtered["Indicador"] == indicador)]

    st.subheader(indicador)
    proceso = df_ind_all["Proceso"].dropna().iloc[0] if not df_ind_all["Proceso"].dropna().empty else "—"
    periodicidad = df_ind_all["Periodicidad"].dropna().iloc[0] if not df_ind_all["Periodicidad"].dropna().empty else "—"
    st.caption(f"Proceso: {proceso} · Periodicidad: {periodicidad}")

    trend_row = compute_trend_table(df_ind_filtered, level="indicador")
    if not trend_row.empty:
        row = trend_row.iloc[0]
        kpi_cols = st.columns(3)
        with kpi_cols[0]:
            kpi_card(
                "Último valor",
                format_ejecucion(row["ultimo_valor"], row["unidad"]),
                delta=format_delta(row["delta_abs"], row["unidad"]),
                show_progress=False,
            )
        with kpi_cols[1]:
            st.markdown("**Dirección**")
            st.markdown(trend_badge_html(row["Tendencia"]), unsafe_allow_html=True)
            if row["Sentido"]:
                st.caption(f"Sentido (dato de origen): {row['Sentido']}")
        with kpi_cols[2]:
            kpi_card("Periodos con dato", int(row["n_periodos"]), show_progress=False)
    else:
        st.info("Sin datos para este indicador en el rango de periodos seleccionado.")

    serie = build_indicador_series(df_ind_filtered, ["Indicador"])
    _render_evolucion(serie)

    subindicadores = sorted(
        s
        for s in df_ind_all["Subindicador"].dropna().unique().tolist()
        if s and s.strip().lower() not in ("nan", "none", "") and s.strip() != indicador.strip()
    )
    if subindicadores:
        trend_sub = compute_trend_table(
            df_ind_filtered[df_ind_filtered["Subindicador"].isin(subindicadores)], level="subindicador"
        )
        trend_sub_lookup = trend_sub.set_index("Subindicador") if not trend_sub.empty else pd.DataFrame()

        st.caption("Subindicadores asociados — cada uno con su propio último valor y dirección")
        n_cols = 2
        for i in range(0, len(subindicadores), n_cols):
            fila = subindicadores[i : i + n_cols]
            cols = st.columns(len(fila))
            for col, sub in zip(cols, fila):
                with col:
                    with st.container(border=True):
                        st.markdown(f"**{sub}**")
                        if sub in trend_sub_lookup.index:
                            srow = trend_sub_lookup.loc[sub]
                            st.markdown(trend_badge_html(srow["Tendencia"]), unsafe_allow_html=True)
                            st.caption(
                                f"Último: {format_ejecucion(srow['ultimo_valor'], srow['unidad'])} · {srow['ultimo_periodo']}"
                            )
                        else:
                            st.caption("Sin dato en el rango seleccionado")
                        st.button(
                            "Ver detalle",
                            key=f"pm_sub_btn_{sub}",
                            on_click=_go,
                            args=("pm_drill_subindicador", sub),
                            use_container_width=True,
                        )
    else:
        st.caption("Este indicador no tiene subindicadores asociados.")


def section_subindicador(
    df_m: pd.DataFrame, periodo_filtered: pd.DataFrame, factor: str, indicador: str, subindicador: str
) -> None:
    df_sub_filtered = periodo_filtered[
        (periodo_filtered["Factor"] == factor)
        & (periodo_filtered["Indicador"] == indicador)
        & (periodo_filtered["Subindicador"] == subindicador)
    ]

    st.subheader(subindicador)
    st.caption(f"Indicador: {indicador}")

    trend_row = compute_trend_table(df_sub_filtered, level="subindicador")
    if not trend_row.empty:
        row = trend_row.iloc[0]
        kpi_cols = st.columns(3)
        with kpi_cols[0]:
            kpi_card(
                "Último valor",
                format_ejecucion(row["ultimo_valor"], row["unidad"]),
                delta=format_delta(row["delta_abs"], row["unidad"]),
                show_progress=False,
            )
        with kpi_cols[1]:
            st.markdown("**Dirección**")
            st.markdown(trend_badge_html(row["Tendencia"]), unsafe_allow_html=True)
            if row["Sentido"]:
                st.caption(f"Sentido (dato de origen): {row['Sentido']}")
        with kpi_cols[2]:
            kpi_card("Periodos con dato", int(row["n_periodos"]), show_progress=False)
    else:
        st.info("Sin datos para este subindicador en el rango de periodos seleccionado.")

    serie = build_indicador_series(df_sub_filtered, ["Indicador", "Subindicador"])
    _render_evolucion(serie)


def _render_evolucion(serie: pd.DataFrame) -> None:
    n_con_dato = int(serie["Ejecucion_num"].notna().sum()) if serie is not None and not serie.empty else 0
    if n_con_dato >= 2:
        st.plotly_chart(chart_trend_detail(serie, "Evolución de Ejecución"), use_container_width=True)
    elif n_con_dato == 1:
        st.info("Este indicador tiene un único periodo con dato — aún no es posible mostrar evolución.")
    else:
        st.info("Sin datos de Ejecución en el rango de periodos seleccionado.")
    _render_historia_table(serie)


def _render_historia_table(serie: pd.DataFrame) -> None:
    if serie is None or serie.empty:
        return

    serie = serie.sort_values(["Periodo_anio", "Periodo_sem"]).reset_index(drop=True)
    valores = serie["Ejecucion_num"]
    unidad_col = serie["Ejecución s"] if "Ejecución s" in serie.columns else pd.Series([None] * len(serie))

    filas = []
    for i in range(len(serie)):
        variacion = "—"
        if i > 0 and pd.notna(valores.iloc[i]) and pd.notna(valores.iloc[i - 1]) and valores.iloc[i - 1] != 0:
            variacion = f"{(valores.iloc[i] - valores.iloc[i - 1]) / valores.iloc[i - 1] * 100:+.1f}%"
        filas.append(
            {
                "Periodo": serie.loc[i, "Periodo"],
                "Ejecución": format_ejecucion(valores.iloc[i], unidad_col.iloc[i]),
                "Variación vs. periodo anterior": variacion,
            }
        )

    st.caption("Historial por periodo")
    st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def render() -> None:
    st.title("Plan de Mejoramiento (Factores CNA)")
    st.caption(
        "Ejecución y cumplimiento de los indicadores del Plan de Mejoramiento "
        "asociados a los factores de acreditación CNA. "
        "Referencia: Anexo 02 CESU 2020."
    )

    _init_state()

    # ── Cargar ambas fuentes ───────────────────────────────────────
    df_m = load_metricas_raw()
    df_p = load_plan_indicadores()

    if df_m.empty and df_p.empty:
        st.warning("No se encontraron datos del Plan de Mejoramiento. Verifica los archivos en data/raw.")
        return

    # ── Filtros ────────────────────────────────────────────────────
    periodo_filtered = _period_range_filter(df_m) if not df_m.empty else pd.DataFrame()
    _quick_filter_panel()

    # ── Navegación ─────────────────────────────────────────────────
    level, factor, caracteristica, indicador, subindicador = _current_level()
    if level != "resumen":
        render_breadcrumb(factor, caracteristica, indicador, subindicador)

    if level == "resumen":
        section_resumen(df_m, df_p, periodo_filtered)
    elif level == "factor":
        section_factor(df_m, df_p, periodo_filtered, factor)
    elif level == "caracteristica":
        section_caracteristica(df_m, periodo_filtered, factor, caracteristica)
    elif level == "indicador":
        section_indicador(df_m, periodo_filtered, factor, indicador)
    elif level == "subindicador":
        section_subindicador(df_m, periodo_filtered, factor, indicador, subindicador)
