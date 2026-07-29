-- =============================================================================
-- scripts/diagnostico_om_db.sql
-- Diagnóstico y prueba manual del esquema de registros_om en Supabase/Postgres.
--
-- Uso: pegar en el SQL Editor de Supabase y correr sección por sección
-- (cada bloque numerado es independiente; lee el resultado antes de seguir
-- al siguiente). Equivalente en SQL puro a scripts/diagnostico_om_db.py.
--
-- Contexto: guardar_registro_om() hace INSERT/UPDATE incluyendo la columna
-- tipo_accion. Si la tabla registros_om fue creada antes de que esa columna
-- existiera en el esquema, el guardado falla silenciosamente (la app solo
-- muestra que el botón "Guardar" no hace nada). Este script te deja
-- verificarlo y repararlo a mano.
-- =============================================================================


-- ── 1) Ver columnas actuales de registros_om ────────────────────────────────
-- Si "tipo_accion" NO aparece en el resultado, ese es el bug: falta la
-- columna y todo guardado de OM está fallando.
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'registros_om'
ORDER BY ordinal_position;


-- ── 2) Reparar: agregar la columna si falta ─────────────────────────────────
-- Puramente aditivo (no toca filas existentes). Seguro de correr aunque la
-- columna ya exista (ADD COLUMN IF NOT EXISTS no falla si ya está).
ALTER TABLE public.registros_om
    ADD COLUMN IF NOT EXISTS tipo_accion TEXT DEFAULT 'OM Kawak';


-- ── 3) Confirmar que la columna quedó agregada ──────────────────────────────
-- Repetir la consulta del paso 1: ahora "tipo_accion" debe aparecer.
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'registros_om'
ORDER BY ordinal_position;


-- ── 4) Confirmar que existe la restricción única (necesaria para el upsert) ─
-- guardar_registro_om() usa "ON CONFLICT ON CONSTRAINT registros_om_unique_key"
-- sobre (id_indicador, periodo, anio). Si esto no devuelve una fila, el
-- upsert real también fallará aunque tipo_accion ya exista.
SELECT conname, pg_get_constraintdef(oid) AS definicion
FROM pg_constraint
WHERE conname = 'registros_om_unique_key'
  AND conrelid = 'public.registros_om'::regclass;

-- Si el paso anterior no devolvió filas, crear la restricción:
-- ALTER TABLE public.registros_om
--     ADD CONSTRAINT registros_om_unique_key UNIQUE (id_indicador, periodo, anio);


-- ── 5) Prueba end-to-end: insertar un registro de prueba (mismo upsert que la app) ─
-- Usa el mismo INSERT ... ON CONFLICT que core/db/operations.py::_upsert_postgres.
INSERT INTO registros_om
    (id_indicador, nombre_indicador, proceso, periodo, anio,
     tiene_om, tipo_accion, numero_om, comentario, registrado_por, fecha_registro)
VALUES
    ('__DIAG_TEST__', 'Diagnóstico manual SQL', 'Diagnóstico', 'Enero', 1900,
     1, 'OM Kawak', 'DIAG-000', 'Registro de prueba - seguro de borrar', '', now()::text)
ON CONFLICT ON CONSTRAINT registros_om_unique_key DO UPDATE SET
    nombre_indicador = EXCLUDED.nombre_indicador,
    proceso          = EXCLUDED.proceso,
    tiene_om         = EXCLUDED.tiene_om,
    tipo_accion      = EXCLUDED.tipo_accion,
    numero_om        = EXCLUDED.numero_om,
    comentario       = EXCLUDED.comentario,
    fecha_registro   = EXCLUDED.fecha_registro;


-- ── 6) Verificar que el registro de prueba quedó guardado con tipo_accion ───
SELECT id_indicador, nombre_indicador, periodo, anio, tiene_om, tipo_accion, numero_om
FROM registros_om
WHERE id_indicador = '__DIAG_TEST__';
-- Esperado: 1 fila, con tipo_accion = 'OM Kawak'.


-- ── 7) Limpieza: borrar el registro de prueba ───────────────────────────────
DELETE FROM registros_om WHERE id_indicador = '__DIAG_TEST__';

-- Confirmar que quedó limpio (debe devolver 0 filas):
SELECT * FROM registros_om WHERE id_indicador = '__DIAG_TEST__';
