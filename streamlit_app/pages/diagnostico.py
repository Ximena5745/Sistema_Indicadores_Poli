"""
Página de diagnóstico para Streamlit Cloud.

Accede a: https://[tu-app].streamlit.app/diagnostico
Esta página verifica que todos los módulos se importen correctamente.

Refactored PHASE 2 WEEK 4: Extracted config and utility functions.
"""

import streamlit as st
import sys
from pathlib import Path

# Import refactored utilities
from .diagnostico_config import IMPORT_TESTS, FILES_TO_CHECK
from .diagnostico_utils import run_import_test, verify_files, get_relevant_modules


def render():
    """Main render function for diagnostico page."""
    st.set_page_config(page_title="Diagnóstico", page_icon="🔍", layout="wide")

    st.title("🔍 Diagnóstico del Sistema")

    # Info del sistema
    st.header("1. Información del Sistema")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Python Version",
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        )
        st.metric("Streamlit Version", st.__version__)
    with col2:
        PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
        st.metric("PROJECT_ROOT", str(PROJECT_ROOT))

    # Test imports
    st.header("2. Test de Imports")

    import_results = []

    for test_config in IMPORT_TESTS:
        st.subheader(f"Test: {test_config['name']}")
        success, error_msg = run_import_test(test_config)

        if success:
            st.success("✅ Import exitoso")
            import_results.append((test_config["name"], True, None))
        else:
            st.error(f"❌ Error al importar")
            import_results.append((test_config["name"], False, error_msg))
            with st.expander("Ver traceback completo"):
                st.code(error_msg)

    # Test 3: Verificar archivos
    st.header("3. Verificación de Archivos")
    file_results = verify_files(PROJECT_ROOT, FILES_TO_CHECK)
    for file_path, exists in file_results:
        if exists:
            st.success(f"✅ {file_path}")
        else:
            st.error(f"❌ {file_path} - NO EXISTE")

    # Resumen
    st.header("4. Resumen")
    all_ok = all(result[1] for result in import_results)
    if all_ok:
        st.success("🎉 Todos los imports funcionan correctamente")
    else:
        st.error("⚠️ Hay problemas con algunos imports")
        failed = [r[0] for r in import_results if not r[1]]
        st.error(f"Módulos con error: {', '.join(failed)}")

    # Info adicional
    with st.expander("📋 sys.path completo"):
        for i, path in enumerate(sys.path):
            st.text(f"{i}: {path}")

    with st.expander("📦 Módulos cargados (filtrados)"):
        relevant_modules = get_relevant_modules()
        st.json(relevant_modules)


if __name__ == "__main__":
    render()
