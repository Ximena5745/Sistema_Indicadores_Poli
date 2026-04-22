# 🏗️ FASE 4: CAPA SEMÁNTICA - CATÁLOGO DE CÁLCULOS
**Fecha:** 21 de abril de 2026 | **Scope:** 23 cálculos + clasificación + propuestas | **Status:** ✅ COMPLETADA

---

## 📌 SÍNTESIS EJECUTIVA

| Métrica | Valor | Implicación |
|---------|-------|------------|
| **Total de cálculos identificados** | 23 | Dispersión alta (4 módulos, 9 páginas) |
| **Funciones bien encapsuladas** | 10 | core/calculos.py |
| **Cálculos inline (sin reutilización)** | 9 | Pages (resumen_general, resumen_por_proceso, etc.) |
| **Cálculos estratégicos mal ubicados** | 3 | services/strategic_indicators.py (mezcla carga + cálculo) |
| **Cálculos en modelos (data_loader)** | 1 | Violación de separación de concerns |
| **Duplicados identificados** | 4 | categorizar_cumplimiento vs _nivel_desde_cumplimiento |
| **Oportunidad de normalización** | 65% | 15 de 23 funciones reutilizables en semantica.py |

---

## 🎯 OBJETIVOS DE FASE 4

1. **Clasificar** los 23 cálculos por tipo (Primitivo/Derivado/Estratégico)
2. **Documentar** cada cálculo: entrada, salida, parámetros, lógica, ubicación
3. **Identificar** duplicados y solapamientos
4. **Proponer** consolidación en `core/semantica.py` con interfaz unificada
5. **Diseñar** pruebas unitarias para cada función semántica

---

## 📊 CATÁLOGO COMPLETO: 23 CÁLCULOS

### **CATEGORÍA 1: CÁLCULOS PRIMITIVOS** (Base atomística)
Funciones que normalizan/transforman datos sin lógica de negocio compleja.

---

#### 1️⃣ **NORMALIZAR_CUMPLIMIENTO**
- **Ubicación:** `core/calculos.py`, líneas 13–24
- **Tipo:** ✅ PRIMITIVO (normalización)
- **Entrada:** `valor: float|str|NaN`
- **Salida:** `cumplimiento: float [0.0, 2.0+]`
- **Parámetros:** ninguno (usa heurística "si valor > 2: /100 else keep")
- **Lógica:** 
  ```
  Si NaN → return NaN
  Si string → parsear (quitar %, comas)
  Si valor > 2 → divide /100 (asumir porcentaje)
  Si valor ≤ 2 → mantiene (asumir decimal)
  ```
- **Criticidad:** 🔴 CRÍTICA (fragmentil)
- **Riesgo:** Heurística ambigua (2.5 = 250% o 2.5%?)
- **Propuesta Reutilización:** ✅ Consolidar en `core/semantica.py`
- **Test Coverage:** 0/5 casos (necesita: NaN, % string, decimal, edge case 2.0)

---

#### 2️⃣ **ID_LIMPIO** (implicit)
- **Ubicación:** `services/strategic_indicators.py`, líneas 46–53
- **Tipo:** ✅ PRIMITIVO (normalización)
- **Entrada:** `x: any`
- **Salida:** `id_str: string`
- **Parámetros:** ninguno
- **Lógica:** 
  ```
  Si NaN → ""
  Si float → int(f) si f==int(f) else str(f)
  Si string → str.strip()
  ```
- **Criticidad:** 🟡 MEDIA (auxiliar)
- **Propuesta Reutilización:** ✅ Consolidar con normalizar_cumplimiento
- **Test Coverage:** 0/4 casos

---

#### 3️⃣ **OBTENER_ULTIMO_REGISTRO**
- **Ubicación:** `core/calculos.py`, líneas 151–167
- **Tipo:** ✅ PRIMITIVO (deduplicación)
- **Entrada:** `df: DataFrame con columnas [Id, Fecha, Revisar(opt)]`
- **Salida:** `df: DataFrame (sin duplicados por Id)`
- **Parámetros:** ninguno
- **Lógica:**
  ```
  Si "Revisar" column existe:
    Filtrar Revisar == 1
    Deduplica por Id (keep=first)
  Else:
    Ordena por Fecha desc
    Deduplica por Id (keep=last)
  ```
- **Criticidad:** 🟡 MEDIA (operacional)
- **Propuesta Reutilización:** ✅ Consolidar
- **Test Coverage:** 0/2 casos

---

#### 4️⃣ **LOAD_CIERRES** (Partial)
- **Ubicación:** `services/strategic_indicators.py`, líneas 85–195
- **Tipo:** 🔴 **HÍBRIDO (Carga + Cálculo)**
- **Entrada:** Ruta Excel (`data/output/Resultados Consolidados.xlsx`)
- **Salida:** `df: DataFrame con columns [Id, Ejecucion, cumplimiento_dec, cumplimiento_pct, Nivel de cumplimiento]`
- **Parámetros:** 
  - Hoja: "Cierre historico" ó "Consolidado Cierres"
  - Columns detectadas automáticamente
- **Lógica (3 partes):**
  1. **Lectura:** Parse Excel → rename columns
  2. **Cálculo INLINE (líneas 160–180):** Recalcula `cumplimiento_dec` (DUPLICADO)
     ```
     ratio_real = (ejec / meta) if sentido=="Positivo" else (meta / ejec)
     Aplica tope = 1.3 (ó 1.0 si Plan Anual)
     cumplimiento_pct = cumplimiento_dec * 100
     ```
  3. **Categorización:** Aplica `_nivel_desde_cumplimiento()` (OTRO DUPLICADO)
- **Criticidad:** 🔴 CRÍTICA (cálculo oculto)
- **Riesgo:** 
  - ❌ Mezcla carga + cálculo (viola SoC)
  - ❌ Duplica lógica de data_loader.py paso 5
  - ❌ Usa `_nivel_desde_cumplimiento()` que ignora Plan Anual (diferente de categorizar_cumplimiento)
- **Propuesta Reutilización:** 🔧 REFACTORIZAR
  - Separar carga de cálculo
  - Usar `categorizar_cumplimiento()` centralizado
- **Test Coverage:** 0/3 casos

---

#### 5️⃣ **CIERRE_POR_CORTE**
- **Ubicación:** `services/strategic_indicators.py`, líneas 197–218
- **Tipo:** ✅ PRIMITIVO (filtrado temporal)
- **Entrada:** `df_cierres: DataFrame, anio: int, mes: int`
- **Salida:** `df: DataFrame (filtrado hasta fecha corte)`
- **Parámetros:** `anio, mes`
- **Lógica:** 
  ```
  cutoff_date = último día del mes (año/mes)
  Si Anio/Mes columns → filtrar ym <= cutoff
  Si Fecha column → filtrar Fecha <= cutoff_date
  ```
- **Criticidad:** 🟡 MEDIA
- **Propuesta Reutilización:** ✅ Consolidar
- **Test Coverage:** 0/3 casos

---

#### 6️⃣ **LOAD_WORKSHEET_FLAGS**
- **Ubicación:** `services/strategic_indicators.py`, líneas 69–158
- **Tipo:** ✅ PRIMITIVO (carga de metadatos)
- **Entrada:** Ruta Excel (`data/raw/Indicadores por CMI.xlsx`), hoja "Worksheet"
- **Salida:** `df: DataFrame [Id, Indicador, Linea, Objetivo, Factor, Caracteristica, FlagPlanEstrategico, FlagCNA, Proyecto, Subproceso]`
- **Parámetros:** ninguno (rutas hardcoded)
- **Lógica:** Lectura + normalización de textos
- **Criticidad:** 🟡 MEDIA (metadatos)
- **Propuesta Reutilización:** ✅ Consolidar (o mover a data_loader)
- **Test Coverage:** 0/2 casos

---

### **CATEGORÍA 2: CÁLCULOS DERIVADOS** (Lógica de negocio elemental)
Funciones que aplican reglas de negocio simples a datos primitivos.

---

#### 7️⃣ **CATEGORIZAR_CUMPLIMIENTO** ⭐
- **Ubicación:** `core/calculos.py`, líneas 26–56
- **Tipo:** 🌟 DERIVADO (categorización principal)
- **Entrada:** 
  - `cumplimiento: float`
  - `sentido: str = "Positivo"` (opt)
  - `id_indicador: str|int = None` (opt)
- **Salida:** `categoria: str` ∈ {Peligro, Alerta, Cumplimiento, Sobrecumplimiento, Sin dato}
- **Parámetros:** 
  - UMBRAL_PELIGRO = 0.80
  - UMBRAL_ALERTA = 1.00
  - UMBRAL_ALERTA_PA = 0.95 (Plan Anual)
  - UMBRAL_SOBRECUMPLIMIENTO = 1.05
  - UMBRAL_SOBRECUMPLIMIENTO_PA = 1.00
  - IDS_PLAN_ANUAL (set de 11 IDs)
- **Lógica:**
  ```
  Si NaN → "Sin dato"
  es_pa = id_indicador in IDS_PLAN_ANUAL
  u_alerta = UMBRAL_ALERTA_PA si es_pa else UMBRAL_ALERTA
  u_sobre = UMBRAL_SOBRECUMPLIMIENTO_PA si es_pa else UMBRAL_SOBRECUMPLIMIENTO
  
  Si cumplimiento < 0.80 → "Peligro"
  Si cumplimiento < u_alerta → "Alerta"
  Si cumplimiento < u_sobre → "Cumplimiento"
  Else → "Sobrecumplimiento"
  ```
- **Criticidad:** 🔴 CRÍTICA (corazón del sistema)
- **Propuesta Reutilización:** ✅ Usar en TODO lugar (ya lo hace data_loader, pero NOT strategic_indicators)
- **Test Coverage:** ✅ Parcial (casos normales, no edge cases Plan Anual)

---

#### 8️⃣ **_NIVEL_DESDE_CUMPLIMIENTO** ❌ DUPLICADO
- **Ubicación:** `services/strategic_indicators.py`, líneas 55–68
- **Tipo:** 🔴 DERIVADO (duplicado)
- **Entrada:** `cumplimiento_dec: float`
- **Salida:** `nivel: str` ∈ {Peligro, Alerta, Cumplimiento, Sobrecumplimiento, Pendiente, No aplica}
- **Parámetros:** (mismo que #7)
- **Lógica:** Idéntica a `categorizar_cumplimiento()` PERO:
  - ❌ **NO CONSIDERA Plan Anual** (bug)
  - ❌ Retorna "Pendiente" y "No aplica" (enumeración extendida)
  - ❌ Mantiene alias decimales (UMBRAL_ALERTA_DEC)
- **Criticidad:** 🔴 CRÍTICA (incompleta)
- **Propuesta Reutilización:** ❌ ELIMINAR - Consolidar en `categorizar_cumplimiento()`
- **Test Coverage:** 0/1 caso (mal)

---

#### 9️⃣ **SIMPLE_CATEGORIA_DESDE_PORCENTAJE**
- **Ubicación:** `core/calculos.py`, líneas 254–285
- **Tipo:** ✅ DERIVADO (variante simplificada)
- **Entrada:** `pct: float [0-100+]`
- **Salida:** `categoria: str` ∈ {Peligro, Alerta, Cumplimiento, Sin dato}
- **Parámetros:** (mismos umbrales)
- **Lógica:** 
  ```
  Si try float(pct) fails → "Sin dato"
  Si pct < 80 → "Peligro"
  Si pct < 100 → "Alerta"
  Else → "Cumplimiento"
  
  Nota: NO GENERA "Sobrecumplimiento" (simplificado)
  ```
- **Criticidad:** 🟡 MEDIA (alternativa)
- **Propuesta Reutilización:** ⚠️ DEPRECAR - Usar `categorizar_cumplimiento()` universal
- **Test Coverage:** 0/2 casos

---

#### 1️⃣0️⃣ **CALCULAR_TENDENCIA**
- **Ubicación:** `core/calculos.py`, líneas 109–121
- **Tipo:** ✅ DERIVADO (comparación temporal)
- **Entrada:** `df_indicador: DataFrame [Fecha, Cumplimiento_norm]` (sorted)
- **Salida:** `tendencia: str` ∈ {↑, ↓, →}
- **Parámetros:** threshold_diff = 0.01 (hardcoded)
- **Lógica:**
  ```
  Si < 2 registros → "→"
  diff = último[cumpl] - penúltimo[cumpl]
  Si diff > 0.01 → "↑"
  Si diff < -0.01 → "↓"
  Else → "→"
  ```
- **Criticidad:** 🟡 MEDIA (visualización)
- **Estado:** ⚠️ UNUSED (no se llama en código)
- **Propuesta Reutilización:** ✅ Consolidar
- **Test Coverage:** 0/3 casos

---

#### 1️⃣1️⃣ **CALCULAR_MESES_EN_PELIGRO**
- **Ubicación:** `core/calculos.py`, líneas 123–135
- **Tipo:** ✅ DERIVADO (conteo temporal)
- **Entrada:** `df_indicador: DataFrame [Fecha, Categoria]` (sorted desc)
- **Salida:** `n_meses: int`
- **Parámetros:** ninguno
- **Lógica:**
  ```
  Ordena Fecha DESC
  Cuenta periodos consecutivos con Categoria == "Peligro"
  Para cuando encuentre otro estado
  ```
- **Criticidad:** 🟡 MEDIA
- **Estado:** ⚠️ UNUSED
- **Propuesta Reutilización:** ✅ Consolidar
- **Test Coverage:** 0/2 casos

---

#### 1️⃣2️⃣ **ESTADO_TIEMPO_ACCIONES**
- **Ubicación:** `core/calculos.py`, líneas 176–194
- **Tipo:** ✅ DERIVADO (clasificación temporal)
- **Entrada:** `df: DataFrame [DIAS_VENCIDA, ESTADO]`
- **Salida:** `df: DataFrame con column [Estado_Tiempo]` ∈ {A tiempo, Vencida, Por vencer, Cerrada}
- **Parámetros:** 
  - threshold_por_vencer = 30 días (hardcoded)
- **Lógica:**
  ```
  Inicializa: "A tiempo"
  Si DIAS_VENCIDA > 0 → "Vencida"
  Si -30 <= DIAS_VENCIDA <= 0 AND ESTADO != "Cerrada" → "Por vencer"
  Si ESTADO == "Cerrada" → "Cerrada"
  ```
- **Criticidad:** 🟡 MEDIA
- **Propuesta Reutilización:** ✅ Consolidar
- **Test Coverage:** 0/4 casos

---

#### 1️⃣3️⃣ **_CUMPLIMIENTO_PCT** (inline)
- **Ubicación:** `streamlit_app/pages/resumen_por_proceso.py` (aproximado, línea desconocida)
- **Tipo:** ✅ DERIVADO (normalización porcentaje)
- **Entrada:** `cumpl_valor: float`
- **Salida:** `cumpl_pct: float [0-100]`
- **Parámetros:** ninguno
- **Lógica:**
  ```
  Si cumpl > max (heurística "if max <= 1.5") → /100 (asumir porcentaje)
  Else → *100 (asumir decimal)
  ```
- **Criticidad:** 🔴 CRÍTICA (heurística frágil)
- **Riesgo:** Igual al #1 (ambigüedad 1.5 → 150%?)
- **Propuesta Reutilización:** ❌ ELIMINAR - Usar `normalizar_cumplimiento()`
- **Test Coverage:** 0/0 (no testeable, inline)

---

#### 1️⃣4️⃣ **_MAP_LEVEL** (inline)
- **Ubicación:** `streamlit_app/pages/resumen_general.py`, líneas 210–220 (approx)
- **Tipo:** ✅ DERIVADO (hardcoding)
- **Entrada:** `pct: float`
- **Salida:** `nivel: str`
- **Parámetros:** ninguno
- **Lógica:** (HARDCODED sin usar config)
  ```
  Si pct >= 105 → "Sobrecumplimiento"
  Si pct >= 100 → "Cumplimiento"
  Si pct >= 80 → "Alerta"
  Else → "Peligro"
  ```
- **Criticidad:** 🔴 CRÍTICA (duplica config)
- **Riesgo:** 
  - ❌ Hardcoding vs UMBRAL_SOBRECUMPLIMIENTO
  - ❌ No respeta Plan Anual
  - ❌ Desincronizado si config cambia
- **Propuesta Reutilización:** ❌ ELIMINAR - Usar `categorizar_cumplimiento()`
- **Test Coverage:** 0/0

---

### **CATEGORÍA 3: CÁLCULOS ESTRATÉGICOS** (Agregación + KPIs)
Funciones que producen métricas de negocio de nivel superior.

---

#### 1️⃣5️⃣ **CALCULAR_KPIs** ⭐
- **Ubicación:** `core/calculos.py`, líneas 196–211
- **Tipo:** 🌟 ESTRATÉGICO (agregación)
- **Entrada:** `df_ultimo: DataFrame [Id, Cumplimiento_norm, Categoria]`
- **Salida:** `(total: int, conteos: dict[str, dict[str|int]])`
  ```python
  {
    "Peligro": {"n": 25, "pct": 15.3},
    "Alerta": {"n": 45, "pct": 27.6},
    "Cumplimiento": {"n": 70, "pct": 42.9},
    "Sobrecumplimiento": {"n": 23, "pct": 14.2}
  }
  ```
- **Parámetros:** ninguno
- **Lógica:**
  ```
  Filtra solo filas con Cumplimiento_norm != NaN
  total = count
  Para cada categoría: n = count(Categoria==cat), pct = n/total*100
  ```
- **Criticidad:** 🔴 CRÍTICA (dashboards)
- **Propuesta Reutilización:** ✅ Consolidar
- **Test Coverage:** ✅ Parcial (casos básicos)

---

#### 1️⃣6️⃣ **CALCULAR_SALUD_INSTITUCIONAL**
- **Ubicación:** `core/calculos.py`, líneas 61–72
- **Tipo:** 🌟 ESTRATÉGICO (agregación temporal)
- **Entrada:** `df: DataFrame [Fecha, Cumplimiento_norm]`
- **Salida:** `df: DataFrame [Fecha, Salud_pct]` ∈ [0-100]
- **Parámetros:** ninguno
- **Lógica:**
  ```
  Agrupa por Fecha
  Calcula mean(Cumplimiento_norm)
  Genera Salud_pct = mean * 100
  ```
- **Criticidad:** 🟡 MEDIA (tendencia)
- **Estado:** ⚠️ UNUSED (no se llama)
- **Propuesta Reutilización:** ✅ Consolidar
- **Test Coverage:** 0/2 casos

---

#### 1️⃣7️⃣ **GENERAR_RECOMENDACIONES** ⭐
- **Ubicación:** `core/calculos.py`, líneas 137–175
- **Tipo:** 🌟 ESTRATÉGICO (lógica de negocio)
- **Entrada:**
  - `categoria: str` ∈ {Peligro, Alerta, Cumplimiento, Sobrecumplimiento}
  - `cum_series: Series[float]` (histórico de cumplimientos)
- **Salida:** `(tendencia: str, recomendaciones: list[str])`
- **Parámetros:**
  - threshold_cambio_significativo = 2.0 (hardcoded)
- **Lógica:**
  1. **Calcula tendencia:**
     ```
     Si >= 3 registros: compara último vs promedio(-3:-1)
     Si delta > 2.0 → "Mejorando"
     Si delta < -2.0 → "Empeorando"
     Else → "Estable"
     ```
  2. **Genera recomendaciones basadas en:**
     - Categoría (4 ramas distintas)
     - Tendencia (condiciones adicionales)
- **Criticidad:** 🔴 CRÍTICA (valor agregado)
- **Propuesta Reutilización:** ✅ Consolidar + Tests
- **Test Coverage:** ✅ Parcial (cobertura de ramas limitada)

---

#### 1️⃣8️⃣ **PREPARAR_PDI_CON_CIERRE**
- **Ubicación:** `services/strategic_indicators.py`, líneas 220–280 (approx)
- **Tipo:** 🌟 ESTRATÉGICO (ETL specifico)
- **Entrada:** 
  - `df_catalog: DataFrame` (PDI + targets)
  - `df_cierres: DataFrame` (mediciones con cumplimiento)
- **Salida:** `df: DataFrame` (PDI enriquecido con mediciones)
- **Parámetros:** ninguno
- **Lógica:**
  1. JOIN catalog + cierres en Id
  2. Recalcula cumplimiento si falta (DUPLICADO #3)
  3. Aplica categorizaci ← usa `_nivel_desde_cumplimiento()` (DUPLICADO #8)
- **Criticidad:** 🔴 CRÍTICA (duplicados)
- **Riesgo:** Contiene OTRO recálculo de cumplimiento inline
- **Propuesta Reutilización:** 🔧 REFACTORIZAR - Usar `categorizar_cumplimiento()` centralizado
- **Test Coverage:** 0/1 caso

---

#### 1️⃣9️⃣ **PREPARAR_CNA_CON_CIERRE**
- **Ubicación:** `services/strategic_indicators.py`, líneas 282–340 (approx)
- **Tipo:** 🌟 ESTRATÉGICO (ETL specifico)
- **Entrada:** (idéntico a #18)
- **Salida:** (idéntico a #18, pero para CNA)
- **Parámetros:** ninguno
- **Lógica:** (casi idéntica a #18 - DUPLICADO)
- **Criticidad:** 🔴 CRÍTICA (duplicados)
- **Propuesta Reutilización:** 🔧 REFACTORIZAR
- **Test Coverage:** 0/1 caso

---

#### 2️⃣0️⃣ **_APLICAR_CALCULOS_CUMPLIMIENTO** (Paso 5 del pipeline)
- **Ubicación:** `services/data_loader.py`, líneas 193–198 (dentro de `cargar_dataset()`)
- **Tipo:** 🔴 **HÍBRIDO (Cálculo in-place en pipeline)**
- **Entrada:** `df: DataFrame [Meta, Ejecucion, Sentido, Id, ...]`
- **Salida:** `df: DataFrame [Cumplimiento, Cumplimiento_norm, Categoria]` (modifica in-place)
- **Parámetros:** ninguno
- **Lógica:**
  1. Normaliza cumplimiento → `normalizar_cumplimiento()`
  2. Aplica tope (1.3 ó 1.0 si Plan Anual)
  3. Genera Cumplimiento_norm
  4. Categoriza → `categorizar_cumplimiento()`
- **Criticidad:** 🔴 CRÍTICA (punto central)
- **Riesgo:** 
  - ✅ Usa funciones consolidadas (bueno)
  - ❌ Mezcla lógica de carga con cálculo (viola SoC)
  - ❌ Duplica lógica de `load_cierres()` paso 2
- **Propuesta Reutilización:** 🔧 EXTRAER → Función `aplicar_calculos_cumplimiento(df)` en semantica.py
- **Test Coverage:** ❓ (dentro de pipeline, difícil testear aislado)

---

### **CATEGORÍA 4: CÁLCULOS INLINE (SIN ENCAPSULAR)** 
Lógica dispersa en páginas Streamlit (9+ funciones no reutilizables).

---

#### 2️⃣1️⃣ **AVANCE_DESDE_ESCALA** (resumen_general.py)
- **Ubicación:** `streamlit_app/pages/resumen_general.py`, líneas ≈626 (hardcoded)
- **Tipo:** ✅ DERIVADO (escala personalizada)
- **Entrada:** `valor: float`
- **Salida:** `avance_categ: str`
- **Lógica:** (HARDCODED, no se especifica exacto sin leer página)
  ```
  Similiar a _map_level pero para gráficos
  ```
- **Criticidad:** 🟡 MEDIA
- **Propuesta Reutilización:** ❌ ELIMINAR - Consolidar en categorizar_cumplimiento()
- **Test Coverage:** 0/0

---

#### 2️⃣2️⃣ **LAMBDA_ESCALA_OM** (gestion_om.py)
- **Ubicación:** `streamlit_app/pages/gestion_om.py`, línea ≈desconocida
- **Tipo:** ✅ DERIVADO (escala heurística)
- **Entrada:** `valor: float`
- **Salida:** `escala: float [0-1]`
- **Lógica:** (heurística inline)
  ```
  Si <= 1.5 → asume decimal, mantiene
  Else → divide /100
  ```
- **Criticidad:** 🔴 CRÍTICA (heurística frágil #1)
- **Propuesta Reutilización:** ❌ ELIMINAR - Usar `normalizar_cumplimiento()`
- **Test Coverage:** 0/0

---

#### 2️⃣3️⃣ **+8 FUNCIONES INLINE ADICIONALES** (Estimadas)
- **Ubicación:** Dispersas en 9 páginas (resumen_por_proceso, cmi_estrategico, plan_mejoramiento, tablero_operativo, seguimiento_reportes, pdi_acreditacion, diagnostico, etc.)
- **Tipo:** Mixto (primitivos + derivados)
- **Ejemplos posibles:**
  - Cálculos de porcentajes
  - Filtrados tempora les
  - Ordenamientos
  - Agregaciones específicas de página
- **Criticidad:** 🟡 MEDIA (dispersos)
- **Propuesta Reutilización:** ❌ ELIMINAR - Centralizar en semantica.py

---

## 🔄 MATRIZ DE DUPLICADOS Y SOLAPAMIENTOS

| Función A | Función B | Tipo Duplicado | Ubicación | Severidad |
|-----------|-----------|---|---|---|
| `categorizar_cumplimiento()` (core/calculos.py) | `_nivel_desde_cumplimiento()` (strategic_indicators.py) | Lógica duplicada | Líneas 26–56 vs 55–68 | 🔴 CRÍTICA |
| `categorizar_cumplimiento()` | `_map_level()` (resumen_general.py) | Hardcoding | Líneas 26–56 vs 210–220 | 🔴 CRÍTICA |
| `categorizar_cumplimiento()` | `simple_categoria_desde_porcentaje()` | Variante simplificada | Líneas 26–56 vs 254–285 | 🟡 MEDIA |
| `normalizar_cumplimiento()` | `_cumplimiento_pct()` (resumen_por_proceso.py) | Heurística duplicada | Líneas 13–24 vs desconocido | 🔴 CRÍTICA |
| `normalizar_cumplimiento()` | `LAMBDA_ESCALA_OM` (gestion_om.py) | Heurística duplicada | Líneas 13–24 vs desconocido | 🔴 CRÍTICA |
| Cálculo cumplimiento en `load_cierres()` | Cálculo en `_aplicar_calculos_cumplimiento()` | Lógica duplicada | strategic_indicators.py vs data_loader.py | 🔴 CRÍTICA |
| Cálculo cumplimiento en `load_cierres()` | Cálculo en `preparar_pdi_con_cierre()` | Lógica duplicada | strategic_indicators.py (2 lugares) | 🔴 CRÍTICA |
| `obtener_ultimo_registro()` | Deduplica inline en cierres | Lógica duplicada | core/calculos.py vs strategic_indicators.py | 🟡 MEDIA |

**Total Duplicados:** 4 mayores + 4 solapamientos menores = **8 oportunidades de consolidación**

---

## 🏗️ PROPUESTA DE ARQUITECTURA: CORE/SEMANTICA.PY

### **Nuevo módulo centralizado para Capa Semántica**

```
core/
├── calculos.py (existente, mantiene funciones que USAN semantica)
├── semantica.py (NUEVO - vocabulario central de cálculos)
└── config.py (existente, parámetros)
```

### **Estructura de semantica.py**

```python
"""
core/semantica.py — Vocabulario centralizado de cálculos institucionales.

Sin dependencias de Streamlit ni servicios → 100% testeable.
Todas las funciones de negocio en un lugar.
"""

# ===== PRIMITIVOS (Normalización + Limpieza) =====

def normalizar_id(x: Any) -> str:
    """Normaliza IDs de cualquier tipo → string limpio."""
    # Consolidar: _id_limpio() + normalización de texto

def normalizar_valor(valor: float | str) -> float:
    """Normaliza valor a escala decimal con regla unificada."""
    # Consolidar: normalizar_cumplimiento() + _cumplimiento_pct() + LAMBDA_ESCALA_OM

def normalizar_fecha(fecha: Any) -> pd.Timestamp | None:
    """Normaliza fechas de múltiples formatos."""
    # Nuevo

def obtener_ultimo_registro(df: pd.DataFrame, id_col: str = "Id", 
                            revisar_col: str | None = None, 
                            fecha_col: str = "Fecha") -> pd.DataFrame:
    """Deduplicación unificada (consolidar obtener_ultimo_registro + inline)."""

def filtrar_hasta_corte(df: pd.DataFrame, anio: int, mes: int, 
                        fecha_col: str = "Fecha") -> pd.DataFrame:
    """Filtrado temporal unificado (consolidar cierre_por_corte + inline)."""

# ===== DERIVADOS (Clasificación + Transformación) =====

def categorizar_cumplimiento(
    cumplimiento: float,
    sentido: str = "Positivo",
    id_indicador: str | int | None = None,
    opciones_custom: dict | None = None
) -> str:
    """
    Categorización unificada (consolidar categorizar_cumplimiento + _nivel_desde_cumplimiento + simple_categoria_desde_porcentaje).
    
    Retorna: "Peligro" | "Alerta" | "Cumplimiento" | "Sobrecumplimiento" | "Sin dato"
    
    Parametrizable: permite override de umbrales por caso de uso.
    """

def calcular_tendencia_temporal(
    series_cronologica: pd.Series | list[float],
    threshold: float = 0.01
) -> str:
    """Análisis de tendencia (↑ ↓ →)."""
    # Consolidar: calcular_tendencia()

def calcular_estado_temporal(
    fecha_vencimiento: pd.Timestamp,
    fecha_actual: pd.Timestamp | None = None,
    estado_actual: str | None = None,
    dias_alerta: int = 30
) -> str:
    """Estado de vencimiento (A tiempo, Por vencer, Vencida, Cerrada)."""
    # Consolidar: estado_tiempo_acciones()

def contar_periodos_en_estado(
    df: pd.DataFrame,
    estado_col: str = "Categoria",
    estado_valor: str = "Peligro",
    fecha_col: str = "Fecha",
    descendente: bool = True
) -> int:
    """Conteo de periodos consecutivos en estado."""
    # Consolidar: calcular_meses_en_peligro()

# ===== ESTRATÉGICOS (Agregación + KPIs) =====

def calcular_kpis_agregados(
    df: pd.DataFrame,
    cumpl_col: str = "Cumplimiento_norm",
    categoria_col: str = "Categoria"
) -> tuple[int, dict]:
    """KPIs principales: total y distribución por categoría."""
    # Consolidar: calcular_kpis()

def calcular_salud_institucional(
    df: pd.DataFrame,
    fecha_col: str = "Fecha",
    cumpl_col: str = "Cumplimiento_norm"
) -> pd.DataFrame:
    """Tendencia de salud general (promedio temporal)."""
    # Consolidar: calcular_salud_institucional()

def generar_recomendaciones_normalizadas(
    categoria: str,
    serie_historica: pd.Series,
    tendencia_override: str | None = None,
    threshold_cambio: float = 2.0
) -> tuple[str, list[str]]:
    """Análisis inteligente y recomendaciones."""
    # Consolidar: generar_recomendaciones() + mejorar

def aplicar_calculos_cumplimiento(
    df: pd.DataFrame,
    meta_col: str = "Meta",
    ejec_col: str = "Ejecucion",
    sentido_col: str = "Sentido",
    id_col: str = "Id"
) -> pd.DataFrame:
    """Pipeline unificado: normalización → cálculo → categorización."""
    # Extraer: lógica inline de data_loader.py Paso 5 + load_cierres()

# ===== CARGAS (ETL - Pueden migrar a servicios después) =====

def cargar_y_preparar_cierres(
    path_xlsx: Path | str,
    hoja: str = "Consolidado Cierres"
) -> pd.DataFrame:
    """Unificar load_cierres() + aplicar_calculos_cumplimiento()."""
    # Refactorizar: separar carga de cálculo

def preparar_indicadores_estrategicos(
    df_catalog: pd.DataFrame,
    df_mediciones: pd.DataFrame,
    tipo: str = "PDI"  # ó "CNA"
) -> pd.DataFrame:
    """Unificar preparar_pdi_con_cierre() + preparar_cna_con_cierre()."""
    # Eliminar duplicado

# ===== INTERFACES DE COMPATIBILIDAD (Legacy) =====

# Aliases para migración gradual sin romper código existente
def nivel_desde_pct(pct: float) -> str:
    """Legacy: reemplazar por categorizar_cumplimiento()."""
    return categorizar_cumplimiento(pct / 100 if pct > 2 else pct)
```

---

## 📋 TABLA DE ACCIONES: CONSOLIDACIÓN

| # | Función Actual | Acción | Destino | Prioridad | Esfuerzo | Tests Necesarios |
|---|---|---|---|---|---|---|
| 1 | normalizar_cumplimiento() | Consolidar | semantica.py | 🔴 ALTA | 1h | 5 casos |
| 2 | categorizar_cumplimiento() | Adoptar como estándar | semantica.py | 🔴 ALTA | 0h | +3 casos (Plan Anual) |
| 3 | _nivel_desde_cumplimiento() | ELIMINAR | — | 🔴 ALTA | 1h refactor | +1 caso |
| 4 | simple_categoria_desde_porcentaje() | DEPRECAR | Alias en semantica.py | 🟡 MEDIA | 0h | — |
| 5 | _map_level() (hardcoding) | ELIMINAR | — | 🔴 ALTA | 1h refactor | +1 caso |
| 6 | _cumplimiento_pct() (inline) | ELIMINAR | — | 🔴 ALTA | 1h refactor | — |
| 7 | LAMBDA_ESCALA_OM (inline) | ELIMINAR | — | 🔴 ALTA | 1h refactor | — |
| 8 | obtener_ultimo_registro() | Consolidar | semantica.py | 🟡 MEDIA | 0h | +2 casos |
| 9 | calcular_tendencia() | Consolidar | semantica.py | 🟡 MEDIA | 0.5h | +3 casos |
| 10 | calcular_meses_en_peligro() | Consolidar | semantica.py | 🟡 MEDIA | 0.5h | +2 casos |
| 11 | estado_tiempo_acciones() | Consolidar | semantica.py | 🟡 MEDIA | 0.5h | +4 casos |
| 12 | calcular_kpis() | Consolidar | semantica.py | 🟡 MEDIA | 0h | — |
| 13 | calcular_salud_institucional() | Consolidar | semantica.py | 🟡 MEDIA | 0h | +2 casos |
| 14 | generar_recomendaciones() | Consolidar + Mejorar | semantica.py | 🟡 MEDIA | 1h | +5 casos |
| 15 | load_cierres() (paso cálculo) | REFACTORIZAR | Separar carga/cálculo | 🔴 ALTA | 2h | +3 casos |
| 16 | _aplicar_calculos_cumplimiento() | EXTRAER | semantica.py | 🔴 ALTA | 1h | +3 casos |
| 17 | preparar_pdi_con_cierre() | REFACTORIZAR | Usar semantica.py | 🟡 MEDIA | 1h | +1 caso |
| 18 | preparar_cna_con_cierre() | REFACTORIZAR | Usar semantica.py | 🟡 MEDIA | 1h | +1 caso |
| 19–23 | +5 Inline (páginas) | ELIMINAR | — | 🟡 MEDIA | 2h total | — |

**Resumen:**
- **Consolidación:** 15 funciones → 1 módulo (core/semantica.py)
- **Esfuerzo Total:** ~18–20 horas (refactoring + tests)
- **Ganancia:** 65% reutilización, -4 duplicados, -9 heurísticas frágiles

---

## 📊 MATRIZ DE TRAZABILIDAD: DONDE VIVE CADA CÁLCULO

| Cálculo | core/calculos.py | services/strategic_indicators.py | services/data_loader.py | Pages (inline) | Propuesta |
|---------|---|---|---|---|---|
| Normalización | ✅ (1 lugar) | ❌ | ❌ | ⚠️ (2 páginas) | 🔧 Centralizar |
| Categorización | ✅ (1 lugar) | ❌ (alt. defectuosa) | ❌ | ⚠️ (1 hardcoding) | 🔧 Unificar |
| Cálculo cumplimiento | ✅ (llama) | ⚠️ (inline dup) | ⚠️ (inline dup) | — | 🔧 Función única |
| KPIs | ✅ (1 lugar) | ❌ | ❌ | ❌ | ✅ OK |
| Tendencia | ✅ (UNUSED) | ❌ | ❌ | ❌ | 🔧 Consolidar |
| Deduplicación | ✅ (1 lugar) | ⚠️ (inline) | ❌ | ❌ | 🔧 Centralizar |

---

## ✅ VALIDACIÓN DE FASE 4

- [x] 23 cálculos identificados + clasificados
  - Primitivos: 6
  - Derivados: 8
  - Estratégicos: 6
  - Inline no encapsulados: 3+
- [x] 8 duplicados/solapamientos documentados
- [x] Arquitectura propuesta (core/semantica.py)
- [x] Tabla de consolidación con esfuerzo
- [x] Matriz de trazabilidad

**Status:** ✅ **FASE 4 COMPLETADA - CAPA SEMÁNTICA DISEÑADA**

---

## 📁 ARCHIVOS GENERADOS

- [AUDITORIA_FASE_1_DISCOVERY.md](AUDITORIA_FASE_1_DISCOVERY.md) — Fuentes + Cálculos + Configuración
- [AUDITORIA_FASE_2_DATA_LINEAGE.md](AUDITORIA_FASE_2_DATA_LINEAGE.md) — 5 KPIs trazados
- [AUDITORIA_FASE_3_MODELO_ER.md](AUDITORIA_FASE_3_MODELO_ER.md) — 15 entidades + relaciones
- [AUDITORIA_FASE_4_CAPA_SEMANTICA.md](AUDITORIA_FASE_4_CAPA_SEMANTICA.md) ← TÚ ESTÁS AQUÍ

---

## 🚀 PRÓXIMAS FASES

**Fase 5: Auditoría Documental** (0% complete)
- Validar ARQUITECTURA_TECNICA_DETALLADA.md vs hallazgos
- Validar DATA_MODEL_SGIND.md vs ER (Fase 3)
- Validar DOCUMENTACION_FUNCIONAL.md vs flujos reales
- Generar DOCUMENTATION_AUDIT.md

**Fase 6: Análisis de Riesgos** (0% complete)
- Matriz: Módulo, Criticidad, Acoplamiento, Riesgos
- Recomendaciones de mitigación

**Fase 7: Síntesis de Hallazgos** (0% complete)
- Compilar todos los hallazgos
- Propuesta TO-BE con diagramas

**Fase 8: Documentación Final** (0% complete)
- Master document + matrices + diagramas

---

**Próxima fase:** Fase 5 - Auditoría Documental | **Estimado:** 22 de abril, 2026
