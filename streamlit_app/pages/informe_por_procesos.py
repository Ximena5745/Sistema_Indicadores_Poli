"""Informe por Procesos page - Main page module."""

import pandas as pd
import streamlit as st

from components.charts import grafico_historico_indicador, tabla_historica_indicador
from streamlit_app.services.data_service import DataService
from streamlit_app.pages.resumen_por_proceso import (
    _mes_to_num,
    _build_indicator_history,
    _latest_per_indicator,
    _render_auditoria_tab,
    _render_calidad_kpis_cards,
    _render_indicadores_subproceso_enhanced,
    _to_float,
)
from streamlit_app.pages.informe_por_procesos_config import MESES_OPCIONES, TAB_NAMES
from streamlit_app.pages.informe_por_procesos_utils import (
    load_propuestas,
    render_propuestas,
    build_summary_by_unit,
    build_frequency_summary,
    build_classification_summary,
    build_consolidated_columns,
    build_ia_indicators,
    prepare_filters,
    get_default_month,
)

# Re-exports for backward compatibility with tests
_load_propuestas = load_propuestas
_render_propuestas = render_propuestas
_build_summary_by_unit = build_summary_by_unit
_build_frequency_summary = build_frequency_summary
_build_classification_summary = build_classification_summary
_build_consolidated_columns = build_consolidated_columns
_build_ia_indicators = build_ia_indicators
_prepare_filters = prepare_filters


def render() -> None:
    """Main render function for the informe por procesos page.
    
    Displays:
    - Interactive filter panel (year, month, process, subprocess)
    - Six tabs: Indicadores, Evolución, Calidad, Auditoría, Propuestas, Análisis IA
    - Process-filtered indicators, historical evolution, quality metrics, audit info,
      proposed indicators, and risk/alert analysis
    """
    st.title("Informe por Procesos")

    ds = DataService()
    tracking_df = ds.get_tracking_data()
    map_df = ds.get_process_map()

    if tracking_df.empty:
        st.warning(
            "No se encontró data de seguimiento en data/output/Resultados Consolidados.xlsx (Consolidado Semestral)."
        )
        return
    if map_df.empty:
        st.warning("No se encontró el mapeo de procesos en data/raw/Subproceso-Proceso-Area.xlsx.")
        return

    try:
        from streamlit_app.components.filter_panel import render_filter_panel
    except ImportError:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from streamlit_app.components.filter_panel import render_filter_panel

    years = (
        sorted(
            [
                int(y)
                for y in pd.to_numeric(tracking_df["Anio"], errors="coerce").dropna().unique().tolist()
            ]
        )
        if "Anio" in tracking_df.columns
        else []
    )
    default_year = 2025 if 2025 in years else (years[-1] if years else None)
    default_month, default_month_num = get_default_month(tracking_df, default_year)

    topbar_year = st.session_state.get("topbar_year")
    topbar_month = st.session_state.get("topbar_month")

    # Panel único de filtros — opciones calculadas del estado previo de sesión
    if topbar_year is not None:
        anio = int(topbar_year)
        mes = str(topbar_month) if topbar_month is not None else default_month
        selected_month_num = MESES_OPCIONES.index(mes) + 1 if mes in MESES_OPCIONES else default_month_num
        full_work_df, snapshot_df = prepare_filters(tracking_df, map_df, int(anio), selected_month_num)
        procesos = sorted(snapshot_df["Proceso_padre"].dropna().astype(str).unique().tolist())
        proceso_sel_cur = st.session_state.get("filter_proceso", "Todos")
        subproceso_options_base: list[str] = sorted(
            snapshot_df[snapshot_df["Proceso_padre"].astype(str) == proceso_sel_cur][
                "Subproceso_final"
            ].dropna().astype(str).unique().tolist()
        ) if proceso_sel_cur != "Todos" else []
        sels_all = render_filter_panel(
            filters=[
                {"key": "proceso", "label": "Proceso", "type": "selectbox", "options": procesos, "include_all": True},
                {"key": "subproceso", "label": "Subproceso", "type": "selectbox", "options": subproceso_options_base, "include_all": True},
            ],
            title="", key_prefix="filter", n_cols=2, show_reset=True,
        )
    else:
        # Calcular opciones con valores previos de session_state antes de renderizar
        ss_anio = int(st.session_state.get("filter_anio") or default_year)
        ss_mes = str(st.session_state.get("filter_mes") or default_month)
        ss_month_num = MESES_OPCIONES.index(ss_mes) + 1 if ss_mes in MESES_OPCIONES else default_month_num
        _, prev_snapshot = prepare_filters(tracking_df, map_df, ss_anio, ss_month_num)
        procesos = sorted(prev_snapshot["Proceso_padre"].dropna().astype(str).unique().tolist())
        proceso_sel_cur = st.session_state.get("filter_proceso", "Todos")
        subproceso_options_base: list[str] = sorted(
            prev_snapshot[prev_snapshot["Proceso_padre"].astype(str) == proceso_sel_cur][
                "Subproceso_final"
            ].dropna().astype(str).unique().tolist()
        ) if proceso_sel_cur != "Todos" else []
        sels_all = render_filter_panel(
            filters=[
                {"key": "anio", "label": "Año", "type": "selectbox", "options": years, "default": default_year, "include_all": False},
                {"key": "mes", "label": "Mes", "type": "selectbox", "options": MESES_OPCIONES, "default": default_month, "include_all": False},
                {"key": "proceso", "label": "Proceso", "type": "selectbox", "options": procesos, "include_all": True},
                {"key": "subproceso", "label": "Subproceso", "type": "selectbox", "options": subproceso_options_base, "include_all": True},
            ],
            title="", key_prefix="filter", n_cols=4, show_reset=True,
        )
        anio = sels_all["anio"] or default_year
        mes = sels_all["mes"] or default_month
        selected_month_num = MESES_OPCIONES.index(mes) + 1 if mes in MESES_OPCIONES else default_month_num
        full_work_df, snapshot_df = prepare_filters(tracking_df, map_df, int(anio), selected_month_num)
    
    proceso_sel = sels_all["proceso"] or "Todos"
    subproceso_sel = sels_all["subproceso"] or "Todos"

    filtered = snapshot_df.copy()
    if proceso_sel != "Todos":
        filtered = filtered[filtered["Proceso_padre"].astype(str) == proceso_sel]
    if subproceso_sel != "Todos":
        filtered = filtered[filtered["Subproceso_final"].astype(str) == subproceso_sel]

    selected_process_label = proceso_sel if proceso_sel != "Todos" else "Todos los procesos"
    selected_subprocess_label = subproceso_sel if subproceso_sel != "Todos" else "Todos los subprocesos"

    latest = _latest_per_indicator(filtered) if not filtered.empty else filtered.copy()
    historic_base = full_work_df.copy()
    if proceso_sel != "Todos":
        historic_base = historic_base[historic_base["Proceso_padre"].astype(str) == proceso_sel]
    if subproceso_sel != "Todos":
        historic_base = historic_base[historic_base["Subproceso_final"].astype(str) == subproceso_sel]

    st.caption(
        f"Filtro activo: {selected_process_label} | Subproceso: {selected_subprocess_label} | Corte: {mes} {anio}"
    )

    tabs = st.tabs(TAB_NAMES)

    with tabs[0]:
        st.markdown("### Indicadores")
        if filtered.empty:
            st.info("No hay datos disponibles.")
        else:
            _render_indicadores_subproceso_enhanced(filtered, historic_base, int(anio), selected_month_num, map_df, proceso_sel)

    with tabs[1]:
        st.markdown("### Evolución")
        if filtered.empty:
            st.info("No hay datos disponibles.")
        else:
            indicador_options = sorted(latest["Indicador"].dropna().astype(str).unique().tolist())
            if not indicador_options:
                st.info("No hay indicadores disponibles para evolución.")
            else:
                selected_indicator = st.selectbox("Indicador para evolución", options=indicador_options, index=0)
                hist_df = _build_indicator_history(full_work_df, selected_indicator)
                if hist_df.empty:
                    st.info("No hay histórico disponible para el indicador seleccionado.")
                else:
                    st.plotly_chart(
                        grafico_historico_indicador(hist_df, titulo=f"Evolución de {selected_indicator}"),
                        use_container_width=True,
                    )
                    hist_table = tabla_historica_indicador(hist_df)
                    if hist_table.empty:
                        st.info("No hay registros históricos con cumplimiento calculado.")
                    else:
                        st.dataframe(hist_table, use_container_width=True)

    with tabs[2]:
        st.markdown("### Calidad")
        if filtered.empty:
            st.info("No hay datos disponibles.")
        else:
            _render_calidad_kpis_cards(filtered)

    with tabs[3]:
        st.markdown("### Auditoría")
        if filtered.empty:
            st.info("No hay datos disponibles.")
        else:
            _render_auditoria_tab(filtered)

    with tabs[4]:
        st.markdown("### Propuestas")
        prop_df, prop_err = load_propuestas(proceso_sel, subproceso_sel)
        if prop_err:
            st.warning(prop_err)
        else:
            render_propuestas(prop_df)

    with tabs[5]:
        st.markdown("### Análisis IA")
        if filtered.empty:
            st.info("No hay datos disponibles.")
        else:
            num_riesgos, num_alertas, num_saludables, riesgos, alertas = build_ia_indicators(filtered)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🔴 Riesgos", num_riesgos)
            with col2:
                st.metric("🟡 Alertas", num_alertas)
            with col3:
                st.metric("🟢 Saludables", num_saludables)
            
            st.markdown("#### Indicadores en Riesgo")
            if riesgos.empty:
                st.info("Sin indicadores en riesgo.")
            else:
                st.dataframe(riesgos, use_container_width=True)
            
            st.markdown("#### Indicadores en Alerta")
            if alertas.empty:
                st.info("Sin indicadores en alerta.")
            else:
                st.dataframe(alertas, use_container_width=True)
