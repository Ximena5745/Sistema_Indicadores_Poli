from pathlib import Path
from datetime import datetime

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
            # Agregar timestamp para forzar recarga
            import time
            styles += f"\n/* Updated: {int(time.time())} */"
            st.markdown(f"<style>{styles}</style>", unsafe_allow_html=True)


def main():
    _inject_styles()

    # Importar páginas bajo demanda para evitar circular imports
    try:
        from streamlit_app.pages import (
            cmi_estrategico,
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
            gestion_om,
            informe_por_procesos,
            plan_mejoramiento,
            resumen_general,
            resumen_por_proceso,
            seguimiento_reportes,
            tablero_operativo,
            pdi_acreditacion,
        )

    # Valor seguro por defecto
    menu = "Resumen General"

    # Deep-link desde CTA de CMI: abrir directamente el módulo CMI Estratégico
    # cuando llega el query param cmi_linea.
    if hasattr(st, "query_params") and st.query_params.get("cmi_linea"):
        menu = "CMI Estratégico"
        st.session_state["sidebar_nav"] = "⌂  CMI Estratégico"

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

            # Filtrar opciones válidas separador visual
            display_options = [opt for opt in menu_labels if not opt.startswith("─")]
            current_index = 0
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
    except Exception as e:
        with st.sidebar:
            st.error(f"Error en sidebar: {e}")

    # Routing
    if menu == "Resumen General":
        resumen_general.render()

    elif menu == "CMI Estratégico":
        from streamlit_app.pages import cmi_estrategico_tabulado
        cmi_estrategico_tabulado.render()

    elif menu == "CMI por Procesos":
        from streamlit_app.pages import cmi_por_procesos_resumen
        cmi_por_procesos_resumen.render()

    elif menu == "Informe por Procesos":
        from streamlit_app.pages import informe_por_procesos
        informe_por_procesos.render()

    elif menu == "Plan de Mejoramiento":
        plan_mejoramiento.render()

    elif menu == "Seguimiento Operativo":
        tab_a, tab_b = st.tabs(["Tablero Operativo", "Seguimiento reportes"])
        with tab_a:
            tablero_operativo.render()
        with tab_b:
            seguimiento_reportes.render()

    elif menu == "Indicadores en Riesgo":
        gestion_om.render()


if __name__ == "__main__":
    main()
