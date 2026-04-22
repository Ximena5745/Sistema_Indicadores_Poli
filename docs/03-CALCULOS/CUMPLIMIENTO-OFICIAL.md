# 📐 Cumplimiento Oficial: Fórmulas, Derivaciones y Ejemplos

**Documento:** CUMPLIMIENTO-OFICIAL.md  
**Versión:** 2.0  
**Fecha:** 21 de abril de 2026  
**Propósito:** Documentar fórmulas matemáticas officialesfor indicador cumplimiento  
**Audiencia:** Analistas, Desarrolladores, Auditores internos  
**Implementación:** [core/semantica.py](../../core/semantica.py) - Single Source of Truth

---

## Tabla de Contenidos

1. [Fórmula Principal de Cumplimiento](#fórmula-principal-de-cumplimiento)
2. [Derivaciones y Casos Especiales](#derivaciones-y-casos-especiales)
3. [Umbrales de Categorización](#umbrales-de-categorización)
4. [Ejemplos de Cálculo](#ejemplos-de-cálculo)
5. [Validaciones y Edge Cases](#validaciones-y-edge-cases)
6. [Referencia de Implementación](#referencia-de-implementación)

---

## Fórmula Principal de Cumplimiento

### Definición Base

$$\text{Cumplimiento} = \frac{\text{Ejecución}}{\text{Meta}} \times 100\%$$

**Donde:**
- **Ejecución:** Valor logrado en el período
- **Meta:** Valor objetivo para el período
- **Resultado:** Porcentaje de cumplimiento (escala 0–300%+)

### Convención Direccional: Sentido

La dirección positiva depende del indicador:

#### Sentido = POSITIVO (Ascendente) ↑

$$\text{Cumplimiento} = \frac{\text{Ejecución}}{\text{Meta}}$$

**Ejemplo:** "Tasa de Permanencia Estudiantil"
- Meta: 85% (queremos ≥ 85%)
- Ejecución: 78%
- Cumplimiento: 78 / 85 = 0.918 = **91.8%**
- Interpretación: Cumplieron 91.8% de la meta

---

#### Sentido = NEGATIVO (Descendente) ↓

$$\text{Cumplimiento} = \frac{\text{Meta}}{\text{Ejecución}}$$

**Ejemplo:** "Tasa de Deserción Estudiantil"
- Meta: 5% (queremos ≤ 5%, es decir, MENOS es mejor)
- Ejecución: 8%
- Cumplimiento: 5 / 8 = 0.625 = **62.5%**
- Interpretación: Cumplieron 62.5% de la meta (deserción mayor de lo esperado)

---

### Normalización de Escala

Los datos en Kawak pueden llegar en **dos escalas diferentes**:

1. **Escala Porcentual:** Valores entre 0–100 (i.e., 95, 78, 105)
2. **Escala Decimal:** Valores entre 0–1 (i.e., 0.95, 0.78, 1.05)

**Normalización automática:**

$$\text{Cumplimiento}_{\text{normalizado}} = \begin{cases}
\frac{\text{Cumplimiento}_{\text{raw}}}{100} & \text{si } \text{Cumplimiento}_{\text{raw}} > 2 \\
\text{Cumplimiento}_{\text{raw}} & \text{si } \text{Cumplimiento}_{\text{raw}} \leq 2
\end{cases}$$

**Implementación:** `core/semantica.py::normalizar_valor_a_porcentaje()`

```python
def normalizar_valor_a_porcentaje(valor, es_porcentaje=True):
    """
    Convierte valor a escala decimal normalizada [0, ∞).
    
    Args:
        valor: Número a normalizar (podría ser %, decimal, string)
        es_porcentaje: Hint sobre escala (auto-detecta si None)
    
    Returns:
        float: Cumplimiento en escala decimal (0.95 = 95%)
    
    Ejemplos:
        normalizar_valor_a_porcentaje(95) → 0.95      # % auto-detected
        normalizar_valor_a_porcentaje(0.95) → 0.95    # Decimal kept
        normalizar_valor_a_porcentaje('95%') → 0.95   # String parsed
        normalizar_valor_a_porcentaje(150) → 1.50     # Sobrecumplimiento
    """
```

---

## Derivaciones y Casos Especiales

### Caso 1: Indicadores con TOPE

**Definición:** Algunos indicadores tienen un límite máximo de cumplimiento (no puede sobrecumplesir más allá).

$$\text{Cumplimiento}_{\text{capped}} = \min(\text{Cumplimiento}_{\text{raw}}, \text{TOPE})$$

**Ejemplos de indicadores con tope:**
- **Plan Anual (373, 390, 414–418, 420, 469–471):** TOPE = 1.00 (100%)
  - No hay sobrecumplimiento en Plan Anual
  - Máximo logro: 100%
  
- **Indicadores institucionales especiales:** TOPE = 1.30 (130%)
  - Permiten sobrecumplimiento hasta 130%

**Implementación:**

```python
# core/config.py
IDS_PLAN_ANUAL = {373, 390, 414, 415, 416, 417, 418, 420, 469, 470, 471}
IDS_TOPE_100 = IDS_PLAN_ANUAL  # Plan Anual = tope 100%
TOPE_DEFAULT = 1.30  # Todos los demás = tope 130%

# core/semantica.py
def categorizar_cumplimiento(cumplimiento, id_indicador=None):
    if id_indicador in IDS_TOPE_100:
        cumplimiento = min(cumplimiento, 1.00)
    else:
        cumplimiento = min(cumplimiento, TOPE_DEFAULT)
```

---

### Caso 2: Registros sin Meta o Ejecución

**Situaciones:**
- Métrica auxiliar (no aplica cálculo)
- Período sin reporte
- Dato en revisión

**Tratamiento:**

$$\text{Cumplimiento}_{\text{NaN}} = \begin{cases}
\text{NaN} & \text{si Meta=0 AND Ejecución=0} \\
\text{NaN} & \text{si TipoRegistro=Metrica} \\
\text{NaN} & \text{si Cumplimiento explícitamente marcado como NaN}
\end{cases}$$

**Categorización:** "Sin Dato"

---

### Caso 3: Meta = 0 (Casos Especiales)

**Interpretación:** ¿Qué significa meta = 0?

| Escenario | Meta | Ejecución | Interpretación | Cumplimiento |
|-----------|------|-----------|---|---|
| Indicador de CERO | 0 | 0 | Meta era 0, lo logramos | 1.0 (100%) |
| Indicador de CERO | 0 | 5 | Meta era 0, superamos | Depende del sentido |
| Sin meta definida | NULL | 50 | No hay meta | NaN (Sin dato) |

**Lógica:**

```python
def calcular_cumplimiento_especial(meta, ejecucion, sentido):
    if meta == 0 and ejecucion == 0:
        return 1.0  # Ambos cero = meta cumplida
    elif meta == 0 and ejecucion > 0:
        if sentido == 'Negativo':
            return float('inf')  # Más es peor (no queremos nada)
        else:
            return float('inf')  # Ganancia inesperada
    elif meta is None or ejecucion is None:
        return float('nan')  # Sin dato
```

---

## Umbrales de Categorización

### Umbrales Estándar (Indicadores Regulares)

```python
# core/config.py
UMBRAL_PELIGRO = 0.80                  # < 80% → 🔴 PELIGRO
UMBRAL_ALERTA = 1.00                   # 80–99% → 🟡 ALERTA
UMBRAL_SOBRECUMPLIMIENTO = 1.05        # ≥ 105% → 🔵 SOBRECUMPLIMIENTO
# En medio [1.00, 1.05): 🟢 CUMPLIMIENTO
```

**Diagrama:**

```
Cumplimiento
    |
    ↓
  < 0.80    → 🔴 PELIGRO           (Crítico, acción requerida)
0.80–0.99   → 🟡 ALERTA            (Cerca de meta, atención)
1.00–1.04   → 🟢 CUMPLIMIENTO      (Meta alcanzada)
  ≥ 1.05    → 🔵 SOBRECUMPLIMIENTO (Superó expectativas)
   NaN      → ⚪ SIN DATO          (No aplica / No disponible)
```

---

### Umbrales Plan Anual (Especiales)

**Indicadores:** 373, 390, 414–420, 469–471

```python
# core/config.py
UMBRAL_ALERTA_PA = 0.95               # < 95% → 🟡 ALERTA
UMBRAL_SOBRECUMPLIMIENTO_PA = 1.00    # ≥ 100% → 🔵 SOBRECUMPLIMIENTO (pero capped)
# En medio [0.95, 1.00): 🟢 CUMPLIMIENTO
```

**Diferencias con estándar:**
1. Alerta comienza en 95% (vs 80% estándar)
   - Plan Anual = compromiso institucional mayor
   - Menos tolerancia a desviaciones
   
2. Máximo cumplimiento = 100% (sin sobrecumplimiento)
   - Presupuesto está limitado
   - No hay overexecution posible

**Diagrama Plan Anual:**

```
Cumplimiento (Plan Anual)
    |
    ↓
  < 0.95    → 🔴 PELIGRO            (Muy bajo para PA)
0.95–0.99   → 🟡 ALERTA             (Dentro rango, pero no 100%)
1.00        → 🟢 CUMPLIMIENTO       (Meta perfecta + tope)
  NaN       → ⚪ SIN DATO
```

**Detección automática:**

```python
# core/semantica.py
def categorizar_cumplimiento(cumplimiento, id_indicador=None):
    if pd.isna(cumplimiento):
        return CategoriaCumplimiento.SIN_DATO
    
    # Detectar Plan Anual
    es_plan_anual = id_indicador in IDS_PLAN_ANUAL
    
    if es_plan_anual:
        # Umbrales PA
        if cumplimiento < 0.95:
            return CategoriaCumplimiento.PELIGRO
        elif cumplimiento < 1.00:
            return CategoriaCumplimiento.CUMPLIMIENTO  # Categoría difere
        else:
            return CategoriaCumplimiento.CUMPLIMIENTO  # Tope en 100%
    else:
        # Umbrales estándar
        if cumplimiento < 0.80:
            return CategoriaCumplimiento.PELIGRO
        elif cumplimiento < 1.00:
            return CategoriaCumplimiento.ALERTA
        elif cumplimiento < 1.05:
            return CategoriaCumplimiento.CUMPLIMIENTO
        else:
            return CategoriaCumplimiento.SOBRECUMPLIMIENTO
```

---

## Ejemplos de Cálculo

### Ejemplo 1: Indicador Regular (Sentido Positivo)

**Indicador:** ID=245, "Permanencia Intersemestral"

| Campo | Valor |
|-------|-------|
| Sentido | Positivo ↑ |
| Meta | 85 |
| Ejecución | 78 |
| Plan Anual | NO |

**Cálculo paso-a-paso:**

$$\text{Cumplimiento}_{\text{raw}} = \frac{78}{85} = 0.9176$$

$$\text{Cumplimiento}_{\text{normalizado}} = 0.9176 \text{ (ya está en escala decimal)}$$

$$\text{Cumplimiento}_{\text{capped}} = \min(0.9176, 1.30) = 0.9176$$

**Categorización:**

- Cumplimiento = 0.9176 (91.76%)
- 0.80 < 0.9176 < 1.00
- **Categoría: 🟡 ALERTA** (Cerca pero no alcanzó meta)

**Interpretación:** El indicador de Permanencia apenas llegó al 91.76% de su meta de 85%. Está en riesgo (menos del 100%), requiere atención.

---

### Ejemplo 2: Indicador Plan Anual

**Indicador:** ID=373, "PDI - Eje 1"

| Campo | Valor |
|-------|-------|
| Sentido | Positivo ↑ |
| Meta | 100 |
| Ejecución | 94.7 |
| Plan Anual | ✅ SÍ |

**Cálculo:**

$$\text{Cumplimiento}_{\text{raw}} = \frac{94.7}{100} = 0.947$$

$$\text{Cumplimiento}_{\text{normalizado}} = 0.947$$

$$\text{Cumplimiento}_{\text{capped}} = \min(0.947, 1.00) = 0.947 \text{ (tope Plan Anual)}$$

**Categorización:**

- Cumplimiento = 0.947 (94.7%)
- Es Plan Anual: 0.95 > 0.947 (¡menos del umbral PA!)
- **Categoría: 🔴 PELIGRO** (Por debajo del 95% PA)

**Interpretación:** El PDI Eje 1 llegó a 94.7%, que es muy cercano a 95%, pero Plan Anual es compromisos institucionales. Por debajo del 95% entra en PELIGRO (aunque sería ALERTA en indicador regular).

---

### Ejemplo 3: Sobrecumplimiento

**Indicador:** ID=77, "Disponibilidad Servicios TI"

| Campo | Valor |
|-------|-------|
| Sentido | Positivo ↑ |
| Meta | 90 |
| Ejecución | 98.5 |
| Plan Anual | NO |

**Cálculo:**

$$\text{Cumplimiento}_{\text{raw}} = \frac{98.5}{90} = 1.0944$$

$$\text{Cumplimiento}_{\text{capped}} = \min(1.0944, 1.30) = 1.0944$$

**Categorización:**

- Cumplimiento = 1.0944 (109.44%)
- 1.05 < 1.0944
- **Categoría: 🔵 SOBRECUMPLIMIENTO** (Superó expectativas)

---

### Ejemplo 4: Indicador Negativo (Descendente)

**Indicador:** ID=276, "Relación Estudiante-Docente"

| Campo | Valor |
|-------|-------|
| Sentido | Negativo ↓ |
| Meta | 25 (estudiantes por docente) |
| Ejecución | 22 (logramos MENOS, lo cual es mejor) |
| Plan Anual | NO |

**Cálculo:**

$$\text{Cumplimiento}_{\text{raw}} = \frac{\text{Meta}}{\text{Ejecución}} = \frac{25}{22} = 1.136$$

$$\text{Cumplimiento}_{\text{capped}} = \min(1.136, 1.30) = 1.136$$

**Categorización:**

- Cumplimiento = 1.136 (113.6%)
- 1.05 < 1.136
- **Categoría: 🔵 SOBRECUMPLIMIENTO** (Superó expectativas)

**Interpretación:** La relación E:D fue mejor que la meta (22 vs meta 25). ¡Excelente logro!

---

### Ejemplo 5: Normalización de Escala (Dato en %)

**Dato recibido:** "Meta: 95%, Ejecución: 78%"

$$\text{Cumplimiento}_{\text{raw}} = \frac{78}{95} = 0.821$$

$$\text{¿Escala?} = \text{Detectar que 78 y 95 son porcentajes}$$

$$\text{Cumplimiento}_{\text{normalizado}} = 0.821 \text{ (ya en decimal)}$$

**Código:**

```python
from core.semantica import normalizar_y_categorizar

categoria = normalizar_y_categorizar(
    valor=None,
    meta=95,
    ejecucion=78,
    sentido='Positivo',
    id_indicador=245
)
# Retorna: CategoriaCumplimiento.ALERTA (82.1% < 100%)
```

---

## Validaciones y Edge Cases

### Validación 1: Coherencia Meta/Ejecución

```python
# Regla: Meta y Ejecución deben tener mismas unidades y escala
✅ Meta: 95, Ejecución: 78    → Valido
✅ Meta: 0.95, Ejecución: 0.78 → Valido
❌ Meta: 95, Ejecución: 0.78   → ERROR (escalas mixtas)
```

**Mitigación:** `normalizar_valor_a_porcentaje()` auto-detects y normaliza.

---

### Validación 2: Cumplimiento > 300%

```python
# Si Cumplimiento > 3.0 (300%), probable error de entrada
❌ Cumplimiento: 5.00 (500%) → Revisar entrada
✅ Cumplimiento: 1.50 (150%) → Valido (sobrecumplimiento alto)
```

---

### Validación 3: NaN Handling

```python
import pandas as pd

# Si Meta o Ejecución es NaN
if pd.isna(meta) or pd.isna(ejecucion):
    cumplimiento = float('nan')
    categoria = CategoriaCumplimiento.SIN_DATO

# Cumplimiento explícitamente NaN
if pd.isna(cumplimiento):
    categoria = CategoriaCumplimiento.SIN_DATO
```

---

## Referencia de Implementación

### Módulo Oficial

**Ubicación:** [`core/semantica.py`](../../core/semantica.py)

**Funciones principales:**

| Función | Entrada | Salida | Caso de Uso |
|---------|---------|--------|-----------|
| `normalizar_valor_a_porcentaje(valor)` | float/str | float [0,∞) | Convertir % ↔ decimal |
| `categorizar_cumplimiento(cumpl, id)` | float, int | CategoriaCumplimiento | Asignar categoría |
| `normalizar_y_categorizar(valor, meta, ejec, id)` | Raw inputs | CategoriaCumplimiento | Pipeline end-to-end |
| `obtener_icono_categoria(categoria)` | CategoriaCumplimiento | str | Dashboard icons |
| `obtener_color_categoria(categoria)` | CategoriaCumplimiento | str | Dashboard colors |

### Consumidores en Código

```python
# ✅ Importar de source centralizado
from core.semantica import categorizar_cumplimiento, normalizar_y_categorizar

# Streamlit pages
streamlit_app/pages/resumen_general.py (línea 206)
streamlit_app/pages/gestion_om.py (línea 8)
streamlit_app/pages/resumen_por_proceso.py (línea 86)

# Services
services/strategic_indicators.py (línea 13)
services/data_loader.py (línea 20)
```

### Suite de Pruebas

**Ubicación:** [`tests/test_semantica.py`](../../tests/test_semantica.py)

**Coverage:**
- 28 test cases
- Regular vs Plan Anual detection
- Boundary values (0.80, 1.00, 1.05)
- NaN / None handling
- String parsing
- Pandas integration

**Ejecución:**

```bash
pytest tests/test_semantica.py -v
```

---

**Última Actualización:** 21 de abril de 2026  
**Próxima Revisión:** 15 de mayo de 2026  
**Contacto:** biinstitucional@poli.edu.co
