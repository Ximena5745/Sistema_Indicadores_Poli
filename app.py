"""
app.py — Entrada principal del Dashboard de Desempeño Institucional.
"""
import os
import sys
from pathlib import Path

import streamlit as st
import subprocess

# ─── Configurar sys.path para importaciones consistentes ────────────────────────
# Asegura que los imports funcionen tanto localmente como en cloud
PROJECT_ROOT = Path(__file__).resolve().parent
STREAMLIT_APP_PATH = PROJECT_ROOT / "streamlit_app"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(STREAMLIT_APP_PATH) not in sys.path:
    sys.path.append(str(STREAMLIT_APP_PATH))

# ─── Modo mantenimiento ───────────────────────────────────────────────────────
# Activar con: variable de entorno SGIND_MAINTENANCE_MODE=1
# o creando el archivo .maintenance_mode en el directorio raíz del proyecto.
_MAINTENANCE_FLAG_FILE = PROJECT_ROOT / ".maintenance_mode"
_MAINTENANCE_ENV = os.getenv("SGIND_MAINTENANCE_MODE", "").strip() in {"1", "true", "yes"}
_MAINTENANCE_ACTIVE = _MAINTENANCE_ENV or _MAINTENANCE_FLAG_FILE.exists()

if _MAINTENANCE_ACTIVE:
    _v2_url = os.getenv("SGIND_V2_URL", "")
    st.set_page_config(
        page_title="Sistema en mantenimiento — SGIND",
        page_icon="🔧",
        layout="centered",
    )
    st.title("🔧 Sistema en mantenimiento")
    st.info(
        "El Sistema de Indicadores (SGIND) se encuentra en proceso de actualización.\n\n"
        "Estará disponible nuevamente en breve.\n\n"
        "Para consultas urgentes, contacte al área de Planeación Institucional."
    )
    if _v2_url:
        st.success(f"La nueva versión del sistema ya está disponible en: [{_v2_url}]({_v2_url})")
    st.stop()


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
