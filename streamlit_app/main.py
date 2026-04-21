from pathlib import Path

import streamlit as st
from streamlit_option_menu import option_menu

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
    menu = "Nuestro Impacto"

    # Configuración del sidebar
    try:
            with st.sidebar:
                # Logo cuadrado con P (fondo oscuro para evitar tonos claros)
                logo_html = """
                <div class='sidebar-logo'>
                  <svg width='40' height='40' viewBox='0 0 40 40' fill='none' xmlns='http://www.w3.org/2000/svg'>
                    <rect width='40' height='40' rx='6' fill='#011638'/>
                    <text x='20' y='27' font-size='20' text-anchor='middle' fill='#ffffff' font-family='Arial' font-weight='800'>SI</text>
                  </svg>
                </div>
                """

                header_html = f"""
                <div class='sidebar-header'>
                  {logo_html}
                  <div class='sidebar-header-text'>
                    <div class='sidebar-title-main'>Sistema de gestión de <span>Indicadores</span></div>
                    <div class='sidebar-subtitle'>POLITÉCNICA GRANCOLMBIANA</div>
                  </div>
                </div>
                """
                st.markdown(header_html, unsafe_allow_html=True)
                st.markdown("<div class='sidebar-section-title'>Módulos del Sistema</div>", unsafe_allow_html=True)

                # Bloque de navegación
                st.markdown("<div class='sidebar-nav-card'>", unsafe_allow_html=True)
                # Menú personalizado HTML/CSS controlado por query param `page`
                options = [
                    ("Nuestro Impacto", "M", "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'><rect width='18' height='18' rx='3' fill='none' stroke='currentColor' stroke-width='1.5'/></svg>"),
                    ("OPEX Financiero", "F", "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'><circle cx='9' cy='9' r='6' fill='none' stroke='currentColor' stroke-width='1.5'/></svg>"),
                    ("Base Normativa", "B", "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'><path d='M4 6h16M4 12h16M4 18h16' stroke='currentColor' stroke-width='1.5' stroke-linecap='round'/></svg>"),
                    ("Auditoría (CSVs)", "A", "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'><path d='M12 6v6l4 2' stroke='currentColor' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/></svg>"),
                ]

                params = st.experimental_get_query_params()
                selected = params.get("page", ["Nuestro Impacto"])[0]

                menu_items = []
                for label, short, icon in options:
                    is_active = "active" if label == selected else ""
                    href = f"?page={label}"
                    item_html = f"<a href='{href}' class='nav-link {is_active}'><span class='nav-icon'>{icon}</span><span class='nav-label'>{label}</span></a>"
                    menu_items.append(item_html)

                menu_html = "<div class='custom-sidebar-menu'>" + "".join(menu_items) + "</div>"
                st.markdown(menu_html, unsafe_allow_html=True)
                menu = selected
                st.markdown("</div>", unsafe_allow_html=True)

                # Footer
                st.markdown("""
                <div style='margin-top: 40px; text-align: center; padding: 20px 0;'>
                    <div style='font-size: 13px; color: rgba(255,255,255,0.8); margin-bottom: 4px;'>
                        Politécnico Grancolombiano
                    </div>
                    <div style='font-size: 12px; color: rgba(255,255,255,0.6); margin-bottom: 12px;'>
                        Institución Universitaria
                    </div>
                    <div style='display: inline-block; background: transparent; border: 1px solid #10b981; 
                                color: #10b981; padding: 6px 16px; border-radius: 20px; 
                                font-size: 12px; font-weight: 600;'>
                        PMV V2.0
                    </div>
                </div>
                """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error en sidebar: {e}")

    # Routing
    if menu == "Nuestro Impacto":
        tab_cmi, tab_plan, tab_acred = st.tabs(["CMI Estratégico", "Plan de Mejoramiento", "Gestión y Acreditación"])
        with tab_cmi:
            cmi_estrategico.render()
        with tab_plan:
            plan_mejoramiento.render()
        with tab_acred:
            pdi_acreditacion.render()

    elif menu == "OPEX Financiero":
        resumen_general.render()

    elif menu == "Base Normativa":
        resumen_por_proceso.render()

    elif menu == "Auditoría (CSVs)":
        tab_a, tab_b, tab_c = st.tabs(["Tablero Operativo", "Seguimiento reportes", "Gestión de OM"])
        with tab_a:
            tablero_operativo.render()
        with tab_b:
            seguimiento_reportes.render()
        with tab_c:
            gestion_om.render()


if __name__ == "__main__":
    main()
