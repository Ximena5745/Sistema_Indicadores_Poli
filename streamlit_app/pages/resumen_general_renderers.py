"""Rendering functions for resumen_general page."""

import pandas as pd
import streamlit as st
from streamlit_app.pages.resumen_general_config import (
    STATUS_COLORS, 
    LINEA_COLORS_BADGE
)
from streamlit_app.pages.resumen_general_utils import _norm_key


def _render_chip(value: int | str, label: str, color: str) -> None:
    """Render a small metric chip."""
    html = f"""
    <div style='
        display: inline-block;
        padding: 0.6rem 1rem;
        border-radius: 8px;
        background-color: {color};
        color: #FFFFFF;
        font-weight: 600;
        font-size: 0.9rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    '>
        <div style='font-size: 1.8rem; font-weight: 700;'>{value}</div>
        <div style='font-size: 0.75rem; opacity: 0.9;'>{label}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def _render_process_card(name: str, indicadores: int, variation: float, color: str) -> None:
    """Render a card showing process compliance."""
    variation_text = f"{variation:+.1f}%" if variation else "Sin variación"
    variation_color = "#16A34A" if variation >= 0 else "#DC2626"
    
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
            <span style='color: {variation_color};'>{variation_text}</span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def _render_strategy_card(title: str, count: int, cumplimiento: float,
                          sobrecumplimiento: int, cumplimiento_n: int,
                          alerta: int, peligro: int, icon: str = "📊",
                          color: str = "#0B5FFF", historico_data: pd.DataFrame | None = None) -> None:
    """Render a strategic line card with metrics and mini chart."""
    
    # Calculate percentages
    total = sobrecumplimiento + cumplimiento_n + alerta + peligro
    pct_sobre = (sobrecumplimiento / total * 100) if total > 0 else 0
    pct_cumpl = (cumplimiento_n / total * 100) if total > 0 else 0
    pct_alerta = (alerta / total * 100) if total > 0 else 0
    pct_peligro = (peligro / total * 100) if total > 0 else 0
    
    # Compliance bar colors
    html_bars = f"""
    <div style='display: flex; height: 20px; border-radius: 4px; overflow: hidden; margin: 0.5rem 0;'>
        <div style='width: {pct_sobre:.1f}%; background-color: #173D66;'></div>
        <div style='width: {pct_cumpl:.1f}%; background-color: #16A34A;'></div>
        <div style='width: {pct_alerta:.1f}%; background-color: #F59E0B;'></div>
        <div style='width: {pct_peligro:.1f}%; background-color: #D32F2F;'></div>
    </div>
    """
    
    html = f"""
    <div style='
        border-left: 4px solid {color};
        border-radius: 8px;
        padding: 1rem;
        background: #F8FAFC;
        margin-bottom: 1rem;
    '>
        <div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
            <span style='font-size: 1.8rem; margin-right: 0.5rem;'>{icon}</span>
            <div>
                <div style='font-weight: 600; font-size: 1rem;'>{title}</div>
                <div style='font-size: 0.85rem; color: #64748B;'>{count} indicadores</div>
            </div>
        </div>
        {html_bars}
        <div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; font-size: 0.8rem; margin-top: 0.5rem;'>
            <div>📈 {sobrecumplimiento} ({pct_sobre:.0f}%)</div>
            <div>✅ {cumplimiento_n} ({pct_cumpl:.0f}%)</div>
            <div>⚠️  {alerta} ({pct_alerta:.0f}%)</div>
            <div>❌ {peligro} ({pct_peligro:.0f}%)</div>
        </div>
        <div style='text-align: center; margin-top: 0.5rem; font-weight: 600; font-size: 1.1rem; color: {color};'>
            {cumplimiento:.1f}% Cumplimiento
        </div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


def _render_variation_table(title: str, rows: list[dict], positive: bool = True) -> None:
    """Render a table of variations (improvements or declines)."""
    if not rows:
        st.info(f"Sin datos de {title}")
        return
    
    st.subheader(title)
    
    table_data = []
    for row in rows[:10]:  # Limit to 10 rows
        change = float(row.get("change", 0) or 0)
        sign = "+" if change >= 0 else ""
        color = "#16A34A" if change >= 0 else "#DC2626"
        
        table_data.append({
            "Indicador": row.get("name", ""),
            "Línea": row.get("linea", ""),
            "Cambio": f"{sign}{change:.1f}%",
        })
    
    if table_data:
        df_table = pd.DataFrame(table_data)
        st.dataframe(df_table, use_container_width=True, hide_index=True)


def _render_tables_by_category(category: str, linea_summary: pd.DataFrame,
                               objetivo_df: pd.DataFrame | None = None,
                               pdi_estrategico: pd.DataFrame | None = None) -> None:
    """Render tables based on category (Indicadores, Proyectos, Retos, Consolidado)."""
    
    if category == "Indicadores":
        st.subheader("Resumen por Línea")
        if not linea_summary.empty:
            st.dataframe(linea_summary, use_container_width=True, hide_index=True)
    
    elif category == "Proyectos":
        st.subheader("Proyectos por Línea")
        if not linea_summary.empty:
            cols_show = ["Linea", "N_Proyectos", "Cumpl_Promedio"]
            cols_show = [c for c in cols_show if c in linea_summary.columns]
            st.dataframe(linea_summary[cols_show], use_container_width=True, hide_index=True)
    
    elif category == "Plan de Retos":
        st.subheader("Retos por Línea")
        if not linea_summary.empty:
            cols_show = ["Linea", "N_Indicadores", "Cumpl_Promedio"]
            cols_show = [c for c in cols_show if c in linea_summary.columns]
            st.dataframe(linea_summary[cols_show], use_container_width=True, hide_index=True)
    
    elif category == "Consolidado":
        st.subheader("Consolidado: Indicadores + Proyectos + Retos")
        if not linea_summary.empty:
            cols_show = [c for c in ["Linea", "N_Indicadores", "N_Proyectos", "N_Retos", "Cumpl_Promedio"]
                        if c in linea_summary.columns]
            st.dataframe(linea_summary[cols_show], use_container_width=True, hide_index=True)
    
    # Show objective details if available
    if objetivo_df is not None and not objetivo_df.empty:
        st.subheader("Objetivos Estratégicos")
        cols_show = [c for c in ["Linea", "Objetivo", "cumplimiento_pct"]
                    if c in objetivo_df.columns]
        if cols_show:
            st.dataframe(objetivo_df[cols_show], use_container_width=True, hide_index=True)


def _build_ia_rows(rows: list[dict]) -> str:
    """Build HTML table rows for IA narrative insights."""
    if not rows:
        return "<tr><td colspan='2' style='color:#94A3B8;'>Sin insights disponibles</td></tr>"
    
    out = ""
    for row in rows:
        text = str(row.get("text", ""))
        sentiment = row.get("sentiment", "neutral")
        color = "#16A34A" if sentiment == "positive" else "#DC2626" if sentiment == "negative" else "#F59E0B"
        
        out += f"""
        <tr>
            <td style='color:{color}; font-weight:600; width:30%;'>{sentiment.upper()}</td>
            <td style='color:#334155;'>{text}</td>
        </tr>
        """
    
    return out


def _build_trend_rows_with_linea(rows: list[dict], positive: bool) -> str:
    """Build HTML table rows for trends with strategic line badges."""
    if not rows:
        return "<tr><td colspan='3' style='color:#94A3B8;font-size:0.8rem;padding:0.6rem;'>Sin datos comparativos</td></tr>"
    
    out = ""
    for row in rows[:5]:
        change = float(row.get("change", 0) or 0)
        sign = "+" if change >= 0 else ""
        color = "#16A34A" if change >= 0 else "#DC2626"
        linea = row.get("linea", "")
        
        lc = _norm_key(linea)
        bg_col, txt_col = LINEA_COLORS_BADGE.get(lc, ("#64748B", "#FFFFFF"))
        
        out += f"""
        <tr>
            <td>{row.get("name", "")}</td>
            <td style='background-color:{bg_col}; color:{txt_col}; padding:0.3rem 0.6rem; border-radius:4px;'>{linea}</td>
            <td style='color:{color};font-weight:700;'>{sign}{change:.1f}%</td>
        </tr>
        """
    
    return out
