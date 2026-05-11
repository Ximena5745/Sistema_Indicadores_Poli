"""Utilities for cmi_estrategico page."""

import pandas as pd
import streamlit as st
import unicodedata
from html import escape

from streamlit_app.pages.cmi_estrategico_config import (
    NIVEL_FLAG_COLORS,
    NIVEL_ICONS_CMI,
    LINEA_COLORS,
)


def get_sin_gestion_df() -> pd.DataFrame:
    """Load CMI worksheet and return indicators with Plan anual == 3.
    
    Returns:
        DataFrame with id, indicator name, and strategic line
    """
    from services.cmi_filters import load_cmi_worksheet

    df = load_cmi_worksheet()
    if df.empty or "Plan anual" not in df.columns:
        return pd.DataFrame()
    sin_gestion = df[df["Plan anual"] == 3].copy()
    cols = [c for c in ["Id", "Indicador", "Linea"] if c in sin_gestion.columns]
    return sin_gestion[cols] if cols else sin_gestion


def linea_color(linea: str) -> str:
    """Get color for strategic line with fallback logic.
    
    Args:
        linea: Line name
    
    Returns:
        Hex color code
    """
    # Try direct lookup first
    if linea in LINEA_COLORS:
        return LINEA_COLORS[linea]
    
    # Fallback: normalize and match by keyword
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
    if "sostenib" in txt or "sustentab" in txt:
        return "#A6CE38"
    if "educaci" in txt or "toda la vida" in txt:
        return "#0F385A"
    return "#1A3A5C"


def apply_cmi_filters(df: pd.DataFrame, linea_sel: str, objetivo_sel: str, nombre_q: str) -> tuple[pd.DataFrame, list]:
    """Apply strategic line/objective/name filters to PDI DataFrame.
    
    Args:
        df: PDI indicators DataFrame
        linea_sel: Selected line or "Todas"
        objetivo_sel: Selected objective or "Todos"
        nombre_q: Search query for indicator name
    
    Returns:
        Tuple of (filtered_df, active_filters_list)
    """
    if linea_sel != "Todas":
        df = df[df["Linea"] == linea_sel]
    if objetivo_sel != "Todos":
        df = df[df["Objetivo"] == objetivo_sel]
    if nombre_q.strip():
        df = df[df["Indicador"].astype(str).str.contains(nombre_q.strip(), case=False, na=False)]
    
    activos = []
    if linea_sel != "Todas":
        activos.append(f"Línea: {linea_sel}")
    if objetivo_sel != "Todos":
        activos.append(f"Objetivo: {objetivo_sel}")
    if nombre_q.strip():
        activos.append(f"Indicador contiene: {nombre_q.strip()}")
    
    return df, activos


def build_metrics_summary(df: pd.DataFrame, pdi_catalog: pd.DataFrame) -> dict:
    """Build summary metrics for the page.
    
    Args:
        df: Filtered PDI data
        pdi_catalog: PDI catalog
    
    Returns:
        Dictionary with summary metrics
    """
    total = len(df)
    con_dato = int(df["cumplimiento_pct"].notna().sum())
    promedio = float(df["cumplimiento_pct"].mean()) if con_dato else 0.0
    top_nivel = df["Nivel de cumplimiento"].value_counts().idxmax() if total else "Sin dato"
    n_lineas_vis = int(df["Linea"].nunique())
    n_obj_vis = int(df["Objetivo"].nunique())
    n_lineas_cat = int(pdi_catalog["Linea"].nunique()) if not pdi_catalog.empty else n_lineas_vis
    n_obj_cat = int(pdi_catalog["Objetivo"].nunique()) if not pdi_catalog.empty else n_obj_vis
    
    return {
        "total": total,
        "con_dato": con_dato,
        "promedio": promedio,
        "top_nivel": top_nivel,
        "n_lineas_vis": n_lineas_vis,
        "n_obj_vis": n_obj_vis,
        "n_lineas_cat": n_lineas_cat,
        "n_obj_cat": n_obj_cat,
    }


def get_pdi_lines_and_objectives(pdi_catalog: pd.DataFrame, df: pd.DataFrame, linea_sel: str) -> tuple[list, list]:
    """Get available strategic lines and objectives.
    
    Args:
        pdi_catalog: PDI catalog DataFrame
        df: PDI data DataFrame
        linea_sel: Selected line or "Todas"
    
    Returns:
        Tuple of (lines_list, objectives_list)
    """
    if not pdi_catalog.empty:
        lineas = sorted(pdi_catalog["Linea"].dropna().astype(str).unique().tolist())
        obj_pool = (
            pdi_catalog if linea_sel == "Todas"
            else pdi_catalog[pdi_catalog["Linea"] == linea_sel]
        )
        objetivos = sorted(obj_pool["Objetivo"].dropna().astype(str).unique().tolist())
    else:
        lineas = sorted(df["Linea"].dropna().astype(str).unique().tolist())
        df_obj = df if linea_sel == "Todas" else df[df["Linea"] == linea_sel]
        objetivos = sorted(df_obj["Objetivo"].dropna().astype(str).unique().tolist())
    
    return lineas, objetivos


def render_indicator_table_html(df_obj: pd.DataFrame) -> str:
    """Render PDI indicators as HTML table with formatted cells.
    
    Args:
        df_obj: DataFrame with indicators for one objective
    
    Returns:
        HTML string representation of table
    """
    cols = [c for c in ["Indicador", "Meta", "Ejecución", "Cumplimiento (%)"] if c in df_obj.columns]
    if df_obj.empty:
        return "<div style='padding:8px'>No hay indicadores para este objetivo.</div>"

    def _nivel_limpio(raw) -> str:
        txt = str(raw or "").strip()
        if not txt:
            return ""
        # Remove icon prefix if present
        parts = txt.split(" ", 1)
        if len(parts) == 2 and parts[0] in {"🔴", "🟡", "🟢", "🔵", "⚫", "⚪", "🚩", "⚑", "🏁", "🎌", "🏴", "🏳️"}:
            return parts[1].strip()
        return txt

    def _cumplimiento_display(row) -> str:
        val = pd.to_numeric(row.get("Cumplimiento (%)"), errors="coerce")
        nivel = _nivel_limpio(row.get("Nivel", ""))
        color = NIVEL_FLAG_COLORS.get(nivel, "#9E9E9E")
        icon = f"<span style='color:{color};font-weight:700'>⚑</span>"
        if pd.isna(val):
            return f"{icon} -".strip()
        return f"{icon} {float(val):.1f}%".strip()

    html = ["<table style='width:100%;border-collapse:collapse;font-size:0.9rem'>"]
    # Header
    html.append(
        "<tr style='background:#e9f7fb;color:#033;'><th style='padding:8px;border:1px solid #d0e9ef;text-align:left'>Indicador</th>"
    )
    for c in cols[1:]:
        html.append(
            f"<th style='padding:8px;border:1px solid #d0e9ef;text-align:center'>{c}</th>"
        )
    html.append("</tr>")
    # Rows
    for _, r in df_obj.iterrows():
        html.append("<tr>")
        html.append(
            f"<td style='padding:8px;border:1px solid #eef7fb'>{escape(str(r.get('Indicador','')))}</td>"
        )
        for c in cols[1:]:
            if c == "Cumplimiento (%)":
                display = _cumplimiento_display(r)
            else:
                val = r.get(c, "")
                display = f"{val}" if pd.notna(val) else ""
            align = "center"
            html.append(
                f"<td style='padding:8px;border:1px solid #eef7fb;text-align:{align}'>{display}</td>"
            )
        html.append("</tr>")
    html.append("</table>")
    return "".join(html)


# Wrapper functions for backward compatibility and aliases
def default_anio(anios: list[int]) -> int:
    """Get default year (wrapper for get_default_anio from config)."""
    from streamlit_app.pages.cmi_estrategico_config import get_default_anio
    return get_default_anio(anios)


def default_corte(anio: int | None) -> str:
    """Get default semester (wrapper for get_default_corte from config)."""
    from streamlit_app.pages.cmi_estrategico_config import get_default_corte
    return get_default_corte(anio)


def prepare_cmi_data(anio: int, mes: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Prepare CMI data for the selected year and month.
    
    Args:
        anio: Year
        mes: Month number
    
    Returns:
        Tuple of (filtered_cierres_df, pdi_catalog)
    """
    from services.strategic_indicators import load_cierres, load_pdi_catalog
    
    # Load base data
    cierres = load_cierres()
    pdi_catalog = load_pdi_catalog()
    
    # Filter by year and month
    if not cierres.empty:
        cierres = cierres[
            (pd.to_numeric(cierres.get("Anio", cierres.get("Año", pd.Series())), errors="coerce") == anio) &
            (pd.to_numeric(cierres.get("Mes_num", cierres.get("Mes", pd.Series())), errors="coerce") == mes)
        ]
    
    return cierres, pdi_catalog
