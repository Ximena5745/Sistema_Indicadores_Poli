"""CMI Estratégico page - Main page module."""

import pandas as pd
import plotly.express as px
import streamlit as st

from services.cmi_filters import filter_df_for_cmi_estrategico
from services.strategic_indicators import (
    NIVEL_COLOR_EXT,
    load_pdi_catalog,
    preparar_pdi_con_cierre,
    load_cierres,
)
from streamlit_app.components.filter_panel import render_filter_panel
from streamlit_app.pages.cmi_estrategico_config import (
    CORTE_SEMESTRAL,
    NEON_BLUE_STYLE,
    get_default_anio,
    get_default_corte,
)
from streamlit_app.pages.cmi_estrategico_utils import (
    apply_cmi_filters,
    build_metrics_summary,
    get_pdi_lines_and_objectives,
    get_sin_gestion_df,
    linea_color,
)

# Re-exports for backward compatibility
_get_sin_gestion_df = get_sin_gestion_df
_default_anio = get_default_anio
_default_corte = get_default_corte


def render():
    """Main render function for the CMI Estratégico page.
    
    Displays:
    - Filter panel (year/semester, line, objective, name search)
    - Summary metrics (total indicators, compliance, predominant level)
    - Visualizations: line bar chart, level pie chart
    - Indicators without management (Plan anual=3)
    - PDI indicators table with metadata
    """
    st.title("CMI Estratégico")
    st.caption(
        "Indicadores del Plan Estratégico (PDI) con cumplimiento de cierre y niveles institucionales."
    )
    
    # Query param support for line filtering
    if hasattr(st, 'query_params') and "linea" in st.query_params:
        linea_from_query = st.query_params["linea"]
        st.session_state["cmi_pdi_linea"] = linea_from_query
        st.rerun()

    # Apply neon blue style
    st.markdown(NEON_BLUE_STYLE, unsafe_allow_html=True)

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

    _anio_default = get_default_anio(anios)
    _corte_default = get_default_corte(_anio_default)

    _c1, _c_btn = st.columns([5, 1])
    with _c1:
        sels_gral = render_filter_panel(
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
            title="Filtros generales",
            key_prefix="cmi_pdi",
            n_cols=2,
        )
    with _c_btn:
        st.markdown("<div style='margin-top:26px'>", unsafe_allow_html=True)
        if st.button("Limpiar", key="cmi_pdi_clear", use_container_width=True):
            for k in ["cmi_pdi_anio", "cmi_pdi_corte", "cmi_pdi_linea",
                      "cmi_pdi_objetivo", "cmi_pdi_nombre"]:
                st.session_state.pop(k, None)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    anio = sels_gral["anio"] or _anio_default
    corte = sels_gral["corte"] or _corte_default
    mes = CORTE_SEMESTRAL[corte]

    df = preparar_pdi_con_cierre(int(anio), int(mes))
    df = filter_df_for_cmi_estrategico(df, id_column="Id")

    if df.empty:
        st.warning("No hay indicadores de CMI Estratégico para el corte seleccionado.")
        return

    pdi_catalog = load_pdi_catalog()
    
    # Get lines and objectives
    linea_sel = st.session_state.get("cmi_pdi_linea", "Todas")
    lineas, objetivos = get_pdi_lines_and_objectives(pdi_catalog, df, linea_sel)

    sels_extra = render_filter_panel(
        filters=[
            {
                "key": "linea", "label": "Línea estratégica",
                "type": "selectbox",
                "options": lineas, "include_all": True, "all_label": "Todas",
            },
            {
                "key": "objetivo", "label": "Objetivo estratégico",
                "type": "selectbox",
                "options": objetivos, "include_all": True,
            },
            {
                "key": "nombre", "label": "Buscar indicador",
                "type": "text",
                "placeholder": "Texto en nombre del indicador",
            },
        ],
        title="Filtros adicionales",
        key_prefix="cmi_pdi",
        n_cols=3,
    )
    
    linea_sel = sels_extra["linea"] or "Todas"
    objetivo_sel = sels_extra["objetivo"] or "Todos"
    nombre_q = sels_extra.get("nombre") or ""

    df, activos = apply_cmi_filters(df, linea_sel, objetivo_sel, nombre_q)

    if df.empty:
        st.info("No hay registros para los filtros seleccionados.")
        return

    if activos:
        st.caption("Filtros activos: " + " · ".join(activos))

    # Summary metrics
    metrics = build_metrics_summary(df, pdi_catalog)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Indicadores PDI", metrics["total"])
    k2.metric("Con cumplimiento", metrics["con_dato"])
    k3.metric("Promedio cumplimiento", f"{metrics['promedio']:.1f}%")
    k4.metric("Nivel predominante", metrics["top_nivel"])

    st.caption(f"Corte seleccionado: {corte} {anio}")
    st.caption(
        f"Catálogo PDI: {metrics['n_lineas_cat']} líneas y {metrics['n_obj_cat']} objetivos. "
        f"Con indicadores Plan Estratégico=1 en corte: {metrics['n_lineas_vis']} líneas y {metrics['n_obj_vis']} objetivos."
    )

    # Visualizations
    c1, c2 = st.columns([1, 1])
    
    with c1:
        by_linea = (
            df.groupby("Linea", dropna=False)["cumplimiento_pct"]
            .mean()
            .fillna(0)
            .reset_index()
            .sort_values("cumplimiento_pct", ascending=True)
        )
        by_linea["Linea"] = by_linea["Linea"].astype(str)
        _linea_map = {lin: linea_color(lin) for lin in by_linea["Linea"].tolist()}
        fig_linea = px.bar(
            by_linea,
            x="cumplimiento_pct",
            y="Linea",
            orientation="h",
            title="Cumplimiento promedio por línea estratégica",
            labels={"cumplimiento_pct": "Cumplimiento (%)", "Linea": "Línea"},
            color="Linea",
            color_discrete_map=_linea_map,
        )
        fig_linea.update_layout(margin=dict(l=10, r=10, t=50, b=10), showlegend=False)
        st.plotly_chart(fig_linea, use_container_width=True, key="cmi_pdi_linea_bar")

    with c2:
        niveles = (
            df["Nivel de cumplimiento"].fillna("Pendiente de reporte").value_counts().reset_index()
        )
        niveles.columns = ["Nivel", "Cantidad"]
        fig_niv = px.pie(
            niveles,
            names="Nivel",
            values="Cantidad",
            title="Distribución por nivel",
            color="Nivel",
            color_discrete_map=NIVEL_COLOR_EXT,
            hole=0.45,
        )
        fig_niv.update_layout(margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig_niv, use_container_width=True, key="cmi_pdi_nivel_pie")

    # Indicators without management
    sin_gestion_df = get_sin_gestion_df()
    if not sin_gestion_df.empty:
        st.markdown(
            "<div style='margin-top:2rem;'><b>Indicadores sin gestión (Plan anual = 3)</b></div>",
            unsafe_allow_html=True,
        )
        st.dataframe(sin_gestion_df, hide_index=True, use_container_width=True)

    # PDI Indicators table
    st.markdown("### Indicadores PDI")
    
    from streamlit_app.utils.formatting import formatear_meta_ejecucion_df
    from html import escape

    _cols_pdi = [
        "Id",
        "Indicador",
        "Linea",
        "Objetivo",
        "cumplimiento_pct",
        "Nivel de cumplimiento",
        "Meta",
        "Ejecucion",
        "Sentido",
        "Anio",
        "Mes",
        "Fecha",
    ]
    tabla = df[[c for c in _cols_pdi if c in df.columns]].copy()
    tabla = tabla.rename(
        columns={
            "cumplimiento_pct": "Cumplimiento (%)",
            "Nivel de cumplimiento": "Nivel",
            "Anio": "Año cierre",
            "Mes": "Mes cierre",
            "Meta": "Meta",
            "Ejecucion": "Ejecución",
        }
    )
    tabla["Cumplimiento (%)"] = pd.to_numeric(tabla["Cumplimiento (%)"], errors="coerce").round(1)
    tabla = formatear_meta_ejecucion_df(tabla, meta_col="Meta", ejec_col="Ejecución")
    tabla = tabla.sort_values(
        (
            ["Linea", "Objetivo", "Id"]
            if all(c in tabla.columns for c in ["Linea", "Objetivo"])
            else ["Id"]
        ),
        na_position="last",
    )

    _cfg_pdi = {
        "Id": st.column_config.TextColumn("ID", width="small"),
        "Indicador": st.column_config.TextColumn("Indicador", width="large"),
        "Linea": st.column_config.TextColumn("Línea", width="medium"),
        "Objetivo": st.column_config.TextColumn("Objetivo", width="large"),
        "Nivel": st.column_config.TextColumn("Nivel", width="medium"),
        "Cumplimiento (%)": st.column_config.NumberColumn(
            "Cumplimiento %", format="%.1f", width="small"
        ),
        "Meta": st.column_config.TextColumn("Meta", width="small"),
        "Ejecución": st.column_config.TextColumn("Ejecución", width="small"),
    }

    st.dataframe(
        tabla,
        use_container_width=True,
        hide_index=True,
        column_config={k: v for k, v in _cfg_pdi.items() if k in tabla.columns},
    )
