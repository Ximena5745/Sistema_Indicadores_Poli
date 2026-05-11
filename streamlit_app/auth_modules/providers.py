"""
OAuth provider configuration utilities.

Manages OIDC provider settings and allowed user emails for authentication.
"""
import streamlit as st


def get_allowed_emails() -> set:
    """
    Retorna el conjunto de emails permitidos desde st.secrets.
    
    Lee la configuración de allowed_emails desde los secrets de Streamlit.
    Soporta tanto valores separados por comas como listas.
    
    Returns:
        set: Conjunto de emails permitidos (en minúsculas)
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
    
    Returns:
        dict: Configuración con keys:
            - provider: str (default: "microsoft")
            - client_id: str
            - client_secret: str
            - require_email_verified: bool (optional, default: True)
    """
    try:
        return {
            "provider": st.secrets.get("auth_provider", "microsoft"),
            "client_id": st.secrets.get("client_id", ""),
            "client_secret": st.secrets.get("client_secret", ""),
            "require_email_verified": st.secrets.get("require_email_verified", True),
        }
    except Exception:
        return {
            "provider": "microsoft",
            "client_id": "",
            "client_secret": "",
            "require_email_verified": True,
        }
