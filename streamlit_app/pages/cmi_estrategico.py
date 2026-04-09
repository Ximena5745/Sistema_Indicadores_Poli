from datetime import date as _date
import unicodedata

import pandas as pd
import plotly.express as px
import streamlit as st

from streamlit_app.services.strategic_indicators import (
    NIVEL_COLOR_EXT,
    load_pdi_catalog,
    preparar_pdi_con_cierre,
    load_cierres,
)

CORTE_SEMESTRAL = {
    "Junio": 6,
    "Diciembre": 12,
}

LINEA_COLORS = {
    "Expansión": "#FBAF17",
    "Transformación organizacional": "#42F2F2",
    "Calidad": "#EC0677",
    "Experiencia": "#1FB2DE",
    "Sostenibilidad": "#A6CE38",
    "Educación para toda la vida": "#0F385A",
}


def _linea_color(linea: str) -> str:
    txt = str(linea or "").strip().lower()
    txt = unicodedata.normalize("NFD", txt)
    txt = "".join(ch for ch in txt if unicodedata.category(ch) != "Mn")
    if "expansi" in txt:
        return "#FBAF17"
    if "transform" in txt:
        return "#42F2F2"
    if "calidad" in txt:
        return "#EC0677"
    if "experien" in txt:
        return "#1FB2DE"
    if "sostenib" in txt:
        return "#A6CE38"
    if "educaci" in txt or "toda la vida" in txt:
        return "#0F385A"
    return "#1f4e79"


def _default_corte(anios: list[int]) -> tuple[int, str]:
    if 2025 in anios:
        return 2025, "Diciembre"
    if anios:
        return anios[-1], "Diciembre"
    return _date.today().year, "Diciembre"


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

        _anio_default, _corte_default = _default_corte(anios)
        _fc1, _fc2 = st.columns(2)
        with _fc1:
            anio = st.selectbox("Año de corte", anios, index=anios.index(_anio_default), key="cmi_pdi_anio")
        with _fc2:
            corte = st.selectbox(
                "Corte semestral",
                list(CORTE_SEMESTRAL.keys()),
                index=list(CORTE_SEMESTRAL.keys()).index(_corte_default),
                key="cmi_pdi_corte",
            )
        mes = CORTE_SEMESTRAL[corte]

    df = preparar_pdi_con_cierre(int(anio), int(mes))
    if df.empty:
        st.warning("No hay indicadores PDI (flag=1) para el corte seleccionado.")
        return

    pdi_catalog = load_pdi_catalog()
    lineas = sorted(
        pdi_catalog["Linea"].dropna().astype(str).unique().tolist()
        if not pdi_catalog.empty else df["Linea"].dropna().astype(str).unique().tolist()
    )
    _ff1, _ff2, _ff3 = st.columns([1, 2, 2])
    with _ff1:
        linea_sel = st.selectbox("Línea estratégica", ["Todas"] + lineas, key="cmi_pdi_linea")

    if not pdi_catalog.empty:
        obj_pool = pdi_catalog if linea_sel == "Todas" else pdi_catalog[pdi_catalog["Linea"] == linea_sel]
        objetivos = sorted(obj_pool["Objetivo"].dropna().astype(str).unique().tolist())
    else:
        df_obj = df if linea_sel == "Todas" else df[df["Linea"] == linea_sel]
        objetivos = sorted(df_obj["Objetivo"].dropna().astype(str).unique().tolist())

    with _ff2:
        objetivo_sel = st.selectbox("Objetivo estratégico", ["Todos"] + objetivos, key="cmi_pdi_objetivo")
    with _ff3:
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

    st.caption(f"Corte seleccionado: {corte} {anio}")

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
        by_linea["Linea"] = by_linea["Linea"].astype(str)
        _linea_map = {lin: _linea_color(lin) for lin in by_linea["Linea"].tolist()}
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
    st.markdown("### Indicadores PDI")
    _cols_pdi = ["Id", "Indicador", "Linea", "Objetivo", "cumplimiento_pct", "Nivel de cumplimiento"]
    if "Meta" in df.columns:
        _cols_pdi.append("Meta")
    if "Ejecucion" in df.columns:
        _cols_pdi.append("Ejecucion")
    if "Sentido" in df.columns:
        _cols_pdi.append("Sentido")
    _cols_pdi += ["Anio", "Mes", "Fecha"]
    tabla = df[[c for c in _cols_pdi if c in df.columns]].copy()
    tabla = tabla.rename(columns={
        "cumplimiento_pct": "Cumplimiento (%)",
        "Nivel de cumplimiento": "Nivel",
        "Anio": "Año cierre",
        "Mes": "Mes cierre",
        "Meta": "Meta",
        "Ejecucion": "Ejecución",
    })
    tabla["Cumplimiento (%)"] = pd.to_numeric(tabla["Cumplimiento (%)"], errors="coerce").round(1)
    if "Meta" in tabla.columns:
        tabla["Meta"] = pd.to_numeric(tabla["Meta"], errors="coerce").round(2)
    if "Ejecución" in tabla.columns:
        tabla["Ejecución"] = pd.to_numeric(tabla["Ejecución"], errors="coerce").round(2)
    tabla = tabla.sort_values(["Linea", "Objetivo", "Id"] if all(c in tabla.columns for c in ["Linea", "Objetivo"]) else ["Id"], na_position="last")

    # Color de fondo por Nivel en columna Nivel
    _NIVEL_BG_CMI = {
        "Peligro": "#FFCDD2", "Alerta": "#FEF3D0", "Cumplimiento": "#E8F5E9",
        "Sobrecumplimiento": "#D0E4FF", "No aplica": "#ECEFF1", "Pendiente de reporte": "#F5F5F5",
    }
    _NIVEL_ICONS_CMI = {
        "Peligro": "🔴", "Alerta": "🟡", "Cumplimiento": "🟢",
        "Sobrecumplimiento": "🔵", "No aplica": "⚫", "Pendiente de reporte": "⚪",
    }
    if "Nivel" in tabla.columns:
        tabla["Nivel"] = tabla["Nivel"].apply(
            lambda n: f'{_NIVEL_ICONS_CMI.get(str(n), "")} {n}' if pd.notna(n) else n
        )
    if "Linea" in tabla.columns:
        tabla["Color Línea"] = tabla["Linea"].apply(lambda l: _linea_color(str(l or "")))

    _cfg_pdi = {
        "Id":        st.column_config.TextColumn("ID",          width="small"),
        "Indicador": st.column_config.TextColumn("Indicador",   width="large"),
        "Linea":     st.column_config.TextColumn("Línea",       width="medium"),
        "Objetivo":  st.column_config.TextColumn("Objetivo",    width="large"),
        "Nivel":     st.column_config.TextColumn("Nivel",       width="medium"),
        "Cumplimiento (%)": st.column_config.NumberColumn("Cumplimiento %", format="%.1f", width="small"),
        "Meta":      st.column_config.NumberColumn("Meta",      format="%.2f", width="small"),
        "Ejecución": st.column_config.NumberColumn("Ejecución", format="%.2f", width="small"),
        "Sentido":   st.column_config.TextColumn("Sentido",     width="small"),
        "Año cierre": st.column_config.NumberColumn("Año",      format="%d",   width="small"),
        "Mes cierre": st.column_config.NumberColumn("Mes",      format="%d",   width="small"),
        "Fecha":     st.column_config.DatetimeColumn("Fecha",   width="small"),
    }
    st.dataframe(
        tabla,
        use_container_width=True,
        hide_index=True,
        column_config={k: v for k, v in _cfg_pdi.items() if k in tabla.columns},
    )
