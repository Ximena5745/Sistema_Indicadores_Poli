"""
Módulo de autenticación para Streamlit.
Protege las páginas verificando usuario autenticado y email en allowlist.
"""
import streamlit as st


def get_allowed_emails() -> set:
    """
    Retorna el conjunto de emails permitidos desde st.secrets.
    """
    try:
        allowed = st.secrets.get("allowed_emails", [])
        if isinstance(allowed, str):
            return {e.strip().lower() for e in allowed.split(",") if e.strip()}
        return {e.strip().lower() for e in allowed if e.strip()}
    except Exception:
        return set()


def get_provider_config() -> dict:
    """
    Retorna la configuración del proveedor OIDC desde st.secrets.
    """
    try:
        return {
            "provider": st.secrets.get("auth_provider", "microsoft"),
            "client_id": st.secrets.get("client_id", ""),
            "client_secret": st.secrets.get("client_secret", ""),
        }
    except Exception:
        return {"provider": "microsoft", "client_id": "", "client_secret": ""}


def require_auth() -> dict:
    """
    Función reutilizable para proteger cualquier página de Streamlit.

    Returns:
        dict: Información del usuario autenticado con keys:
            - email: str
            - name: str
            - authenticated: bool
            - authorized: bool

    Comportamiento:
    - Si no hay sesión activa: muestra login y llama st.stop()
    - Si hay sesión pero email no autorizado: muestra acceso denegado y llama st.stop()
    - Si está autorizado: retorna info del usuario
    """
    user_info = {
        "email": None,
        "name": None,
        "authenticated": False,
        "authorized": False,
    }

    if not st.user.is_logged_in:
        _render_login_prompt()
        st.session_state["user_authenticated"] = False
        st.session_state["user_email"] = None
        st.stop()
        return user_info

    email = None
    name = None
    email_verified = False

    if hasattr(st.user, "email") and st.user.email:
        email = st.user.email
    if hasattr(st.user, "name") and st.user.name:
        name = st.user.name
    if hasattr(st.user, "email_verified") and st.user.email_verified:
        email_verified = st.user.email_verified

    user_info["email"] = email
    user_info["name"] = name
    user_info["authenticated"] = True
    user_info["email_verified"] = email_verified

    if not email:
        _render_access_denied("No se pudo obtener el correo electrónico del usuario.")
        st.session_state["user_authenticated"] = True
        st.session_state["user_email"] = None
        st.session_state["user_authorized"] = False
        st.stop()
        return user_info

    allowed_emails = get_allowed_emails()
    email_lower = email.lower()

    provider_config = get_provider_config()
    require_verification = provider_config.get("require_email_verified", True)

    if require_verification and not email_verified:
        _render_access_denied(
            f"Tu correo {email} no está verificado. "
            "Por favor verifica tu correo en el proveedor de identidad."
        )
        st.session_state["user_authenticated"] = True
        st.session_state["user_email"] = email_lower
        st.session_state["user_authorized"] = False
        st.stop()
        return user_info

    if allowed_emails and email_lower not in allowed_emails:
        _render_access_denied(
            f"El correo {email} no tiene autorización para acceder a esta aplicación."
        )
        st.session_state["user_authenticated"] = True
        st.session_state["user_email"] = email_lower
        st.session_state["user_authorized"] = False
        st.stop()
        return user_info

    st.session_state["user_authenticated"] = True
    st.session_state["user_email"] = email_lower
    st.session_state["user_authorized"] = True

    user_info["authorized"] = True
    return user_info


def _render_login_prompt():
    """Muestra el prompt de login con el botón de st.login()."""
    st.set_page_config(page_title="Login - Sistema de Indicadores", layout="centered")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔐 Sistema de Indicadores")
        st.markdown("### Autenticación requerida")
        st.markdown("Por favor, inicia sesión con tu cuenta institucional.")

        provider_config = get_provider_config()
        provider = provider_config.get("provider", "google")

        st.login(
            provider=provider,
            prompt="select_account",
        )

        st.info("ℹ️ Usa tu correo institucional (@tuinstitucion.edu.co)")

        st.markdown("---")
        st.caption("¿Problemas? Contacta al administrador del sistema.")


def _render_access_denied(reason: str):
    """Muestra mensaje de acceso denegado con botón de logout."""
    st.set_page_config(page_title="Acceso Denegado", layout="centered")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("⛔ Acceso Denegado")
        st.markdown("### No tienes autorización para acceder")
        st.error(reason)

        st.markdown("---")
        st.markdown("**¿Crees que esto es un error?**")
        st.markdown("- Verifica que tu correo esté registrado en el sistema")
        st.markdown("- Contacta al administrador para solicitar acceso")

        st.markdown("---")
        st.logout()

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