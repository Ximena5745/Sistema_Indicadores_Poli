from pathlib import Path

import pandas as pd
import streamlit as st
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from streamlit_app.components.charts import grafico_historico_indicador, tabla_historica_indicador
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
    _render_resumen_banner,
    _render_resumen_overview_cards,
    _to_float,
)
from services.cmi_filters.filters import filter_df_for_procesos

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


def _month_value_to_num(value: object) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if text.isdigit():
        num = int(text)
        return num if 1 <= num <= 12 else None
    return _mes_to_num(text)


def _build_executive_summary(filtered: pd.DataFrame, base_df: pd.DataFrame | None) -> dict[str, object]:
    pct = pd.to_numeric(filtered.get("Cumplimiento_pct", pd.Series(dtype=float)), errors="coerce")
    avg = float(pct.mean()) if not pct.dropna().empty else 0.0
    score = min(100.0, avg)
    total_indicadores = int(filtered["Indicador"].dropna().astype(str).str.strip().nunique()) if "Indicador" in filtered.columns else 0
    total_procesos = int(filtered["Proceso_padre"].dropna().astype(str).str.strip().nunique()) if "Proceso_padre" in filtered.columns else 0
    total_subprocesos = int(filtered["Subproceso_final"].dropna().astype(str).str.strip().nunique()) if "Subproceso_final" in filtered.columns else 0
    cumple = int((pct >= 100).sum())
    alerta = int(((pct >= 80) & (pct < 100)).sum())
    peligro = int((pct < 80).sum())
    sin_dato = int(pct.isna().sum())
    delta = None
    if base_df is not None and not base_df.empty:
        base_pct = pd.to_numeric(base_df.get("Cumplimiento_pct", pd.Series(dtype=float)), errors="coerce")
        if not base_pct.dropna().empty:
            delta = float(avg - float(base_pct.mean()))
    return {
        "avg": avg,
        "score": score,
        "label": "Saludable" if score >= 95 else "Estable" if score >= 80 else "En riesgo",
        "total_indicadores": total_indicadores,
        "total_procesos": total_procesos,
        "total_subprocesos": total_subprocesos,
        "cumple": cumple,
        "alerta": alerta,
        "peligro": peligro,
        "sin_dato": sin_dato,
        "delta": delta,
    }


def _format_delta(delta: float | None) -> str:
    if delta is None:
        return "Sin cambio"
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:.1f}% respecto al año anterior"


def _render_executive_cards(summary: dict[str, object]) -> None:
    delta_label = _format_delta(summary["delta"])
    st.markdown(
        f"""
        <div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin:0 0 18px;'>
            <div style='padding:20px;border-radius:20px;background:#ffffff;border:1px solid rgba(15,23,42,0.08);box-shadow:0 18px 40px rgba(15,23,42,0.06);'>
                <div style='font-size:0.75rem;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;'>Score de Salud</div>
                <div style='font-size:2.8rem;font-weight:800;color:#0f172a;'>{summary["score"]:.1f}</div>
                <div style='font-size:0.85rem;color:#15803d;font-weight:700;margin-top:10px;'>{summary["label"]}</div>
                <div style='font-size:0.78rem;color:#64748b;margin-top:10px;'>{delta_label}</div>
            </div>
            <div style='padding:20px;border-radius:20px;background:#ffffff;border:1px solid rgba(15,23,42,0.08);box-shadow:0 18px 40px rgba(15,23,42,0.06);'>
                <div style='font-size:0.75rem;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;'>Cumplimiento Global</div>
                <div style='font-size:2.8rem;font-weight:800;color:#0f172a;'>{summary["avg"]:.1f}%</div>
                <div style='font-size:0.85rem;color:#64748b;margin-top:10px;'>Meta: 100%</div>
            </div>
            <div style='padding:20px;border-radius:20px;background:#ffffff;border:1px solid rgba(15,23,42,0.08);box-shadow:0 18px 40px rgba(15,23,42,0.06);'>
                <div style='font-size:0.75rem;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;'>Indicadores evaluados</div>
                <div style='font-size:2.8rem;font-weight:800;color:#0f172a;'>{summary["total_indicadores"]}</div>
                <div style='font-size:0.85rem;color:#64748b;margin-top:10px;'>{summary["total_indicadores"]} activos en el periodo</div>
            </div>
            <div style='padding:20px;border-radius:20px;background:#ffffff;border:1px solid rgba(15,23,42,0.08);box-shadow:0 18px 40px rgba(15,23,42,0.06);'>
                <div style='font-size:0.75rem;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;'>Estado de alertas</div>
                <div style='font-size:2.8rem;font-weight:800;color:#0f172a;'>{summary["alerta"] + summary["peligro"]}</div>
                <div style='font-size:0.85rem;color:#64748b;margin-top:10px;'>{summary["alerta"]} alertas · {summary["peligro"]} críticos</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_year_comparison(historic_base: pd.DataFrame, selected_month_num: int) -> None:
    if historic_base.empty or "Anio" not in historic_base.columns:
        return

    df = historic_base.copy()
    if "Mes" in df.columns:
        df["Mes_num"] = df["Mes"].map(lambda x: _month_value_to_num(x))
        df = df[df["Mes_num"] == selected_month_num]

    df["Anio"] = pd.to_numeric(df["Anio"], errors="coerce")
    df = df.dropna(subset=["Anio"])
    if df.empty:
        return

    summary = (
        df.groupby(df["Anio"].astype(int), dropna=False)["Cumplimiento_pct"]
        .agg(lambda s: pd.to_numeric(s, errors="coerce").mean())
        .reset_index(name="promedio")
        .sort_values("Anio")
    )
    if summary.empty:
        return

    rows = []
    for _, row in summary.tail(4).iterrows():
        ano = int(row["Anio"])
        prom = float(row["promedio"]) if pd.notna(row["promedio"]) else 0.0
        rows.append((ano, prom))

    cards_html = ""
    for ano, prom in rows:
        cards_html += f"""
            <div style='padding:18px;border-radius:18px;background:#ffffff;border:1px solid rgba(15,23,42,0.08);box-shadow:0 10px 24px rgba(15,23,42,0.06);'>
                <div style='font-size:0.85rem;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;'>Año {ano}</div>
                <div style='font-size:2.4rem;font-weight:800;color:#0f172a;'>{prom:.1f}%</div>
                <div style='font-size:0.82rem;color:#64748b;margin-top:10px;'>Cumplimiento promedio</div>
            </div>
        """
    st.markdown(
        f"""
        <div style='margin:22px 0 12px;font-size:1rem;font-weight:700;color:#0f172a;'>Evolución comparativa interanual</div>
        <div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin-bottom:22px;'>{cards_html}</div>
        """,
        unsafe_allow_html=True,
    )

    figure = go.Figure(
        data=[
            go.Bar(
                x=[ano for ano, _ in rows],
                y=[prom for _, prom in rows],
                marker_color="#2563eb",
                text=[f"{prom:.1f}%" for _, prom in rows],
                textposition="outside",
                hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
            )
        ]
    )
    figure.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,250,252,0.8)",
        xaxis=dict(showgrid=False, tickfont=dict(size=12, color="#0f172a")),
        yaxis=dict(showgrid=True, gridcolor="rgba(15,23,42,0.08)", tickfont=dict(size=12, color="#0f172a"), ticksuffix="%"),
    )
    st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})


def _render_critical_indicators(filtered: pd.DataFrame) -> None:
    if filtered.empty:
        return
    pct_col = "Cumplimiento_pct" if "Cumplimiento_pct" in filtered.columns else (
        "cumplimiento_pct" if "cumplimiento_pct" in filtered.columns else None
    )
    if pct_col is None:
        return
    work = filtered.copy()
    work[pct_col] = pd.to_numeric(work[pct_col], errors="coerce")
    work = work.dropna(subset=[pct_col])
    if work.empty:
        return
    critical = work[work[pct_col] < 80].copy()
    if critical.empty:
        st.success("No hay indicadores críticos en este corte.")
        return
    critical = critical.sort_values(pct_col).head(3)
    items = ""
    for _, row in critical.iterrows():
        indicador = str(row.get("Indicador", "Sin nombre"))
        proceso = str(row.get("Proceso_padre", "Sin proceso"))
        valor = float(row[pct_col])
        items += f"<div style='margin-bottom:12px;padding:16px;border-radius:18px;background:#fff7ed;border:1px solid #fcd9b6;'>"
        items += f"<div style='font-weight:700;color:#b45309;margin-bottom:6px;'>{indicador}</div>"
        items += f"<div style='font-size:0.88rem;color:#475569;margin-bottom:4px;'>Proceso: {proceso}</div>"
        items += f"<div style='font-size:1rem;font-weight:700;color:#991b1b;'>Cumplimiento: {valor:.1f}%</div>"
        items += "</div>"
    st.markdown(
        f"""
        <div style='margin-top:20px;'>
            <div style='font-size:1rem;font-weight:700;color:#0f172a;margin-bottom:12px;'>Indicadores críticos</div>
            {items}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_distribution_cards(filtered: pd.DataFrame) -> None:
    pct_col = "Cumplimiento_pct" if "Cumplimiento_pct" in filtered.columns else (
        "cumplimiento_pct" if "cumplimiento_pct" in filtered.columns else None
    )
    if pct_col is None:
        return
    work = filtered.copy()
    work[pct_col] = pd.to_numeric(work[pct_col], errors="coerce")
    cumple = int((work[pct_col] >= 100).sum())
    alerta = int(((work[pct_col] >= 80) & (work[pct_col] < 100)).sum())
    critico = int((work[pct_col] < 80).sum())
    sin_dato = int(work[pct_col].isna().sum())
    cards = [
        ("Cumple", cumple, "#ECFDF5", "#166534"),
        ("Alerta", alerta, "#FEF3C7", "#98660E"),
        ("Crítico", critico, "#FEF2F2", "#991B1B"),
        ("Sin dato", sin_dato, "#F8FAFC", "#475569"),
    ]
    cells = ""
    for title, value, bg, color in cards:
        cells += f"<div style='padding:18px;border-radius:18px;background:{bg};border:1px solid rgba(15,23,42,0.08);'>"
        cells += f"<div style='font-size:0.78rem;font-weight:700;color:{color};text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;'>{title}</div>"
        cells += f"<div style='font-size:2rem;font-weight:800;color:#0f172a;'>{value}</div>"
        cells += "</div>"
    st.markdown(
        f"""
        <div style='margin-top:22px;'>
            <div style='font-size:1rem;font-weight:700;color:#0f172a;margin-bottom:12px;'>Distribución por Estado</div>
            <div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;'>{cells}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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

    try:
        from streamlit_app.components.filter_panel import render_filter_panel
    except ImportError:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from streamlit_app.components.filter_panel import render_filter_panel

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
    default_month_num = _get_prev_month_for_year(tracking_df, default_year) or 12
    default_month = MESES_OPCIONES[default_month_num - 1]

    topbar_year = st.session_state.get("topbar_year")
    topbar_month = st.session_state.get("topbar_month")
    if topbar_year is not None:
        st.info(f"Filtro activo desde barra global: {str(topbar_month) if topbar_month is not None else default_month} {topbar_year}")

    initial_year = int(topbar_year) if topbar_year is not None else default_year
    initial_month = str(topbar_month) if topbar_month is not None else default_month
    initial_month_num = MESES_OPCIONES.index(initial_month) + 1 if initial_month in MESES_OPCIONES else default_month_num
    _, initial_snapshot_df = _prepare_filters(tracking_df, map_df, int(initial_year), initial_month_num)

    procesos = sorted(initial_snapshot_df["Proceso_padre"].dropna().astype(str).unique().tolist())
    proceso_sel_cur = st.session_state.get("filter_proceso", "Todos")
    subproceso_options_base: list[str] = []
    if proceso_sel_cur != "Todos":
        subproceso_options_base = sorted(
            initial_snapshot_df[initial_snapshot_df["Proceso_padre"].astype(str) == proceso_sel_cur][
                "Subproceso_final"
            ].dropna().astype(str).unique().tolist()
        )

    sels_filters = render_filter_panel(
        filters=[
            {
                "key": "anio", "label": "Año",
                "type": "selectbox",
                "options": years, "default": initial_year, "include_all": False,
            },
            {
                "key": "mes", "label": "Mes",
                "type": "selectbox",
                "options": MESES_OPCIONES, "default": initial_month, "include_all": False,
            },
            {
                "key": "proceso", "label": "Proceso",
                "type": "selectbox",
                "options": procesos, "include_all": True,
            },
            {
                "key": "subproceso", "label": "Subproceso",
                "type": "selectbox",
                "options": subproceso_options_base, "include_all": True,
            },
        ],
        title="Filtros oficiales",
        key_prefix="filter",
        n_cols=4,
    )

    anio = int(topbar_year) if topbar_year is not None else sels_filters["anio"] or default_year
    mes = str(topbar_month) if topbar_year is not None else sels_filters["mes"] or default_month
    proceso_sel = sels_filters["proceso"] or "Todos"
    subproceso_sel = sels_filters["subproceso"] or "Todos"

    selected_month_num = MESES_OPCIONES.index(mes) + 1 if mes in MESES_OPCIONES else default_month_num
    full_work_df, snapshot_df = _prepare_filters(tracking_df, map_df, int(anio), selected_month_num)

    prev_year = int(anio) - 1 if int(anio) - 1 in years else None
    base_df = None
    if prev_year is not None:
        _, prev_snapshot_df = _prepare_filters(tracking_df, map_df, int(prev_year), selected_month_num)
        if not prev_snapshot_df.empty:
            base_df = prev_snapshot_df

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
            "Resumen Ejecutivo",
            "Indicadores",
            "Calidad de Datos",
            "Auditoría",
            "Propuestas",
            "Análisis IA",
        ]
    )

    with tabs[0]:
        st.markdown("### Resumen Ejecutivo")
        if filtered.empty:
            st.info("No hay datos disponibles.")
        else:
            summary = _build_executive_summary(filtered, base_df)
            _render_executive_cards(summary)
            _render_year_comparison(historic_base, selected_month_num)
            _render_critical_indicators(filtered)
            _render_distribution_cards(filtered)

    with tabs[1]:
        st.markdown("### Indicadores")
        if filtered.empty:
            st.info("No hay datos disponibles.")
        else:
            _render_indicadores_subproceso_cards(filtered, historic_base, int(anio), selected_month_num, map_df, proceso_sel)

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
