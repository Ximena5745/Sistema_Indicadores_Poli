"""
CMI Estratégico tabbed interface for strategic indicators (PDI).

Refactored PHASE 2 WEEK 4: Extracted config and utility functions.
"""

import streamlit as st
import pandas as pd

from services.strategic_indicators import load_cierres, load_pdi_catalog
from streamlit_app.components.cmi_tabs import (
    render_tab_resumen,
    render_tab_listado,
    render_tab_alertas
)
from streamlit_app.components.cmi_tabs.tab_lineas import render_tab_lineas

# Import refactored utilities
from .cmi_estrategico_config import CORTE_SEMESTRAL, TAB_NAMES
from .cmi_estrategico_utils import default_anio, default_corte, prepare_cmi_data


def render():
    """Main render function for CMI Estratégico page."""
    from streamlit_app.utils.cmi_styles import inject_cmi_premium_css
    inject_cmi_premium_css()

    # Padding exclusivo para CMI Estratégico
    pad_left, content_col, pad_right = st.columns([0.035, 0.93, 0.035])
    with content_col:
        st.title("CMI Estratégico")
        st.caption("Indicadores del Plan Estratégico (PDI) interactivo y detallado.")

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

        from streamlit_app.components.filter_panel import render_filter_panel

        _anio_default = default_anio(anios)
        _corte_default = default_corte(_anio_default)

        sels = render_filter_panel(
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
            key_prefix="cmi_tab",
            n_cols=2,
            show_reset=True,
            reset_keys=["cmi_tab_anio", "cmi_tab_corte"],
        )
        anio = sels["anio"] or _anio_default
        corte = sels["corte"] or _corte_default
        mes = CORTE_SEMESTRAL[corte]

        # Prepare data
        df_filtrado, pdi_catalog = prepare_cmi_data(int(anio), int(mes))

        if df_filtrado.empty:
            st.warning("No hay indicadores para los filtros seleccionados.")
            return

        # Navigation handling
        linea_target = st.query_params.get("cmi_linea")
        if linea_target:
            if isinstance(linea_target, list):
                linea_target = linea_target[0]
            linea_target = str(linea_target).strip()
            if linea_target and st.session_state.get("_cmi_linea_processed") != linea_target:
                st.session_state["cmi_tab_linea_expand"] = linea_target
                st.session_state["cmi_tab_panel"] = "Líneas Estratégicas"
                st.session_state["_cmi_linea_processed"] = linea_target

        if "cmi_tab_panel" not in st.session_state or st.session_state["cmi_tab_panel"] not in TAB_NAMES:
            st.session_state["cmi_tab_panel"] = "Resumen Desglosado"

        selected_panel = st.segmented_control(
            "Sección",
            options=TAB_NAMES,
            key="cmi_tab_panel",
            label_visibility="collapsed",
        )

        # Render selected tab
        if selected_panel == "Resumen Desglosado":
            render_tab_resumen(df_filtrado)
        elif selected_panel == "Líneas Estratégicas":
            render_tab_lineas(df_filtrado, pdi_catalog=pdi_catalog)
        elif selected_panel == "Listado de Indicadores":
            render_tab_listado(df_filtrado)
        elif selected_panel == "Alertas":
            render_tab_alertas(df_filtrado)
