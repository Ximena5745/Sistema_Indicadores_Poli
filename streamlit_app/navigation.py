"""
Navigation and routing system for Streamlit app.

Manages sidebar navigation, menu selection, and page routing to different modules.
"""
from datetime import datetime
import streamlit as st


def render_sidebar_navigation() -> str:
    """
    Renderiza el sidebar de navegación y retorna el menú seleccionado.
    
    Returns:
        str: Nombre del menú seleccionado (ej: "Resumen General", "CMI Estratégico")
    """
    with st.sidebar:
        st.markdown(
            """
            <div class='sidebar-v2-header'>
              <div class='sidebar-v2-logo'>
                <svg width='22' height='22' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'>
                  <path d='M4 19V5M4 19H20M8 14L11 11L14 13L20 7' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/>
                </svg>
              </div>
              <div class='sidebar-v2-brand'>
                <div class='sidebar-v2-title'>Sistema de Indicadores</div>
                <div class='sidebar-v2-subtitle'>POLITÉCNICO GRANCOLOMBIANO</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        menu_labels = [
            "◫  Resumen General",
            "⌂  CMI Estratégico",
            "◷  CMI por Procesos",
            "◯  Informe por Procesos",
            "◐  Plan de Mejoramiento",
            "─────────────────────",
            "◧  Seguimiento Operativo",
            "△  Indicadores en Riesgo",
        ]
        menu_map = {
            "◫  Resumen General": "Resumen General",
            "⌂  CMI Estratégico": "CMI Estratégico",
            "◷  CMI por Procesos": "CMI por Procesos",
            "◯  Informe por Procesos": "Informe por Procesos",
            "◐  Plan de Mejoramiento": "Plan de Mejoramiento",
            "─────────────────────": "divider",
            "◧  Seguimiento Operativo": "Seguimiento Operativo",
            "△  Indicadores en Riesgo": "Indicadores en Riesgo",
        }

        # Filtrar opciones válidas (sin separador visual)
        display_options = [opt for opt in menu_labels if not opt.startswith("─")]
        current_index = 0
        
        # Obtener menú actual desde sesión o parámetros
        menu = "Resumen General"
        
        # Deep-link desde CTA: abrir directamente el módulo si viene en query params
        if hasattr(st, "query_params") and st.query_params.get("cmi_linea"):
            menu = "CMI Estratégico"
            st.session_state["sidebar_nav"] = "⌂  CMI Estratégico"
        
        if menu in menu_map.values():
            for i, opt in enumerate(display_options):
                if menu_map.get(opt) == menu:
                    current_index = i
                    break

        selected_menu = st.radio(
            "navegación",
            options=display_options,
            index=current_index,
            key="sidebar_nav",
            label_visibility="collapsed",
        )
        menu = menu_map[selected_menu]

        # Footer con información de actualización
        updated_at = datetime.now().strftime("%d/%m/%Y %H:%M")
        st.markdown(
            f"""
            <div class='sidebar-v2-update'>
                <div class='title'>Fecha de actualización</div>
                <div class='value'>{updated_at}</div>
            </div>
            <div class='sidebar-v2-footer'>
                Gerencia de Planeación y Gestión Institucional
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    return menu


def router(menu: str):
    """
    Enruta el menú seleccionado a la página correspondiente.
    
    Args:
        menu: Nombre del menú seleccionado
        
    Raises:
        ModuleNotFoundError: Si la página no puede ser importada
    """
    # Importar páginas bajo demanda para evitar circular imports
    try:
        from streamlit_app.pages import (
            cmi_estrategico,
            cmi_estrategico_tabulado,
            gestion_om,
            informe_por_procesos,
            plan_mejoramiento,
            resumen_general,
            resumen_por_proceso,
            seguimiento_reportes,
            tablero_operativo,
            pdi_acreditacion,
        )
    except (ImportError, ModuleNotFoundError):
        from .pages import (
            cmi_estrategico,
            cmi_estrategico_tabulado,
            gestion_om,
            informe_por_procesos,
            plan_mejoramiento,
            resumen_general,
            resumen_por_proceso,
            seguimiento_reportes,
            tablero_operativo,
            pdi_acreditacion,
        )

    # Routing
    if menu == "Resumen General":
        resumen_general.render()
    elif menu == "CMI Estratégico":
        cmi_estrategico_tabulado.render()
    elif menu == "CMI por Procesos":
        resumen_por_proceso.render()
    elif menu == "Informe por Procesos":
        informe_por_procesos.render()
    elif menu == "Plan de Mejoramiento":
        plan_mejoramiento.render()
    elif menu == "Seguimiento Operativo":
        seguimiento_reportes.render()
    elif menu == "Indicadores en Riesgo":
        tablero_operativo.render()
    else:
        st.error(f"Página no encontrada: {menu}")
