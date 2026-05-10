# 🔄 PHASE 2: Core Code Refactoring — SRP Violations

**Status:** 🟡 INICIADO - 10 Mayo 2026  
**Enfoque:** Código Central (`core/`) — NO agentes  
**Objetivo:** Resolver violaciones SRP, mejorar reproducibilidad y testabilidad  
**Duración Estimada:** 2 semanas, ~120 horas  

---

## 📊 Análisis de Violaciones SRP en Core

### 1️⃣ `core/db_manager.py` (712 líneas) — CRÍTICO 🔴

**Responsabilidades Actuales (VIOLATION):**

| ID | Responsabilidad | Líneas | Problema |
|----|-----------------|--------|----------|
| A1 | Configuración/Secretos | ~150 | Lógica Streamlit + .env + Supabase |
| A2 | Conexión BD | ~200 | Manejo dual SQLite/PostgreSQL |
| A3 | Normalización de Datos | ~80 | Mes/Periodo/Año conversiones |
| A4 | Esquema/Índices | ~40 | DDL para ambas BD |
| A5 | Notificaciones | ~20 | Logs + Streamlit alerts |
| A6 | CRUD Operations | ~150 | guardar/leer registros |
| A7 | Inicialización | ~50 | Bootstrapping BD |

**Plan de Descomposición:**

```
core/db_manager.py (712L) 
  ├─ core/db/config_provider.py (150L) — Gestión secretos/config
  ├─ core/db/connection_manager.py (200L) — Conexiones SQLite/Postgres
  ├─ core/db/data_normalizer.py (80L) — Normalización temporal
  ├─ core/db/schema_manager.py (40L) — DDL e índices
  ├─ core/db/operations.py (150L) — CRUD operations
  └─ core/db/__init__.py — Exports públicos (API estable)
```

**Beneficios:**
- ✅ Cada módulo: <200 líneas
- ✅ Tests independientes por responsabilidad
- ✅ Fácil evolución: cambiar config sin tocar CRUD
- ✅ Reutilización: data_normalizer usado en otros sitios

---

### 2️⃣ `core/semantica.py` (523 líneas) — ALTO 🟠

**Responsabilidades Actuales (VIOLATION):**

| ID | Responsabilidad | Líneas | Problema |
|----|-----------------|--------|----------|
| B1 | Categorización | ~150 | Lógica de umbrales |
| B2 | Normalización | ~200 | Conversión valores/porcentajes |
| B3 | Presentación Visual | ~80 | Colores e iconos |
| B4 | Nivel/Health | ~93 | Salud institucional |

**Plan de Descomposición:**

```
core/semantica.py (523L)
  ├─ core/domain/categorization.py (150L) — Lógica pura de categorías
  ├─ core/domain/normalization.py (200L) — Conversión de valores
  ├─ core/presentation/visual_mapping.py (80L) — Colores + iconos (UI)
  ├─ core/domain/health_metrics.py (93L) — Salud agregada
  └─ core/domain/__init__.py — Exports públicos
```

**Beneficios:**
- ✅ Dominio separado de presentación
- ✅ `visual_mapping.py` → importable solo por UI
- ✅ Tests de negocio sin dependencias Streamlit
- ✅ Categorización es Pure Functions (determinística)

---

### 3️⃣ `core/calculos.py` (261 líneas) — OK 🟢

**Status:** Aceptable (bajo límite de 200L, pero cercano)  
**Responsabilidades:**
- Normalización de cumplimiento
- Wrapper para categorización
- Salud agregada (compuesta)

**Acción:** Monitorear, pero no refactorizar ahora (depende de semantica.py)

---

### 4️⃣ `core/config.py` (261 líneas) — OK 🟢

**Status:** Aceptable  
**Responsabilidades:**
- Constantes de umbrales (UMBRAL_PELIGRO, etc.)
- Carga IDS_PLAN_ANUAL desde Excel
- Logging setup

**Potencial Mejora:** Separar Excel loading a `core/db/config_loader.py`

---

## 🛣️ Hoja de Ruta PHASE 2

### Semana 1: Descomposición db_manager.py

**Paso 1 (2h): Analizar dependencias** ✅ COMPLETADO
- Identificado: 7 funciones públicas
- Imports externos: solo Streamlit pages (renderers.py, gestion_om.py)

**Paso 2 (3h): Crear structure db/ con __init__.py** ✅ COMPLETADO
- Creada carpeta `core/db/`
- Estructura: config_provider.py → data_normalizer.py → connection_manager.py (prox.)

**Paso 3 (8h): Extraer módulos en orden** 🟡 EN PROGRESO
1. ✅ COMPLETADO - `config_provider.py` (160L)
   - safe_streamlit_secrets_get(), get_database_url(), sanitize_postgres_dsn()
   - extract_supabase_project_ref(), get_postgres_connect_kwargs()
   - use_postgres(), get_sqlite_path()
   
2. ✅ COMPLETADO - `data_normalizer.py` (130L)
   - numero_mes_a_nombre(), normalizar_nombre_mes()
   - normalizar_periodo_anio()
   - MESES_ESPANOL, MESES_NORMALIZACION_MAP

3. 🟡 PENDIENTE - `connection_manager.py` (~200L)
   - _connect_postgres(), _build_ipv4_retry_connect_kwargs()
   - _init_sqlite(), _init_postgres()

4. 🟡 PENDIENTE - `schema_manager.py` (~40L)
   - _ensure_sqlite_unique_index(), _ensure_postgres_unique_constraint()

5. 🟡 PENDIENTE - `operations.py` (~150L)
   - guardar_registro_om(), leer_registros_om(), registros_om_como_dict()
   - guardar_acciones_bulk(), leer_acciones(), borrar_acciones_por_marker()

**Paso 4 (7h): Testing** 🟡 PROX.
- Tests unitarios por módulo (sin mocking)
- Tests integración: verify backward compatibility
- Verificar 572/572 tests siguen pasando

### Semana 2: Descomposición semantica.py + Consolidación

**Paso 1 (3h): Descomponer semantica.py**
1. `core/domain/categorization.py` - Pure logic
2. `core/domain/normalization.py` - Value conversions
3. `core/presentation/visual_mapping.py` - UI concerns
4. `core/domain/health_metrics.py` - Aggregates

**Paso 2 (4h): Testing + Refactor dependencias**
- Tests para cada módulo dominio (sin Streamlit)
- Actualizar imports en calculos.py, otros
- Verificar suite

**Paso 3 (3h): Crear core/domain/__init__.py estable**
- Exports públicos consistentes
- Documentación de API

**Paso 4 (3h): Artefactos + Commit**
- Generar reportes de refactorización
- Git commits con clara trazabilidad
- Actualizar SOFTWARE_INTELLIGENCE_FRAMEWORK_STATUS.md

---

## 🎯 Métricas de Éxito PHASE 2

| Métrica | Baseline | Target | Status |
|---------|----------|--------|--------|
| Max líneas por módulo | 712 | <200 | 🟡 |
| Módulos db/ | 1 | 5 | 🟡 |
| Modules dominio | 0 | 4 | 🟡 |
| SRP violations core/ | 7 | 0 | 🟡 |
| Test passing | 572 | 572+ | 🟡 |
| Regressions | 0 | 0 | 🟡 |
| Coverage (domain) | - | 85%+ | 🟡 |

---

## 🚀 Próximo Paso: PASO 1

Iniciar análisis de dependencias en db_manager.py para determinar orden seguro de extracción.
