"""
Configuration and constants for diagnostico page.
"""

# Import tests configuration
IMPORT_TESTS = [
    {
        "name": "core.proceso_types",
        "module": "core.proceso_types",
        "imports": ["TIPOS_PROCESO", "TIPO_PROCESO_COLORS", "get_tipo_color"],
        "test_code": "get_tipo_color('APOYO')",
    },
    {
        "name": "resumen_por_proceso",
        "module": "streamlit_app.pages.resumen_por_proceso",
        "imports": [],
        "test_code": "hasattr(module, 'render')",
    },
]

# Files to verify
FILES_TO_CHECK = [
    "core/proceso_types.py",
    "core/__init__.py",
    "streamlit_app/pages/resumen_por_proceso.py",
    "app.py",
]
