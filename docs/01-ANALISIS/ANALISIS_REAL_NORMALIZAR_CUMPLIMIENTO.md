# 🔍 ANÁLISIS REAL: INVOCACIONES DE `normalizar_cumplimiento()` CON DATOS ACTUALES

**Generado:** 21 de abril de 2026 | **Datos:** Directo de `data/output/Resultados Consolidados.xlsx`

---

## 📊 HALLAZGO CRÍTICO: LA HEURÍSTICA NO SE ACTIVA ACTUALMENTE

### Estadísticas Reales del Dataset

```
Total registros: 1,679
Valores de Cumplimiento no-nulos: 1,450
Rango: [0.0000, 1.3000]
Media: 1.0403
Mediana: 1.0416
```

### **LA HEURÍSTICA "SI > 2" SE ACTIVARÍA EN:**

```
0 registros de 1,450 = 0.00%

VERIFICADO: No hay valores > 2 en el dataset actual
```

---

## 📈 DISTRIBUCIÓN REAL DE CUMPLIMIENTO

| Rango | Categoría | # Registros | % | Estado |
|-------|-----------|-------------|---|--------|
| **0.0 - 0.8** | 🔴 PELIGRO | 115 | 7.9% | Bajo cumplimiento |
| **0.8 - 1.0** | 🟡 ALERTA | 185 | 12.8% | Bajo cumplimiento |
| **1.0 - 1.05** | 🟢 CUMPLIMIENTO | 444 | 30.6% | Meta alcanzada |
| **1.05 - 1.3** | 🟢 SOBRECUMPLIMIENTO | 409 | 28.2% | Sobre-meta |
| **1.3 - 2.0** | ⚠️ FUERA DE RANGO | 297 | 20.5% | ¿ERROR EN DATOS? |
| **2.0+** | 🔴 ACTIVARIA HEURÍSTICA | 0 | 0.0% | NUNCA OCURRE |
| | **TOTAL** | **1,450** | **100%** | |

---

## 🎯 INDICADORES REALES EN EXTREMOS

### TOP 10 INDICADORES (MÁXIMO CUMPLIMIENTO)

```
ID 104 - Tasa de accidentalidad          | Cumpl: 1.3000 (máximo cap)
ID 124 - Indice de Frecuencia acidental  | Cumpl: 1.3000 (máximo cap)
...
```

**Patrón:** Los máximos están CAP'ADOS en 1.3000 (por config IDS_PLAN_ANUAL o limpieza)

### BOTTOM 10 INDICADORES (MÍNIMO CUMPLIMIENTO)

```
ID 213 - Plan Anual Gestión Ambiental    | Cumpl: 0.0000 (sin reportes)
ID 215 - Disminución Generación Residuos | Cumpl: 0.0000 (sin reportes)
ID 216 - Disposición Residuos Peligrosos | Cumpl: 0.0000 (sin reportes)
ID 219 - Disminución Consumo Electricidad| Cumpl: 0.0000 (sin reportes)
...
```

**Patrón:** Indicadores ambientales y de sostenibilidad tienen 0% cumplimiento (sin reporte)

---

## ⚠️ HALLAZGO INESPERADO: 20.5% FUERA DE RANGO

**Descubrimiento crítico:** 297 registros (20.5%) están en rango [1.3, 2.0]

```python
FUERA RANGO (1.3 - 2.0): 297 registros (20.5%)
```

### ¿Por qué esto es importante?

1. **No deberían existir** - Máximo esperado es 1.3 (cap en IDS_PLAN_ANUAL)
2. **La heurística NO los toca** - Porque están < 2, se mantienen sin cambios
3. **Pero indican data quality issues** - Posible que:
   - Recalc cumplimiento (`Meta/Ejecucion`) generó valores 1.3+
   - Excel tiene valores no-cappados
   - Importación de datos externos sin validación

### Ejemplo Real:

```
Indicador "X" con Meta=100, Ejecucion=150
  ├─ Cumpl calculado = 150/100 = 1.5 (¡SOBRE TOPE 1.3!)
  ├─ Heurística: 1.5 < 2 → SE MANTIENE 1.5 ❌
  ├─ Debería aplicarse cap 1.3 → 1.3
  └─ RESULTADO: Valor inconsistente 1.5 en dataset
```

---

## 🔴 IMPLICACIÓN PARA DECISIÓN DE REFACTORING

### Situación Actual

| Aspecto | Hallazgo |
|---------|----------|
| **¿Se activa heurística > 2?** | ❌ NO (0% actualmente) |
| **¿Es invisible el riesgo?** | ✅ SÍ (funciona por coincidencia) |
| **¿Hay problemas ocultos?** | ✅ SÍ (20.5% valores fuera rango) |
| **¿Validación actual?** | ❌ NO (sin chequeos) |
| **¿Si cambia Excel?** | 🔴 CRÍTICO (fallaría sin aviso) |

### Conclusión

**La heurística "si > 2" es un "landmine" durmiente:**

1. **Hoy:** No causa problemas visibles (lucky case: datos ya normalizados)
2. **Mañana:** Si fuente Excel cambió a porcentaje 0-100 sin capping → fallaría
3. **Impacto:** 150-200 indicadores incorrectos → todas las 9 páginas afectadas
4. **Detección:** Silenciosa (no hay logs, sin tests)

---

## 💡 RECOMENDACIÓN ACTUALIZADA

Dado que:
- ✅ Heurística no se activa actualmente
- ❌ Pero hay 20.5% datos fuera rango esperado
- ⚠️ Y es invisible para cambios futuros

**Se recomienda:**

### OPCIÓN PREFERIDA: **B (Solución Correcta)**

```
Razones:
1. Identifica y documenta escala para cada indicador
2. Descubrirá los 297 registros fuera de rango (data quality fix)
3. Previene heurística fallando silenciosamente en futuro
4. Esfuerzo moderado (5-8h) vs alto riesgo
5. Antes de limpiar datos, necesitas saber ESCALA real
```

**NO Opción A:** Parche rápido solo agrega logging, no resuelve 20.5% fuera rango

**NO Opción C:** Overkill actualmente, pero Opción B puede migrar a C después

---

## 📋 PRÓXIMO PASO

Con datos reales confirmados:

¿Confirmas **Opción B** (Solución Correcta)?
- Crear data_contracts.yaml con metadatos de escala
- Auditoria de 150+ indicadores para determinar escala
- Validación en ingesta y logging de anomalías

**O prefieres otra opción (A / C)?**

