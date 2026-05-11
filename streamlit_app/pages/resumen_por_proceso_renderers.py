"""Rendering functions (Streamlit components) for resumen_por_proceso page."""

import streamlit as st
import pandas as pd

from streamlit_app.pages.resumen_por_proceso_config import NIVELES_COLORS
from streamlit_app.pages.resumen_por_proceso_utils_transforms import (
    _cumpl_icon, _cumpl_label, _status_color_for_pct
)


def _section_title(title: str, level: int = 3, accent: str = "#0B5FFF") -> None:
    """Render section title with colored left border."""
    html = f"""
    <div style='
        border-left: 4px solid {accent};
        padding-left: 1rem;
        margin-bottom: 1rem;
        margin-top: 1.5rem;
    '>
        <h{level} style='margin: 0; color: #0F385A; font-weight: 600;'>{title.upper()}</h{level}>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def _render_process_card(name: str, indicadores: int, cumplimiento: float,
                         delta: str = "", color: str = "#0B5FFF") -> None:
    """Render process summary card."""
    
    delta_html = f"<div style='color: #6E7781; font-size: 0.85rem;'>{delta}</div>" if delta else ""
    cumpl_text = f"{cumplimiento:.1f}%" if cumplimiento else "—"
    
    html = f"""
    <div style='
        border: 1px solid {color};
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        background: #FFFFFF;
    '>
        <div style='
            color: {color};
            font-weight: 600;
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
        '>{name}</div>
        <div style='
            display: flex;
            justify-content: space-between;
            font-size: 0.9rem;
        '>
            <span>Indicadores: <strong>{indicadores}</strong></span>
            <span style='color: {_status_color_for_pct(cumplimiento)};'><strong>{cumpl_text}</strong></span>
        </div>
        {delta_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def _render_resumen_overview_cards(summary: dict, n_procesos: int = 0,
                                   n_subprocesos: int = 0) -> None:
    """Render 6 KPI cards: total, metrics, levels."""
    
    cols = st.columns(6)
    
    cards = [
        ("📊 Indicadores", summary.get("total", 0), "#0B5FFF"),
        ("🔵 Sobrecumpl.", summary.get("sobrecumplimiento", 0), "#6699FF"),
        ("🟢 Cumplimiento", summary.get("cumplimiento", 0), "#2E7D32"),
        ("🟡 Alerta", summary.get("alerta", 0), "#F9A825"),
        ("🔴 Peligro", summary.get("peligro", 0), "#C62828"),
        ("📈 Promedio", f"{summary.get('promedio', 0):.1f}%", "#1FB2DE"),
    ]
    
    for col, (label, value, color) in zip(cols, cards):
        with col:
            st.metric(label, value)


def _render_resumen_banner() -> None:
    """Render main banner with health status."""
    
    html = """
    <div style='
        background: linear-gradient(135deg, #0F385A 0%, #1A5F7A 100%);
        color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 14px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(15, 56, 90, 0.15);
    '>
        <h2 style='margin: 0 0 0.5rem 0; font-size: 1.8rem;'>📊 Resumen de Procesos</h2>
        <p style='margin: 0; opacity: 0.9; font-size: 0.95rem;'>
            Dashboard operacional con indicadores de procesos, cumplimiento y alertas
        </p>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


def _render_indicadores_summary_cards(summary: dict) -> None:
    """Render indicator summary cards."""
    
    cols = st.columns(6)
    
    metrics = [
        ("Total", summary.get("total", 0), "#0B5FFF"),
        ("Sobrecumpl.", summary.get("sobrecumplimiento", 0), "#6699FF"),
        ("Cumplimiento", summary.get("cumplimiento", 0), "#2E7D32"),
        ("Alerta", summary.get("alerta", 0), "#F9A825"),
        ("Peligro", summary.get("peligro", 0), "#C62828"),
        ("Promedio", f"{summary.get('promedio', 0):.1f}%", "#1FB2DE"),
    ]
    
    for col, (label, value, color) in zip(cols, metrics):
        with col:
            st.metric(label, value)


def _build_ia_rows_rpp(rows: list[dict]) -> str:
    """Build HTML table rows for AI insights."""
    
    if not rows:
        return "<tr><td colspan='2'>Sin datos</td></tr>"
    
    out = ""
    for row in rows[:5]:
        proceso = str(row.get("proceso", ""))
        cambio = str(row.get("cambio", ""))
        color = "#2E7D32" if float(cambio.replace("%", "")) >= 0 else "#C62828"
        
        out += f"""
        <tr>
            <td>{proceso}</td>
            <td style='color: {color}; font-weight: 600;'>{cambio}</td>
        </tr>
        """
    
    return out


def _render_indicadores_subproceso_cards(df: pd.DataFrame, items_per_page: int = 15) -> None:
    """Render indicator cards by subprocess with pagination."""
    
    if df.empty:
        st.info("Sin datos disponibles")
        return
    
    # Simple display without pagination (full pagination would need more code)
    for idx, row in df.head(items_per_page).iterrows():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"**{row.get('Indicador', 'Sin nombre')}**")
        with col2:
            cumpl = row.get("cumplimiento_pct", 0)
            st.write(_cumpl_label(cumpl))
        with col3:
            st.write(row.get("Subproceso", "—"))


def _build_info_table(df_latest: pd.DataFrame) -> pd.DataFrame:
    """Build information table: Indicator, Meta, Ejecucion, Cumplimiento."""
    
    if df_latest.empty:
        return pd.DataFrame()
    
    cols_display = []
    for col in ["Indicador", "Meta", "Ejecucion", "cumplimiento_pct"]:
        if col in df_latest.columns:
            cols_display.append(col)
    
    if not cols_display:
        return df_latest
    
    return df_latest[cols_display].copy()


def _build_indicadores_table(df_latest: pd.DataFrame) -> pd.DataFrame:
    """Build detailed indicators table."""
    
    if df_latest.empty:
        return pd.DataFrame()
    
    cols = []
    for col in ["Subproceso", "Indicador", "Meta", "Ejecucion", "cumplimiento_pct"]:
        if col in df_latest.columns:
            cols.append(col)
    
    if not cols:
        return df_latest
    
    return df_latest[cols].rename(columns={
        "cumplimiento_pct": "Cumplimiento (%)"
    })


def _build_propuestos(df_latest: pd.DataFrame, process_name: str = "") -> pd.DataFrame:
    """Build proposed actions table."""
    
    if df_latest.empty:
        return pd.DataFrame()
    
    cols = []
    for col in ["Indicador", "Plan_mejora", "PDI", "SGA", "Retos"]:
        if col in df_latest.columns:
            cols.append(col)
    
    if not cols:
        return pd.DataFrame({"Indicador": ["—"]})
    
    return df_latest[cols] if cols else pd.DataFrame()
