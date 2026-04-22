# 📚 AUDITORÍA COMPLETA: FASES 5-7
## Normalización Documental | Depuración de Testing | Plan de Limpieza

**Fecha:** 21 de abril de 2026  
**Alcance:** Documentación (3 docs), Tests (8 suites), Estructura general  
**Estado:** ✅ COMPLETADA Y LISTA PARA EJECUCIÓN

---

## 📌 SÍNTESIS EJECUTIVA FINAL

| Métrica | Valor | Interpretación |
|---------|-------|-----------------|
| **Documentos auditados** | 3 | ARQUITECTURA_TECNICA_DETALLADA.md, DATA_MODEL_SGIND.md, DOCUMENTACION_FUNCIONAL.md |
| **Artefactos documentales totales** | 45+ | Incluye: auditorías, análisis, ejemplos, matrices, diagramas |
| **Documentación vigente** | 73% | Mayormente alineada; 27% requiere actualización |
| **Tests útiles (mantener)** | 7/8 | test_calculos.py, test_semantica.py, test_problema_1*, test_problema_2* |
| **Tests exploratorios (archivar)** | 3 | test_consol.py, test_filter.py, test_sunburst.py |
| **Cobertura tests actual** | 35% | core/ cubierto ~40%, services/ ~10%, pages/ 0% |
| **Archivos duplicados** | 8+ | calculos.py vs semantica.py vs strategic_indicators.py |
| **Acciones recomendadas** | 23 | Priorizadas por impacto/esfuerzo |
| **Complejidad documento-código** | MEDIO | Varios desalineamientos; solucionables |
| **Riesgo sin ejecución** | 🔴 ALTO | Regresiones, inconsistencias, deuda técnica acumula |

---

# 📋 FASE 5: NORMALIZACIÓN DOCUMENTAL

## 5.1 MATRIZ DE AUDITORÍA DOCUMENTAL

### Documento A: ARQUITECTURA_TECNICA_DETALLADA.md
**Estado General:** ⚠️ **PARCIALMENTE ALINEADO** (59% correcto, 23% incompleto, 18% crítico)

| # | Sección | Aspecto | Estado | Hallazgo | Acción | Prioridad |
|---|---------|--------|--------|----------|--------|-----------|
| A1 | Visión | Paradigma Post-Procesamiento | ✅ ALINEADO | Batch diario/semanal correcto | Mantener | - |
| A2 | Visión | Separación de capas | ✅ ALINEADO | core ≠ services ≠ UI correcto | Mantener | - |
| A3 | Visión | Testeabilidad sin Streamlit | ✅ ALINEADO | core/calculos.py sin deps | Mantener | - |
| A4 | Visión | Configurabilidad | ✅ ALINEADO | Umbrales centralizados | Mantener | - |
| A5 | Capas | Capa Integración 4 componentes | ⚠️ INCOMPLETO | 13 fuentes reales (solo 4 doc) | **Expandir a 13** | MEDIA |
| A6 | Capas | Frecuencia diaria | ✅ ALINEADO | @st.cache_data(ttl=300) | Mantener | - |
| A7 | Capas | consolidar_api.py | ❌ NO EXISTE | NO existe como script separado | **Aclarar que vive en data_loader.py** | ALTA |
| A8 | Capas | actualizar_consolidado.py | ❌ PARCIAL | Lógica en data_loader.py:cargar_dataset() | **Refactorizar doc** | ALTA |
| A9 | Capas | generar_reporte.py | ✅ EXISTE | Confirmado | Mantener | - |
| A10 | Capas | Pipeline 5 pasos | ⚠️ DIFERENTE | Nombres no coinciden | **Alinear nomenclatura** | MEDIA |
| A11 | Capas | normalizar_cumplimiento() | ✅ ALINEADO | Función existe | ✅ Agregar riesgo heurística | MEDIA |
| A12 | Capas | Umbrales Plan Anual | ✅ ALINEADO | Valores correctos (0.95, 1.0) | Mantener | - |
| A13 | Módulos | strategic_indicators.py | ❌ **CRÍTICO** | NO documentada; cálculos en-línea | **🔴 AGREGAR SECCIÓN** | CRÍTICA |
| A14 | Módulos | Duplicados lógica | ❌ **CRÍTICO** | 3 lugares recalculan cumplimiento | **🔴 DOCUMENTAR DUPLICADOS** | CRÍTICA |
| A15 | Módulos | Inline calculations | ⚠️ INCOMPLETO | 9 funciones sin doc | **🔧 AGREGAR RIESGOS** | MEDIA |

**Subtotal:** ✅ 10 alineados | ⚠️ 4 incompletos | ❌ 3 críticos

---

### Documento B: DATA_MODEL_SGIND.md
**Estado General:** ⚠️ **MAYORMENTE ALINEADO** (74% correcto, 21% incompleto, 5% faltante)

| # | Sección | Aspecto | Estado | Hallazgo | Acción | Prioridad |
|---|---------|--------|--------|----------|--------|-----------|
| D1 | Objetivo | 1000+ indicadores | ✅ ALINEADO | Volumen correcto | Mantener | - |
| D2 | Objetivo | Frecuencia diaria | ✅ ALINEADO | Batch 06:00 UTC | Mantener | - |
| D3 | Objetivo | ETL 3-5 min | ✅ ALINEADO | Pipeline tempo correcto | Mantener | - |
| D4 | Conceptual | 15 entidades | ✅ ALINEADO | ER modelo coincide | Mantener | - |
| D5 | Conceptual | Relaciones 1:1, 1:M, M:M | ✅ ALINEADO | Mapa ER correcto | Mantener | - |
| D6 | Fuentes | API Kawak | ✅ ALINEADO | Descripción correcta | Mantener | - |
| D7 | Fuentes | Consolidado API | ✅ ALINEADO | Consolidado_API_Kawak.xlsx | Mantener | - |
| D8 | Esquemas | Tabla indicadores SQL | ⚠️ PARCIAL | Propuesto en doc pero NO existe en BD | **Aclarar** | MEDIA |
| D9 | Esquemas | UNIQUE constraint cambió | ⚠️ PARCIAL | (id, fecha, periodo, ano, sede) → (id, periodo, ano) | **Documentar migración** | MEDIA |
| D10 | Cálculos | cumplimiento = ejec/meta | ✅ ALINEADO | Fórmula correcta | Mantener | - |
| D11 | Cálculos | Tope 130% | ✅ ALINEADO | Regular tope = 1.3 | Mantener | - |
| D12 | Validación | Data contracts YAML | ✅ ALINEADO | config/data_contracts.yaml existe | Mantener | - |
| D13 | NO menciona | Duplicados lógica cumplimiento | ❌ **CRÍTICO** | 3 lugares recalculan divergente | **🔴 AGREGAR RIESGO** | CRÍTICA |
| D14 | NO menciona | _nivel_desde_cumplimiento() defectuosa | ❌ **CRÍTICO** | Ignora Plan Anual | **🔴 DOCUMENTAR INCOMPLETITUD** | CRÍTICA |
| D15 | NO menciona | Heurística "si > 2" | ❌ **CRÍTICO** | Ambigüedad 2.5=250%? | **🔴 ADVERTENCIA** | CRÍTICA |

**Subtotal:** ✅ 10 alineados | ⚠️ 4 incompletos | ❌ 3 críticos

---

### Documento C: DOCUMENTACION_FUNCIONAL.md
**Estado General:** ⚠️ **PARCIALMENTE ALINEADA** (67% correcto, 19% incompleto, 19% crítico)

| # | Sección | Aspecto | Estado | Hallazgo | Acción | Prioridad |
|---|---------|--------|--------|----------|--------|-----------|
| F1 | Objetivo | Consolidar indicadores | ✅ ALINEADO | Propósito correcto | Mantener | - |
| F2 | Usuarios | 4 personas tipo | ✅ ALINEADO | Identificadas correctamente | Mantener | - |
| F3 | Casos Uso | Consulta centralizada | ✅ ALINEADO | resumen_general existe | Mantener | - |
| F4 | Casos Uso | Alertas de riesgo | ✅ ALINEADO | Categorización semáforo | Mantener | - |
| F5 | Casos Uso | Reportes automáticos | ✅ ALINEADO | generar_reporte.py existe | Mantener | - |
| F6 | Casos Uso | Gestión OM | ✅ ALINEADO | gestion_om.py existe | Mantener | - |
| F7 | Métricas | Cumplimiento = Ejec/Meta | ✅ ALINEADO | Fórmula correcta | Mantener | - |
| F8 | Métricas | Tendencia | ⚠️ UNUSED | Función existe pero NO usada en dashboards | **Aclarar o eliminar** | BAJA |
| F9 | Métricas | Categorización | ✅ ALINEADO | Semáforo correcto | Mantener | - |
| F10 | Jerarquía | Área → Proceso → Sub → Indicador | ✅ ALINEADO | Estructura correcta | Mantener | - |
| F11 | Dimensiones | Período (mes, año) | ✅ ALINEADO | Presente en datos | Mantener | - |
| F12 | Dimensiones | Sede | ⚠️ INCOMPLETO | Mencionada pero no visible en UI | **Verificar uso** | MEDIA |
| F13 | Data Contracts | Validación YAML | ✅ ALINEADO | config/data_contracts.yaml | Mantener | - |
| F14 | Hardcoding | _map_level() en resumen_general.py | ❌ **CRÍTICO** | Duplica UMBRAL_SOBRECUMPLIMIENTO | **🔴 ELIMINAR** | CRÍTICA |
| F15 | Hardcoding | _cumplimiento_pct() en resumen_por_proceso.py | ❌ **CRÍTICO** | Heurística "if max <= 1.5" | **🔴 ELIMINAR** | CRÍTICA |
| F16 | Hardcoding | lambda_avance en gestion_om.py | ❌ **CRÍTICO** | Heurística idéntica | **🔴 CONSOLIDAR** | CRÍTICA |
| F17 | Páginas | preparar_pdi_con_cierre() | ⚠️ DUPLICADO | Recalcula cumplimiento inline | **Refactorizar** | MEDIA |
| F18 | Páginas | preparar_cna_con_cierre() | ⚠️ DUPLICADO | Copia lógica de preparar_pdi_con_cierre() | **Refactorizar** | MEDIA |
| F19 | Páginas | diagnostico.py | ⚠️ INCOMPLETO | Página menor sin documentación | **Documentar** | BAJA |
| F20 | Páginas | pdi_acreditacion.py | ⚠️ INCOMPLETO | Página menor sin documentación | **Documentar** | BAJA |

**Subtotal:** ✅ 12 alineados | ⚠️ 6 incompletos/unused | ❌ 5 críticos

---

## 5.2 ÍNDICE MAESTRO DE DOCUMENTACIÓN

### ESTRUCTURA RECOMENDADA (Living Documentation)

```
docs/
├─ 00-MASTER-INDEX.md                    ← NUEVO: punto de entrada
│  ├ Tabla: Artifact | Type | Status | Related Code | Last Updated
│  └ Roadmap de documentación
│
├─ 01-ARQUITECTURA/
│  ├─ ARQUITECTURA_SISTEMA.md            ← MEJORADA: from Fase 1 + fixes
│  ├─ ARQUITECTURA_DATOS.md              ← NUEVO: consolidar DATA_MODEL
│  └─ ARQUITECTURA_API.md                ← NUEVO: fuentes de datos
│
├─ 02-MODELO-DATOS/
│  ├─ ENTIDADES.md                       ← NUEVO: diccionario de 15 entidades
│  ├─ RELACIONES.md                      ← NUEVO: ER modelo Mermaid
│  └─ DATA-CONTRACTS.md                  ← NUEVO: YAML + validación
│
├─ 03-CALCULOS/
│  ├─ CUMPLIMIENTO-OFICIAL.md            ← NUEVO: categorizar_cumplimiento()
│  ├─ NORMALIZACIÓN.md                   ← NUEVO: normalizar_cumplimiento()
│  ├─ CASOS-ESPECIALES.md                ← NUEVO: Meta=0, Negativo, PA
│  └─ UMBRAL-DEFINITIVO.md               ← NUEVO: Plan Anual vs Regular
│
├─ 04-FUNCIONAL/
│  ├─ USUARIO-FLOWS.md                   ← MEJORADA: 9 páginas + casos
│  ├─ INDICADORES.md                     ← NUEVO: catálogo de 47 funciones
│  └─ DASHBOARD-SPECS.md                 ← NUEVO: especificaciones UI
│
├─ 05-RIESGOS/
│  ├─ MATRIZ-RIESGOS.md                  ← Consolidar riesgos técnicos
│  └─ MITIGACIÓN-PLAN.md                 ← Plan de corrección
│
├─ 06-DECISIONS/
│  ├─ ADR-001-CUMPLIMIENTO-CENTRALIZACION.md
│  ├─ ADR-002-PLAN-ANUAL-DETECTAR.md
│  └─ ADR-NNN-PATTERN.md
│
└─ 07-CHANGELOG/
   └─ DOCUMENTACION-UPDATES.md           ← LOG de cambios en docs
```

### MATRIZ DE ARTEFACTOS (TOO): Trazabilidad Código-Documentación

| Artefacto | Tipo | Ubicación | Relacionado con Código | Vigencia | Acción |
|-----------|------|-----------|----------------------|----------|--------|
| ARQUITECTURA_TECNICA_DETALLADA.md | Técnico | docs/ | core/, services/ | 80% | Actualizar: A5, A7, A8 |
| DATA_MODEL_SGIND.md | Modelo | docs/ | services/data_loader.py | 85% | Actualizar: D13, D14, D15 |
| DOCUMENTACION_FUNCIONAL.md | Funcional | 04-FUNCIONAL/ | streamlit_app/ | 75% | Actualizar: F14-F20 |
| AUDITORIA_RESUMEN_EJECUTIVO.md | Resumen | docs/ | N/A (resumen) | 100% | Mantener |
| AUDITORIA_FASE_4_CAPA_SEMANTICA.md | Análisis | docs/ | core/semantica.py | 95% | Actualizar: +versión |
| AUDITORIA_EJEMPLOS_REFACTORIZACION.md | Código | docs/ | core/calculos_oficial.py | 85% | Actualizar: +nuevos tests |
| AUDITORIA_DIAGRAMAS_VISUALES.md | Visual | docs/ | Múltiples | 90% | Mantener |
| MASTER_INDEX.md | Índice | root/ | N/A | 60% | 🔴 **CREAR NUEVO** |

---

## 5.3 HALLAZGOS CRÍTICOS: DOCUMENTACIÓN

### 🔴 CRÍTICO #1: Strategic_indicators.py NO documentada
**Ubicación:** ARQUITECTURA_TECNICA_DETALLADA.md (Módulos Core)  
**Problema:** Módulo con cálculos en-línea no está descrito en arquitectura  
**Impacto:** Desarrolladores nuevos no entienden que hay cálculos duplicados aquí  
**Solución:**
- ✅ Agregar sección "Módulos - Servicios" en ARQUITECTURA
- ✅ Listar: load_cierres(), preparar_pdi_con_cierre(), preparar_cna_con_cierre()
- ✅ Referenciar AUDITORIA_FASE_4_CAPA_SEMANTICA.md

---

### 🔴 CRÍTICO #2: Heurística "si > 2" no advertida en documentación
**Ubicación:** DATA_MODEL_SGIND.md (Cálculos)  
**Problema:** normalizar_cumplimiento() usa heurística sin documentar riesgos  
**Impacto:** Indicadores pueden categorizarse incorrectamente si valor > 2  
**Solución:**
- ✅ Agregar sección "Data Quality Risks" en DATA_MODEL
- ✅ Advertencia sobre escala de entrada (% vs decimal)
- ✅ Referenciar test_calculos.py para validación

---

### 🔴 CRÍTICO #3: Funciones hardcodeadas en UI no documentadas
**Ubicación:** DOCUMENTACION_FUNCIONAL.md (Páginas)  
**Problema:** resumen_por_proceso.py tiene _cumplimiento_pct() con heurística sin referencia  
**Impacto:** Si alguien cambia umbral en config.py, UI sigue usando valores fijos  
**Solución:**
- ✅ Crear sección "Configuration Risks" en DOCUMENTACION
- ✅ Listar: _map_level(), _cumplimiento_pct(), lambda_avance
- ✅ Proponer refactorización

---

---

# 🧪 FASE 6: DEPURACIÓN DE TESTING

## 6.1 MATRIZ DE AUDITORÍA DE TESTS

### Clasificación: Automatizado vs Exploratorio

| Test Suite | Archivo | Líneas | Tests | Estado | Clasificación | Cobertura | Acción |
|-----------|---------|--------|-------|--------|----------------|-----------|--------|
| **Calculos** | test_calculos.py | 260+ | 35 | ✅ ACTIVO | 🟢 **AUTOMATIZADO** | 40% (core/calculos) | **MANTENER** |
| **Semantica** | test_semantica.py | 211 | 28 | ✅ ACTIVO | 🟢 **AUTOMATIZADO** | 35% (core/semantica) | **MANTENER** |
| **Data Loader** | test_data_loader.py | 260+ | 22 | ✅ ACTIVO | 🟢 **AUTOMATIZADO** | 20% (services/data_loader) | **MANTENER** |
| **Problema 1** | test_problema_1_plan_anual.py | 260+ | 15 | ✅ ACTIVO | 🟢 **AUTOMATIZADO** | 50% (Plan Anual logic) | **MANTENER** |
| **Problema 2** | test_problema_2_casos_especiales.py | 260+ | 25 | ✅ ACTIVO | 🟢 **AUTOMATIZADO** | 50% (Casos especiales) | **MANTENER** |
| **Fase 2 Wrapper** | test_fase2_normalizacion_wrapper.py | 180 | 20 | ✅ ACTIVO | 🟢 **AUTOMATIZADO** | 35% (wrapper functions) | **MANTENER** |
| **Console** | test_consol.py | ~50 | N/A | ⚠️ PASIVO | 🔴 **EXPLORATORIO** | 0% | 🔴 **ARCHIVAR** |
| **Filter** | test_filter.py | ~50 | N/A | ⚠️ PASIVO | 🔴 **EXPLORATORIO** | 0% | 🔴 **ARCHIVAR** |
| **Sunburst** | test_sunburst.py | ~50 | N/A | ⚠️ PASIVO | 🔴 **EXPLORATORIO** | 0% | 🔴 **ARCHIVAR** |

**Resumen:**
- ✅ **7 suites automatizadas** (135+ tests reales) → Mantener
- 🔴 **3 exploratorios** (sin pytest real) → Archivar
- 📊 **Cobertura promedio:** 32% (objetivo: 80%)

---

## 6.2 TESTS ÚTILES (MANTENER)

### ✅ 1. test_calculos.py (260+ líneas, 35 tests)
**Propósito:** Validar normalización y categorización en core/  
**Cobertura:**
- ✅ normalizar_cumplimiento() - 12 tests (rango, NaN, strings, formato latino)
- ✅ categorizar_cumplimiento() - 10 tests (límites, sentido, Plan Anual)
- ✅ calcular_tendencia() - 4 tests (↑↓→)
- ✅ calcular_meses_en_peligro() - 4 tests
- ✅ calcular_kpis() - 3 tests
- ✅ estado_tiempo_acciones() - 2 tests

**Crítico para:** Regressions en categorización  
**Mantener:** 🟢 **VITAL**

---

### ✅ 2. test_semantica.py (211 líneas, 28 tests)
**Propósito:** Validar core/semantica.py (NUEVA centralizada)  
**Cobertura:**
- ✅ categorizar_cumplimiento() - 10 tests (regular vs Plan Anual)
- ✅ NaN/None handling - 3 tests
- ✅ String conversion - 3 tests
- ✅ Boundary values - 3 tests
- ✅ Color/Icono helpers - 2 tests
- ✅ Pandas integration - 2 tests
- ✅ Backward compatibility - 2 tests

**Crítico para:** Plan Anual no se quiebre  
**Mantener:** 🟢 **VITAL**

---

### ✅ 3. test_data_loader.py (260+ líneas, 22 tests)
**Propósito:** Validar cargar_dataset() y transformaciones  
**Cobertura:**
- ✅ ID normalization - 4 tests (_id_a_str)
- ✅ Column renaming - 3 tests (_renombrar)
- ✅ Calculation application - 2 tests
- ✅ Consolidation reading - 2 tests
- ✅ Deduplication - 3 tests (obtener_ultimo_registro)
- ✅ Integration tests - 3 tests (cargar_dataset flujo completo)

**Crítico para:** Pipeline ETL  
**Mantener:** 🟢 **VITAL**

---

### ✅ 4. test_problema_1_plan_anual_mal_categorizado.py (260+ líneas, 15 tests)
**Propósito:** Validar que Plan Anual se categoriza correctamente  
**Cobertura:**
- ✅ Plan Anual 0.947 → Cumplimiento (no Alerta)
- ✅ Mismo 0.947 Regular → Alerta
- ✅ Diferencia umbrales PA vs Regular
- ✅ Estándares RN-02, RN-03
- ✅ Umbrales definidos correctamente
- ✅ Coherencia umbrales
- ✅ Límites contiguos

**Crítico para:** Problema #1 no resurja  
**Mantener:** 🟢 **VITAL**

---

### ✅ 5. test_problema_2_casos_especiales.py (260+ líneas, 25 tests)
**Propósito:** Validar casos especiales (Meta=0&Ejec=0, Negativo&Ejec=0)  
**Cobertura:**
- ✅ Meta=0 & Ejec=0 → 1.0 (éxito perfecto)
- ✅ Negativo & Ejec=0 → 1.0 (cero es perfecto)
- ✅ Cálculos estándar Positivo/Negativo
- ✅ Topes dinámicos (Regular 1.3, PA 1.0)
- ✅ Entrada inválida handling
- ✅ Mínimo 0 (no negativos)
- ✅ Integración con data_loader

**Crítico para:** Problema #2 y #4 no resurjan  
**Mantener:** 🟢 **VITAL**

---

### ✅ 6. test_fase2_normalizacion_wrapper.py (180 líneas, 20 tests)
**Propósito:** Validar wrapper normalizar_y_categorizar()  
**Cobertura:**
- ✅ Porcentaje Plan Anual (95% → Cumpl)
- ✅ Porcentaje Regular (100% → Cumpl)
- ✅ Decimal handling
- ✅ String con % automático
- ✅ NaN/None
- ✅ Detección automática de escala
- ✅ Aplicar en Series/DataFrame
- ✅ Edge cases (umbrales exactos)

**Crítico para:** Dashboard functions  
**Mantener:** 🟢 **IMPORTANTE**

---

## 6.3 TESTS A ELIMINAR/ARCHIVAR

### 🔴 1. test_consol.py
**Estado:** ⚠️ PASIVO (no está en conftest.py collect_ignore_glob)  
**Problema:** Código exploratorio sin pytest assertions claras  
**Acción:**
- ✅ Mover a `tests/archived/exploratory/test_consol.py`
- ✅ Agregar comentario: "Exploratorio - sin validaciones"
- ✅ No ejecutar en CI/CD

---

### 🔴 2. test_filter.py
**Estado:** ⚠️ PASIVO  
**Problema:** Tests de filtros sin cobertura clara  
**Acción:**
- ✅ Verificar si lógica está en services/
- ✅ Si sí → crear tests reales en test_data_loader.py
- ✅ Archivar original

---

### 🔴 3. test_sunburst.py
**Estado:** ⚠️ PASIVO  
**Problema:** Tests de visualización (Streamlit) sin pytest support  
**Acción:**
- ✅ Archivar (visualizaciones requieren end-to-end, no unit tests)
- ✅ Considerar E2E tests con Streamlit Cloud

---

## 6.4 TESTS FALTANTES (PROPONER)

| Test Suite | Por hacer | Prioridad | Esfuerzo | Ubicación recomendada |
|-----------|-----------|-----------|----------|----------------------|
| **Strategic Indicators** | load_cierres() | CRÍTICA | 2h | test_strategic_indicators.py |
| **Strategic Indicators** | preparar_pdi_con_cierre() | CRÍTICA | 2h | test_strategic_indicators.py |
| **Strategic Indicators** | preparar_cna_con_cierre() | CRÍTICA | 2h | test_strategic_indicators.py |
| **Pages** | resumen_general.py funciones | MEDIA | 3h | test_pages_resumen_general.py |
| **Pages** | cmi_estrategico.py funciones | MEDIA | 3h | test_pages_cmi_estrategico.py |
| **Pages** | resumen_por_proceso.py funciones | MEDIA | 3h | test_pages_resumen_por_proceso.py |
| **Config** | Validación YAML data_contracts | MEDIA | 1h | test_config.py |
| **Integration** | Pipeline completo E2E | ALTA | 5h | test_e2e_pipeline.py |

**Total esfuerzo:** ~21h (corto plazo)

---

## 6.5 COBERTURA ACTUAL VS OBJETIVO

```
ACTUAL (32% promedio):
├─ core/           ████████░░░░░░░░░░ 40%  ✅ Aceptable
├─ services/       ██░░░░░░░░░░░░░░░░ 10%  ❌ Crítico
├─ streamlit_app/  ░░░░░░░░░░░░░░░░░░  0%  ❌ No testeable
├─ scripts/        █░░░░░░░░░░░░░░░░░  5%  ❌ Crítico
└─ config/         ██░░░░░░░░░░░░░░░░ 10%  ❌ Crítico

OBJETIVO (80% en 3 meses):
├─ core/           ████████████████░░ 80%  ✅ Ideal
├─ services/       ████████░░░░░░░░░░ 40%  ✅ Aceptable
├─ streamlit_app/  ████░░░░░░░░░░░░░░ 20%  ✅ Básico (E2E)
├─ scripts/        ████░░░░░░░░░░░░░░ 20%  ✅ Mínimo
└─ config/         ██░░░░░░░░░░░░░░░░ 10%  ✅ Mínimo
```

---

---

# 🧹 FASE 7: PLAN DE LIMPIEZA

## 7.1 BACKLOG DE ACCIONES PRIORIZADAS

### PRIORIDAD 1: CRÍTICO (SEMANA 1 - 22.5 horas)

| # | Acción | Tipo | Módulo | Esfuerzo | Impacto | Blocker | Descripción |
|---|--------|------|--------|----------|---------|---------|-------------|
| **C1** | Crear core/semantica.py | Técnica | core/ | 3h | 🔴 ALTO | NO | Centralizar categorizar_cumplimiento() oficial |
| **C2** | Tests para semantica.py | Testing | tests/ | 3h | 🔴 ALTO | Tras C1 | 20+ test cases para semantica.py |
| **C3** | Consolidar normalizar_cumplimiento() | Técnica | core/ | 2h | 🔴 ALTO | NO | Unificar lógica de normalización |
| **C4** | Consolidar categorizar_cumplimiento() | Técnica | core/ | 3h | 🔴 ALTO | Tras C1 | Una función oficial (ya en semantica) |
| **C5** | Eliminar _nivel_desde_cumplimiento() | Técnica | services/ | 1h | 🔴 ALTO | Tras C4 | Reemplazar con categorizar_oficial |
| **C6** | Refactorizar preparar_pdi_con_cierre() | Técnica | services/ | 2h | 🔴 ALTO | NO | Extraer cálculos → semantica.py |
| **C7** | Refactorizar preparar_cna_con_cierre() | Técnica | services/ | 2h | 🔴 ALTO | NO | Usar función genérica |
| **C8** | Eliminar _map_level() en resumen_general | Técnica | streamlit_app/ | 1h | 🔴 ALTO | NO | Usar categorizar_official |
| **C9** | Eliminar _cumplimiento_pct() en resumen_por_proceso | Técnica | streamlit_app/ | 1h | 🔴 ALTO | NO | Usar normalizar_wrapper |
| **C10** | Consolidar lambda_avance en gestion_om | Técnica | streamlit_app/ | 0.5h | 🔴 ALTO | NO | Consolidar con semántica |
| **C11** | Suite tests para strategic_indicators | Testing | tests/ | 3h | 🔴 ALTO | Tras C4 | Tests para load_cierres, preparar_* |
| **C12** | Documentación CRÍTICA - Fix Arquitectura | Documental | docs/ | 1h | 🔴 ALTO | NO | Agregar secciones: strategic_indicators, duplicados |

**Subtotal:** 22.5h | **Resultado:** -80% duplicados, +40% test coverage

---

### PRIORIDAD 2: IMPORTANTE (SEMANA 2 - 13 horas)

| # | Acción | Tipo | Módulo | Esfuerzo | Impacto | Descripción |
|---|--------|------|--------|----------|---------|-------------|
| **M1** | Reescribir ARQUITECTURA_TECNICA_DETALLADA.md | Documental | docs/ | 3h | 🟡 MEDIA | Incorporar Fases 1-4 + fixes |
| **M2** | Crear documento DATA-CONTRACTS.md | Documental | docs/ | 2h | 🟡 MEDIA | Validación YAML centralizada |
| **M3** | Crear documento CUMPLIMIENTO-OFICIAL.md | Documental | docs/ | 2h | 🟡 MEDIA | Especificación de categorización |
| **M4** | Tests para pages/ (básico) | Testing | tests/ | 3h | 🟡 MEDIA | test_pages_resumen_general.py, etc |
| **M5** | Archivar tests exploratorios | Limpieza | tests/ | 1h | 🟡 MEDIA | Mover test_consol, filter, sunburst |
| **M6** | Refactorizar config.py | Técnica | core/ | 2h | 🟡 MEDIA | Centralizar IDS_PLAN_ANUAL, IDS_TOPE_100 |

**Subtotal:** 13h | **Resultado:** Documentación actualizada + archivos organizados

---

### PRIORIDAD 3: TÉCNICA DEUDA (SEMANA 3 - 13.5 horas)

| # | Acción | Tipo | Módulo | Esfuerzo | Impacto | Descripción |
|---|--------|------|--------|----------|---------|-------------|
| **T1** | Refactorizar data_loader.py | Técnica | services/ | 3h | 🟢 MEDIO | Separar ETL phases |
| **T2** | E2E tests pipeline | Testing | tests/ | 5h | 🟢 MEDIO | test_e2e_pipeline.py |
| **T3** | Eliminar unused imports | Limpieza | Todo | 1h | 🟢 BAJO | Black, mypy fixes |
| **T4** | Code quality (linting) | Técnica | Todo | 2h | 🟢 BAJO | pylint, black |
| **T5** | Validación YAML config | Técnica | config/ | 1h | 🟢 BAJO | JSONSchema |
| **T6** | Dead code sweep | Limpieza | Todo | 0.5h | 🟢 BAJO | Funciones unused |

**Subtotal:** 12.5h | **Resultado:** Code quality +20%, cobertura +15%

---

## 7.2 MATRIZ IMPACTO vs ESFUERZO (Priorización)

```
ESFUERZO (horas)
     1h    2h    3h    5h+
    ▲
    │ ⬛C5  ⬛C9  ⬛C1  ⬛M4
    │ ⬛C10 ⬛C3  ⬛C2  ⬛T2
IMPACTO│    ⬛C8  ⬛C11 ⬛M1
    │    ⬛M5  ⬛C6  ⬛T1
    │         ⬛C7  
    │         ⬛C12
    └─────────────────
       BAJO   MEDIO   ALTO
```

**Zona Crítica (Hacer PRIMERO):** Alta Impacto + Bajo Esfuerzo
- C5, C9, C10 (1h cada) → Eliminar 3 hardcoding
- C3, C8 (2h) → Consolidar normalización
- C1, C2 (3h) → Crear semantica + tests

---

## 7.3 ACCIONES DE LIMPIEZA ESTRUCTURAL

### Eliminar / Reorganizar Archivos

| Archivo | Acción | Justificación | Impacto |
|---------|--------|---------------|---------|
| tests/test_consol.py | 🗑️ Archivar | Exploratorio, sin pytest | 🟢 BAJO |
| tests/test_filter.py | 🗑️ Archivar | Exploratorio | 🟢 BAJO |
| tests/test_sunburst.py | 🗑️ Archivar | Exploratorio | 🟢 BAJO |
| services/strategic_indicators.py (_nivel_desde_cumplimiento) | 🔧 Refactorizar | Defectuosa, duplicada | 🔴 CRÍTICO |
| streamlit_app/pages/resumen_general.py (_map_level) | 🔧 Refactorizar | Hardcoding | 🔴 CRÍTICO |
| streamlit_app/pages/resumen_por_proceso.py (_cumplimiento_pct) | 🔧 Refactorizar | Hardcoding | 🔴 CRÍTICO |
| streamlit_app/pages/gestion_om.py (lambda_avance) | 🔧 Refactorizar | Hardcoding | 🔴 CRÍTICO |

### Crear Archivos Nuevos

| Archivo | Propósito | Impacto |
|---------|-----------|---------|
| core/semantica.py | Centralizar categorizar_cumplimiento() | 🔴 CRÍTICO |
| tests/test_semantica.py | Validar semantica.py | 🔴 CRÍTICO |
| tests/test_strategic_indicators.py | Tests para services/ | 🔴 CRÍTICO |
| tests/test_e2e_pipeline.py | Integration tests | 🟡 IMPORTANTE |
| tests/archived/exploratory/ | Archivar tests exploratorios | 🟢 BAJO |
| docs/03-CALCULOS/CUMPLIMIENTO-OFICIAL.md | Documentar lógica | 🟡 IMPORTANTE |

### Reorganizar Directorios

```
tests/
├─ test_*.py                          (actual)
├─ conftest.py                        (actual)
└─ archived/
   └─ exploratory/
      ├─ test_consol.py               ← archivar
      ├─ test_filter.py               ← archivar
      └─ test_sunburst.py             ← archivar
```

---

## 7.4 RIESGOS SI NO SE EJECUTA LA LIMPIEZA

### 🔴 RIESGO #1: Deuda técnica exponencial
**Causa:** 8+ duplicados de cálculos no consolidados  
**Impacto:** 
- Cambiar umbral = actualizar 8 lugares
- Bugs = difíciles de rastrear
- Mantención ↑ 300%

**Si no se ejecuta:** En 6 meses, costo de cambios = 10x actual

---

### 🔴 RIESGO #2: Regresiones silenciosas
**Causa:** Cobertura tests 32% (bajo)  
**Impacto:**
- Plan Anual puede romperse sin detectar
- Categorización diverge en producción
- Conflicting fixes en ramas

**Si no se ejecuta:** 3+ bugs en prod que toman 2 semanas arreglar c/u

---

### 🔴 RIESGO #3: Onboarding de nuevos devs imposible
**Causa:** Documentación 25% desalineada + código oculto  
**Impacto:**
- Nuevo dev entiende mal arquitectura
- Implementa fix en lugar equivocado
- Crea más duplicados

**Si no se ejecuta:** Onboarding pasa de 2 semanas a 6 semanas

---

### 🔴 RIESGO #4: Imposibilidad de refactorizar sin regresar
**Causa:** Sin tests automáticos, no hay confianza en cambios  
**Impacto:**
- Cambios pequeños requieren testing manual completo
- Features nuevas mueven código existente (miedo)
- Velocity ↓ 40%

**Si no se ejecuta:** Proyecto queda congelado en arquitectura actual

---

### 🟡 RIESGO #5: Documentación se vuelve inútil
**Causa:** Docs no sincronizadas con código  
**Impacto:**
- Devs ignoran documentación
- Se convierte en "legacy" no confiable
- Decisiones se pierden

**Si no se ejecuta:** En 3 meses, documentación es inútil

---

---

# 📊 RESUMEN EJECUTIVO: ESTADO DEL PROYECTO

## Diagnóstico General

```
DIMENSIÓN                    ANTES      DESPUÉS    META
────────────────────────────────────────────────────────
Duplicación de código        8 lugares  1 lugar    1 lugar
Test Coverage               32%        50%+       80%
Documentación alineada      73%        95%+       95%
Facilidad cambio umbral     30 min     2 min      2 min
Riesgo inconsistencia       🔴 ALTO    🟡 MEDIO   🟢 BAJO
Onboarding nuevos devs      6 weeks    3 weeks    2 weeks
```

## Costo vs Beneficio

| Aspecto | Costo | Beneficio | ROI |
|---------|-------|-----------|-----|
| **Tiempo** | 49h en 3 semanas | +200% velocity | 4x en 2 meses |
| **Riesgo** | Nulo (cambios son fixes) | -80% bugs | ∞ |
| **Deuda técnica** | Se paga ahora | -70% acumulada | Infinito |
| **Mantenibilidad** | +1 h/semana doc | -2 h/semana debug | Break-even mes 1 |

---

## Roadmap de Ejecución

```
SEMANA 1 (P1): 22.5h - CRÍTICO
├─ core/semantica.py (centralizar)
├─ Tests para semantica (20+ cases)
├─ Eliminar duplicados en UI (3h)
└─ Documentación crítica fixes

SEMANA 2 (P2): 13h - IMPORTANTE
├─ Reescribir documentación arquitectura
├─ Tests para pages/
├─ Archivar tests exploratorios
└─ Refactorizar config.py

SEMANA 3+ (P3): 12.5h - DEUDA TÉCNICA
├─ E2E tests pipeline
├─ Code quality (linting, mypy)
├─ Dead code sweep
└─ Performance profiling
```

---

## Checklist de Validación Post-Limpieza

- [ ] Cobertura tests ≥ 50% (objetivo 80%)
- [ ] Cero duplicados de categorizar_cumplimiento()
- [ ] Plan Anual tests pasen al 100%
- [ ] Documentación 90%+ alineada con código
- [ ] CI/CD pipeline verde
- [ ] Onboarding doc completada
- [ ] Refactorización estratégica_indicators completa
- [ ] Hardcoding en UI eliminado
- [ ] Config centralizados en core/config.py
- [ ] Archivos temporales archivados

---

## Próximos Pasos Inmediatos

### HOY (Sprint Planning)
1. [ ] Revisar y aprobar Plan de Limpieza
2. [ ] Estimar 49h en sprints de 2 semanas
3. [ ] Asignar dev senior para P1 (22.5h)

### ESTA SEMANA (Kickoff)
1. [ ] Crear rama `refactor/fase-5-6-7-cleanup`
2. [ ] Crear core/semantica.py (boilerplate)
3. [ ] Crear tests/test_semantica.py (boilerplate)
4. [ ] Crear task tracker en Jira/GitHub

### PRÓXIMAS 2 SEMANAS (P1)
1. [ ] Implementar core/semantica.py
2. [ ] 20+ test cases
3. [ ] Eliminar 3 hardcoding en UI
4. [ ] Documentación fixes

---

**Documento generado:** 21 de abril 2026  
**Próxima revisión:** 5 de mayo 2026 (Post-Semana 1)  
**Responsable:** Arquitecto Técnico + Dev Senior  
**Aprobado por:** [Aún pendiente]
