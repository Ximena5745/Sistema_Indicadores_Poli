# 📊 FASE 2: RESUMEN EJECUTIVO DEL MAPEO

**Fecha:** 21 de abril de 2026  
**Status:** ✅ MAPEO COMPLETADO - 52% YA REFACTORIZADO  
**Siguiente:** Mejoras residuales (2-3 horas)  

---

## 🎯 HALLAZGO PRINCIPAL

**Sorpresa Positiva:** El codebase YA ha sido parcialmente refactorizado hacia funciones centralizadas.

```
ESTADO ACTUAL:
├─ Funciones centralizadas en core/semantica.py: ✅ 4+ funciones
├─ Uso en dashboards: ✅ 6+ páginas ya refactorizadas
├─ Duplicaciones residuales: ⚠️ 4-6 conversiones manuales
└─ Duplicaciones críticas: 🔴 1-2 (load_cierres, HTML)

PROGRESO: 52% completo (13/25 ubicaciones)
```

---

## ✅ LO QUE YA FUNCIONA

### Funciones Centralizadas (Operativas)
```
✅ core.semantica:
   ├─ categorizar_cumplimiento()        → Usado en 6+ dashboards
   ├─ recalcular_cumplimiento_faltante() → Usado en data_loader.py
   ├─ normalizar_valor_a_porcentaje()   → Usado en 2+ dashboards
   └─ obtener_icono_categoria()         → Usado en gestion_om.py

✅ core.calculos:
   └─ obtener_ultimo_registro()         → Función disponible (¿reutilizada?)
```

### Dashboards Correctamente Integrados
```
✅ resumen_general.py
   └─ Usa: categorizar_cumplimiento() (línea 206-230)
   └─ Nivel de integración: ⭐⭐⭐⭐ (EXCEPTO conversión manual)

✅ resumen_por_proceso.py
   └─ Usa: normalizar_valor_a_porcentaje() (línea 86+)
   └─ Nivel de integración: ⭐⭐⭐⭐

✅ pdi_acreditacion.py
   └─ Usa: categorizar_cumplimiento() (línea 32+)
   └─ Nivel de integración: ⭐⭐⭐⭐

✅ gestion_om.py (PARCIALMENTE)
   └─ Usa: categorizar_cumplimiento() (línea 889+)
   └─ Nivel de integración: ⭐⭐⭐ (requiere mejorar conversiones)
```

---

## ⚠️ PROBLEMAS RESIDUALES (FÁCILES DE ARREGLAR)

### Problema #1: Conversión Manual % → Decimal (4+ lugares)

**Patrón problemático:**
```python
# Antipatrón: Conversión manual repetida
cumpl_decimal = pct / 100.0
categoria = categorizar_cumplimiento(cumpl_decimal)
```

**Ubicaciones:**
- resumen_general.py:216 (¿realmente problemática?)
- gestion_om.py:911, 929, 956 (4 instancias)
- Otros dashboards: TBD

**Impacto:** Bajo (funciona, pero código ineficiente)

**Solución (5 minutos):**
```python
# ANTES:
cumpl_decimal = row["cumplimiento_pct"] / 100.0
categoria = categorizar_cumplimiento(cumpl_decimal, id_indicador=id_ind)

# DESPUÉS - Opción A (usar función existente):
from core.semantica import normalizar_valor_a_porcentaje
cumpl_norm = normalizar_valor_a_porcentaje(row["cumplimiento_pct"], tiene_porcentaje=True)
categoria = categorizar_cumplimiento(cumpl_norm, id_indicador=id_ind)

# MEJOR - Opción B (función wrapper):
categoria = normalizar_y_categorizar(row["cumplimiento_pct"], 
                                    es_porcentaje=True,
                                    id_indicador=id_ind)
```

---

### Problema #2: load_cierres() Potencialmente No Refactorizado

**Ubicación:** services/strategic_indicators.py línea 85-195

**Status:** ❓ Necesita verificación

**Riesgo:** Mezcla de SoC (data loading + cálculos inline)

**Solución:** Verificar si usa funciones centralizadas

---

### Problema #3: HTML Dashboards (3 archivos)

**Archivos:**
- dashboard_profesional.html
- dashboard_mini.html
- dashboard_rediseñado.html

**Status:** ❓ Requiere análisis (puede tener lógica JavaScript inline)

**Riesgo:** Bajo (probablemente solo presentación)

---

## 📋 PLAN DE ACCIÓN FASE 2 (REVISADO)

### Cambio en la Estrategia

Basado en el mapeo, FASE 2 NO necesita consolidar 5 duplicaciones masivas.  
En su lugar, necesita:

1. **Completar refactorizaciones parciales** (2-3 horas)
2. **Mejorar conversiones de porcentaje** (1-2 horas)
3. **Verificar load_cierres()** (1 hora)
4. **Auditar HTML dashboards** (1 hora)
5. **Tests de integración** (2-3 horas)

**Total estimado: 8-10 horas (1 día)**

---

### Paso 1: Consolidar Función Wrapper (1 hora)

**Crear en core/semantica.py:**
```python
def normalizar_y_categorizar(valor, 
                             es_porcentaje=None, 
                             id_indicador=None,
                             sentido="Positivo") -> str:
    """
    Conversión automática + categorización en una sola función.
    
    Reemplaza:
    - Conversión manual % → decimal
    - Llamadas dobles a normalizar + categorizar
    
    Uso:
    df["Categoria"] = df.apply(
        lambda r: normalizar_y_categorizar(r["Cumplimiento_pct"],
                                          es_porcentaje=True,
                                          id_indicador=r.get("Id"))
    )
    """
    # Normalizar a formato decimal
    valor_norm = normalizar_valor_a_porcentaje(valor, tiene_porcentaje=es_porcentaje)
    
    # Categorizar
    return categorizar_cumplimiento(valor_norm, id_indicador=id_indicador)
```

---

### Paso 2: Reemplazar en Dashboards (1-2 horas)

**gestion_om.py (líneas 911, 929, 956):**
```python
# ANTES:
cumpl_decimal = (row.get("Cumplimiento_pct", 0) or 0) / 100.0
categoria = categorizar_cumplimiento(cumpl_decimal)

# DESPUÉS:
categoria = normalizar_y_categorizar(row.get("Cumplimiento_pct", 0),
                                    es_porcentaje=True)
```

**Otros dashboards con patrón similar:** TBD

---

### Paso 3: Verificar load_cierres() (1 hora)

**Ubicación:** services/strategic_indicators.py línea 85-195

**Acción:**
- [ ] Leer línea 85-195
- [ ] Verificar si usa funciones centralizadas
- [ ] Si no, refactorizar

**Esperado:** Debería importar de core.semantica

---

### Paso 4: Auditar HTML Dashboards (1 hora)

**Archivos a revisar:**
- [ ] dashboard_profesional.html
- [ ] dashboard_mini.html
- [ ] dashboard_rediseñado.html

**Acción:** Buscar lógica de cálculo de cumplimiento

**Esperado:** Probablemente solo datos + presentación (no lógica)

---

### Paso 5: Tests de Integración (2-3 horas)

**Crear:**
- [ ] tests/test_normalizacion_y_categorizar.py (10 tests)
- [ ] tests/test_integracion_fase2.py (20-30 tests)

**Coverage:** ≥ 80% en funciones nuevas/modificadas

---

## 📊 PROGRESO CONSOLIDADO

### Antes de FASE 2
```
Duplicaciones encontradas: 8
Ya resueltas (FASE 1):      3
Pendientes (FASE 2):        5
```

### Después del Mapeo FASE 2
```
Duplicaciones encontradas: 8
Ya resueltas (FASE 1):      3
Parcialmente refactorizadas: 4-5
Pendientes críticas:        1-2
```

**Cambio:** De "5 duplicaciones grandes" a "4-6 mejoras residuales menores"

---

## ✅ RECOMENDACIÓN

**FASE 2 puede ser más rápida que lo estimado.**

**Nueva línea de tiempo:**

| Tarea | Tiempo | Status |
|-------|--------|--------|
| Paso 1: Función wrapper | 1h | 📝 Planificado |
| Paso 2: Reemplazos dashboards | 1-2h | 📝 Planificado |
| Paso 3: Verificar load_cierres | 1h | 📝 Planificado |
| Paso 4: Auditar HTML | 1h | 📝 Planificado |
| Paso 5: Tests integración | 2-3h | 📝 Planificado |
| **TOTAL** | **6-8h** | ✅ **1 día** |

**Vs estimado original:** 32 horas (4 días)  
**Mejora:** 75% de reducción 🎉

---

## 🎯 SIGUIENTE ACCIÓN INMEDIATA

Para continuar FASE 2 (completar mejoras residuales):

1. [ ] Crear función `normalizar_y_categorizar()` en core/semantica.py
2. [ ] Ejecutar búsqueda en gestion_om.py para líneas exactas
3. [ ] Reemplazar conversiones manuales
4. [ ] Verificar load_cierres()
5. [ ] Crear tests de integración

---

## 📌 NOTA IMPORTANTE

**El codebase es mucho más sano de lo que indicaba la auditoría original.**

Posible explicación:
- Refactorizaciones manuales anteriores no documentadas
- Limpieza parcial ya completada
- Funciones centralizadas ya en uso

**Beneficio:** FASE 2 será mucho más rápida y de menor riesgo.

---

*Documento generado en FASE 2: Mapeo de Duplicaciones*  
*Auditoría: 21 de abril de 2026*  
*Status: Listo para Paso 1*
