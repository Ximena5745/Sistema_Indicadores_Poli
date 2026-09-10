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
    compute_trend_table,
    get_caracteristicas_for_factor,
    get_factor_options,
    load_metricas_raw,
)
from streamlit_app.components.plan_mejoramiento_charts import (
    TREND_COLORS,
    chart_evolucion_agregada,
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
)
from streamlit_app.utils.cna_icons import factor_icon_html, factor_icon_path

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
    alerts = build_alerts(trend_ind)
    danger = [a for a in alerts if a["level"] == "danger"]
    if danger:
        render_alert_strip(
            f"{len(danger)} indicador(es) muestran comportamiento desfavorable en el último periodo reportado.",
            level="danger",
        )


def section_resumen(df: pd.DataFrame, periodo_filtered: pd.DataFrame) -> None:
    factores = get_factor_options()
    trend_ind = compute_trend_table(periodo_filtered, level="indicador")
    agg_factor = aggregate_trend_by(trend_ind, "Factor")

    con_dato = trend_ind[trend_ind["Tendencia"] != "sin_datos"] if not trend_ind.empty else trend_ind
    total_ind = trend_ind["Indicador"].nunique() if not trend_ind.empty else 0
    pct_fav = (con_dato["Tendencia"] == "favorable").mean() * 100 if not con_dato.empty else 0.0
    pct_desfav = (con_dato["Tendencia"] == "desfavorable").mean() * 100 if not con_dato.empty else 0.0
    mejor = agg_factor.iloc[0]["Factor"] if not agg_factor.empty else "—"
    peor = agg_factor.iloc[-1]["Factor"] if not agg_factor.empty else "—"

    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        kpi_card("Indicadores con dato", total_ind, show_progress=False)
    with kpi_cols[1]:
        kpi_card("% Favorable global", f"{pct_fav:.0f}%", show_progress=False)
    with kpi_cols[2]:
        kpi_card("% Desfavorable global", f"{pct_desfav:.0f}%", show_progress=False)
    with kpi_cols[3]:
        st.markdown("**Mejor / peor factor**")
        st.caption(f"↑ {_short(mejor, 32)}")
        st.caption(f"↓ {_short(peor, 32)}")

    _render_alerts(trend_ind)

    st.subheader("Ranking de Factores")
    st.caption("Cada barra suma 100% — el color muestra la proporción de indicadores, sin importar cuántos tenga cada factor.")
    st.plotly_chart(chart_trend_ranking(agg_factor, "Factor"), use_container_width=True)

    st.subheader("Explorar por Factor")
    st.caption("Selecciona un factor para ver sus características e indicadores")
    agg_lookup = agg_factor.set_index("Factor") if not agg_factor.empty else pd.DataFrame()
    n_cols = 4
    for i in range(0, len(factores), n_cols):
        fila = factores[i : i + n_cols]
        cols = st.columns(len(fila))
        for col, f in zip(cols, fila):
            with col:
                with st.container(border=True):
                    st.image(str(factor_icon_path(f["num"])), use_container_width=True)
                    if f["label"] in agg_lookup.index:
                        pct = agg_lookup.loc[f["label"], "pct_favorable"]
                        color = TREND_COLORS["favorable"] if pct >= 50 else TREND_COLORS["desfavorable"]
                        st.markdown(
                            f"<div style='text-align:center;font-size:0.78rem;font-weight:700;color:{color};'>"
                            f"{pct:.0f}% favorable</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            "<div style='text-align:center;font-size:0.78rem;color:#9E9E9E;'>Sin dato</div>",
                            unsafe_allow_html=True,
                        )
                    st.button(
                        _short(f["nombre"], 28),
                        key=f"pm_factor_btn_{f['num']}",
                        on_click=_go,
                        args=("pm_drill_factor", f["label"]),
                        use_container_width=True,
                    )

    evo = compute_evolucion_agregada(periodo_filtered)
    st.plotly_chart(
        chart_evolucion_agregada(evo, "Evolución global — % indicadores con tendencia favorable"),
        use_container_width=True,
    )

    with st.expander("Ver mapa jerárquico completo"):
        _render_sunburst(trend_ind)


def _render_sunburst(trend_ind: pd.DataFrame) -> None:
    if trend_ind.empty:
        st.info("Sin datos suficientes para el mapa jerárquico.")
        return
    trend_score = {"favorable": 1, "estable": 0, "desfavorable": -1}
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
    pct_fav = (con_dato["Tendencia"] == "favorable").mean() * 100 if not con_dato.empty else 0.0
    n_desfav = int((trend_ind["Tendencia"] == "desfavorable").sum()) if not trend_ind.empty else 0

    kpi_cols = st.columns(3)
    with kpi_cols[0]:
        kpi_card("Indicadores", trend_ind["Indicador"].nunique() if not trend_ind.empty else 0, show_progress=False)
    with kpi_cols[1]:
        kpi_card("% Favorable", f"{pct_fav:.0f}%", show_progress=False)
    with kpi_cols[2]:
        kpi_card("Desfavorables", n_desfav, show_progress=False)

    _render_alerts(trend_ind)

    agg_car = aggregate_trend_by(trend_ind, "Caracteristica")
    st.subheader("Características")
    st.plotly_chart(chart_trend_ranking(agg_car, "Caracteristica"), use_container_width=True)

    caracteristicas = get_caracteristicas_for_factor(factor)
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

    evo = compute_evolucion_agregada(df_factor)
    st.plotly_chart(chart_evolucion_agregada(evo, f"Evolución — {factor}"), use_container_width=True)


def section_caracteristica(df: pd.DataFrame, periodo_filtered: pd.DataFrame, factor: str, caracteristica: str) -> None:
    df_car = periodo_filtered[(periodo_filtered["Factor"] == factor) & (periodo_filtered["Caracteristica"] == caracteristica)]
    st.subheader(caracteristica)

    trend_ind = compute_trend_table(df_car, level="indicador")
    con_dato = trend_ind[trend_ind["Tendencia"] != "sin_datos"] if not trend_ind.empty else trend_ind
    pct_fav = (con_dato["Tendencia"] == "favorable").mean() * 100 if not con_dato.empty else 0.0
    n_desfav = int((trend_ind["Tendencia"] == "desfavorable").sum()) if not trend_ind.empty else 0

    kpi_cols = st.columns(3)
    with kpi_cols[0]:
        kpi_card("Indicadores", trend_ind["Indicador"].nunique() if not trend_ind.empty else 0, show_progress=False)
    with kpi_cols[1]:
        kpi_card("% Favorable", f"{pct_fav:.0f}%", show_progress=False)
    with kpi_cols[2]:
        kpi_card("Desfavorables", n_desfav, show_progress=False)

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
            st.markdown("**Tendencia**")
            st.markdown(trend_badge_html(row["Tendencia"]), unsafe_allow_html=True)
            st.caption(f"Sentido: {row['Sentido'] or '—'}")
        with kpi_cols[2]:
            kpi_card("Periodos con dato", int(row["n_periodos"]), show_progress=False)
    else:
        st.info("Sin datos para este indicador en el rango de periodos seleccionado.")

    sentido = df_ind_all["Sentido"].dropna().iloc[0] if not df_ind_all["Sentido"].dropna().empty else ""
    serie = build_indicador_series(df_ind_filtered, ["Indicador"])
    st.plotly_chart(chart_trend_detail(serie, "Evolución de Ejecución", sentido), use_container_width=True)
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
            st.markdown("**Tendencia**")
            st.markdown(trend_badge_html(row["Tendencia"]), unsafe_allow_html=True)
            st.caption(f"Sentido: {row['Sentido'] or '—'}")
        with kpi_cols[2]:
            kpi_card("Periodos con dato", int(row["n_periodos"]), show_progress=False)
    else:
        st.info("Sin datos para este subindicador en el rango de periodos seleccionado.")

    sentido = df_sub_all["Sentido"].dropna().iloc[0] if not df_sub_all["Sentido"].dropna().empty else ""
    serie = build_indicador_series(df_sub_filtered, ["Indicador", "Subindicador"])
    st.plotly_chart(chart_trend_detail(serie, "Evolución de Ejecución", sentido), use_container_width=True)
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
