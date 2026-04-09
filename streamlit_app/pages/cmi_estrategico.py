from datetime import date as _date

import pandas as pd
import plotly.express as px
import streamlit as st

from streamlit_app.services.strategic_indicators import (
    NIVEL_COLOR_EXT,
    load_pdi_catalog,
    preparar_pdi_con_cierre,
    load_cierres,
)

MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


def _default_mes_por_anio(anio: int) -> int:
    hoy = _date.today()
    if anio < hoy.year:
        return 12
    if anio == hoy.year:
        return max(1, hoy.month - 1)
    return 1


def render():
    st.title("CMI Estratégico")
    st.caption("Indicadores del Plan Estratégico (PDI) con cumplimiento de cierre y niveles institucionales.")

    cierres = load_cierres()
    if cierres.empty:
        st.error("No se encontró información de cierres en Resultados Consolidados.xlsx.")
        return

    anios = sorted(pd.to_numeric(cierres["Anio"], errors="coerce").dropna().astype(int).unique().tolist())
    if not anios:
        st.error("No hay años disponibles en consolidado de cierres.")
        return

    with st.expander("🔎 Filtros", expanded=False):
        if st.button("Limpiar filtros", key="cmi_pdi_clear"):
            for k in [
                "cmi_pdi_anio", "cmi_pdi_mes", "cmi_pdi_linea", "cmi_pdi_objetivo", "cmi_pdi_nombre",
                "_cmi_pdi_last_anio",
            ]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

        anio = st.selectbox("Año de corte", anios, index=len(anios) - 1, key="cmi_pdi_anio")
        if st.session_state.get("_cmi_pdi_last_anio") != anio:
            if "cmi_pdi_mes" in st.session_state:
                del st.session_state["cmi_pdi_mes"]
            st.session_state["_cmi_pdi_last_anio"] = anio

        _meses_disponibles = sorted(
            pd.to_numeric(cierres.loc[pd.to_numeric(cierres["Anio"], errors="coerce") == anio, "Mes"], errors="coerce")
            .dropna().astype(int).unique().tolist()
        )
        if not _meses_disponibles:
            _meses_disponibles = list(range(1, 13))

        _mes_default = _default_mes_por_anio(int(anio))
        if _mes_default not in _meses_disponibles:
            _mes_default = _meses_disponibles[-1]

        mes = st.selectbox(
            "Mes de corte",
            _meses_disponibles,
            index=_meses_disponibles.index(_mes_default),
            key="cmi_pdi_mes",
            format_func=lambda m: MESES_ES.get(int(m), str(m)),
        )

    df = preparar_pdi_con_cierre(int(anio), int(mes))
    if df.empty:
        st.warning("No hay indicadores PDI (flag=1) para el corte seleccionado.")
        return

    pdi_catalog = load_pdi_catalog()
    lineas = sorted(
        pdi_catalog["Linea"].dropna().astype(str).unique().tolist()
        if not pdi_catalog.empty else df["Linea"].dropna().astype(str).unique().tolist()
    )
    linea_sel = st.selectbox("Línea estratégica", ["Todas"] + lineas, key="cmi_pdi_linea")

    if not pdi_catalog.empty:
        obj_pool = pdi_catalog if linea_sel == "Todas" else pdi_catalog[pdi_catalog["Linea"] == linea_sel]
        objetivos = sorted(obj_pool["Objetivo"].dropna().astype(str).unique().tolist())
    else:
        df_obj = df if linea_sel == "Todas" else df[df["Linea"] == linea_sel]
        objetivos = sorted(df_obj["Objetivo"].dropna().astype(str).unique().tolist())

    objetivo_sel = st.selectbox("Objetivo estratégico", ["Todos"] + objetivos, key="cmi_pdi_objetivo")
    nombre_q = st.text_input("Buscar indicador", key="cmi_pdi_nombre", placeholder="Texto en nombre del indicador")

    if linea_sel != "Todas":
        df = df[df["Linea"] == linea_sel]
    if objetivo_sel != "Todos":
        df = df[df["Objetivo"] == objetivo_sel]
    if nombre_q.strip():
        df = df[df["Indicador"].astype(str).str.contains(nombre_q.strip(), case=False, na=False)]

    if df.empty:
        st.info("No hay registros para los filtros seleccionados.")
        return

    activos = []
    if linea_sel != "Todas":
        activos.append(f"Línea: {linea_sel}")
    if objetivo_sel != "Todos":
        activos.append(f"Objetivo: {objetivo_sel}")
    if nombre_q.strip():
        activos.append(f"Indicador contiene: {nombre_q.strip()}")
    if activos:
        st.caption("Filtros activos: " + " · ".join(activos))

    total = len(df)
    con_dato = int(df["cumplimiento_pct"].notna().sum())
    promedio = float(df["cumplimiento_pct"].mean()) if con_dato else 0.0
    top_nivel = df["Nivel de cumplimiento"].value_counts().idxmax() if total else "Sin dato"
    n_lineas_vis = int(df["Linea"].nunique())
    n_obj_vis = int(df["Objetivo"].nunique())
    n_lineas_cat = int(pdi_catalog["Linea"].nunique()) if not pdi_catalog.empty else n_lineas_vis
    n_obj_cat = int(pdi_catalog["Objetivo"].nunique()) if not pdi_catalog.empty else n_obj_vis

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Indicadores PDI", total)
    k2.metric("Con cumplimiento", con_dato)
    k3.metric("Promedio cumplimiento", f"{promedio:.1f}%")
    k4.metric("Nivel predominante", top_nivel)

    st.caption(
        f"Catálogo PDI: {n_lineas_cat} líneas y {n_obj_cat} objetivos. "
        f"Con indicadores Plan Estratégico=1 en corte: {n_lineas_vis} líneas y {n_obj_vis} objetivos."
    )

    c1, c2 = st.columns([1, 1])
    with c1:
        by_linea = (
            df.groupby("Linea", dropna=False)["cumplimiento_pct"]
            .mean().fillna(0).reset_index().sort_values("cumplimiento_pct", ascending=True)
        )
        fig_linea = px.bar(
            by_linea,
            x="cumplimiento_pct",
            y="Linea",
            orientation="h",
            title="Cumplimiento promedio por línea estratégica",
            labels={"cumplimiento_pct": "Cumplimiento (%)", "Linea": "Línea"},
            color_discrete_sequence=["#1f4e79"],
        )
        fig_linea.update_layout(margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig_linea, use_container_width=True, key="cmi_pdi_linea_bar")

    with c2:
        niveles = df["Nivel de cumplimiento"].fillna("Pendiente de reporte").value_counts().reset_index()
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

    st.markdown("### Indicadores PDI")
    tabla = df[[
        "Id", "Indicador", "Linea", "Objetivo", "cumplimiento_pct", "Nivel de cumplimiento", "Anio", "Mes", "Fecha",
    ]].copy()
    tabla = tabla.rename(columns={
        "cumplimiento_pct": "Cumplimiento (%)",
        "Nivel de cumplimiento": "Nivel",
        "Anio": "Año cierre",
        "Mes": "Mes cierre",
    })
    tabla["Cumplimiento (%)"] = pd.to_numeric(tabla["Cumplimiento (%)"], errors="coerce").round(1)
    st.dataframe(tabla.sort_values(["Linea", "Objetivo", "Id"], na_position="last"), use_container_width=True, hide_index=True)
