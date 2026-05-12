"""
Authentication module - Backward compatibility wrapper.

This module maintains backward compatibility by re-exporting authentication
functions from the refactored auth_modules package.

For new code, import directly from auth_modules:
    from auth_modules import require_auth, init_auth_session
"""
import streamlit as st

from auth_modules import (
    init_auth_session as _init_auth_session,
    require_auth,
    get_allowed_emails,
    get_provider_config,
)

__all__ = [
    "init_auth_session",
    "require_auth",
    "get_allowed_emails",
    "get_provider_config",
    "check_auth_state",
    "get_current_user",
]


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
    _init_auth_session()