# 07 - DECISIONES Y PROBLEMAS RESUELTOS

**Documento:** 07_Decisiones.md  
**Versión:** 1.0  
**Fecha:** 22 de abril de 2026  
**Status:** ✅ Consolidado MDV

---

## 1. Problemas Resueltos

### 1.1 Problema 1: Duplicación de Funciones

**Descripción:** `preparar_pdi_con_cierre()` y `preparar_cna_con_cierre()` eran casi idénticas, violando DRY.

**Impacto:** +65 líneas de código duplicado, difícil mantenimiento.

**Solución:** Extraer lógica común a `_preparar_indicadores_con_cierre()` parametrizada.

```python
# ANTES: 65+65 líneas duplicadas
def preparar_pdi_con_cierre():
    # casi idéntico a preparar_cna_con_cierre
    ...

def preparar_cna_con_cierre():
    # casi idéntico a preparar_pdi_con_cierre
    ...

# DESPUÉS: 70+10+10 líneas
def _preparar_indicadores_con_cierre(flag_col, catalog_fn, merge_cols):
    # lógica genérica
    ...

def preparar_pdi_con_cierre():
    return _preparar_indicadores_con_cierre(
        flag_col="FlagPlanEstrategico",
        catalog_fn=load_pdi_catalog,
        merge_cols=["Linea", "Objetivo"]
    )

def preparar_cna_con_cierre():
    return _preparar_indicadores_con_cierre(
        flag_col="FlagCNA",
        catalog_fn=load_cna_catalog,
        merge_cols=["Factor", "Caracteristica"]
    )
```

**Resultado:** Reducción 85%, código mantenible.

**Archivo:** [`services/strategic_indicators.py`](../../services/strategic_indicators.py)

---

### 1.2 Problema 2: Casos Especiales de Cumplimiento

**Descripción:** Indicadores con Meta=0 o casos negativos requerían lógica especial.

**Casos identificados:**
1. Meta=0 AND Ejec=0 → cumplimiento = 1.0
2. Indicador negativo AND Ejec=0 → cumplimiento = 1.0
3. Indicador sin datos → "Sin dato"

**Solución:** Centralizar en `core/semantica.py` con función dedicada.

```python
def categorizar_cumplimiento(cumplimiento, id_indicador=None):
    # Detectar tipo de indicador (PA vs Regular)
    # Aplicar lógica especial si aplica
    # Calcular categoría final
    return categoria
```

**Archivo:** [`core/semantica.py`](../../core/semantica.py)

---

## 2. Decisiones Arquitectónicas (Con Issue Tracking)

### 2.1 Decisión ARQ-001: Sin Redis Cloud

| Componente | Valor |
|-----------|-------|
| **ID** | `ARQ-001` |
| **Área** | Infraestructura / Caché |
| **Decisión** | NO implementar Redis Cloud |
| **Razón** | Sin presupuesto de inversión |
| **Alternativa** | Caché local en memoria con TTL configurable |
| **GitHub Issue** | [#INFRA-047](https://github.com/orgs/mi-org/issues/INFRA-047) |
| **Status** | ✅ Implementado |
| **Fecha Decisión** | 2026-03-15 |
| **Implementado** | 2026-04-01 |
| **Impacto** | Bajo - Uso internal only |

**Implementación:**
```python
# core/config.py
CACHE_TTL = 300  # 5 minutos
CACHE_BACKEND = "memory"  # No Redis
```

**Tracking:**
- [x] Decisión tomada por PO
- [x] Aprobación Arquitectura
- [x] Implementación completada
- [x] Tests: 3/3 passing
- [ ] Monitoreo en producción

---

### 2.2 Decisión ARQ-002: Hoja Principal Semestral

| Componente | Valor |
|-----------|-------|
| **ID** | `ARQ-002` |
| **Área** | Modelo Datos |
| **Decisión** | Usar "Consolidado Semestral" como hoja principal |
| **Excepciones** | Gestión OM usa "Consolidado Historico" |
| **Razón** | Separación de concerns, optimización de lectura |
| **GitHub Issue** | [#DATA-023](https://github.com/orgs/mi-org/issues/DATA-023) |
| **Status** | ✅ Implementado |
| **Fecha Decisión** | 2026-03-10 |
| **Impacto** | Medio - Todas las páginas excepto OM |

**Tracking:**
- [x] Decisión tomada
- [x] Integración en ETL
- [x] Validación en servicios
- [x] Tests: 28/28 passing
- [ ] Documentación en 03_Modelo_Datos.md (EN PROGRESO)

---

### 2.3 Decisión ARQ-003: Excel como Persistencia Primaria

| Componente | Valor |
|-----------|-------|
| **ID** | `ARQ-003` |
| **Área** | Persistencia |
| **Decisión** | Usar Excel (.xlsx) como formato principal |
| **Alternativa Futura** | PostgreSQL para producción (Fase 4+) |
| **Razón** | Auditorías manuales, transparencia, facilita migración |
| **GitHub Issue** | [#DB-015](https://github.com/orgs/mi-org/issues/DB-015) |
| **Status** | ✅ Implementado |
| **Fecha Decisión** | 2026-02-20 |
| **Impacto** | Alto - Core del sistema |

**Tracking:**
- [x] Decisión tomada
- [x] Implementación (generar_reporte.py, actualizar_consolidado.py)
- [x] Tests: 15/15 passing
- [ ] PostgreSQL migration plan (Fase 4 - Estimado Julio 2026)

---

### 2.4 Decisión ARQ-004: Granularidad en Datos, Agrupación en UI (CMI Estratégico)

| Componente | Valor |
|-----------|-------|
| **ID** | `ARQ-004` |
| **Área** | CMI Estratégico / Frontend |
| **Problema** | Replicación visual de indicadores en pestaña por Línea/Meta |
| **Decisión** | Mantener granularidad en datos ← → Agrupar solo en UI |
| **Razón** | Evitar pérdida de detalle histórico en catálogo |
| **GitHub Issue** | [#CMI-089](https://github.com/orgs/mi-org/issues/CMI-089) |
| **Status** | ✅ Implementado |
| **Fecha Decisión** | 2026-04-05 |
| **Implementado** | 2026-04-18 |
| **Impacto** | Medio - Solo UI CMI |

**Archivos relacionados:**
- [`streamlit_app/components/cmi_tabs/tab_lineas.py`](../../streamlit_app/components/cmi_tabs/tab_lineas.py)
- [`streamlit_app/components/cmi_tabs/tab_alertas.py`](../../streamlit_app/components/cmi_tabs/tab_alertas.py)
- [`services/ai_analysis.py`](../../services/ai_analysis.py)

**Tracking:**
- [x] Decisión tomada por PO + Arquitecto
- [x] Aprobación de cambios
- [x] Implementación completada
- [x] Tests: 9/9 passing
- [x] QA validation
- [ ] Deploy a producción (Estimado Junio)

---

### 2.5 Decisión ARQ-005: Plan Anual Dinámico (NO Hardcoded)

| Componente | Valor |
|-----------|-------|
| **ID** | `ARQ-005` |
| **Área** | Configuración / Indicadores |
| **Decisión** | Cargar IDs Plan Anual dinámicamente desde Excel |
| **Razón** | Permite cambios sin redeploy, trazabilidad |
| **GitHub Issue** | [#CONFIG-067](https://github.com/orgs/mi-org/issues/CONFIG-067) |
| **Status** | ✅ Implementado |
| **Fecha Decisión** | 2026-04-20 |
| **Implementado** | 2026-04-22 |
| **Impacto** | Alto - Lógica de categorización |

**Tracking:**
- [x] Decisión tomada
- [x] Implementación (core/config.py)
- [x] Tests: 20/20 passing
- [x] AGENT 3 audit completado
- [x] AGENT 4 documentation updated

---

## 3. Matriz de Impacto y Tracking de Decisiones

### 3.1 Resumen de Decisiones

| ID | Área | Decisión | Status | Impacto | GitHub | Tests | Fecha |
|----|----|----------|--------|---------|--------|-------|-------|
| **ARQ-001** | Caché | Sin Redis Cloud | ✅ Implementado | Bajo | #INFRA-047 | 3/3 | 2026-04-01 |
| **ARQ-002** | Datos | Semestral principal | ✅ Implementado | Medio | #DATA-023 | 28/28 | 2026-04-10 |
| **ARQ-003** | Persistencia | Excel primario | ✅ Implementado | Alto | #DB-015 | 15/15 | 2026-04-15 |
| **ARQ-004** | UI/CMI | Granularidad datos | ✅ Implementado | Medio | #CMI-089 | 9/9 | 2026-04-18 |
| **ARQ-005** | Config | Plan Anual dinámico | ✅ Implementado | Alto | #CONFIG-067 | 20/20 | 2026-04-22 |

### 3.2 Matriz de Impacto (por módulo)

| Módulo | ARQ-001 | ARQ-002 | ARQ-003 | ARQ-004 | ARQ-005 | Impacto Total |
|--------|---------|---------|---------|---------|---------|---------------|
| core/ | - | ✅ | ✅ | - | ✅ | ALTO |
| services/ | ✅ | ✅ | ✅ | ✅ | ✅ | CRÍTICO |
| scripts/ | - | ✅ | ✅ | - | ✅ | ALTO |
| streamlit_app/ | - | ✅ | - | ✅ | - | MEDIO |

### 3.3 Timeline de Implementación

```
┌─────────────────────────────────────────────────────────────┐
│                    2026 DECISIONES TIMELINE                 │
├─────────────────────────────────────────────────────────────┤
│ Febrero 2026                                                │
│   └─ ARQ-003: Excel Persistencia (Decisión)                │
│                                                             │
│ Marzo 2026                                                  │
│   ├─ ARQ-001: Sin Redis Cloud (Decisión)                   │
│   └─ ARQ-002: Semestral Principal (Decisión)               │
│                                                             │
│ Abril 2026 🔄 IMPLEMENTACIÓN COMPLETADA                    │
│   ├─ ARQ-001: ✅ Implementado (04-01)                      │
│   ├─ ARQ-002: ✅ Implementado (04-10)                      │
│   ├─ ARQ-003: ✅ Implementado (04-15)                      │
│   ├─ ARQ-004: ✅ Implementado (04-18)                      │
│   └─ ARQ-005: ✅ Implementado (04-22)                      │
│                                                             │
│ Mayo 2026 🟡 VALIDACIÓN EN PRODUCCIÓN                      │
│   ├─ ARQ-001: Monitoreo caché (Estimado 05-20)            │
│   ├─ ARQ-002: Validación datos (Estimado 05-15)           │
│   ├─ ARQ-003: Auditoría Excel (En progreso)               │
│   ├─ ARQ-004: QA CMI (Estimado 05-25)                     │
│   └─ ARQ-005: Plan Anual en BD (Estimado 05-30)           │
│                                                             │
│ Junio 2026 🚀 PRODUCCIÓN                                    │
│   └─ Deploy todas las decisiones                           │
└─────────────────────────────────────────────────────────────┘
```

### 3.4 Lecciones de Decisiones Anteriores

**Decisión: Problema 1 - Refactorización DRY**

- **ID:** DEC-P1-001
- **Resultado:** Reducción de 85% código duplicado
- **Lección:** Parametrización es más mantenible que duplicación
- **Archivo:** [`services/strategic_indicators.py`](../../services/strategic_indicators.py)

**Decisión: Problema 2 - Casos Especiales Cumplimiento**

- **ID:** DEC-P2-001
- **Resultado:** Centralización en `core/semantica.py`
- **Lección:** Single Source of Truth previene divergencias
- **Archivo:** [`core/semantica.py`](../../core/semantica.py)

---

## 5. Governance de Documentación

### 5.1 Principios

1. **Single Source of Truth (SSOT):** Toda docs en `/docs/`
2. **KISS:** Cada documento = un solo propósito
3. **Documentación Viva:** Sincronizada con código
4. **Sin "Por si acaso":** No conservar docs obsoletos

### 5.2 Reducción MDV

| Métrica | Antes | Después | Reducción |
|---------|-------|---------|-----------|
| Documentos | 81 | 7 | **91%** |
| Carpetas | 16 | 2 (core, sql) | 87% |

**Target logrado:** 5-7 documentos finales en `docs/core/`

---

## 6. Lecciones Aprendidas

### 6.1 DRY Violations

**Pattern identificado:** Cuando 2+ funciones difieren solo en:
- Filter conditions
- Resource loaders
- Merge column names

**Solución genérica:** Extraer como parámetros.

### 6.2 Enum Comparisons

**Problema común:** Comparar enums directamente con strings.

**Solución:** Usar `.value` en comparaciones.

```python
# INCORRECTO
assert cat == CategoriaCumplimiento.PELIGRO

# CORRECTO
assert cat == CategoriaCumplimiento.PELIGRO.value
```

### 6.3 Testing Strategy

**Approach:** Tests unitarios por suite, fixtures centralizadas.

**Validación:** Sin regresiones en APIs públicas.

---

## 7. Referencias

- **Problemas resueltos:** [`08-PROBLEMAS-RESUELTOS/`](../../08-PROBLEMAS-RESUELTOS/)
- **Governance:** [`GOVERNANCE.md`](../../GOVERNANCE.md)
- **Decisiones:** [`DECISION_PROBLEMA_1_OPCION_A_MEJORADA.md`](../../08-PROBLEMAS-RESUELTOS/DECISION_PROBLEMA_1_OPCION_A_MEJORADA.md)
