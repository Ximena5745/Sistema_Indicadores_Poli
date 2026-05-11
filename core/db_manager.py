"""
core/db_manager.py — Persistencia dual SQLite (local) / PostgreSQL (Supabase).

DEPRECATED: Functions moved to core/db/ subpackage.

Prioridad de detección de DATABASE_URL:
  1. st.secrets["DATABASE_URL"]  → Streamlit Cloud
  2. Variable de entorno DATABASE_URL → .env local / Render
  3. Sin URL → SQLite local en data/db/registros_om.db
"""

import os
import re
import sqlite3
import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Import from refactored modules
from core.db.config_provider import (
    safe_streamlit_secrets_get,
    get_database_url,
    sanitize_postgres_dsn,
    extract_supabase_project_ref,
    get_postgres_connect_kwargs,
)

from core.db.data_normalizer import (
    numero_mes_a_nombre,
    normalizar_nombre_mes,
    normalizar_periodo_anio,
)

from core.db.connection_manager import (
    _connect_postgres,
    _build_ipv4_retry_connect_kwargs,
    _use_pg,
    _notify_streamlit,
    _init_sqlite,
    _init_postgres,
    inicializar_db,
)

from core.db.schema_manager import (
    _ensure_sqlite_unique_index,
    _ensure_postgres_unique_constraint,
)

# Create backward-compatible aliases for private functions
# These allow existing code in this file to use _-prefixed names
_safe_st_secrets_get = safe_streamlit_secrets_get
_get_database_url = get_database_url
_sanitize_postgres_dsn = sanitize_postgres_dsn
_extract_supabase_project_ref = extract_supabase_project_ref
_get_postgres_connect_kwargs = get_postgres_connect_kwargs
_mes_numero_a_nombre = numero_mes_a_nombre
_normalize_mes_nombre = normalizar_nombre_mes
_normalize_om_periodo_anio = normalizar_periodo_anio

# Legacy path constant for backward compatibility
DB_PATH = Path(__file__).parent.parent / "data" / "db" / "registros_om.db"

# Override _init_sqlite from connection_manager to use db_manager.DB_PATH
# This allows tests to monkeypatch DB_PATH and have it propagate correctly
_original_init_sqlite = _init_sqlite


def _init_sqlite():
    """Wrapper that passes db_manager.DB_PATH to connection_manager._init_sqlite"""
    return _original_init_sqlite(db_path=DB_PATH)


# ── Upsert ────────────────────────────────────────────────────────────────────


def guardar_registro_om(datos: dict) -> bool:
    """
    Upsert en registros_om.
    datos: dict con claves:
        id_indicador, nombre_indicador, proceso, periodo, anio,
        tiene_om (0/1), tipo_accion, numero_om, comentario
    Returns True si éxito.
    """
    inicializar_db()

    periodo, anio = _normalize_om_periodo_anio(datos.get("periodo", ""), datos.get("anio", 0))
    datos = {
        "id_indicador": str(datos.get("id_indicador", "")),
        "nombre_indicador": str(datos.get("nombre_indicador", "")),
        "proceso": str(datos.get("proceso", "")),
        "periodo": str(periodo),
        "anio": int(anio),
        "tiene_om": int(datos.get("tiene_om", 0)),
        "tipo_accion": str(datos.get("tipo_accion", "OM Kawak")),
        "numero_om": str(datos.get("numero_om", "")),
        "comentario": str(datos.get("comentario", "")),
        "registrado_por": "",
        "fecha_registro": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    try:
        if _use_pg():
            return _upsert_postgres(datos)
        else:
            return _upsert_sqlite(datos)
    except Exception as e:
        _notify_streamlit("error", f"Error al guardar: {e}")
        return False


def _upsert_sqlite(d: dict) -> bool:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO registros_om
            (id_indicador, nombre_indicador, proceso, periodo, anio,
             tiene_om, tipo_accion, numero_om, comentario, registrado_por, fecha_registro)
        VALUES
            (:id_indicador, :nombre_indicador, :proceso, :periodo, :anio,
             :tiene_om, :tipo_accion, :numero_om, :comentario, :registrado_por, :fecha_registro)
        ON CONFLICT(id_indicador, periodo, anio) DO UPDATE SET
            nombre_indicador = excluded.nombre_indicador,
            proceso          = excluded.proceso,
            tiene_om         = excluded.tiene_om,
            tipo_accion      = excluded.tipo_accion,
            numero_om        = excluded.numero_om,
            comentario       = excluded.comentario,
            fecha_registro   = excluded.fecha_registro
    """,
        d,
    )
    conn.commit()
    conn.close()
    return True


def _upsert_postgres(d: dict) -> bool:
    conn = _connect_postgres()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO registros_om
            (id_indicador, nombre_indicador, proceso, periodo, anio,
             tiene_om, tipo_accion, numero_om, comentario, registrado_por, fecha_registro)
        VALUES
            (%(id_indicador)s, %(nombre_indicador)s, %(proceso)s, %(periodo)s,
             %(anio)s, %(tiene_om)s, %(tipo_accion)s, %(numero_om)s, %(comentario)s,
             %(registrado_por)s, %(fecha_registro)s)
        ON CONFLICT ON CONSTRAINT registros_om_unique_key DO UPDATE SET
            nombre_indicador = EXCLUDED.nombre_indicador,
            proceso          = EXCLUDED.proceso,
            tiene_om         = EXCLUDED.tiene_om,
            tipo_accion      = EXCLUDED.tipo_accion,
            numero_om        = EXCLUDED.numero_om,
            comentario       = EXCLUDED.comentario,
            fecha_registro   = EXCLUDED.fecha_registro
    """,
        d,
    )
    conn.commit()
    cur.close()
    conn.close()
    return True


# ── Consulta ──────────────────────────────────────────────────────────────────


def leer_registros_om(anio: int = None, periodo: str = None):
    """Retorna lista de dicts con los registros guardados."""
    try:
        if _use_pg():
            return _leer_postgres(anio, periodo)
        else:
            return _leer_sqlite(anio, periodo)
    except Exception as e:
        _notify_streamlit("error", f"Error al leer registros: {e}")
        return []


def _leer_sqlite(anio, periodo):
    if not DB_PATH.exists():
        return []
    periodo_norm = ""
    if periodo:
        periodo_norm, _ = _normalize_om_periodo_anio(periodo, anio or 0)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if anio and periodo_norm:
        rows = conn.execute(
            "SELECT * FROM registros_om WHERE anio = ? AND periodo = ? ORDER BY fecha_registro DESC",
            (anio, periodo_norm),
        ).fetchall()
    elif anio:
        rows = conn.execute(
            "SELECT * FROM registros_om WHERE anio = ? ORDER BY fecha_registro DESC",
            (anio,),
        ).fetchall()
    elif periodo_norm:
        rows = conn.execute(
            "SELECT * FROM registros_om WHERE periodo = ? ORDER BY fecha_registro DESC",
            (periodo_norm,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM registros_om ORDER BY fecha_registro DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _leer_postgres(anio, periodo):
    import psycopg2.extras

    conn = _connect_postgres()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    periodo_norm = ""
    if periodo:
        periodo_norm, _ = _normalize_om_periodo_anio(periodo, anio or 0)

    if anio and periodo_norm:
        cur.execute(
            "SELECT * FROM registros_om WHERE anio = %(anio)s AND periodo = %(periodo)s ORDER BY fecha_registro DESC",
            {"anio": anio, "periodo": periodo_norm},
        )
    elif anio:
        cur.execute(
            "SELECT * FROM registros_om WHERE anio = %(anio)s ORDER BY fecha_registro DESC",
            {"anio": anio},
        )
    elif periodo_norm:
        cur.execute(
            "SELECT * FROM registros_om WHERE periodo = %(periodo)s ORDER BY fecha_registro DESC",
            {"periodo": periodo_norm},
        )
    else:
        cur.execute("SELECT * FROM registros_om ORDER BY fecha_registro DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


def registros_om_como_dict(anio: int = None, periodo: str = None) -> dict:
    """
    Retorna {id_indicador: {"tiene_om": bool, "tipo_accion": str, "numero_om": str, "periodo": str, "comentario": str}}
    Útil para cruzar con tabla de indicadores en otros módulos.
    Si un indicador tiene múltiples registros (distintos períodos), conserva el más reciente.
    """
    registros = leer_registros_om(anio=anio, periodo=periodo)
    result = {}
    for r in registros:
        iid = r["id_indicador"]
        if iid not in result:  # leer_registros_om ordena DESC → primer registro = más reciente
            result[iid] = {
                "tiene_om": bool(r.get("tiene_om", 0)),
                "tipo_accion": r.get("tipo_accion", "OM Kawak"),
                "numero_om": r.get("numero_om", ""),
                "periodo": r.get("periodo", ""),
                "comentario": r.get("comentario", ""),
                "anio": r.get("anio", ""),
            }
    return result


# Inicializar al importar
inicializar_db()


def guardar_acciones_bulk(df) -> bool:
    """
    Guarda un DataFrame o lista de dicts de acciones en una tabla `acciones`.
    Esta función es deliberadamente tolerante: crea la tabla con columnas TEXT
    según los nombres de columnas del DataFrame y luego inserta filas.

    Retorna True si la operación parece exitosa.
    """
    if df is None:
        return False
    try:
        import pandas as pd
    except Exception:
        pd = None

    # Normalizar a DataFrame
    if pd is not None and not isinstance(df, pd.DataFrame):
        try:
            df = pd.DataFrame(df)
        except Exception:
            return False

    # Si no hay filas, salir
    if (hasattr(df, "empty") and df.empty) or (not hasattr(df, "shape") and len(df) == 0):
        return False

    cols = list(df.columns)
    try:
        if _use_pg():
            conn = _connect_postgres()
            cur = conn.cursor()
            # Crear tabla con columnas TEXT si no existe
            cols_defs = ", ".join([f'"{c}" TEXT' for c in cols])
            cur.execute(f"CREATE TABLE IF NOT EXISTS acciones (id SERIAL PRIMARY KEY, {cols_defs})")
            # Insertar filas
            for _, row in df.iterrows():
                vals = [None if (pd is not None and pd.isna(x)) else str(x) for x in row.tolist()]
                placeholders = ",".join(["%s"] * len(vals))
                cur.execute(
                    f'INSERT INTO acciones ({", ".join([f"\"{c}\"" for c in cols])}) VALUES ({placeholders})',
                    tuple(vals),
                )
            conn.commit()
            cur.close()
            conn.close()
            return True
        else:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cols_defs = ", ".join([f'"{c}" TEXT' for c in cols])
            cur.execute(
                f"CREATE TABLE IF NOT EXISTS acciones (id INTEGER PRIMARY KEY AUTOINCREMENT, {cols_defs})"
            )
            insert_sql = f'INSERT INTO acciones ({", ".join([f"\"{c}\"" for c in cols])}) VALUES ({", ".join(["?" for _ in cols])})'
            for _, row in df.iterrows():
                vals = [None if (pd is not None and pd.isna(x)) else str(x) for x in row.tolist()]
                cur.execute(insert_sql, vals)
            conn.commit()
            conn.close()
            return True
    except Exception as e:
        _notify_streamlit("error", f"Error guardar_acciones_bulk: {e}")
        return False


def leer_acciones(limit: int = 1000) -> list:
    """Lee hasta `limit` filas de la tabla `acciones` y retorna lista de dicts."""
    try:
        if _use_pg():
            import psycopg2
            import psycopg2.extras

            conn = _connect_postgres()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(f"SELECT * FROM acciones ORDER BY id DESC LIMIT {int(limit)}")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return [dict(r) for r in rows]
        else:
            if not DB_PATH.exists():
                return []
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM acciones ORDER BY id DESC LIMIT {int(limit)}")
            rows = cur.fetchall()
            conn.close()
            return [dict(r) for r in rows]
    except Exception as e:
        _notify_streamlit("error", f"Error leer_acciones: {e}")
        return []


def borrar_acciones_por_marker(col: str, value: str) -> bool:
    """Borra filas de la tabla `acciones` donde `col` == `value`.

    Retorna True si la operación se ejecutó sin excepciones.
    """
    try:
        if _use_pg():
            conn = _connect_postgres()
            cur = conn.cursor()
            cur.execute(f'DELETE FROM acciones WHERE "{col}" = %s', (str(value),))
            conn.commit()
            cur.close()
            conn.close()
            return True
        else:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute(f'DELETE FROM acciones WHERE "{col}" = ?', (str(value),))
            conn.commit()
            conn.close()
            return True
    except Exception as e:
        _notify_streamlit("error", f"Error borrar_acciones_por_marker: {e}")
        return False
