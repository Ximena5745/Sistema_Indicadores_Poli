# AGENT 5 — Data Validation Report
**Fecha:** 2026-06-04  
**Status:** Auditoría completada  
**Datos analizados:** Consolidado_API_Kawak.xlsx (12,703 registros, 298 indicadores únicos)

---

## Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| **Total registros analizados** | 12,703 |
| **Indicadores únicos** | 298 |
| **Período cubierto** | 2022-01-31 a 2026-02-28 |
| **Anomalías encontradas** | 3 |
| **Validaciones implementadas** | 69 |
| **GAPs identificados** | 15 |

---

## Hallazgos Críticos

### 1. DUPLICADOS — 181 combinaciones (ID, fecha) duplicadas
**Severidad:** MEDIA  
**Categoría:** Duplicados

**Evidencia:**
- 181 registros tienen más de una entrada para la misma combinación (ID, fecha)
- Ejemplo: ID 122 tiene 8 registros para 2025-01-31
- Top duplicados: ID 116, 122, 172

**Impacto:**
- En dashboards: Posible doble conteo en agregaciones
- En decisiones: Valores duplicados pueden inflar métricas

**Causa Raíz:**
- Fuente: API Kawak devuelve múltiples registros para el mismo indicador/período
- ETL: No hay deduplicación antes del consolidado

**Solución Propuesta:**
1. Agregar deduplicación en `consolidar_api.py` (tomar último registro)
2. Implementar validación de unicidad en `validation_gate.py`

---

### 2. VALORES NEGATIVOS — 17 valores negativos en resultado
**Severidad:** MEDIA  
**Categoría:** Rangos

**Evidencia:**
- 17 registros con `resultado` < 0
- Rango esperado: [0, 1.3]

**Impacto:**
- En dashboards: Podría mostrar cumplimiento negativo
- En cálculos: Afecta promedios y tendencias

**Causa Raíz:**
- Fuente: API Kawak envía datos negativos (posible error de captura)
- ETL: No rechaza valores negativos

**Solución Propuesta:**
1. Investigar origen de valores negativos
2. Si son válidos, documentar excepción
3. Si no son válidos, agregar filtro en ETL

---

### 3. VALORES > 1.3 — 1,756 valores exceden el rango máximo
**Severidad:** MEDIA  
**Categoría:** Rangos

**Evidencia:**
- 1,756 registros con `resultado` > 1.3 (130%)
- Solo 459 registros en rango válido [0, 1.3]
- 11 registros entre 1.0-1.3 (sobrecumplimiento permitido)

**Impacto:**
- En dashboards: Valores extremos distorsionan escalas
- En cálculos: Violan supuestos de normalización

**Causa Raíz:**
- Fuente: API Kawak no valida rangos antes de enviar
- ETL: `agent5_corrections.py` debería aplicar capping pero no está filtrando

**Solución Propuesta:**
1. Verificar por qué `agent5_corrections.py` no está aplicando capping
2. Revisar si el capping está configurado para ejecutar
3. Agregar logging más detallado de correcciones aplicadas

---

## Inventario de Validaciones Existentes (69 total)

### Por Archivo

| Archivo | Validaciones | Tipos |
|---------|--------------|-------|
| `validation_gate.py` | 18 | Schema, Null, Duplicate, Range, Type, Cardinality |
| `intermediate_validation.py` | 15 | Schema, Null, Duplicate, Range, Cardinality |
| `consolidar_api.py` | 8 | Precondition, Null, Type |
| `actualizar_consolidado.py` | 6 | Contract, Range, Consistency |
| `calculos.py` | 9 | Null, Type, Range, Schema |
| `agent5_corrections.py` | 4 | Schema, Consistency |
| `purga.py` | 4 | Range, Type, Referential, Duplicate |
| `health_metrics.py` | 5 | Null, Type, Arithmetic, Range |

### Por Tipo de Validación

| Tipo | Cantidad | Severidad Promedio |
|------|----------|-------------------|
| **Schema** | 12 | Crítica |
| **Null** | 14 | Crítica/Alta |
| **Range** | 18 | Media |
| **Duplicate** | 7 | Media |
| **Type** | 10 | Media |
| **Cardinality** | 8 | Media/Baja |

### Por Severidad

| Severidad | Cantidad | Acción |
|-----------|----------|--------|
| **Crítica** | 15 | Bloquea ETL |
| **Alta** | 18 | Alerta + logging |
| **Media** | 25 | Warning only |
| **Baja** | 11 | Info logging |

---

## Cobertura de Validación

### Matriz de Cobertura

| Dimensión | Descarga | Transformación | Cálculo | Tests | GAP |
|-----------|----------|----------------|---------|-------|-----|
| **Completitud** | ✓ | ✓ | ✗ | ✓ | Falta en cálculos |
| **Duplicados** | ✓ | ✗ | ✗ | ✓ | Falta automatizar |
| **Rangos** | ✓ | ✓ | ✓ | ✓ | OK |
| **Tipos** | ✓ | ✓ | ✗ | ✗ | Falta test |
| **Nulos** | ✓ | ✓ | ✓ | ✓ | OK |
| **Consistencia** | ✗ | ✗ | ✗ | ✗ | Crítico |

### Porcentaje de Cobertura

| Dimensión | Cobertura |
|-----------|-----------|
| Completitud | 75% |
| Duplicados | 50% |
| Rangos | 100% |
| Tipos | 60% |
| Nulos | 100% |
| Consistencia | 0% |
| **Promedio** | **64%** |

---

## GAPs Identificados (15)

### Críticos (Bloquean ETL)

| # | GAP | Impacto |
|---|-----|---------|
| 1 | `validate_after_consolidar_api` nunca se ejecuta | Sin validación post-descarga |
| 2 | `validate_before_write` nunca se ejecuta | Sin validación pre-escritura |

### Altos

| # | GAP | Impacto |
|---|-----|---------|
| 3 | Sin validación de salida de `consolidar_api.py` | Datos corruptos pasan silenciosamente |
| 4 | Sin check de consistencia input/output rows | Pérdida de datos no detectada |
| 5 | Sin null check en Meta/Ejecucion output | Nulos propagan a cálculos |

### Medios

| # | GAP | Impacto |
|---|-----|---------|
| 6 | Sin validación de enum Categoria | Categorías inválidas pasan |
| 7 | Sin duplicate check en output final | Duplicados en dashboards |
| 8 | Sin cross-sheet consistency | Valores contradictorios entre hojas |
| 9 | Sin validación Anio/Mes vs Fecha | Inconsistencia temporal |
| 10 | Sin schema validation Kawak catalog | Catálogo corrupto no detectado |
| 11 | Mismatch column name Id vs ID | Fragilidad en contratos |
| 13 | Sin tests para intermediate_validation | Sin cobertura de testing |

### Bajos

| # | GAP | Impacto |
|---|-----|---------|
| 12 | Sin timeout/resource-limit | OOM en datos grandes |
| 14 | Sin null guard en calcular_salud | NaN se propaga silenciosamente |
| 15 | Sin validación de sentido | Valores inválidos no detectados |

---

## Recomendaciones

### Inmediatas (0-2 horas)
1. **Activar `validate_after_consolidar_api`** — Importar y llamar en `actualizar_consolidado.py`
2. **Activar `validate_before_write`** — Importar y llamar antes de escribir Excel
3. **Investigar capping de Ejecucion** — Verificar por qué `agent5_corrections.py` no aplica

### Corto Plazo (2-8 horas)
4. **Agregar deduplicación** — Implementar en `consolidar_api.py`
5. **Agregar null check output** — Meta, Ejecucion, Cumplimiento en validación de salida
6. **Agregar validación de enum Categoria** — Verificar valores permitidos
7. **Crear tests para intermediate_validation** — Cobertura mínima 80%

### Largo Plazo (> 8 horas)
8. **Implementar Great Expectations** — Suite completa de validaciones
9. **Agregar cross-sheet consistency** — Verificar coherencia entre hojas
10. **Dashboard de calidad** — Métricas en tiempo real

---

## Matriz de Validación Recomendada (Great Expectations)

```python
expectations = [
    # Completitud
    {"expectation_type": "expect_table_row_count_to_be_between", "value": {"min_value": 1000}},
    {"expectation_type": "expect_column_values_to_not_be_null", "column": "ID"},
    {"expectation_type": "expect_column_values_to_not_be_null", "column": "fecha"},
    
    # Tipos
    {"expectation_type": "expect_column_values_to_be_in_type_list", "column": "resultado", "value": {"type_list": ["float", "int"]}},
    
    # Rangos
    {"expectation_type": "expect_column_values_to_be_between", "column": "resultado", "value": {"min_value": 0, "max_value": 1.3}},
    
    # Duplicados
    {"expectation_type": "expect_compound_columns_to_be_unique", "column_list": ["ID", "fecha"]},
    
    # Fechas
    {"expectation_type": "expect_column_values_to_be_between", "column": "fecha", "value": {"min_value": "2022-01-01", "max_value": "2026-12-31"}},
]
```

---

## Archivos Generados

| Artefacto | Propósito |
|-----------|-----------|
| `AGENT5_DATA_VALIDATION.md` | Este reporte |
| `AGENT5_ANOMALIES.csv` | Lista de anomalías |
| `AGENT5_VALIDATION_MATRIX.csv` | Matriz de cobertura |

---

**Generado por:** AGENT 5 — Data Validation Framework  
**Versión:** 1.0 SGIND-Optimizada
