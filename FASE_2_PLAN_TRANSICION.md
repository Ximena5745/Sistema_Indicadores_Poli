# 🚀 TRANSICIÓN A FASE 2: BÚSQUEDA DE DUPLICACIONES

**De:** FASE 1 (Centralización de Cálculos) ✅ COMPLETADA  
**A:** FASE 2 (Eliminación de Duplicaciones)  
**Fecha:** 21 de abril de 2026  

---

## 📋 ESTADO ACTUAL: FASE 1

```
✅ FUNCIONES CENTRALIZADAS (2):
   ├─ categorizar_cumplimiento() en core/semantica.py
   └─ recalcular_cumplimiento_faltante() en core/semantica.py

✅ CÓDIGO LIMPIADO:
   ├─ _nivel_desde_cumplimiento() eliminada
   ├─ Lógica inline removida
   └─ core/config.py con umbrales sincronizados

✅ INTEGRACIONES COMPLETADAS:
   ├─ data_loader.py: usa función oficial
   └─ strategic_indicators.py: usa función oficial

✅ TESTS EXITOSOS:
   ├─ 66 tests nuevos
   ├─ 44+ tests pre-existentes
   └─ 110+ tests pasando (100%)

✅ VALIDACIONES PASADAS:
   ├─ Auditoría: 15/15 ✅
   ├─ Datos: 2/2 indicadores correctos ✅
   └─ Coverage: 85%+ en core ✅

STATUS: 🟢 LISTA PARA FASE 2
```

---

## 🎯 FASE 2: BÚSQUEDA DE DUPLICACIONES (3-4 días)

### Según Auditoría Previa: 8 DUPLICACIONES ENCONTRADAS

**Del documento AUDITORIA_COMPLETA_SGIND.md:**

```
1. ✓ normalizar_cumplimiento()
   └─ Encontrada en: core/calculos.py, resumen_por_proceso.py (+ otros)
   └─ Causa: Heurística ambigua (si > 2 → divide /100)

2. ✓ categorizar_cumplimiento() [2 VERSIONES DIVERGENTES]
   ├─ Versión A: core/calculos.py
   ├─ Versión B: core/semantica.py ← OFICIAL (ahora)
   └─ Problema: Versión A no soporta Plan Anual

3. ✓ _nivel_desde_cumplimiento()
   └─ Ubicación: services/strategic_indicators.py:55
   └─ Status: ✅ ELIMINADA EN FASE 1

4. ✓ _map_level() [similar a categorizar]
   └─ Ubicación: streamlit_app/pages/resumen_general.py
   └─ Problema: Lógica duplicada, no detecta Plan Anual

5. ✓ obtener_ultimo_registro()
   └─ Ubicación: core/calculos.py:151-167
   └─ Duplicada en: otros dashboards (implicit)

6. ✓ _recalc_cumpl() [lambda inline]
   └─ Ubicación: services/data_loader.py:248
   └─ Status: ✅ REMOVIDA/REFACTORIZADA EN FASE 1

7. ✓ load_cierres() [mezcla carga + cálculo]
   └─ Ubicación: services/strategic_indicators.py:85-195
   └─ Problema: Viola SoC (Separation of Concerns)

8. ✓ recalcifiación de cumplimiento [inline en 12 dashboards]
   └─ Ubicación: streamlit_app/pages/ (9 páginas + 3 HTML)
   └─ Problema: Lógica inline, no centralizada

TOTAL: 8 duplicaciones
YA RESUELTA EN FASE 1: 3 ✅ (_nivel_desde, _recalc_cumpl, categorizar)
PENDIENTE PARA FASE 2: 5 (normalizar, _map_level, obtener_ultimo, load_cierres, inline en dashboards)
```

---

## 📊 PLAN FASE 2

### Paso 1: Identificar Todas las Duplicaciones (1 día)

```
TAREAS:
├─ [ ] Buscar todas las invocaciones de "normalizar_cumplimiento"
├─ [ ] Buscar todas las invocaciones de "categorizar_cumplimiento"
├─ [ ] Buscar todas las invocaciones de "_map_level"
├─ [ ] Buscar todas las invocaciones de "obtener_ultimo_registro"
├─ [ ] Buscar todas las lógicas de recálculo inline
├─ [ ] Crear matriz de: ubicación × función × tipo
└─ [ ] Documentar FASE_2_MAPEO_DUPLICACIONES.md

ENTREGA:
└─ Documento con 100% de duplicaciones identificadas
```

### Paso 2: Consolidar Funciones Centrales (1 día)

```
TAREAS:
├─ [ ] core/semantica.py: Agregar normalizar_cumplimiento()
├─ [ ] core/semantica.py: Agregar obtener_ultimo_registro()
├─ [ ] core/semantica.py: Agregar métodos auxiliares
├─ [ ] core/calculos.py: Deprecar versiones viejas (si existen)
└─ [ ] Crear tests para funciones consolidadas

FUNCIONES FINALES:
├─ categorizar_cumplimiento() ← OFICIAL (ya existe)
├─ recalcular_cumplimiento_faltante() ← OFICIAL (ya existe)
├─ normalizar_cumplimiento() ← NUEVA
├─ obtener_ultimo_registro() ← NUEVA
└─ [otras según se descubran]

ENTREGA:
└─ core/semantica.py actualizado con 4+ funciones centrales
```

### Paso 3: Reemplazar en Todos los Dashboards (1 día)

```
TAREAS:
├─ [ ] data_loader.py: reemplazar normalizar_cumplimiento()
├─ [ ] strategic_indicators.py: reemplazar en load_cierres()
├─ [ ] resumen_general.py: reemplazar _map_level() por función oficial
├─ [ ] resumen_por_proceso.py: reemplazar lógica inline
├─ [ ] cmi_estrategico.py: reemplazar lógica inline
├─ [ ] gestion_om.py: reemplazar lógica inline
├─ [ ] plan_mejoramiento.py: reemplazar lógica inline
├─ [ ] tablero_operativo.py: reemplazar lógica inline
├─ [ ] seguimiento_reportes.py: reemplazar lógica inline
├─ [ ] pdi_acreditacion.py: reemplazar lógica inline
├─ [ ] diagnostico.py: reemplazar lógica inline
├─ [ ] dashboard_profesional.html: reemplazar lógica JS (si aplica)
└─ [ ] dashboard_mini.html: reemplazar lógica JS (si aplica)

UBICACIONES: 13 archivos (9 Streamlit + 3 HTML + 1 core)

ENTREGA:
└─ Todos los dashboards usando funciones centralizadas
```

### Paso 4: Tests de Integración (0.5 días)

```
TAREAS:
├─ [ ] Tests para normalizar_cumplimiento()
├─ [ ] Tests para obtener_ultimo_registro()
├─ [ ] Tests de integración con data_loader
├─ [ ] Tests de integración con strategic_indicators
├─ [ ] Tests de integración con dashboards (si posible)
└─ [ ] Validar cobertura ≥ 80%

ENTREGA:
└─ 30-50 tests nuevos (100% pasando)
```

### Paso 5: Validación Final (0.5 días)

```
TAREAS:
├─ [ ] Auditoría: verificar 0 duplicaciones
├─ [ ] Auditoría: verificar 100% uses función centralizada
├─ [ ] Auditoría: verificar 0 lógica inline
├─ [ ] Datos: validar cambios en datos reales
├─ [ ] Performance: verificar no hay degradación
└─ [ ] Documentación: crear FASE_2_RESUELTO.md

ENTREGA:
└─ Auditoría 100% pasada, datos validados
```

---

## 📈 DEPENDENCIAS

### De FASE 1 ✅
- [x] categorizar_cumplimiento() centralizada
- [x] recalcular_cumplimiento_faltante() centralizada
- [x] core/config.py con umbrales sincronizados
- [x] core/semantica.py creado

### Para FASE 2
- [ ] Continuidad de core/semantica.py
- [ ] Tests de FASE 1 pasando (prerequisito)
- [ ] No hay conflictos con FASE 1

---

## 📋 ESTIMACIÓN: FASE 2

```
ACTIVIDADES:
├─ Mapeo de duplicaciones:      1 día (8h)
├─ Consolidación funciones:     1 día (8h)
├─ Reemplazos en código:        1 día (8h)
├─ Tests de integración:        0.5 días (4h)
├─ Validación final:            0.5 días (4h)
└─ TOTAL:                        4 días (32h)

TIMELINE: 4 días laborales
INICIO SUGERIDO: 22 de abril
FIN SUGERIDO: 25 de abril
```

---

## 🎯 OBJETIVOS FASE 2

```
OBJETIVO 1: Eliminar duplicaciones
├─ De: 8 copias de "categorizar_cumplimiento" + otras
└─ A: 1 función oficial + imports en todos lados

OBJETIVO 2: Centralizar core/semantica.py
├─ De: 2 funciones
└─ A: 4+ funciones (normalizar, categorizar, recalcular, etc.)

OBJETIVO 3: Limpiar todos los dashboards
├─ De: Lógica inline en 12 archivos
└─ A: Imports de funciones centralizadas

OBJETIVO 4: 100% cobertura de migraciones
├─ De: 13 archivos divergentes
└─ A: 13 archivos sincronizados

OBJETIVO 5: Validación exitosa
├─ De: 8 duplicaciones encontradas
└─ A: 0 duplicaciones (100% consolidado)
```

---

## 📊 MÉTRICAS FASE 2

### Antes
```
Duplicaciones:          8
Versiones de categorizar: 2
Lógica inline:          12 lugares
Centralización:         0%
Coverage:               85%
```

### Después
```
Duplicaciones:          0
Versiones de categorizar: 1 ✅
Lógica inline:          0
Centralización:         100% ✅
Coverage:               90%+ ✅
```

---

## ✅ PRÓXIMAS ACCIONES

### Inmediato (Hoy)
- [x] ✅ Validar FASE 1 completada
- [ ] Revisar auditoría de duplicaciones
- [ ] Preparar plan FASE 2

### Mañana (22 de abril)
- [ ] Iniciar FASE 2 - Mapeo de duplicaciones
- [ ] Crear FASE_2_MAPEO_DUPLICACIONES.md
- [ ] Identificar 100% de duplicaciones

### Semana (22-25 de abril)
- [ ] Completar FASE 2 (4 días)
- [ ] 0 duplicaciones restantes
- [ ] 100% funciones centralizadas
- [ ] Validación final exitosa

---

## 📄 DOCUMENTOS A GENERAR EN FASE 2

```
✅ FASE_2_MAPEO_DUPLICACIONES.md
   └─ Matriz completa de duplicaciones encontradas

✅ FASE_2_CONSOLIDACION.md
   └─ Plan detallado de consolidación

✅ FASE_2_MIGRACIONES.md
   └─ Estado de cada migración (13 archivos)

✅ FASE_2_TESTS.md
   └─ Tests nuevos (30-50 tests)

✅ FASE_2_VALIDACION.md
   └─ Auditoría final

✅ FASE_2_RESUELTO.md
   └─ Resumen final de FASE 2
```

---

## 🎉 VISIÓN FINAL (FASE 1 + FASE 2)

```
DESPUÉS DE FASE 2:
├─ 1 core/semantica.py centralizado con 4+ funciones
├─ 13 archivos usando funciones centralizadas
├─ 0 duplicaciones
├─ 0 lógica inline
├─ 100%+ funciones soportan Plan Anual
├─ 150+ tests (100% pasando)
├─ 90%+ coverage en core
└─ Sistema listo para FASE 3 (Refactorización de Carga)
```

---

**Status Actual:** FASE 1 ✅ COMPLETADA  
**Status Próximo:** FASE 2 ⏳ PENDIENTE  
**Readiness:** 🟢 LISTO PARA INICIAR  

---

*Documento generado por Auditoría Exhaustiva del Sistema de Indicadores*  
*Fecha: 21 de abril de 2026*
