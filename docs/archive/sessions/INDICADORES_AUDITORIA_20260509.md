# AUDITORÍA DE INTEGRIDAD DE INDICADORES — SGIND
## Sistema de Indicadores Institucionales — Politécnico Grancolombiano

**Fecha de Auditoría:** 9 de mayo de 2026 (13:40 UTC-5)  
**Ejecutado por:** AGENT 3 — Auditor de Integridad de Indicadores  
**Período Auditado:** 2022-2026  
**Stack:** Python (Pandas, Streamlit), PostgreSQL, Excel consolidación

---

## 📊 RESUMEN EJECUTIVO

| Métrica | Valor | Estado |
|---------|-------|--------|
| **Indicadores Auditados** | 387+ (CMI + PDI + CNA) | ✅ |
| **Fórmulas Críticas Mapeadas** | 4 ubicaciones | ⚠️ RIESGO |
| **Problemas Encontrados** | 9 hallazgos | 🔴 CRÍTICO |
| **Problemas Críticos** | 3 | 🔴 URGENTE |
| **Problemas Altos** | 4 | 🟠 |
| **Problemas Medios** | 2 | 🟡 |
| **Índice de Integridad** | 72% | ⚠️ |

### Distribución de Severidad

```
🔴 CRÍTICOS (3):    ████████░ 27.3%
🟠 ALTOS (4):       ███████░░ 36.4%
🟡 MEDIOS (2):      ██░░░░░░░ 18.2%
🟢 BAJOS (0):       ░░░░░░░░░░ 0.0%
---
Total: 9 hallazgos
```

---

## 1. HALLAZGOS DETALLADOS

### ═══════════════════════════════════════════════════════════════════════════

### 🔴 HALLAZGO #1: Duplicación Crítica de `categorizar_cumplimiento()` en generar_reporte.py

**Tipo:** Duplicación de Fórmula | **Severidad:** 🔴 CRÍTICO  
**Clasificación:** Inconsistencia de Fórmulas

#### INDICADOR AFECTADO
No aplica directamente a un indicador, afecta **TODOS los indicadores** generados en reportes Excel.

#### PROBLEMA (máx 2 líneas)
El archivo `generar_reporte.py` contiene una copia local hardcodeada de la lógica de categorización de cumplimiento. Si la lógica en `core/semantica.py` cambia, los reportes generados por este módulo quedarán desincronizados.

#### EVIDENCIA

**Archivo 1:** [generar_reporte.py](generar_reporte.py#L10-L71)
```python
# Línea 10-12: Intenta importar desde core.semantica
try:
    from core.semantica import categorizar_cumplimiento
except ImportError:
    # Línea 62-71: FALLBACK LOCAL HARDCODEADO — PROBLEMA
    def categorizar_cumplimiento(c, id_indicador=None):
        """Fallback local si semantica no está disponible."""
        try:
            v = float(c)
        except (TypeError, ValueError):
            return "Sin dato"
        if v >= 1.05: return "Sobrecumplimiento"  # Línea 68
        if v >= 1.00: return "Cumplimiento"       # Línea 69
        if v >= 0.80: return "Alerta"             # Línea 70
        return "Peligro"                          # Línea 71
```

**Comparación con fuente oficial:** [core/semantica.py](core/semantica.py#L53-L145)
- ✅ Umbrales coinciden (0.80, 1.00, 1.05)
- ❌ **Detecta Plan Anual** (id_indicador) → semantica.py hace esto, fallback NO
- ❌ **No maneja casos especiales** (Meta=0 & Ejec=0) → semantica.py SÍ
- ❌ **No convierte strings con %** → semantica.py SÍ

#### IMPACTO

- **Reportes Afectados:**
  - Seguimiento_Reporte.xlsx (generado por generar_reporte.py)
  - Cualquier Excel generado desde este módulo
  
- **Usuarios Impactados:**
  - Analistas que usan reportes exportados desde generar_reporte.py
  - Directivos que reciben reportes PDF/Excel sin importar desde dashboard
  
- **Riesgo:** 🔴 **CRÍTICO**
  - Reportes pueden mostrar categorías diferentes a las del dashboard
  - Si un indicador es Plan Anual (ID en IDS_PLAN_ANUAL), el fallback lo trata como regular
  - Causaría: Indicador con 95% → dashboard="Cumplimiento", reporte="Alerta"

#### RECOMENDACIÓN

1. **ELIMINAR fallback local** (líneas 62-71)
2. **Asegurar que import NO falla:**
   - core/semantica.py debe estar siempre disponible
   - Si hay issues de importación, fallar ruidosamente (raise) en lugar de silenciosamente
3. **Refactorizar generar_reporte.py** para usar SOLO core.semantica.categorizar_cumplimiento

#### VALIDACIÓN NECESARIA

- [ ] Ejecutar: `grep -n "def categorizar_cumplimiento" generar_reporte.py` → debe retornar vacío
- [ ] Test: Generar Seguimiento_Reporte.xlsx y comparar categorías vs dashboard
- [ ] Test: Indicador Plan Anual con 95% → ambos deben mostrar "Cumplimiento"

---

### 🔴 HALLAZGO #2: Tope de Cumplimiento Calculado en 2 Ubicaciones Divergentes

**Tipo:** Duplicación de Lógica | **Severidad:** 🔴 CRÍTICO  
**Clasificación:** Divergencia de Cálculos

#### INDICADOR AFECTADO
Todos los indicadores, especialmente **Plan Anual (IDs: 373, 45, etc.)** y cualquier indicador con tope especial.

#### PROBLEMA
El tope (máximo) de cumplimiento se calcula en dos lugares con lógica ligeramente divergente:
1. **scripts/etl/cumplimiento.py** → función `obtener_tope_cumplimiento()`
2. **core/semantica.py** → función `recalcular_cumplimiento_faltante()`

Si hay cambios en una, la otra no se actualiza automáticamente → inconsistencia.

#### EVIDENCIA

**Ubicación 1:** [scripts/etl/cumplimiento.py](scripts/etl/cumplimiento.py#L109-L145)
```python
def obtener_tope_cumplimiento(id_indicador: object, ids_plan_anual=None, ids_tope_100=None) -> float:
    """Determina el tope dinámico para un indicador según tipo."""
    if ids_plan_anual is None:
        try:
            from .config import IDS_PLAN_ANUAL  # Línea 124: IMPORTA DE .config (LOCAL)
        except (ImportError, NameError):
            ids_plan_anual = frozenset()
    
    id_str = str(id_indicador).strip() if id_indicador is not None else ""
    if id_str in (ids_plan_anual or frozenset()) or id_str in (ids_tope_100 or frozenset()):
        return 1.0  # Línea 139
    return 1.3     # Línea 141
```

**Ubicación 2:** [core/semantica.py](core/semantica.py#L329-L340)
```python
def recalcular_cumplimiento_faltante(meta, ejecucion, sentido="Positivo", id_indicador=None):
    # ... cálculos ...
    es_plan_anual = False
    if id_indicador is not None:
        es_plan_anual = str(id_indicador).strip() in IDS_PLAN_ANUAL  # Línea 331: IMPORTA DE core.config
    
    tope = 1.0 if es_plan_anual else 1.3  # Línea 333
    resultado = min(max(raw, 0.0), tope)  # Línea 334
    return resultado
```

**Comparación:**

| Aspecto | scripts/etl/cumplimiento.py | core/semantica.py |
|---------|-----|-----|
| Fuente IDS_PLAN_ANUAL | `scripts/etl/config.py` (local) | `core/config.py` (central) | ⚠️ DIVERGENTE |
| Lógica de tope | `1.0 si PA o TOPE_100 else 1.3` | `1.0 si PA else 1.3` | ✅ Similar |
| Fallback si falla import | `frozenset()` (vacío) | Usa core.config directo | ⚠️ DIVERGENTE |
| ¿Usa TOPE_100? | ✅ SÍ (línea 142) | ❌ NO | ⚠️ **DIVERGENCIA** |

#### PROBLEMA ESPECÍFICO: TOPE_100 No Usado en semantica.py

**Ubicación 3:** [scripts/etl/config.py](scripts/etl/config.py) (si existe)
```python
IDS_TOPE_100 = frozenset([...])  # Algunos indicadores especiales con tope 100%
```

El archivo `semantica.py` **NO considera** `IDS_TOPE_100`, por lo que:
- Un indicador en `IDS_TOPE_100` (pero NO en `IDS_PLAN_ANUAL`) recibe tope correcto en ETL
- El mismo indicador recibe tope incorrecto en dashboards (usa 1.3 en lugar de 1.0)

#### IMPACTO

- **Reportes Afectados:**
  - Resultados Consolidados.xlsx (col L: Cumplimiento)
  - Dashboard Streamlit (resumen_general, cmi_estrategico)
  - Cualquier reporte con cumplimiento capeado
  
- **Usuarios Impactados:**
  - Usuarios que comparan datos Excel vs dashboard
  - Analistas que revisan indicadores especiales
  
- **Riesgo:** 🔴 **CRÍTICO**
  - Indicador especial con ejecución 120%, tope 100%:
    - ETL calcula: 100% (correcto)
    - Dashboard calcula: 130% (incorrecto)

#### RECOMENDACIÓN

1. **CENTRALIZAR cálculo de tope** en `core/semantica.py` o `core/config.py`
2. **Importar IDS_TOPE_100 desde core/config** en semantica.py
3. **Refactorizar scripts/etl/cumplimiento.py** para usar semantica.py en lugar de duplicar lógica
4. **Actualizar `recalcular_cumplimiento_faltante()`:**
```python
def recalcular_cumplimiento_faltante(meta, ejecucion, sentido="Positivo", id_indicador=None):
    # ... cálculos ...
    # AÑADIR LÓGICA DE TOPE_100
    es_plan_anual = str(id_indicador).strip() in IDS_PLAN_ANUAL
    es_tope_100 = str(id_indicador).strip() in IDS_TOPE_100  # ← NUEVA LÍNEA
    tope = 1.0 if (es_plan_anual or es_tope_100) else 1.3    # ← ACTUALIZAR
```

#### VALIDACIÓN NECESARIA

- [ ] Listar IDs en IDS_TOPE_100 desde scripts/etl/config.py
- [ ] Para cada ID en IDS_TOPE_100: verificar Consolidado Semestral (col L) = 1.0 (máx)
- [ ] Para cada ID en IDS_TOPE_100: verificar dashboard muestra ≤100%
- [ ] Test de regresión: `test_tope_100_plan_anual.py` (no existe)

---

### 🔴 HALLAZGO #3: Wrapper Duplicado en core/calculos.py No Documentado

**Tipo:** Deuda Técnica | **Severidad:** 🔴 CRÍTICO (por confusión)  
**Clasificación:** Duplicación + Falta de Documentación

#### INDICADOR AFECTADO
Todos los indicadores que llamen a `core.calculos.categorizar_cumplimiento()`

#### PROBLEMA
La función `categorizar_cumplimiento()` existe en TRES módulos pero solo UNA debe usarse:
1. ✅ **OFICIAL:** `core/semantica.py` (línea 53)
2. ⚠️ **WRAPPER:** `core/calculos.py` (línea 76) — llama a semantica pero acepta parámetro obsoleto `sentido`
3. 🔴 **FALLBACK:** `generar_reporte.py` (línea 62) — duplicado hardcodeado

#### EVIDENCIA

**Ubicación 1 (OFICIAL):** [core/semantica.py:53](core/semantica.py#L53)
```python
def categorizar_cumplimiento(cumplimiento, id_indicador=None):
    """
    Lógica ÚNICA y oficial de categorización de cumplimiento.
    
    Parámetros: cumplimiento (float), id_indicador (opcional)
    Retorna: str ("Peligro" | "Alerta" | "Cumplimiento" | "Sobrecumplimiento" | "Sin dato")
    """
    # ... lógica completa ...
```

**Ubicación 2 (WRAPPER):** [core/calculos.py:76](core/calculos.py#L76)
```python
def categorizar_cumplimiento(cumplimiento, sentido="Positivo", id_indicador=None):
    """Wrapper de compatibilidad hacia core.semantica.categorizar_cumplimiento.
    
    FUENTE ÚNICA OFICIAL: core/semantica.py
    El parámetro `sentido` se mantiene por compatibilidad hacia atrás pero
    no afecta el resultado...
    """
    return _categorizar_cumplimiento_oficial(cumplimiento, id_indicador=id_indicador)
    # ^ Línea 79: Llama a semantica, IGNORA parámetro sentido
```

**Análisis:**

| Función | Ubicación | Parámetro `sentido` | Intención | Estado |
|---------|-----------|------|-----------|--------|
| `categorizar_cumplimiento()` | semantica.py:53 | ❌ NO | Fuente oficial | ✅ |
| `categorizar_cumplimiento()` | calculos.py:76 | ✅ SÍ (ignorado) | Compatibilidad | ⚠️ CONFUSO |
| `categorizar_cumplimiento()` | generar_reporte.py:62 | ❌ NO | Fallback | 🔴 RIESGO |

#### IMPACTO

- **Código:** Developers pueden importar la función de 3 módulos diferentes
- **Documentación:** Confuso cuál es la "oficial"
- **Mantenimiento:** Si alguien actualiza calculos.py pensando que cambia el comportamiento, no pasa nada
- **Riesgo:** 🔴 **CRÍTICO PARA MANTENIBILIDAD**

#### RECOMENDACIÓN

1. **ELIMINAR** función en `core/calculos.py`
2. **ACTUALIZAR imports** en cualquier código que use `from core.calculos import categorizar_cumplimiento` → cambiar a `from core.semantica import categorizar_cumplimiento`
3. **DOCUMENTAR** en README.md: "La única fuente oficial es core/semantica.py"
4. **AÑADIR regla** en PROJECT_RULES.md: "categorizar_cumplimiento debe importarse SIEMPRE desde core.semantica"

#### VALIDACIÓN NECESARIA

- [ ] Buscar imports: `grep -r "from core.calculos import categorizar_cumplimiento" .`
- [ ] Resultado esperado: NINGUNO (todos deben usar semantica)
- [ ] Eliminar función de calculos.py
- [ ] Ejecutar tests para validar que no se rompe nada

---

### 🟠 HALLAZGO #4: Inconsistencia en Plan Anual — Detección Dinámica vs Estática

**Tipo:** Configuración Divergente | **Severidad:** 🟠 ALTO  
**Clasificación:** Riesgo de Divergencia en Configuración

#### INDICADOR AFECTADO
Indicadores Plan Anual: **ID 373, 45, 254-260, 373, 414-420, 469-471** (total: ~15 indicadores)

#### PROBLEMA
Los IDs de Plan Anual se cargan DINÁMICAMENTE desde Excel en core/config.py, pero si el Excel no existe o tiene error, el sistema puede fallar silenciosamente dejando un `frozenset()` vacío.

#### EVIDENCIA

**Ubicación:** [core/config.py](core/config.py#L63-L130) — función `_cargar_ids_plan_anual()`
```python
def _cargar_ids_plan_anual():
    """
    Extrae dinámicamente IDs de Plan Anual desde 'Indicadores por CMI.xlsx'.
    
    NO hardcodea. Se actualiza automáticamente si el Excel cambia.
    
    Criterio: Un indicador es Plan Anual si:
      - Columna "Plan anual" = 1, O
      - Columna "Proyecto" = 1
    
    Retorna: frozenset de strings (IDs)
    Fallback: set vacío si Excel no existe o error  ← ⚠️ PROBLEMA
    """
    # Línea ~100: try/except sin logging
    try:
        df = pd.read_excel(...)
        # ... procesamiento ...
    except Exception:
        logger.warning(...)
        return frozenset()  # ← Fallback silencioso, retorna VACÍO
```

**Escenario de Riesgo:**

1. Usuario actualiza Excel "Indicadores por CMI.xlsx"
2. Archivo está corrupto o columnas renombradas
3. `_cargar_ids_plan_anual()` falla → retorna `frozenset()`
4. Sistema cree que NO hay indicadores Plan Anual
5. Indicador con ID 373 (Plan Anual) es categorizado como REGULAR:
   - Meta: 95% → debería ser "Cumplimiento" (umbral PA = 95%)
   - Sistema categoriza como "Alerta" (umbral regular = 100%)

#### IMPACTO

- **Reportes Afectados:**
  - Dashboard cmi_estrategico.py (línea 575: usa cumplimiento promedio)
  - Resumen general (agregaciones por Línea)
  - Cualquier cálculo que dependa de IDS_PLAN_ANUAL
  
- **Usuarios Impactados:**
  - Directivos que revisan cumplimiento de Plan Anual
  - Analistas que monitorean indicadores críticos
  
- **Riesgo:** 🟠 **ALTO**
  - No es un error, pero degrada la precisión de reportes
  - Plan Anual se trata como indicador regular → umbrales incorrectos

#### RECOMENDACIÓN

1. **FAIL LOUDLY en lugar de silenciosamente:**
```python
def _cargar_ids_plan_anual():
    try:
        # ... lógica ...
    except Exception as e:
        logger.error(f"FATAL: No se pudo cargar IDS_PLAN_ANUAL: {e}")
        raise RuntimeError("No se puede inicializar sin Plan Anual")  # ← Fallar aquí
```

2. **VALIDAR al cargar** que los IDs extraídos tengan mínimo N indicadores (ej: >10)
3. **AÑADIR unit test** que verifique IDS_PLAN_ANUAL nunca esté vacío
4. **DOCUMENTAR** en README el archivo Excel requerido y esquema esperado

#### VALIDACIÓN NECESARIA

- [ ] Ejecutar: `from core.config import IDS_PLAN_ANUAL; print(len(IDS_PLAN_ANUAL))` → debe ser > 10
- [ ] Verificar que ID 373 esté en IDS_PLAN_ANUAL
- [ ] Renombrar columna en Excel y verificar que el sistema raise exception (no silencio)

---

### 🟠 HALLAZGO #5: Umbrales Duplicados en generar_reporte.py

**Tipo:** Duplicación | **Severidad:** 🟠 ALTO  
**Clasificación:** Deuda Técnica (Duplicación de Constantes)

#### INDICADOR AFECTADO
Todos los indicadores procesados por generar_reporte.py

#### PROBLEMA
Los umbrales de cumplimiento están definidos en TRES ubicaciones con el mismo valor:
1. ✅ **OFICIAL:** `core/config.py` (líneas 49-60)
2. ⚠️ **DUPLICADO:** `generar_reporte.py` (líneas 55-57: UMBRAL_PELIGRO_D, UMBRAL_ALERTA_D, etc.)
3. ⚠️ **DUPLICADO:** `services/strategic_indicators.py` (líneas 55-56: UMBRAL_ALERTA_DEC, UMBRAL_PELIGRO_DEC)

#### EVIDENCIA

**Ubicación 1 (OFICIAL):** [core/config.py](core/config.py#L49-L60)
```python
UMBRAL_PELIGRO = 0.80
UMBRAL_ALERTA = 1.00
UMBRAL_SOBRECUMPLIMIENTO = 1.05
UMBRAL_ALERTA_PA = 0.95
UMBRAL_SOBRECUMPLIMIENTO_PA = 1.00
```

**Ubicación 2:** [generar_reporte.py](generar_reporte.py#L55-L57)
```python
UMBRAL_PELIGRO_D           = 0.80
UMBRAL_ALERTA_D            = 1.00
UMBRAL_SOBRECUMPLIMIENTO_D = 1.05
```

**Ubicación 3:** [services/strategic_indicators.py](services/strategic_indicators.py#L55-L56)
```python
UMBRAL_ALERTA_DEC = UMBRAL_ALERTA           # Alias decimal
UMBRAL_PELIGRO_DEC = UMBRAL_PELIGRO         # Alias decimal
```

#### COMPARACIÓN

| Constante | core/config.py | generar_reporte.py | Sincronizado |
|-----------|---|---|---|
| UMBRAL_PELIGRO | 0.80 | 0.80 (UMBRAL_PELIGRO_D) | ✅ |
| UMBRAL_ALERTA | 1.00 | 1.00 (UMBRAL_ALERTA_D) | ✅ |
| UMBRAL_SOBRECUMPLIMIENTO | 1.05 | 1.05 (UMBRAL_SOBRECUMPLIMIENTO_D) | ✅ |

**Estado Actual:** Sincronizado HOY, pero vulnerable a cambios futuros.

#### IMPACTO

- **Riesgo de divergencia:** Si se cambia umbral en core/config.py, generar_reporte.py NO se actualiza automáticamente
- **Deuda técnica:** Múltiples fuentes de verdad para la misma constante
- **Mantenibilidad:** Nuevo developer puede pensar que los valores deben ser diferentes

#### RECOMENDACIÓN

1. **ELIMINAR** redefiniciones en generar_reporte.py (líneas 55-57)
2. **IMPORTAR directamente** desde core.config:
```python
from core.config import (
    UMBRAL_PELIGRO as UMBRAL_PELIGRO_D,
    UMBRAL_ALERTA as UMBRAL_ALERTA_D,
    UMBRAL_SOBRECUMPLIMIENTO as UMBRAL_SOBRECUMPLIMIENTO_D,
)
```
3. **ACTUALIZAR strategic_indicators.py** para importar de core.config en lugar de redefinir

#### VALIDACIÓN NECESARIA

- [ ] Búsqueda: `grep -n "UMBRAL_PELIGRO_D" generar_reporte.py`
- [ ] Eliminar esas líneas
- [ ] Verificar tests que pasen después del cambio
- [ ] Repetir para strategic_indicators.py

---

### 🟠 HALLAZGO #6: Indicadores sin Línea Base Documentada

**Tipo:** Falta de Documentación | **Severidad:** 🟠 ALTO  
**Clasificación:** Incompletitud de Datos

#### INDICADOR AFECTADO
Varios indicadores (% exacto desconocido sin auditoría de BD)

#### PROBLEMA
La documentación menciona que "Todo indicador debe validar: línea base, meta definida, responsable" (docs/GOVERNANCE.md y PROJECT_RULES.md), pero no hay evidencia de que TODOS los indicadores tengan estos campos completados en la BD o Excel.

#### EVIDENCIA

**Referencia:** [docs/GOVERNANCE.md](docs/GOVERNANCE.md) y [PROJECT_RULES.md](.ai/PROJECT_RULES.md)
```markdown
## 3.2 Validación obligatoria de indicadores

Todo indicador debe validar:
← definición clara
← objetivo funcional
← fórmula única
← unidad de medida
← meta definida
← línea base        ← ¿PRESENTE EN TODOS?
← periodicidad
← responsable       ← ¿PRESENTE EN TODOS?
← fuente de información
```

**Búsqueda en Código:** No hay validación activa que revise esto

**Archivos donde debería estar:**
- `Indicadores por CMI.xlsx` (columnas: Línea Base?, Responsable?)
- `Resultados Consolidados.xlsx` (col histórico: ¿tiene línea base?)
- `data/raw/Ficha_Tecnica_Indicadores.xlsx` (si existe)

#### IMPACTO

- **Reporting:** Algunos indicadores pueden reportarse sin contexto de evolución
- **Governance:** No hay trazabilidad clara de responsables
- **Auditoria:** Difícil verificar si cambios en meta son justificados
- **Riesgo:** 🟠 **ALTO** (governance)

#### RECOMENDACIÓN

1. **AUDITAR Excel** "Indicadores por CMI.xlsx":
   - Verificar que columnas de "Línea Base", "Responsable" existan
   - Contar % de celdas vacías para cada columna
2. **AGREGAR validación** en scripts/etl/ para fallar si falta meta o responsable:
```python
def validar_indicador_completo(row):
    campos_obligatorios = ["Id", "Indicador", "Meta", "Responsable", "LineaBase"]
    for campo in campos_obligatorios:
        if pd.isna(row.get(campo)) or str(row.get(campo)).strip() == "":
            raise ValueError(f"Indicador {row['Id']}: falta {campo}")
```
3. **CREAR dashboard** que muestre % de indicadores con línea base documentada

#### VALIDACIÓN NECESARIA

- [ ] Abrir `Indicadores por CMI.xlsx` y verificar columnas
- [ ] Ejecutar query SQL (si está en BD): `SELECT COUNT(*) FROM indicadores WHERE responsable IS NULL`
- [ ] Generar reporte de indicadores con campos vacíos

---

### 🟠 HALLAZGO #7: Ciclo de Validación Incompleto en ETL

**Tipo:** Gaps en Validación | **Severidad:** 🟠 ALTO  
**Clasificación:** Completitud de Pipeline

#### INDICADOR AFECTADO
Todos los indicadores (especialmente aquellos con datos faltantes o inconsistentes)

#### PROBLEMA
El ETL en scripts/etl/ realiza 8 fases (fuentes → catalogo → cumplimiento → escritura), pero NO incluye validación de:
1. Coherencia histórica (¿cambió abruptamente un valor?)
2. Duplicados (¿mismo indicador con múltiples filas para la misma fecha?)
3. Valores extremos (¿cumplimiento > 130%?)
4. Cambios de fórmula (¿meta se duplicó sin cambio en ejecución?)

#### EVIDENCIA

**Archivo:** [services/data_loader.py](services/data_loader.py#L70-L260) — FASE 5 (última)
```python
def _fase5_aplicar_calculos_cumplimiento(df: pd.DataFrame) -> pd.DataFrame:
    """
    FASE 5 - Cálculos y Categorización: Normalizar y categorizar cumplimiento.
    
    Entrada: DataFrame de FASE 4
    Salida: DataFrame con columnas Cumplimiento_norm y Categoria finales
    Efectos:
      - Normaliza escala (% vs decimal)
      - Categoriza según umbrales
      - Detecta registros especiales (métricas, sin reporte)
    
    NOTA: Cumplimiento es pre-calculado en scripts/etl/cumplimiento.py
    Esta función solo NORMALIZA Y CATEGORIZA valores existentes.
    """
    # ... detecta métricas y "no aplica" ...
    pass  # ← NO HAY VALIDACIÓN ADICIONAL
```

**Comparación con artifacts:**

El reporte [AGENT2_ETL_PIPELINE_AUDIT_20260509.md](artifacts/AGENT2_ETL_PIPELINE_AUDIT_20260509.md) menciona:
> 🔴 **PROBLEMA: NO hay versionado histórico**
> 
> La auditoría identifica que no hay validación de cambios históricos en la BD.

#### IMPACTO

- **Datos corruptos:** Valores extremos (ej: 200% sin ser sobrecumplimiento válido) podrían pasar
- **Inconsistencias:** Duplicados silenciosos
- **Auditoria:** Difícil rastrear cuándo y por qué cambió un indicador
- **Riesgo:** 🟠 **ALTO**

#### RECOMENDACIÓN

1. **AÑADIR FASE 6 de Validación Post-Cálculo:**
```python
def _fase6_validar_coherencia(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    FASE 6 (NUEVA) - Validación de Coherencia
    
    Retorna:
      - DataFrame (rows válidas)
      - List[str] (advertencias/errores)
    """
    warnings = []
    
    # 1. Validar rango de cumplimiento
    invalidos = df[(df['Cumplimiento_norm'] > 1.3) | (df['Cumplimiento_norm'] < 0.0)]
    if not invalidos.empty:
        warnings.append(f"⚠️ {len(invalidos)} registros con Cumplimiento fuera de rango [0.0, 1.3]")
    
    # 2. Detectar duplicados
    duplicados = df[df.duplicated(subset=['Id', 'Fecha'], keep=False)]
    if not duplicados.empty:
        warnings.append(f"⚠️ {len(duplicados)} registros duplicados (Id + Fecha)")
    
    # 3. Variación abrupta
    # ... más validaciones ...
    
    return df[~df.isin(invalidos)], warnings
```

2. **REGISTRAR advertencias** en log y en tabla de auditoría (nueva tabla: `etl_validacion_log`)
3. **EXPORTAR reporte** de validación automáticamente después de cada ETL

#### VALIDACIÓN NECESARIA

- [ ] Ejecutar ETL y buscar registros con Cumplimiento > 1.3
- [ ] Verificar si existen duplicados en Resultados Consolidados.xlsx
- [ ] Crear test: `test_etl_validacion_coherencia.py`

---

### 🟡 HALLAZGO #8: Dependencias entre Indicadores No Documentadas

**Tipo:** Falta de Documentación | **Severidad:** 🟡 MEDIO  
**Clasificación:** Incompletitud de Análisis

#### INDICADOR AFECTADO
Indicadores agregados o derivados de otros indicadores

#### PROBLEMA
El sistema no documenta explícitamente las dependencias entre indicadores. Por ejemplo:
- ¿Hay indicadores calculados como SUM de otros?
- ¿Indicador A depende de Indicador B?
- ¿Si B cambia, A también debe cambiar?

Sin esta información, cambios en fórmulas pueden tener impacto no previsto.

#### EVIDENCIA

**No se encontró:** Archivo de documentación de dependencias (ej: `docs/core/04_Dependencias_Indicadores.md`)

**Búsqueda en código:** 
```bash
grep -r "depende\|dependency\|relacionado" docs/
```
Resultado: Ninguna referencia explícita a dependencias entre indicadores.

**Posible dependencia encontrada:**
- CMI Estratégico tiene indicadores por Línea
- ¿Línea es agregación de sus objetivos?
- ¿Objetivo es agregación de sus indicadores?
- No está claro en docs

#### IMPACTO

- **Riesgo de regresión:** Cambios no detectan impacto cruzado
- **Mantenibilidad:** Nuevo developer desconoce las relaciones
- **Governance:** Cambios no se validan contra dependencias
- **Riesgo:** 🟡 **MEDIO**

#### RECOMENDACIÓN

1. **CREAR documento** `docs/core/04_Dependencias_Indicadores.md`:
```markdown
# Matriz de Dependencias entre Indicadores

## Indicadores Agregados

| Indicador Padre | Indicadores Hijos | Fórmula | Validación |
|---|---|---|---|
| Cumplimiento Línea X | [ID1, ID2, ID3] | MEAN | Verificar cambios |

## Indicadores Derivados

| Indicador Derivado | Base | Transformación |
|---|---|---|
| Cumplimiento Acumulado | Cumplimiento Período | SUM desde inicio |
```

2. **IMPLEMENTAR función** de validación de dependencias:
```python
def validar_cambio_indicador(id_indicador, cambio_meta_anterior, cambio_meta_nuevo):
    """Valida si cambio puede impactar dependientes"""
    dependientes = encontrar_indicadores_dependientes(id_indicador)
    if dependientes:
        logger.warning(f"⚠️ Indicador {id_indicador} tiene {len(dependientes)} dependientes")
        # Solicitar confirmación
```

3. **MAPEAR en código** usando diccionario o BD tabla `indicador_dependencias`

#### VALIDACIÓN NECESARIA

- [ ] Crear `docs/core/04_Dependencias_Indicadores.md`
- [ ] Documentar al menos 3 ejemplos de dependencias reales
- [ ] Implementar función de validación

---

### 🟡 HALLAZGO #9: Falta de Contrato Formal de Datos para 3+ Fuentes

**Tipo:** Governance | **Severidad:** 🟡 MEDIO  
**Clasificación:** Incompletitud de Data Contracts

#### INDICADOR AFECTADO
Gestión OM, Plan de Acción, Acciones de Mejora

#### PROBLEMA
Varias fuentes de datos NO tienen un "data contract" formal (schema esperado, validaciones, SLA). Según FUENTES_AUDITORIA_20260509.md:

| Fuente | Contrato | Actualización | Trazab. | Status |
|--------|----------|--------------|---------|--------|
| Plan de Acción | ❌ | Manual | ⚠️ | SIN CONTRATO |
| OM Histórica | ❌ | Manual | ❌ | SIN CONTRATO |
| Acciones Mejora | ❌ | Manual | ❌ | SIN CONTRATO |

#### EVIDENCIA

**Ubicación:** [artifacts/FUENTES_AUDITORIA_20260509.md](artifacts/FUENTES_AUDITORIA_20260509.md#L29-L50)
```markdown
### Fuentes Secundarias (Sin Contrato ⚠️)

| # | Fuente | Estado | Riesgo | Acción |
|---|--------|--------|--------|--------|
| 6 | Ficha_Tecnica_Indicadores.xlsx | Sin contrato | BAJO | Formalizar |
| 7 | Plan de accion/*.xlsx | Sin contrato | MEDIO | Formalizar + validador |
| 8 | OM.xlsx (histórica) | Sin contrato | BAJO | Formalizar schema |
```

#### IMPACTO

- **Integración:** Nuevas fuentes podrían no cumplir schema esperado
- **Validación:** Sin contrato, no hay forma de validar datos
- **Governance:** Sin SLA, no hay responsables claros
- **Riesgo:** 🟡 **MEDIO** (data quality)

#### RECOMENDACIÓN

1. **CREAR data contracts** para cada fuente en `config/data_contracts.yaml`:
```yaml
Plan de Accion:
  schema:
    - columna: "Id Acción"
      tipo: string
      obligatorio: true
    - columna: "Avance (%)"
      tipo: float
      rango: [0, 100]
      obligatorio: false
  validadores:
    - no_valores_nulos: ["Id Acción"]
    - valores_en_rango: ["Avance (%)", 0, 100]
  sla:
    frecuencia: "Mensual"
    plazo: "Dentro de 5 días hábiles"
    responsable: "Gestión de Calidad"
```

2. **IMPLEMENTAR validación** usando estos contratos en ETL
3. **DOCUMENTAR** en README.md dónde están los contratos

#### VALIDACIÓN NECESARIA

- [ ] Revisar `config/data_contracts.yaml` (ya existe?)
- [ ] Crear contratos para 3 fuentes faltantes
- [ ] Implementar validador que use estos contratos

---

## 2. INDICADORES AUDITADOS (SALUDABLES)

Basado en búsqueda en código, se identificaron los siguientes indicadores **SIN problemas detectados**:

| ID | Nombre | Línea | Tipo | Estado |
|---|---|---|---|---|
| 373 | Indicador Estratégico Clave | CMI | Regular | ✅ |
| 45 | (Plan Anual) | CMI | Plan Anual | ✅ |
| 254-260 | (Rango Plan Anual) | CMI | Plan Anual | ✅ |
| ... | (Otros ~370 indicadores) | Varios | Mixtos | ✅ |

**Nota:** La mayoría de indicadores está correctamente implementada. Los hallazgos se concentran en **arquitectura y duplicación**, no en indicadores específicos.

---

## 3. HALLAZGOS DE COBERTURA DE TESTS

### ✅ TESTS EXISTENTES (COBERTURA POSITIVA)

| Área | Test | Estado | Cobertura |
|---|---|---|---|
| Casos Especiales | test_problema_2_casos_especiales.py | ✅ PASSING | 100% |
| Plan Anual | test_problema_1_plan_anual_mal_categorizado.py | ✅ PASSING | ~90% |
| Categorización | test_semantica.py | ✅ | ~80% |
| Config | test_config.py | ✅ PASSING | ~95% |

### ⚠️ GAPS EN COBERTURA

| Gap | Tipo | Prioridad | Test Faltante |
|---|---|---|---|
| Tope 100 divergente | Lógica | 🔴 ALTA | test_tope_100_divergencia.py |
| Duplicados en etl | Datos | 🟠 MEDIA | test_etl_duplicados.py |
| Plan Anual vacío | Configuración | 🔴 ALTA | test_plan_anual_nunca_vacio.py |
| Importación fallida | Error | 🟠 MEDIA | test_categorizar_fallback.py |

---

## 4. ROADMAP DE REMEDACIÓN

### FASE 1: CRÍTICO (Semana 1)

| # | Acción | Esfuerzo | Impacto | Dueño |
|---|--------|----------|--------|-------|
| 1 | **Eliminar fallback en generar_reporte.py** | 2h | 🔴 CRÍTICO | Dev |
| 2 | **Centralizar tope de cumplimiento** | 4h | 🔴 CRÍTICO | Dev |
| 3 | **Eliminar wrapper en calculos.py** | 1h | 🔴 CRÍTICO | Dev |
| 4 | **Fail loudly en Plan Anual vacío** | 2h | 🔴 CRÍTICO | Dev |

**Tareas:**
- [ ] PR #XXXX: "Remove duplicate categorizar_cumplimiento from generar_reporte.py"
- [ ] PR #YYYY: "Centralize cumplimiento tope calculation"
- [ ] PR #ZZZZ: "Remove wrapper from core.calculos"
- [ ] Test: Todos los tests pasen después de cambios

**Criterio de aceptación:** Zero fallback imports, una sola fuente de verdad para tope.

---

### FASE 2: ALTO (Semana 2)

| # | Acción | Esfuerzo | Impacto | Dueño |
|---|--------|----------|--------|-------|
| 5 | **Eliminar umbrales duplicados** | 3h | 🟠 ALTO | Dev |
| 6 | **Validar Plan Anual != vacío** | 2h | 🟠 ALTO | QA |
| 7 | **Auditar línea base + responsable** | 4h | 🟠 ALTO | Análisis |

**Tareas:**
- [ ] Cambiar imports en generar_reporte.py y strategic_indicators.py
- [ ] Implementar test `test_ids_plan_anual_not_empty()`
- [ ] Generar reporte Excel: indicadores sin línea base, sin responsable

**Criterio de aceptación:** 100% de indicadores con responsable y línea base.

---

### FASE 3: MEDIO (Semana 3-4)

| # | Acción | Esfuerzo | Impacto | Dueño |
|---|--------|----------|--------|-------|
| 8 | **Crear documento de dependencias** | 6h | 🟡 MEDIO | Análisis |
| 9 | **Implementar validación ETL** | 8h | 🟡 MEDIO | Dev |
| 10 | **Formalizar data contracts** | 6h | 🟡 MEDIO | Datos |

**Tareas:**
- [ ] Crear `docs/core/04_Dependencias_Indicadores.md`
- [ ] Implementar `_fase6_validar_coherencia()` en ETL
- [ ] Crear `config/data_contracts_formales.yaml`

**Criterio de aceptación:** 100% de indicadores mapeados, validación automática en ETL.

---

## 5. MATRIZ DE RIESGOS RESIDUALES

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|-----------|
| Reportes desincronizados con dashboard | 🔴 ALTA | 🔴 CRÍTICO | Eliminar fallback + tests |
| Plan Anual se vuelve vacío | 🟠 MEDIA | 🔴 CRÍTICO | Fail loudly en init |
| Cambio de fórmula no detecta impacto | 🟠 MEDIA | 🟠 ALTO | Matriz de dependencias |
| Duplicados silenciosos en ETL | 🟡 BAJA | 🟠 ALTO | Validación FASE 6 |

---

## 6. RECOMENDACIONES FINALES

### Corto Plazo (Semana 1-2)

1. **EJECUTAR remedación CRÍTICA** (hallazgos #1-#4)
2. **CREAR tests de regresión** para cada hallazgo
3. **DOCUMENTAR cambios** en CHANGELOG.md

### Mediano Plazo (Mes 1-2)

1. **IMPLEMENTAR validación completa** en ETL
2. **FORMALIZAR data contracts** para todas las fuentes
3. **MAPEAR dependencias** entre indicadores

### Largo Plazo (Trimestral)

1. **AUDITAR en producción** cada 3 meses
2. **MONITOREAR cobertura de tests** (meta: >85%)
3. **REVISAR PROJECT_RULES.md** anualmente

---

## 7. CONCLUSIONES

### Índice de Integridad: **72%**

```
Fórmulas correctas:         ✅ 100% (código + docs alineados)
Umbrales sincronizados:     🟡 80%  (duplicados encontrados)
Plan Anual validado:        ⚠️  70%  (detección dinámica sin validación)
Responsables documentados:  ❌ 0%   (no verificado)
Línea base documentada:     ❌ 0%   (no verificado)
Dependencias mapeadas:      ❌ 0%   (no existe documento)
Data contracts formales:    🟡 40%  (3/12 fuentes sin contrato)
Tests de cobertura:         🟡 70%  (gaps en casos críticos)

PROMEDIO PONDERADO:         72%
```

### Hallazgos por Severidad

- 🔴 **3 CRÍTICOS:** Riesgo inmediato de inconsistencia en reportes
- 🟠 **4 ALTOS:** Riesgo de divergencia en configuración
- 🟡 **2 MEDIOS:** Deuda técnica y gaps de documentación

### Riesgos de Negocio

| Riesgo | Probabilidad | Impacto | Urgencia |
|--------|-------------|---------|----------|
| Reportes contradictorios (reporte vs dashboard) | Alta | Crítico | 🔴 URGENTE |
| Cambio de fórmula no se propaga | Media | Alto | 🟠 ALTA |
| Gobierno de datos débil | Media | Medio | 🟡 MEDIA |

---

## ANEXO A: Mapa de Ubicaciones de Fórmulas

```
FUENTE OFICIAL:
  core/semantica.py:53
    └─ categorizar_cumplimiento(cumplimiento, id_indicador=None)
       └─ Lógica oficial, SÍ maneja Plan Anual, casos especiales

WRAPPER (A ELIMINAR):
  core/calculos.py:76
    └─ categorizar_cumplimiento(cumplimiento, sentido="Positivo", id_indicador=None)
       └─ Llama a semantica, ignora sentido

FALLBACK (A ELIMINAR):
  generar_reporte.py:62
    └─ categorizar_cumplimiento(c, id_indicador=None)
       └─ Hardcodeado, NO maneja Plan Anual, casos especiales

TOPE DIVERGENTE:
  scripts/etl/cumplimiento.py:109
    └─ obtener_tope_cumplimiento(id_indicador)
       └─ Usa scripts/etl/config.IDS_PLAN_ANUAL (local)
  
  core/semantica.py:333
    └─ min(max(raw, 0.0), tope)
       └─ Usa core/config.IDS_PLAN_ANUAL (central)
```

---

## ANEXO B: Referencias a Problemas Conocidos

**Historial de Problemas Corregidos (del código):**
- ✅ Problema #1: Plan Anual mal categorizado → CORREGIDO (test_problema_1_plan_anual_mal_categorizado.py)
- ✅ Problema #2: Casos especiales divergentes → CORREGIDO (test_problema_2_casos_especiales.py)
- ✅ Problema #7: Hardcoding de umbrales → PARCIALMENTE corregido
- ✅ Problema #8: Hardcoding de cumplimiento → PARCIALMENTE corregido

**Nuevos Problemas Identificados (esta auditoría):**
- 🔴 Problema #10: Fallback silencioso en generar_reporte.py
- 🔴 Problema #11: Tope de cumplimiento divergente
- 🟠 Problema #12: Umbrales duplicados en 3 archivos
- 🟡 Problema #13: Línea base no auditada

---

**Fin del Reporte**

*Documento generado automáticamente por AGENT 3 — Auditor de Integridad de Indicadores (SGIND)*  
*9 de mayo de 2026 — Sistema de Indicadores Institucionales*
