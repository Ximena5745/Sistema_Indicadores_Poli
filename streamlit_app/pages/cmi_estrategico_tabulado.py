import streamlit as st
import pandas as pd
from datetime import date as _date

from services.cmi_filters import filter_df_for_cmi_estrategico
from services.strategic_indicators import (
    load_pdi_catalog,
    preparar_pdi_con_cierre,
    load_cierres,
)
from streamlit_app.utils.cmi_helpers import aplicar_filtros_globales

from streamlit_app.components.cmi_tabs import (
    render_tab_resumen,
    render_tab_listado,
    render_tab_alertas
)
from streamlit_app.components.cmi_tabs.tab_lineas import render_tab_lineas

CORTE_SEMESTRAL = {
    "Junio": 6,
    "Diciembre": 12,
}

def _default_anio(anios: list[int]) -> int:
    if 2025 in anios:
        return 2025
    if anios:
        return anios[-1]
    return _date.today().year

def _default_corte(anio: int | None) -> str:
    if anio is None:
        return "Diciembre"
    today = _date.today()
    if int(anio) < today.year:
        return "Diciembre"
    if today > _date(today.year, 7, 20):
        return "Junio"
    return "Diciembre"

def render():
    from streamlit_app.utils.cmi_styles import inject_cmi_premium_css
    inject_cmi_premium_css()
    
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

    # Filtros Globales
    with st.expander("🔎 Filtros Globales", expanded=False):
        if st.button("Limpiar filtros", key="cmi_pdi_clear_tab"):
            for k in ["cmi_tab_anio", "cmi_tab_corte", "cmi_tab_linea", "cmi_tab_objetivo", "cmi_tab_nombre"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

        _anio_default = _default_anio(anios)
        _fc1, _fc2 = st.columns(2)
        with _fc1:
            anio = st.selectbox("Año de corte", options=anios, index=anios.index(_anio_default) if _anio_default in anios else 0, key="cmi_tab_anio")
        with _fc2:
            _corte_default = _default_corte(int(anio) if anio is not None else None)
            corte = st.selectbox(
                "Corte semestral",
                list(CORTE_SEMESTRAL.keys()),
                index=list(CORTE_SEMESTRAL.keys()).index(_corte_default),
                key="cmi_tab_corte",
            )
        mes = CORTE_SEMESTRAL[corte]

        df = preparar_pdi_con_cierre(int(anio), int(mes))
        df = filter_df_for_cmi_estrategico(df, id_column="Id")

        if not df.empty:
            pdi_catalog = load_pdi_catalog()
            lineas = sorted(df["Linea"].dropna().astype(str).unique().tolist())
            
            _ff1, _ff2, _ff3 = st.columns([1, 2, 2])
            with _ff1:
                linea_sel = st.selectbox("Línea estratégica", ["Todas"] + lineas, key="cmi_tab_linea")
            
            df_obj = df if linea_sel == "Todas" else df[df["Linea"] == linea_sel]
            objetivos = sorted(df_obj["Objetivo"].dropna().astype(str).unique().tolist())
            
            with _ff2:
                objetivo_sel = st.selectbox("Objetivo estratégico", ["Todos"] + objetivos, key="cmi_tab_objetivo")
            with _ff3:
                nombre_q = st.text_input("Buscar indicador", key="cmi_tab_nombre", placeholder="Texto en nombre del indicador")
                
            df_filtrado = aplicar_filtros_globales(df, pdi_catalog, linea_sel, objetivo_sel, nombre_q)
        else:
            df_filtrado = pd.DataFrame()

    if df_filtrado.empty:
        st.warning("No hay indicadores para los filtros seleccionados.")
        return

    # Navegación principal controlable por estado
    tab_names = [
        "Resumen Desglosado", 
        "Líneas Estratégicas", 
        "Listado de Indicadores", 
        "Alertas"
    ]

    # Navegación desde CTA "Ver análisis detallado" de Vista rápida
    linea_target = st.query_params.get("cmi_linea")
    if linea_target:
        st.session_state["cmi_tab_linea_expand"] = str(linea_target)
        st.session_state["cmi_tab_panel"] = "Líneas Estratégicas"
        st.query_params.pop("cmi_linea", None)

    if "cmi_tab_panel" not in st.session_state or st.session_state["cmi_tab_panel"] not in tab_names:
        st.session_state["cmi_tab_panel"] = "Resumen Desglosado"

    selected_panel = st.segmented_control(
        "Sección",
        options=tab_names,
        key="cmi_tab_panel",
        label_visibility="collapsed",
    )

    if selected_panel == "Resumen Desglosado":
        render_tab_resumen(df_filtrado)
    elif selected_panel == "Líneas Estratégicas":
        render_tab_lineas(df_filtrado)
    elif selected_panel == "Listado de Indicadores":
        render_tab_listado(df_filtrado)
    elif selected_panel == "Alertas":
        render_tab_alertas(df_filtrado)
