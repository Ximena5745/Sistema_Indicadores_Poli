"""
Main entry point for Streamlit application.

Backward compatibility wrapper that uses refactored bootstrap and navigation modules.
For new code, import directly from those modules.
"""
import streamlit as st
from streamlit_app.bootstrap import inject_styles_with_cachebust
from streamlit_app.navigation import render_sidebar_navigation, router


def main():
    """Main entry point function for the Streamlit application."""
    st.set_page_config(page_title="Sistema de Indicadores", layout="wide")

    # Inyectar estilos con cache-busting
    inject_styles_with_cachebust()

    # Renderizar navegación y obtener menú seleccionado
    menu = render_sidebar_navigation()

    # Enrutar al módulo seleccionado
    router(menu)


if __name__ == "__main__":
    main()
