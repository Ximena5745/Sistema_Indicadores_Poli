# 🧾 DECISIÓN FORMALIZADA: PROBLEMA #1

**Fecha:** 21 de abril de 2026  
**Problema:** Heurística "si > 2" sin validación en `normalizar_cumplimiento()`  
**Decisión Tomada:** **OPCIÓN A MEJORADA**  
**Estado:** ✅ APROBADA PARA IMPLEMENTACIÓN

---

## 📋 FORMALIZACIÓN

### PASO 4: Traducción a Acciones Concretas

#### Acción 1: Remover Heurística Mágica

```python
# ANTES (heurística ambigua):
def normalizar_cumplimiento(valor):
    if pd.isna(valor):
        return np.nan
    return valor / 100 if valor > 2 else valor  # ← HEURÍSTICA

# DESPUÉS (validación simple):
def normalizar_cumplimiento(valor):
    if pd.isna(valor):
        return np.nan
    try:
        valor = float(valor)
    except (ValueError, TypeError):
        logger.warning(f"No se puede convertir a float: {valor}")
        return np.nan
    
    # Validar rango esperado [0, 1.3]
    if not (0 <= valor <= 1.3):
        logger.warning(f"Valor fuera de rango esperado [0, 1.3]: {valor}")
        return np.nan  # O return valor si prefieres mantenerlo
    
    return valor
```

#### Acción 2: Archivos Impactados

| Archivo | Cambio | Impacto |
|---------|--------|---------|
| **core/calculos.py** | Reemplazar función | DIRECTO (16 líneas) |
| **services/data_loader.py** | Sin cambios | Indirecto (usar función mejorada) |
| **core/config.py** | Posible: agregar RANGO_CUMPLIMIENTO | Bajo |
| **tests/** | Crear test_calculos.py | Validación |

#### Acción 3: Pseudocódigo de Implementación

```python
# services/data_loader.py (Paso 4b - sin cambios en llamada)
df["Cumplimiento_norm"] = (
    df["Cumplimiento"].apply(normalizar_cumplimiento)  # ← Misma llamada
    if "Cumplimiento" in df.columns
    else float("nan")
)

# core/config.py (agregar constante)
RANGO_CUMPLIMIENTO = (0.0, 1.3)  # Mín, Máx esperado

# core/calculos.py (nueva validación)
def normalizar_cumplimiento(valor):
    """
    Valida que cumplimiento esté en rango esperado [0, 1.3].
    
    Notas:
    - Datos ya vienen normalizados desde Excel
    - Este función es de VALIDACIÓN, no de conversión
    - Si valor está fuera de rango → log warning + retorna NaN
    """
    ...
```

---

## 📊 PASO 5: MATRIZ DE TRAZABILIDAD

| # | Problema | Componente | Decisión | Tipo Solución | Impacto | Prioridad | Status |
|---|----------|-----------|----------|--------------|---------|-----------|--------|
| **C1** | Heurística "si > 2" sin validación | core/calculos.py | Opción A Mejorada | Validación simple | ✅ BAJO (solo logs) | P0 | 🔄 IN-PROGRESS |

**Desglose:**
- **Componente afectado:** core/calculos.py::normalizar_cumplimiento()
- **Cambio:** Remover heurística, dejar validación de rango
- **Tipo solución:** Validación + logging (no cambio de lógica de negocio)
- **Impacto en sistema:** ✅ BAJO - No cambia resultados (datos ya válidos)
- **Backward compatibility:** ✅ SÍ - Si entrada ∈ [0,1.3] → salida idéntica
- **Riesgo implementación:** ✅ BAJO - Solo añade validación defensiva

---

## 📝 ESPECIFICACIÓN TÉCNICA

### Función Mejorada: normalizar_cumplimiento()

**Ubicación:** `core/calculos.py` líneas 17-23

**Comportamiento:**
1. Si `valor` es NaN → retorna NaN ✅
2. Si `valor` es string → intenta convertir ✅
3. Si `valor` < 0 o > 1.3 → log warning + retorna NaN
4. Si `valor` ∈ [0, 1.3] → retorna valor sin modificar ✅

**Testing:**
```python
# Tests esperados
assert normalizar_cumplimiento(0.5) == 0.5     # Normal
assert normalizar_cumplimiento(1.3) == 1.3     # Max
assert normalizar_cumplimiento(0.0) == 0.0     # Min
assert pd.isna(normalizar_cumplimiento(np.nan))  # NaN in
assert pd.isna(normalizar_cumplimiento(1.4))   # Fuera de rango
assert pd.isna(normalizar_cumplimiento(-0.1))  # Fuera de rango
assert pd.isna(normalizar_cumplimiento("abc")) # Invalid string
assert normalizar_cumplimiento("0.95") == 0.95 # Valid string
```

---

## 🎯 DEPENDENCIAS AFECTADAS

```
core/calculos.py::normalizar_cumplimiento()
    ↓
services/data_loader.py::_aplicar_calculos_cumplimiento() [línea 281]
    ↓
cargar_dataset() [caché ttl=300]
    ↓
Todas 9 páginas Streamlit
```

**Cadena de impacto:** CRÍTICA pero SEGURA (solo añade validación)

---

## ⚠️ CONSIDERACIONES

### Por Qué Opción A Mejorada vs A Simple

| Aspecto | Opción A Simple | Opción A Mejorada |
|---------|-----------------|-------------------|
| **Heurística** | ❌ Removida | ❌ Removida |
| **Validación** | ❌ Ninguna | ✅ Rango [0,1.3] |
| **Logging** | ❌ No | ✅ Sí (warnings) |
| **Esfuerzo** | 0.5h | 1h |
| **Seguridad** | Media | Alta |

**Ventaja:** Detecta anomalías futuras sin romper código actual.

---

## ✅ CHECKLIST IMPLEMENTACIÓN

### Pre-Implementación
- [ ] Crear rama feature/normalizar-cumplimiento-fix
- [ ] Backup de core/calculos.py actual
- [ ] Verificar que Cumplimiento siempre está en [0, 1.3]

### Implementación
- [ ] Actualizar función normalizar_cumplimiento() en core/calculos.py
- [ ] Agregar logger.warning() para valores fuera de rango
- [ ] Actualizar docstring con comportamiento
- [ ] Agregar constante RANGO_CUMPLIMIENTO en core/config.py

### Testing
- [ ] Crear tests/test_calculos.py con 8 casos
- [ ] Ejecutar: `pytest tests/test_calculos.py::test_normalizar_cumplimiento`
- [ ] Verificar logs en data_loader.py

### Validación
- [ ] Smoke test en todas 9 páginas (sin errores)
- [ ] Verificar que no hay warnings en dataset actual
- [ ] Comparar antes/después resultados (deben ser idénticos)

### Documentación
- [ ] Actualizar README.md (si aplica)
- [ ] Añadir nota en core/calculos.py sobre cambio
- [ ] Documentar en CHANGELOG

---

## 📅 CRONOGRAMA

| Tarea | Esfuerzo | Fecha Estimada |
|-------|----------|-----------------|
| Implementación | 1h | 21 abr 2026 |
| Testing | 1h | 21 abr 2026 |
| Validación | 0.5h | 21 abr 2026 |
| **Total** | **2.5h** | **~3h desde ahora** |

---

## 🎓 LECCIONES APRENDIDAS

1. **Validación de datos > Heurísticas:** Validar siempre es mejor que asumir
2. **Two-column pattern:** Cumplimiento (normalizado) + Cumplimiento Real (crudo) es correcto
3. **Logging defensivo:** Agregar warnings sin romper codigo es buena práctica

---

## 🔄 PRÓXIMA FASE

Después de implementar Problema #1 (Opción A Mejorada):

**Problema #2 (Queue):** 8 Duplicados de categorizar_cumplimiento()
- Ubicación: 4+ módulos
- Impacto: Inconsistencia de criterios
- Propuesta: Consolidar en core/semantica.py

---

## ✍️ FIRMAS DIGITALES

| Rol | Decisión | Fecha | Status |
|-----|----------|-------|--------|
| **Usuario/Arquitecto** | ✅ Opción A Mejorada | 21 abr 2026 | APROBADA |
| **Implementador** | PENDIENTE | TBD | En Queue |
| **QA/Validación** | PENDIENTE | TBD | En Queue |

---

**DOCUMENTO FORMALIZADO - LISTO PARA IMPLEMENTACIÓN**

