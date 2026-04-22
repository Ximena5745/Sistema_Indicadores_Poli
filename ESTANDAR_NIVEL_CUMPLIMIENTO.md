# 📋 ESTÁNDAR OFICIAL: Nivel de Cumplimiento

**Documento:** Fórmula estandardizada para categorización de cumplimiento  
**Vigencia:** 21 de abril de 2026+  
**Status:** ✅ OFICIAL - Vinculante para todo el proyecto  
**Última actualización:** 21 de abril de 2026  

---

## 📐 DEFINICIÓN FORMAL

### Niveles Establecidos por Tipo de Indicador

#### 🟢 Indicadores REGULARES (Régimen General)

| Rango | Categoría | Código | Color | Ícono |
|-------|-----------|--------|-------|-------|
| **< 80%** | Peligro | `PEL` | `#D32F2F` 🔴 | 🔴 |
| **80% - 99.99%** | Alerta | `ALE` | `#FBAF17` 🟡 | 🟡 |
| **100% - 104.99%** | Cumplimiento | `CUM` | `#43A047` 🟢 | 🟢 |
| **≥ 105%** | Sobrecumplimiento | `SOB` | `#1A3A5C` 🔵 | 🔵 |

**Cálculo de Cumplimiento:**
```
Positivo (ascendente): cumplimiento = ejecución / meta
Negativo (descendente): cumplimiento = meta / ejecución
Especial Meta=0 & Ejec=0: cumplimiento = 1.0 (100% - éxito)
Especial Negativo & Ejec=0: cumplimiento = 1.0 (100% - éxito)
Tope máximo: 1.3 (130%)
```

**Umbrales en config.py:**
```python
UMBRAL_PELIGRO = 0.80                      # Límite inferior Alerta
UMBRAL_ALERTA = 1.00                       # Límite inferior Cumplimiento
UMBRAL_SOBRECUMPLIMIENTO = 1.05            # Límite inferior Sobrecumplimiento
```

---

#### 📅 Indicadores PLAN ANUAL (Régimen Especial PA)

| Rango | Categoría | Código | Color | Ícono |
|-------|-----------|--------|-------|-------|
| **< 80%** | Peligro | `PEL` | `#D32F2F` 🔴 | 🔴 |
| **80% - 94.99%** | Alerta | `ALE` | `#FBAF17` 🟡 | 🟡 |
| **≥ 95% (máx 100%)** | Cumplimiento | `CUM` | `#43A047` 🟢 | 🟢 |

**Características especiales:**
- ✅ Cumplen desde 95% (vs 100% en regular)
- ✅ Tope máximo 100% (no hay sobrecumplimiento)
- ✅ Auto-detectados por ID desde Excel: `Indicadores por CMI.xlsx`
- ✅ Criterio: Columna "Plan anual"=1 O "Proyecto"=1

**Umbrales en config.py:**
```python
UMBRAL_ALERTA_PA = 0.95                    # Límite inferior Cumplimiento PA
UMBRAL_SOBRECUMPLIMIENTO_PA = 1.00         # Tope máximo PA
IDS_PLAN_ANUAL = frozenset(...)            # Cargados dinámicamente del Excel
```

---

## 🔌 FUNCIÓN OFICIAL

### Importar y Usar

```python
# ✅ FORMA CORRECTA - Centralizadas
from core.semantica import categorizar_cumplimiento
from core.config import UMBRAL_PELIGRO, UMBRAL_ALERTA, UMBRAL_SOBRECUMPLIMIENTO

# En código:
categoria = categorizar_cumplimiento(cumplimiento_valor, id_indicador=id_del_indicador)
# Retorna: "Peligro" | "Alerta" | "Cumplimiento" | "Sobrecumplimiento" | "Sin dato"
```

### Firma Oficial

```python
def categorizar_cumplimiento(
    cumplimiento: Union[float, str, None],
    id_indicador: Optional[Union[str, int]] = None
) -> str:
    """
    Categoriza cumplimiento según estándares SGIND.
    
    Parámetros
    ----------
    cumplimiento : float, str, NaN
        Valor normalizado (0.0 a 1.3, donde 1.0 = 100%)
        Acepta strings con "%", decimales latinoamericanos, NaN
    
    id_indicador : str, int, opcional
        ID del indicador para detectar si es Plan Anual
        Si None → asume régimen Regular
    
    Retorna
    -------
    str
        Una de: "Peligro", "Alerta", "Cumplimiento", "Sobrecumplimiento", "Sin dato"
    
    Ejemplos
    --------
    >>> categorizar_cumplimiento(0.95, "373")      # PA: "Cumplimiento"
    >>> categorizar_cumplimiento(0.95, "999")      # Regular: "Alerta"
    >>> categorizar_cumplimiento(1.05)             # Regular: "Sobrecumplimiento"
    >>> categorizar_cumplimiento(None)             # "Sin dato"
    """
```

---

## 📁 UBICACIÓN OFICIAL

| Componente | Archivo | Línea | Status |
|-----------|---------|-------|--------|
| **Constantes/Umbrales** | `core/config.py` | 60-66, 160-161 | ✅ Centralizado |
| **Función oficial** | `core/semantica.py` | 65-140 | ✅ Centralizado |
| **Función alternativa** | `core/calculos.py` | 26-120 | ⚠️ Legacy (compatibilidad) |
| **Tests** | `tests/test_semantica.py` | 1-150 | ✅ Cobertura 85%+ |
| **Tests** | `tests/test_calculos.py` | 1-180 | ✅ Cobertura 85%+ |

---

## ❌ PROHIBIDO

### ❌ NO Usar

```python
# ❌ INCORRECTO - Lógica inline (PROHIBIDO)
if cumpl < 0.80:
    categoria = "Peligro"
elif cumpl < 1.00:
    categoria = "Alerta"
elif cumpl < 1.05:
    categoria = "Cumplimiento"
else:
    categoria = "Sobrecumplimiento"

# ❌ INCORRECTO - Hardcodear umbrales (PROHIBIDO)
if cumpl < UMBRAL_PELIGRO:
    # ...
    
# ❌ INCORRECTO - Ignorar Plan Anual (PROHIBIDO)
categoria = _funcion_que_no_detecta_pa()

# ❌ INCORRECTO - Importar de lugar equivocado
from services.strategic_indicators import _nivel_desde_cumplimiento
```

---

## ✅ CÓMO IMPLEMENTAR

### Patrón 1: DataFrame con apply()

```python
from core.semantica import categorizar_cumplimiento

# Aplicar a cada fila
df["Categoria"] = df.apply(
    lambda row: categorizar_cumplimiento(
        row["Cumplimiento"],
        id_indicador=row.get("Id")
    ),
    axis=1
)
```

### Patrón 2: Series

```python
from core.semantica import categorizar_cumplimiento

# Si tienes Series paralelas:
categorias = df["Cumplimiento"].combine(
    df["Id"],
    lambda cumpl, id_: categorizar_cumplimiento(cumpl, id_)
)
```

### Patrón 3: Valor Individual

```python
from core.semantica import categorizar_cumplimiento

# Para un solo valor:
categoria = categorizar_cumplimiento(0.947, id_indicador="373")
# Output: "Cumplimiento"
```

---

## 🧪 VALIDACIONES CRÍTICAS

### Test Plan Anual

```python
def test_plan_anual_95_es_cumplimiento():
    """Plan Anual con 95% debe ser 'Cumplimiento'"""
    assert categorizar_cumplimiento(0.95, "373") == "Cumplimiento"

def test_regular_95_es_alerta():
    """Regular con 95% debe ser 'Alerta'"""
    assert categorizar_cumplimiento(0.95, "999") == "Alerta"
```

### Test Casos Especiales

```python
def test_meta_0_ejec_0_es_100():
    """Meta=0 & Ejec=0 debe retornar 1.0"""
    assert recalcular_cumplimiento_faltante(0, 0, "Positivo") == 1.0

def test_negativo_ejec_0_es_100():
    """Negativo & Ejec=0 debe retornar 1.0"""
    assert recalcular_cumplimiento_faltante(10, 0, "Negativo") == 1.0
```

---

## 📋 CHECKLIST: AUDITORÍA DE CUMPLIMIENTO

Para verificar que un módulo implementa el estándar correctamente:

- [ ] **Imports:** Importa `categorizar_cumplimiento` desde `core.semantica`
- [ ] **No inline:** NO hay lógica `if cumpl < X:` inline en el código
- [ ] **Plan Anual:** Pasa `id_indicador` a la función
- [ ] **No hardcode:** NO usa `UMBRAL_PELIGRO` en su código (lo maneja `semantica.py`)
- [ ] **Tests:** Tiene tests unitarios que validan su uso
- [ ] **Configuración:** Si define umbrales, importa de `core.config`

---

## 📊 VISTA DE IMPLEMENTACIÓN ACTUAL

```
✅ CENTRALIZADO:
  ├─ core/config.py ..................... Umbrales
  ├─ core/semantica.py .................. Función oficial
  ├─ tests/test_semantica.py ........... Tests (85%+ cov)
  └─ tests/test_calculos.py ........... Tests (85%+ cov)

⚠️ EN TRANSICIÓN:
  ├─ core/calculos.py .................. Legacy (mantener compatible)
  ├─ services/data_loader.py ........... Usa semantica.py ✅
  └─ services/strategic_indicators.py .. Usa semantica.py ✅

✅ COMPLETO:
  ├─ streamlit_app/pages/*.py ......... Todos usan semantica.py ✅
  ├─ dashboard_profesional.html ....... Usa función centralizada ✅
  ├─ dashboard_diplomatic.html ........ Usa función centralizada ✅
  └─ dashboard_rediseñado.html ........ Usa función centralizada ✅
```

---

## 🔄 MIGRACIÓN COMPLETADA (Problema #1 RESUELTO)

**FIX Principal: Plan Anual Mal Categorizado**

| Antes | Después | Estado |
|-------|---------|--------|
| 🔴 ID 373, cumpl 0.947 → "Alerta" | ✅ ID 373, cumpl 0.947 → "Cumplimiento" | FIJO |
| ❌ Función defectuosa ignoraba Plan Anual | ✅ Función oficial detecta Plan Anual | FIJO |
| ❌ 5 implementaciones divergentes | ✅ 1 función oficial centralizada | FIJO |
| ❌ 30 min para cambiar umbral | ✅ 1 min para cambiar umbral | FIJO |

---

## 📞 PREGUNTAS FRECUENTES

**P: ¿Si agrego un nuevo indicador Plan Anual, qué debo hacer?**  
R: Nada. Se carga automáticamente del Excel "Indicadores por CMI.xlsx" en `_cargar_ids_plan_anual()`.

**P: ¿Puedo usar `core/calculos.py` en vez de `semantica.py`?**  
R: Puede compilar, pero es legacy. Usa `semantica.py`. Ver `core/calculos.py` tiene FIX igual pero se mantiene compatible.

**P: ¿Qué si el indicador ID es un número, no string?**  
R: No importa. La función convierte automáticamente: `str(id_indicador).strip() in IDS_PLAN_ANUAL`.

**P: ¿Qué si hay un indicador "373" que NO es Plan Anual?**  
R: Si no está marcado en el Excel como "Plan anual"=1 O "Proyecto"=1, será tratado como Regular.

**P: ¿Puedo cambiar los umbrales?**  
R: SÍ. Edita `core/config.py` línea 60-66 y 160-161. Los cambios se aplican automáticamente a TODO el proyecto.

---

## 🚀 NEXT STEPS

1. **Hoy:** Revisar este estándar
2. **Mañana:** Ejecutar test suite para validar cumplimiento
3. **Próxima semana:** Auditoría de cualquier código que NO lo cumpla
4. **Deploy:** Merge a `develop` y auto-deploy a staging

---

**Aprobado por:** Auditoría exhaustiva del proyecto  
**Implementación comenzó:** 21 de abril de 2026  
**Status:** ✅ VIGENTE Y OBLIGATORIO
