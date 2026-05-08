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
from services.cmi_filters import filter_df_for_procesos

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


def _render_informe_por_procesos_styles() -> None:
    st.markdown(
        """
        <style>
        .dashboard-filter-panel, .informe-filter-panel {
            background: #F8FAFC;
            border: 1px solid #CBD5E1;
            border-left: 4px solid #1D4ED8;
            border-radius: 18px;
            padding: 16px;
            margin-bottom: 20px;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
        }
        .dashboard-filter-title, .informe-filter-title {
            font-size: 0.85rem;
            font-weight: 700;
            color: #1E3A8A;
            margin-bottom: 14px;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }
        .dashboard-filter-label, .informe-filter-label {
            font-size: 0.72rem;
            font-weight: 700;
            color: #475569;
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .dashboard-filter-panel .stSelectbox > div,
        .informe-filter-panel .stSelectbox > div {
            background: #ffffff !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 12px !important;
            min-height: 42px !important;
            padding: 0.12rem 0.35rem !important;
        }
        .dashboard-filter-panel .stSelectbox label,
        .informe-filter-panel .stSelectbox label {
            display: none !important;
        }
        .dashboard-filter-panel .stSelectbox .css-1n76uvr,
        .dashboard-filter-panel .stSelectbox .css-1siy2j7,
        .informe-filter-panel .stSelectbox .css-1n76uvr,
        .informe-filter-panel .stSelectbox .css-1siy2j7 {
            margin-bottom: 0 !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #eef4ff;
            padding: 8px;
            border-radius: 14px;
            box-shadow: inset 0 1px 4px rgba(37, 99, 235, 0.08);
        }
        .stTabs [data-baseweb="tab"] {
            padding: 0.8rem 1.2rem;
            border-radius: 999px !important;
            font-weight: 600;
            color: #1e3a8a;
            transition: all 0.2s ease;
            border: 1px solid transparent !important;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #1d4ed8, #60a5fa) !important;
            color: white !important;
            box-shadow: 0 8px 18px rgba(29, 78, 169, 0.16);
        }
        .stTabs [data-baseweb="tab"]:not([aria-selected="true"]) {
            background: rgba(255,255,255,0.96) !important;
            border: 1px solid rgba(37, 99, 235, 0.13) !important;
        }
        .stButton > button {
            border-radius: 999px;
            min-height: 44px;
            font-weight: 600;
            padding: 0.75rem 1rem;
        }
        .informe-button-row .stButton > button {
            width: 100%;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


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

    source_style = {
        "Retos": {"bg": "#e8f5e9", "border": "#66bb6a", "title": "#1b5e20"},
        "Proyectos": {"bg": "#e3f2fd", "border": "#42a5f5", "title": "#0d47a1"},
        "Plan de mejoramiento": {"bg": "#fff3e0", "border": "#ffb74d", "title": "#e65100"},
        "Calidad": {"bg": "#f3e5f5", "border": "#ba68c8", "title": "#4a148c"},
    }
    source_order = ["Retos", "Proyectos", "Plan de mejoramiento", "Calidad"]

    procesos = sorted(df["Proceso"].dropna().astype(str).unique().tolist())
    if not procesos:
        st.info("No hay procesos definidos en los indicadores propuestos.")
        return

    proc_tabs = st.tabs(procesos)
    for tab, proceso in zip(proc_tabs, procesos):
        with tab:
            proc_df = df[df["Proceso"].astype(str) == proceso].copy()
            subps = sorted(proc_df["Subproceso"].dropna().astype(str).unique().tolist())
            if not subps:
                st.info("Sin subprocesos con propuestas para este proceso.")
                continue

            sub_tabs = st.tabs(subps)
            for sub_tab, sp in zip(sub_tabs, subps):
                with sub_tab:
                    sp_df_all = proc_df[proc_df["Subproceso"].astype(str) == sp].copy()
                    col_blocks = st.columns(4)
                    for i, fuente in enumerate(source_order):
                        with col_blocks[i]:
                            style = source_style[fuente]
                            st.markdown(
                                f"<div style='font-weight:700;color:{style['title']};margin-bottom:8px;border-left:4px solid {style['border']};padding-left:8px;'>{fuente}</div>",
                                unsafe_allow_html=True,
                            )
                            src_df = sp_df_all[sp_df_all["Fuente"].astype(str) == fuente].copy()
                            if src_df.empty:
                                st.caption("Sin propuestas")
                                continue

                            for _, r in src_df.iterrows():
                                ind = str(r.get("Indicador Propuesto", "")).strip()
                                if not ind:
                                    continue
                                fac = str(r.get("Factor", "")).strip()
                                car = str(r.get("Característica", "")).strip()
                                extra = ""
                                if fuente == "Plan de mejoramiento":
                                    tags = []
                                    if fac and fac.lower() != "nan":
                                        tags.append(f"Factor: {fac}")
                                    if car and car.lower() != "nan":
                                        tags.append(f"Característica: {car}")
                                    extra = (
                                        "<div style='font-size:0.74rem;color:#5d4037;margin-top:6px;line-height:1.2;'>"
                                        + " | ".join(tags)
                                        + "</div>"
                                        if tags
                                        else ""
                                    )
                                st.markdown(
                                    f"""
                                    <div style='background:{style['bg']};border:1px solid {style['border']};border-radius:10px;padding:10px 10px;margin-bottom:8px;'>
                                        <div style='font-size:0.88rem;color:#263238;line-height:1.25;font-weight:600;'>{ind}</div>
                                        {extra}
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )


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
    full_work_df = filter_df_for_procesos(
        full_work_df,
        id_column="Id",
        map_df=map_df,
    )

    snapshot_df = _prepare_tracking(tracking_df, map_df, month_num=month_num)
    snapshot_df = filter_df_for_procesos(
        snapshot_df,
        id_column="Id",
        year=int(anio),
        map_df=map_df,
    )
    if "Anio" in snapshot_df.columns:
        snapshot_df = snapshot_df[pd.to_numeric(snapshot_df["Anio"], errors="coerce") == int(anio)]

    return full_work_df, snapshot_df


def render() -> None:
    st.title("Informe por Procesos")
    _render_informe_por_procesos_styles()

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

    st.markdown("""
        <div class='dashboard-filter-panel'>
            <div class='dashboard-filter-title'>Filtros oficiales</div>
            <div class='dashboard-filter-row'>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3, col4 = st.columns([1, 1, 2, 2], gap="small")
    topbar_year = st.session_state.get("topbar_year")
    topbar_month = st.session_state.get("topbar_month")
    with col1:
        st.markdown("<div class='dashboard-filter-item'>", unsafe_allow_html=True)
        st.markdown("<div class='dashboard-filter-label'>Año</div>", unsafe_allow_html=True)
        if topbar_year is not None:
            anio = int(topbar_year)
            st.markdown(f"**{anio}**")
        else:
            anio = st.selectbox(
                "Año",
                options=years,
                index=default_year_idx if years else None,
                key="filter_anio",
                label_visibility="collapsed",
            )
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='dashboard-filter-item'>", unsafe_allow_html=True)
        st.markdown("<div class='dashboard-filter-label'>Mes</div>", unsafe_allow_html=True)
        if topbar_month is not None:
            mes = str(topbar_month)
            st.markdown(f"**{mes}**")
        else:
            mes = st.selectbox(
                "Mes",
                options=MESES_OPCIONES,
                index=MESES_OPCIONES.index(default_month),
                key="filter_mes",
                label_visibility="collapsed",
            )
        st.markdown("</div>", unsafe_allow_html=True)

    selected_month_num = MESES_OPCIONES.index(mes) + 1 if mes in MESES_OPCIONES else default_month_num
    full_work_df, snapshot_df = _prepare_filters(tracking_df, map_df, int(anio), selected_month_num)

    with col3:
        st.markdown("<div class='dashboard-filter-item'>", unsafe_allow_html=True)
        st.markdown("<div class='dashboard-filter-label'>Proceso</div>", unsafe_allow_html=True)
        procesos = sorted(snapshot_df["Proceso_padre"].dropna().astype(str).unique().tolist())
        proceso_sel = st.selectbox(
            "Proceso (Filtro Padre)",
            options=["Todos"] + procesos,
            index=0,
            key="filter_proceso",
            label_visibility="collapsed",
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div class='dashboard-filter-item'>", unsafe_allow_html=True)
        st.markdown("<div class='dashboard-filter-label'>Subproceso</div>", unsafe_allow_html=True)
        subproceso_options = ["Todos"]
        if proceso_sel != "Todos":
            subprocesos = sorted(
                snapshot_df[snapshot_df["Proceso_padre"].astype(str) == proceso_sel]["Subproceso_final"].dropna().astype(str).unique().tolist()
            )
            if subprocesos:
                subproceso_options += subprocesos
        subproceso_sel = st.selectbox(
            "Subproceso",
            options=subproceso_options,
            index=0,
            key="filter_subproceso",
            label_visibility="collapsed",
        )
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

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

    with tabs[2]:
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

    with tabs[3]:
        st.markdown("### Auditoría")
        _render_auditoria_tab(selected_process_label)

    with tabs[4]:
        st.markdown("### Propuestas")
        propuestas_df, propuestas_msg = _load_propuestas(proceso_sel, subproceso_sel)
        if propuestas_msg:
            st.warning(propuestas_msg)
        else:
            _render_propuestas(propuestas_df)

    with tabs[5]:
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
