# AGENT 5 Implementation Guide
**Software Intelligence Framework — Sistema de Indicadores Poli**  
**Especialista en Validación de Datos**  
**Versión:** 1.0 SGIND  
**Fecha:** 9 de mayo de 2026

---

## 🎯 Qué es AGENT 5

**AGENT 5** es el especialista en **calidad de datos**, responsable de:

1. ✅ **Auditar** todas las validaciones existentes en el ETL
2. ✅ **Detectar** anomalías e inconsistencias en datos
3. ✅ **Proponer** reglas de validación automática con Great Expectations
4. ✅ **Generar** reportes de hallazgos priorizados

---

## 📦 Artefactos Generados

### 1. `.agent5.instructions.md`
**Propósito:** Prompt especializado optimizado  
**Ubicación:** `./.agent5.instructions.md`  
**Contenido:**
- Rol y responsabilidades del AGENT 5
- Matriz de validación (7 dimensiones)
- Pasos de ejecución
- Hallazgos esperados

### 2. `scripts/agent5_data_validation.py`
**Propósito:** Framework ejecutable de análisis de datos  
**Ejecución:**
```bash
python scripts/agent5_data_validation.py
```
**Genera:**
- Reporte Markdown de hallazgos
- Suite de Great Expectations (JSON)
- Inventario de validaciones (CSV)

### 3. `artifacts/AGENT5_DATA_VALIDATION_*.md`
**Ejemplo:** `AGENT5_DATA_VALIDATION_20260509_230450.md`  
**Contiene:**
- Resumen ejecutivo de hallazgos
- Hallazgos clasificados por severidad
- Instrucciones de corrección
- Próximos pasos

### 4. `artifacts/GREAT_EXPECTATIONS_SUITE_*.json`
**Contiene:** Reglas de validación automática
```json
{
  "criticales": [
    {
      "expectation_type": "expect_column_values_to_not_be_null",
      "column": "id_indicador"
    },
    ...
  ],
  "tecnicas": [...]
}
```

### 5. `artifacts/VALIDACIONES_INVENTARIO_*.csv`
**Contiene:** Auditoría de validaciones existentes
```
archivo,modulo,patron,tipo_validacion,instancias
scripts/actualizar_consolidado.py,ETL Principal,if not,Business Rule,4
core/calculos.py,Cálculo de Indicadores,if not,Business Rule,1
```

---

## 🔍 Análisis Realizado (9 mayo 2026)

### Validaciones Inventariadas: 6

| Módulo | Patrón | Tipo | Instancias |
|--------|--------|------|-----------|
| ETL Principal | if not | Business Rule | 4 |
| ETL Principal | raise | Error Handling | 1 |
| Cálculo Indicadores | if not | Business Rule | 1 |
| Configuración | if not | Business Rule | 2 |
| Configuración | raise | Error Handling | 4 |
| Generación Reportes | if not | Business Rule | 25 |

### Hallazgos Detectados: 2

#### ✗ CRÍTICO: Ejecución fuera de rango
- **Descripción:** 1 valor de ejecución fuera del rango permitido [0, 1.3]
- **Impacto:** Dashboards muestran porcentajes inválidos
- **Solución:** Validar fuentes de datos, aplicar capping en ETL

#### ⚠ ALTO: Meta fuera de rango
- **Descripción:** 1 valor de meta con valor 0 (fuera de rango esperado)
- **Impacto:** Metas inválidas generan categorización incorrecta
- **Solución:** Revisar indicadores con meta 0 o > 100%

---

## 🚀 Cómo Usar AGENT 5

### Opción 1: Análisis Manual (Recomendado para casos específicos)

```bash
# 1. Leer instrucciones especializadas
cat .agent5.instructions.md

# 2. Ejecutar análisis
python scripts/agent5_data_validation.py

# 3. Revisar reporte generado
# Archivo: artifacts/AGENT5_DATA_VALIDATION_*.md
```

### Opción 2: Integrar en Pipeline Existente

```python
# scripts/actualizar_consolidado.py
from agent5_data_validation import DataValidationAgent

# Al final del ETL:
validator = DataValidationAgent()
validator.run_analysis()
```

### Opción 3: Usar Great Expectations Directamente

```python
# Cargar suite de validaciones
import json
from great_expectations.core.batch import RuntimeBatchRequest

with open('artifacts/GREAT_EXPECTATIONS_SUITE_*.json') as f:
    expectations = json.load(f)

# Aplicar validaciones a dataframe
for expectation in expectations['criticales']:
    df.expect_column_values_to_not_be_null(
        column=expectation['column']
    )
```

---

## 📋 7 Dimensiones de Validación

### 1. **COMPLETITUD**
```
¿Faltan datos en campos críticos?
- Mínimo 500 registros por consolidación
- Max 5% nulos en columnas esenciales
```

### 2. **DUPLICADOS**
```
¿Hay registros repetidos?
- Sin duplicados en [Proceso, Indicador, Período]
- Si hay, documentar motivo
```

### 3. **RANGOS**
```
¿Valores dentro de límites?
- Ejecución: [0, 1.3]
- Meta: (0, 1.0]
```

### 4. **TIPOS DE DATO**
```
¿Tipos correctos?
- id_indicador: integer
- ejecucion: float
- período: datetime
```

### 5. **NULOS PERMITIDOS**
```
¿Campos obligatorios presente?
- id_indicador: NOT NULL
- id_proceso: NOT NULL
```

### 6. **CONSISTENCIA HISTÓRICA**
```
¿Valores cambian entre versiones?
- Sin cambios retroactivos sin auditoría
```

### 7. **CONSISTENCIA ENTRE FUENTES**
```
¿API y Excel coinciden?
- Reconciliación ≤ 2% diferencia
```

---

## 🎓 Interpretación de Hallazgos

### Severidad

| Nivel | Acción | Plazo |
|-------|--------|-------|
| 🔴 **CRÍTICO** | Bloquea ETL, requiere corrección inmediata | Hoy |
| 🟠 **ALTO** | Afecta reportes, debe resolverse pronto | Esta semana |
| 🟡 **MEDIO** | Mejora técnica deseable | Este mes |
| 🟢 **BAJO** | Optimización opcional | Roadmap |

### Categoría

- **Completitud:** Faltan datos
- **Duplicados:** Registros repetidos
- **Rangos:** Valores inválidos
- **Tipos:** Tipo de dato incorrecto
- **Nulos:** Campos obligatorios vacíos
- **Consistencia:** Datos cambian incorrectamente

---

## ✅ Próximos Pasos

### Corto Plazo (Esta semana)
1. [ ] Revisar hallazgos CRÍTICOS
2. [ ] Implementar correcciones
3. [ ] Ejecutar validación nuevamente
4. [ ] Validar cambios en tests

### Mediano Plazo (Este mes)
1. [ ] Integrar Great Expectations en ETL
2. [ ] Configurar alertas de validación
3. [ ] Automatizar correcciones
4. [ ] Capacitar equipo en reglas

### Largo Plazo (Próximos meses)
1. [ ] Expandir cobertura a 100%
2. [ ] Dashboard de calidad de datos
3. [ ] SLA de integridad
4. [ ] Auditoría continua

---

## 🔗 Integración con Otros AGENTs

```
AGENT 1 (Data Source Audit)
    ↓
AGENT 5 (Data Validation) ← Valida fuentes
    ↓
AGENT 2 (ETL Pipeline) ← Propone mejoras
    ↓
AGENT 3 (Indicator Integrity) ← Verifica indicadores
    ↓
AGENT 8 (Roadmap) ← Plan de implementación
```

---

## 📞 Contacto y Soporte

**Preguntas sobre validación de datos?**

1. Revisar `.agent5.instructions.md` (prompt especializado)
2. Ejecutar `python scripts/agent5_data_validation.py`
3. Revisar artefactos generados en `artifacts/`
4. Consultar documentación en `docs/core/`

---

## 📚 Referencias

| Documento | Propósito |
|-----------|-----------|
| `.agent5.instructions.md` | Prompt especializado |
| `scripts/agent5_data_validation.py` | Framework ejecutable |
| `artifacts/AGENT5_*.md` | Reportes de análisis |
| `artifacts/GREAT_EXPECTATIONS_*.json` | Reglas de validación |
| `core/config.py` | Umbrales y configuración |

---

**Status:** ✅ IMPLEMENTADO  
**Versión:** 1.0 SGIND  
**Framework:** Software Intelligence v1.0
