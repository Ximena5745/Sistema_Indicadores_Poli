"""
app.py — Entrada principal del Dashboard de Desempeño Institucional.
"""
import os

import streamlit as st
import subprocess


def _get_git_commit_short():
    try:
        p = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True)
        return p.stdout.strip()
    except Exception:
        return os.getenv("GIT_COMMIT", "unknown")


EMBEDDED_MODE = os.getenv("POWER_APPS_EMBEDDED", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

# Delegar siempre a la nueva UI (streamlit_app/main.py) — este `app.py` es el
# único entrypoint. La función _new_main() ejecuta st.navigation() que bloquea act.
try:
    # Importar la nueva UI al tiempo de ejecución para poder capturar errores de import
    from streamlit_app.main import main as _new_main
except Exception as e:
    # Registrar traza completa en archivo para diagnóstico en despliegue
    import traceback
    tb = traceback.format_exc()
    try:
        with open('import_error_traceback.txt', 'w', encoding='utf-8') as f:
            f.write(tb)
    except Exception:
        pass

    # Mostrar una página mínima en Streamlit con el error (ayuda a debugging en cloud)
    st.set_page_config(page_title="Error - Sistema de Indicadores", layout="wide")
    st.title("Error al iniciar la aplicación")
    st.error("Ha ocurrido un error al importar el módulo de la interfaz. Se ha guardado la traza en `import_error_traceback.txt`.")
    with st.expander("Ver detalles de la excepción"):
        st.code(tb)
else:
    # El entrypoint delega a la nueva UI sin elementos de diagnóstico en el sidebar.
    _new_main()
