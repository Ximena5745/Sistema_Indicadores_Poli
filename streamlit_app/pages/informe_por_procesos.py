from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from streamlit_app.components.charts import grafico_historico_indicador, tabla_historica_indicador
from streamlit_app.services.data_service import DataService
from streamlit_app.styles.design_system import COLORS, GRADIENTS
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
    card_styles = [
        (COLORS["primary"], COLORS["primary_light"]),
        (COLORS["success"], COLORS["success_light"]),
        (COLORS["info"], COLORS["info_light"]),
        (COLORS["warning"], COLORS["warning_light"]),
    ]
    card_html = ""
    titles = [
        "Score de Salud",
        "Cumplimiento Global",
        "Indicadores evaluados",
        "Estado de alertas",
    ]
    values = [
        f"{summary['score']:.1f}",
        f"{summary['avg']:.1f}%",
        f"{summary['total_indicadores']}",
        f"{summary['alerta'] + summary['peligro']}",
    ]
    descriptions = [
        f"{summary['label']} · {delta_label}",
        "Meta: 100%",
        f"{summary['total_indicadores']} activos en el periodo",
        f"{summary['alerta']} alertas · {summary['peligro']} críticos",
    ]

    for index, (title, value, description) in enumerate(zip(titles, values, descriptions)):
        border_color, accent_color = card_styles[index]
        card_html += f"""
            <div style='padding:20px;border-radius:18px;background:{COLORS['surface']};border:1px solid #E2E8F0;box-shadow:0 10px 24px rgba(15,23,42,0.06);border-top:4px solid {accent_color};'>
                <div style='font-size:0.78rem;font-weight:700;color:{COLORS['text_secondary']};text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;'>{title}</div>
                <div style='font-size:2.8rem;font-weight:800;color:{COLORS['text_primary']};'>{value}</div>
                <div style='font-size:0.9rem;color:{COLORS['gray_600']};margin-top:12px;'>{description}</div>
            </div>
        """

    components.html(
        f"""
        <div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin:0 0 18px;'>
            {card_html}
        </div>
        """,
        height=260,
        scrolling=False,
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

    # Paleta de colores diferenciados por año
    year_colors = [
        ("#2563eb", "#dbeafe"),  # azul
        ("#16a34a", "#dcfce7"),  # verde
        ("#d97706", "#fef3c7"),  # ámbar
        ("#7c3aed", "#ede9fe"),  # violeta
    ]
    cards_html = ""
    bar_colors = []
    for index, (ano, prom) in enumerate(rows):
        accent_color, bg_color = year_colors[index % len(year_colors)]
        bar_colors.append(accent_color)
        cards_html += f"""
            <div style='padding:12px 16px;border-radius:14px;background:{bg_color};border:1px solid {accent_color}33;box-shadow:0 4px 12px rgba(15,23,42,0.06);border-left:4px solid {accent_color};'>
                <div style='font-size:0.75rem;font-weight:700;color:{accent_color};text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;'>Año {ano}</div>
                <div style='font-size:1.9rem;font-weight:800;color:#0f172a;line-height:1.1;'>{prom:.1f}%</div>
                <div style='font-size:0.76rem;color:#64748b;margin-top:4px;'>Cumplimiento promedio</div>
            </div>
        """
    components.html(
        f"""
        <div style='margin:16px 0 8px;font-size:0.95rem;font-weight:700;color:#0f172a;'>Evolución comparativa interanual</div>
        <div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-bottom:14px;'>{cards_html}</div>
        """,
        height=160,
        scrolling=False,
    )

    year_labels = [str(ano) for ano, _ in rows]
    year_values = [prom for _, prom in rows]
    max_val = max(year_values) if year_values else 100

    figure = go.Figure(
        data=[
            go.Bar(
                x=year_labels,
                y=year_values,
                marker=dict(color=bar_colors),
                text=[f"{prom:.1f}%" for prom in year_values],
                textposition="outside",
                textfont=dict(size=12, color="#0f172a", family="Inter, sans-serif"),
                hovertemplate="Año %{x}: %{y:.1f}%<extra></extra>",
            )
        ]
    )
    figure.update_layout(
        margin=dict(l=0, r=0, t=20, b=0),
        height=220,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,250,252,0.6)",
        xaxis=dict(
            type="category",
            showgrid=False,
            tickfont=dict(size=13, color="#0f172a"),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(15,23,42,0.07)",
            tickfont=dict(size=11, color="#64748b"),
            ticksuffix="%",
            range=[0, max_val * 1.20],
        ),
        bargap=0.4,
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
        items += f"<div style='margin-bottom:12px;padding:18px;border-radius:18px;background:#FEF2F2;border:1px solid rgba(211,47,47,0.16);box-shadow:0 10px 24px rgba(15,23,42,0.06);'>"
        items += f"<div style='font-weight:700;color:{COLORS['danger']};margin-bottom:6px;font-size:1rem;'>{indicador}</div>"
        items += f"<div style='font-size:0.88rem;color:{COLORS['text_secondary']};margin-bottom:6px;'>Proceso: {proceso}</div>"
        items += f"<div style='font-size:1.05rem;font-weight:700;color:{COLORS['danger_dark']};'>Cumplimiento: {valor:.1f}%</div>"
        items += "</div>"
    components.html(
        f"""
        <div style='margin-top:20px;'>
            <div style='font-size:1rem;font-weight:700;color:{COLORS['text_primary']};margin-bottom:12px;'>Indicadores críticos</div>
            {items}
        </div>
        """,
        height=280,
        scrolling=False,
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
        ("Cumple", cumple, "#ECFDF5", COLORS['success']),
        ("Alerta", alerta, "#FEF3C7", COLORS['warning']),
        ("Crítico", critico, "#FEE2E2", COLORS['danger']),
        ("Sin dato", sin_dato, COLORS['surface_variant'], COLORS['text_secondary']),
    ]
    cells = ""
    for title, value, bg, color in cards:
        cells += f"<div style='padding:20px;border-radius:18px;background:{bg};border:1px solid #E2E8F0;box-shadow:0 10px 24px rgba(15,23,42,0.06);'>"
        cells += f"<div style='font-size:0.8rem;font-weight:700;color:{color};text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;'>{title}</div>"
        cells += f"<div style='font-size:2.2rem;font-weight:800;color:{COLORS['text_primary']};'>{value}</div>"
        cells += "</div>"
    components.html(
        f"""
        <div style='margin-top:22px;'>
            <div style='font-size:1rem;font-weight:700;color:{COLORS['text_primary']};margin-bottom:18px;'>Distribución por Estado</div>
            <div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;'>{cells}</div>
        </div>
        """,
        height=260,
        scrolling=False,
    )


# ── Calidad de Datos — funciones auxiliares ───────────────────────────────────

_DIM_MAP = {
    "Completitud": "II. COMPLETITUD",
    "Consistencia": "III. CONSISTENCIA",
    "Oportunidad": "I. OPORTUNIDAD",
    "Exactitud": "IV. PRECISIÓN",
}

_DIM_COLORS = {
    "Completitud": "#42a5f5",
    "Consistencia": "#66bb6a",
    "Oportunidad": "#ffa726",
    "Exactitud": "#ab47bc",
}


def _cat_to_score(val: object) -> float | None:
    t = _norm_text(val)
    if not t:
        return None
    if "PARCIAL" in t:
        return 50.0
    if "NO CUMPLE" in t:
        return 0.0
    if "CUMPLE" in t:
        return 100.0
    return None


def _compute_calidad_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte df de calidad con columnas categóricas a scores numéricos 0-100."""
    if df.empty:
        return pd.DataFrame()
    work = df.copy()
    indicator_col = "Temática" if "Temática" in work.columns else None
    work["Indicador"] = work[indicator_col].astype(str).str.strip() if indicator_col else "Sin nombre"
    for dim_name, src_col in _DIM_MAP.items():
        if src_col in work.columns:
            work[dim_name] = work[src_col].apply(_cat_to_score)
        else:
            work[dim_name] = None
    score_cols = [d for d in _DIM_MAP if d in work.columns]
    numeric_scores = work[score_cols].apply(pd.to_numeric, errors="coerce")
    work["Score Total"] = numeric_scores.mean(axis=1, skipna=True).round(0).astype("Int64")
    return work[["Indicador"] + list(_DIM_MAP.keys()) + ["Score Total"]].copy()


def _dim_scores_global(df_scored: pd.DataFrame) -> dict[str, float]:
    out = {}
    for dim in _DIM_MAP:
        if dim in df_scored.columns:
            vals = pd.to_numeric(df_scored[dim], errors="coerce").dropna()
            out[dim] = round(float(vals.mean()), 1) if not vals.empty else 0.0
        else:
            out[dim] = 0.0
    return out


def _score_color(score: float) -> tuple[str, str]:
    """Retorna (bg, fg) según score."""
    if score >= 90:
        return "#e8f5e9", "#1b5e20"
    if score >= 70:
        return "#fff8e1", "#e65100"
    return "#ffebee", "#b71c1c"


def _render_calidad_header(score_global: float) -> None:
    bg, fg = _score_color(score_global)
    st.markdown(
        f"""
        <div style='display:flex;align-items:center;justify-content:space-between;
                    margin-bottom:16px;'>
            <div style='font-size:1.25rem;font-weight:700;color:#0f172a;'>
                ⚡ Evaluación de Calidad de Datos
            </div>
            <div style='background:{bg};color:{fg};border:1px solid {fg};
                        border-radius:20px;padding:4px 14px;font-size:0.82rem;
                        font-weight:700;'>
                SCORE GLOBAL: {score_global:.0f}%
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_calidad_gauge_dims(score_global: float, dim_scores: dict[str, float]) -> None:
    col_gauge, col_dims, col_radar = st.columns([1, 1.4, 1.6])

    with col_gauge:
        color = "#66bb6a" if score_global >= 90 else ("#ffa726" if score_global >= 70 else "#ef5350")
        capped = min(score_global, 100.0)
        fig = go.Figure(go.Pie(
            values=[capped, max(0.0, 100.0 - capped)],
            hole=0.72,
            marker=dict(colors=[color, "#E5E7EB"]),
            textinfo="none",
            hoverinfo="none",
            sort=False,
        ))
        fig.add_annotation(
            text=f"<b>{score_global:.0f}%</b>",
            x=0.5, y=0.58,
            font=dict(size=28, color=color, family="Inter, sans-serif"),
            showarrow=False, xanchor="center",
        )
        fig.add_annotation(
            text="SCORE TOTAL",
            x=0.5, y=0.40,
            font=dict(size=9, color="#64748B", family="Inter, sans-serif"),
            showarrow=False, xanchor="center",
        )
        fig.update_layout(
            margin=dict(t=0, b=0, l=0, r=0),
            showlegend=False,
            height=220,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_dims:
        st.markdown(
            "<div style='font-size:0.78rem;font-weight:600;color:#64748B;"
            "text-transform:uppercase;letter-spacing:0.05em;margin-bottom:10px;'>"
            "DIMENSIONES DE CALIDAD</div>",
            unsafe_allow_html=True,
        )
        for dim, score in dim_scores.items():
            clr = _DIM_COLORS.get(dim, "#1A3A5C")
            bar_w = max(0, min(100, score))
            st.markdown(
                f"""
                <div style='margin-bottom:10px;'>
                    <div style='display:flex;justify-content:space-between;
                                font-size:0.8rem;font-weight:600;color:#374151;
                                margin-bottom:3px;'>
                        <span>{dim}</span>
                        <span style='color:{clr};font-weight:700;'>{score:.0f}%</span>
                    </div>
                    <div style='background:#E5E7EB;border-radius:6px;height:8px;'>
                        <div style='background:{clr};width:{bar_w}%;height:8px;
                                    border-radius:6px;'></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_radar:
        if dim_scores:
            dims = list(dim_scores.keys())
            vals = [dim_scores[d] for d in dims]
            vals_closed = vals + [vals[0]]
            dims_closed = dims + [dims[0]]
            fig_r = go.Figure(go.Scatterpolar(
                r=vals_closed,
                theta=dims_closed,
                fill="toself",
                fillcolor="rgba(66, 165, 245, 0.18)",
                line=dict(color="#1A3A5C", width=2),
                marker=dict(color="#1A3A5C", size=5),
            ))
            fig_r.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=8)),
                    angularaxis=dict(tickfont=dict(size=10, color="#374151")),
                    bgcolor="rgba(0,0,0,0)",
                ),
                showlegend=False,
                height=220,
                margin=dict(t=10, b=10, l=20, r=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.markdown(
                "<div style='font-size:0.78rem;font-weight:600;color:#64748B;"
                "text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;'>"
                "ANÁLISIS POR DIMENSIÓN</div>",
                unsafe_allow_html=True,
            )
            st.plotly_chart(fig_r, use_container_width=True)


def _render_calidad_alertas(dim_scores: dict[str, float], df_scored: pd.DataFrame) -> None:
    """Alertas y recomendaciones en la misma fila: 2 alertas + 3 recomendaciones."""
    if not dim_scores:
        return

    # --- Conteos reales por dimensión ---
    dim_stats: dict[str, dict] = {}
    for dim in _DIM_MAP:
        if dim in df_scored.columns:
            col_data = pd.to_numeric(df_scored[dim], errors="coerce").dropna()
            n_total = len(col_data)
            dim_stats[dim] = {
                "total": n_total,
                "cumple": int((col_data == 100).sum()),
                "parcial": int((col_data == 50).sum()),
                "no_cumple": int((col_data == 0).sum()),
            }

    worst_dim = min(dim_scores, key=dim_scores.get)
    best_dim = max(dim_scores, key=dim_scores.get)
    worst_score = dim_scores[worst_dim]
    best_score = dim_scores[best_dim]

    # --- Construir HTML de alertas ---
    alert_cards: list[str] = []

    if worst_score < 90:
        ws = dim_stats.get(worst_dim, {})
        n_nc = ws.get("no_cumple", 0)
        n_pa = ws.get("parcial", 0)
        n_tot = ws.get("total", 0)
        ind_nc_list: list[str] = []
        if n_tot > 0 and worst_dim in df_scored.columns:
            mask = pd.to_numeric(df_scored[worst_dim], errors="coerce") == 0
            ind_nc_list = [str(v) for v in df_scored.loc[mask, "Indicador"].tolist() if str(v) not in ("nan", "")]
        det_nc = f"{n_nc} NO CUMPLE" + (f" · {n_pa} PARCIAL" if n_pa else "") + (f" / {n_tot}" if n_tot else "")
        ind_txt = (", ".join(ind_nc_list[:3]) + (f" +{len(ind_nc_list)-3}" if len(ind_nc_list) > 3 else "")) if ind_nc_list else ""
        alert_cards.append(
            f"<div style='background:#fff8e1;border-left:4px solid #ffa726;border-radius:6px;"
            f"padding:8px 10px;'>"
            f"<div style='font-size:0.75rem;font-weight:700;color:#e65100;'>⏱ Crítica: {worst_dim} · {worst_score:.0f}/100</div>"
            f"<div style='font-size:0.72rem;color:#78350f;margin-top:2px;'>{det_nc}"
            + (f"<br><i>{ind_txt}</i>" if ind_txt else "")
            + "</div></div>"
        )

    if best_score >= 90:
        bs = dim_stats.get(best_dim, {})
        n_cum = bs.get("cumple", 0)
        n_tot_b = bs.get("total", 0)
        pct_ok = f"{n_cum}/{n_tot_b}" if n_tot_b else "—"
        alert_cards.append(
            f"<div style='background:#e8f5e9;border-left:4px solid #66bb6a;border-radius:6px;"
            f"padding:8px 10px;'>"
            f"<div style='font-size:0.75rem;font-weight:700;color:#1b5e20;'>✓ Fortaleza: {best_dim} · {best_score:.0f}/100</div>"
            f"<div style='font-size:0.72rem;color:#1b5e20;margin-top:2px;'>{pct_ok} indicadores CUMPLEN al 100%.</div>"
            f"</div>"
        )

    # --- Construir recomendaciones ---
    recs: list[tuple] = []

    if not df_scored.empty and "Score Total" in df_scored.columns:
        peores = df_scored.dropna(subset=["Score Total"]).copy()
        peores["Score Total"] = pd.to_numeric(peores["Score Total"], errors="coerce")
        peores = peores.sort_values("Score Total")
        if not peores.empty:
            worst_row = peores.iloc[0]
            worst_ind = str(worst_row.get("Indicador", ""))
            ws_score = float(worst_row["Score Total"])
            dims_fallando = [
                f"{d} ({_to_float(worst_row.get(d)):.0f}%)"
                for d in _DIM_MAP if _to_float(worst_row.get(d)) is not None and _to_float(worst_row.get(d)) < 100
            ]
            items = [f"Score: {ws_score:.0f}/100"]
            if dims_fallando:
                items.append(", ".join(dims_fallando))
            items.append("Convocar responsable para corregir NO CUMPLE.")
            recs.append(("Alta", f"«{worst_ind}»", "#ef5350", "#ffebee", items))

    if dim_scores:
        wdim = min(dim_scores, key=dim_scores.get)
        wdim_score = dim_scores[wdim]
        if wdim_score < 90:
            ind_nc: list[str] = []
            if wdim in df_scored.columns:
                mask = pd.to_numeric(df_scored[wdim], errors="coerce") < 100
                ind_nc = [str(v) for v in df_scored.loc[mask, "Indicador"].tolist() if str(v) not in ("nan", "")]
            listado = ", ".join(f'«{i}»' for i in ind_nc[:2]) + (f" +{len(ind_nc)-2}" if len(ind_nc) > 2 else "")
            items_m = [
                f"{wdim}: {wdim_score:.0f}/100 — {len(ind_nc)} sin cumplimiento.",
                listado if listado else "",
                f"Meta: ≥ 90% antes del próximo corte.",
            ]
            recs.append(("Media", f"Fortalecer: {wdim}", "#ffa726", "#fff8e1", [i for i in items_m if i]))

    if dim_scores:
        bdim = max(dim_scores, key=dim_scores.get)
        bscore = dim_scores[bdim]
        n_ok, n_tot = 0, 0
        if bdim in df_scored.columns:
            col_data = pd.to_numeric(df_scored[bdim], errors="coerce").dropna()
            n_ok = int((col_data == 100).sum())
            n_tot = len(col_data)
        recs.append(("Baja", f"Mantener: {bdim}", "#66bb6a", "#e8f5e9", [
            f"{n_ok}/{n_tot} CUMPLEN al 100% (score: {bscore:.0f}/100).",
            "Documentar prácticas y auditar trimestralmente.",
        ]))

    # --- Renderizar en una sola fila: alertas | recomendaciones ---
    st.markdown(
        "<div style='font-size:0.82rem;font-weight:700;color:#0f172a;margin:12px 0 5px 0;'>"
        "⚠️ Alertas &nbsp;&nbsp;&nbsp; 💡 Recomendaciones Priorizadas</div>",
        unsafe_allow_html=True,
    )
    n_alert_cols = len(alert_cards) if alert_cards else 1
    n_rec_cols = len(recs) if recs else 1
    all_cols = st.columns([1] * n_alert_cols + [1] * n_rec_cols)

    for i, card_html in enumerate(alert_cards):
        with all_cols[i]:
            st.markdown(card_html, unsafe_allow_html=True)

    pcolor_map = {"Alta": "#ef5350", "Media": "#ffa726", "Baja": "#66bb6a"}
    for j, (prio, titulo, dot_color, bg_color, items) in enumerate(recs):
        pcolor = pcolor_map.get(prio, "#64748B")
        items_html = "".join(
            f"<li style='font-size:0.72rem;color:#374151;margin-bottom:2px;'>{a}</li>"
            for a in items
        )
        with all_cols[n_alert_cols + j]:
            st.markdown(
                f"<div style='background:{bg_color};border-left:4px solid {dot_color};"
                f"border-radius:6px;padding:8px 10px;'>"
                f"<div style='font-size:0.68rem;font-weight:700;color:{pcolor};"
                f"text-transform:uppercase;margin-bottom:2px;'>{prio} Prioridad</div>"
                f"<div style='font-size:0.75rem;font-weight:700;color:#0f172a;"
                f"margin-bottom:3px;line-height:1.2;'>{titulo}</div>"
                f"<ul style='margin:0;padding-left:13px;'>{items_html}</ul>"
                f"</div>",
                unsafe_allow_html=True,
            )


def _render_detalle_indicadores(df_scored: pd.DataFrame) -> None:
    if df_scored.empty:
        st.info("Sin datos de detalle.")
        return
    st.markdown(
        "<div style='font-size:1rem;font-weight:700;color:#0f172a;margin:16px 0 8px 0;'>"
        "📋 Detalle por Indicador</div>",
        unsafe_allow_html=True,
    )
    dims = list(_DIM_MAP.keys())
    header_cells = "".join(
        f"<th style='padding:8px 10px;background:#f1f5f9;color:#374151;"
        f"font-size:0.75rem;font-weight:700;text-transform:uppercase;"
        f"letter-spacing:0.05em;white-space:nowrap;'>{d.upper()}</th>"
        for d in dims
    )
    header = (
        "<tr>"
        "<th style='padding:8px 10px;background:#f1f5f9;color:#374151;"
        "font-size:0.75rem;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.05em;text-align:left;'>INDICADOR</th>"
        + header_cells
        + "<th style='padding:8px 10px;background:#f1f5f9;color:#374151;"
        "font-size:0.75rem;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.05em;'>SCORE TOTAL</th>"
        "</tr>"
    )
    rows_html = ""
    for _, row in df_scored.iterrows():
        ind = str(row.get("Indicador", ""))
        dim_cells = ""
        for dim in dims:
            val = _to_float(row.get(dim))
            if val is None:
                dim_cells += "<td style='padding:6px 10px;text-align:center;'><span style='background:#eceff1;color:#607d8b;border-radius:6px;padding:2px 8px;font-size:0.78rem;'>—</span></td>"
            else:
                bg, fg = _score_color(val)
                dim_cells += (
                    f"<td style='padding:6px 10px;text-align:center;'>"
                    f"<span style='background:{bg};color:{fg};border-radius:6px;"
                    f"padding:2px 8px;font-size:0.78rem;font-weight:600;'>{val:.0f}%</span>"
                    f"</td>"
                )
        total = _to_float(row.get("Score Total"))
        if total is None:
            total_cell = "<td style='padding:6px 10px;text-align:center;color:#9ca3af;font-size:0.85rem;'>—</td>"
        else:
            _, fg = _score_color(total)
            total_cell = (
                f"<td style='padding:6px 10px;text-align:center;font-size:0.9rem;"
                f"font-weight:700;color:{fg};'>{total:.0f}%</td>"
            )
        rows_html += (
            f"<tr style='border-bottom:1px solid #f1f5f9;'>"
            f"<td style='padding:8px 10px;font-size:0.85rem;color:#0f172a;"
            f"max-width:280px;line-height:1.3;'>{ind}</td>"
            + dim_cells
            + total_cell
            + "</tr>"
        )
    st.markdown(
        f"<div style='overflow-x:auto;'>"
        f"<table style='width:100%;border-collapse:collapse;'>"
        f"<thead>{header}</thead>"
        f"<tbody>{rows_html}</tbody>"
        f"</table></div>",
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
    unidad_options_base = sorted(initial_snapshot_df["Unidad"].dropna().astype(str).unique().tolist()) if "Unidad" in initial_snapshot_df.columns else []

    unidad_sel_cur = st.session_state.get("filter_unidad", "Todos")
    proceso_sel_cur = st.session_state.get("filter_proceso", "Todos")

    proceso_df_base = initial_snapshot_df.copy()
    if unidad_sel_cur != "Todos" and "Unidad" in proceso_df_base.columns:
        proceso_df_base = proceso_df_base[proceso_df_base["Unidad"].astype(str) == unidad_sel_cur]
    proceso_options_base = sorted(proceso_df_base["Proceso_padre"].dropna().astype(str).unique().tolist())

    sub_df_base = initial_snapshot_df.copy()
    if unidad_sel_cur != "Todos" and "Unidad" in sub_df_base.columns:
        sub_df_base = sub_df_base[sub_df_base["Unidad"].astype(str) == unidad_sel_cur]
    if proceso_sel_cur != "Todos":
        sub_df_base = sub_df_base[sub_df_base["Proceso_padre"].astype(str) == proceso_sel_cur]
    subproceso_options_base = sorted(sub_df_base["Subproceso_final"].dropna().astype(str).unique().tolist())

    clasificacion_options_base = sorted(initial_snapshot_df["Clasificacion"].dropna().astype(str).unique().tolist()) if "Clasificacion" in initial_snapshot_df.columns else sorted(initial_snapshot_df["Clasificación"].dropna().astype(str).unique().tolist()) if "Clasificación" in initial_snapshot_df.columns else []
    frecuencia_options_base = sorted(initial_snapshot_df["Periodicidad"].dropna().astype(str).unique().tolist()) if "Periodicidad" in initial_snapshot_df.columns else sorted(initial_snapshot_df["Frecuencia"].dropna().astype(str).unique().tolist()) if "Frecuencia" in initial_snapshot_df.columns else sorted(initial_snapshot_df["Frecuencia de Medición"].dropna().astype(str).unique().tolist()) if "Frecuencia de Medición" in initial_snapshot_df.columns else []

    sels_filters = render_filter_panel(
        filters=[
            {
                "key": "anio",
                "label": "Año",
                "type": "selectbox",
                "options": years,
                "default": initial_year,
                "include_all": False,
            },
            {
                "key": "mes",
                "label": "Mes",
                "type": "selectbox",
                "options": MESES_OPCIONES,
                "default": initial_month,
                "include_all": False,
            },
            {
                "key": "clasificacion",
                "label": "Clasificación",
                "type": "selectbox",
                "options": clasificacion_options_base,
                "include_all": True,
            },
            {
                "key": "frecuencia",
                "label": "Frecuencia",
                "type": "selectbox",
                "options": frecuencia_options_base,
                "include_all": True,
            },
            {
                "key": "unidad",
                "label": "Unidad",
                "type": "selectbox",
                "options": unidad_options_base,
                "include_all": True,
            },
            {
                "key": "proceso",
                "label": "Proceso",
                "type": "selectbox",
                "options": proceso_options_base,
                "include_all": True,
            },
            {
                "key": "subproceso",
                "label": "Subproceso",
                "type": "selectbox",
                "options": subproceso_options_base,
                "include_all": True,
            },
        ],
        title="Filtros oficiales",
        key_prefix="filter",
        n_cols=4,
    )

    anio = int(topbar_year) if topbar_year is not None else sels_filters["anio"] or default_year
    mes = str(topbar_month) if topbar_year is not None else sels_filters["mes"] or default_month
    clasificacion_sel = sels_filters["clasificacion"] or "Todos"
    frecuencia_sel = sels_filters["frecuencia"] or "Todos"
    unidad_sel = sels_filters["unidad"] or "Todos"
    proceso_sel = sels_filters["proceso"] or "Todos"
    subproceso_sel = sels_filters["subproceso"] or "Todos"

    selected_month_num = MESES_OPCIONES.index(mes) + 1 if mes in MESES_OPCIONES else default_month_num
    full_work_df, snapshot_df = _prepare_filters(tracking_df, map_df, int(anio), selected_month_num)

    if clasificacion_sel != "Todos":
        if "Clasificacion" in snapshot_df.columns:
            snapshot_df = snapshot_df[snapshot_df["Clasificacion"].astype(str) == clasificacion_sel]
        elif "Clasificación" in snapshot_df.columns:
            snapshot_df = snapshot_df[snapshot_df["Clasificación"].astype(str) == clasificacion_sel]
    if frecuencia_sel != "Todos":
        if "Periodicidad" in snapshot_df.columns:
            snapshot_df = snapshot_df[snapshot_df["Periodicidad"].astype(str) == frecuencia_sel]
        elif "Frecuencia" in snapshot_df.columns:
            snapshot_df = snapshot_df[snapshot_df["Frecuencia"].astype(str) == frecuencia_sel]
        elif "Frecuencia de Medición" in snapshot_df.columns:
            snapshot_df = snapshot_df[snapshot_df["Frecuencia de Medición"].astype(str) == frecuencia_sel]
    if unidad_sel != "Todos" and "Unidad" in snapshot_df.columns:
        snapshot_df = snapshot_df[snapshot_df["Unidad"].astype(str) == unidad_sel]

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
        if latest.empty:
            st.info("No hay datos disponibles.")
        else:
            summary = _build_executive_summary(latest, base_df)
            _render_executive_cards(summary)
            _render_year_comparison(historic_base, selected_month_num)
            _render_critical_indicators(latest)
            _render_distribution_cards(latest)

    with tabs[1]:
        st.markdown("### Indicadores")
        if filtered.empty:
            st.info("No hay datos disponibles.")
        else:
            _render_indicadores_subproceso_cards(filtered, historic_base, int(anio), selected_month_num, map_df, proceso_sel)

    with tabs[2]:
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
                df_scored = _compute_calidad_scores(calidad_df)
                dim_scores = _dim_scores_global(df_scored)
                score_global = round(float(pd.Series(list(dim_scores.values())).mean()), 1) if dim_scores else 0.0

                _render_calidad_header(score_global)
                _render_calidad_gauge_dims(score_global, dim_scores)
                _render_calidad_alertas(dim_scores, df_scored)
                _render_detalle_indicadores(df_scored)

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
