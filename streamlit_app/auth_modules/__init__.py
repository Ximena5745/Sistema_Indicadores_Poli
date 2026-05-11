"""
Authentication module - Guards and provider configuration.
"""
from .guards import init_auth_session, require_auth
from .providers import get_allowed_emails, get_provider_config

__all__ = [
    "init_auth_session",
    "require_auth",
    "get_allowed_emails",
    "get_provider_config",
]
