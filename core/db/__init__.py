"""
core/db — Persistencia de datos (dual SQLite/PostgreSQL).

API pública que mantiene backward compatibility con core.db_manager.
"""

from core.db.config_provider import (
    DB_PATH,
    get_database_url,
    get_postgres_connect_kwargs,
    get_sqlite_path,
    safe_streamlit_secrets_get,
    use_postgres,
    sanitize_postgres_dsn,
    extract_supabase_project_ref,
)

from core.db.data_normalizer import (
    numero_mes_a_nombre,
    normalizar_nombre_mes,
    normalizar_periodo_anio,
)

__all__ = [
    # Config provider
    "DB_PATH",
    "get_database_url",
    "get_postgres_connect_kwargs",
    "get_sqlite_path",
    "safe_streamlit_secrets_get",
    "use_postgres",
    "sanitize_postgres_dsn",
    "extract_supabase_project_ref",
    # Data normalizer
    "numero_mes_a_nombre",
    "normalizar_nombre_mes",
    "normalizar_periodo_anio",
]
