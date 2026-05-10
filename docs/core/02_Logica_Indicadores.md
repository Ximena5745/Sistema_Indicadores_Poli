# 02 - LÓGICA DE CÁLCULO DE INDICADORES

**Documento:** 02_Logica_Indicadores.md  
**Versión:** 1.0  
**Fecha:** 22 de abril de 2026  
**Status:** ✅ Consolidado MDV

---

## 1. Cálculo de Cumplimiento

### 1.1 Fórmula Oficial

```python
# Indicadores POSITIVOS (ascendente)
cumplimiento = ejecución / meta

# Indicadores NEGATIVOS (descendente)
cumplimiento = meta / ejecución

# Casos especiales
Meta=0 AND Ejec=0: cumplimiento = 1.0 (100% - éxito)
Negativo AND Ejec=0: cumplimiento = 1.0 (100% - éxito)

# Tope máximo
cumplimiento = min(cumplimiento, 1.3)  # 130%
```

### 1.2 Categorización por Tipo de Indicador

#### 🟢 Indicadores REGULARES (Régimen General)

| Rango | Categoría | Código | Color |
|-------|-----------|--------|-------|
| **< 80%** | Peligro | `PEL` | `#D32F2F` 🔴 |
| **80% - 99.99%** | Alerta | `ALE` | `#FBAF17` 🟡 |
| **100% - 104.99%** | Cumplimiento | `CUM` | `#43A047` 🟢 |
| **≥ 105%** | Sobrecumplimiento | `SOB` | `#6699FF` 🔵 |

#### 📅 Indicadores PLAN ANUAL (Régimen Especial PA)

| Rango | Categoría | Código | Color |
|-------|-----------|--------|-------|
| **< 80%** | Peligro | `PEL` | `#D32F2F` 🔴 |
| **80% - < 95%** | Alerta | `ALE` | `#FBAF17` 🟡 |
| **≥ 95% (máx 100%)** | Cumplimiento | `CUM` | `#43A047` 🟢 |

**Características PA:**
- Cumplen desde 95% (vs 100% en regular)
- **Nota:** 95% es INCLUSIVO: ≥ 95% = Cumplimiento
- Tope máximo 100% (no sobrecumplimiento)
- Auto-detectados por ID desde Excel: `Indicadores por CMI.xlsx`

---

## 2. Umbrales Configurados

```python
# core/config.py
UMBRAL_PELIGRO = 0.80                      # Límite inferior Alerta
UMBRAL_ALERTA = 1.00                       # Límite inferior Cumplimiento
UMBRAL_SOBRECUMPLIMIENTO = 1.05            # Límite inferior Sobrecumplimiento
UMBRAL_ALERTA_PA = 0.95                    # Límite inferior Cumplimiento PA
UMBRAL_SOBRECUMPLIMIENTO_PA = 1.00        # Tope máximo PA
```

---

## 3. Concepto de "No Aplica"

**Definición:** Un indicador marca "No Aplica" cuando NO corresponde medirlo en un período específico (estacionalidad, fase del proyecto).

**NO es un error ni un dato faltante.**

### Detección:
1. El campo `analisis` contiene "no aplica" → `es_na = True`
2. `resultado = NaN` Y sin datos en variables/series → `es_na = True`

### Escritura en consolidado:
| Campo | Valor |
|-------|-------|
| Ejecución (K) | `None` (celda vacía) |
| Ejecución_Signo (O) | `"No Aplica"` |
| Cumplimiento (L) | `""` (fórmula) |
| Meta (J) | Se conserva si existe, `None` si no |

---

## 4. Construcción de Llaves (LLAVE)

La **LLAVE** es el identificador único de cada registro: `Id + Fecha`.

```
LLAVE = Id + "-" + AÑO + "-" + MES + "-" + DÍA
Ejemplo: "68-2024-06-30"
```

---

## 5. Tipos de Indicadores

| Tipo | Descripción | Cálculo |
|------|-------------|---------|
| **VARIABLES** | Indicadores con sub-componentes | Suma de variables |
| **SERIES** | Indicadores con múltiples períodos | Histórico acumulado |
| **DIRECTO** | Valor directo de fuente | Uso directo |
| **SIMBOLO** | Indicador simbólico (+/-) | Signo específico |

---

## 6. Motor de Reglas (Fase 2 - No Activo)

### Status Actual

| Componente | Estado | Ubicación |
|-----------|--------|-----------|
| **Código** | ✅ Implementado | `scripts/consolidation/core/rules_engine.py` |
| **Tests** | ❌ 0% coverage | `tests/test_rules_engine.py` (no existe) |
| **Activación** | 🟡 Pendiente | Estimado: Junio 2026 |
| **Integración** | 🟡 Parcial | Importable pero no usado en pipelines |

### Descripción

El **Motor de Reglas** es un sistema extensible para evaluar condiciones sobre indicadores y generar alertas automáticas. Fue diseñado en FASE 2 pero está pausado hasta Junio 2026 por:

1. **Requisitos No Met:** Necesita cobertura de tests ≥ 80%
2. **Prioridades:** FASE 1-3 de sincronización documental prioritarias
3. **Roadmap:** Activación programada post-auditoría AGENT 4

### API y Ejemplos

```python
from scripts.consolidation.core.rules_engine import RulesEngine, NivelAlerta

# ═══════════════════════════════════════════════════════════════════════════
# OPCIÓN 1: Uso Directo (Cuando se active en Junio 2026)
# ═══════════════════════════════════════════════════════════════════════════

# Crear motor con configuración por defecto
motor = RulesEngine()

# Evaluar todas las reglas sobre un DataFrame
resultados = motor.evaluar_todo(df_consolidado)

# Generar alertas formales
alertas = motor.generar_alertas(resultados)

# ═══════════════════════════════════════════════════════════════════════════
# OPCIÓN 2: Agregar Reglas Personalizadas (Fase 3+)
# ═══════════════════════════════════════════════════════════════════════════

from scripts.consolidation.core.rules_engine import Regla, TipoRegla

# Crear regla personalizada
regla_custom = Regla(
    id="mi_regla",
    nombre="Mi Regla Personalizada",
    tipo=TipoRegla.VARIACION,
    nivel_alerta=NivelAlerta.CRÍTICA,
    evaluador=lambda df: df[df['cumplimiento'] < 0.50]  # Detección custom
)

# Agregar al motor
motor.agregar_regla(regla_custom)

# Evaluar
resultados = motor.evaluar_todo(df)
```

### Reglas Estándar (Disponibles)

| ID | Nombre | Tipo | Descripción | Nivel |
|----|----|------|-------------|-------|
| `semaforizacion` | Semaforización | Cumplimiento | Detección automática de Peligro/Alerta/Cumplimiento | INFO |
| `variacion_abrupta` | Variación Abrupta | Variación | Cambio > ±25% mes a mes | CRÍTICA |
| `tendencia_descendente` | Tendencia Descendente | Tendencia | 3+ meses consecutivos con caída | ALTA |
| `falta_actualizacion` | Falta de Actualización | Actualización | Registro sin actualizar > 30 días | MEDIA |
| `nulos_excesivos` | Nulos Excesivos | Nulos | > 30% de registros sin valor | CRÍTICA |

### Timeline de Activación

**Fase 2a: Setup (Mayo 2026)**
- Crear suite de tests (`tests/test_rules_engine.py`)
- Alcanzar 80% coverage del módulo
- Documentar casos de uso

**Fase 2b: Integración (Junio 2026)**
- Conectar motor a `scripts/actualizar_consolidado.py`
- Agregar alertas a notificaciones
- Implementar exportación de alertas

**Fase 2c: Production (Julio 2026)**
- Monitoring de reglas en dashboard
- Tuning de umbrales según datos reales
- Soporte para reglas personalizadas

---

## 7. Gestión de Avance de OM

### Fuente de Datos
```
data/raw/Plan de accion/
├── PA_1.xlsx
├── PA_2.xlsx
└── ... (otros archivos .xlsx)
```

### Algoritmo
1. Leer todos los archivos Excel de `Plan de accion`
2. Concatenar en un único DataFrame
3. Eliminar registros sin Id de OM o sin avance
4. Agrupar por `Id Oportunidad de mejora`
5. Calcular promedio del campo `Avance (%)`
6. Retornar diccionario `{id_om: avance_promedio}`

```python
def _cargar_avance_om() -> dict:
    base_path = Path("data/raw/Plan de accion")
    dfs = []
    for f in base_path.glob("*.xlsx"):
        df = pd.read_excel(f, dtype=str, na_filter=False)
        df_subset = df[["Id Acción", "Avance (%)", "Id Oportunidad de mejora"]]
        dfs.append(df_subset)
    
    df_all = pd.concat(dfs, ignore_index=True)
    df_all["Avance (%)"] = pd.to_numeric(df_all["Avance (%)"], errors="coerce")
    resultado = df_all.groupby("Id Oportunidad de mejora")["Avance (%)"].mean().to_dict()
    
    return {str(k): round(v, 1) for k, v in resultado.items()}
```

---

## 9. Función Centralizada de Cálculo (Living Documentation + Data Contract)

### 9.1 Función: `normalizar_y_categorizar()`

**Ubicación:** `core/semantica.py:432`

**Propósito:** Wrapper que combina normalización de cumplimiento + categorización en una sola función. Centraliza la lógica de conversión automática y garantiza consistencia en formato de entrada/salida.

**Data Contract:**

```python
def normalizar_y_categorizar(
    valor: float | str,
    es_porcentaje: bool | None = None,
    id_indicador: str | int | None = None,
    sentido: str = "Positivo"
) -> str:
    """
    RETORNA: Categoría - "Peligro" | "Alerta" | "Cumplimiento" | "Sobrecumplimiento" | "Sin dato"
    
    PARÁMETROS:
    - valor: float, str, NaN - Valor de cumplimiento (puede ser porcentaje o decimal)
    - es_porcentaje: None (auto-detectar), True (0-130), False (0-1.3)
    - id_indicador: ID del indicador para auto-detectar Plan Anual
    - sentido: "Positivo" o "Negativo"
    """
    pass
```

**Valores de Retorno por Tipo de Indicador:**

| Tipo Indicador | Rango | Categoría Retornada |
|----------------|-------|---------------------|
| REGULAR | < 80% | Peligro |
| REGULAR | 80% - 99.99% | Alerta |
| REGULAR | 100% - 104.99% | Cumplimiento |
| REGULAR | ≥ 105% | Sobrecumplimiento |
| PLAN ANUAL | < 80% | Peligro |
| PLAN ANUAL | 80% - 94.99% | Alerta |
| PLAN ANUAL | ≥ 95% | Cumplimiento |

### 9.2 Función: `_render_strategy_card()`

**Ubicación:** `streamlit_app/pages/resumen_general.py:1136`

**Propósito:** Renderiza una tarjeta de estrategia con gráfico embebido de cumplimiento histórico por línea estratégica.

**Data Contract:**

```python
def _render_strategy_card(
    title: str,
    indicators: int,
    cumplimiento: float,
    color: str,
    icon: str,
    historico: pd.DataFrame | None = None
) -> None:
    """
    PARÁMETROS:
    - title: Título de la tarjeta (nombre de línea estratégica)
    - indicators: Cantidad de indicadores en la línea
    - cumplimiento: Porcentaje de cumplimiento actual (%)
    - color: Color principal de la tarjeta
    - icon: Icono representativo
    - historico: DataFrame con columnas 'Año' y 'Cumplimiento' (opcional)
    
    VISUALIZACIÓN:
    - Gráfico de línea con marcadores
    - Línea de meta (100%) punteada
    - Tooltip interactivo mostrando: Año, Cumplimiento %
    
    DATOS REQUERIDOS (historico):
    - Columna 'Año': int (años disponibles: 2022-2025)
    - Columna 'Cumplimiento': float (porcentaje 0-130)
    """
    pass
```

### 9.3 Cálculo de Cumplimiento por Línea

**Fórmula:**
```
Cumplimiento_Línea = promedio(cumplimiento_pct de todos los indicadores de la línea en cierre anual)
```

**Proceso:**
1. Filtrar datos por línea estratégica y mes de cierre (diciembre = 12)
2. Agrupar por año
3. Calcular promedio de `cumplimiento_pct`
4. Mostrar en tarjeta + gráfico histórico

---

### 9.4 Función: `obtener_color_categoria()`

**Ubicación:** [`core/semantica.py:168`](../../core/semantica.py#L168)

**Propósito:** Retorna el color hexadecimal asignado a una categoría de cumplimiento.

**Data Contract:**

```python
def obtener_color_categoria(categoria: str) -> str:
    """
    RETORNA: color hex (ej: "#D32F2F")
    
    PARÁMETROS:
    - categoria: str - Una de: "Peligro", "Alerta", "Cumplimiento", 
                       "Sobrecumplimiento", "Sin dato"
    """
```

**Valores de Retorno:**

| Categoría | Color Hex | Uso |
|-----------|-----------|-----|
| Peligro | #D32F2F | 🔴 Rojo |
| Alerta | #FBAF17 | 🟡 Naranja |
| Cumplimiento | #43A047 | 🟢 Verde |
| Sobrecumplimiento | #6699FF | 🔵 Azul |
| Sin dato | #BDBDBD | ⚪ Gris |

**Ejemplo:**
```python
from core.semantica import obtener_color_categoria

color = obtener_color_categoria("Cumplimiento")
print(color)  # "#43A047"
```

---

### 9.5 Función: `obtener_icono_categoria()`

**Ubicación:** [`core/semantica.py:179`](../../core/semantica.py#L179)

**Propósito:** Retorna el emoji/ícono asignado a una categoría de cumplimiento.

**Data Contract:**

```python
def obtener_icono_categoria(categoria: str) -> str:
    """
    RETORNA: emoji (ej: "🔴")
    
    PARÁMETROS:
    - categoria: str - Una de: "Peligro", "Alerta", "Cumplimiento", 
                       "Sobrecumplimiento", "Sin dato"
    """
```

**Valores de Retorno:**

| Categoría | Ícono |
|-----------|-------|
| Peligro | 🔴 |
| Alerta | 🟡 |
| Cumplimiento | 🟢 |
| Sobrecumplimiento | 🔵 |
| Sin dato | ⚪ |

**Ejemplo:**
```python
from core.semantica import obtener_icono_categoria

icono = obtener_icono_categoria("Alerta")
print(icono)  # "🟡"
```

---

### 9.6 Función: `recalcular_cumplimiento_faltante()`

**Ubicación:** [`core/semantica.py:187`](../../core/semantica.py#L187)

**Propósito:** Recalcula cumplimiento cuando falta por derivación de meta/ejecución.

**Data Contract:**

```python
def recalcular_cumplimiento_faltante(
    meta: float,
    ejecucion: float,
    sentido: str = "Positivo",
    id_indicador: str | int | None = None
) -> float:
    """
    RETORNA: cumplimiento normalizado (0.0 a 1.3)
    
    PARÁMETROS:
    - meta: float - Valor de meta
    - ejecucion: float - Valor de ejecución
    - sentido: str - "Positivo" o "Negativo"
    - id_indicador: str - Para detectar Plan Anual (opcional)
    """
```

**Lógica:**
- **Positivo:** cumplimiento = ejecución / meta
- **Negativo:** cumplimiento = meta / ejecución
- **Casos especiales:**
  - Si meta=0 AND ejecución=0 → 1.0 (100%)
  - Si negativo AND ejecución=0 → 1.0 (100%)
- **Tope:** mín(cumplimiento, 1.3) = máximo 130%

**Ejemplo:**
```python
from core.semantica import recalcular_cumplimiento_faltante

# Indicador positivo: 85/100 = 0.85 (85%)
c1 = recalcular_cumplimiento_faltante(meta=100, ejecucion=85, sentido="Positivo")
print(c1)  # 0.85

# Indicador negativo: 10/8 = 1.25 (125%)
c2 = recalcular_cumplimiento_faltante(meta=10, ejecucion=8, sentido="Negativo")
print(c2)  # 1.25
```

---

## 10. Referencias

- **Código fuente:** [`core/semantica.py`](../../core/semantica.py)
- **Configuración:** [`core/config.py`](../../core/config.py)
- **Tests:** [`tests/`](../../tests/)
