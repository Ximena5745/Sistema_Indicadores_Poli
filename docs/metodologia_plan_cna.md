# Metodología — Medición del Plan de Mejoramiento CNA

## 1. Fuentes de datos

### 1.1 Indicadores del Plan de Mejoramiento
- **Archivo:** `data/raw/Plan de mejoramiento/Indicadores Plan de Mejoramiento.xlsx`
- **Hoja:** `Indicadores Plan de Mejor` (header fila 2)
- **Filas:** 66 indicadores
- **Campos clave:**
  - `Factor`, `Característica`, `Acción de Mejora`, `Indicador`
  - `ID Kawak` (25/66 con ID)
  - `Indicador o Metrica` (53 Indicador / 5 Métrica / 8 Pendiente)
  - `Estado` (31 Pendiente / 26 Creado / 5 Autoevaluación / 2 Crear)
  - `Estado de aprobación` (60 Aprobado / 5 Pendiente)
  - `Meta 2025/2026`, `Ejecución 2025/2026`, `% Cump 2025/2026`
  - `2027-2030`: columnas de metas futuras

### 1.2 Métricas CNA
- **Archivo:** `data/raw/Plan de mejoramiento/Resultados_Consolidados_CNA_actualizado.xlsx`
- **Hoja:** `Metricas` — 1142 filas, 85 indicadores, 107 subindicadores
- **Hoja:** `Factor-Característica` — catálogo canónico 12 factores → 38 características
- **Periodos:** `2019-1` a `2026-1`
- **Meta:** solo 4 filas con dato (no se usa para cumplimiento)

## 2. Llaves de relación

| Nivel | Plan ↔ Métricas |
|-------|-----------------|
| Factor | ✅ Coincidencia por nombre normalizado |
| Característica | ✅ Coincidencia vía catálogo Factor-Característica |
| Indicador | ❌ 0 coincidencias exactas (normalizado) |
| Subindicador | ❌ No aplica en Plan |
| ID | ⚠️ Solo 1 overlap (ID 109) |

**Decisión:** Dos módulos separados, sin join a nivel indicador. Vínculo solo a nivel Factor/Característica.

## 3. Reglas de clasificación — Estado (Plan)

Combinación de `Estado` + `Estado de aprobación` + `Indicador o Metrica`:

| Estado | Regla |
|--------|-------|
| **Activo** | `Estado de aprobación = Aprobado` AND `Indicador o Metrica = Indicador` AND tiene Meta o Ejecución numérica en 2025/2026 |
| **Aprobado** | `Estado de aprobación = Aprobado` pero sin medición aún |
| **Pendiente** | `Estado de aprobación = Pendiente` OR `Estado ∈ {Pendiente, Crear}` OR `Indicador o Metrica = Pendiente` |

## 4. Reglas de cumplimiento — Indicadores (Plan)

- **Cumplimiento** = `Ejecución / Meta` (solo donde ambos son numéricos y Meta ≠ 0)
- **Tope:** 130% (cap para evitar distorsión por sobrecumplimiento extremo)
- **Promedio general/por factor:** media aritmética de `%Cump` disponibles
- **Sin dato:** excluido del promedio, etiquetado como "Pendiente medición"
- **Resto (sin Meta o sin Ejecución):** `n_con_dato / n_total` visible

## 5. Reglas de dirección — Métricas

- **Dirección** = comparación de los 2 últimos periodos con dato
- Clasificación: `aumento` | `disminución` | `estable` | `sin datos`
- **NEUTRA:** no califica si subir o bajar es "bueno" o "malo"
- **Promedio por factor:** `% de indicadores en aumento` (no promedio de valores)

## 6. Tratamiento de casos especiales

| Caso | Regla |
|------|-------|
| Indicadores sin ejecución | Se muestran como "Sin dato", no se penaliza con 0% |
| Métricas sin histórico | `st.info("único periodo — sin evolución")` |
| Registros duplicados F1/F7 | Se cuentan en ambos factores + nota metodológica |
| Indicadores sin métrica asociada | Se muestran en tabla QA como "Sin correspondencia" |
| Métricas sin indicador asociada | Se muestran en tabla QA como "Sin correspondencia" |
| Múltiples registros por periodo | `keep="last"` en deduplicación |
| Datos faltantes en series | Se omiten del cálculo de tendencia |

## 7. Tabla QA (cruce de fuentes)

| Métrica | Valor |
|---------|-------|
| Indicadores Plan únicos | 66 |
| Indicadores Métricas únicos | 85 |
| Subindicadores Métricas | 107 |
| Match exacto Plan↔Métricas | 0 |
| Overlap IDs (Kawak↔Id) | 1 (ID 109) |
| Duplicados en Métricas (F1/F7) | ~10 filas |
| Plan con Ejecución 2025 | 14/66 |
| Plan con Ejecución 2026 | 6/66 |
| Métricas con Meta | 4/1142 |

## 8. Visualizaciones

### Nivel 0 — Resumen
- KPIs Estado: Total / Activos / Aprobados / Pendientes + %
- Cumplimiento general: promedio %Cump (solo con dato) + n
- Grid 12 factores: píldoras clicables con ícono + %Cump
- Tendencia: línea %Cump por periodo (Plan) + línea % en aumento (Métricas)

### Nivel 1 — Factor
- KPIs por factor: indicadores, %Cump, en brecha (<60%), alto (≥90%)
- Tabs A (Indicadores Plan) / B (Métricas CNA)
- Heatmap Factor×Periodo: dirección por periodo

### Nivel 2 — Indicador/Métrica
- Tarjetas con Meta, Ejecución, %Cump, tendencia
- Línea evolución con punteado Meta
- Tabla historia por periodo
- Subindicadores (si existen)

## 9. Dependencias de código

```
services/plan_mejoramiento_loader.py
├── load_plan_indicadores()          ← NUEVO
├── classify_plan_estado()           ← NUEVO
├── compute_plan_cumplimiento_by_factor()  ← NUEVO
├── get_plan_indicadores_for_factor()      ← NUEVO
├── aggregate_plan_estado_by()             ← NUEVO
├── load_metricas_raw()              ← EXISTENTE (sin cambios)
├── load_factor_caracteristica_map()  ← EXISTENTE (sin cambios)
├── compute_trend_table()            ← EXISTENTE (sin cambios)
└── aggregate_trend_by()             ← EXISTENTE (sin cambios)

streamlit_app/pages/plan_mejoramiento.py  ← EVOLUCIONA
├── Resumen ejecutivo (V0-V6)
├── Vista Factor (V7-V10)
├── Tab A Indicadores (V11-V13)
└── Tab B Métricas (V14-V16)
```
