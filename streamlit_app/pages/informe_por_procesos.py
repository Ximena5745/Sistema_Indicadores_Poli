from pathlib import Path

import pandas as pd
import streamlit as st
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from components.charts import grafico_historico_indicador, tabla_historica_indicador
from streamlit_app.services.data_service import DataService
from streamlit_app.pages.resumen_por_proceso import (
    _mes_to_num,
    _get_prev_month_for_year,
    _build_indicator_history,
    _default_month_num,
    _latest_per_indicator,
    _load_calidad_data,
    _norm_text,
    _prepare_tracking,
    _render_auditoria_tab,
    _render_calidad_kpis_cards,
    _render_indicadores_subproceso_cards,
    _to_float,
)
from services.cmi_filters import filter_df_for_cmi_procesos

MESES_OPCIONES = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]


def _load_propuestas(proceso_actual: str = "Todos", subproceso_actual: str = "Todos") -> tuple[pd.DataFrame, str | None]:
    excel_path = (
        Path(__file__).parents[2]
        / "data"
        / "raw"
        / "Propuesta Indicadores"
        / "Indicadores Propuestos.xlsx"
    )
    if not excel_path.exists():
        return pd.DataFrame(), f"No existe el archivo: {excel_path}"

    try:
        retos = pd.read_excel(excel_path, sheet_name="Retos")
        retos_filtrados = retos[retos["Aplica Desempeño"].astype(str).str.upper() == "SI"][
            ["Proceso", "Subproceso", "Indicador Propuesto"]
        ]
        retos_filtrados = retos_filtrados.dropna(subset=["Indicador Propuesto"])
        retos_filtrados["Fuente"] = "Retos"

        proyectos = pd.read_excel(excel_path, sheet_name="Proyectos")
        proyectos_filtrados = proyectos[proyectos["Propuesta"].astype(str).str.upper() == "SI"][
            ["Proceso", "Subproceso", "Nombre del Indicador Propuesto"]
        ]
        proyectos_filtrados = proyectos_filtrados.rename(columns={"Nombre del Indicador Propuesto": "Indicador Propuesto"})
        proyectos_filtrados = proyectos_filtrados.dropna(subset=["Indicador Propuesto"])
        proyectos_filtrados["Fuente"] = "Proyectos"

        plan = pd.read_excel(excel_path, sheet_name="Plan de mejoramiento", header=1)
        plan_filtrados = plan[plan["Propuesta Indicador"].astype(str).str.upper() == "SI"][
            ["Proceso", "Subproceso", "INDICADOR DE RESULTADO O IMPACTO"]
        ]
        plan_filtrados = plan_filtrados.rename(columns={"INDICADOR DE RESULTADO O IMPACTO": "Indicador Propuesto"})
        plan_filtrados = plan_filtrados.dropna(subset=["Indicador Propuesto"])
        plan_filtrados["Fuente"] = "Plan de mejoramiento"

        calidad = pd.read_excel(excel_path, sheet_name="Calidad")
        calidad_filtrados = calidad[["Proceso", "Subroceso", "Propuesta SGC (Indicadores)"]].rename(
            columns={"Subroceso": "Subproceso", "Propuesta SGC (Indicadores)": "Indicador Propuesto"}
        )
        calidad_filtrados = calidad_filtrados.dropna(subset=["Indicador Propuesto"])
        calidad_filtrados["Fuente"] = "Calidad"

        df_final = pd.concat(
            [retos_filtrados, proyectos_filtrados, plan_filtrados, calidad_filtrados],
            ignore_index=True,
        )
        df_final = df_final.drop_duplicates(subset=["Proceso", "Subproceso", "Indicador Propuesto", "Fuente"])

        if proceso_actual != "Todos":
            proceso_norm = _norm_text(proceso_actual)
            df_final = df_final[df_final["Proceso"].astype(str).map(_norm_text) == proceso_norm]
        if subproceso_actual != "Todos":
            sub_norm = _norm_text(subproceso_actual)
            df_final = df_final[df_final["Subproceso"].astype(str).map(_norm_text) == sub_norm]

        return df_final, None
    except Exception as exc:
        return pd.DataFrame(), f"Error leyendo indicadores propuestos: {exc}"


def _render_propuestas(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No hay indicadores propuestos para el filtro seleccionado.")
        return

    st.dataframe(df.sort_values(["Fuente", "Proceso", "Subproceso"], ascending=[True, True, True]).head(100), use_container_width=True)


def _build_summary_by_unit(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    summary = (
        df.groupby(["Proceso_padre", "Subproceso_final"], dropna=False)
        .agg(
            indicadores=("Indicador", "nunique"),
            cumplimiento=("Cumplimiento_pct", "mean"),
        )
        .reset_index()
    )
    summary["cumplimiento"] = pd.to_numeric(summary["cumplimiento"], errors="coerce").round(1)
    return summary


def _build_frequency_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    summary = (
        df.groupby(["Periodicidad", "Mes"], dropna=False)
        .agg(indicadores=("Indicador", "nunique"), cumplimiento=("Cumplimiento_pct", "mean"))
        .reset_index()
    )
    summary["cumplimiento"] = pd.to_numeric(summary["cumplimiento"], errors="coerce").round(1)
    return summary


def _build_classification_summary(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in ["Clasificacion", "Tipo de proceso"] if c in df.columns]
    if not cols:
        return pd.DataFrame()
    summary = (
        df.groupby(cols, dropna=False)
        .agg(indicadores=("Indicador", "nunique"), cumplimiento=("Cumplimiento_pct", "mean"))
        .reset_index()
    )
    summary["cumplimiento"] = pd.to_numeric(summary["cumplimiento"], errors="coerce").round(1)
    return summary


def _build_consolidated_columns(df: pd.DataFrame) -> list[str]:
    columns = [
        c
        for c in [
            "Proceso",
            "Subproceso",
            "Subproceso_final",
            "Indicador",
            "Clasificacion",
            "Periodicidad",
            "Mes",
            "Cumplimiento_pct",
            "Meta",
            "Ejecucion",
            "Tipo de proceso",
        ]
        if c in df.columns
    ]
    return columns


def _build_ia_indicators(df: pd.DataFrame) -> tuple[int, int, int, pd.DataFrame, pd.DataFrame]:
    if df.empty or "Cumplimiento_pct" not in df.columns:
        return 0, 0, 0, pd.DataFrame(), pd.DataFrame()
    cumple = pd.to_numeric(df["Cumplimiento_pct"], errors="coerce")
    riesgos = df[cumple < 80].copy()
    alertas = df[(cumple >= 80) & (cumple < 100)].copy()
    saludables = df[cumple >= 100].copy()
    riesgos = riesgos.sort_values("Cumplimiento_pct").head(10)
    alertas = alertas.sort_values("Cumplimiento_pct").head(10)
    return len(riesgos), len(alertas), len(saludables), riesgos, alertas


def _prepare_filters(tracking_df: pd.DataFrame, map_df: pd.DataFrame, anio: int, month_num: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    full_work_df = _prepare_tracking(tracking_df, map_df, month_num=None)
    full_work_df = filter_df_for_cmi_procesos(full_work_df, id_column="Id")

    snapshot_df = _prepare_tracking(tracking_df, map_df, month_num=month_num)
    snapshot_df = filter_df_for_cmi_procesos(snapshot_df, id_column="Id")
    if "Anio" in snapshot_df.columns:
        snapshot_df = snapshot_df[pd.to_numeric(snapshot_df["Anio"], errors="coerce") == int(anio)]

    return full_work_df, snapshot_df


def render() -> None:
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
    default_year_idx = years.index(default_year) if default_year in years else 0
    default_month_num = _get_prev_month_for_year(tracking_df, default_year) or 12
    default_month = MESES_OPCIONES[default_month_num - 1]

    st.markdown("#### Filtros")
    c1, c2, c3 = st.columns(3)
    with c1:
        anio = st.selectbox("Año", options=years, index=default_year_idx if years else None)
    with c2:
        mes = st.selectbox("Mes", options=MESES_OPCIONES, index=MESES_OPCIONES.index(default_month))
    with c3:
        st.caption("Corte: selecciona año y mes para actualizar el informe.")

    selected_month_num = MESES_OPCIONES.index(mes) + 1 if mes in MESES_OPCIONES else default_month_num
    full_work_df, snapshot_df = _prepare_filters(tracking_df, map_df, int(anio), selected_month_num)

    procesos = sorted(snapshot_df["Proceso_padre"].dropna().astype(str).unique().tolist())
    proceso_sel = st.selectbox("Proceso (Filtro Padre)", options=["Todos"] + procesos, index=0)

    filtered = snapshot_df.copy()
    if proceso_sel != "Todos":
        filtered = filtered[filtered["Proceso_padre"].astype(str) == proceso_sel]

    subproceso_sel = "Todos"
    if proceso_sel != "Todos":
        subprocesos = sorted(filtered["Subproceso_final"].dropna().astype(str).unique().tolist())
        if subprocesos:
            subproceso_sel = st.selectbox("Subproceso", options=["Todos"] + subprocesos, index=0)
            if subproceso_sel != "Todos":
                filtered = filtered[filtered["Subproceso_final"].astype(str) == subproceso_sel]

    selected_process_label = proceso_sel if proceso_sel != "Todos" else "Todos los procesos"
    selected_subprocess_label = subproceso_sel if subproceso_sel != "Todos" else "Todos los subprocesos"

    latest = _latest_per_indicator(filtered) if not filtered.empty else filtered.copy()
    historic_base = full_work_df.copy()
    if not historic_base.empty and "Anio" in historic_base.columns:
        historic_base = historic_base[pd.to_numeric(historic_base["Anio"], errors="coerce") == int(anio)]
    if proceso_sel != "Todos":
        historic_base = historic_base[historic_base["Proceso_padre"].astype(str) == proceso_sel]
    if subproceso_sel != "Todos":
        historic_base = historic_base[historic_base["Subproceso_final"].astype(str) == subproceso_sel]

    st.caption(
        f"Filtro activo: {selected_process_label} | Subproceso: {selected_subprocess_label} | Corte: {mes} {anio}"
    )

    tabs = st.tabs(
        [
            "Indicadores",
            "Evolución",
            "Calidad",
            "Auditoría",
            "Propuestas",
            "Análisis IA",
        ]
    )

    with tabs[0]:
        st.markdown("### Indicadores")
        if filtered.empty:
            st.info("No hay datos disponibles.")
        else:
            _render_indicadores_subproceso_cards(filtered, historic_base, int(anio), selected_month_num, map_df, proceso_sel)

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
                        st.markdown("#### Detalle histórico")
                        st.dataframe(hist_table, use_container_width=True, hide_index=True)

    with tabs[6]:
        st.markdown("### Calidad")
        calidad_df, calidad_msg = _load_calidad_data()
        if calidad_msg:
            st.warning(calidad_msg)
        elif calidad_df.empty:
            st.info("No hay datos de calidad disponibles.")
        else:
            if proceso_sel != "Todos":
                proc_norm = _norm_text(proceso_sel)
                calidad_df["_proc_norm"] = calidad_df["Proceso"].astype(str).map(_norm_text)
                calidad_df = calidad_df[calidad_df["_proc_norm"] == proc_norm].drop(columns=["_proc_norm"], errors="ignore")
            if subproceso_sel != "Todos" and "Subproceso" in calidad_df.columns:
                sub_norm = _norm_text(subproceso_sel)
                calidad_df = calidad_df[calidad_df["Subproceso"].astype(str).map(_norm_text) == sub_norm]
            if calidad_df.empty:
                st.info("Sin datos de calidad para el filtro seleccionado.")
            else:
                _render_calidad_kpis_cards(calidad_df)
                st.dataframe(calidad_df.head(100), use_container_width=True)

    with tabs[7]:
        st.markdown("### Auditoría")
        _render_auditoria_tab(selected_process_label)

    with tabs[8]:
        st.markdown("### Propuestas")
        propuestas_df, propuestas_msg = _load_propuestas(proceso_sel, subproceso_sel)
        if propuestas_msg:
            st.warning(propuestas_msg)
        else:
            _render_propuestas(propuestas_df)

    with tabs[9]:
        st.markdown("### Análisis IA")
        if filtered.empty:
            st.info("No hay datos disponibles.")
        else:
            riesgos, alertas, saludables, df_riesgos, df_alertas = _build_ia_indicators(filtered)
            st.markdown(
                f"- Indicadores en peligro: **{riesgos}**\n"
                f"- Indicadores en alerta: **{alertas}**\n"
                f"- Indicadores saludables: **{saludables}**"
            )
            if not df_riesgos.empty:
                st.markdown("#### Riesgos principales")
                st.dataframe(df_riesgos[[c for c in ["Indicador", "Proceso", "Subproceso_final", "Cumplimiento_pct"] if c in df_riesgos.columns]].head(20), use_container_width=True)
            if not df_alertas.empty:
                st.markdown("#### Alertas principales")
                st.dataframe(df_alertas[[c for c in ["Indicador", "Proceso", "Subproceso_final", "Cumplimiento_pct"] if c in df_alertas.columns]].head(20), use_container_width=True)
