"""Tablero Operativo page - Main page module."""

import pandas as pd
import streamlit as st

from streamlit_app.services.data_service import DataService
from streamlit_app.components.filter_panel import render_filter_panel
from streamlit_app.pages.tablero_operativo_config import (
    KANBAN_COLS,
    MESES,
    NIVEL_ICON_EXT,
    ORDEN_SEV,
)
from streamlit_app.pages.tablero_operativo_utils import (
    build_donut_chart,
    build_process_chart,
    detect_overdue_indicators,
    get_ventana,
    load_base,
    load_qc_artifacts,
    normalize_string,
    prepare_tracking_df,
)


def render() -> None:
    """Main render function for tablero operativo (operational dashboard).
    
    Displays:
    - Filter panel (year, month, process)
    - Summary metrics (total indicators, compliance %)
    - Visualizations: donut chart (levels), bar chart (process compliance)
    - Quality artifacts
    - Kanban board of indicators by compliance level
    - Overdue and at-risk indicators
    """
    st.title("Tablero Operativo")
    st.caption("Dashboard de seguimiento de indicadores con detección de vencidos y alertas.")

    ds = DataService()
    df = load_base()
    map_df = ds.get_process_map()

    if df.empty:
        st.warning("No hay datos de seguimiento disponibles.")
        return
    if map_df.empty:
        st.warning("No se encontró el mapeo de procesos.")
        return

    # Get available years
    anios = sorted(
        pd.to_numeric(df["Anio"], errors="coerce").dropna().astype(int).unique().tolist()
    )
    if not anios:
        st.error("No hay años disponibles.")
        return

    anio_default = 2025 if 2025 in anios else (anios[-1] if anios else None)
    
    # Filter panel
    sels = render_filter_panel(
        filters=[
            {
                "key": "anio",
                "label": "Año",
                "type": "selectbox",
                "options": anios,
                "default": anio_default,
                "include_all": False,
            },
            {
                "key": "mes",
                "label": "Mes de corte",
                "type": "selectbox",
                "options": MESES,
                "default": "Diciembre",
                "include_all": False,
            },
        ],
        title="Filtros del tablero",
        key_prefix="tablero",
        n_cols=2,
        show_reset=True,
    )

    anio = sels.get("anio") or anio_default
    mes_sel = sels.get("mes") or "Diciembre"
    mes_num = MESES.index(mes_sel) + 1 if mes_sel in MESES else 12

    # Prepare data
    df_prep = prepare_tracking_df(df, map_df, mes_num, int(anio))

    if df_prep.empty:
        st.info("No hay datos para los filtros seleccionados.")
        return

    # Summary metrics
    total = len(df_prep)
    con_dato = int(df_prep["Cumplimiento_pct"].notna().sum())
    prom = float(df_prep["Cumplimiento_pct"].mean()) if con_dato else 0.0

    k1, k2, k3 = st.columns(3)
    k1.metric("Indicadores", total)
    k2.metric("Con cumplimiento", con_dato)
    k3.metric("Promedio cumplimiento", f"{prom:.1f}%")

    st.caption(f"Corte: {mes_sel} {anio}")

    # Visualizations
    col1, col2 = st.columns([1, 1])

    with col1:
        fig_donut = build_donut_chart(df_prep)
        st.plotly_chart(fig_donut, use_container_width=True)

    with col2:
        fig_proceso = build_process_chart(df_prep)
        st.plotly_chart(fig_proceso, use_container_width=True)

    # Quality artifacts
    st.markdown("### Artefactos de Calidad")
    artifacts = load_qc_artifacts()
    if artifacts:
        for art in artifacts[:3]:  # Show first 3
            with st.expander(f"📊 {art['file']}"):
                st.json(art["data"])
    else:
        st.info("No hay artefactos de calidad disponibles.")

    # Overdue detection
    st.markdown("### Indicadores Vencidos y Alertas")
    overdue_df = detect_overdue_indicators(df_prep, mes_num, int(anio))
    
    vencidos = overdue_df[overdue_df["Status"] == "Vencido"]
    alertas = overdue_df[overdue_df["Status"] == "Alerta"]
    
    c1, c2 = st.columns(2)
    with c1:
        st.metric("🔴 Vencidos", len(vencidos))
        if not vencidos.empty:
            st.dataframe(vencidos[["Id", "DaysOverdue"]], use_container_width=True, hide_index=True)
    
    with c2:
        st.metric("🟡 Alertas", len(alertas))
        if not alertas.empty:
            st.dataframe(alertas[["Id", "DaysOverdue"]], use_container_width=True, hide_index=True)

    # Kanban board
    st.markdown("### Kanban: Indicadores por Nivel")
    
    kanban_data = {}
    for nivel in KANBAN_COLS:
        kanban_data[nivel] = df_prep[df_prep["Nivel de cumplimiento"] == nivel]

    cols = st.columns(len(KANBAN_COLS))
    for col, nivel in zip(cols, KANBAN_COLS):
        with col:
            count = len(kanban_data[nivel])
            icon = NIVEL_ICON_EXT.get(nivel, "•")
            st.subheader(f"{icon} {nivel}")
            st.metric("Cantidad", count)
            
            # Show top 3 indicators
            if count > 0:
                top_inds = kanban_data[nivel]["Indicador"].head(3).tolist()
                for ind in top_inds:
                    st.caption(f"• {ind[:30]}...")

    # Full indicators table
    st.markdown("### Tabla de Indicadores")
    
    table_cols = ["Id", "Indicador", "Proceso_padre", "Cumplimiento_pct", "Nivel de cumplimiento"]
    table_df = df_prep[[c for c in table_cols if c in df_prep.columns]].copy()
    table_df = table_df.rename(columns={
        "Cumplimiento_pct": "Cumplimiento (%)",
        "Nivel de cumplimiento": "Nivel",
        "Proceso_padre": "Proceso",
    })
    
    st.dataframe(table_df, use_container_width=True, hide_index=True)
