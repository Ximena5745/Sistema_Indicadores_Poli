"""
scripts/diagnostico_om_db.py — Diagnóstico y prueba end-to-end de registros_om.

Verifica que la base de datos activa (Supabase/PostgreSQL si hay credenciales
configuradas, o SQLite local en su defecto) tenga el esquema correcto de
registros_om, ejecuta la migración automática (inicializar_db) y prueba un
guardado + lectura + limpieza reales usando guardar_registro_om().

Uso:
    python scripts/diagnostico_om_db.py

Requiere que las credenciales de Supabase estén disponibles como en la app
(DATABASE_URL, o SUPABASE_URL + SUPABASE_DB_PASSWORD) vía variables de entorno
o .streamlit/secrets.toml. Sin esas credenciales, corre contra el SQLite local
(data/db/registros_om.db).
"""

import sys
import sqlite3
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.db.connection_manager import _use_pg, _connect_postgres, inicializar_db, DB_PATH


ID_PRUEBA = "__DIAG_TEST__"


def _columnas_actuales() -> list:
    if _use_pg():
        conn = _connect_postgres()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'registros_om'
            ORDER BY ordinal_position
            """
        )
        cols = [r[0] for r in cur.fetchall()]
        cur.close()
        conn.close()
    else:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute("PRAGMA table_info(registros_om)")
        cols = [r[1] for r in cur.fetchall()]
        conn.close()
    return cols


def _borrar_registro_prueba() -> None:
    if _use_pg():
        conn = _connect_postgres()
        cur = conn.cursor()
        cur.execute("DELETE FROM registros_om WHERE id_indicador = %s", (ID_PRUEBA,))
        conn.commit()
        cur.close()
        conn.close()
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM registros_om WHERE id_indicador = ?", (ID_PRUEBA,))
        conn.commit()
        conn.close()


def main() -> int:
    backend = "PostgreSQL/Supabase" if _use_pg() else f"SQLite ({DB_PATH})"
    print(f"Backend detectado: {backend}\n")

    print("Columnas ANTES de inicializar_db():")
    antes = _columnas_actuales()
    print(" ", antes)
    tenia_tipo_accion = "tipo_accion" in antes

    print("\nEjecutando inicializar_db() (crea tabla si falta y migra columnas)...")
    inicializar_db()

    print("\nColumnas DESPUÉS de inicializar_db():")
    despues = _columnas_actuales()
    print(" ", despues)

    if "tipo_accion" not in despues:
        print("\n[FALLO] La columna tipo_accion sigue sin existir tras la migración.")
        print("Revisa que el usuario de la BD tenga permisos ALTER TABLE sobre registros_om.")
        return 1

    if not tenia_tipo_accion:
        print("\n[OK] La columna tipo_accion FALTABA y fue agregada por la migración.")
    else:
        print("\n[OK] La columna tipo_accion ya existía (no se necesitó migrar).")

    # ── Prueba end-to-end: guardar → leer → limpiar ────────────────────────
    from core.db_manager import guardar_registro_om, registros_om_como_dict

    payload = {
        "id_indicador": ID_PRUEBA,
        "nombre_indicador": "Diagnóstico automatizado",
        "proceso": "Diagnóstico",
        "periodo": "Enero",
        "anio": 1900,
        "tiene_om": 1,
        "tipo_accion": "OM Kawak",
        "numero_om": "DIAG-000",
        "comentario": "Registro de prueba generado por diagnostico_om_db.py",
    }

    print(f"\nProbando guardar_registro_om() con id_indicador={ID_PRUEBA!r} ...")
    ok = guardar_registro_om(payload)
    print("  guardar_registro_om ->", ok)

    if not ok:
        print("\n[FALLO] guardar_registro_om devolvió False.")
        print("Revisa los mensajes de advertencia/error impresos arriba (excepción real).")
        return 1

    leido = registros_om_como_dict(anio=1900, periodo="Enero").get(ID_PRUEBA)
    print("  Registro leído de vuelta:", leido)

    exito_lectura = bool(leido) and leido.get("tipo_accion") == "OM Kawak"

    print("\nLimpiando registro de prueba...")
    _borrar_registro_prueba()
    print("[OK] Registro de prueba eliminado.")

    if not exito_lectura:
        print("\n[FALLO] El registro no se guardó/leyó con los valores esperados.")
        return 1

    print("\n" + "=" * 60)
    print("DIAGNÓSTICO COMPLETO: guardado y lectura funcionan correctamente.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
