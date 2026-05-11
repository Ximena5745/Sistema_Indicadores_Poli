"""
Main entry point for Streamlit application.

Backward compatibility wrapper that uses refactored bootstrap and navigation modules.
For new code, import directly from those modules.
"""
import streamlit as st
from bootstrap import inject_styles_with_cachebust
from navigation import render_sidebar_navigation, router

st.set_page_config(page_title="Sistema de Indicadores", layout="wide")

# Inyectar estilos con cache-busting
inject_styles_with_cachebust()

# Renderizar navegación y obtener menú seleccionado
menu = render_sidebar_navigation()

# Enrutar al módulo seleccionado
router(menu)
        cmi_estrategico_tabulado.render()

    elif menu == "CMI por Procesos":
        from streamlit_app.pages import resumen_por_proceso
        resumen_por_proceso.render()

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
