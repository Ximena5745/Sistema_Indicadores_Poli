from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Sistema de Indicadores", layout="wide")


def load_css(file_path):
    """Carga un archivo CSS y lo retorna como una cadena."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def _inject_styles():
    """Inyecta estilos locales con ruta robusta para local y cloud."""
    base = Path(__file__).resolve().parent / "styles"
    css_files = ["styles.css", "main.css"]
    for css_name in css_files:
        css_path = base / css_name
        if not css_path.exists():
            css_path = Path(f"streamlit_app/styles/{css_name}")
        if css_path.exists():
            styles = load_css(str(css_path))
            st.markdown(f"<style>{styles}</style>", unsafe_allow_html=True)


def main():
    _inject_styles()

    # Importar páginas bajo demanda para evitar circular imports
    try:
        from streamlit_app.pages import (
            cmi_estrategico,
            gestion_om,
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
            gestion_om,
            plan_mejoramiento,
            resumen_general,
            resumen_por_proceso,
            seguimiento_reportes,
            tablero_operativo,
            pdi_acreditacion,
        )

    # Valor seguro por defecto
    menu = "Resumen General"

    # Configuración del sidebar
    try:
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
                    <div class='sidebar-v2-subtitle'>POLITÉCNICA GRANCOLOMBIANA</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.text_input(
                "Buscar indicador",
                placeholder="Buscar indicador...",
                key="sidebar_search",
                label_visibility="collapsed",
            )

            st.markdown("<div class='sidebar-v2-section'>PRINCIPAL</div>", unsafe_allow_html=True)

            menu_labels = [
                "◫  Resumen General",
                "⌂  Resumen Estratégico",
                "◷  Resumen por Procesos",
                "◧  Seguimiento Operativo",
                "◌  Indicadores en Riesgo",
                "△  Alertas Activas",
                "⚙  Configuración",
            ]
            menu_map = {
                "◫  Resumen General": "Resumen General",
                "⌂  Resumen Estratégico": "Resumen Estratégico",
                "◷  Resumen por Procesos": "Resumen por Procesos",
                "◧  Seguimiento Operativo": "Seguimiento Operativo",
                "◌  Indicadores en Riesgo": "Indicadores en Riesgo",
                "△  Alertas Activas": "Alertas Activas",
                "⚙  Configuración": "Configuración",
            }

            current_index = menu_labels.index("◫  Resumen General")
            if menu in menu_map.values():
                current_index = list(menu_map.values()).index(menu)

            selected_menu = st.radio(
                "Navegación principal",
                options=menu_labels,
                index=current_index,
                key="sidebar_main_nav",
                label_visibility="collapsed",
            )
            menu = menu_map[selected_menu]

            st.markdown(
                """
                <div class='sidebar-v2-profile'>
                  <div class='avatar'>AG</div>
                  <div class='meta'>
                    <div class='name'>Admin General</div>
                    <div class='role'>Rectoría · 2025</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    except Exception as e:
                with st.sidebar:
                        st.error(f"Error en sidebar: {e}")

    # Routing
    if menu == "Resumen General":
        resumen_general.render()

    elif menu == "Resumen Estratégico":
        cmi_estrategico.render()

    elif menu == "Resumen por Procesos":
        resumen_por_proceso.render()

    elif menu == "Seguimiento Operativo":
        tab_a, tab_b = st.tabs(["Tablero Operativo", "Seguimiento reportes"])
        with tab_a:
            tablero_operativo.render()
        with tab_b:
            seguimiento_reportes.render()

    elif menu == "Indicadores en Riesgo":
        plan_mejoramiento.render()

    elif menu == "Alertas Activas":
        gestion_om.render()

    elif menu == "Configuración":
        pdi_acreditacion.render()


if __name__ == "__main__":
    main()
