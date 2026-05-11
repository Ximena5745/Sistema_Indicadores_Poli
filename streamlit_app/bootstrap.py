"""
Bootstrap utilities for Streamlit app initialization.

Handles CSS loading and style injection with cache-busting timestamp support.
"""
from pathlib import Path
import streamlit as st


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


def inject_styles_with_cachebust(css_files: list = None, add_timestamp: bool = True):
    """
    Inyecta estilos locales con ruta robusta para local y cloud.
    
    Intenta cargar archivos CSS desde la ruta relativa al script actual.
    Si no existen, intenta rutas alternativas para entornos cloud.
    Opcionalmente agrega timestamp para forzar recarga.
    
    Args:
        css_files: Lista de nombres de archivos CSS a cargar.
                  Por defecto: ["styles.css", "main.css"]
        add_timestamp: Si True, agrega timestamp como comentario CSS para cache-busting
    """
    if css_files is None:
        css_files = ["styles.css", "main.css"]
    
    base = Path(__file__).resolve().parent / "styles"
    
    for css_name in css_files:
        css_path = base / css_name
        
        # Intenta ruta alternativa para entornos cloud
        if not css_path.exists():
            css_path = Path(f"streamlit_app/styles/{css_name}")
        
        if css_path.exists():
            styles = load_css(str(css_path))
            
            # Agregar timestamp para forzar recarga
            if add_timestamp:
                import time
                styles += f"\n/* Updated: {int(time.time())} */"
            
            st.markdown(f"<style>{styles}</style>", unsafe_allow_html=True)
