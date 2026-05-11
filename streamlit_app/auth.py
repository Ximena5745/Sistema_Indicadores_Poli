"""
Authentication module - Backward compatibility wrapper.

This module maintains backward compatibility by re-exporting authentication
functions from the refactored auth_modules package.

For new code, import directly from auth_modules:
    from auth_modules import require_auth, init_auth_session
"""
from auth_modules import init_auth_session, require_auth, get_allowed_emails, get_provider_config

__all__ = [
    "init_auth_session",
    "require_auth",
    "get_allowed_emails",
    "get_provider_config",
]


        st.warning("Cierra sesión y contacta al administrador si necesitas ayuda.")


def check_auth_state() -> bool:
    """
    Verifica rápidamente el estado de autenticación sin detener la app.
    Útil para mostrar elementos condicionales según el estado.

    Returns:
        bool: True si el usuario está autenticado Y autorizado
    """
    return st.session_state.get("user_authorized", False)


def get_current_user() -> dict:
    """
    Retorna la información del usuario actual desde session_state.
    Útil para acceder a la info del usuario en cualquier lugar de la app.

    Returns:
        dict: {email, authenticated, authorized}
    """
    return {
        "email": st.session_state.get("user_email"),
        "authenticated": st.session_state.get("user_authenticated", False),
        "authorized": st.session_state.get("user_authorized", False),
    }


def init_auth_session():
    """
    Inicializa las variables de sesión necesarias para autenticación.
    Debe llamarse al inicio de la aplicación principal.
    """
    if "user_authenticated" not in st.session_state:
        st.session_state["user_authenticated"] = False
    if "user_email" not in st.session_state:
        st.session_state["user_email"] = None
    if "user_authorized" not in st.session_state:
        st.session_state["user_authorized"] = False