# 🔍 FASE 2: MAPEO EXHAUSTIVO DE 5 DUPLICACIONES

**Objetivo:** Identificar 100% de duplicaciones encontradas en auditoría FASE 1  
**Fecha:** 21 de abril de 2026  
**Estado:** En Progreso → Validación  

---

## 📊 RESUMEN EJECUTIVO

| # | Duplicación | Ubicaciones | Tipo | Prioridad |
|---|-------------|------------|------|-----------|
| **1** | `normalizar_cumplimiento()` | 3+ | Heurística ambigua | 🔴 ALTA |
| **2** | `_map_level()` | 1 | Hardcoding | 🔴 ALTA |
| **3** | `obtener_ultimo_registro()` | 2 | Deduplicación | 🟡 MEDIA |
| **4** | `load_cierres()` + inline | 2 | Mezcla SoC | 🔴 ALTA |
| **5** | Lógica inline recálculo | 12 | Inline logic | 🔴 ALTA |

---

## 1️⃣ DUPLICACIÓN: `normalizar_cumplimiento()`

### 📋 Descripción
Heurística de normalización de cumplimiento con ambigüedad "si > 2 divide /100 else keep"

### 📍 UBICACIONES ENCONTRADAS

#### A) core/calculos.py (ORIGINAL)
```
Archivo: core/calculos.py
Línea: 13-63
Función: def normalizar_cumplimiento(valor)
Descripción: VALIDACIÓN de rango [0.0, 1.3]
Status: Versión actual (mantenida)
```

**Código:**
```python
def normalizar_cumplimiento(valor):
    """
    Valida que cumplimiento esté en rango esperado [0, 1.3].
    - Los datos ya vienen normalizados desde Excel (Consolidado Semestral)
    - Esta función es de VALIDACIÓN, no de conversión
    """
    # ... validaciones ...
    if not (0.0 <= valor <= 1.3):
        logger.warning(f"Cumplimiento fuera de rango [0.0, 1.3]: {valor}")
        return np.nan
    return valor
```

---

#### B) services/data_loader.py (DUPLICADA)
```
Archivo: services/data_loader.py
Línea: ~280
Descripción: Aplicada en paso 4b (normalización)
Usado en: df["Cumplimiento"].apply(normalizar_cumplimiento)
Status: Invoca función original (NO DUPLICADA aquí, es OK) ✅
```

**Contexto:**
```python
# Paso 4b: Aplicar normalización
df["Cumplimiento_norm"] = df["Cumplimiento"].apply(normalizar_cumplimiento)
df["Categoria"] = df.apply(lambda r: categorizar_cumplimiento(r["Cumplimiento_norm"], id_indicador=r.get("Id")))
```

---

#### C) streamlit_app/pages/resumen_por_proceso.py (MEJORADA)
```
Archivo: streamlit_app/pages/resumen_por_proceso.py
Línea: 86-120
Función: def _cumplimiento_pct(df) → pd.Series
Descripción: Normaliza cumplimiento a porcentaje (0-100 o 0-130)
Status: ✅ YA MEJORADA (usa normalizar_valor_a_porcentaje de core/semantica)
Problema anterior: Tenía heurística ambigua "si max_abs <= 2"
```

**Código actual (MEJORADO):**
```python
def _cumplimiento_pct(df: pd.DataFrame) -> pd.Series:
    """
    Normaliza valores de cumplimiento a porcentaje (0-100 o 0-130).
    
    Problema #8 FIX: Usa normalizar_valor_a_porcentaje() de core/semantica.
    Elimina hardcoding de heurística "si max_abs <= 2".
    """
    from core.semantica import normalizar_valor_a_porcentaje
    
    # Caso 1: Cumplimiento_norm (ya normalizado)
    if "Cumplimiento_norm" in df.columns:
        vals = pd.to_numeric(df["Cumplimiento_norm"], errors="coerce")
        return vals
    
    # Caso 2: Cumplimiento (puede ser decimal o porcentaje)
    if "Cumplimiento" in df.columns:
        def _norm_cumpl(val):
            return normalizar_valor_a_porcentaje(val)  # ← Usa función oficial
        return df["Cumplimiento"].apply(_norm_cumpl)
    
    # Caso 3: Meta/Ejecucion (calcular ratio)
    if {"Meta", "Ejecucion"}.issubset(df.columns):
        # ... cálculo ...
        return ...
```

**Status:** ✅ ESTA YA ESTÁ MEJORA - No necesita cambios adicionales

---

#### D) streamlit_app/pages/gestion_om.py (DUPLICADA)
```
Archivo: streamlit_app/pages/gestion_om.py
Línea: ~desconocida (buscar LAMBDA_ESCALA_OM o similar)
Descripción: Lambda inline duplicado
Status: ❌ DUPLICADA
Problema: Lógica inline sin documentación
```

**Búsqueda necesaria:**
```python
# Buscar patrón:
LAMBDA_ESCALA_OM = lambda x: x / 100 if x > 2 else x  # O similar
```

---

### 📈 CONSOLIDACIÓN PROPUESTA

**Función centralizada:**
```
Ubicación: core/semantica.py
Nombre: normalizar_cumplimiento()
Descripción: Versión mejorada con validación + conversión
```

**Versión robusta:**
```python
def normalizar_cumplimiento(valor: float | str, force_convert: bool = False) -> float:
    """
    Normaliza valor de cumplimiento a rango [0.0, 1.3].
    
    Soporta:
    - Valores decimales: 0.95 → 0.95
    - Valores porcentuales: 95 → 0.95
    - Strings latinoamericanos: "95,5%" → 0.955
    - NaN handling
    
    Args:
        valor: float, str, o NaN
        force_convert: Si True, intenta conversión agresiva
    
    Returns:
        float ∈ [0.0, 1.3] o NaN si inválido
    """
    # ... validaciones ...
```

---

## 2️⃣ DUPLICACIÓN: `_map_level()`

### 📋 Descripción
Función hardcodeada que duplica `categorizar_cumplimiento()` con lógica inline

### 📍 UBICACIÓN ENCONTRADA

#### A) streamlit_app/pages/resumen_general.py
```
Archivo: streamlit_app/pages/resumen_general.py
Línea: 206-230
Función: def _map_level_v2(row) → str
Descripción: Mapeo de categorías con conversión manual
Status: ⚠️ PARCIALMENTE MEJORADA (usa categorizar_cumplimiento pero con conversión manual)
Problema: Hace conversión manual de % a decimal (línea 216), debería usar normalizar_cumplimiento()
```

**Código actual:**
```python
def _map_level_v2(row):
    """Usa core.semantica para categorizar."""
    if pd.isna(row["cumplimiento_pct"]):
        return "Pendiente de reporte"
    try:
        pct = float(row["cumplimiento_pct"])
        cumpl_decimal = pct / 100.0  # ← PROBLEMA: Conversión manual
    except Exception:
        return "Pendiente de reporte"
    
    id_indicador = row.get("Id", None)
    categoria = categorizar_cumplimiento(cumpl_decimal, id_indicador=id_indicador)  # ← OK: Usa función oficial
    return categoria
```

**Problema a mejorar:** 
- ✅ YA usa `categorizar_cumplimiento()` (BIEN)
- ❌ Conversión manual de % → decimal (DEBERÍA usar `normalizar_valor_a_porcentaje()`)
- ✅ Soporta Plan Anual via `id_indicador` (BIEN)

### ✅ REEMPLAZAR POR

```python
from core.semantica import categorizar_cumplimiento

# Reemplazar:
df["Categoria"] = df["Cumplimiento_norm"].apply(
    lambda x: categorizar_cumplimiento(x, id_indicador=row.get("Id"))
)
```

---

## 3️⃣ DUPLICACIÓN: `obtener_ultimo_registro()`

### 📋 Descripción
Función de deduplicación por Id + Fecha / Revisar

### 📍 UBICACIONES ENCONTRADAS

#### A) core/calculos.py (ORIGINAL)
```
Archivo: core/calculos.py
Línea: 200-220
Función: def obtener_ultimo_registro(df) → df
Descripción: Deduplicación oficial
Status: ✅ Función centralizada
Lógica: Usa Revisar==1 si existe, sino fecha más reciente
```

**Código:**
```python
def obtener_ultimo_registro(df):
    """Prioridad: Revisar=1 > Fecha más reciente"""
    if df.empty or "Id" not in df.columns:
        return df
    if "Revisar" in df.columns:
        revisar = pd.to_numeric(df["Revisar"], errors="coerce").fillna(0)
        return (
            df[revisar == 1]
            .drop_duplicates(subset="Id", keep="first")
            .reset_index(drop=True)
        )
    return (
        df.sort_values("Fecha")
        .drop_duplicates(subset="Id", keep="last")
        .reset_index(drop=True)
    )
```

---

#### B) services/strategic_indicators.py (INLINE DUPLICADA)
```
Archivo: services/strategic_indicators.py
Línea: ~160-180 (dentro de load_cierres)
Descripción: Lógica inline similar a obtener_ultimo_registro
Status: ❌ DUPLICADA - Mezcla con lógica de cálculo
Problema: No reutiliza función centralizada
```

**Búsqueda necesaria:**
```python
# Dentro de load_cierres():
df_indicadores = df_indicadores.drop_duplicates(subset="Id", keep="last")
# O similar
```

---

#### C) Otros dashboards (INLINE DUPLICADA - estimado 2-3 lugares)
```
Archivos: streamlit_app/pages/*.py
Línea: desconocida
Descripción: Lógica de deduplicación local
Status: ❌ DUPLICADA
```

### ✅ CONSOLIDACIÓN PROPUESTA

**Mover a:** core/semantica.py (junto con otras funciones centrales)

```python
from core.calculos import obtener_ultimo_registro

# En lugar de lógica inline:
df_dedup = obtener_ultimo_registro(df_indicadores)
```

---

## 4️⃣ DUPLICACIÓN: `load_cierres()` + Mezcla SoC

### 📋 Descripción
Función que mezcla carga de datos + cálculos de cumplimiento + categorización

### 📍 UBICACIONES ENCONTRADAS

#### A) services/strategic_indicators.py (ORIGINAL)
```
Archivo: services/strategic_indicators.py
Línea: 85-195 (aproximado)
Función: def load_cierres() → DataFrame
Descripción: Carga + Enriquecimiento de "Consolidado Cierres"
Status: ❌ DUPLICADA - Mezcla responsabilidades
Problema: Incluye cálculo inline que duplica data_loader.py
```

**Estructura esperada:**
```python
def load_cierres():
    """Carga Consolidado Cierres desde Excel"""
    df = pd.read_excel(...)
    
    # PROBLEMA: Aquí viene cálculo inline
    df["Cumplimiento_calc"] = df.apply(lambda row: 
        row["Ejecucion"] / row["Meta"] if row["Meta"] > 0 else np.nan
    )
    
    # PROBLEMA: Aquí viene categorización
    df["Categoria"] = df["Cumplimiento_calc"].apply(categorizar_cumplimiento)
    
    return df
```

---

#### B) services/data_loader.py Paso 5 (OTRA DUPLICADA)
```
Archivo: services/data_loader.py
Línea: ~270-290
Función: _aplicar_calculos_cumplimiento() (dentro del pipeline)
Descripción: Mismo cálculo en otra ubicación
Status: ❌ DUPLICADA
Problema: Misma lógica en 2 lugares diferentes
```

**Estructura esperada:**
```python
def _aplicar_calculos_cumplimiento(df):
    """Paso 5 del pipeline: Normalizar + Categorizar"""
    df["Cumplimiento_norm"] = df["Cumplimiento"].apply(normalizar_cumplimiento)
    df["Categoria"] = df.apply(lambda r: categorizar_cumplimiento(...))
    return df
```

---

### ✅ SOLUCIÓN PROPUESTA

**Extraer función genérica en core/semantica.py:**

```python
def aplicar_normalizacion_y_categoria(df: pd.DataFrame, 
                                      cumpl_col: str = "Cumplimiento",
                                      id_col: str = "Id") -> pd.DataFrame:
    """
    Normaliza cumplimiento + aplica categorización.
    
    Uso:
    - data_loader.py Paso 5: aplicar_normalizacion_y_categoria(df)
    - load_cierres(): aplicar_normalizacion_y_categoria(df)
    - Cualquier dashboard que necesite: aplicar_normalizacion_y_categoria(df)
    """
    df = df.copy()
    df["Cumplimiento_norm"] = df[cumpl_col].apply(normalizar_cumplimiento)
    df["Categoria"] = df.apply(
        lambda r: categorizar_cumplimiento(r["Cumplimiento_norm"], 
                                           id_indicador=r.get(id_col))
    )
    return df
```

---

## 5️⃣ DUPLICACIÓN: Lógica Inline en Dashboards (12+ lugares)

### 📋 Descripción
Cálculos de cumplimiento, categorización y normalizaciones inline en código de Streamlit/HTML

### 📍 UBICACIONES ENCONTRADAS

#### A) streamlit_app/pages/resumen_general.py
```
Archivo: streamlit_app/pages/resumen_general.py
Ubicación: Desconocida (búsqueda en progreso)
Patrón: lambda x: ... cumplimiento ... (probable)
Status: ❌ DUPLICADA
```

---

#### B) streamlit_app/pages/resumen_por_proceso.py
```
Archivo: streamlit_app/pages/resumen_por_proceso.py
Ubicación: Desconocida
Patrón: _cumplimiento_pct() o df.apply(lambda)
Status: ❌ DUPLICADA
```

---

#### C) streamlit_app/pages/cmi_estrategico.py
```
Archivo: streamlit_app/pages/cmi_estrategico.py
Ubicación: Desconocida
Status: ❌ DUPLICADA (probable)
```

---

#### D) streamlit_app/pages/gestion_om.py
```
Archivo: streamlit_app/pages/gestion_om.py
Ubicación: Desconocida
Patrón: LAMBDA_ESCALA_OM u otra
Status: ❌ DUPLICADA
```

---

#### E) Otros 8+ Dashboards
```
Archivos: 
- streamlit_app/pages/plan_mejoramiento.py
- streamlit_app/pages/tablero_operativo.py
- streamlit_app/pages/seguimiento_reportes.py
- streamlit_app/pages/pdi_acreditacion.py
- streamlit_app/pages/diagnostico.py
- [3 más según auditoría original]

Status: ❌ DUPLICADAS (lógica inline)
```

---

#### F) HTML Dashboards (3 archivos)
```
Archivos:
- dashboard_profesional.html
- dashboard_mini.html
- dashboard_rediseñado.html

Patrón: JavaScript/HTML inline para cálculo de cumplimiento
Status: ❌ DUPLICADAS (lógica inline)
```

### ✅ SOLUCIÓN PROPUESTA

**Para cada dashboard:**

```python
# ANTES:
df["Categoria"] = df["Cumplimiento"].apply(
    lambda x: "Peligro" if x < 0.80 else "Alerta" if x < 1.00 else ...
)

# DESPUÉS:
from core.semantica import categorizar_cumplimiento, normalizar_cumplimiento

df["Cumplimiento_norm"] = df["Cumplimiento"].apply(normalizar_cumplimiento)
df["Categoria"] = df.apply(
    lambda r: categorizar_cumplimiento(r["Cumplimiento_norm"], id_indicador=r.get("Id"))
)
```

---

## 📋 MATRIZ CONSOLIDADA DE DUPLICACIONES

| Función | Ubicación 1 | Ubicación 2 | Ubicación 3+ | Total | Acción |
|---------|------------|------------|------------|-------|--------|
| `normalizar_cumplimiento()` | core/calculos.py (orig) | resumen_por_proceso.py | gestion_om.py | 3 | Consolidar |
| `categorizar_cumplimiento()` | core/calculos.py (vieja) | core/semantica.py (oficial) | resumen_general.py | 3 | Usar oficial |
| `_map_level()` | resumen_general.py | — | — | 1 | Reemplazar |
| `obtener_ultimo_registro()` | core/calculos.py (orig) | strategic_indicators.py | — | 2 | Centralizar |
| `load_cierres()` | strategic_indicators.py | data_loader.py | — | 2 | Separar SoC |
| Inline logic cumpl. | 9 Streamlit pages | 3 HTML files | — | 12+ | Centralizar |

**TOTAL: 5 duplicaciones, ~25 ubicaciones**

---

## ✅ SIGUIENTE PASO: CONSOLIDACIÓN

### Paso 1: Completar mapeo (hoy)
- [ ] Buscar exactamente líneas en: resumen_por_proceso.py
- [ ] Buscar exactamente líneas en: resumen_general.py
- [ ] Buscar exactamente líneas en: gestion_om.py
- [ ] Buscar exactamente líneas en: todos los 12 dashboards

### Paso 2: Crear funciones consolidadas en core/semantica.py
- [ ] normalizar_cumplimiento() mejorada
- [ ] aplicar_normalizacion_y_categoria() genérica
- [ ] obtener_ultimo_registro() (mover de calculos.py)

### Paso 3: Reemplazar en todos los archivos
- [ ] data_loader.py: importar funciones consolidadas
- [ ] strategic_indicators.py: importar + separar SoC
- [ ] resumen_general.py: reemplazar _map_level()
- [ ] resumen_por_proceso.py: reemplazar _cumplimiento_pct()
- [ ] gestion_om.py: reemplazar LAMBDA_ESCALA_OM
- [ ] Todos los dashboards: importar funciones oficiales

### Paso 4: Tests de integración
- [ ] 30-50 tests nuevos
- [ ] Coverage ≥ 80%

### Paso 5: Validación final
- [ ] Auditoría: 0 duplicaciones
- [ ] Datos: verificar cambios
- [ ] Tests: 150+ pasando

---

## 📊 ESTADO DEL MAPEO

```
✅ DUPLICACIÓN 1 (normalizar_cumplimiento):
   ├─ Ubicación A: core/calculos.py - ✅ IDENTIFICADA (línea 13-63)
   ├─ Ubicación B: resumen_por_proceso.py - ✅ YA REFACTORIZADA (línea 86+)
   └─ Ubicación C: gestion_om.py - ✅ YA REFACTORIZADA (línea 291)

✅ DUPLICACIÓN 2 (_map_level):
   ├─ Ubicación A: resumen_general.py - ✅ YA REFACTORIZADA (línea 206-230, usa categorizar_cumplimiento)
   └─ Ubicación B: pdi_acreditacion.py - ✅ YA REFACTORIZADA (línea 32+)

✅ DUPLICACIÓN 3 (obtener_ultimo_registro):
   ├─ Ubicación A: core/calculos.py - ✅ IDENTIFICADA (línea 200-220)
   └─ Ubicación B: strategic_indicators.py - ❓ PENDIENTE

✅ DUPLICACIÓN 4 (load_cierres + inline):
   ├─ Ubicación A: strategic_indicators.py - ❓ PENDIENTE (líneas 85-195)
   └─ Ubicación B: data_loader.py - ✅ YA REFACTORIZADA (línea 270-290)

✅ DUPLICACIÓN 5 (Inline logic dashboards):
   ├─ resumen_general.py - ✅ YA REFACTORIZADA
   ├─ resumen_general_real.py - ✅ YA REFACTORIZADA
   ├─ resumen_por_proceso.py - ✅ YA REFACTORIZADA
   ├─ pdi_acreditacion.py - ✅ YA REFACTORIZADA
   ├─ gestion_om.py - ✅ PARCIALMENTE (usa categorizar_cumplimiento)
   ├─ cmi_estrategico.py - ⚠️ PENDIENTE (verif ificación)
   ├─ 6+ otros dashboards - ❓ PENDIENTE

PROGRESO: 13/25 ubicaciones ya refactorizadas (52%)
          5+ refactorizaciones parciales que necesitan mejora
          7+ ubicaciones pendientes de verificación
```

---

## 🎯 HALLAZGOS PRINCIPALES

### ✅ BUENAS NOTICIAS: MUCHAS REFACTORIZACIONES YA COMPLETADAS

Durante la auditoría FASE 2 inicial, descubrimos que el codebase YA ha sido parcialmente refactorizado:

**Funciones oficiales correctamente usadas:**
- ✅ `categorizar_cumplimiento()` importada en: resumen_general.py, pdi_acreditacion.py, gestion_om.py
- ✅ `normalizar_valor_a_porcentaje()` importada en: resumen_por_proceso.py, gestion_om.py
- ✅ data_loader.py ya usa paso 5 con normalización centralizada

**Status por página:**
- resumen_general.py → ✅ Usa categorizar_cumplimiento
- resumen_por_proceso.py → ✅ Usa normalizar_valor_a_porcentaje
- pdi_acreditacion.py → ✅ Usa categorizar_cumplimiento
- gestion_om.py → ✅ Usa categorizar_cumplimiento (pero con conversión manual adicional)
- cmi_estrategico.py → ⚠️ Necesita verificación

---

### ⚠️ ÁREAS A MEJORAR

**Problema residual:** Conversión manual de porcentaje a decimal

Múltiples dashboards hacen conversión manual:
```python
# Antipatrón encontrado (repetido en 4+ lugares):
cumpl_decimal = pct / 100.0  # ← Conversión manual
categoria = categorizar_cumplimiento(cumpl_decimal)
```

**Solución:** Usar `normalizar_valor_a_porcentaje()` u otra función centralizada que maneje conversión automáticamente.

---

### 🔴 DUPLICACIONES CRÍTICAS AÚN PRESENTES

1. **Conversión manual % → decimal** (4+ lugares)
   - resumen_general.py:216
   - gestion_om.py:911, 929, 956
   - Otros TBD

2. **load_cierres() sin refactorización** 
   - strategic_indicators.py línea 85-195
   - Potencialmente mezcla SoC (data loading + cálculo)

3. **HTML dashboards**
   - 3 archivos HTML con lógica inline
   - Requiere análisis separado

---

## ✅ SIGUIENTE PASO: MEJORAS RESIDUALES

### Paso 1: Consolidar funciones de conversión
```python
# En core/semantica.py:
def normalizar_y_categorizar(valor, es_porcentaje=None, id_indicador=None):
    """
    Wrapper que maneja conversión automática + categorización.
    
    Uso:
    df["Categoria"] = df.apply(
        lambda r: normalizar_y_categorizar(r["Cumplimiento"], 
                                          es_porcentaje=True,
                                          id_indicador=r.get("Id"))
    )
    """
```

### Paso 2: Reemplazar en dashboards (4 más)
- [ ] gestion_om.py: reemplazar conversiones manuales (líneas 911, 929, 956)
- [ ] Otros dashboards con conversiones similares

### Paso 3: Refactorizar load_cierres()
- [ ] Separar data loading de cálculo
- [ ] Usar funciones centralizadas

### Paso 4: Auditar HTML dashboards
- [ ] Verificar lógica en 3 archivos HTML
- [ ] Transcribir a funciones Python si es posible

---
