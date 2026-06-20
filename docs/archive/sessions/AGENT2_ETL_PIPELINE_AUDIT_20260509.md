# AGENT 2 — AUDITORÍA ETL & PIPELINE
### Sistema de Indicadores Institucionales (SGIND)

**Generado:** 9 de mayo de 2026  
**Alcance:** Auditoría completa de arquitectura, trazabilidad, validaciones, versionado y recuperación  
**Conclusión:** ⚠️ **Pipeline funcional pero con gaps críticos en reproducibilidad y auditabilidad**

---

## EJECUTIVO

El pipeline ETL actual del SGIND está **bien arquitecturado** en capas (extracción → transformación → carga) con separación clara de responsabilidades. Sin embargo, presenta **gaps operacionales críticos**:

- ✅ Arquitectura modular (16 submódulos en etl/)
- ✅ Data contracts documentados en YAML
- ⚠️ **Versionado parcial** — timestamps pero sin histórico de consolidaciones
- ⚠️ **Audit trail incompleto** — no se registra quién disparó qué, cuándo
- ❌ **Sin retry automático** para fallos de conectividad API
- ❌ **Sin notificación de fallos** a equipo de calidad
- ❌ **Versiones de librerías no fijadas exactamente** (requirements.txt sin ==)

---

## 1. ARQUITECTURA ETL ACTUAL

### 1.1 Estructura General

```
Pipeline ETL de 3 etapas:
  Etapa 1: consolidar_api.py          → Extrae de API Kawak + Excel local
  Etapa 2: actualizar_consolidado.py  → Transforma y carga (orquestador principal)
  Etapa 3: generar_reporte.py         → Genera artefactos de auditoría (JSON/CSV)

Orquestación:
  run_pipeline.py                     → Ejecuta las 3 etapas en secuencia
```

**Archivos clave:**
- [scripts/consolidar_api.py](scripts/consolidar_api.py#L1) — **167 líneas**
  - Responsabilidad única: Leer archivos anuales Kawak + API
  - Salida: `data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx`
  
- [scripts/actualizar_consolidado.py](scripts/actualizar_consolidado.py#L1) — **~330 líneas**
  - Orquestador principal — coordina 10+ módulos del paquete etl/
  - Carga 5 DataFrames intermedios
  - Usa workbook_local_copy() para evitar bloqueos de archivos
  
- [scripts/generar_reporte.py](scripts/generar_reporte.py#L1) — **142 líneas**
  - Responsabilidad única: Resumir artefactos (JSON/CSV)

### 1.2 Modularidad — Paquete etl/

La lógica de negocio está distribuida en 16 módulos **especializados por responsabilidad**:

| Módulo | Responsabilidad | Líneas |
|--------|-----------------|--------|
| [etl/config.py](scripts/etl/config.py) | Carga settings.toml (año_cierre, IDs especiales) | ~65 |
| [etl/fuentes.py](scripts/etl/fuentes.py) | Carga de todas las fuentes externas | ~300 |
| [etl/normalizacion.py](scripts/etl/normalizacion.py) | Limpieza de strings, IDs, tipos | ~150 |
| [etl/catalogo.py](scripts/etl/catalogo.py) | Construcción del catálogo maestro | ~200 |
| [etl/extraccion.py](scripts/etl/extraccion.py) | Extrae Meta/Ejecución de filas | ~250 |
| [etl/builders.py](scripts/etl/builders.py#L1) | Construye registros para cada hoja | ~350 |
| [etl/validacion_historica.py](scripts/etl/validacion_historica.py#L1) | Detecta anomalías en series tiempo | ~150 |
| [etl/cumplimiento.py](scripts/etl/cumplimiento.py) | Cálculos de cumplimiento | ~180 |
| [etl/periodos.py](scripts/etl/periodos.py) | Mapeo de fechas ↔ períodos | ~120 |
| [etl/signos.py](scripts/etl/signos.py) | Lógica de signos (Positivo/Negativo) | ~100 |
| [etl/no_aplica.py](scripts/etl/no_aplica.py) | Detección de "No Aplica" | ~80 |
| [etl/formulas_excel.py](scripts/etl/formulas_excel.py) | Reescribe fórmulas Excel | ~200 |
| [etl/escritura.py](scripts/etl/escritura.py) | I/O a Excel optimizado | ~150 |
| [etl/purga.py](scripts/etl/purga.py) | Limpieza de datos inválidos | ~250 |
| [etl/workbook_io.py](scripts/etl/workbook_io.py) | Context manager para acceso seguro Excel | ~80 |
| [etl/desglose.py](scripts/etl/desglose.py) | Análisis de series | ~50 |

**Evaluación:** ✅ **Excelente separación de concerns** — cada módulo tiene una responsabilidad clara y reutilizable.

### 1.3 Responsabilidades — ¿Claramente Separadas?

#### **Extracción**
- Ubicación: [etl/fuentes.py](scripts/etl/fuentes.py#L32) — `cargar_fuente_consolidada()`
- Lee: `Consolidado_API_Kawak.xlsx` (generado por consolidar_api.py)
- Normaliza: IDs, tipos, columnasclaves
- **Gap:** No maneja fallos parciales de API (si la API devuelve 80% de datos, se procesan igual)

#### **Transformación**
- Ubicación: [scripts/etl/](scripts/etl/) — 12+ módulos
- Orquestación: [actualizar_consolidado.py](scripts/actualizar_consolidado.py#L96) — `main()`
  - Carga catálogos (~línea 114)
  - Construye registros (línea ~180)
  - Limpia datos inválidos (línea ~200)
  - Escribe hojas (línea ~250)
- **Gap:** Lógica muy concentrada en `main()` — difícil de testear unitariamente

#### **Carga**
- Ubicación: [etl/escritura.py](scripts/etl/escritura.py) — `escribir_filas()`, `escribir_hoja_nueva()`
- Usa: `openpyxl` para escritura directa a Excel
- Usa: [etl/workbook_io.py](scripts/etl/workbook_io.py) — context manager para evitar bloqueos
  ```python
  with workbook_local_copy(OUTPUT_FILE) as (local_output_file, source_workbook):
      wb = openpyxl.load_workbook(local_output_file)
      # escribir...
  ```
- **Buena práctica:** Copia local del workbook antes de escribir, luego sincroniza

### 1.4 Composición — ¿Se ejecutan separados o juntos?

**Estado actual: SEPARADOS + orquestación manual**

```bash
# Manual (3 comandos separados)
python scripts/consolidar_api.py
python scripts/actualizar_consolidado.py
python scripts/generar_reporte.py

# O automatizado
python scripts/run_pipeline.py  → ejecuta en secuencia
```

**Archivo orquestador:** [scripts/run_pipeline.py](scripts/run_pipeline.py#L1) — ~400 líneas
- Ejecuta 3 scripts en subprocesos
- Captura stdout/stderr
- Genera artefactos: `pipeline_run_YYYYMMDD_HHMMSS.json`, `.log`
- **Gap:** No existe retry automático si un paso falla

### 1.5 Idempotencia — ¿Se pueden ejecutar múltiples veces?

**Evaluación: ✅ SÍ, pero con condiciones**

#### [consolidar_api.py](scripts/consolidar_api.py)
```python
# Línea 130-132
df_total = pd.concat(frames, ignore_index=True)
df_total.to_excel(_OUT_API, index=False)
```
- **Idempotente:** ✅ Sobrescribe `Consolidado_API_Kawak.xlsx` completo
- Cada ejecución recrea los catálogos desde cero (FUENTE DE VERDAD)

#### [actualizar_consolidado.py](scripts/actualizar_consolidado.py#L96)
```python
# Línea 137 (workbook_local_copy context manager)
with workbook_local_copy(OUTPUT_FILE) as (local_output_file, source_workbook):
    wb = openpyxl.load_workbook(local_output_file)
    ws_hist = wb["Consolidado Historico"]
    ws_sem  = wb["Consolidado Semestral"]
    ws_cierres = wb["Consolidado Cierres"]
    # escribir nuevos registros, pero:
    # - Línea 200+: limpiar_cierres_existentes() → elimina cierres del año actual
    # - Línea 215: deduplicar_sheet() → elimina duplicados
```
- **Idempotente:** ✅ Pero con **efectos secundarios**:
  - Primera ejecución: Agrega registros nuevos
  - Segunda ejecución: Cierres se limpian y se re-construyen (posible pérdida de metadatos)
  - **Recomendación:** Implementar versionado de consolidados antes de limpiar

#### [generar_reporte.py](scripts/generar_reporte.py#L59)
```python
# Línea 74-77
json_path = art_dir / f"reporte_{stamp}.json"
json_path.write_text(json.dumps(reporte, ...), encoding="utf-8")
```
- **Idempotente:** ✅ Genera archivo con timestamp, no sobrescribe anteriores

**Conclusión sobre idempotencia:** ⚠️ **Parcial**
- Extracción y reporting: idempotentes
- Carga principal: potencialmente destructiva en segunda ejecución (cierres se limpian)

---

## 2. FLUJO DE DATOS Y TRAZABILIDAD

### 2.1 Mapeo Completo del Flujo

```
EXTRACCIÓN
┌─────────────────────────────────────────┐
│ API Kawak (2022-2026)                   │
│ + Excel local (data/raw/Kawak/*.xlsx)   │
└──────────────────┬──────────────────────┘
                   │
    consolidar_api.py (Parte 1 y 2)
                   │
                   ▼
         ┌─────────────────────────────────────────┐
         │ Consolidado_API_Kawak.xlsx              │  ← ARTEFACTO CLAVE
         │ - 15k+ registros por año                │
         │ - Columnas: ID, fecha, resultado        │
         │ - NO tiene deduplicación                │
         └──────────────┬──────────────────────────┘
                        │
         TRANSFORMACIÓN (actualizar_consolidado.py)
                        │
         ┌──────────────▼──────────────────┐
         │ 1. Carga Fuente Principal       │
         │    [etl/fuentes.py:32]          │
         │    - df_api = pd.read_excel()   │
         │    - Normaliza IDs (_id_str)    │
         │    - Renombra columnas          │
         └──────────────┬──────────────────┘
                        │
         ┌──────────────▼──────────────────────────┐
         │ 2. Enriquecimiento Primario             │
         │    - Carga Catálogo Indicadores        │
         │    - JOIN por Id (clasificación)       │
         │    - Agrega Sentido, Periodicidad      │
         └──────────────┬──────────────────────────┘
                        │
         ┌──────────────▼──────────────────────────┐
         │ 3. Enriquecimiento Secundario           │
         │    - JOIN CMI (Subproceso, Línea)      │
         │    - Mapeo de Procesos Maestros        │
         │    - Data Validation Skill             │
         │      (Subproceso-Proceso-Area.xlsx)    │
         └──────────────┬──────────────────────────┘
                        │
         ┌──────────────▼──────────────────────────┐
         │ 4. Construcción de Registros           │
         │    [etl/builders.py]                    │
         │    - Histórico (línea temporal)        │
         │    - Semestral (agregaciones)          │
         │    - Cierres (fin de año)              │
         └──────────────┬──────────────────────────┘
                        │
         ┌──────────────▼──────────────────────────┐
         │ 5. Validación Histórica                │
         │    [etl/validacion_historica.py]       │
         │    - Detecta cambios de Sentido        │
         │    - Caídas brutas >50% Meta/Ejec     │
         │    - Emite WARNING/ERROR               │
         └──────────────┬──────────────────────────┘
                        │
         ┌──────────────▼──────────────────────────┐
         │ 6. Escritura a Excel                   │
         │    [etl/escritura.py]                   │
         │    - Usa workbook_local_copy()         │
         │    - Deduplicación                     │
         │    - Materialización de fórmulas       │
         └──────────────┬──────────────────────────┘
                        │
CARGA                  ▼
         ┌──────────────────────────────────────────────┐
         │ Resultados Consolidados.xlsx                │
         │ ├─ Consolidado Historico (completo)         │
         │ ├─ Consolidado Semestral (principal)        │
         │ ├─ Consolidado Cierres (fin de año)        │
         │ └─ Catalogo Indicadores (maestro)           │
         └──────────────┬───────────────────────────────┘
                        │
generar_reporte.py     │
                        │
                        ▼
         ┌──────────────────────────────────────────┐
         │ CONSUMIDORES                             │
         ├─ app.py (streamlit)                      │
         ├─ services/data_loader.py (5 fases)      │
         ├─ pages/*.py (dashboards)                 │
         └─ Reportes (.json, .csv)                  │
```

### 2.2 Puntos de Pérdida de Información

#### **PUNTO 1: Validación Kawak [scripts/etl/fuentes.py:220]**
```python
kawak_validos = cargar_kawak_validos()
# ...
if (id_s, año) not in kawak_validos:
    skipped += 1
    continue  # ← PÉRDIDA SILENCIOSA
```
- **¿Qué se pierde?** Registros cuyo (Id, Año) no está en el catálogo Kawak 2025
- **¿Cuántos?** No se registra
- **¿Por qué se pierde?** Validez cruzada contra fuente oficial Kawak
- **Riesgo:** Datos válidos pueden ser rechazados por fuente desactualizada

#### **PUNTO 2: Extracción de Series [scripts/etl/extraccion.py:~150]**
```python
meta, ejec, fuente, es_na = _extraer_registro(row, hist_escalas, ...)
if fuente in ("skip", "sin_resultado"):
    skipped += 1
    continue  # ← PÉRDIDA SILENCIOSA
```
- **¿Qué se pierde?** Registros sin Meta o Ejecución extraíble
- **¿Cuántos?** No se registra
- **¿Por qué se pierde?** Variable no tiene datos o no coincide patrón esperado
- **Riesgo:** Datos parciales descartados sin auditoría

#### **PUNTO 3: Validación de Período [scripts/etl/builders.py:~75]**
```python
if not _fecha_es_periodo_valido(fecha_ts, periodicidad):
    skipped += 1
    continue  # ← PÉRDIDA SILENCIOSA
```
- **¿Qué se pierde?** Registros cuya fecha no coincide con periodicidad
- **¿Por qué?** Fechas fuera de rango esperado para Mensual/Trimestral/etc
- **Riesgo:** Datos válidos rechazados por validaciones demasiado estrictas

#### **PUNTO 4: Deduplicación [scripts/etl/escritura.py:~120]**
```python
def deduplicar_sheet(ws, llaves_de_df):
    # Elimina filas duplicadas pero no registra qué se eliminó
```
- **¿Qué se pierde?** Registros duplicados descartados
- **¿Cuántos?** No se registra en log
- **¿Por qué?** Clave LLAVE duplicada
- **Riesgo:** Posible pérdida de datos si duplicados son legítimos

### 2.3 Introducción de Duplicados

**Mecanismo de Llave:**
```python
# scripts/etl/fuentes.py:60-68
df["LLAVE"] = (
    id_series + "-" +
    fecha_series.dt.year.astype(int).astype(str) + "-" +
    fecha_series.dt.month.astype(int).astype(str).str.zfill(2) + "-" +
    fecha_series.dt.day.astype(int).astype(str).str.zfill(2)
)
# Ej: 245-2026-04-09  (Id-Año-Mes-Día)
```

**Riesgo de duplicados:**
1. Si API devuelve mismo registro 2 veces → LLAVE idéntica
2. Si se ejecuta pipeline 2 veces sin limpiar → llaves_existentes NO se consulta en segunda ejecución
3. **Mitigación:** [scripts/etl/escritura.py:deduplicar_sheet()] deduplica por LLAVE antes de escribir

**Evaluación:** ⚠️ **Deduplicación reactiva** (detecta después), no preventiva

### 2.4 Transformaciones Manuales

**No se detectaron transformaciones manuales evidentes.** El flujo es automatizado, excepto:
- Archivos Kawak anuales (generados por API manualmente)
- Plan de Acción (ingesta manual via planillas)

### 2.5 Trazabilidad — ¿Se registra de dónde viene cada dato?

**Mecanismo actual:**
1. **LLAVE:** Identifica registro único (Id + Fecha)
2. **Columna Fuente (no presente en salida):** En [etl/builders.py], se calcula `fuente` pero no se guarda

**Gap crítico:** 
```python
# No se registra en consolidado final:
# - Cuándo se extrajo (timestamp de extracción)
# - De dónde (API vs Excel vs LMI)
# - Versión del pipeline que lo procesó
```

**Recomendación:** Agregar columna `Origen` + `Timestamp_Extraccion` al consolidado

---

## 3. CONTRATOS DE DATOS Y VALIDACIONES

### 3.1 Validaciones Implementadas

#### **UBICACIÓN:** [config/data_contracts.yaml](config/data_contracts.yaml) — **350+ líneas**

**Hojas validadas:** 4 principales
- Consolidado Historico
- Consolidado Semestral
- Consolidado Cierres
- Catalogo Indicadores

**Tipos de validaciones definidas:**

| Validación | Columnas | Implementada |
|-----------|----------|--------------|
| **Tipo** | Anio, Fecha, Id (string), Meta/Ejecucion (float) | ✅ Parcial (openpyxl) |
| **Requerida** | Anio, Fecha, Periodo, Id, Indicador, Proceso | ✅ Sí (dropna) |
| **Rango numérico** | Meta (min:0), Anio (2022-2030), Cumplimiento (0-1.3) | ✅ Sí (core/calculos.py) |
| **Patron regex** | Id (^[0-9a-zA-Z\-]+$) | ❌ No |
| **Categorical** | Periodicidad, Sentido, Clasificacion | ✅ Parcial (strings) |
| **Coherencia temporal** | Fecha ↔ Año, Periodo ↔ Mes | ✅ Sí (etl/periodos.py) |
| **Lógica negocio** | Cambio retroactivo Sentido, Caída >50% Meta | ✅ Sí (etl/validacion_historica.py) |

### 3.2 Dónde Se Valida

```
ENTRADA (consolidar_api.py)
├─ Lee Excel/CSV
├─ Filtra NaN: df[df["fecha"].notna()]  [línea 126]
├─ Normaliza IDs: _id_str()  [línea 117]
└─ Diag: cuenta "N/A" strings  [línea 71-76]

TRANSFORMACIÓN (actualizar_consolidado.py)
├─ Valida Kawak: cargar_kawak_validos()  [línea 122]
├─ Valida extracción: _extraer_registro()  [etl/extraccion.py]
├─ Valida período: _fecha_es_periodo_valido()  [etl/builders.py:75]
├─ Valida coherencia: validar_coherencia_historica()  [etl/validacion_historica.py:26]
└─ Valida tipos Excel: openpyxl cell formulas

SALIDA (generar_reporte.py)
├─ Lee consolidado final
├─ Verifica rango fechas, conteo IDs
└─ Genera summary JSON/CSV
```

**Evaluación:** ⚠️ **Validaciones dispersas** — no centralizadas en un único orquestador

### 3.3 Validaciones Faltantes CRÍTICAS

#### **1. Validación de contrato en entrada**
```python
# Gap: No existe validación que verifique:
# - Consolidado_API_Kawak.xlsx tiene columnas requeridas
# - Tipos de datos correctos antes de procesar
```
**Recomendación:** Usar [services/data_validation.py:validate_dataset()](services/data_validation.py#L130)
```python
from services.data_validation import validate_dataset
report = validate_dataset(df_api, source_name="consolidado_api_kawak")
if not report.is_valid:
    for err in report.error_issues:
        logger.error(err)
        sys.exit(1)
```

#### **2. Validación de cardinalidad**
```python
# Gap: No se verifica:
# - Cada Id debe tener exactamente 1 registro por Periodo/Fecha
# - Meta/Ejecucion son coherentes (no hay Ejecutado > 2x Meta)
```

#### **3. Validación de integridad referencial**
```python
# Gap: No se valida:
# - Todos los Id en Consolidado deben existir en Catálogo
# - Sentido en Consolidado ↔ Sentido en Catálogo son coherentes
```
**Existe en contract:** [config/data_contracts.yaml:~280]
```yaml
validaciones:
  - "Todos los Id en Catalogo deben existir en Consolidado Semestral"
```
**Pero NO se implementa:** services/data_validation.py no incluye esta regla

#### **4. Validación de rangos de cumplimiento**
```python
# Gap: No valida cambios bruscos en cumplimiento
# - ¿Cumplimiento pasó de 50% a 150% entre periodos?
# - ¿Meta cambió 10x respecto a período anterior?
```

### 3.4 Qué Pasa Cuando Falla Validación

| Caso | Comportamiento | Registro |
|------|---------------|----------|
| Fecha NaN | **Skip silencioso** en [consolidar_api.py:126] | ⚠️ Logger solo cuenta |
| Kawak Id no válido | **Skip silencioso** en [builders.py:73] | ❌ No se registra |
| Período inválido | **Skip silencioso** en [builders.py:75] | ❌ No se registra |
| Extracción fallida | **Skip silencioso** en [extraccion.py:~150] | ❌ No se registra |
| Cambio Sentido | **WARNING en log** en [validacion_historica.py:80] | ✅ Se registra |
| Caída Meta >50% | **WARNING en log** en [validacion_historica.py:120] | ✅ Se registra |

**Evaluación:** ⚠️ **Manejo inconsistente** — algunos errores se silencian, otros generan warnings

### 3.5 Centralización de Validaciones

**Arquitectura actual:**
```
config/data_contracts.yaml
    ↓
services/data_validation.py  (ValidationReport, validate_dataset)
    ↓
NO SE USA en actualizar_consolidado.py
```

**Estado:** ❌ **Data contracts definidos pero no ejecutados en pipeline**

**Recomendación:** Implementar gate de validación en actualizar_consolidado.py:main()
```python
# Después de línea 140 (cargar_fuente_consolidada)
report = validate_dataset(df_api, source_name="consolidado_api_kawak")
if report.error_count > 0:
    logger.error("Validación fallida: %s", report.to_dict())
    sys.exit(1)  # Bloquear pipeline
```

---

## 4. VERSIONADO, REPRODUCIBILIDAD Y AUDITORÍA

### 4.1 Timestamps y Artefactos

#### **Consolidados con versión temporal:**
```
data/output/Resultados Consolidados.xlsx
    ├─ Consolidado Historico
    ├─ Consolidado Semestral
    ├─ Consolidado Cierres
    └─ Catalogo Indicadores
    
🔴 PROBLEMA: NO hay versionado histórico
   - Cada ejecución SOBRESCRIBE
   - No se puede recuperar consolidación de hace 2 semanas
```

#### **Artefactos con timestamp:**
```
artifacts/
├─ reporte_20260505.json        ✅ Timestamp al archivo
├─ reporte_20260505.csv         ✅ Timestamp al archivo
├─ pipeline_run_20260505_hhmmss.json  ✅ Timestamp completo
└─ pipeline_run_20260505_hhmmss.log   ✅ Timestamp completo
```

**Ubicación:** [scripts/generar_reporte.py:57]
```python
stamp = datetime.now().strftime("%Y%m%d")
json_path = art_dir / f"reporte_{stamp}.json"
```

**Limitación:** Timestamp solo al día, no a minuto. Si se ejecuta 2 veces en mismo día, se sobrescribe.

### 4.2 Reproducibilidad — ¿Se pueden reproducir consolidaciones antiguas?

**Capacidad actual:**

| Escenario | Posible | Método | Gap |
|-----------|---------|--------|-----|
| Reproducir consolidación de hoy | ✅ Sí | Guardar snapshot de Consolidado_API_Kawak.xlsx + código | Requiere backup manual |
| Reproducir consolidación de hace 1 semana | ❌ No | — | No hay histórico |
| Reproducir consolidación de hace 1 mes | ❌ No | — | No hay histórico |
| "Rollback" a consolidación anterior | ❌ No | — | No hay versioning de consolidados |

**Causa:** El consolidado principal NO tiene histórico de versiones.

**Workaround manual:** [scripts/backup_sqlite.py](scripts/backup_sqlite.py#L48)
```python
def run_backup(db_path: Path = DB_PATH, retention_days: int = DEFAULT_RETENTION_DAYS) -> Path:
    """Backup de BD SQLite con rotación (retiene 30 días)"""
```
Existe backup para BD pero NO para Excel consolidados.

### 4.3 Audit Trail — ¿Quién, Cuándo, Qué Cambió?

**Información capturada:**

```
✅ CAPTURADO:
  - Timestamp de ejecución: datetime.now() en actualizar_consolidado.py:104
  - Registros procesados: logger.info("   %d registros fuente", len(df_api))
  - Año cierre: logger.info("  ACTUALIZAR CONSOLIDADO  —  Año cierre: %s", AÑO_CIERRE_ACTUAL)
  
❌ NO CAPTURADO:
  - Usuario que ejecutó pipeline
  - IP/máquina donde se ejecutó
  - Variables de entorno (rama git, commit)
  - Cambios específicos entre consolidados (qué filas se modificaron)
  - Motivo de ejecución (automático vs manual)
```

**Ubicación de logs:**
- Stdout del script (temporal, se pierde)
- [artifacts/pipeline_run_YYYYMMDD_HHMMSS.log](scripts/run_pipeline.py#L300) — capturado por run_pipeline.py

**Contenido típico de log:**
```
2026-05-09 14:30:15  INFO      ACTUALIZAR CONSOLIDADO  —  Año cierre: 2025
2026-05-09 14:30:15  INFO      1. Cargando fuente consolidada API/Kawak…
2026-05-09 14:30:18  INFO         5234 registros fuente
2026-05-09 14:30:18  INFO      2. Cargando catálogo…
2026-05-09 14:30:21  INFO         Procesando Consolidado Historico…
2026-05-09 14:30:35  INFO         [Consolidado Historico] 1823 registros nuevos, 45 skipped
```

**Evaluación:** ⚠️ **Audit trail básico** — registro de qué pasó, pero no de quién/dónde/por qué

### 4.4 Versionado de Librerías

**Archivo:** [requirements.txt](requirements.txt) — **19 líneas**

```
streamlit>=1.36.0           ❌ >= (NO fijado exactamente)
plotly>=5.22.0              ❌ >= (NO fijado exactamente)
pandas>=2.2.2               ❌ >= (NO fijado exactamente)
openpyxl>=3.1.4             ❌ >= (NO fijado exactamente)
xlrd>=2.0.1                 ❌ >= (NO fijado exactamente)
```

**Problema:**
- Pandas 2.2.2 vs 2.3.0 pueden cambiar comportamiento de función
- openpyxl 3.1.4 vs 3.2.0 puede introducir bugs
- CI/CD reproduciría diferente en máquina A vs B

**Recomendación:**
```txt
streamlit==1.36.0
plotly==5.22.0
pandas==2.2.2
openpyxl==3.1.4
xlrd==2.0.1
numpy==1.24.0
pyyaml==6.0
pydantic==2.0.0  # agregar versión exacta
```

### 4.5 Reproducibilidad del Código

**Control de versiones:**
- Código en git (implícito)
- **Gap:** No se registra en logs qué commit/rama ejecutó el pipeline

**Ejemplo de log ideal:**
```
Git commit: a3f4b21 (main)
Git branch: main
Código ejecutado desde: /c:/Users/ximen/.../.venv/lib/site-packages/...
```

---

## 5. MANEJO DE ERRORES, RECUPERACIÓN Y NOTIFICACIÓN

### 5.1 Fallos Parciales de API

**Escenario:** API Kawak devuelve 80% de datos (timeout parcial)

**Comportamiento actual:**
```python
# consolidar_api.py:125-127
df    = df[df["fecha"].notna()].copy()
print(f"  {y}.xlsx: {antes:,} filas → {len(df):,} (eliminados {antes - len(df):,} sin fecha)")
# Se procesan los datos que SI llegaron
```

**Evaluación:** ❌ **NO hay detección de fallo parcial**
- Si API devuelve 50% de registros (vs 100% esperado), pipeline continúa
- No se dispara alerta

**Recomendación:**
```python
MIN_RECORDS_EXPECTED = {
    2022: 5000, 2023: 6000, 2024: 7000, 2025: 8000, 2026: 9000
}
for year in YEARS:
    if len(frames[year]) < MIN_RECORDS_EXPECTED[year] * 0.9:
        logger.error(f"⚠️ FALLO PARCIAL: {year} tiene {len(frames[year])} registros (< 90% esperado)")
        sys.exit(1)  # Bloquear pipeline
```

### 5.2 Registros de Omisiones

**¿Se registran datos no procesados?**

| Punto de omisión | Registrado | Dónde |
|------------------|-----------|-------|
| Fecha NaN en consolidar_api | ✅ Sí | Conteo: `eliminados {antes - len(df):,}` |
| Id no válido en Kawak | ❌ No | Contador `skipped` pero no se loguea |
| Período inválido | ❌ No | Contador `skipped` pero no se loguea |
| Extracción fallida | ❌ No | Contador `skipped` pero no se loguea |

**Ubicación de skipped:**
```python
# scripts/etl/builders.py:29-30
skipped   = 0  # contador
...
if (id_s, año) not in kawak_validos:
    skipped += 1
    continue  # ← cuenta pero no se reporta después
```

**Gap:** El contador `skipped` se computa pero NO se loguea en stdout/artifacts

**Recomendación:**
```python
# Agregar al final de construir_registros_*
logger.warning(f"[{hoja}] {skipped} registros omitidos (validación)")
```

### 5.3 Retry Automático

**¿Existe retry en caso de fallo de conexión?**

**Respuesta:** ❌ **NO**

Ejemplo — cuando falla lectura de Excel:
```python
# scripts/etl/fuentes.py:39-42
if not CONSOLIDADO_API_KW.exists():
    logger.error(f"No se encontró {CONSOLIDADO_API_KW}...")
    return pd.DataFrame()  # ← Retorna vacío, no reintenta
```

**Recomendación:** Implementar retry con backoff
```python
import time
import tenacity

@tenacity.retry(
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    stop=tenacity.stop_after_attempt(3),
    retry=tenacity.retry_if_exception_type(IOError),
)
def cargar_fuente_consolidada() -> pd.DataFrame:
    return pd.read_excel(CONSOLIDADO_API_KW)
```

### 5.4 Notificación de Fallos

**¿Se notifica al equipo de calidad?**

**Respuesta:** ❌ **NO**

Cuando falla pipeline:
- Existe log en `artifacts/pipeline_run_*.log`
- Pero NO se envía correo, Slack, Teams, o webhook

**Recomendación:** Agregar notificación en [scripts/run_pipeline.py](scripts/run_pipeline.py#L300)
```python
import smtplib
from email.mime.text import MIMEText

def notificar_fallo(error_msg: str):
    """Envía notificación por email si falla pipeline"""
    recipients = ["calidad@institucion.edu"]
    msg = MIMEText(f"Pipeline ETL falló:\n{error_msg}")
    msg["Subject"] = "🚨 ALERTA: Pipeline ETL Fallido"
    
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login("pipeline@institucion.edu", os.environ["MAIL_PASSWORD"])
        server.send_message(msg)
```

### 5.5 Mecanismos de Rollback

**¿Existe rollback o recuperación?**

**Respuesta:** ⚠️ **Parcial**

**Lo que existe:**
- Backup de BD SQLite: [scripts/backup_sqlite.py](scripts/backup_sqlite.py#L48)
  ```python
  def run_backup(db_path: Path = DB_PATH, retention_days: int = DEFAULT_RETENTION_DAYS) -> Path:
      """Backup con retención 30 días"""
  ```
  - Retiene últimos 30 días de backups

**Lo que NO existe:**
- Rollback de Excel consolidados (no hay histórico de versiones)
- Rollback de transformaciones intermedias (etl logs no se guardan)
- Rollback automático en caso de fallo

**Recomendación:** Implementar versionado de consolidados
```python
# Antes de escribir nueva consolidación
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = OUTPUT_DIR / f"Resultados_Consolidados_BACKUP_{timestamp}.xlsx"
shutil.copy(OUTPUT_FILE, backup_path)
logger.info(f"Backup creado: {backup_path}")

# Luego escribir nuevo
escribir_consolidado_nuevo(OUTPUT_FILE)

# Si ocurre error:
except Exception as e:
    logger.error(f"Restaurando desde backup {backup_path}")
    shutil.copy(backup_path, OUTPUT_FILE)
    raise
```

### 5.6 Matriz de Resiliencia

| Fallo | Detectado | Registrado | Recuperable | Notificado |
|------|-----------|-----------|------------|-----------|
| API timeout | ❌ Parcial | ❌ No | ❌ No | ❌ No |
| Excel corrupto | ✅ Sí (exception) | ✅ Sí | ⚠️ Backup BD | ❌ No |
| Memoria insuficiente | ✅ Sí | ✅ Sí | ❌ No | ❌ No |
| Validación fallida | ⚠️ Parcial | ⚠️ Parcial | ❌ No | ❌ No |
| Fallo en cálculo cumpl. | ✅ Sí | ✅ Sí | ❌ No | ❌ No |

---

## 6. RESUMEN DE HALLAZGOS

### 6.1 Fortalezas ✅

| Aspecto | Hallazgo |
|--------|----------|
| **Arquitectura** | Modular y desacoplada — 16 submódulos reutilizables |
| **Separación de responsabilidades** | Extracción, transformación, carga claramente separadas |
| **Data contracts** | 350+ líneas de especificaciones YAML bien definidas |
| **Idempotencia** | Mayormente idempotente (excepto cierres que se limpian) |
| **Validación lógica negocio** | Detección de cambios Sentido, caídas Meta, coherencia temporal |
| **Logging** | Configurado en nivel INFO, captura pasos principales |
| **Backup** | Sistema de backup SQLite con rotación 30 días |
| **Artefactos** | Reportes JSON/CSV con timestamp para auditoría |
| **Trazabilidad** | LLAVE única (Id-Fecha) para trazar registros |

### 6.2 Gaps Críticos ❌

| Aspecto | Gap | Impacto | Severidad |
|--------|-----|--------|----------|
| **Validación de entrada** | Data contracts definidos pero NO ejecutados en pipeline | Garbage in, garbage out | 🔴 CRÍTICO |
| **Versionado de consolidados** | Cada ejecución sobrescribe sin histórico | No se pueden reproducir consolidaciones antiguas | 🔴 CRÍTICO |
| **Audit trail** | No se registra usuario, máquina, rama git, motivo | Imposible auditar responsabilidad | 🔴 CRÍTICO |
| **Retry automático** | Sin reintentos en fallos de conexión | Fallos transitorios = pipeline fallido | 🟠 ALTO |
| **Notificación de fallos** | Sin alertas a equipo de calidad | Fallos silenciosos, descubrimiento tardío | 🟠 ALTO |
| **Omisiones registradas** | Registros omitidos (skipped) no se loguean | No se sabe qué datos se perdieron | 🟠 ALTO |
| **Versionado de libs** | requirements.txt usa >= en lugar de == | Reproducibilidad entre máquinas en riesgo | 🟠 ALTO |
| **Rollback de consolidados** | No hay mecanismo para revertir cambios | Errores en transformación no son recuperables | 🟠 ALTO |

### 6.3 Gaps Moderados ⚠️

| Aspecto | Gap | Impacto |
|--------|-----|--------|
| **Cardinalidad** | No se valida 1 registro = 1 (Id, Período, Fecha) | Duplicados silenciosos posibles |
| **Integridad referencial** | No se valida que todos Id en consolidado existan en catálogo | Inconsistencia entre hojas |
| **Rango cumplimiento** | No se valida cambios bruscos (%>100% → 20% entre períodos) | Anomalías no detectadas |
| **Patrón regex** | ID no se valida contra patrón esperado | IDs malformados pueden pasar |
| **Orquestación centralizada** | Scripts separados + manual run_pipeline.py | Posible falta de sinergia |
| **Logging distribuido** | Logs en stdout + archivos sin rotación | Logs pueden crecer indefinidamente |

---

## 7. ARQUITECTURA ETL OBJETIVO (PROPUESTA)

### 7.1 Principios Rectores

```
1. SINGLE SOURCE OF TRUTH
   - 1 archivo de contrato de datos (data_contracts.yaml)
   - 1 validador centralizado (services/data_validation.py)
   - 1 logger centralizado (logging.getLogger("etl"))

2. REPRODUCIBILIDAD GARANTIZADA
   - Todas las librerías con == en requirements.txt
   - Versionado de consolidados con timestamp (no sobrescribir)
   - Registro de quién/cuándo/por qué ejecutó pipeline

3. OBSERVABILIDAD COMPLETA
   - Cada decisión que rechaza datos se loguea (auditoría)
   - Métricas de calidad: registros procesados/omitidos/duplicados
   - Alertas automáticas en fallos

4. RECUPERACIÓN AUTOMÁTICA
   - Retry con backoff en fallos transitorios
   - Rollback en caso de error
   - Notificación de fallos a stakeholders
```

### 7.2 Arquitectura Propuesta (en 4 capas)

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: INGESTA VALIDADA (validation gate)                │
│ ├─ Consolidado_API_Kawak.xlsx → Validar contrato          │
│ ├─ Reportar issues en ValidationReport                     │
│ └─ BLOQUEAR si errors, CONTINUAR si warnings              │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 2: TRANSFORMACIÓN RASTREABLE (etl/ con telemetría)  │
│ ├─ Construir registros (Histórico, Semestral, Cierres)   │
│ ├─ Loguear CADA decisión (aceptado/rechazado/duplicado)  │
│ ├─ Mantener LLAVE + Origen + Timestamp_Extraccion       │
│ └─ Tabla de auditoría: [id, decisión, motivo, timestamp]│
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 3: CARGA VERSIONADA (escribir con rollback)         │
│ ├─ Backup de consolidado anterior                          │
│ ├─ Escribir a versión temporal                             │
│ ├─ Verificar integridad (checksum)                         │
│ ├─ Si OK → renombrar a producción                          │
│ └─ Si FALLA → restaurar backup automáticamente             │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 4: REPORTERÍA Y NOTIFICACIÓN                         │
│ ├─ Generar reporte JSON/CSV (como hoy)                     │
│ ├─ Enviar notificación: [OK/WARNING/ERROR]                │
│ ├─ Guardar audit trail en BD (quién/cuándo/qué)          │
│ └─ Exposición en dashboard (Grafana/Kibana)              │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 Contratos de Datos Recomendados

**Matriz de Validaciones por Punto ETL:**

| Punto ETL | Validación | Ubicación | Acción en fallo |
|-----------|-----------|-----------|-----------------|
| **Entrada: Consolidado_API_Kawak** | Tipos + Requeridas + Cardinalidad | LAYER 1 (nuevo gate) | BLOQUEAR |
| **Extracción de Meta/Ejecucion** | Rango (0-inf), Patrón número | LAYER 2 (etl/extraccion.py) | LOGUEAR + SKIP |
| **Validación de Período** | Fecha coherente con Periodicidad | LAYER 2 (etl/periodos.py) | LOGUEAR + SKIP |
| **Cambio de Sentido** | Retroactivo (Pos ↔ Neg) | LAYER 2 (etl/validacion_historica.py) | WARNING + LOGUEAR |
| **Caída de Meta/Ejec** | >50% vs período anterior | LAYER 2 (etl/validacion_historica.py) | WARNING + LOGUEAR |
| **Salida: Consolidado Semestral** | Tipos + Referencial (Id ↔ Catálogo) | LAYER 3 (antes de escribir) | BLOQUEAR |

---

## 8. PLAN DE MEJORA (Priorizado)

### 8.1 Tabla de Mejoras

| # | Mejora | Criticidad | Esfuerzo | Beneficio | Propuesta |
|---|--------|-----------|----------|-----------|-----------|
| **1** | Ejecutar validation gate en entrada | 🔴 P1 | 4h | 🔵 Alto | Llamar `validate_dataset()` en actualizar_consolidado.py línea 110 |
| **2** | Versionado de consolidados | 🔴 P1 | 6h | 🔵 Alto | Agregar timestamp a ruta del consolidado, mantener últimos 5 |
| **3** | Audit trail centralizado | 🔴 P1 | 8h | 🔵 Alto | Tabla `AuditLog` en BD: usuario, máquina, rama, timestamp, status |
| **4** | Logueo de omisiones | 🟠 P2 | 3h | 🟢 Medio | Agregar `logger.warning()` a cada contador `skipped` |
| **5** | Retry automático | 🟠 P2 | 5h | 🟢 Medio | Usar `@tenacity.retry` en cargar_fuente_consolidada() + Excel load |
| **6** | Notificación de fallos | 🟠 P2 | 4h | 🟢 Medio | Agregar SMTP/webhook en run_pipeline.py, notificar a calidad@institucion |
| **7** | Fijado de versiones | 🟠 P2 | 1h | 🟢 Medio | Cambiar requirements.txt de >= a == |
| **8** | Rollback automático | 🟠 P2 | 5h | 🟢 Medio | Backup pre-escritura, restore en exception, log completo |
| **9** | Validación cardinalidad | 🟠 P3 | 4h | 🟡 Bajo | Verificar 1 registro/Id/Período, loguear duplicados antes de dedup |
| **10** | Integridad referencial | 🟠 P3 | 3h | 🟡 Bajo | Validar Id en consolidado ⊆ Id en catálogo, antes de escribir |
| **11** | Patrón regex para IDs | 🟡 P3 | 2h | 🟡 Bajo | Validar contra `^[0-9a-zA-Z\-]+$` en validate_dataset() |
| **12** | Rango cumplimiento anómalo | 🟡 P3 | 4h | 🟡 Bajo | Detectar cambios >50% en cumplimiento entre períodos |

### 8.2 Roadmap Sugerido

**Fase 1 (Inmediata — Semana 1):**
- ✅ #1 Validation gate (4h) — BLOQUEA garbage
- ✅ #4 Logueo omisiones (3h) — auditoría visible
- ✅ #7 Fix requirements.txt (1h) — reproducibilidad inmediata

**Fase 2 (Corto plazo — Semana 2-3):**
- ✅ #2 Versionado consolidados (6h) — recuperabilidad
- ✅ #3 Audit trail (8h) — trazabilidad
- ✅ #5 Retry automático (5h) — resiliencia

**Fase 3 (Mediano plazo — Semana 4-6):**
- ✅ #6 Notificación (4h) — visibilidad
- ✅ #8 Rollback automático (5h) — recuperación
- ✅ #9-11 Validaciones adicionales (9h) — robustez

---

## 9. RECOMENDACIONES INMEDIATAS

### 9.1 Quick Wins (< 2 horas)

```python
# 1. Fija versiones en requirements.txt
# Cambiar:
pandas>=2.2.2
# Por:
pandas==2.2.2

# 2. Loguea contador de omisiones
# En scripts/etl/builders.py, agregar al final:
logger.warning(f"[{hoja}] {skipped} registros omitidos")

# 3. Revisa log de última ejecución
# Ver: artifacts/pipeline_run_*.log para entender omisiones
```

### 9.2 Cambios Estructurales (1-2 semanas)

```python
# Archivo: scripts/actualizar_consolidado.py
# Agregar después de línea 111 (después de cargar_fuente_consolidada)

from services.data_validation import validate_dataset

logger.info("2. Validando contrato de datos…")
report = validate_dataset(df_api, source_name="consolidado_api_kawak")

if report.error_count > 0:
    logger.error(f"❌ {report.error_count} errores críticos detectados:")
    report.print_issues(level_filter="error")
    sys.exit(1)  # BLOQUEAR pipeline

if report.warning_count > 0:
    logger.warning(f"⚠️ {report.warning_count} warnings (continuando):")
    report.print_issues(level_filter="warning")

logger.info(f"✅ Validación OK: dataset es válido")
```

### 9.3 Tablero de Monitoreo Recomendado

**Crear dashboard para:**
- Ejecuciones/día
- Registros procesados/omitidos/duplicados
- Cambios en Sentido (warnings)
- Caídas >50% Meta/Ejecución
- Tiempo de ejecución (minutos)
- Timestamp de última actualización exitosa

---

## 10. CONCLUSIONES

### 10.1 Veredicto General

**El pipeline ETL del SGIND está ARQUITECTURAMENTE SÓLIDO pero OPERACIONALMENTE FRÁGIL.**

- ✅ **Lo que funciona:** Transformación de datos, lógica de negocio, modularidad
- ⚠️ **Lo que falta:** Observabilidad, recuperabilidad, auditabilidad

### 10.2 Riesgos Operacionales

| Riesgo | Probabilidad | Impacto | Recomendación |
|--------|------------|--------|---------------|
| Fallo no detectado en API (datos incompletos) | 🟠 Media | 🔴 Alto | Validación de cardinalidad mínima esperada |
| Consolidación anterior perdida tras error | 🟠 Media | 🔴 Alto | Versionado con backup automático |
| No se sabe quién/cuándo cambió datos | 🔴 Alto | 🟠 Medio | Audit trail de usuario/timestamp |
| Fallo transitorios dejan pipeline parado | 🟠 Media | 🟠 Medio | Retry automático con backoff |
| Registros omitidos sin explicación | 🔴 Alto | 🟠 Medio | Logueo centralizado de skipped |

### 10.3 Roadmap Resumido

```
SEMANA 1 (Validación inmediata)
├─ Agregar validation gate (30 min)
├─ Loguear omisiones (30 min)
└─ Fix requirements.txt (15 min)

SEMANA 2-3 (Recuperabilidad)
├─ Versionado de consolidados (6h)
├─ Audit trail en BD (8h)
└─ Retry automático (5h)

SEMANA 4+ (Robustez)
├─ Notificaciones automáticas
├─ Rollback automático
└─ Validaciones adicionales
```

---

## 11. ANEXOS

### A. Archivos Clave del Pipeline

```
Entrada:
  data/raw/Consolidado_API_Kawak.xlsx     [Generado por consolidar_api.py]
  data/raw/Indicadores por CMI.xlsx       [Catálogo CMI]
  data/raw/Subproceso-Proceso-Area.xlsx  [Mapeo de procesos]

Config:
  config/settings.toml                    [Año cierre, IDs especiales]
  config/data_contracts.yaml              [Especificaciones de esquema]
  config/mapeos_procesos.yaml             [Jerarquía de procesos]

Código:
  scripts/actualizar_consolidado.py       [Orquestador principal]
  scripts/etl/                            [16 módulos especializados]
  services/data_validation.py             [Validador de contratos]
  services/data_loader.py                 [Carga para Streamlit (5 fases)]

Salida:
  data/output/Resultados Consolidados.xlsx  [Consolidado final]
  artifacts/reporte_*.json                  [Resumen en JSON]
  artifacts/pipeline_run_*.log              [Log de ejecución]

BD:
  data/db/registros_om.db                 [SQLite con historiales]
```

### B. Métricas de Calidad Sugeridas

```sql
-- Tabla de auditoría propuesta
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    user VARCHAR(100),
    machine VARCHAR(100),
    git_branch VARCHAR(100),
    git_commit VARCHAR(40),
    action VARCHAR(50),              -- "consolidate", "validate", etc
    status VARCHAR(20),              -- "success", "warning", "error"
    registros_procesados INTEGER,
    registros_omitidos INTEGER,
    registros_duplicados INTEGER,
    registros_nuevos INTEGER,
    errores TEXT,
    warnings TEXT
);

-- Consulta de seguimiento
SELECT 
    DATE(timestamp) as fecha,
    COUNT(*) as ejecuciones,
    SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as exitosas,
    SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) as fallidas,
    AVG(registros_procesados) as promedio_registros
FROM audit_log
GROUP BY DATE(timestamp)
ORDER BY fecha DESC;
```

### C. Comando para Ejecutar Pipeline

```bash
# Ejecución manual (3 pasos)
python scripts/consolidar_api.py
python scripts/actualizar_consolidado.py
python scripts/generar_reporte.py

# Ejecución automática (orquestada)
python scripts/run_pipeline.py

# Con logging a archivo
python scripts/run_pipeline.py 2>&1 | tee pipeline_$(date +%Y%m%d_%H%M%S).log

# Desde cronjob (recomendado: 2 AM cada domingo)
0 2 * * 0 cd /c/Users/ximen/OneDrive/Proyectos_DS/Sistema_Indicadores_Poli && \
          python scripts/run_pipeline.py >> logs/pipeline_$(date +\%Y\%m\%d).log 2>&1
```

---

**Fin del Reporte**  
**Auditoría realizada por:** AGENT 2 — Especialista ETL & Pipeline  
**Fecha:** 9 de mayo de 2026  
**Versión:** 1.0
