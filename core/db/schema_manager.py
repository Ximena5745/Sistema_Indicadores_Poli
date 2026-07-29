"""
core/db/schema_manager.py — Database schema management (DDL operations).

Responsibility: Creating and maintaining database constraints and indexes.

This module handles:
  - SQLite unique index creation for UPSERT support
  - PostgreSQL unique constraint creation for ON CONFLICT support
  - DDL (Data Definition Language) operations
"""

import sqlite3
from typing import Any


def _ensure_sqlite_unique_index(conn: sqlite3.Connection) -> None:
    """
    Creates a unique index for UPSERT functionality in SQLite.

    SQLite requires an explicit index for ON CONFLICT clause to work with the
    expected key (id_indicador, periodo, anio). This function creates such an index
    if it doesn't already exist.

    Args:
        conn: SQLite connection object
    """
    cur = conn.cursor()
    cur.execute("PRAGMA index_list('registros_om')")
    indexes = {row[1] for row in cur.fetchall() if row[2] == 1}
    if "idx_registros_om_id_indicador_periodo_anio_unique" not in indexes:
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_registros_om_id_indicador_periodo_anio_unique "
            "ON registros_om (id_indicador, periodo, anio)"
        )
        conn.commit()


_COLUMNAS_ESPERADAS_REGISTROS_OM = {
    "tipo_accion": "TEXT DEFAULT 'OM Kawak'",
}


def _ensure_sqlite_columns(conn: sqlite3.Connection) -> None:
    """
    Agrega a registros_om columnas que pueden faltar en bases de datos creadas
    antes de que esas columnas existieran en el esquema.

    CREATE TABLE IF NOT EXISTS es un no-op contra una tabla ya existente, así
    que una base de datos antigua nunca recibe columnas añadidas después
    (ej. tipo_accion) a menos que se migren explícitamente aquí.
    """
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(registros_om)")
    existentes = {row[1] for row in cur.fetchall()}
    for columna, definicion in _COLUMNAS_ESPERADAS_REGISTROS_OM.items():
        if columna not in existentes:
            cur.execute(f"ALTER TABLE registros_om ADD COLUMN {columna} {definicion}")
    conn.commit()


def _ensure_postgres_columns(cur: Any) -> None:
    """Equivalente PostgreSQL de _ensure_sqlite_columns (ver docstring)."""
    cur.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'registros_om'
        """
    )
    existentes = {row[0] for row in cur.fetchall()}
    for columna, definicion in _COLUMNAS_ESPERADAS_REGISTROS_OM.items():
        if columna not in existentes:
            cur.execute(f"ALTER TABLE public.registros_om ADD COLUMN {columna} {definicion}")


def _ensure_postgres_unique_constraint(cur: Any) -> None:
    """
    Creates a unique constraint for ON CONFLICT functionality in PostgreSQL.

    PostgreSQL uses constraints (not indexes) for ON CONFLICT clauses.
    This function:
      1. Checks if constraint already exists
      2. Drops any orphaned index with the same name
      3. Creates the constraint if needed

    Args:
        cur: PostgreSQL cursor object
    """
    cur.execute(
        """
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'registros_om_unique_key'
          AND conrelid = 'public.registros_om'::regclass
    """
    )
    if cur.fetchone() is not None:
        return

    # Drop any orphaned index with the same name before creating constraint
    cur.execute(
        """
        SELECT 1
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname = 'registros_om_unique_key'
          AND c.relkind = 'i'
          AND n.nspname = 'public'
    """
    )
    if cur.fetchone() is not None:
        cur.execute("DROP INDEX IF EXISTS public.registros_om_unique_key")

    cur.execute(
        "ALTER TABLE public.registros_om ADD CONSTRAINT registros_om_unique_key UNIQUE (id_indicador, periodo, anio)"
    )
