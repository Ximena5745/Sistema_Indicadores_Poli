# 🔧 GUÍA DE REFACTORIZACIÓN: EJEMPLOS DE CÓDIGO

**Archivo:** Ejemplos de cambios antes/después para cada problema identificado

---

## PROBLEMA #1: Reemplazar `_nivel_desde_cumplimiento()` Defectuosa

### ANTES (Incorrecto - strategic_indicators.py línea 55)

```python
def _nivel_desde_cumplimiento(cumplimiento_dec):
    """❌ NO soporta Plan Anual"""
    if pd.isna(cumplimiento_dec):
        return "Sin dato"
    
    # Usa umbrales FIJOS (ignora si indicador es Plan Anual)
    if cumplimiento_dec < UMBRAL_PELIGRO_DEC:
        return "Peligro"
    elif cumplimiento_dec < UMBRAL_ALERTA_DEC:
        return "Alerta"
    elif cumplimiento_dec < UMBRAL_SOBRECUMPLIMIENTO_DEC:
        return "Cumplimiento"
    else:
        return "Sobrecumplimiento"


def load_cierres():
    """Carga datos históricos de Cierres"""
    df = pd.read_excel(...)
    
    # ❌ PROBLEMA: Se categoriza sin considerar si es Plan Anual
    df["Categoria"] = df["Cumplimiento"].apply(_nivel_desde_cumplimiento)
    
    return df
```

**RESULTADO INCORRECTO:**
```
Indicador 373 (Plan Anual), cumpl=0.947
├─ Esperado: "Cumplimiento" (umbral PA: 0.95)
└─ Actual: "Alerta" (umbral Regular: 1.00) ❌
```

---

### DESPUÉS (Correcto)

```python
from core.semantica import categorizar_cumplimiento  # ← IMPORT OFICIAL

# ✅ ELIMINAR función defectuosa
# (borrar _nivel_desde_cumplimiento)

def load_cierres():
    """Carga datos históricos de Cierres"""
    df = pd.read_excel(...)
    
    # ✅ USAR función oficial que SOPORTA Plan Anual
    df["Categoria"] = df.apply(
        lambda row: categorizar_cumplimiento(
            row["Cumplimiento"],
            id_indicador=row.get("Id")  # ← PASAR ID para detección PA
        ),
        axis=1
    )
    
    return df
```

**RESULTADO CORRECTO:**
```
Indicador 373 (Plan Anual), cumpl=0.947
├─ ID es detectado como Plan Anual
├─ Se aplica umbral PA (0.95)
└─ Resultado: "Cumplimiento" ✅
```

---

## PROBLEMA #2: Unificar Cálculo de Cumplimiento (Meta/Ejec)

### ANTES (3 Lugares diferentes)

#### Ubicación 1: services/data_loader.py:248 (Inline lambda)
```python
def _aplicar_calculos_cumplimiento(df: pd.DataFrame) -> pd.DataFrame:
    # ... código previo ...
    
    # ❌ CÁLCULO INLINE - Cuando Cumplimiento es NaN
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
```

#### Ubicación 2: services/strategic_indicators.py:160 (Similar)
```python
# ❌ CÓDIGO DUPLICADO similar al anterior
```

#### Ubicación 3: scripts/etl/cumplimiento.py:23 (Mejor, pero no se usa)
```python
def _calc_cumpl(
    meta: object,
    ejec: object,
    sentido: str,
    tope: float = 1.3,
) -> Tuple[Optional[float], Optional[float]]:
    """✅ Esta es LA MEJOR implementación pero está aislada"""
    # ... implementación con casos especiales ...
    
    # CASOS ESPECIALES que las otras NO tienen:
    if m == 0 and e == 0:
        return 1.0, 1.0  # ✅ Meta=0 & Ejec=0 = éxito
    
    if sentido.strip().lower() == "negativo" and e == 0 and m > 0:
        return 1.0, 1.0  # ✅ Negativo & Ejec=0 = éxito
```

---

### DESPUÉS (Función Única Oficial)

#### Paso 1: Crear `core/calculos_oficial.py` (NUEVA CENTRALIZADA)

```python
"""
core/calculos_oficial.py
MÓDULO ÚNICO de cálculo de cumplimiento.

Centraliza la lógica que estaba duplicada en:
- services/data_loader.py
- services/strategic_indicators.py  
- scripts/etl/cumplimiento.py
"""

from typing import Optional, Tuple
import pandas as pd
import numpy as np
import logging

from core.config import IDS_PLAN_ANUAL

logger = logging.getLogger(__name__)


def calcular_cumplimiento(
    meta: object,
    ejecucion: object,
    sentido: str = "Positivo",
    id_indicador: object = None
) -> float:
    """
    FUNCIÓN OFICIAL de cálculo de cumplimiento.
    
    Centraliza la lógica oficial para indicadores, garantizando
    consistencia en todo el sistema.
    
    Parámetros
    ----------
    meta : float | str | int
        Meta del período (debe ser > 0)
        
    ejecucion : float | str | int
        Ejecución real del período
        
    sentido : str, default "Positivo"
        "Positivo": más es mejor (cumpl = ejec/meta)
        "Negativo": menos es mejor (cumpl = meta/ejec)
        
    id_indicador : str | int, optional
        ID del indicador para detectar Plan Anual
        y aplicar tope correcto (1.0 vs 1.3)
    
    Retorna
    -------
    float
        Cumplimiento cappado:
        - [0, 1.0] si Plan Anual
        - [0, 1.3] si regular
        
        O NaN si no se puede calcular (meta=0, entrada inválida, etc.)
    
    Casos Especiales
    ----------------
    1. Meta=0 AND Ejecución=0
       → Retorna 1.0 (100% éxito - ambas metas logradas)
       Ej: Mortalidad laboral (meta=0 muertes, ejecutado=0)
       
    2. Sentido="Negativo" AND Ejecución=0 AND Meta>0
       → Retorna 1.0 (100% éxito - cero es perfecto)
       Ej: Accidentalidad (meta=1.6 accidentes, ejecutado=0)
       
    3. Meta=0 (sin Ejecución=0)
       → Retorna NaN (no se puede calcular)
       Ej: Intento dividir por cero
    
    Ejemplos
    --------
    >>> calcular_cumplimiento(100, 50, "Positivo")
    0.5
    
    >>> calcular_cumplimiento(100, 150, "Positivo")
    1.3  # Tope regular
    
    >>> calcular_cumplimiento(100, 150, "Positivo", id_indicador="373")
    1.0  # Tope Plan Anual
    
    >>> calcular_cumplimiento(100, 0, "Negativo")
    1.0  # Caso especial: cero accidentes = éxito
    
    >>> calcular_cumplimiento(0, 0, "Positivo")
    1.0  # Caso especial: ambas metas en cero
    """
    # ── VALIDAR ENTRADA ────────────────────────────────────────
    if meta is None or ejecucion is None:
        logger.debug(f"Meta o Ejecución es None: meta={meta}, ejec={ejecucion}")
        return np.nan
    
    # Convertir a float
    try:
        m = float(meta)
        e = float(ejecucion)
    except (TypeError, ValueError):
        logger.debug(f"No convertible a float: meta={meta} ({type(meta)}), ejec={ejecucion}")
        return np.nan
    
    # ── CASO ESPECIAL 1: Meta=0 Y Ejecución=0 ────────────────────
    # Interpretación: meta de 0 muertes, 0 accidentes, etc. lograda perfectamente
    if m == 0 and e == 0:
        logger.debug("Caso especial: Meta=0 y Ejec=0 → 100% (éxito perfecto)")
        return 1.0
    
    # ── CASO ESPECIAL 2: Sentido Negativo Y Ejecución=0 ──────────
    # Interpretación: indicador que menos es mejor (gastos, accidentes)
    # Si ejecutó 0 (cero gastos, cero accidentes), es perfecto
    if sentido.strip().lower() == "negativo" and e == 0 and m > 0:
        logger.debug("Caso especial Negativo: Ejec=0 y Meta>0 → 100% (cero es perfecto)")
        return 1.0
    
    # ── ERROR: Meta no puede ser 0 (división por cero) ─────────────
    if m == 0:
        logger.debug(f"Meta es 0 (no se puede dividir): meta={m}, ejec={e}")
        return np.nan
    
    # ── CÁLCULO SEGÚN SENTIDO ──────────────────────────────────────
    if sentido.strip().lower() == "positivo":
        # Más es mejor: cumplimiento = ejecución / meta
        raw = e / m
    else:
        # Menos es mejor (Negativo): cumplimiento = meta / ejecución
        # Pero si ejec=0 ya fue manejado arriba como éxito
        if e == 0:
            logger.debug(f"Sentido Negativo con Ejec=0: meta={m}, ejec={e}")
            return np.nan
        raw = m / e
    
    # ── NORMALIZAR: ASEGURAR MÍNIMO 0 ──────────────────────────────
    raw = max(raw, 0.0)
    
    # ── APLICAR TOPE DINÁMICO ──────────────────────────────────────
    es_plan_anual = (
        id_indicador is not None and 
        str(id_indicador).strip() in IDS_PLAN_ANUAL
    )
    tope = 1.0 if es_plan_anual else 1.3
    cumpl_capped = min(raw, tope)
    
    logger.debug(
        f"Calc cumpl: meta={m}, ejec={e}, sentido={sentido}, "
        f"raw={raw:.4f}, es_pa={es_plan_anual}, tope={tope}, capped={cumpl_capped:.4f}"
    )
    
    return cumpl_capped


# Alias para compatibilidad
recalcular_cumplimiento = calcular_cumplimiento


def calcular_cumplimiento_con_real(
    meta: object,
    ejecucion: object,
    sentido: str = "Positivo",
    id_indicador: object = None
) -> Tuple[Optional[float], Optional[float]]:
    """
    Calcula cumplimiento CAPPED y REAL (sin tope).
    
    Retorna (cumpl_capped, cumpl_real) para análisis avanzado.
    """
    # Usar lógica de calcular_cumplimiento hasta normalizar
    cumpl_capped = calcular_cumplimiento(meta, ejecucion, sentido, id_indicador)
    
    # Calcular sin tope (cumpl_real)
    try:
        m, e = float(meta), float(ejecucion)
        if m > 0:
            raw = e / m if sentido.strip().lower() == "positivo" else m / e
            cumpl_real = max(raw, 0.0)
        else:
            cumpl_real = np.nan
    except:
        cumpl_real = np.nan
    
    return cumpl_capped, cumpl_real
```

#### Paso 2: Actualizar Importes en `services/data_loader.py`

```python
# ANTES
from core.config import UMBRAL_PELIGRO, UMBRAL_ALERTA, ...

# DESPUÉS
from core.calculos_oficial import calcular_cumplimiento
from core.config import IDS_PLAN_ANUAL
```

#### Paso 3: Reemplazar inline en data_loader.py:248

```python
# ❌ ANTES (inline lambda 30 líneas)
def _aplicar_calculos_cumplimiento(df: pd.DataFrame) -> pd.DataFrame:
    mask_nan = df["Cumplimiento"].isna() & ~_mask_metrica & ~_mask_sin_reporte
    if mask_nan.any():
        def _recalc_cumpl(row: pd.Series) -> float:
            try:
                m, e = float(row["Meta"]), float(row["Ejecucion"])
            except (TypeError, ValueError):
                return float("nan")
            # ... 25 líneas más ...
        df.loc[mask_nan, "Cumplimiento"] = df[mask_nan].apply(_recalc_cumpl, axis=1)

# ✅ DESPUÉS (1 línea + import)
def _aplicar_calculos_cumplimiento(df: pd.DataFrame) -> pd.DataFrame:
    mask_nan = df["Cumplimiento"].isna() & ~_mask_metrica & ~_mask_sin_reporte
    if mask_nan.any():
        df.loc[mask_nan, "Cumplimiento"] = df[mask_nan].apply(
            lambda row: calcular_cumplimiento(
                row["Meta"], 
                row["Ejecucion"],
                row.get("Sentido", "Positivo"),
                row.get("Id")
            ),
            axis=1
        )
```

---

## PROBLEMA #3: Eliminar Inline en Dashboards

### ANTES (resumen_general.py - Inline duplicado)

```python
# ❌ INLINE SIN REUTILIZACIÓN
def main():
    st.title("Resumen General")
    
    df = cargar_dataset()
    
    # ❌ Categorización hardcoded (copia de código)
    df['Categoria'] = df['Cumplimiento'].apply(
        lambda x: "Peligro" if x < 0.80 else
                  "Alerta" if x < 1.00 else
                  "Cumplimiento" if x < 1.05 else
                  "Sobrecumplimiento"
    )
    
    # ... resto de código ...
```

**PROBLEMAS:**
- No usa función centralizada
- No soporta Plan Anual (id_indicador)
- Si cambias umbral, hay que actualizar aquí

---

### DESPUÉS (resumen_general.py - Centralizado)

```python
from core.semantica import categorizar_cumplimiento

def main():
    st.title("Resumen General")
    
    df = cargar_dataset()
    
    # ✅ USA FUNCIÓN OFICIAL
    df['Categoria'] = df.apply(
        lambda row: categorizar_cumplimiento(
            row['Cumplimiento'],
            id_indicador=row.get('Id')  # ← SOPORTE Plan Anual
        ),
        axis=1
    )
    
    # ... resto de código ...
```

**BENEFICIOS:**
- ✅ 1 única fuente de verdad
- ✅ Soporta Plan Anual automáticamente
- ✅ Cambio de umbral = actualizar 1 lugar

---

## PROBLEMA #4: Crear Tests Exhaustivos

### BEFORE (Sin tests)

```python
# ❌ NO HAY TESTS para calcular_cumplimiento
# Riesgo: Cambios silenciosos sin validación
```

---

### AFTER (Con tests)

```python
# tests/test_calculos_oficial.py

import pytest
import pandas as pd
import numpy as np

from core.calculos_oficial import (
    calcular_cumplimiento,
    calcular_cumplimiento_con_real
)


class TestCalcularCumplimiento:
    """Suite exhaustiva para calcular_cumplimiento()"""
    
    # ───────────────────────────────────────────────────────────
    # CASOS BÁSICOS
    # ───────────────────────────────────────────────────────────
    
    def test_positivo_basico(self):
        """Positivo: cumpl = ejec/meta"""
        assert calcular_cumplimiento(100, 50, "Positivo") == 0.5
        assert calcular_cumplimiento(100, 100, "Positivo") == 1.0
        assert calcular_cumplimiento(100, 150, "Positivo") == 1.3  # Tope regular
    
    def test_negativo_basico(self):
        """Negativo: cumpl = meta/ejec"""
        assert calcular_cumplimiento(100, 50, "Negativo") == 2.0
        assert calcular_cumplimiento(100, 100, "Negativo") == 1.0
        assert calcular_cumplimiento(100, 150, "Negativo") == 1.3  # Tope aplicado
    
    # ───────────────────────────────────────────────────────────
    # PLAN ANUAL
    # ───────────────────────────────────────────────────────────
    
    def test_plan_anual_tope_1_0(self):
        """Plan Anual: tope = 1.0 (no 1.3)"""
        # Regular: tope 1.3
        assert calcular_cumplimiento(100, 150, "Positivo") == 1.3
        
        # Plan Anual: tope 1.0
        assert calcular_cumplimiento(100, 150, "Positivo", id_indicador="373") == 1.0
    
    def test_plan_anual_no_sobrecumple_notoriamente(self):
        """Plan Anual: máximo 100%"""
        result = calcular_cumplimiento(50, 100, "Positivo", id_indicador="373")
        assert result == 1.0  # Cappado a 1.0
    
    # ───────────────────────────────────────────────────────────
    # CASOS ESPECIALES
    # ───────────────────────────────────────────────────────────
    
    def test_meta_cero_ejec_cero_es_exito(self):
        """Caso especial: Meta=0 & Ejec=0 → 1.0 (100%)"""
        # Mortalidad laboral: meta=0 (cero muertes), ejec=0 (ninguna muerte)
        assert calcular_cumplimiento(0, 0, "Positivo") == 1.0
        assert calcular_cumplimiento(0, 0, "Negativo") == 1.0
    
    def test_negativo_ejec_cero_es_exito(self):
        """Caso especial: Negativo & Ejec=0 → 1.0"""
        # Accidentalidad: meta=1.6, ejec=0 (cero accidentes)
        assert calcular_cumplimiento(100, 0, "Negativo") == 1.0
        
        # Pero si meta también es 0, es caso especial 1
        # (ya manejado arriba)
    
    def test_meta_cero_sin_ejec_cero_es_error(self):
        """Error: Meta=0 sin Ejec=0 → NaN"""
        assert pd.isna(calcular_cumplimiento(0, 50, "Positivo"))
    
    def test_negativo_ejec_cero_meta_cero_es_exito(self):
        """Caso especial combinada: Meta=0 & Ejec=0 gana"""
        # Si Meta=0 Y Ejec=0, es caso especial 1 (éxito)
        # (no es "división por cero" sino "ambas metas logradas")
        assert calcular_cumplimiento(0, 0, "Negativo") == 1.0
    
    # ───────────────────────────────────────────────────────────
    # ENTRADA INVÁLIDA
    # ───────────────────────────────────────────────────────────
    
    def test_entrada_string_convertible(self):
        """Entrada: strings convertibles a float"""
        assert calcular_cumplimiento("100", "50") == 0.5
        assert calcular_cumplimiento("100.5", "50.25") == 0.5
    
    def test_entrada_string_no_convertible(self):
        """Entrada: strings no convertibles → NaN"""
        assert pd.isna(calcular_cumplimiento("abc", 50))
        assert pd.isna(calcular_cumplimiento(100, "xyz"))
    
    def test_entrada_none(self):
        """Entrada: None → NaN"""
        assert pd.isna(calcular_cumplimiento(None, 50))
        assert pd.isna(calcular_cumplimiento(100, None))
    
    def test_entrada_array(self):
        """Entrada: array/list no convertible → NaN"""
        assert pd.isna(calcular_cumplimiento([100], 50))
        assert pd.isna(calcular_cumplimiento(100, [50]))
    
    # ───────────────────────────────────────────────────────────
    # TOPE DINÁMICO
    # ───────────────────────────────────────────────────────────
    
    def test_tope_regular_1_3(self):
        """Tope regular: 1.3"""
        assert calcular_cumplimiento(100, 150) == 1.3
        assert calcular_cumplimiento(100, 200) == 1.3
        assert calcular_cumplimiento(100, 9999) == 1.3
    
    def test_tope_plan_anual_1_0(self):
        """Tope Plan Anual: 1.0"""
        assert calcular_cumplimiento(100, 150, id_indicador="373") == 1.0
        assert calcular_cumplimiento(100, 200, id_indicador="373") == 1.0
    
    def test_tope_nunca_negativo(self):
        """Tope: nunca retorna negativo"""
        assert calcular_cumplimiento(100, -50) == 0.0
        assert calcular_cumplimiento(100, -9999) == 0.0
    
    # ───────────────────────────────────────────────────────────
    # INTEGRACIÓN
    # ───────────────────────────────────────────────────────────
    
    def test_integración_pipeline(self):
        """Test integración: simula pipeline completo"""
        datos = pd.DataFrame({
            'Id': ['373', '123', '245', '0', '0'],
            'Meta': [100, 100, 0, 100, 100],
            'Ejecucion': [90, 150, 0, 0, 50],
            'Sentido': ['Positivo', 'Positivo', 'Positivo', 'Negativo', 'Negativo']
        })
        
        # Aplicar función
        datos['Cumplimiento'] = datos.apply(
            lambda row: calcular_cumplimiento(
                row['Meta'],
                row['Ejecucion'],
                row['Sentido'],
                row['Id']
            ),
            axis=1
        )
        
        # Validar resultados
        assert datos.iloc[0]['Cumplimiento'] == 0.9  # PA regular
        assert datos.iloc[1]['Cumplimiento'] == 1.3  # Regular sobrecumple
        assert datos.iloc[2]['Cumplimiento'] == 1.0  # Meta=0 & Ejec=0
        assert pd.isna(datos.iloc[3]['Cumplimiento'])  # Error (meta=0)
        assert datos.iloc[4]['Cumplimiento'] == 1.0  # Negativo & Ejec=0 = éxito


class TestCalcularCumplimientoConReal:
    """Suite para calcular_cumplimiento_con_real()"""
    
    def test_retorna_tupla(self):
        """Retorna tupla (capped, real)"""
        capped, real = calcular_cumplimiento_con_real(100, 150, "Positivo")
        assert capped == 1.3  # Tope aplicado
        assert real == 1.5    # Sin tope
    
    def test_plan_anual_diferente_tope(self):
        """Plan Anual: tope diferente en ambas"""
        capped_pa, real = calcular_cumplimiento_con_real(100, 150, "Positivo", "373")
        assert capped_pa == 1.0  # PA tope
        assert real == 1.5       # Sin tope (igual)
```

---

## RESUMEN: Cambios Necesarios

| Archivo | Cambio | Líneas | Tiempo |
|---------|--------|--------|--------|
| Crear: `core/calculos_oficial.py` | Nueva función centralizada | +200 | 2h |
| `services/data_loader.py` | Reemplazar inline | 25→3 | 15m |
| `services/strategic_indicators.py` | Reemplazar `_nivel_desde_cumplimiento()` | 15→5 | 15m |
| Crear: `tests/test_calculos_oficial.py` | Suite exhaustiva | +300 | 2h |
| 9× `streamlit_app/pages/*.py` | Importar + usar función | 12→5 | 45m |
| 3× `dashboard/*.html` | Refactor JavaScript | 50→15 | 1h |

**TOTAL:** 44 horas de desarrollo (2 devs-semana)

---

**Próximo paso:** Crear rama `refactor/centralizacion-calculos` e implementar Fase 1
