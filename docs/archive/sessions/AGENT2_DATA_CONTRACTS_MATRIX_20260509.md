# CONTRATOS DE DATOS — MATRIZ DE VALIDACIONES RECOMENDADAS
## Sistema de Indicadores Institucionales (SGIND)

**Generado:** 9 de mayo de 2026  
**Estado actual:** ⚠️ Data contracts definidos en YAML pero NO ejecutados en pipeline  
**Recomendación:** Implementar validation gate en Layer 1 del ETL

---

## MATRIZ: Punto ETL × Validaciones Necesarias

### LEYENDA
- ✅ **Implementada** — Validación existe en código
- ⚠️ **Parcial** — Validación incompleta o dispersa
- ❌ **Falta** — Validación no implementada
- 🔴 **Crítica** — Debe bloquearse pipeline si falla
- 🟠 **Alta** — Debe loguear warning si falla
- 🟡 **Media** — Puede continuar, reportar anomalía

---

## 1. PUNTO: ENTRADA - Consolidado_API_Kawak.xlsx

**Responsabilidad:** scripts/consolidar_api.py + scripts/etl/fuentes.py

| Validación | Columna | Criterio | Estado | Criticidad | Ubicación Actual | Acción Recomendada |
|-----------|---------|----------|--------|-----------|-----------------|-------------------|
| **Presencia de columnas** | ID, fecha, resultado, ... | Todas las columnas requeridas existen | ❌ Falta | 🔴 Crítica | (ninguna) | Validar en Layer 1 antes de cargar |
| **Tipo: ID** | ID | String o numérico | ✅ Sí | 🔴 Crítica | consolidar_api.py:117 `_id_str()` | Mantener |
| **Tipo: fecha** | fecha | Datetime, formato YYYY-MM-DD | ⚠️ Parcial | 🔴 Crítica | etl/fuentes.py:45 `pd.to_datetime()` | Aceptar pero loguear conversiones fallidas |
| **Tipo: resultado** | resultado | Float o string numérico | ⚠️ Parcial | 🟠 Alta | etl/extraccion.py | Implementar validación explícita |
| **Requerida: ID** | ID | NOT NULL | ⚠️ Parcial | 🔴 Crítica | consolidar_api.py:123-124 | Agregar .dropna() |
| **Requerida: fecha** | fecha | NOT NULL | ✅ Sí | 🔴 Crítica | consolidar_api.py:126 | Mantener |
| **Cardinalidad: ID-fecha** | ID, fecha | 1 registro por combinación única | ❌ Falta | 🟠 Alta | (ninguna) | Validar en Layer 1 |
| **Patrón: ID** | ID | Regex: `^[0-9a-zA-Z\-]+$` | ❌ Falta | 🟡 Media | (ninguna) | Validar en Layer 1 |
| **Rango: resultado** | resultado | 0 ≤ result ≤ 500 (sensibilidad al dominio) | ❌ Falta | 🟡 Media | (ninguna) | Validar si patrón indicadores conocido |
| **Fecha mín/máx** | fecha | Entre 2022-01-01 y 2030-12-31 | ⚠️ Parcial | 🟡 Media | etl/config.py:8 `AÑO_CIERRE_ACTUAL` | Validar contra AÑOS válidos |
| **Sin duplicados** | ID, fecha | Deduplicación antes de procesar | ❌ Falta | 🟠 Alta | etl/escritura.py:dedup (post-proceso) | Validar en entrada, rechazar duplicados |
| **Valores permitidos** | (si aplica) | Comparar contra lista blanca | ⚠️ Parcial | 🟡 Media | etl/catalogo.py | Validar clasificación, proceso |

**Evaluación de Layer 1:**
```python
# RECOMENDADO: scripts/actualizar_consolidado.py línea 110

from services.data_validation import validate_dataset

def validar_consolidado_api_entrada(df: pd.DataFrame) -> None:
    """Gate de validación crítica antes de procesar"""
    
    # 1. Columnas requeridas
    COLS_REQUERIDAS = {"ID", "fecha", "resultado"}
    if not COLS_REQUERIDAS.issubset(df.columns):
        raise ValueError(f"Columnas faltantes: {COLS_REQUERIDAS - set(df.columns)}")
    
    # 2. Sin nulos en críticas
    nulls = df[["ID", "fecha"]].isnull().sum()
    if nulls.any():
        raise ValueError(f"Nulos encontrados: {nulls[nulls > 0].to_dict()}")
    
    # 3. Cardinalidad
    duplicados = df.groupby(["ID", "fecha"]).size()
    if (duplicados > 1).any():
        raise ValueError(f"{(duplicados > 1).sum()} combinaciones ID-fecha duplicadas")
    
    # 4. Rangos
    if (df["fecha"] < "2022-01-01").any() or (df["fecha"] > "2030-12-31").any():
        raise ValueError("Fechas fuera de rango [2022-01-01, 2030-12-31]")
    
    logger.info("✅ Consolidado_API_Kawak pasó validación de entrada")
```

---

## 2. PUNTO: TRANSFORMACIÓN - Extracción de Meta/Ejecución

**Responsabilidad:** scripts/etl/extraccion.py

| Validación | Campo | Criterio | Estado | Criticidad | Ubicación | Acción Recomendada |
|-----------|-------|----------|--------|-----------|-----------|-------------------|
| **Tipo: Meta** | Meta | Float ≥ 0 | ⚠️ Parcial | 🟠 Alta | etl/extraccion.py:150+ | Loguear conversiones fallidas |
| **Tipo: Ejecución** | Ejecucion | Float (sin límite superior) | ⚠️ Parcial | 🟠 Alta | etl/extraccion.py:150+ | Loguear conversiones fallidas |
| **Patrón: Meta** | Meta | No puede ser "N/A" o string | ⚠️ Parcial | 🟡 Media | consolidar_api.py:71-76 | Mejorar diagnóstico |
| **Patrón: Ejecucion** | resultado | Detectar "No Aplica" explícito | ✅ Sí | 🟠 Alta | etl/no_aplica.py | Mantener |
| **Lógica negocio: Ejecucion** | Ejecucion | Si Meta=0, Ejecucion debe ser 0 o nulo | ❌ Falta | 🟡 Media | (ninguna) | Validar en construcción registros |
| **Consistencia: Meta anterior** | Meta | No > 2x vs período anterior | ⚠️ Parcial | 🟡 Media | etl/validacion_historica.py:120 | Mejorar umbral a ±50% |

**Evaluación de Layer 2:**
```python
# scripts/etl/validacion_historica.py

def validar_meta_ejecucion(row, df_historico_id):
    """Valida coherencia de Meta/Ejecución vs histórico"""
    
    # 1. Tipo
    try:
        meta = float(row.Meta) if pd.notna(row.Meta) else None
        ejec = float(row.Ejecucion) if pd.notna(row.Ejecucion) else None
    except ValueError as e:
        logger.warning(f"  Id={row.Id}: No se pudo convertir Meta/Ejec a float: {e}")
        return "skip"
    
    # 2. Rango
    if meta is not None and meta < 0:
        logger.warning(f"  Id={row.Id}: Meta negativa ({meta})")
        return "warning"
    
    if ejec is not None and meta is not None and ejec > meta * 2:
        logger.warning(f"  Id={row.Id}: Ejecución > 2x Meta ({ejec} vs {meta})")
        return "warning"
    
    # 3. Coherencia
    if df_historico_id is not None and not df_historico_id.empty:
        meta_anterior = df_historico_id["Meta"].iloc[-1] if "Meta" in df_historico_id else None
        if meta is not None and meta_anterior is not None:
            if meta > meta_anterior * 1.5 or meta < meta_anterior * 0.5:
                logger.warning(f"  Id={row.Id}: Meta cambió >50% ({meta_anterior} → {meta})")
                return "warning"
    
    return "ok"
```

---

## 3. PUNTO: TRANSFORMACIÓN - Validación de Período

**Responsabilidad:** scripts/etl/periodos.py, scripts/etl/builders.py

| Validación | Campo | Criterio | Estado | Criticidad | Ubicación | Acción Recomendada |
|-----------|-------|----------|--------|-----------|-----------|-------------------|
| **Coherencia: Fecha ↔ Periodicidad** | Fecha, Periodicidad | Fecha debe ser último día del período | ✅ Sí | 🔴 Crítica | etl/periodos.py:_fecha_es_periodo_valido | Mantener, mejorar logging |
| **Formato: Período** | Período | Regex: `^[0-9]{4}-[12]$` (YYYY-S) | ⚠️ Parcial | 🟡 Media | etl/periodos.py | Validar explícitamente |
| **Rango: Año período** | Período | Año ∈ [2022, 2030] | ✅ Sí | 🟡 Media | etl/config.py | Mantener |
| **Validación: Semestre** | Período | Si S=1 → mes ∈ [1-6], si S=2 → mes ∈ [7-12] | ✅ Sí | 🟠 Alta | etl/periodos.py | Mantener |
| **Requerida: Período** | Período | NOT NULL (calculado desde Fecha si falta) | ✅ Sí | 🔴 Crítica | services/data_loader.py:_fase4 | Mantener |

**Evaluación de Layer 2:**
```python
# scripts/etl/periodos.py

def _fecha_es_periodo_valido_mejorado(fecha_ts, periodicidad, loguear=True) -> bool:
    """Valida que fecha coincida con periodicidad + loguea desvíos"""
    
    try:
        fecha_ts = pd.to_datetime(fecha_ts)
    except:
        if loguear:
            logger.warning(f"  Fecha inválida: {fecha_ts}")
        return False
    
    periodicidad = str(periodicidad).strip().lower()
    
    # Definir últimos días esperados
    periodos_validos = {
        "mensual": lambda f: f == ultimo_dia_mes(f.year, f.month),
        "bimestral": lambda f: (f.month % 2 == 0) and (f == ultimo_dia_mes(f.year, f.month)),
        "trimestral": lambda f: (f.month % 3 == 0) and (f == ultimo_dia_mes(f.year, f.month)),
        "semestral": lambda f: f.month in [6, 12] and (f == ultimo_dia_mes(f.year, f.month)),
        "anual": lambda f: f.month == 12 and f.day == 31,
    }
    
    es_valido = periodos_validos[periodicidad](fecha_ts)
    
    if not es_valido and loguear:
        logger.warning(f"  Fecha {fecha_ts.date()} no es último día de período {periodicidad}")
    
    return es_valido
```

---

## 4. PUNTO: TRANSFORMACIÓN - Cambios Retroactivos

**Responsabilidad:** scripts/etl/validacion_historica.py

| Validación | Campo | Criterio | Estado | Criticidad | Ubicación | Acción Recomendada |
|-----------|-------|----------|--------|-----------|-----------|-------------------|
| **Cambio de Sentido** | Sentido | Retroactivo Positivo ↔ Negativo = ERROR | ✅ Sí | 🔴 Crítica | etl/validacion_historica.py:80 | Mantener, BLOQUEAR en Layer 1 |
| **Caída > 50% Meta** | Meta | vs período anterior | ✅ Sí | 🟠 Alta | etl/validacion_historica.py:120 | Mantener como WARNING |
| **Caída > 80% Ejecución** | Ejecucion | vs promedio últimos 3 períodos | ✅ Sí | 🟠 Alta | etl/validacion_historica.py:140 | Mantener como WARNING |
| **Cambio clasificación** | Clasificacion | Estratégico ↔ Operativo | ❌ Falta | 🟡 Media | (ninguna) | Implementar WARNING |

**Evaluación de Layer 2:**
```python
# Ya implementado en scripts/etl/validacion_historica.py
# Mantener y EXPONER alertas en logs de pipeline
```

---

## 5. PUNTO: CARGA - Consolidado Semestral

**Responsabilidad:** scripts/etl/escritura.py, scripts/etl/builders.py

| Validación | Columna | Criterio | Estado | Criticidad | Ubicación | Acción Recomendada |
|-----------|---------|----------|--------|-----------|-----------|-------------------|
| **Integridad referencial: Id** | Id | ∀ Id ∈ Consolidado → Id ∈ Catálogo | ❌ Falta | 🔴 Crítica | (ninguna) | Validar antes de escribir LAYER 3 |
| **Integridad referencial: Proceso** | Proceso | ∀ Proceso en Consolidado → Proceso válido | ❌ Falta | 🔴 Crítica | (ninguna) | Validar antes de escribir LAYER 3 |
| **Requeridas: Anio, Fecha, Id, Indicador, Periodo, Proceso** | — | Sin nulos en estos campos | ⚠️ Parcial | 🔴 Crítica | etl/builders.py | Validar pre-escritura en LAYER 3 |
| **Tipo: Cumplimiento** | Cumplimiento | Float ∈ [0.0, 1.3] | ✅ Sí | 🔴 Crítica | core/config.py:RANGO_CUMPLIMIENTO | Mantener |
| **Cardinalidad: Id-Periodo** | Id, Periodo | 1 registro por combinación única | ⚠️ Parcial | 🟠 Alta | etl/escritura.py:deduplicar_sheet | Validar pre-escritura + loguear dedup |
| **Coherencia: Fecha ↔ Periodo ↔ Año** | Fecha, Periodo, Anio | Fecha debe derivar de Período calculado | ⚠️ Parcial | 🟠 Alta | services/data_loader.py:_fase4 | Mantener |
| **Rango: Meta/Ejecucion** | Meta, Ejecucion | ≥ 0 (excepto "No Aplica") | ⚠️ Parcial | 🟡 Media | etl/builders.py | Validar pre-escritura |

**Evaluación de Layer 3:**
```python
# RECOMENDADO: Nueva función antes de escribir Excel

def validar_consolidado_preescritura(
    df_hist: pd.DataFrame, 
    df_sem: pd.DataFrame, 
    df_cierres: pd.DataFrame,
    df_cat: pd.DataFrame
) -> None:
    """Valida integridad referencial antes de escribir Excel"""
    
    # 1. Integridad referencial: Id → Catálogo
    ids_consolidado = set(pd.concat([df_hist, df_sem, df_cierres])["Id"].unique())
    ids_catalogo = set(df_cat["Id"].unique())
    ids_huerfanos = ids_consolidado - ids_catalogo
    if ids_huerfanos:
        logger.error(f"❌ {len(ids_huerfanos)} IDs sin entrada en Catálogo: {ids_huerfanos}")
        raise ValueError("Integridad referencial fallida: Id huérfanos en consolidado")
    
    # 2. Requeridas
    COLS_REQUERIDAS_SEM = {"Anio", "Fecha", "Id", "Indicador", "Periodo", "Proceso"}
    for col in COLS_REQUERIDAS_SEM:
        nulos = df_sem[col].isnull().sum()
        if nulos > 0:
            logger.error(f"❌ {nulos} nulos en Consolidado Semestral.{col} (requerida)")
            raise ValueError(f"Columna requerida {col} tiene nulos")
    
    # 3. Cardinalidad
    duplicados = df_sem.groupby(["Id", "Periodo"]).size()
    if (duplicados > 1).any():
        logger.warning(f"⚠️ {(duplicados > 1).sum()} combinaciones Id-Periodo duplicadas (se deduplicarán)")
    
    # 4. Rango cumplimiento
    fuera_rango = (df_sem["Cumplimiento"] < 0) | (df_sem["Cumplimiento"] > 1.3)
    if fuera_rango.any():
        logger.error(f"❌ {fuera_rango.sum()} valores de Cumplimiento fuera de [0.0, 1.3]")
        raise ValueError("Cumplimiento fuera de rango permitido")
    
    logger.info("✅ Consolidados pasaron validación pre-escritura")
```

---

## 6. RESUMEN DE BRECHAS

### Implementadas (✅)
- Normalización de IDs
- Conversión de fechas
- Detección de "No Aplica"
- Validación de coherencia histórica
- Deduplicación (post-proceso)
- Cálculos de cumplimiento

### Parcialmente Implementadas (⚠️)
- Validación de tipos (dispersa)
- Rango de Meta/Ejecución (no explícita)
- Cardinalidad (solo post-dedup)
- Validación de Período (no loguea desvíos)

### No Implementadas (❌) — CRÍTICAS
- Gate de validación en ENTRADA
- Integridad referencial (Id ↔ Catálogo)
- Patrón regex para IDs
- Validación de columnas requeridas
- Gate de validación pre-ESCRITURA
- Notificación de anomalías

---

## 7. IMPLEMENTACIÓN RECOMENDADA

### Fase 1: Gate de Entrada (LAYER 1)
**Archivo:** `scripts/actualizar_consolidado.py` línea 110

```python
# Después de cargar_fuente_consolidada()
logger.info("2. Validando contrato de entrada…")
validate_entrada_consolidado_api(df_api)
```

### Fase 2: Gate de Transformación (LAYER 2)
**Archivos:** `scripts/etl/validacion_historica.py` + nuevas validaciones

```python
# En builders.py, cada construcción de registro
for row in df.itertuples():
    estado = validar_meta_ejecucion(row, df_hist_id)
    if estado == "skip":
        skipped += 1
        logger.warning(f"  [SKIP] Id={row.Id}: {razon}")
        continue
```

### Fase 3: Gate de Salida (LAYER 3)
**Archivo:** `scripts/etl/escritura.py` línea 100

```python
# Antes de escribir Excel
logger.info("7. Validando consolidados pre-escritura…")
validar_consolidado_preescritura(df_hist, df_sem, df_cierres, df_cat)
logger.info("   ✅ Integridad referencial OK")
```

---

**Fin de Matriz de Validaciones**
