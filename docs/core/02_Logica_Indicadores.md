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
| **≥ 105%** | Sobrecumplimiento | `SOB` | `#1A3A5C` 🔵 |

#### 📅 Indicadores PLAN ANUAL (Régimen Especial PA)

| Rango | Categoría | Código | Color |
|-------|-----------|--------|-------|
| **< 80%** | Peligro | `PEL` | `#D32F2F` 🔴 |
| **80% - 94.99%** | Alerta | `ALE` | `#FBAF17` 🟡 |
| **≥ 95% (máx 100%)** | Cumplimiento | `CUM` | `#43A047` 🟢 |

**Características PA:**
- Cumplen desde 95% (vs 100% en regular)
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

## 6. Motor de Reglas (Opcional - Fase 2)

```python
from scripts.consolidation.core.rules_engine import RulesEngine, NivelAlerta

# Crear motor
motor = RulesEngine()

# Evaluar reglas sobre DataFrame
resultados = motor.evaluar_todo(df)

# Generar alertas formales
alertas = motor.generar_alertas(resultados)
```

### Reglas Implementadas

| ID | Nombre | Tipo | Prioridad |
|----|--------|------|-----------|
| semaforizacion | Semaforización | rango_cumplimiento | 1 |
| variacion_abrupta | Variación Abrupta | variacion | 2 |
| tendencia_descendente | Tendencia Descendente | tendencia | 3 |
| falta_actualizacion | Falta de Actualización | actualizacion | 2 |
| nulos_excesivos | Nulos Excesivos | nulos | 3 |

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

## 10. Referencias

- **Código fuente:** [`core/semantica.py`](../../core/semantica.py)
- **Configuración:** [`core/config.py`](../../core/config.py)
- **Tests:** [`tests/`](../../tests/)
