# 📋 PROBLEMA #2: CASOS ESPECIALES DIVERGENTES 🔴 CRÍTICA

**Status:** EN PROGRESO  
**Fecha:** 21 de abril de 2026  
**Severidad:** 🔴 CRÍTICA - Datos incorrectos en casos especiales  

---

## 🔴 EL PROBLEMA

### Descripción
Hay **3 implementaciones distintas** del cálculo de cumplimiento que manejan **casos especiales de forma diferente**:

#### Caso Especial #1: Meta=0 & Ejecución=0
```
Interpretación: "Meta de 0 muertes, 0 accidentes lograda perfectamente"
Ejemplo: Indicador "Mortalidad Laboral" (meta=0, ejecutado=0)

IMPLEMENTACIÓN 1 (data_loader.py:248 - DEFECTUOSA):
└─ Calcula: 0/0 → NaN ❌

IMPLEMENTACIÓN 2 (strategic_indicators.py:160 - DEFECTUOSA):
└─ Calcula: 0/0 → NaN ❌

IMPLEMENTACIÓN 3 (cumplimiento.py:23 - CORRECTA):
└─ Retorna: 1.0 (100% éxito) ✅
```

#### Caso Especial #2: Sentido=Negativo & Ejecución=0
```
Interpretación: "Indicador donde menos es mejor (gastos, accidentes)"
Ejemplo: "Accidentalidad" (meta=1.6 accidentes permitidos, ejecutado=0)

IMPLEMENTACIÓN 1 (data_loader.py:248 - DEFECTUOSA):
└─ Calcula: 1.6/0 → ∞ ❌ (división por cero)

IMPLEMENTACIÓN 2 (strategic_indicators.py:160 - DEFECTUOSA):
└─ Calcula: 1.6/0 → ∞ ❌ (división por cero)

IMPLEMENTACIÓN 3 (cumplimiento.py:23 - CORRECTA):
└─ Retorna: 1.0 (100% éxito - cero es perfecto) ✅
```

---

## 📍 UBICACIÓN DE LAS 3 IMPLEMENTACIONES DIVERGENTES

### IMPLEMENTACIÓN #1: data_loader.py (línea 248)
**Problema:** Lambda inline dentro de función

```python
# Línea 248-276 en _aplicar_calculos_cumplimiento()
def _recalc_cumpl(row):
    # ❌ NO maneja casos especiales (Meta=0, Ejec=0)
    # ❌ NO maneja Negativo & Ejec=0
    # ❌ Lógica inline sin reutilización
    if pd.isna(row["Cumplimiento"]):
        if row["Meta"] == 0:
            return None  # ❌ Debería ser 1.0 si Ejec=0 también
        elif row["Sentido"] == "Positivo":
            return row["Ejecucion"] / row["Meta"]
        else:
            return row["Meta"] / row["Ejecucion"]  # ❌ Falla si Ejec=0
    return row["Cumplimiento"]
```

**Ubicación:** `services/data_loader.py:248-276`  
**Responsabilidad:** Recalcular cumplimiento faltante  
**Status:** ❌ DEFECTUOSA

---

### IMPLEMENTACIÓN #2: strategic_indicators.py (línea 160)
**Problema:** También recalcula pero con lógica distinta

```python
# Línea 160 en load_cierres()
# Se aplica cuando Cumplimiento es NaN
cumpl = df["Meta"] / df["Ejecucion"] if df["Sentido"]=="Negativo" else ...
# ❌ NO maneja Meta=0 & Ejec=0
# ❌ Falla si Ejec=0 en Negativo
```

**Ubicación:** `services/strategic_indicators.py:160` (en `load_cierres()`)  
**Responsabilidad:** Recalcular cumplimiento en datos históricos  
**Status:** ❌ DEFECTUOSA

---

### IMPLEMENTACIÓN #3: cumplimiento.py (línea 23) ✅ BEST
**Problema:** No se reutiliza, está solo en scripts/etl

```python
# Línea 23-100 en scripts/etl/cumplimiento.py
def _calc_cumpl(meta, ejec, sentido, tope=1.3) → Tuple:
    """
    ✅ Maneja TODAS las casos especiales:
    - Meta=0 & Ejec=0 → (1.0, 1.0) ✅ Correcto
    - Negativo & Ejec=0 → (1.0, 1.0) ✅ Correcto
    - Retorna (cumpl_capped, cumpl_real) ✅ Diferencia tope
    """
    
    # CASO ESPECIAL 1: Meta=0 y Ejecución=0
    if m == 0 and e == 0:
        return 1.0, 1.0  # ✅ Éxito perfecto
    
    # CASO ESPECIAL 2: Sentido Negativo y Ejecución=0
    if sentido.lower() == "negativo" and e == 0 and m > 0:
        return 1.0, 1.0  # ✅ Cero es perfecto
    
    # Cálculo estándar
    if sentido.lower() == "positivo":
        raw = e / m
    else:
        raw = m / e if e != 0 else None
    
    cumpl_capped = min(raw, tope) if raw else None
    return cumpl_capped, raw
```

**Ubicación:** `scripts/etl/cumplimiento.py:23-100`  
**Responsabilidad:** Cálculo puro de cumplimiento  
**Status:** ✅ CORRECTA (pero aislada)

---

## ❌ IMPACTO DE LA DIVERGENCIA

### Indicadores Afectados
```
Aproximadamente 5-10 indicadores con casos especiales:
├─ Mortalidad Laboral (Meta=0)
├─ Accidentalidad (Negativo & Ejec=0)
├─ Otros indicadores de "cero es perfecto"
└─ ...
```

### Datos Incorrectos Generados
```
EJEMPLO: Indicador "Accidentalidad"
Meta: 1.6 accidentes permitidos
Ejecutado: 0 accidentes (perfecto)

ESPERADO: cumplimiento = 1.0 (100% éxito)

CON IMPLEMENTACIÓN 1-2:
└─ Intenta: 1.6 / 0 = ∞ = NaN ❌
  Dashboard muestra: "Sin dato" ❌
  Usuario confundido: ¿Qué pasó? ¿Error?

CON IMPLEMENTACIÓN 3:
└─ Retorna: 1.0 (100% éxito) ✅
  Dashboard muestra: "Cumplimiento" ✅
  Usuario sabe: "Cero accidentes = perfecto" ✅
```

---

## ✅ SOLUCIÓN: CENTRALIZAR EN 1 FUNCIÓN GLOBAL

### Propuesta
Crear **`recalcular_cumplimiento_faltante()`** en `core/semantica.py` que:

1. **Unifica** las 3 lógicas en 1 función
2. **Usa** la lógica correcta de `cumplimiento.py`
3. **Centraliza** para que todos usen la misma
4. **Reutiliza** en ambos lugares (data_loader + strategic_indicators)

### Firma de la Función
```python
def recalcular_cumplimiento_faltante(
    meta: float,
    ejecucion: float,
    sentido: str = "Positivo",
    id_indicador: Optional[str] = None
) -> float:
    """
    Recalcula cumplimiento cuando falta (NaN).
    
    Casos especiales:
    ✅ Meta=0 & Ejec=0 → 1.0 (éxito perfecto)
    ✅ Negativo & Ejec=0 → 1.0 (cero es perfecto)
    
    Parámetros
    ----------
    meta : float
        Meta del indicador
    ejecucion : float
        Ejecución del indicador
    sentido : str
        "Positivo" (más es mejor) o "Negativo" (menos es mejor)
    id_indicador : str, opcional
        Para detectar Plan Anual y aplicar tope dinámico
    
    Retorna
    -------
    float
        Cumplimiento normalizado (0.0 a 1.3 regular, o 0.0 a 1.0 PA)
        None si no se puede calcular
    """
```

### Ubicación
`core/semantica.py` (junto a `categorizar_cumplimiento()`)

---

## 🔄 REEMPLAZO EN CÓDIGO ACTUAL

### CAMBIO 1: data_loader.py (línea 248)
```python
# ANTES (lambda inline defectuosa):
def _recalc_cumpl(row):
    if pd.isna(row["Cumplimiento"]):
        ...lógica inline...
    return row["Cumplimiento"]

# DESPUÉS (función centralizada):
from core.semantica import recalcular_cumplimiento_faltante

if pd.isna(row["Cumplimiento"]):
    row["Cumplimiento"] = recalcular_cumplimiento_faltante(
        row["Meta"],
        row["Ejecucion"],
        row.get("Sentido", "Positivo"),
        row.get("Id")
    )
```

### CAMBIO 2: strategic_indicators.py (línea 160)
```python
# ANTES (lógica inline divergente):
cumpl = df["Meta"] / df["Ejecucion"] if ...
# ❌ No maneja casos especiales

# DESPUÉS (función centralizada):
from core.semantica import recalcular_cumplimiento_faltante

df["Cumplimiento"] = df.apply(
    lambda row: recalcular_cumplimiento_faltante(
        row["Meta"],
        row["Ejecucion"],
        row.get("Sentido", "Positivo"),
        row.get("Id")
    ) if pd.isna(row["Cumplimiento"]) else row["Cumplimiento"],
    axis=1
)
```

---

## 🧪 TESTS REQUERIDOS

### Test: Meta=0 & Ejec=0 → 1.0
```python
def test_meta_0_ejec_0_retorna_100():
    """Meta=0 & Ejecución=0 debe retornar 1.0 (éxito perfecto)"""
    resultado = recalcular_cumplimiento_faltante(0, 0, "Positivo")
    assert resultado == 1.0, f"Esperado 1.0, obtenido {resultado}"
```

### Test: Negativo & Ejec=0 → 1.0
```python
def test_negativo_ejec_0_retorna_100():
    """Negativo & Ejecución=0 debe retornar 1.0 (cero es perfecto)"""
    resultado = recalcular_cumplimiento_faltante(1.6, 0, "Negativo")
    assert resultado == 1.0, f"Esperado 1.0, obtenido {resultado}"
```

### Test: Positivo & Ejec=0 & Meta>0 → NaN
```python
def test_positivo_ejec_0_retorna_none():
    """Positivo & Ejecución=0 (Meta>0) debe retornar None (error)"""
    resultado = recalcular_cumplimiento_faltante(10, 0, "Positivo")
    assert resultado is None, f"Esperado None, obtenido {resultado}"
```

### Test: Tope dinámico según Plan Anual
```python
def test_tope_regular_max_130():
    """Regular: cumplimiento se topa a 1.3 (130%)"""
    resultado = recalcular_cumplimiento_faltante(100, 150, "Positivo", id_indicador="999")
    assert resultado <= 1.3, f"Tope regular violado: {resultado}"

def test_tope_pa_max_100():
    """Plan Anual: cumplimiento se topa a 1.0 (100%)"""
    resultado = recalcular_cumplimiento_faltante(100, 150, "Positivo", id_indicador="1")
    assert resultado <= 1.0, f"Tope PA violado: {resultado}"
```

---

## 📊 MATRIZ DE CAMBIOS REQUERIDOS

| Archivo | Línea | Cambio | Antes | Después | Status |
|---------|-------|--------|-------|---------|--------|
| `core/semantica.py` | NEW | Crear función | N/A | ✅ Función centralizada | ⏳ TODO |
| `services/data_loader.py` | 248 | Reemplazar lambda | ❌ Inline defectuosa | ✅ Import función | ⏳ TODO |
| `services/strategic_indicators.py` | 160 | Reemplazar lógica | ❌ Inline divergente | ✅ Import función | ⏳ TODO |
| `tests/test_problema_2_*` | NEW | Tests | N/A | 10+ tests | ⏳ TODO |

---

## 🎯 CHECKLIST: SOLUCIÓN

- [ ] Crear `recalcular_cumplimiento_faltante()` en `core/semantica.py`
- [ ] Implementar casos especiales (Meta=0, Negativo & Ejec=0)
- [ ] Aplicar tope dinámico (Regular vs PA)
- [ ] Reemplazar en `data_loader.py:248`
- [ ] Reemplazar en `strategic_indicators.py:160`
- [ ] Crear tests (10+)
- [ ] Ejecutar tests (100% pass)
- [ ] Validar datos en ambos lugares
- [ ] Merge a develop

---

## 📈 IMPACTO ESPERADO

### Antes (Divergente)
```
Indicador "Accidentalidad":
├─ Ejecutado con data_loader: NaN ❌
├─ Ejecutado con strategic_indicators: NaN ❌
├─ Ejecutado con cumplimiento.py: 1.0 ✅
└─ Status: INCONSISTENTE - datos malos
```

### Después (Centralizado)
```
Indicador "Accidentalidad":
├─ Ejecutado con data_loader: 1.0 ✅
├─ Ejecutado con strategic_indicators: 1.0 ✅
├─ Usados en dashboards: 1.0 ✅
└─ Status: CONSISTENTE - datos correctos
```

---

## ⏰ TIMELINE

- **Hoy:** Crear función + reemplazar código
- **Mañana:** Tests + validación
- **ASAP:** Merge a develop

---

**Documento:** Plan de resolución de PROBLEMA #2  
**Status:** 🔴 CRÍTICA - 3 lógicas divergentes  
**Próxima acción:** Crear función centralizada
