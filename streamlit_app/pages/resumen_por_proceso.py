"""
Resumen por Proceso page - Process summary dashboard.

Main orchestration module combining data loading, filtering, visualization, and rendering.
"""

from pathlib import Path
import streamlit as st
import pandas as pd

try:
    from components.charts import grafico_historico_indicador
    from streamlit_app.services.data_service import DataService
    from streamlit_app.utils.formatting import formatear_meta_ejecucion_df
    from services.cmi_filters import filter_df_for_procesos
    from core.proceso_types import TIPOS_PROCESO, get_tipo_color
    from streamlit_app.components.filter_panel import render_filter_panel
    from streamlit_app.components.cmi_tabs.tab_alertas import render_tab_alertas
except (ImportError, ModuleNotFoundError):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from components.charts import grafico_historico_indicador
    from streamlit_app.services.data_service import DataService
    from streamlit_app.utils.formatting import formatear_meta_ejecucion_df
    from services.cmi_filters import filter_df_for_procesos
    from core.proceso_types import TIPOS_PROCESO, get_tipo_color
    from streamlit_app.components.filter_panel import render_filter_panel
    from streamlit_app.components.cmi_tabs.tab_alertas import render_tab_alertas

from streamlit_app.pages.resumen_por_proceso_config import (
    MESES_OPCIONES, COMPLIANCE_LEVELS
)
from streamlit_app.pages.resumen_por_proceso_utils_transforms import (
    _ensure_nivel_cumplimiento, _compute_indicador_summary,
    _available_months_with_data, _default_month_num, _process_counts_cmi,
    _cumpl_label, _status_color_for_pct, _to_float, _mes_to_num, _norm_text,
    _norm_key, _categoria_por_pct, _cumpl_icon, _cumpl_delta
)
from streamlit_app.pages.resumen_por_proceso_utils_data import (
    _prepare_tracking, _load_indicadores_por_cmi,
    _load_calidad_data, _load_analisis_indicadores, _load_analisis_periodos,
    _latest_per_indicator, _build_indicator_yearly
)
from streamlit_app.pages.resumen_por_proceso_visuals import (
    _render_cmi_por_cmi_summary_charts, _build_processo_compliance_chart,
    _build_level_distribution_chart
)
from streamlit_app.pages.resumen_por_proceso_renderers import (
    _section_title, _render_resumen_banner, _render_resumen_overview_cards,
    _render_indicadores_summary_cards, _render_indicadores_subproceso_cards,
    _build_indicadores_table, _render_process_card
)


def render() -> None:
    """Main render function for resumen_por_proceso dashboard."""
    
    # Banner
    _render_resumen_banner()
    
    # Load base data
    ds = DataService()
    try:
        tracking_df = ds.get_tracking_data()
        map_df = ds.get_process_map()
    except Exception:
        st.error("No se pudieron cargar los datos de seguimiento")
        return
    
    if tracking_df.empty or map_df.empty:
        st.warning("No hay datos disponibles para mostrar")
        return
    
    # Filter panel
    anos_disponibles = sorted(tracking_df["Anio"].dropna().unique().astype(int).tolist())
    if not anos_disponibles:
        st.error("No hay años disponibles en los datos")
        return
    
    sels = render_filter_panel(
        filters=[
            {
                "key": "anio",
                "label": "Año",
                "type": "selectbox",
                "options": anos_disponibles,
                "default": max(anos_disponibles),
                "include_all": False,
            },
            {
                "key": "mes",
                "label": "Mes",
                "type": "selectbox",
                "options": MESES_OPCIONES,
                "default": "Diciembre",
                "include_all": False,
            },
        ],
        title="Filtros",
        key_prefix="rpp",
        n_cols=2,
    )
    
    year_sel = sels.get("anio", max(anos_disponibles))
    mes_sel = sels.get("mes", "Diciembre")
    mes_num = MESES_OPCIONES.index(mes_sel) + 1 if mes_sel in MESES_OPCIONES else 12
    
    # Prepare data
    df_prep = _prepare_tracking(tracking_df, map_df, mes_num)
    df_prep = _ensure_nivel_cumplimiento(df_prep)
    df_prep = filter_df_for_procesos(df_prep)
    
    if df_prep.empty:
        st.info("No hay datos para los filtros seleccionados")
        return
    
    # Summary metrics
    summary = _compute_indicador_summary(df_prep)
    n_procesos = df_prep["Proceso_padre"].nunique() if "Proceso_padre" in df_prep.columns else 0
    n_subprocesos = df_prep["Subproceso"].nunique() if "Subproceso" in df_prep.columns else 0
    
    _section_title("Resumen General")
    _render_resumen_overview_cards(summary, n_procesos, n_subprocesos)
    
    # Create tabs
    tab_resumen, tab_procesos, tab_indicadores, tab_alertas, tab_analisis = st.tabs([
        "📊 Resumen",
        "🏭 Procesos",
        "📈 Indicadores",
        "🚨 Alertas",
        "🔍 Análisis"
    ])
    
    # Tab 1: Resumen
    with tab_resumen:
        _section_title("Indicadores por Categor ía")
        _render_indicadores_summary_cards(summary)
        
        col1, col2 = st.columns(2)
        with col1:
            fig_dist = _build_level_distribution_chart(df_prep)
            st.plotly_chart(fig_dist, use_container_width=True)
        with col2:
            fig_proc = _build_processo_compliance_chart(df_prep)
            st.plotly_chart(fig_proc, use_container_width=True)
    
    # Tab 2: Procesos
    with tab_procesos:
        _section_title("Cumplimiento por Proceso")
        
        if "Proceso_padre" in df_prep.columns:
            proceso_summary = df_prep.groupby("Proceso_padre").agg({
                "cumplimiento_pct": "mean",
                "Indicador": "count"
            }).reset_index()
            proceso_summary.columns = ["Proceso", "Cumplimiento", "Indicadores"]
            
            for _, row in proceso_summary.iterrows():
                _render_process_card(
                    row["Proceso"],
                    int(row["Indicadores"]),
                    row["Cumplimiento"],
                    color=_status_color_for_pct(row["Cumplimiento"])
                )
        else:
            st.info("Sin datos de procesos")
    
    # Tab 3: Indicadores
    with tab_indicadores:
        _section_title("Detalle de Indicadores")
        
        df_latest = _latest_per_indicator(df_prep)
        if not df_latest.empty:
            _render_indicadores_subproceso_cards(df_latest)
            
            st.markdown("### Tabla de Indicadores")
            table_df = _build_indicadores_table(df_latest)
            if not table_df.empty:
                st.dataframe(table_df, use_container_width=True, hide_index=True)
        else:
            st.info("Sin indicadores disponibles")
    
    # Tab 4: Alertas
    with tab_alertas:
        try:
            render_tab_alertas()
        except Exception:
            st.info("No se pudo cargar la sección de alertas")
    
    # Tab 5: Análisis
    with tab_analisis:
        _section_title("Análisis Avanzado")
        
        st.markdown("#### Análisis de Cumplimiento")
        st.write(f"**Período**: {mes_sel} {year_sel}")
        st.write(f"**Total Indicadores**: {summary.get('total', 0)}")
        st.write(f"**Cumplimiento Promedio**: {summary.get('promedio', 0):.1f}%")
        
        # Compliance breakdown
        cols = st.columns(4)
        with cols[0]:
            st.metric("🔵 Sobrecumplimiento", summary.get("sobrecumplimiento", 0))
        with cols[1]:
            st.metric("🟢 Cumplimiento", summary.get("cumplimiento", 0))
        with cols[2]:
            st.metric("🟡 Alerta", summary.get("alerta", 0))
        with cols[3]:
            st.metric("🔴 Peligro", summary.get("peligro", 0))


# Re-exports for backward compatibility with tests
_prepare_tracking_main = _prepare_tracking
_compute_summary = _compute_indicador_summary
_ensure_nivel = _ensure_nivel_cumplimiento

# Stub functions for backward compatibility with other modules
def _build_indicator_history(df, indicador):
    """Stub: Build indicator history data."""
    if df.empty or "Indicador" not in df.columns:
        return df
    return df[df["Indicador"] == indicador].sort_values("fecha", ascending=False) if "fecha" in df.columns else df[df["Indicador"] == indicador]

def _latest_per_indicator(df):
    """Filter to latest record per indicator."""
    if df.empty or "Indicador" not in df.columns:
        return df
    return df.sort_values("Id", ascending=False).drop_duplicates("Indicador", keep="first")

def _render_auditoria_tab():
    """Stub: Render audit tab."""
    st.info("Sección de auditoría")

def _render_calidad_kpis_cards(df):
    """Stub: Render quality KPI cards."""
    st.info("Tarjetas de KPIs de calidad")

def _render_indicadores_subproceso_enhanced(df, **kwargs):
    """Stub: Enhanced subprocess indicators rendering."""
    st.info("Indicadores por subproceso mejorado")
