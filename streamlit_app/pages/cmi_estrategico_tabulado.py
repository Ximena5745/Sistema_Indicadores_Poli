import streamlit as st
import pandas as pd
from datetime import date as _date

from services.cmi_filters import filter_df_for_cmi_estrategico
from services.strategic_indicators import (
    load_pdi_catalog,
    preparar_pdi_con_cierre,
    load_cierres,
)
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

    # Padding exclusivo para CMI Estratégico via layout (sin tocar otras páginas).
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

        pdi_catalog = pd.DataFrame()

        # Filtros Globales — solo Año y Corte Semestral
        with st.expander("🔎 Filtros Globales", expanded=False):
            if st.button("Limpiar filtros", key="cmi_pdi_clear_tab"):
                for k in ["cmi_tab_anio", "cmi_tab_corte"]:
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

        if df.empty:
            st.warning("No hay indicadores para los filtros seleccionados.")
            return

        pdi_catalog = load_pdi_catalog(include_ids=True)
        df_filtrado = df

        # Enriquecer df_filtrado con metadatos de Ficha_Tecnica.xlsx (join por Id).
        # Aporta: Descripcion, Responsable del calculo, Fuente V1, Formula, Frecuencia.
        # Fuente única de verdad — no duplica lógica de cálculo.
        try:
            from services.data_loader import cargar_ficha_tecnica as _cft
            _ft = _cft()
            if not _ft.empty and "Id" in _ft.columns:
                # La columna de descripción puede venir con encoding roto (Latin-1 mal leído).
                # Se detecta dinámicamente buscando la columna que contiene "descripci" (case-insensitive).
                _desc_col = next(
                    (c for c in _ft.columns if "descripci" in c.lower()),
                    None,
                )
                _wanted = [
                    c for c in [
                        _desc_col,
                        "Responsable del calculo",
                        "Fuente V1",
                        "Formula",
                        "Frecuencia",
                    ]
                    if c and c in _ft.columns
                ]
                _ft_sub = _ft[["Id"] + _wanted].drop_duplicates(subset="Id", keep="first").copy()
                if _desc_col and _desc_col in _ft_sub.columns:
                    _ft_sub = _ft_sub.rename(columns={_desc_col: "Descripcion"})
                # Normalizar ambas claves a string antes del join para evitar mismatch int↔str.
                df_filtrado = df_filtrado.copy()
                df_filtrado["Id"] = df_filtrado["Id"].astype(str)
                _ft_sub["Id"] = _ft_sub["Id"].astype(str)
                df_filtrado = df_filtrado.merge(_ft_sub, on="Id", how="left")
        except Exception:
            pass  # Si falla el join, la ficha renderiza con los campos disponibles

        # Navegación principal controlable por estado
        tab_names = [
            "Resumen Desglosado",
            "Líneas Estratégicas",
            "Listado de Indicadores",
            "Alertas"
        ]

        # Navegación desde CTA "Ver análisis detallado" de Vista rápida.
        # Evita rerun por mutar query_params; se procesa una vez por valor.
        linea_target = st.query_params.get("cmi_linea")
        if linea_target:
            if isinstance(linea_target, list):
                linea_target = linea_target[0]
            linea_target = str(linea_target).strip()
            if linea_target and st.session_state.get("_cmi_linea_processed") != linea_target:
                st.session_state["cmi_tab_linea_expand"] = linea_target
                st.session_state["cmi_tab_panel"] = "Líneas Estratégicas"
                st.session_state["_cmi_linea_processed"] = linea_target

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
            render_tab_lineas(df_filtrado, pdi_catalog=pdi_catalog)
        elif selected_panel == "Listado de Indicadores":
            render_tab_listado(df_filtrado)
        elif selected_panel == "Alertas":
            render_tab_alertas(df_filtrado)
