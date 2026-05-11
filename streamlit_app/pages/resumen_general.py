"""
Resumen General page - Strategic indicators dashboard for PDI 2022-2026.

Main orchestration module for the resumen_general dashboard.
Combines data loading, filtering, visualization, and rendering.
"""

from pathlib import Path
import streamlit as st
import pandas as pd

try:
    from services.strategic_indicators import (
        preparar_pdi_con_cierre, load_pdi_catalog, load_cierres, load_worksheet_flags
    )
    from core.config import DATA_OUTPUT
    from core.proceso_types import TIPOS_PROCESO, get_tipo_color
    from core.calculos import simple_categoria_desde_porcentaje
    from core.semantica import categorizar_cumplimiento
    from streamlit_app.services.data_service import DataService
    from services.cmi_filters import filter_df_for_cmi_estrategico, filter_df_for_cmi_procesos
    from streamlit_app.components.filter_panel import render_filter_panel
except (ImportError, ModuleNotFoundError):
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from services.strategic_indicators import (
        preparar_pdi_con_cierre, load_pdi_catalog, load_cierres, load_worksheet_flags
    )
    from core.config import DATA_OUTPUT
    from core.proceso_types import TIPOS_PROCESO, get_tipo_color
    from core.calculos import simple_categoria_desde_porcentaje
    from core.semantica import categorizar_cumplimiento
    from streamlit_app.services.data_service import DataService
    from services.cmi_filters import filter_df_for_cmi_estrategico, filter_df_for_cmi_procesos
    from streamlit_app.components.filter_panel import render_filter_panel

from streamlit_app.pages.resumen_general_config import STRATEGIC_DEFS, LINEA_COLORS
from streamlit_app.pages.resumen_general_utils import (
    _load_consolidado_cierres,
    _load_plan_retos_data,
    _load_plan_retos_planes,
    _build_linea_summary_from_df,
    _build_linea_summary_from_retos,
    _get_proyectos_ids,
    _merge_consolidado_summaries,
    _available_years,
    _available_months_for_year,
    _latest_month_for_year,
    _filter_consolidado_by_year_month,
    _norm_key,
)
from streamlit_app.pages.resumen_general_visuals import (
    _build_sunburst,
    _build_gantt_for_proyectos,
)
from streamlit_app.pages.resumen_general_renderers import (
    _render_chip,
    _render_strategy_card,
    _render_variation_table,
    _render_tables_by_category,
)
from streamlit_app.pages.resumen_general_styles import _inject_dashboard_styles


def _load_base_data_by_category(category: str, year: int, use_all_years: bool = False):
    """Load and prepare data based on selected category.
    
    Returns: (linea_summary, objetivo_df, pdi_base_df, historico_df, pdi_estrategico)
    """
    linea_summary = pd.DataFrame()
    objetivo_df = pd.DataFrame()
    pdi_base_df = pd.DataFrame()
    historico_df = pd.DataFrame()
    pdi_estrategico = pd.DataFrame()
    
    if category == "Indicadores":
        # Load strategic PDI indicators
        pdi_base_df = preparar_pdi_con_cierre(year, 12)
        if not pdi_base_df.empty:
            pdi_estrategico = filter_df_for_cmi_estrategico(pdi_base_df.copy())
            linea_summary = _build_linea_summary_from_df(pdi_estrategico, unique_count_col="Id")
            objetivo_df = pdi_estrategico[["Linea", "Objetivo", "cumplimiento_pct"]].drop_duplicates()
            
            if use_all_years:
                try:
                    historico_df = preparar_pdi_con_cierre(year, 12)
                except Exception:
                    pass
    
    elif category == "Proyectos":
        # Load projects from cierres
        try:
            proyectos_ids = _get_proyectos_ids()
            cierres_df = load_cierres()
            if not cierres_df.empty and proyectos_ids:
                cierres_df = cierres_df[cierres_df["Id"].astype(str).str.strip().isin(proyectos_ids)]
                
                # Add line and objective information
                try:
                    flags_df = load_worksheet_flags()
                    if not flags_df.empty:
                        cierres_df = cierres_df.merge(
                            flags_df[["Id", "Linea", "Objetivo"]],
                            on="Id", how="left"
                        )
                except Exception:
                    pass
                
                linea_summary = _build_linea_summary_from_df(cierres_df)
                objetivo_df = cierres_df[["Linea", "Objetivo", "cumplimiento_pct"]].drop_duplicates()
        except Exception:
            pass
    
    elif category == "Plan de Retos":
        # Load plan de retos
        linea_df, obj_df = _load_plan_retos_data(int(year))
        planes_df = _load_plan_retos_planes(int(year))
        
        if not linea_df.empty:
            linea_summary = _build_linea_summary_from_retos(linea_df, obj_df, planes_df)
            objetivo_df = obj_df if not obj_df.empty else pd.DataFrame()
    
    elif category == "Consolidado":
        # Load and merge all three sources
        try:
            # Indicadores
            pdi_base_df = preparar_pdi_con_cierre(int(year), 12)
            pdi_estrategico = filter_df_for_cmi_estrategico(pdi_base_df.copy()) if not pdi_base_df.empty else pd.DataFrame()
            s1 = _build_linea_summary_from_df(pdi_estrategico, unique_count_col="Id")
            o1 = pdi_estrategico[["Linea", "Objetivo"]] if not pdi_estrategico.empty else pd.DataFrame()
            
            # Proyectos
            proyectos_ids = _get_proyectos_ids()
            cierres_df = load_cierres() if not pdi_base_df.empty else pd.DataFrame()
            if not cierres_df.empty and proyectos_ids:
                cierres_df = cierres_df[cierres_df["Id"].astype(str).str.strip().isin(proyectos_ids)]
                try:
                    flags_df = load_worksheet_flags()
                    if not flags_df.empty:
                        cierres_df = cierres_df.merge(flags_df[["Id", "Linea", "Objetivo"]], on="Id", how="left")
                except Exception:
                    pass
                s2 = _build_linea_summary_from_df(cierres_df)
                o2 = cierres_df[["Linea", "Objetivo"]] if not cierres_df.empty else pd.DataFrame()
            else:
                s2 = pd.DataFrame()
                o2 = pd.DataFrame()
            
            # Retos
            linea_df, obj_df = _load_plan_retos_data(int(year))
            planes_df = _load_plan_retos_planes(int(year))
            s3 = _build_linea_summary_from_retos(linea_df, obj_df, planes_df) if not linea_df.empty else pd.DataFrame()
            o3 = obj_df if not obj_df.empty else pd.DataFrame()
            
            # Merge summaries
            linea_summary, objetivo_df = _merge_consolidado_summaries(s1, s2, s3, o1, o2, o3)
        except Exception:
            pass
    
    return linea_summary, objetivo_df, pdi_base_df, historico_df, pdi_estrategico


def render() -> None:
    """Main render function for resumen_general dashboard."""
    
    # Inject custom styles
    _inject_dashboard_styles()
    
    # Header
    st.markdown("""
    <div class='rg-header'>
        <h1>📊 Plan de Desarrollo Institucional 2022–2026</h1>
        <p>Seguimiento estratégico de indicadores, proyectos y retos institucionales</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Filter panel
    sels = render_filter_panel(
        filters=[
            {
                "key": "anio",
                "label": "Año",
                "type": "selectbox",
                "options": [2022, 2023, 2024, 2025, 2026],
                "default": 2025,
                "include_all": False,
            },
            {
                "key": "vista",
                "label": "Vista",
                "type": "selectbox",
                "options": ["Indicadores", "Proyectos", "Plan de Retos", "Consolidado"],
                "default": "Indicadores",
                "include_all": False,
            },
        ],
        title="Filtros",
        key_prefix="rg",
        n_cols=2,
    )
    
    year_estrategico = sels.get("anio", 2025)
    categoria = sels.get("vista", "Indicadores")
    
    # Load data
    linea_summary, objetivo_df, pdi_base_df, historico_df, pdi_estrategico = _load_base_data_by_category(
        categoria, int(year_estrategico), use_all_years=False
    )
    
    if linea_summary.empty:
        st.warning(f"No hay datos disponibles para {categoria} en {year_estrategico}.")
        return
    
    # Panel container
    st.markdown("<div class='rg-panel'>", unsafe_allow_html=True)
    
    # Metrics summary
    st.markdown("### Métricas Generales")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Indicadores", len(linea_summary))
    with col2:
        avg_cumpl = linea_summary.get("Cumpl_Promedio", pd.Series()).mean() if "Cumpl_Promedio" in linea_summary.columns else 0
        st.metric("Cumplimiento Promedio", f"{avg_cumpl:.1f}%")
    with col3:
        n_sobrecumpl = linea_summary.get("Sobrecumplimiento", pd.Series()).sum() if "Sobrecumplimiento" in linea_summary.columns else 0
        st.metric("Sobrecumplimiento", int(n_sobrecumpl))
    
    # Strategic line cards
    st.markdown("### Líneas Estratégicas")
    
    cols = st.columns(2)
    for idx, card_def in enumerate(STRATEGIC_DEFS):
        col = cols[idx % 2]
        
        linea_norm = card_def["key"]
        row = None
        
        # Find matching row in summary
        if not linea_summary.empty and "Linea" in linea_summary.columns:
            for _, r in linea_summary.iterrows():
                if _norm_key(str(r.get("Linea", ""))) == linea_norm:
                    row = r
                    break
        
        with col:
            if row is not None:
                try:
                    n_ind = int(float(row.get("N_Indicadores", 0) or 0))
                except (ValueError, TypeError):
                    n_ind = 0
                
                try:
                    cumpl = float(row.get("Cumpl_Promedio", 0) or 0)
                except (ValueError, TypeError):
                    cumpl = 0.0
                
                try:
                    sobre = int(float(row.get("Sobrecumplimiento", 0) or 0))
                except (ValueError, TypeError):
                    sobre = 0
                
                try:
                    cumpl_n = int(float(row.get("Cumplimiento", 0) or 0))
                except (ValueError, TypeError):
                    cumpl_n = 0
                
                try:
                    alerta = int(float(row.get("Alerta", 0) or 0))
                except (ValueError, TypeError):
                    alerta = 0
                
                try:
                    peligro = int(float(row.get("Peligro", 0) or 0))
                except (ValueError, TypeError):
                    peligro = 0
                
                _render_strategy_card(
                    title=card_def["label"],
                    count=n_ind,
                    cumplimiento=cumpl,
                    sobrecumplimiento=sobre,
                    cumplimiento_n=cumpl_n,
                    alerta=alerta,
                    peligro=peligro,
                    icon=card_def["icon"],
                    color=card_def["color"]
                )
            else:
                st.info(f"{card_def['label']}: Sin datos")
    
    # Sunburst chart
    if not pdi_estrategico.empty:
        st.markdown("### Jerarquía de Objetivos")
        fig_sunburst = _build_sunburst(pdi_estrategico)
        st.plotly_chart(fig_sunburst, use_container_width=True)
    
    # Tables by category
    st.markdown("### Detalles")
    _render_tables_by_category(categoria, linea_summary, objetivo_df, pdi_estrategico)
    
    st.markdown("</div>", unsafe_allow_html=True)


# Re-exports for backward compatibility with tests
_load_consolidado = _load_consolidado_cierres
_load_retos_data = _load_plan_retos_data
_build_summary = _build_linea_summary_from_df
