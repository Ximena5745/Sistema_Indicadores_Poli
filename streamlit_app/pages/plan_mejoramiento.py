"""Plan de Mejoramiento page - Main page module."""

import pandas as pd
import plotly.express as px
import streamlit as st

from services.data_loader import cargar_acciones_mejora
from services.strategic_indicators import (
    NIVEL_COLOR_EXT,
    load_cna_catalog,
    preparar_cna_con_cierre,
    load_cierres,
)
from streamlit_app.components.filter_panel import render_filter_panel
from streamlit_app.pages.plan_mejoramiento_config import (
    CORTE_SEMESTRAL,
    get_default_corte,
)
from streamlit_app.pages.plan_mejoramiento_utils import (
    apply_cna_filters,
    build_cna_table,
    build_factor_characteristics_tree,
    build_improvement_actions_kpis,
    build_metrics_summary,
    get_cna_characteristics,
    get_cna_factor_options,
    get_factor_color_map,
)

# Re-exports for backward compatibility with tests
_default_corte = get_default_corte


def render():
    """Main render function for the plan de mejoramiento page.
    
    Displays:
    - Filter panel (year/semester, factor, characteristic, name search)
    - Summary metrics (total indicators, factors, characteristics, compliance)
    - Visualizations: factor bar chart, level pie chart, factor/level stacked bar, factor/char treemap
    - CNA indicators table with metadata
    - Improvement actions KPIs and data linked to CNA indicators
    """
    st.title("Plan de Mejoramiento")
    st.caption(
        "Indicadores CNA con filtros dependientes por Factor y Característica + cumplimiento de cierre."
    )

    cierres = load_cierres()
    if cierres.empty:
        st.error("No se encontró información de cierres en Resultados Consolidados.xlsx.")
        return

    anios = sorted(
        pd.to_numeric(cierres["Anio"], errors="coerce").dropna().astype(int).unique().tolist()
    )
    if not anios:
        st.error("No hay años disponibles en consolidado de cierres.")
        return

    _anio_default, _corte_default = get_default_corte(anios)

    sels_corte = render_filter_panel(
        filters=[
            {
                "key": "anio", "label": "Año de corte",
                "type": "segmented_control",
                "options": anios, "default": _anio_default, "include_all": False,
            },
            {
                "key": "corte", "label": "Corte semestral",
                "type": "segmented_control",
                "options": list(CORTE_SEMESTRAL.keys()),
                "default": _corte_default, "include_all": False,
            },
        ],
        title="Filtros",
        key_prefix="pm_cna",
        n_cols=2,
        show_reset=True,
        reset_keys=["pm_cna_anio", "pm_cna_corte", "pm_cna_factor",
                    "pm_cna_caracteristica", "pm_cna_nombre", "_pm_cna_last_anio"],
    )
    anio = sels_corte["anio"] or _anio_default
    corte = sels_corte["corte"] or _corte_default

    mes = CORTE_SEMESTRAL[corte]
    df = preparar_cna_con_cierre(int(anio), int(mes))
    if df.empty:
        st.warning("No hay indicadores CNA (flag=1) para el corte seleccionado.")
        return

    cna_catalog = load_cna_catalog()
    factores = get_cna_factor_options(cna_catalog, df)

    # Panel de filtros CNA — factor primero, luego cargar caracts dinámicamente
    factor_sel = st.session_state.get("pm_cna_factor", "Todos")
    caracts = get_cna_characteristics(cna_catalog, df, factor_sel)

    sels_cna = render_filter_panel(
        filters=[
            {
                "key": "factor", "label": "Factor CNA",
                "type": "selectbox",
                "options": factores, "include_all": True,
            },
            {
                "key": "caracteristica", "label": "Característica",
                "type": "selectbox",
                "options": caracts, "include_all": True, "all_label": "Todas",
            },
            {
                "key": "nombre", "label": "Buscar indicador",
                "type": "text",
                "placeholder": "Texto en nombre del indicador",
            },
        ],
        title="Filtros CNA",
        key_prefix="pm_cna",
        n_cols=3,
    )
    factor_sel = sels_cna["factor"] or "Todos"
    car_sel = sels_cna["caracteristica"] or "Todas"
    nombre_q = sels_cna.get("nombre") or ""

    df, activos = apply_cna_filters(df, factor_sel, car_sel, nombre_q)

    if df.empty:
        st.info("No hay registros para los filtros seleccionados.")
        return

    if activos:
        st.caption("Filtros activos: " + " · ".join(activos))
    st.caption(f"Corte seleccionado: {corte} {anio}")

    # Summary metrics
    metrics = build_metrics_summary(df, cna_catalog)
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Indicadores CNA", metrics["total"])
    k2.metric("Factores visibles", metrics["n_fact"])
    k3.metric("Características visibles", metrics["n_car"])
    k4.metric("Con cumplimiento", metrics["con_dato"])
    k5.metric("Promedio cumplimiento", f"{metrics['prom']:.1f}%")

    st.caption(
        f"Catálogo CNA: {metrics['total_fact_catalogo']} factores y {metrics['total_car_catalogo']} características. "
        f"Con indicadores CNA=1 en corte: {metrics['n_fact']} factores y {metrics['n_car']} características."
    )

    factor_color_map = get_factor_color_map(df)

    # Visualizations row 1: Factor bar chart & Level pie chart
    r1c1, r1c2 = st.columns([1, 1])
    
    with r1c1:
        by_factor = (
            df.groupby("Factor", dropna=False)["cumplimiento_pct"]
            .mean()
            .fillna(0)
            .reset_index()
            .sort_values("cumplimiento_pct", ascending=True)
        )
        fig_factor = px.bar(
            by_factor,
            x="cumplimiento_pct",
            y="Factor",
            orientation="h",
            title="Cumplimiento promedio por factor",
            labels={"cumplimiento_pct": "Cumplimiento (%)", "Factor": "Factor"},
            color="Factor",
            color_discrete_map=factor_color_map,
        )
        fig_factor.update_layout(margin=dict(l=10, r=10, t=50, b=10), showlegend=False)
        try:
            from components.renderers import render_echarts
            st.plotly_chart(fig_factor, use_container_width=True, key="pm_factor_avg")
        except Exception:
            st.plotly_chart(fig_factor, use_container_width=True, key="pm_factor_avg")

    with r1c2:
        niveles = (
            df["Nivel de cumplimiento"].fillna("Pendiente de reporte").value_counts().reset_index()
        )
        niveles.columns = ["Nivel", "Cantidad"]
        fig_niv = px.pie(
            niveles,
            names="Nivel",
            values="Cantidad",
            title="Distribución de niveles",
            color="Nivel",
            color_discrete_map=NIVEL_COLOR_EXT,
            hole=0.45,
        )
        st.plotly_chart(fig_niv, use_container_width=True, key="pm_niveles_pie")

    # Visualizations row 2: Stacked bar & Treemap
    st.markdown("### Gráficas adicionales")
    r2c1, r2c2 = st.columns([1, 1])
    
    with r2c1:
        df_stack = (
            df.groupby(["Factor", "Nivel de cumplimiento"], dropna=False)
            .size()
            .reset_index(name="Cantidad")
        )
        fig_stack = px.bar(
            df_stack,
            x="Factor",
            y="Cantidad",
            color="Nivel de cumplimiento",
            title="Indicadores por factor y nivel",
            barmode="stack",
            color_discrete_map=NIVEL_COLOR_EXT,
        )
        st.plotly_chart(fig_stack, use_container_width=True, key="pm_factor_nivel_stack")

    with r2c2:
        df_tree = build_factor_characteristics_tree(df, factor_color_map)
        if df_tree.empty:
            st.info("No hay datos válidos para el treemap de factor/característica.")
        else:
            fig_tree = px.treemap(
                df_tree,
                path=["Factor", "Caracteristica"],
                values="Cantidad",
                title="Mapa de indicadores por factor y característica",
                color="Factor",
                color_discrete_map=factor_color_map,
            )
            fig_tree.update_layout(margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig_tree, use_container_width=True, key="pm_factor_car_tree")

    # CNA Indicators table
    st.markdown("### Indicadores CNA")
    tabla, column_config = build_cna_table(df)
    st.dataframe(
        tabla,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
    )

    # Improvement actions section
    st.markdown("---")
    st.markdown("### 📋 Acciones de Mejora asociadas")
    st.caption(
        "Acciones registradas en acciones_mejora.xlsx cuyo ID coincide con indicadores CNA visibles."
    )

    df_acc = cargar_acciones_mejora()
    if df_acc.empty:
        st.info("No hay datos de acciones de mejora disponibles.")
    else:
        # Find ID column in actions
        id_col_acc = None
        for cand in ("ID_INDICADOR", "Id", "ID", "INDICADOR_ID", "id_indicador"):
            if cand in df_acc.columns:
                id_col_acc = cand
                break

        if id_col_acc is None:
            st.info("No se encontró columna de ID de indicador en acciones_mejora.xlsx.")
        else:
            ids_cna = set(df["Id"].astype(str).str.strip().unique())
            acc_kpis = build_improvement_actions_kpis(df_acc, id_col_acc, ids_cna)

            if acc_kpis["total"] == 0:
                st.info(
                    "No se encontraron acciones vinculadas a los indicadores CNA del corte actual."
                )
            else:
                ak1, ak2, ak3, ak4 = st.columns(4)
                ak1.metric("Total acciones", acc_kpis["total"])
                ak2.metric("Cerradas", acc_kpis["cerradas"])
                ak3.metric("Abiertas", acc_kpis["abiertas"])
                ak4.metric(
                    "Avance promedio", f"{acc_kpis['avance_prom']:.1f}%" if acc_kpis['avance_prom'] is not None else "—"
                )

                if acc_kpis["vencidas"] is not None:
                    st.caption(f"Acciones vencidas: **{acc_kpis['vencidas']}**")

                # Chart: Average progress by status
                df_acc_cna = acc_kpis["df_cna"]
                estado_col = acc_kpis["estado_col"]
                if estado_col and "AVANCE" in df_acc_cna.columns:
                    _acc_g = df_acc_cna.groupby(estado_col)["AVANCE"].mean().reset_index()
                    _acc_g.columns = ["Estado", "Avance promedio (%)"]
                    _acc_g["Avance promedio (%)"] = _acc_g["Avance promedio (%)"].round(1)
                    fig_acc = px.bar(
                        _acc_g,
                        x="Estado",
                        y="Avance promedio (%)",
                        title="Avance promedio por estado de acción",
                        color="Estado",
                        text_auto=True,
                    )
                    st.plotly_chart(fig_acc, use_container_width=True)

                # Actions table
                _col_acc = ["Id", "Descripcion", "Estado", "Avance", "Responsable", "Fecha_Finalizacion"]
                _acc_table = df_acc_cna[
                    [c for c in _col_acc if c in df_acc_cna.columns]
                ].copy()
                _acc_table = _acc_table.rename(
                    columns={
                        "Descripcion": "Descripción",
                        "Fecha_Finalizacion": "Fecha de cierre",
                    }
                )
                st.dataframe(_acc_table, use_container_width=True, hide_index=True)
