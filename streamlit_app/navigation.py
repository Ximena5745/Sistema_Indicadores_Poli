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

        menu_items = [
            ("◫  Resumen General", "Resumen General"),
            ("⌂  CMI Estratégico", "CMI Estratégico"),
            ("◷  CMI por Procesos", "CMI por Procesos"),
            ("◯  Informe por Procesos", "Informe por Procesos"),
            ("◐  Plan de Mejoramiento", "Plan de Mejoramiento"),
            (None, None),  # separador visual
            ("◧  Seguimiento Operativo", "Seguimiento Operativo"),
            ("◈  Gestión OM", "Gestión OM"),
        ]

        # Obtener menú actual desde sesión o parámetros
        menu = st.session_state.get("sidebar_nav_menu", "Resumen General")

        # Deep-link desde CTA: abrir directamente el módulo si viene en query params
        if hasattr(st, "query_params") and st.query_params.get("cmi_linea"):
            menu = "CMI Estratégico"

        for i, (label, value) in enumerate(menu_items):
            if label is None:
                st.markdown("<div class='sidebar-v2-empty'></div>", unsafe_allow_html=True)
                continue
            is_active = value == menu
            if st.button(
                label,
                key=f"sidebar_nav_btn_{i}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                menu = value
                st.session_state["sidebar_nav_menu"] = value

        st.session_state["sidebar_nav_menu"] = menu

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
            cmi_estrategico_tabulado,
            gestion_om,
            informe_por_procesos,
            plan_mejoramiento,
            resumen_general,
            resumen_por_proceso,
            seguimiento_reportes,
        )
    except (ImportError, ModuleNotFoundError):
        from .pages import (
            cmi_estrategico_tabulado,
            gestion_om,
            informe_por_procesos,
            plan_mejoramiento,
            resumen_general,
            resumen_por_proceso,
            seguimiento_reportes,
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
    elif menu == "Gestión OM":
        gestion_om.render()
    else:
        st.error(f"Página no encontrada: {menu}")
