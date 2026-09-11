"""
pages/plan_mejoramiento.py — Plan de Mejoramiento (Factores CNA)

Navegación jerárquica Factor → Característica → Indicador → Subindicador,
analizando exclusivamente Ejecución por Periodo (sin Meta/Cumplimiento ni
ficha técnica del indicador). Lectura ejecutiva macro→micro: Resumen de los
12 factores → Factor → Características → Indicadores → Subindicadores →
Evolución temporal, con breadcrumb persistente.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from services.plan_mejoramiento_loader import (
    aggregate_trend_by,
    build_indicador_series,
    compute_evolucion_agregada,
    compute_evolucion_por_segmento,
    compute_trend_table,
    get_caracteristicas_for_factor,
    get_factor_options,
    load_metricas_raw,
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
    """Acceso directo por Factor/Característica, alternativo al clic en el grid.

    Se evalúa ANTES de derivar el nivel actual, para que un cambio aquí se
    refleje en la misma corrida del script (sin necesidad de `st.rerun()`).
    """
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


def _render_alerts(trend_ind: pd.DataFrame) -> None:
    """Nota informativa, no una advertencia de "mal desempeño": son métricas
    crudas, una disminución no es intrínsecamente negativa."""
    alerts = build_alerts(trend_ind)
    disminuciones = [a for a in alerts if a["level"] == "info"]
    if disminuciones:
        render_alert_strip(
            f"{len(disminuciones)} indicador(es) disminuyeron en el último periodo reportado.",
            level="info",
        )


def _narrative_insight(pct_aumento: float, pct_disminucion: float, n_factores_mas_disminucion: int) -> str:
    """Puramente descriptivo: nunca califica el panorama de "bueno" o "malo",
    ni declara un factor "mejor" o "peor" — los 12 factores agrupan métricas
    de naturaleza distinta (unidades, escalas, significado) y no son
    comparables entre sí como un ranking único."""
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


def _inject_factor_pill_css(factores: list[dict], agg_factor: pd.DataFrame) -> None:
    """CSS por factor, dirigido a `.st-key-pm_factor_btn_<n>` (la clase que
    Streamlit agrega automáticamente a un widget cuando se le pasa `key=`).

    El fondo del st.button ES la imagen real de assets/CNA/{n}.jpeg (la
    píldora completa: ícono + nombre, ya diseñada) — no una recreación con
    Material Symbols. Ícono y botón son el mismo nodo del DOM: el texto
    nativo del botón se oculta visualmente (sigue accesible para lectores de
    pantalla) porque el nombre ya está dibujado en la imagen; el único
    contenido añadido por CSS es el badge de "% en aumento", que no existe
    en la imagen fuente.
    """
    agg_lookup = agg_factor.set_index("Factor") if agg_factor is not None and not agg_factor.empty else pd.DataFrame()
    rules = []
    for f in factores:
        key = f"pm_factor_btn_{f['num']}"
        uri = factor_icon_data_uri(f["num"])
        bg_rule = f"background-image:url({uri});" if uri else "background:#1A3A5C;"
        if f["label"] in agg_lookup.index:
            badge = f"{agg_lookup.loc[f['label'], 'pct_aumento']:.0f}% en aumento"
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


def _render_factor_pill_grid(factores: list[dict], agg_factor: pd.DataFrame) -> None:
    _inject_factor_pill_css(factores, agg_factor)

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


def section_resumen(df: pd.DataFrame, periodo_filtered: pd.DataFrame) -> None:
    factores = get_factor_options()
    trend_ind = compute_trend_table(periodo_filtered, level="indicador")
    agg_factor = aggregate_trend_by(trend_ind, "Factor")

    con_dato = trend_ind[trend_ind["Tendencia"] != "sin_datos"] if not trend_ind.empty else trend_ind
    pct_aumento = (con_dato["Tendencia"] == "aumento").mean() * 100 if not con_dato.empty else 0.0
    pct_disminucion = (con_dato["Tendencia"] == "disminucion").mean() * 100 if not con_dato.empty else 0.0
    n_factores_mas_disminucion = (
        int((agg_factor["n_disminucion"] > agg_factor["n_aumento"]).sum()) if not agg_factor.empty else 0
    )

    # ── Hero: narrativa ejecutiva + dona de composición global ─────────────
    hero_cols = st.columns([3, 2])
    with hero_cols[0]:
        st.markdown(
            f"<div style='background:linear-gradient(135deg,#EFF6FF 0%,#F8FAFF 100%);"
            f"border:1px solid #DCE8FA;border-radius:14px;padding:20px 22px;height:100%;"
            f"font-size:1.05rem;line-height:1.55;color:#1A2B3C;'>"
            f"{_narrative_insight(pct_aumento, pct_disminucion, n_factores_mas_disminucion)}</div>",
            unsafe_allow_html=True,
        )
    with hero_cols[1]:
        st.plotly_chart(chart_global_donut(agg_factor), use_container_width=True)

    _render_alerts(trend_ind)

    # ── Los 12 Factores CNA — grid de píldoras (basado en assets/CNA/Consolidado.png) ──
    # Ícono + nombre + % son UN solo st.button (icon= nativo), nunca dos
    # elementos apilados; el color de cada píldora viene de la misma paleta
    # institucional del material CNA, vía CSS dirigido a la clase estable
    # `st-key-<key>` que Streamlit asigna a cada widget con `key=`.
    st.subheader("Los 12 Factores CNA")
    st.caption("Haz clic en un factor para explorar sus características e indicadores.")
    _render_factor_pill_grid(factores, agg_factor)

    # ── Heatmap Factor × Periodo — dónde y cuándo mejoró/estancó cada uno ──
    # Orden fijo 1→12 (el mismo del grid de arriba), NUNCA por desempeño: los
    # 12 factores agrupan métricas de naturaleza distinta (unidades, escalas,
    # significado) y no son comparables entre sí como un ranking único — el
    # color de cada celda sigue mostrando el estado propio de ese factor.
    st.subheader("Evolución por Factor y Periodo")
    st.caption("Cada celda resume el comportamiento de ese factor en ese periodo — orden 1 a 12, sin implicar ranking entre factores.")
    evo_factor = compute_evolucion_por_segmento(periodo_filtered, "Factor")
    orden_factores = [f["label"] for f in factores]
    st.plotly_chart(chart_heatmap_periodo(evo_factor, "Factor", row_order=orden_factores), use_container_width=True)
    st.markdown(trend_legend_html(), unsafe_allow_html=True)

    with st.expander("Ver detalle en barras por Factor"):
        st.plotly_chart(chart_trend_ranking(agg_factor, "Factor", category_order=orden_factores), use_container_width=True)

    with st.expander("Ver mapa jerárquico completo"):
        _render_sunburst(trend_ind)


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


def _render_historia_table(serie: pd.DataFrame) -> None:
    """Tabla Periodo · Ejecución · Variación — evita que el detalle se pierda
    al quedarse solo con el último valor en las tarjetas KPI."""
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


def section_factor(df: pd.DataFrame, periodo_filtered: pd.DataFrame, factor: str) -> None:
    df_factor = periodo_filtered[periodo_filtered["Factor"] == factor]
    factor_nums = df[df["Factor"] == factor]["Factor_num"].dropna()
    factor_num = int(factor_nums.iloc[0]) if not factor_nums.empty else None

    header_cols = st.columns([1, 6])
    with header_cols[0]:
        if factor_num:
            st.markdown(factor_icon_html(factor_num, size=64), unsafe_allow_html=True)
    with header_cols[1]:
        st.subheader(factor)

    trend_ind = compute_trend_table(df_factor, level="indicador")
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

    # Orden fijo (el de la hoja Factor-Característica), nunca por desempeño:
    # las características agrupan métricas distintas y no son comparables
    # entre sí como un ranking único.
    caracteristicas = get_caracteristicas_for_factor(factor)
    agg_car = aggregate_trend_by(trend_ind, "Caracteristica")
    st.subheader("Características")
    st.plotly_chart(
        chart_trend_ranking(agg_car, "Caracteristica", category_order=caracteristicas), use_container_width=True
    )

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

    st.subheader("Evolución por Característica y Periodo")
    evo_car = compute_evolucion_por_segmento(df_factor, "Caracteristica")
    st.plotly_chart(chart_heatmap_periodo(evo_car, "Caracteristica", row_order=caracteristicas), use_container_width=True)
    st.markdown(trend_legend_html(), unsafe_allow_html=True)


def section_caracteristica(df: pd.DataFrame, periodo_filtered: pd.DataFrame, factor: str, caracteristica: str) -> None:
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


def section_indicador(df: pd.DataFrame, periodo_filtered: pd.DataFrame, factor: str, indicador: str) -> None:
    df_ind_all = df[(df["Factor"] == factor) & (df["Indicador"] == indicador)]
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
        with kpi_cols[2]:
            kpi_card("Periodos con dato", int(row["n_periodos"]), show_progress=False)
    else:
        st.info("Sin datos para este indicador en el rango de periodos seleccionado.")

    serie = build_indicador_series(df_ind_filtered, ["Indicador"])
    st.plotly_chart(chart_trend_detail(serie, "Evolución de Ejecución"), use_container_width=True)
    _render_historia_table(serie)

    subindicadores = sorted(
        s
        for s in df_ind_all["Subindicador"].dropna().unique().tolist()
        if s and s.strip().lower() not in ("nan", "none", "")
    )
    if subindicadores:
        st.caption("Subindicadores asociados")
        n_cols = 2
        for i in range(0, len(subindicadores), n_cols):
            fila = subindicadores[i : i + n_cols]
            cols = st.columns(len(fila))
            for col, sub in zip(cols, fila):
                with col:
                    with st.container(border=True):
                        st.markdown(f"**{sub}**")
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
    df: pd.DataFrame, periodo_filtered: pd.DataFrame, factor: str, indicador: str, subindicador: str
) -> None:
    df_sub_all = df[(df["Factor"] == factor) & (df["Indicador"] == indicador) & (df["Subindicador"] == subindicador)]
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
        with kpi_cols[2]:
            kpi_card("Periodos con dato", int(row["n_periodos"]), show_progress=False)
    else:
        st.info("Sin datos para este subindicador en el rango de periodos seleccionado.")

    serie = build_indicador_series(df_sub_filtered, ["Indicador", "Subindicador"])
    st.plotly_chart(chart_trend_detail(serie, "Evolución de Ejecución"), use_container_width=True)
    _render_historia_table(serie)


def render() -> None:
    st.title("Plan de Mejoramiento")
    st.caption("Ejecución por Periodo de los indicadores asociados a los factores de acreditación CNA.")

    _init_state()

    df = load_metricas_raw()
    if df.empty:
        st.warning(
            "No se encontraron datos del Plan de Mejoramiento. Verifica que "
            "'data/raw/Plan de mejoramiento/Resultados_Consolidados_CNA_actualizado.xlsx' exista."
        )
        return

    periodo_filtered = _period_range_filter(df)
    _quick_filter_panel()

    level, factor, caracteristica, indicador, subindicador = _current_level()
    if level != "resumen":
        render_breadcrumb(factor, caracteristica, indicador, subindicador)

    if level == "resumen":
        section_resumen(df, periodo_filtered)
    elif level == "factor":
        section_factor(df, periodo_filtered, factor)
    elif level == "caracteristica":
        section_caracteristica(df, periodo_filtered, factor, caracteristica)
    elif level == "indicador":
        section_indicador(df, periodo_filtered, factor, indicador)
    elif level == "subindicador":
        section_subindicador(df, periodo_filtered, factor, indicador, subindicador)
