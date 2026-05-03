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

## 2. Decisiones Arquitectónicas

### 2.1 Decisión: Sin Redis Cloud

| Aspecto | Decisión |
|---------|----------|
| **Opción considerada** | Redis Cloud para caché |
| **Decisión final** | NO implementar Redis Cloud |
| **Razón** | Sin presupuesto de inversión |
| **Alternativa** | Caché local en memoria con TTL configurable |

**Implementación:**
```python
# core/config.py
CACHE_TTL = 300  # 5 minutos
```

### 2.2 Decisión: Hoja Principal Semestral

| Aspecto | Decisión |
|---------|----------|
| **Hoja principal** | Consolidado Semestral |
| **Excepción** | Gestion OM usa Consolidado Historico |
| **Razón** | Separación de concerns, optimización |

### 2.3 Decisión: Excel como Persistencia

| Aspecto | Decisión |
|---------|----------|
| **Formato** | Excel (.xlsx) con fórmulas |
| **Razón** | Auditorías manuales, transparencia |
| **Alternativa futura** | PostgreSQL para producción |

### 2.4 Decisión: Mantener granularidad y agrupar en UI (CMI Estratégico)

| Aspecto | Decisión |
|---------|----------|
| **Problema** | Replicación visual de indicadores en pestaña por Línea/Meta |
| **Decisión final (PO)** | Mantener granularidad en datos y agrupar únicamente en UI |
| **Razón** | Evitar pérdida de detalle histórico/funcional en catálogo y cierres |
| **Implementación** | Agrupación por `Id` (fallback `Indicador`) en render de `tab_lineas.py` |

**Impacto controlado:**
- No se modifica lógica de cálculo ni consolidación.
- No se compacta catálogo en backend.
- Se evita duplicación visual sin afectar trazabilidad.

**Archivos relacionados:**
- [`streamlit_app/components/cmi_tabs/tab_lineas.py`](../../streamlit_app/components/cmi_tabs/tab_lineas.py)
- [`streamlit_app/components/cmi_tabs/tab_alertas.py`](../../streamlit_app/components/cmi_tabs/tab_alertas.py)
- [`services/ai_analysis.py`](../../services/ai_analysis.py)
- [`scripts/detect_inconsistencias.py`](../../scripts/detect_inconsistencias.py)

---

## 3. Consolidados de Decisiones

### 3.1 Decisión Problema 1 Opción A (Mejorada)

**Resumen:** Implementar refactorización DRY con función genérica parametrizable.

**Detalles:**
- Función `_generic_loader(flag_col, catalog_fn, merge_cols)`
- Reutilización entre PDI y CNA
- Tests de regresión passing

**Archivo:** [`DECISION_PROBLEMA_1_OPCION_A_MEJORADA.md`](../../08-PROBLEMAS-RESUELTOS/DECISION_PROBLEMA_1_OPCION_A_MEJORADA.md)

---

## 4. Governance de Documentación

### 4.1 Principios

1. **Single Source of Truth (SSOT):** Toda docs en `/docs/`
2. **KISS:** Cada documento = un solo propósito
3. **Documentación Viva:** Sincronizada con código
4. **Sin "Por si acaso":** No conservar docs obsoletos

### 4.2 Reducción MDV

| Métrica | Antes | Después | Reducción |
|---------|-------|---------|-----------|
| Documentos | 81 | 7 | **91%** |
| Carpetas | 16 | 2 (core, sql) | 87% |

**Target logrado:** 5-7 documentos finales en `docs/core/`

---

## 5. Lecciones Aprendidas

### 5.1 DRY Violations

**Pattern identificado:** Cuando 2+ funciones difieren solo en:
- Filter conditions
- Resource loaders
- Merge column names

**Solución genérica:** Extraer como parámetros.

### 5.2 Enum Comparisons

**Problema común:** Comparar enums directamente con strings.

**Solución:** Usar `.value` en comparaciones.

```python
# INCORRECTO
assert cat == CategoriaCumplimiento.PELIGRO

# CORRECTO
assert cat == CategoriaCumplimiento.PELIGRO.value
```

### 5.3 Testing Strategy

**Approach:** Tests unitarios por suite, fixtures centralizadas.

**Validación:** Sin regresiones en APIs públicas.

---

## 6. Referencias

- **Problemas resueltos:** [`08-PROBLEMAS-RESUELTOS/`](../../08-PROBLEMAS-RESUELTOS/)
- **Governance:** [`GOVERNANCE.md`](../../GOVERNANCE.md)
- **Decisiones:** [`DECISION_PROBLEMA_1_OPCION_A_MEJORADA.md`](../../08-PROBLEMAS-RESUELTOS/DECISION_PROBLEMA_1_OPCION_A_MEJORADA.md)
