"""Utilities for informe_por_procesos page."""

import pandas as pd
import streamlit as st

from streamlit_app.pages.informe_por_procesos_config import (
    EXCEL_SHEETS,
    MESES_OPCIONES,
    SOURCE_ORDER,
    SOURCE_STYLE,
    get_excel_path,
)
from streamlit_app.pages.resumen_por_proceso import (
    _norm_text,
    _prepare_tracking,
)
from streamlit_app.services.cmi_filters import filter_df_for_procesos


def load_propuestas(proceso_actual: str = "Todos", subproceso_actual: str = "Todos") -> tuple[pd.DataFrame, str | None]:
    """Load proposed indicators from Excel file.
    
    Args:
        proceso_actual: Filter by process name or "Todos"
        subproceso_actual: Filter by subprocess name or "Todos"
    
    Returns:
        Tuple of (DataFrame with proposed indicators, error message or None)
    """
    excel_path = get_excel_path()
    if not excel_path.exists():
        return pd.DataFrame(), f"No existe el archivo: {excel_path}"

    try:
        # Load Retos sheet
        retos = pd.read_excel(excel_path, sheet_name=EXCEL_SHEETS["Retos"]["sheet"])
        retos_filtrados = retos[retos[EXCEL_SHEETS["Retos"]["filter_col"]].astype(str).str.upper() == "SI"][
            EXCEL_SHEETS["Retos"]["select_cols"]
        ]
        retos_filtrados = retos_filtrados.dropna(subset=["Indicador Propuesto"])
        retos_filtrados["Fuente"] = "Retos"

        # Load Proyectos sheet
        proyectos = pd.read_excel(excel_path, sheet_name=EXCEL_SHEETS["Proyectos"]["sheet"])
        proyectos_filtrados = proyectos[proyectos[EXCEL_SHEETS["Proyectos"]["filter_col"]].astype(str).str.upper() == "SI"][
            EXCEL_SHEETS["Proyectos"]["select_cols"]
        ]
        proyectos_filtrados = proyectos_filtrados.rename(columns=EXCEL_SHEETS["Proyectos"]["rename"])
        proyectos_filtrados = proyectos_filtrados.dropna(subset=["Indicador Propuesto"])
        proyectos_filtrados["Fuente"] = "Proyectos"

        # Load Plan de mejoramiento sheet
        plan = pd.read_excel(excel_path, sheet_name=EXCEL_SHEETS["Plan"]["sheet"], header=EXCEL_SHEETS["Plan"]["header"])
        plan_filtrados = plan[plan[EXCEL_SHEETS["Plan"]["filter_col"]].astype(str).str.upper() == "SI"][
            EXCEL_SHEETS["Plan"]["select_cols"]
        ]
        plan_filtrados = plan_filtrados.rename(columns=EXCEL_SHEETS["Plan"]["rename"])
        plan_filtrados = plan_filtrados.dropna(subset=["Indicador Propuesto"])
        plan_filtrados["Fuente"] = "Plan de mejoramiento"

        # Load Calidad sheet
        calidad = pd.read_excel(excel_path, sheet_name=EXCEL_SHEETS["Calidad"]["sheet"])
        calidad_filtrados = calidad[EXCEL_SHEETS["Calidad"]["select_cols"]].rename(
            columns=EXCEL_SHEETS["Calidad"]["rename"]
        )
        calidad_filtrados = calidad_filtrados.dropna(subset=["Indicador Propuesto"])
        calidad_filtrados["Fuente"] = "Calidad"

        # Combine all sheets
        df_final = pd.concat(
            [retos_filtrados, proyectos_filtrados, plan_filtrados, calidad_filtrados],
            ignore_index=True,
        )
        df_final = df_final.drop_duplicates(subset=["Proceso", "Subproceso", "Indicador Propuesto", "Fuente"])

        # Apply filters if specified
        if proceso_actual != "Todos":
            proceso_norm = _norm_text(proceso_actual)
            df_final = df_final[df_final["Proceso"].astype(str).map(_norm_text) == proceso_norm]
        if subproceso_actual != "Todos":
            sub_norm = _norm_text(subproceso_actual)
            df_final = df_final[df_final["Subproceso"].astype(str).map(_norm_text) == sub_norm]

        return df_final, None
    except Exception as exc:
        return pd.DataFrame(), f"Error leyendo indicadores propuestos: {exc}"


def render_propuestas(df: pd.DataFrame) -> None:
    """Render proposed indicators with styled cards organized by source and process.
    
    Args:
        df: DataFrame with proposed indicators
    """
    if df.empty:
        st.info("No hay indicadores propuestos para el filtro seleccionado.")
        return

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
                    for i, fuente in enumerate(SOURCE_ORDER):
                        with col_blocks[i]:
                            style = SOURCE_STYLE[fuente]
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


def build_summary_by_unit(df: pd.DataFrame) -> pd.DataFrame:
    """Build summary of indicators by process and subprocess.
    
    Args:
        df: Input DataFrame with indicator data
    
    Returns:
        Summary DataFrame with count and average compliance per unit
    """
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


def build_frequency_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Build summary of indicators by periodicity and month.
    
    Args:
        df: Input DataFrame with indicator data
    
    Returns:
        Summary DataFrame with count and average compliance by frequency
    """
    if df.empty:
        return pd.DataFrame()
    summary = (
        df.groupby(["Periodicidad", "Mes"], dropna=False)
        .agg(indicadores=("Indicador", "nunique"), cumplimiento=("Cumplimiento_pct", "mean"))
        .reset_index()
    )
    summary["cumplimiento"] = pd.to_numeric(summary["cumplimiento"], errors="coerce").round(1)
    return summary


def build_classification_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Build summary of indicators by classification and process type.
    
    Args:
        df: Input DataFrame with indicator data
    
    Returns:
        Summary DataFrame with count and average compliance by classification
    """
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


def build_consolidated_columns(df: pd.DataFrame) -> list[str]:
    """Get consolidated columns for display.
    
    Args:
        df: Input DataFrame
    
    Returns:
        List of column names to display
    """
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


def build_ia_indicators(df: pd.DataFrame) -> tuple[int, int, int, pd.DataFrame, pd.DataFrame]:
    """Extract and classify indicators for IA analysis.
    
    Args:
        df: Input DataFrame with indicator data
    
    Returns:
        Tuple of (num_riesgos, num_alertas, num_saludables, riesgos_df, alertas_df)
    """
    if df.empty or "Cumplimiento_pct" not in df.columns:
        return 0, 0, 0, pd.DataFrame(), pd.DataFrame()
    cumple = pd.to_numeric(df["Cumplimiento_pct"], errors="coerce")
    riesgos = df[cumple < 80].copy()
    alertas = df[(cumple >= 80) & (cumple < 100)].copy()
    saludables = df[cumple >= 100].copy()
    riesgos = riesgos.sort_values("Cumplimiento_pct").head(10)
    alertas = alertas.sort_values("Cumplimiento_pct").head(10)
    return len(riesgos), len(alertas), len(saludables), riesgos, alertas


def prepare_filters(tracking_df: pd.DataFrame, map_df: pd.DataFrame, anio: int, month_num: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Prepare full year and monthly snapshot dataframes with filters applied.
    
    Args:
        tracking_df: Tracking data DataFrame
        map_df: Process map DataFrame
        anio: Year to filter by
        month_num: Month number (1-12)
    
    Returns:
        Tuple of (full_work_df, snapshot_df) with filters applied
    """
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


def get_default_month(tracking_df: pd.DataFrame, default_year: int) -> tuple[str, int]:
    """Get default month and month number from tracking data.
    
    Args:
        tracking_df: Tracking data DataFrame
        default_year: Default year to use
    
    Returns:
        Tuple of (month_name, month_number)
    """
    from streamlit_app.pages.resumen_por_proceso import _get_prev_month_for_year
    
    month_num = _get_prev_month_for_year(tracking_df, default_year) or 12
    month_name = MESES_OPCIONES[month_num - 1]
    return month_name, month_num
