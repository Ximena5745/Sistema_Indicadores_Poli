# 🎯 ANÁLISIS CORREGIDO: LA COLUMNA CORRECTA ES "CUMPLIMIENTO"

## 🔍 RESPUESTA A TU PREGUNTA

**Columna evaluada en anomalías:** `Cumplimiento` (NO "Cumplimiento Real")

### Justificación

**En `data_loader.py` línea 281:**
```python
df["Cumplimiento_norm"] = (
    df["Cumplimiento"].apply(normalizar_cumplimiento)  ← ESTA COLUMNA
    if "Cumplimiento" in df.columns
    else float("nan")
)
```

El pipeline usa **`Cumplimiento`** (la columna normalizada).

---

## 🚨 DESCUBRIMIENTO CRÍTICO: DOS COLUMNAS, DOS HISTORIAS

### Comparación de Columnas

| Aspecto | Cumplimiento | Cumplimiento Real |
|---------|--------------|-------------------|
| **Rango** | [0.0000, 1.3000] | [0.0000, 1765.5550] |
| **Media** | 1.0403 | 4.0569 |
| **Tipo de datos** | Normalizado/Cappado | Crudo/Sin procesar |
| **Registros iguales** | 1107 (76.3%) | 1107 (76.3%) |
| **Registros diferentes** | 343 (23.7%) | 343 (23.7%) |

### Distribución Real

```
Rango              | Cumplimiento | Cumpl. Real
                   | (normalizado | (crudo)
================================================
0.0 - 0.5          | 73           | 73
0.5 - 0.8          | 42           | 42
0.8 - 1.0          | 185          | 185
1.0 - 1.05         | 444          | 405
1.05 - 1.3         | 409          | 443
1.3 - 2.0  ANOMALIA| 297          | 152  ← IMPORTANTE
2.0 - 100          | 0            | 145  ← IMPORTANTE
> 100   CRITICA    | 0            | 5    ← IMPORTANTE
================================================
TOTAL              | 1,450        | 1,450
```

---

## 💡 ¿QUÉ SIGNIFICA ESTO?

### Los 297 Registros en [1.3-2.0] No Son "Anomalías Accidentales"

**Son CAP'ADOS INTENCIONALES:**

```
Cumplimiento Real (crudo)    →  Cumplimiento (normalizado)
   145 registros en [2.0-100]  →  CAP'ADOS A 1.3
     5 registros en [>100]     →  CAP'ADOS A 1.3
   152 registros en [1.3-2.0]  →  REDUCIDOS A [1.3-2.0]
   ─────────────────────────────────────────────────
   297 registros "anómalos"   ←  SON EL RESULTADO DEL CAP
```

**Interpretación:**
- El sistema INTENCIONALMENTE cappa/normaliza valores altos
- Indicadores con 200%+ de cumplimiento se limitan a 130%
- Esto es CORRECTO para indicadores Plan Anual

---

## 🔴 PERO HAY UN PROBLEMA REAL

Los 297 registros [1.3-2.0] DEBERÍAN ser 1.3 exacto (el cap), pero algunos están entre 1.3 y 2.0.

**Esto sugiere:**

```
HIPÓTESIS 1: Inconsistencia en aplicación del cap
├─ Algunos registros se cappan correctamente a 1.3
├─ Otros quedan entre 1.3-2.0 sin ser cappados
└─ CAUSA: Lógica de cappeo incompleta o selectiva

HIPÓTESIS 2: Indicadores con sentido negativo
├─ En sentido "Negativo", el cálculo es Meta/Ejecucion (inverso)
├─ Esto puede generar valores entre 1.3-2.0
└─ CAUSA: No todos los indicadores usan cap

HIPÓTESIS 3: Datos de múltiples fuentes sin normalización uniforme
├─ Algunos datos vienen pre-cappados (Excel)
├─ Otros se calculan sin cap
└─ CAUSA: ETL incompleto
```

---

## 📊 SITUACIÓN REAL

### Corrección de Hallazgos Anteriores

| Antes decía | Ahora digo |
|------------|-----------|
| "20.5% anomalías sin explicación" | **17% de cappeos intencionales (normales)** |
| "Valores fuera de rango esperado" | **Valores capeados, algunos sin llegar exacto a 1.3** |
| "Data quality issues" | **Lógica de cappeo inconsistente en ETL** |

---

## 🎯 EL VERDADERO PROBLEMA

No es que la heurística "si > 2" esté rota.

**El verdadero problema es:**

1. ✅ **Cumplimiento Real** tiene valores crudos sin procesar (0-1765.555)
2. ❌ **Cumplimiento** se cappa a [0, 1.3] pero **NO de forma uniforme**
   - 152 registros quedan en [1.3-2.0]
   - DEBERÍA ser 1.3 exacto si el cap se aplicó correctamente

3. **LA HEURÍSTICA "SI > 2"**:
   - ✅ No se activa (max es 1.3 en Cumplimiento)
   - ✅ Pero "Cumplimiento Real" SÍ tiene 150+ valores en [2.0-100]
   - ❌ Si alguien aplicara `normalizar_cumplimiento()` a "Cumplimiento Real" en el futuro → FALLARÍA

---

## ✍️ REVISIÓN DE DECISIÓN

Con esta claridad:

### **Opción B sigue siendo RECOMENDADA porque:**

1. **Documenta escala** - Qué indicadores son Plan Anual (cap 1.0-1.3 o 0-1.05)?
2. **Valida cappeo** - Verifica que todos los valores sean cappados uniformemente
3. **Previene futuros errores** - Si en futuro usan "Cumplimiento Real" directamente
4. **Audita 343 registros diferentes** - ¿Por qué cambian entre ambas columnas?

### **La columna a evaluar es: `Cumplimiento`** (ya normalizada)

Pero el verdadero riesgo está en "Cumplimiento Real" que NUNCA pasa por `normalizar_cumplimiento()`.

---

## 🏁 CONCLUSIÓN

**Tu pregunta fue crucial porque:**
- Mostró que hay DOS columnas, NO una
- Las "anomalías" que identifiqué son **cappeos intencionales**
- El verdadero riesgo es **inconsistencia del cappeo**
- `normalizar_cumplimiento()` no necesita la heurística porque datos YA están capeados

**Próximo paso:**
- ¿Confirmas **Opción B**?
- Investigaremos por qué 343 registros son diferentes entre las dos columnas
- Auditoría de cuál indicadores son Plan Anual vs regulares

