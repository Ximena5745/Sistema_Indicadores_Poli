"""
CSS loading and styling injection utilities for Streamlit app.

Handles loading CSS files from both local and cloud environments with robust
path resolution for different deployment contexts.
"""
import streamlit as st
from pathlib import Path


def load_css(file_path: str) -> str:
    """
    Carga un archivo CSS y lo retorna como una cadena.
    
    Args:
        file_path: Ruta del archivo CSS a cargar
        
    Returns:
        str: Contenido del archivo CSS
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def inject_styles(css_files: list = None):
    """
    Inyecta estilos locales con ruta robusta para local y cloud.
    
    Intenta cargar archivos CSS desde la ruta relativa al script actual.
    Si no existen, intenta rutas alternativas para entornos cloud.
    
    Args:
        css_files: Lista de nombres de archivos CSS a cargar.
                  Por defecto: ["styles.css", "main.css"]
    """
    if css_files is None:
        css_files = ["styles.css", "main.css"]
    
    base = Path(__file__).resolve().parent.parent / "styles"
    
    for css_name in css_files:
        css_path = base / css_name
        
        # Intenta ruta alternativa para entornos cloud
        if not css_path.exists():
            css_path = Path(f"streamlit_app/styles/{css_name}")
        
        if css_path.exists():
            styles = load_css(str(css_path))
            st.markdown(f"<style>{styles}</style>", unsafe_allow_html=True)
