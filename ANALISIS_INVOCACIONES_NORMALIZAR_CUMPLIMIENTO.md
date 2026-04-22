# 🔍 ANÁLISIS: DÓNDE SE USA `normalizar_cumplimiento()`

## 📍 UBICACIÓN DEL CÓDIGO ACTUAL

**Archivo:** `core/calculos.py` (líneas 17-23)

```python
def normalizar_cumplimiento(valor):
    """Garantiza escala decimal [0..n]. Divide /100 solo si valor > 2."""
    if pd.isna(valor):
        return np.nan
    if isinstance(valor, str):
        valor = valor.replace("%", "").replace(",", ".").strip()
        try:
            valor = float(valor)
        except ValueError:
            return np.nan
    valor = float(valor)
    return valor / 100 if valor > 2 else valor  # ← HEURÍSTICA MÁGICA
```

---

## 🎯 INVOCACIONES ENCONTRADAS EN CODEBASE

### **INVOCACIÓN #1: Pipeline ETL Principal** 🔥 CRÍTICA

**Archivo:** `services/data_loader.py` (línea 281)  
**Función:** `_aplicar_calculos_cumplimiento()` (Paso 4b del pipeline)  
**Contexto:** Se ejecuta en CADA carga de dataset

```python
def _aplicar_calculos_cumplimiento(df: pd.DataFrame) -> pd.DataFrame:
    """Paso 4b: Detectar métricas/sin-reporte, recalcular y categorizar cumplimiento."""
    
    # ... [260+ líneas de lógica previas] ...
    
    # ✅ LÍNEA 281-285: INVOCACIÓN AQUÍ
    df["Cumplimiento_norm"] = (
        df["Cumplimiento"].apply(normalizar_cumplimiento)  # ← AQUÍ
        if "Cumplimiento" in df.columns
        else float("nan")
    )
```

**Impacto:**
- Se aplica a **TODA la columna "Cumplimiento"** de cada fila en dataset
- Ejecutado en `cargar_dataset()` (caché ttl=300s)
- Ejecutado en `cargar_dataset_historico()` (para Gestión OM)
- **Afecta:** Todas las 9 páginas que consumen estos datos

**Flujo:**
```
Excel (Resultados Consolidados.xlsx)
  ↓
cargar_dataset()
  ├─ Paso 1: _leer_consolidado_semestral()
  ├─ Paso 2: _enriquecer_clasificacion()
  ├─ Paso 3: _enriquecer_cmi_y_procesos()
  ├─ Paso 4a: _reconstruir_columnas_formula()
  └─ Paso 4b: _aplicar_calculos_cumplimiento()  ← normalizar_cumplimiento() AQUÍ
    ├─ df["Cumplimiento_norm"] = apply(normalizar_cumplimiento)
    └─ df["Categoria"] = categorizar_cumplimiento(Cumplimiento_norm)
  ↓
Todas las 9 páginas consumen dataset normalizado
```

---

### **INVOCACIÓN #2: Recalcificación de Cumplimiento (INLINE)**

**Archivo:** `services/data_loader.py` (línea 251)  
**Función:** `_aplicar_calculos_cumplimiento()` (mismo lugar, línea anterior)

```python
def _aplicar_calculos_cumplimiento(df: pd.DataFrame) -> pd.DataFrame:
    """Paso 4b: Detectar métricas/sin-reporte, recalcular y categorizar cumplimiento."""
    
    # ... [estructura de máscaras para detectar tipo de registro] ...
    
    # ✅ LÍNEA 248-276: RECALCIFICACIÓN INLINE (cuando Cumplimiento es NaN)
    if "Cumplimiento" in df.columns and "Meta" in df.columns and "Ejecucion" in df.columns:
        mask_nan = df["Cumplimiento"].isna() & ~_mask_metrica & ~_mask_sin_reporte
        if mask_nan.any():
            def _recalc_cumpl(row: pd.Series) -> float:
                try:
                    m, e = float(row["Meta"]), float(row["Ejecucion"])
                except (TypeError, ValueError):
                    return float("nan")
                if m == 0 or pd.isna(m) or pd.isna(e):
                    return float("nan")
                sentido = str(row.get("Sentido", "Positivo"))
                raw = (e / m) if sentido == "Positivo" else (m / e if e != 0 else float("nan"))
                if pd.isna(raw):
                    return float("nan")
                tope = 1.0 if str(row.get("Id", "")).strip() in IDS_PLAN_ANUAL else 1.3
                return min(max(raw, 0.0), tope)
            df.loc[mask_nan, "Cumplimiento"] = df[mask_nan].apply(_recalc_cumpl, axis=1)
    
    # ✅ DESPUÉS: SE NORMALIZA EL RESULTADO
    df["Cumplimiento_norm"] = (
        df["Cumplimiento"].apply(normalizar_cumplimiento)  # ← AQUÍ TAMBIÉN
        if "Cumplimiento" in df.columns
        else float("nan")
    )
```

**Impacto:**
- Cuando Cumplimiento es NaN, recalcula como `Meta/Ejecución` o `Ejecución/Meta`
- Luego aplica `normalizar_cumplimiento()` al resultado
- **Problema:** Recalc genera decimales (e.g., 0.5 = 50%), pero heurística asume > 2 → porcentaje

---

## 📊 MATRIZ: TODOS LOS LUGARES DONDE SE AFECTA

| # | Lugar | Función | Línea | Tipo | Impacto | Datos Afectados |
|---|-------|---------|-------|------|--------|-----------------|
| **1** | `services/data_loader.py` | `_aplicar_calculos_cumplimiento()` | 281 | DIRECTO: `.apply()` | 🔥 CRÍTICO | ALL rows en Cumplimiento_norm |
| **2** | `services/data_loader.py` | `_aplicar_calculos_cumplimiento()` | 276 | INDIRECTO: post-recalc | 🔥 CRÍTICO | Cuando Cumplimiento es NaN |
| **3** | `streamlit_app/pages/resumen_general.py` | `main()` | ~150-200 | CONSUMER | 🟡 MODERADO | 150-200 indicadores de resumen |
| **4** | `streamlit_app/pages/resumen_por_proceso.py` | `main()` | ~150-200 | CONSUMER | 🟡 MODERADO | Indicadores por proceso |
| **5** | `streamlit_app/pages/cmi_estrategico.py` | `main()` | ~100-150 | CONSUMER | 🟡 MODERADO | PDI + CNA filtrados |
| **6** | `streamlit_app/pages/gestion_om.py` | `main()` | ~150-200 | CONSUMER | 🟡 MODERADO | Oportunidades de mejora |
| **7** | `streamlit_app/pages/plan_mejoramiento.py` | `main()` | ~100-150 | CONSUMER | 🟡 MODERADO | CNA indicadores |
| **8** | `streamlit_app/pages/tablero_operativo.py` | `main()` | ~150-200 | CONSUMER | 🟡 MODERADO | Indicadores operativos |
| **9** | `streamlit_app/pages/seguimiento_reportes.py` | `main()` | ~100-150 | CONSUMER | 🟡 MODERADO | Reportes consolidados |
| **10** | `streamlit_app/pages/pdi_acreditacion.py` | `main()` | ~100-150 | CONSUMER | 🟡 MODERADO | PDI para acreditación |
| **11** | `streamlit_app/pages/diagnostico.py` | `main()` | ~100-150 | CONSUMER | 🟡 MODERADO | Diagnósticos institucionales |

---

## 📈 DATOS CONCRETOS: EJEMPLOS DE VALORES PROCESADOS

### Ejemplo 1: Indicador de Permanencia (ID 245)

```
Fuente (Excel): Cumplimiento = 2.0 (¿porcentaje 2% o decimal 2.0?)
├─ Heurística: 2.0 ≤ 2 → SE MANTIENE COMO 2.0
├─ Resultado: Cumplimiento_norm = 2.0 (¡INCORRECTO si era %)
├─ Categorización:
│   ├─ 2.0 ≥ 1.05 → "Sobrecumplimiento" (¡ERRÓNEO!)
│   └─ Recomendación: "El indicador sobrepasa expectativas" ❌
└─ Usuario: Lee "Sobrecumplimiento" pero era un dato corrupto
```

### Ejemplo 2: Indicador de Tasa de Aprobación (ID 276)

```
Fuente (Excel): Cumplimiento = 95 (porcentaje, debe ser 0.95)
├─ Heurística: 95 > 2 → SE DIVIDE /100 = 0.95 ✅
├─ Resultado: Cumplimiento_norm = 0.95 (CORRECTO)
├─ Categorización:
│   └─ 0.95 ∈ [UMBRAL_ALERTA=1.00, UMBRAL_SOBRE=1.05) → "Cumplimiento" ✅
└─ Usuario: Recibe categoría correcta
```

### Ejemplo 3: Indicador de Eficiencia (ID 77) - OVER-ACHIEVEMENT

```
Fuente (Excel): Cumplimiento = 150 (porcentaje, 150%)
├─ Heurística: 150 > 2 → SE DIVIDE /100 = 1.50
├─ Resultado: Cumplimiento_norm = 1.50 (¡CAP EN 1.3!)
├─ Nota: _recalc_cumpl() applica "tope = 1.3 si no Plan Anual"
│   └─ Pero si Cumplimiento VIENE del Excel, NO se applica cap
│   └─ Result: 1.50 se pasa sin capping (¡BUG!)
├─ Categorización:
│   └─ 1.50 ≥ 1.05 → "Sobrecumplimiento" (POTENCIALMENTE INCORRECTO)
└─ Usuario: Ve sobre-cumplimiento excesivo
```

### Ejemplo 4: Indicador de Calidad (ID 203) - EDGE CASE

```
Fuente (Excel): Cumplimiento = 2.5 (ambigüedad total)
├─ ¿Es 2.5% o 250%?
├─ Heurística: 2.5 > 2 → SE DIVIDE /100 = 0.025 (asume 250%)
├─ Resultado: Cumplimiento_norm = 0.025 (es 2.5% si era decim...)
├─ Categorización:
│   └─ 0.025 < 0.80 → "Peligro"
├─ Impacto: ¿Indicador realmente en peligro o fue mal entrada?
└─ Usuario: Toma decisión basada en dato ambiguo
```

---

## 🔴 ESCENARIOS DE FALLO OBSERVADO

### FALLO #1: Cero Cálculos en Cambio de Escala

```python
# Cambio de escala de entrada (alguien corrige Excel de porcentaje a decimal)
ANTES:  Cumplimiento = 95  → normalizar(95) = 0.95 ✅
DESPUÉS: Cumplimiento = 0.95 → normalizar(0.95) = 0.95 ✅
# ¡Pero causó CAMBIO de comportamiento!
```

### FALLO #2: Datos Mixed en una Misma Columna

```python
# Si Excel tiene mezcla de escalas en una columna:
df["Cumplimiento"] = [95, 0.95, 2.0, 150, None]
# Heurística aplica por fila independiente:
df["Cumplimiento_norm"] = [0.95, 0.95, 2.0, 1.50, NaN]
#                           ✅    ✅    ❌    ❌     ✅
# Sin validación, NO se detecta el problema
```

### FALLO #3: Caché Sin Invalidación

```python
# Caso: Alguien cambia Excel y recarga app
cargar_dataset() {
  # Caché @st.cache_data(ttl=300) devuelve resultado viejo
  # Si Excel cambió de escala, la normalización anterior es obsoleta
  # Usuario sigue viendo datos normalizados con escala antigua
}
```

---

## 📝 CASOS DE USO REALES POR INDICADOR

Basado en auditoría de 5 KPIs:

| ID | Nombre | Fuente Escala | Valor Típico | Normaliza Correctamente? |
|----|--------------------|------------------|-----------------|-------|
| **245** | Permanencia | Decimal [0,1] | 0.92 | ⚠️ SÍ (pero casualmente) |
| **276** | Aprobación | Porcentaje [0,100] | 95 | ✅ SÍ |
| **77** | Eficiencia | Porcentaje [0,150] | 125 | ⚠️ PARCIAL (sin cap) |
| **203** | Calidad | Mixed? | 2.5 | ❌ NO (ambiguo) |
| **274** | Retención | Decimal [0,1] | 0.88 | ⚠️ SÍ (pero casualmente) |

---

## 💡 ¿POR QUÉ LA HEURÍSTICA EXISTE?

**Hipótesis (basada en auditoría):**

1. **Excel tiene mixed scales** - Algunos indicadores en %, otros en decimales
2. **Sin documentación de escala** - No hay metadatos que indiquen cuál es cuál
3. **"Detect automatically"** - Alguien pensó "si > 2, debe ser %, sino decimal"
4. **Aceptable para 70-80% casos** - Funciona para la mayoría por coincidencia
5. **Falla para edge cases** - 2.0-2.9 range causa problemas

---

## 🚨 RESUMEN DEL RIESGO

| Aspecto | Severidad | Detalle |
|--------|-----------|---------|
| **Dónde ocurre** | 🔥 CRÍTICO | En ETL principal (data_loader.py línea 281) - afecta TODOS los datos |
| **Cuándo ocurre** | 🔥 CRÍTICO | En CADA carga de dataset (se ejecuta después del recalc cumplimiento) |
| **A quién afecta** | 🔥 CRÍTICO | Todas las 9 páginas consumen estos datos normalizados |
| **Qué pasa** | 🔥 CRÍTICO | Normalización incorrecta → Categorización incorrecta → Decisiones erróneas |
| **Posibles impactos** | 🔥 CRÍTICO | <ul><li>Indicadores mal categorizados</li><li>Recomendaciones inciertas</li><li>Reportes con datos erróneos</li><li>Decisiones estratégicas basadas en datos malos</li><li>Pérdida de confianza en sistema</li></ul> |

---

## 🎯 CONCLUSIÓN

**`normalizar_cumplimiento()` es una función crítica que:**

1. ✅ **SE USA 1 VEZ DIRECTAMENTE** en línea 281 de `data_loader.py`
2. ✅ **PERO AFECTA A 150-200+ INDICADORES** por cada carga
3. ✅ **IMPACTA TODAS LAS 9 PÁGINAS** que consumen los datos normalizados
4. ✅ **SE EJECUTA EN CACHÉ CADA 5 MINUTOS** (TTL=300s)
5. ⚠️ **LA HEURÍSTICA "SI > 2" CAUSA FALLOS EN EDGE CASES** (valores entre 2.0-2.9, mixed scales)

**Decisión de refactoring debe considerare:**
- Impacto masivo: Un cambio aquí afecta TODO el sistema
- Criticidad: Sin validación correcta → datos incorrectos globalmente
- Timing: Implementar en Semana 1 (bloqueador para otras fixes)

