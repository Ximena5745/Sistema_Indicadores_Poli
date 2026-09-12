"""
pages/plan_mejoramiento.py — Plan de Mejoramiento CNA (vista plana)

Réplica del mockup `plan_mejoramiento_cna.html` (ver plan
`rol-actuar-como-scalable-hollerith.md`): 2 pestañas planas — Indicadores /
Métricas — con KPIs, filtros, gráfico y tabla clickable con modal de detalle.
Sin drilldown Factor→Característica→Indicador (reemplazado por completo).

Fuentes de datos (sin join a nivel indicador — ver
docs/metodologia_plan_cna.md):
  - Indicadores del Plan: `load_plan_indicadores()` (66 filas, Meta/Ejecución/
    %Cump 2025-2026, metas 2026-2030).
  - Métricas CNA: `build_metricas_historico()` (serie anual completa por
    indicador/subindicador, con tendencia Creciente/Decreciente/Estable/Sin
    suficiente historia).
"""

from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from services.plan_mejoramiento_loader import (
    TENDENCIA_METRICAS_FILTRO_OPTIONS,
    build_metricas_historico,
    get_factor_options,
    load_plan_indicadores,
)
from streamlit_app.components.plan_mejoramiento_charts import (
    chart_indicadores_cumplimiento,
    chart_indicadores_metas_por_factor,
    chart_metrica_detalle,
    chart_metricas_por_factor,
)
from streamlit_app.pages.plan_mejoramiento_utils import (
    PM_COLORS,
    build_indicador_cump_texto,
    build_indicador_metas_futuras_texto,
    fmt_num_or_dash,
    fmt_variacion_or_dash,
    kpi_card_html,
    tipo_tag_html,
    variacion_html,
)

_METAS_FUTURAS_YEARS = ("2026", "2027", "2028", "2029", "2030")
_TIPO_FILTRO_MAP = {"Solo indicadores": "Indicador", "Solo métricas": "Metrica", "Sin clasificar": "Pendiente"}


# ─────────────────────────────────────────────────────────────────────────────
# Estilos / hero
# ─────────────────────────────────────────────────────────────────────────────

def _inject_pm_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');
        div[data-testid="stAppViewContainer"] * { font-family: 'Montserrat', sans-serif; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_hero() -> None:
    st.markdown(
        f'<div style="background:linear-gradient(120deg,{PM_COLORS["navy"]} 0%,#1B2C46 100%);'
        f'color:#fff;border-radius:14px;padding:20px 26px;margin-bottom:14px;'
        f'display:flex;align-items:center;gap:14px;">'
        f'<div style="width:34px;height:34px;border-radius:9px;flex:none;'
        f'background:linear-gradient(135deg,{PM_COLORS["blue"]},{PM_COLORS["cyan"]});'
        f'display:flex;align-items:center;justify-content:center;font-weight:800;'
        f'color:{PM_COLORS["navy"]};font-size:14px;">P</div>'
        f'<div>'
        f'<div style="font-size:18px;font-weight:700;">Evaluación de Indicadores y Métricas — Modelo CNA</div>'
        f'<div style="font-size:12px;color:rgba(255,255,255,.72);margin-top:2px;">'
        f'Politécnico Grancolombiano · Gerencia de Planeación · Medición y Mejora</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def _or_default(value, default: str = "—") -> str:
    """`value or default` falla si `value` es NaN (float NaN es truthy en
    Python) — este helper comprueba nulos explícitamente."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    text = str(value).strip()
    return text if text else default


def _factor_full_badge_html(factor_label: str | None) -> str:
    return (
        f'<span style="display:inline-block;font-size:11px;font-weight:800;color:#fff;'
        f'background:{PM_COLORS["navy"]};padding:3px 10px;border-radius:6px;">'
        f'{factor_label or "—"}</span>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# Pestaña Indicadores
# ─────────────────────────────────────────────────────────────────────────────

def _render_export_button(rows_view: pd.DataFrame, es_metas: bool) -> None:
    if rows_view.empty:
        st.button("Exportar a Excel", disabled=True, use_container_width=True, key="pm_export_disabled")
        return

    def _num(serie: pd.Series) -> pd.Series:
        return pd.to_numeric(serie, errors="coerce")

    if es_metas:
        data = pd.DataFrame(
            {
                "Factor": rows_view["Factor"],
                "Característica": rows_view["Caracteristica"],
                "Indicador": rows_view["Indicador"],
                "Tipo": rows_view["Tipo"],
                **{f"Meta {y}": _num(rows_view[f"Meta_num_{y}"]) for y in _METAS_FUTURAS_YEARS},
            }
        )
        sheet_name, file_suffix = "Metas 2026-2030", "metas"
    else:
        data = pd.DataFrame(
            {
                "Factor": rows_view["Factor"],
                "Indicador": rows_view["Indicador"],
                "Meta 2025": _num(rows_view["Meta_num_2025"]),
                "Ejecución 2025": _num(rows_view["Ejecucion_num_2025"]),
                "% Cump 2025": _num(rows_view["Cump_calc_2025"]) * 100,
                "Meta 2026": _num(rows_view["Meta_num_2026"]),
                "Ejecución 2026": _num(rows_view["Ejecucion_num_2026"]),
                "% Cump 2026": _num(rows_view["Cump_calc_2026"]) * 100,
            }
        )
        sheet_name, file_suffix = "Cumplimiento historico", "cumplimiento"

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        data.to_excel(writer, sheet_name=sheet_name, index=False)

    st.download_button(
        "Exportar a Excel",
        data=buffer.getvalue(),
        file_name=f"indicadores_{file_suffix}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        key="pm_export_btn",
    )


def _open_indicador_modal(row: pd.Series) -> None:
    @st.dialog(row["Indicador"])
    def _dialog() -> None:
        st.markdown(_factor_full_badge_html(row.get("Factor")), unsafe_allow_html=True)
        st.markdown("**Característica**")
        st.write(_or_default(row.get("Caracteristica")))

        c1 = st.columns(2)
        with c1[0]:
            st.markdown("**Acción de mejora**")
            st.write(_or_default(row.get("Accion_Mejora")))
        with c1[1]:
            st.markdown("**Tipo**")
            st.markdown(tipo_tag_html(row.get("Tipo")), unsafe_allow_html=True)

        c2 = st.columns(2)
        with c2[0]:
            st.markdown("**Estado / Aprobación**")
            st.write(f"{_or_default(row.get('Estado_raw'))} / {_or_default(row.get('Estado_Aprobacion'))}")
        with c2[1]:
            st.markdown("**Responsable**")
            st.write(_or_default(row.get("Responsable")))

        c3 = st.columns(2)
        with c3[0]:
            st.markdown("**Fuente**")
            st.write(_or_default(row.get("Fuente")))
        with c3[1]:
            st.markdown("**Periodicidad**")
            st.write(_or_default(row.get("Periodicidad"), "No definida"))

        st.markdown("**Fórmula**")
        st.write(_or_default(row.get("Formula"), "No registrada"))
        st.markdown("**Observación de desempeño**")
        st.write(_or_default(row.get("Observacion"), "Sin observaciones"))
        st.markdown("**Meta / Ejecución / % Cumplimiento — 2025 y 2026**")
        st.write(build_indicador_cump_texto(row))
        st.markdown("**Metas 2026 – 2030**")
        st.write(build_indicador_metas_futuras_texto(row))

    _dialog()


def _render_tab_indicadores(df_plan: pd.DataFrame) -> None:
    total = len(df_plan)
    meta_cols = [f"Meta_num_{y}" for y in _METAS_FUTURAS_YEARS]
    con_meta = int(df_plan[meta_cols].notna().any(axis=1).sum()) if total else 0
    con_hist = int((df_plan["Cump_calc_2025"].notna() | df_plan["Cump_calc_2026"].notna()).sum()) if total else 0
    aprobados = int((df_plan["Estado_Aprobacion"] == "Aprobado").sum()) if total else 0
    pct_aprobados = round(aprobados / total * 100) if total else 0

    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        st.markdown(
            kpi_card_html("Indicadores del plan", total, "asociados a 12 factores CNA", PM_COLORS["blue"]),
            unsafe_allow_html=True,
        )
    with kpi_cols[1]:
        st.markdown(
            kpi_card_html("Con meta 2026–2030", con_meta, "al menos un año definido", PM_COLORS["cyan"]),
            unsafe_allow_html=True,
        )
    with kpi_cols[2]:
        st.markdown(
            kpi_card_html("Con cumplimiento histórico", con_hist, "dato real en 2025 y/o 2026", PM_COLORS["gold"]),
            unsafe_allow_html=True,
        )
    with kpi_cols[3]:
        st.markdown(
            kpi_card_html("Aprobados", aprobados, f"{pct_aprobados}% del total", PM_COLORS["lime"]),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

    subview = st.segmented_control(
        "Sub-vista",
        ["Metas 2026–2030", "Cumplimiento histórico"],
        default="Metas 2026–2030",
        required=True,
        key="pm_ind_subview",
        label_visibility="collapsed",
    )
    es_metas = subview == "Metas 2026–2030"

    st.subheader(subview)
    st.caption(
        "Trayectoria de metas definidas por indicador, agrupadas por factor CNA."
        if es_metas
        else "Meta, ejecución y % de cumplimiento 2025–2026, solo para indicadores con información registrada."
    )

    factores = get_factor_options()
    filt_cols = st.columns([2, 2, 3, 1.4, 1.6])
    with filt_cols[0]:
        factor_sel = st.selectbox(
            "Factor", ["Todos los factores"] + [f["label"] for f in factores], key="pm_ind_factor"
        )
    with filt_cols[1]:
        tipo_sel = st.selectbox(
            "Tipo",
            ["Indicador y métrica", "Solo indicadores", "Solo métricas", "Sin clasificar"],
            key="pm_ind_tipo",
        )
    with filt_cols[2]:
        query = st.text_input(
            "Buscar",
            placeholder="Buscar por indicador, característica...",
            key="pm_ind_search",
            label_visibility="collapsed",
        )

    rows = df_plan.copy()
    if factor_sel != "Todos los factores":
        rows = rows[rows["Factor"] == factor_sel]
    if tipo_sel in _TIPO_FILTRO_MAP:
        rows = rows[rows["Tipo"] == _TIPO_FILTRO_MAP[tipo_sel]]
    if query.strip():
        q = query.strip().lower()
        hay = (
            rows["Indicador"].fillna("") + " " + rows["Caracteristica"].fillna("") + " " + rows["Accion_Mejora"].fillna("")
        ).str.lower()
        rows = rows[hay.str.contains(q, na=False, regex=False)]

    rows_view = (
        rows[rows[meta_cols].notna().any(axis=1)]
        if es_metas
        else rows[rows["Cump_calc_2025"].notna() | rows["Cump_calc_2026"].notna()]
    )

    with filt_cols[3]:
        st.markdown(
            f'<div style="text-align:center;font-size:11.5px;font-weight:700;color:{PM_COLORS["navy"]};'
            f'background:{PM_COLORS["surface_2"]};padding:8px 10px;border-radius:9px;'
            f'border:1px solid {PM_COLORS["border"]};">'
            f'{len(rows_view)} {"con meta definida" if es_metas else "con dato histórico"}</div>',
            unsafe_allow_html=True,
        )
    with filt_cols[4]:
        _render_export_button(rows_view, es_metas)

    st.plotly_chart(
        chart_indicadores_metas_por_factor(rows_view) if es_metas else chart_indicadores_cumplimiento(rows_view),
        use_container_width=True,
    )

    if rows_view.empty:
        st.info(
            "No hay indicadores con metas 2026–2030 definidas para este filtro."
            if es_metas
            else "Ningún indicador de este filtro tiene cumplimiento histórico registrado todavía."
        )
        return

    rows_sorted = rows_view.sort_values("Factor_num").reset_index(drop=True)
    factor_col = [f"F{int(f)}" if pd.notna(f) else "—" for f in rows_sorted["Factor_num"]]

    if es_metas:
        display = pd.DataFrame(
            {
                "Factor": factor_col,
                "Indicador": rows_sorted["Indicador"],
                "Tipo": rows_sorted["Tipo"],
                "Meta 2026": rows_sorted["Meta_num_2026"].map(fmt_num_or_dash),
                "Meta 2027": rows_sorted["Meta_num_2027"].map(fmt_num_or_dash),
                "Meta 2028": rows_sorted["Meta_num_2028"].map(fmt_num_or_dash),
                "Meta 2029": rows_sorted["Meta_num_2029"].map(fmt_num_or_dash),
                "Meta 2030": rows_sorted["Meta_num_2030"].map(fmt_num_or_dash),
            }
        )
    else:
        display = pd.DataFrame(
            {
                "Factor": factor_col,
                "Indicador": rows_sorted["Indicador"],
                "Meta 2025": rows_sorted["Meta_num_2025"].map(fmt_num_or_dash),
                "Ejec. 2025": rows_sorted["Ejecucion_num_2025"].map(fmt_num_or_dash),
                "% Cump 2025": (rows_sorted["Cump_calc_2025"] * 100).map(lambda v: fmt_num_or_dash(v, 1, "%")),
                "Meta 2026": rows_sorted["Meta_num_2026"].map(fmt_num_or_dash),
                "Ejec. 2026": rows_sorted["Ejecucion_num_2026"].map(fmt_num_or_dash),
                "% Cump 2026": (rows_sorted["Cump_calc_2026"] * 100).map(lambda v: fmt_num_or_dash(v, 1, "%")),
            }
        )

    event = st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="pm_ind_table",
    )
    seleccion = event.selection["rows"] if event and event.selection else []
    if seleccion:
        _open_indicador_modal(rows_sorted.iloc[seleccion[0]])


# ─────────────────────────────────────────────────────────────────────────────
# Pestaña Métricas
# ─────────────────────────────────────────────────────────────────────────────

def _open_metrica_modal(row: pd.Series) -> None:
    @st.dialog(row["Indicador"])
    def _dialog() -> None:
        st.markdown(_factor_full_badge_html(row.get("Factor")), unsafe_allow_html=True)
        subindicador = row.get("Subindicador")
        if _or_default(subindicador, "") and subindicador != row.get("Indicador"):
            st.caption(subindicador)

        st.plotly_chart(chart_metrica_detalle(row), use_container_width=True)

        c1 = st.columns(2)
        with c1[0]:
            st.markdown("**Proceso**")
            st.write(_or_default(row.get("Proceso")))
        with c1[1]:
            st.markdown("**Sentido / Periodicidad**")
            st.write(f"{_or_default(row.get('Sentido'))} · {_or_default(row.get('Periodicidad'))}")

        c2 = st.columns(2)
        with c2[0]:
            st.markdown("**Variación último año**")
            st.markdown(
                variacion_html(row.get("variacion_ultima_pct")) + " respecto al año anterior",
                unsafe_allow_html=True,
            )
        with c2[1]:
            st.markdown("**Variación promedio anual**")
            st.markdown(
                variacion_html(row.get("variacion_promedio_pct")) + " promedio interanual",
                unsafe_allow_html=True,
            )

    _dialog()


def _render_tab_metricas(df_historico: pd.DataFrame) -> None:
    total = len(df_historico)
    n_factores = df_historico["Factor"].nunique() if total else 0
    n_creciente = int((df_historico["tendencia"] == "Creciente").sum()) if total else 0
    n_decreciente = int((df_historico["tendencia"] == "Decreciente").sum()) if total else 0
    pct_creciente = round(n_creciente / total * 100) if total else 0
    pct_decreciente = round(n_decreciente / total * 100) if total else 0

    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        st.markdown(
            kpi_card_html("Métricas con histórico", total, "series 2019–2026", PM_COLORS["blue"]),
            unsafe_allow_html=True,
        )
    with kpi_cols[1]:
        st.markdown(
            kpi_card_html("Factores cubiertos", n_factores, "de 12 del modelo CNA", PM_COLORS["cyan"]),
            unsafe_allow_html=True,
        )
    with kpi_cols[2]:
        st.markdown(
            kpi_card_html("En tendencia creciente", n_creciente, f"{pct_creciente}% del total", PM_COLORS["gold"]),
            unsafe_allow_html=True,
        )
    with kpi_cols[3]:
        st.markdown(
            kpi_card_html(
                "En tendencia decreciente", n_decreciente, f"{pct_decreciente}% del total", PM_COLORS["magenta"]
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    st.subheader("Resultados por factor")
    st.caption("Número de métricas con serie histórica registrada, por factor del modelo CNA.")

    factores = get_factor_options()
    opciones_pill = ["Todos"] + [f["label"] for f in factores]

    chart_event = st.plotly_chart(
        chart_metricas_por_factor(df_historico),
        use_container_width=True,
        on_select="rerun",
        selection_mode="points",
        key="pm_met_factor_chart",
    )
    if chart_event and chart_event.selection and chart_event.selection["points"]:
        factor_clic = chart_event.selection["points"][0].get("customdata")
        if factor_clic in opciones_pill:
            st.session_state["pm_met_factor_pill"] = factor_clic

    st.subheader("Resultados, tendencia y variaciones")
    st.caption(
        "Selecciona un factor para filtrar. Haz clic en una métrica para ver su gráfica completa "
        "(resultado vs. meta cuando existe)."
    )

    st.session_state.setdefault("pm_met_factor_pill", "Todos")
    numero_por_label = {f["label"]: f["num"] for f in factores}

    filt_cols = st.columns([5, 2, 3])
    with filt_cols[0]:
        factor_sel = st.pills(
            "Factor",
            opciones_pill,
            format_func=lambda f: "Todos" if f == "Todos" else f"F{numero_por_label.get(f, '?')}",
            key="pm_met_factor_pill",
        )
    with filt_cols[1]:
        tendencia_sel = st.selectbox("Tendencia", TENDENCIA_METRICAS_FILTRO_OPTIONS, key="pm_met_tendencia")
    with filt_cols[2]:
        query = st.text_input(
            "Buscar", placeholder="Buscar métrica...", key="pm_met_search", label_visibility="collapsed"
        )

    factor_sel = factor_sel or "Todos"
    if factor_sel != "Todos":
        st.caption(f"Filtrando por: **{factor_sel}**")

    rows = df_historico.copy()
    if factor_sel != "Todos":
        rows = rows[rows["Factor"] == factor_sel]
    if tendencia_sel != "Toda tendencia":
        rows = rows[rows["tendencia"] == tendencia_sel]
    if query.strip():
        q = query.strip().lower()
        hay = (rows["Indicador"].fillna("") + " " + rows["Subindicador"].fillna("")).str.lower()
        rows = rows[hay.str.contains(q, na=False, regex=False)]

    if rows.empty:
        st.info("No hay métricas que coincidan con el filtro.")
        return

    rows_sorted = rows.sort_values("ultimo_anio", ascending=False, na_position="last").reset_index(drop=True)

    display = pd.DataFrame(
        {
            "Factor": [f"F{int(f)}" if pd.notna(f) else "—" for f in rows_sorted["Factor_num"]],
            "Métrica": [
                ind if (not sub or sub == ind) else f"{ind} · {sub}"
                for ind, sub in zip(rows_sorted["Indicador"], rows_sorted["Subindicador"])
            ],
            "Proceso": rows_sorted["Proceso"],
            "Último año": rows_sorted["ultimo_anio"].map(lambda v: fmt_num_or_dash(v, 0)),
            "Resultado": rows_sorted["ultimo_valor"].map(lambda v: fmt_num_or_dash(v, 2)),
            "Variación último año": rows_sorted["variacion_ultima_pct"].map(fmt_variacion_or_dash),
            # Solo texto plano — st.dataframe no soporta HTML/color por celda,
            # a diferencia del <span> coloreado del mockup (limitación nativa
            # de la grilla, ver plan §restricciones técnicas).
            "Tendencia": [
                tendencia if tendencia in ("Creciente", "Decreciente", "Estable") else "—"
                for tendencia in rows_sorted["tendencia"]
            ],
            "Serie": [
                [p["ejecucion"] for p in serie if p["ejecucion"] is not None] for serie in rows_sorted["serie"]
            ],
        }
    )

    event = st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="pm_met_table",
        column_config={
            "Serie": st.column_config.LineChartColumn("Serie", width="small"),
        },
    )
    seleccion = event.selection["rows"] if event and event.selection else []
    if seleccion:
        _open_metrica_modal(rows_sorted.iloc[seleccion[0]])


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def render() -> None:
    _inject_pm_styles()
    _render_hero()

    view = st.segmented_control(
        "Vista",
        ["Indicadores", "Métricas"],
        default="Indicadores",
        required=True,
        key="pm_active_view",
        label_visibility="collapsed",
    )

    df_plan = load_plan_indicadores()
    df_historico = build_metricas_historico()

    if df_plan.empty and df_historico.empty:
        st.warning("No se encontraron datos del Plan de Mejoramiento. Verifica los archivos en data/raw.")
        return

    if view == "Métricas":
        _render_tab_metricas(df_historico)
    else:
        _render_tab_indicadores(df_plan)

    st.caption(
        'Panel generado a partir de "Indicadores Plan de Mejoramiento" y '
        '"Resultados Consolidados CNA – Métricas" · Politécnico Grancolombiano'
    )
