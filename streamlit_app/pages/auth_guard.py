"""
Auth guard para páginas adicionales.
Coloca este import al inicio de cada página para protegerla.

Usage:
    from pages.auth_guard import require_page_auth
    require_page_auth()
"""
from streamlit_app.auth import require_auth, init_auth_session


def require_page_auth():
    """
    Protege la página actual verificando autenticación y autorización.
    Debe llamarse al inicio de cada página en streamlit_app/pages/
    """
    init_auth_session()
    return require_auth()