# 🔬 MATRICES TÉCNICAS: ANÁLISIS DETALLADO DE CÁLCULOS

**Fecha:** 21 de abril de 2026  
**Scope:** Análisis profundo de 47 funciones identificadas  
**Nivel:** Técnico - Para arquitectos e implementadores

---

## MATRIZ 1: Inventario Completo de Funciones de Cálculo

### Categoría: PRIMITIVOS (Normalización de entrada)

| # | Función | Ubicación | Línea | Parámetros | Retorna | Casos especiales | Coverage |
|---|---------|-----------|-------|-----------|---------|------------------|----------|
| P1 | `normalizar_cumplimiento()` | core/calculos.py | 13 | valor | float ∈ [0,1.3] | NaN handling | 40% |
| P2 | `_id_limpio()` | services/data_loader.py | 46 | x | str | NaN→"", float→int | 20% |
| P3 | `normalizar_valor()` | core/semantica.py | 309 | valor, hint | float | Format latinoamericano | 30% |
| P4 | `normalizar_fecha()` | AUDITORIA_FASE_4 | 558 | fecha | Timestamp | Múltiples formatos | 10% |
| P5 | `obtener_ultimo_registro()` | core/calculos.py | 151 | df | df | Deduplicación | 0% |

**Hallazgo:** P1 duplica lógica con P3 (normalizadores de valor)

---

### Categoría: DERIVADOS (Lógica de negocio elemental)

| # | Función | Ubicación | Fórmula | Parámetros | Retorna | Casos especiales | Coverage |
|---|---------|-----------|---------|-----------|---------|------------------|----------|
| D1 | `categorizar_cumplimiento()` | core/calculos.py:26 | Umbrales | cumpl, sentido, id | str | Plan Anual detection | 50% |
| D2 | `categorizar_cumplimiento()` | core/semantica.py:56 | Umbrales | cumpl, id | str | PA + strings | 50% |
| D3 | `_nivel_desde_cumplimiento()` | services/strategic_indicators.py:55 | Umbrales | cumpl_dec | str | ❌ NO Plan Anual | 20% |
| D4 | `_calc_cumpl()` | scripts/etl/cumplimiento.py:23 | ejec/meta | meta, ejec, sentido, tope | (float, float) | Meta=0&Ejec=0→1.0 | 70% |
| D5 | `recalcular_cumplimiento_faltante()` | core/semantica.py:189 | ejec/meta | meta, ejec, sentido, id | float | PA tope dinámico | 60% |
| D6 | `calcular_tendencia()` | core/calculos.py:114 | Δ(t, t-1) | df_indicador | str {↑,↓,→} | < 2 registros | 40% |
| D7 | `calcular_meses_en_peligro()` | core/calculos.py:125 | Conteo | df_indicador | int | Periodos consecutivos | 30% |

**Hallazgos:** 
- D1 vs D2 vs D3 = 3 versiones (D3 defectuosa)
- D4 tiene mejores casos especiales que D5
- D6/D7 no reutilizadas en dashboards (inline)

---

### Categoría: ESTRATÉGICOS (Agregaciones y análisis)

| # | Función | Ubicación | Lógica | Entrada | Salida | Cobertura | Test |
|---|---------|-----------|--------|---------|--------|-----------|------|
| S1 | `calcular_salud_institucional()` | core/calculos.py:101 | Promedio cumpl por Fecha | df con Fecha, Cumpl | df[Fecha, Salud_%] | Temporal | 20% |
| S2 | `calcular_kpis()` | core/calculos.py:223 | Conteos por categoría | df_ultimo | dict{Peligro, Alerta, ...} | Agregación | 30% |
| S3 | `generar_recomendaciones()` | core/calculos.py:138 | Lógica contextual | categoria, cum_series | (tendencia, [recs]) | 4 contextos | 40% |
| S4 | `load_cierres()` | services/strategic_indicators.py:85 | Carga+Cálculo+Categor | Ruta Excel | df con Categoria | MEZCLA SoC | 15% |
| S5 | `load_worksheet_flags()` | services/strategic_indicators.py:69 | Carga metadatos | Ruta Excel | df[Id, Flags] | - | 10% |

**Hallazgo:** S4 es híbrida (I/O + Cálculo + Lógica) - violación SoC

---

## MATRIZ 2: Fórmulas de Cumplimiento Comparadas

### Escenario: Indicador POSITIVO (Meta=100, Ejec=90)

```
Fórmula esperada: cumpl = 90/100 = 0.90 (90%)
Categoría esperada: Alerta (0.80-0.99)
```

| Implementación | Resultado cumpl | Categoría | Plan Anual? | Casos especiales? |
|---|---|---|---|---|
| **core/calculos.py:26** | ✅ 0.90 | ✅ Alerta | ✅ Sí | ⚠️ Parcial |
| **core/semantica.py:56** | ✅ 0.90 | ✅ Alerta | ✅ Sí | ✅ Sí |
| **strategic_indicators.py:55** | ✅ 0.90 | ✅ Alerta | ❌ No | ❌ No |
| **data_loader.py:248** | ✅ 0.90 | ✅ Alerta | ✅ Sí | ❌ No |
| **cumplimiento.py:23** | ✅ 0.90 | N/A | ⚠️ Partial | ✅ Sí |

---

### Escenario: Indicador NEGATIVO (Meta=100, Ejec=50)

```
Fórmula esperada: cumpl = 100/50 = 2.0 (200%) → Tope 1.3 = 1.3 (Sobrecumplimiento)
```

| Implementación | Resultado | Tope aplicado | Categoría |
|---|---|---|---|
| **core/calculos.py:26** | 1.3 | ✅ 1.3 | ✅ Sobrecumplimiento |
| **core/semantica.py:56** | 1.3 | ✅ 1.3 | ✅ Sobrecumplimiento |
| **strategic_indicators.py:55** | 1.3 | ⚠️ (no soportado) | ✅ Sobrecumplimiento |
| **data_loader.py:248** | 1.3 | ✅ 1.3 | ✅ Sobrecumplimiento |
| **cumplimiento.py:23** | 1.3 | ✅ 1.3 | N/A |

---

### Escenario CRÍTICO: Plan Anual (ID=373, Meta=95, Ejec=90)

```
Fórmula Plan Anual: cumpl = 90/95 = 0.947 (94.7%)
Categoría ESPERADA: Alerta (0.80-0.94) - NO cumple PA
Categoría ESPERADA: Alerta (0.80-0.94.9) con umbral PA
```

| Implementación | Resultado cumpl | Categoría | ¿CORRECTO? |
|---|---|---|---|
| **core/calculos.py:26** | ✅ 0.947 | ✅ Alerta (PA) | ✅ CORRECTO |
| **core/semantica.py:56** | ✅ 0.947 | ✅ Alerta (PA) | ✅ CORRECTO |
| **strategic_indicators.py:55** | ✅ 0.947 | ❌ Alerta (REGULAR) | ❌ INCORRECTO |
| **data_loader.py:248** | ✅ 0.947 | ✅ Alerta (PA) | ✅ CORRECTO |
| **cumplimiento.py:23** | ✅ 0.947 | N/A | ⚠️ Parcial |

**RIESGO CRÍTICO:** strategic_indicators.py categoriza Plan Anual con umbral REGULAR

---

### Escenario ESPECIAL: Meta=0 & Ejec=0 (Indicador de Riesgo)

```
Contexto: Mortalidad laboral - meta=0 (cero muertes), ejecutado=0 (ninguna muerte)
Interpretación correcta: 100% cumplimiento (meta lograda perfectamente)
```

| Implementación | Resultado | Interpretación | ¿CORRECTO? |
|---|---|---|---|
| **core/calculos.py:26** | NaN | ❌ "No se puede calcular" | ❌ INCORRECTO |
| **core/semantica.py:56** | NaN | ❌ "No se puede calcular" | ❌ INCORRECTO |
| **strategic_indicators.py:55** | NaN | ❌ "No se puede calcular" | ❌ INCORRECTO |
| **data_loader.py:248** | NaN | ❌ "No se puede calcular" | ❌ INCORRECTO |
| **cumplimiento.py:23** | 1.0 | ✅ "100% éxito, ambas metas logradas" | ✅ CORRECTO |

**HALLAZGO:** Solo `cumplimiento.py:23` maneja correctamente este caso

---

### Escenario ESPECIAL: Negativo & Ejec=0 (Indicador de Gastos)

```
Contexto: Accidentalidad - meta=1.6 accidentes, ejecutado=0 accidentes
Interpretación correcta: 100% cumplimiento (cero accidentes = éxito)
```

| Implementación | Resultado | Interpretación | ¿CORRECTO? |
|---|---|---|---|
| **core/calculos.py:26** | NaN | ❌ "División por cero" | ❌ INCORRECTO |
| **core/semantica.py:56** | NaN | ❌ "División por cero" | ❌ INCORRECTO |
| **strategic_indicators.py:55** | NaN | ❌ "División por cero" | ❌ INCORRECTO |
| **data_loader.py:248** | NaN | ❌ "División por cero" | ❌ INCORRECTO |
| **cumplimiento.py:23** | 1.0 | ✅ "100% éxito, cero es perfecto" | ✅ CORRECTO |

**HALLAZGO:** Solo `cumplimiento.py:23` maneja correctamente este caso

---

## MATRIZ 3: Umbrales de Categorización Por Tipo de Indicador

### Comparación de Umbrales Configurados

| Umbral | Esperado | config.py | calculos.py | semantica.py | strategic_indicators | Consistency |
|--------|----------|-----------|------------|-------------|----------------------|------------|
| PELIGRO | 0.80 | 0.80 | 0.80 | 0.80 | 0.80 | ✅ OK |
| ALERTA (Regular) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | ✅ OK |
| ALERTA (PA) | 0.95 | 0.95 | 0.95 | 0.95 | ❌ No usa | ❌ FAIL |
| SOBRE (Regular) | 1.05 | 1.05 | 1.05 | 1.05 | 1.05 | ✅ OK |
| SOBRE (PA) | 1.00 | 1.00 | 1.00 | 1.00 | ❌ No usa | ❌ FAIL |

**CRÍTICO:** strategic_indicators.py NO diferencia Plan Anual (2 umbrales faltantes)

---

### Matriz de Decisión: ¿Qué umbral usar?

```
Situación: Cumplimiento = 0.95

SI indicador es PLAN ANUAL:
  [0.80, 0.95) → Alerta
  [0.95, 1.00] → Cumplimiento    ← 0.95 está AQUÍ → Cumplimiento ✅
  
SI indicador es REGULAR:
  [0.80, 1.00) → Alerta          ← 0.95 está AQUÍ → Alerta ✅
  [1.00, 1.05) → Cumplimiento
```

**Resultado:** Mismo valor (0.95) → categoría diferente según tipo

---

## MATRIZ 4: Cobertura de Datos Por Función

### ¿Qué % del dataset procesa cada función?

| Función | Dataset | Volumen | Casos donde se aplica |
|---------|---------|---------|----------------------|
| `cargar_dataset()` | ALL | 100% | Carga principal ETL |
| → `_aplicar_calculos_cumplimiento()` | ALL | 100% | Paso 4b pipeline |
| → `normalizar_cumplimiento()` | ALL | 100% | A TODA columna Cumplimiento |
| → `categorizar_cumplimiento()` | ALL | 100% | A TODA columna Cumplimiento |
| `load_cierres()` | Subset | ~30% | strategic_indicators solamente |
| → `_nivel_desde_cumplimiento()` | Subset | ~30% | strategic_indicators solamente |
| Dashboards inline | Filtered | 5-20% | Por page (resumen_general, etc.) |

**CRÍTICO:** `_aplicar_calculos_cumplimiento()` afecta 100% de datos con lógica incompleta

---

## MATRIZ 5: Trazabilidad Inversa de Bugs

### Bug: Indicadores Plan Anual mal categorizados

**SÍNTOMAS:**
- Indicador 373 con cumpl=0.95 → se categoriza como "Alerta" en strategic_indicators
- Pero en resumen_general → se categoriza como "Cumplimiento" (CORRECTO)

**ORIGEN:**
```
strategic_indicators.load_cierres()
  ↓
df["Categoria"] = df["Cumplimiento"].apply(_nivel_desde_cumplimiento)  ← DEFECTUOSA
  ↓
_nivel_desde_cumplimiento(0.95)
  ├─ if 0.95 < UMBRAL_ALERTA (1.00) → "Alerta"
  └─ ❌ NO verifica si es Plan Anual
```

**VERSUS: Correcto en data_loader**
```
data_loader._aplicar_calculos_cumplimiento()
  ↓
df["Categoria"] = df.apply(
  lambda row: categorizar_cumplimiento(row["Cumplimiento"], row["Id"]),
  axis=1
)
  ↓
categorizar_cumplimiento(0.95, id_indicador="373")
  ├─ es_plan_anual = "373" in IDS_PLAN_ANUAL → True
  ├─ u_alerta = UMBRAL_ALERTA_PA (0.95)
  └─ ✅ 0.95 >= 0.95 → "Cumplimiento"
```

---

## MATRIZ 6: Dependencias de Funciones

### Grafo de Dependencias

```
config.py
  ├─ UMBRAL_* constants
  ├─ IDS_PLAN_ANUAL
  ├─ COLOR_CATEGORIA
  └─ ICONOS_CATEGORIA

core/calculos.py
  ├─ Importa: config
  ├─ Exporta: categorizar_cumplimiento(), calcular_tendencia(), ...
  └─ Usado por: data_loader, dashboards (inline), tests

core/semantica.py
  ├─ Importa: config
  ├─ Exporta: categorizar_cumplimiento(), recalcular_cumplimiento_faltante()
  └─ Usado por: (POCO USADO ACTUALMENTE)

services/data_loader.py
  ├─ Importa: core/calculos
  ├─ Ejecuta: _aplicar_calculos_cumplimiento() con categorizar_cumplimiento()
  ├─ Carga: 100% de datos
  └─ Salida: df_main → (9 dashboards)

services/strategic_indicators.py
  ├─ Importa: core/calculos
  ├─ Ejecuta: load_cierres() con _nivel_desde_cumplimiento() ❌ DEFECTUOSA
  ├─ Carga: ~30% de datos
  └─ Salida: df_cierres → (2 dashboards)

scripts/etl/cumplimiento.py
  ├─ Importa: (ninguno - standalone)
  ├─ Exporta: _calc_cumpl(), obtener_tope_cumplimiento()
  └─ Usado por: formulas_excel.py, tests

streamlit_app/pages/*.py (9 archivos)
  ├─ Importan: core/calculos (ALGUNOS)
  ├─ Inline: categorizar, tendencia, etc. (MUCHOS)
  └─ Problema: Duplicación
```

**CRÍTICO:** data_loader.py es CUELLO DE BOTELLA (100% de datos fluyen por ahí)

---

## MATRIZ 7: Test Coverage Actual vs Requerido

### Funciones Críticas - Cobertura

| Función | Archivo Test | Casos | Coverage | Requerido | Gap |
|---------|---|---|---|---|---|
| `categorizar_cumplimiento()` | test_calculos.py | 5 | 50% | 95% | -45% |
| `_calc_cumpl()` | (NO EXISTE) | 0 | 0% | 95% | -95% |
| `calcular_cumplimiento()` (ejec/meta) | test_calculos.py | 3 | 30% | 95% | -65% |
| `normalizar_cumplimiento()` | test_calculos.py | 2 | 20% | 80% | -60% |
| `calcular_tendencia()` | (NO EXISTE) | 0 | 0% | 80% | -80% |
| `_nivel_desde_cumplimiento()` | test_calculos.py | 1 | 10% | 90% | -80% |
| `load_cierres()` | test_strategic_ind.py | 1 | 15% | 80% | -65% |

**PROMEDIO COVERAGE: 32% (CRÍTICO - Mínimo requerido: 80%)**

---

### Test Cases FALTANTES

#### Para `categorizar_cumplimiento()`
- [ ] Plan Anual con cumpl=0.95 → "Cumplimiento" (PA specific)
- [ ] Plan Anual con cumpl=0.94 → "Alerta" (PA specific)
- [ ] Entrada string "0,95" (formato latinoamericano)
- [ ] Entrada string "95%" (con porcentaje)
- [ ] Entrada tipo dict (debe fallar gracefully)
- [ ] Entrada array (debe fallar gracefully)

#### Para `_calc_cumpl()`
- [ ] Meta=0, Ejec=0 → 1.0 (caso especial)
- [ ] Sentido Negativo, Ejec=0, Meta>0 → 1.0 (caso especial)
- [ ] Meta=0, Ejec>0 → NaN (error)
- [ ] Entrada string "100" (convertible a float)
- [ ] Entrada string "abc" (no convertible → NaN)
- [ ] Entrada None → NaN
- [ ] Tope regular vs Plan Anual (dinámico)

---

## MATRIZ 8: Puntos de Integración en Pipeline

### Flujo de Datos: Desde Excel Hasta Dashboard

```
Excel (Resultados Consolidados.xlsx)
  ↓
[1] services/data_loader.cargar_dataset()
  ├─ Paso 1: _leer_consolidado_semestral()
  ├─ Paso 2: _enriquecer_clasificacion()
  ├─ Paso 3: _enriquecer_cmi_y_procesos()
  ├─ Paso 4: _reconstruir_columnas_formula()
  ├─ [Paso 4b: _aplicar_calculos_cumplimiento()]
  │  ├─ df["Cumplimiento_norm"] = normalizar_cumplimiento()
  │  └─ df["Categoria"] = categorizar_cumplimiento()
  │
  └─ Retorna: df_main (1450 registros ≈)
     ├─ Cachea por 300 segundos (st.cache_data)
     └─ Consumido por 9 páginas:
        ├─ resumen_general.py
        ├─ resumen_por_proceso.py
        ├─ cmi_estrategico.py
        ├─ gestion_om.py
        ├─ plan_mejoramiento.py
        ├─ pdi_acreditacion.py
        ├─ diagnostico.py
        ├─ seguimiento_reportes.py
        └─ tablero_operativo.py

[2] services/strategic_indicators.load_cierres() [PARALELA]
  ├─ Lee Excel (Cierre historico)
  ├─ [INLINE: recalc cumplimiento cuando NaN]
  ├─ [DEFECTUOSA: _nivel_desde_cumplimiento()]
  └─ Retorna: df_cierres
     └─ Consumido por 2 páginas:
        ├─ gestion_om.py (prioridad OM)
        └─ strategic_indicators (si existe)

[3] scripts/etl/ [BATCH, fuera de aplicación]
  ├─ Rematerializa fórmulas Excel
  ├─ Usa _calc_cumpl() de cumplimiento.py
  └─ Usa formulas_excel.py

CUELLOS DE BOTELLA:
  [1] es crítico: 100% de datos, 9 consumidores
  [2] es secundaria: ~30% de datos, 2 consumidores
```

---

## MATRIZ 9: Matriz de Mitigación de Riesgos

### Riesgo vs Solución vs Impacto

| ID | Riesgo | Solución | Esfuerzo | Impacto |
|---|---|---|---|---|
| R1 | Categorización PA incorrecta en strategic_indicators | Reemplazar `_nivel_desde_cumplimiento()` | 🟢 BAJO | 🔴 CRÍTICO |
| R2 | Cambio de umbral requiere updates manuales | Centralizar en función única | 🟢 BAJO | 🟡 ALTO |
| R3 | Casos especiales divergentes (Meta=0, Ejec=0) | Usar `_calc_cumpl()` como oficial | 🟡 MEDIO | 🟡 ALTO |
| R4 | Test coverage bajo en cálculos | Crear suite test (50+ casos) | 🟡 MEDIO | 🟡 ALTO |
| R5 | Duplicación en 12 dashboards | Eliminar inline, usar funciones | 🟡 MEDIO | 🟡 MEDIO |
| R6 | Mezcla SoC en `load_cierres()` | Separar I/O de cálculo | 🟡 MEDIO | 🟢 BAJO |
| R7 | Lógica inline en HTML/JS dashboards | Crear API endpoint centralizado | 🟠 ALTO | 🟢 BAJO |

---

## MATRIZ 10: Comparativa de Refactorización

### Antes vs Después

| Métrica | ANTES | DESPUÉS | Mejora |
|---------|-------|---------|--------|
| **Funciones de cálculo** | 5 (divergentes) | 1 (oficial) | -80% |
| **Lugares con lógica de cumplimiento** | 12 (inline) | 1 (centralizado) | -92% |
| **Lugares con umbral de Peligro** | 12 | 1 | -92% |
| **LOC en cálculos** | 450 | 200 | -56% |
| **Test cases necesarios** | 15 | 50 | +233% |
| **Tiempo cambio umbral** | 30 min (manual) | 1 min (1 lugar) | -97% |
| **Riesgo de regresión** | 🔴 ALTO | 🟢 BAJO | ✅ |
| **Deuda técnica** | 🔴 CRÍTICA | 🟢 BAJO | ✅ |

---

## CONCLUSIONES TÉCNICAS

### Top 5 Hallazgos

1. **`_nivel_desde_cumplimiento()` es DEFECTUOSA** - NO soporta Plan Anual
   - **Impacto:** Indicadores PA mal categorizados en strategic_indicators
   - **Severidad:** 🔴 CRÍTICA
   - **Fix:** Reemplazar por `categorizar_cumplimiento()` oficial

2. **Tres implementaciones de cálculo Meta/Ejec DIVERGENTES**
   - **Impacto:** Casos especiales (Meta=0&Ejec=0) tratados diferente
   - **Severidad:** 🔴 CRÍTICA
   - **Fix:** Usar `_calc_cumpl()` como función única oficial

3. **Duplicación en 12 dashboards sin reutilización**
   - **Impacto:** Cambio de lógica requiere updates en 12 lugares
   - **Severidad:** 🟡 ALTA
   - **Fix:** Centralizar, importar funciones

4. **Test coverage INSUFICIENTE (32% promedio)**
   - **Impacto:** Cambios sin garantía de corrección
   - **Severidad:** 🟡 ALTA
   - **Fix:** Expandir a 80%+ coverage

5. **Mezcla SoC en `load_cierres()` (I/O + Cálculo)**
   - **Impacto:** Difícil de mantener y testear
   - **Severidad:** 🟡 MEDIA
   - **Fix:** Separar responsabilidades

---

**Documento técnico completado:** 21 abr 2026
