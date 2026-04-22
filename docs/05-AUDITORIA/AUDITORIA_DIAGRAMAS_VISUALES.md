# 🎨 DIAGRAMAS VISUALES: ARQUITECTURA ACTUAL VS PROPUESTA

**Documento:** Visualización de la auditoría con diagramas

---

## 1️⃣ DIAGRAMA: Flujo Actual (PROBLEMÁTICO)

```
┌─────────────────────────────────────────────────────────────┐
│                    EXCEL CONSOLIDADO                        │
│            (Resultados Consolidados.xlsx)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  services/data_loader.py           │
        │  _aplicar_calculos_cumplimiento()  │
        │                                    │
        │  ✅ Usa: categorizar_cumplimiento()│
        │     (core/calculos.py:26)          │
        └────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌─────────┐  ┌──────────────┐  ┌──────────┐
    │  Page 1 │  │   Page 2     │  │ Page 3-9 │
    │ (Bueno) │  │  (Bueno)     │  │ (Bueno)  │
    └─────────┘  └──────────────┘  └──────────┘
         │               │
         └───────────────┼─────────────────────┐
                         │                     │
                         ▼                     ▼
            ┌────────────────────┐   ┌──────────────────┐
            │strategic_indicators│   │ PERO: strategic_ │
            │.load_cierres()     │   │ indicators TAMBIÉN│
            │                    │   │ categoriza datos  │
            │❌ Usa:             │   │                  │
            │_nivel_desde_...()  │   │❌ CON FUNCIÓN    │
            │(NO Plan Anual!)    │   │   DEFECTUOSA     │
            └────────────────────┘   └──────────────────┘
                     │
                     ▼
            ┌─────────────────────┐
            │  Datos INCONSISTENTES│
            │  Plan Anual mal      │
            │  categorizados       │
            └─────────────────────┘
```

**PROBLEMAS:**
- 🔴 Dos funciones `categorizar_cumplimiento()` (divergentes)
- 🔴 `_nivel_desde_cumplimiento()` NO soporta Plan Anual
- 🟡 12 dashboards con cálculos inline

---

## 2️⃣ DIAGRAMA: Flujo Propuesto (CENTRALIZADO)

```
┌─────────────────────────────────────────────────────────────┐
│                    EXCEL CONSOLIDADO                        │
│            (Resultados Consolidados.xlsx)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  services/data_loader.py           │
        │  _aplicar_calculos_cumplimiento()  │
        │                                    │
        │  ✅ Importa:                       │
        │     from core.calculos_oficial     │
        │     import categorizar_cumplimiento│
        └────────────────────────────────────┘
                         │
         ┌───────────────┼────────────────────────────┐
         │               │                            │
         ▼               ▼                            ▼
    ┌─────────┐  ┌──────────────┐  ┌─────────────────────┐
    │ Page 1-9│  │ strategic_   │  │core/calculos_oficial│
    │(Todos)  │  │ indicators   │  │(ÚNICA FUENTE)       │
    │         │  │              │  │                     │
    │✅ Import│  │✅ Import:    │  │✅ Función oficial:  │
    │función  │  │  categorizar_│  │  categorizar_        │
    │oficial  │  │  cumplimiento│  │  cumplimiento()     │
    │         │  │  ()          │  │  (con Plan Anual)   │
    └─────────┘  └──────────────┘  │                     │
         │            │             │✅ Función oficial:  │
         │            │             │  calcular_          │
         └────────────┼─────────────┤  cumplimiento()     │
                      │             │  (cases especiales) │
                      └─────────────┤                     │
                                    │✅ Función oficial:  │
                                    │  calcular_tendencia │
                                    │  ()                 │
                                    └─────────────────────┘
                                             │
                                             ▼
                                    ┌─────────────────────┐
                                    │ Datos CONSISTENTES  │
                                    │ Plan Anual correcto │
                                    │ Sin duplicación     │
                                    └─────────────────────┘
```

**BENEFICIOS:**
- ✅ 1 única función `categorizar_cumplimiento()`
- ✅ Todos los dashboards usan lo mismo
- ✅ Plan Anual siempre correcto
- ✅ Cambio en 1 lugar = efecto en 100% datos

---

## 3️⃣ DIAGRAMA: Impacto de Cambiar Umbral

### ANTES (Actual - Problematico)

```
CAMBIAR: Umbral Peligro de 0.80 a 0.75

AFECTA:
  ❌ core/calculos.py:26
  ❌ core/semantica.py:56
  ❌ services/strategic_indicators.py:55
  ❌ resumen_general.py (inline)
  ❌ resumen_por_proceso.py (inline)
  ❌ cmi_estrategico.py (inline)
  ❌ gestion_om.py (inline)
  ❌ plan_mejoramiento.py (inline)
  ❌ pdi_acreditacion.py (inline)
  ❌ diagnostico.py (inline)
  ❌ seguimiento_reportes.py (inline)
  ❌ tablero_operativo.py (inline)
  
TOTAL: 12 LUGARES
TIEMPO: ~30 minutos
RIESGO: Olvidar uno ➜ Inconsistencia ⚠️
```

### DESPUÉS (Propuesto - Centralizado)

```
CAMBIAR: Umbral Peligro de 0.80 a 0.75

AFECTA:
  ✅ core/calculos_oficial.py:1
  
TOTAL: 1 LUGAR
TIEMPO: 1 minuto
RIESGO: 0 ✅
```

**IMPACTO:** -97% en tiempo, -100% en riesgo

---

## 4️⃣ DIAGRAMA: Dependencias de Módulos

### ACTUAL (Spaghetti - Dependencias cruzadas)

```
┌──────────────────────────────────────────────────────────┐
│                    config.py                              │
│         (UMBRAL_PELIGRO, UMBRAL_ALERTA, ...)            │
└─────┬────────────────┬──────────────┬────────────────┬───┘
      │                │              │                │
      ▼                ▼              ▼                ▼
┌──────────┐    ┌─────────────┐  ┌─────────┐   ┌──────────────┐
│core/     │    │core/        │  │services/│   │scripts/etl/  │
│calculos. │    │semantica.py │  │data_    │   │cumplimiento. │
│py        │    │             │  │loader.py    │py            │
│          │    │ (REDUNDANTE)│  │        │   │              │
│❌ v1     │    │ ❌ v2       │  │✅ USA  │   │✅ MEJOR IMPL │
│Categorizar     │Categorizar  │  │ v1 Y v2    │_calc_cumpl()│
│cumplimiento()  │cumplimiento │  │            │             │
└────┬───────────┴────────┬────┴──────┬────────┴──────┬───────┘
     │                    │           │               │
     └────────────┬───────┴───────────┴───────────────┘
                  │
           ┌──────▼─────────┐
           │strategic_      │
           │indicators.py   │
           │❌ _nivel_desde_│
           │cumplimiento()  │
           │(DEFECTUOSA)    │
           └────────────────┘


PROBLEMA: 5 implementaciones diferentes de la misma lógica
RESULTADO: Divergencia, inconsistencia
```

### PROPUESTO (Centralizado - Hub and Spoke)

```
                    ┌──────────────────────┐
                    │    config.py         │
                    │(UMBRALES ÚNICOS)     │
                    └──────────┬───────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────┐
        │  core/calculos_oficial.py (ÚNICA HUB)   │
        │                                          │
        │  ✅ categorizar_cumplimiento()           │
        │  ✅ calcular_cumplimiento()              │
        │  ✅ calcular_tendencia()                 │
        │  ✅ calcular_salud_institucional()       │
        │  ✅ calcular_meses_en_peligro()          │
        │                                          │
        │  → Soporte Plan Anual                    │
        │  → Casos especiales                      │
        │  → Logging centralizado                  │
        │  → Tests exhaustivos                     │
        └──────────────────────────────────────────┘
           │      │      │       │        │
    ┌──────▼──┬───▼──┬───▼──┬───▼──┬────▼──┐
    │ data_   │strat │ Page │ Page │ tests │
    │ loader  │ egic │ 1-12 │      │       │
    │  .py    │ .py  │      │      │       │
    │         │      │      │      │       │
    │ ✅ import│ ✅ import│ ✅ import│      │
    └─────────┴──────┴──────┴──────┴───────┘

BENEFICIO: Todo fluye desde 1 fuente
RESULTADO: Consistencia garantizada
```

---

## 5️⃣ DIAGRAMA: Categorización Plan Anual - Antes vs Después

### ANTES (Divergente)

```
Indicador ID=373 (Plan Anual)
Cumplimiento = 0.947 (94.7%)

FLUJO 1: En data_loader.py
├─ categorizar_cumplimiento(0.947, id_indicador="373")
├─ Detecta Plan Anual ✅
├─ Aplica umbral PA (0.95)
├─ Resultado: "Cumplimiento" ✅ CORRECTO
└─ Se muestra en: resumen_general, cmi_estrategico, etc.

FLUJO 2: En strategic_indicators.py
├─ _nivel_desde_cumplimiento(0.947)
├─ NO detecta Plan Anual ❌
├─ Aplica umbral Regular (1.00)
├─ Resultado: "Alerta" ❌ INCORRECTO
└─ Se muestra en: strategic_indicators

USUARIO VE:
  Page A: "Cumplimiento" ✅
  Page B: "Alerta" ❌
  → CONFUSIÓN "¿Cuál es la verdad?"
```

### DESPUÉS (Centralizado)

```
Indicador ID=373 (Plan Anual)
Cumplimiento = 0.947 (94.7%)

TODOS LOS FLUJOS: Usan core/calculos_oficial.py
├─ categorizar_cumplimiento(0.947, id_indicador="373")
├─ Detecta Plan Anual ✅
├─ Aplica umbral PA (0.95)
├─ Resultado: "Cumplimiento" ✅ CORRECTO
└─ Se muestra en: TODAS las páginas

USUARIO VE:
  Page A: "Cumplimiento" ✅
  Page B: "Cumplimiento" ✅
  → CONSISTENCIA "Todos los datos alineados"
```

---

## 6️⃣ DIAGRAMA: Pipeline Completo Post-Refactor

```
┌─────────────────────────────────────────────────────────────┐
│          EXCEL (Resultados Consolidados.xlsx)              │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ data_loader.py       │
         │ cargar_dataset()     │
         │                      │
         │ Paso 1-3: I/O        │
         │ Paso 4: Fórmulas     │
         │ Paso 5: Cálculos     │
         │                      │
         │ Importa:             │
         │ ✅ from core.calculos│
         │    _oficial import   │
         │    calcular_*, ...   │
         └──────────────────────┘
                    │
      ┌─────────────┼─────────────┐
      │             │             │
      ▼             ▼             ▼
  ┌────────────────────────────────────────┐
  │  st.cache_data(ttl=300)                │
  │  → DataFrame con:                      │
  │    • Cumplimiento (calculado)          │
  │    • Categoría (oficial)               │
  │    • Tendencia (oficial)               │
  │    • Salud (oficial)                   │
  └────────────────────────────────────────┘
      │
      └─────────────┬─────────────────────┐
                    │                     │
    ┌───────────────▼────────────────┐   ▼
    │ Todos los Dashboards (9 pages) │ Tests suite
    │ ✅ Usan datos oficiales        │ (50+ cases)
    │ ✅ Importan funciones oficiales│
    │ ✅ 0 lógica inline             │
    └────────────────────────────────┘
                    │
                    ▼
    ┌────────────────────────────────┐
    │ Datos Consistentes GARANTIZADOS│
    │ Plan Anual: CORRECTO           │
    │ Cambios: RÁPIDOS (1 lugar)     │
    │ Deuda técnica: ELIMINADA       │
    └────────────────────────────────┘
```

---

## 7️⃣ DIAGRAMA: Matriz de Cambios Requeridos

```
┌──────────────────┬────────┬────────┬─────────┐
│ Archivo          │ Tipo   │ LOC    │ Tiempo  │
├──────────────────┼────────┼────────┼─────────┤
│ CREAR:           │        │        │         │
│ core/            │        │        │         │
│ calculos_        │ NUEVO  │ +200   │ 2h      │
│ oficial.py       │        │        │         │
│                  │        │        │         │
│ REEMPLAZAR:      │        │        │         │
│ services/        │        │        │         │
│ data_loader.py   │ -30    │ -25    │ 15m     │
│ línea 248        │ inline │ → 3    │         │
│                  │        │        │         │
│ services/        │        │        │         │
│ strategic_       │ -15    │ -10    │ 15m     │
│ indicators.py    │ defect │ → 5    │         │
│ línea 55         │        │        │         │
│                  │        │        │         │
│ 9 × pages/*      │ -12    │ -10    │ 45m     │
│                  │ inline │ → 5    │         │
│                  │        │        │         │
│ TESTS:           │        │        │         │
│ tests/           │ NUEVO  │ +300   │ 2h      │
│ test_calculos    │ suite  │        │         │
│                  │        │        │         │
├──────────────────┼────────┼────────┼─────────┤
│ TOTAL ESFUERZO   │        │ -450   │ 4.25h   │
│ (LOC reducidas)  │        │ LOC    │ (~P1)   │
└──────────────────┴────────┴────────┴─────────┘
```

---

## 8️⃣ DIAGRAMA: Matriz de Riesgos Pre vs Post Refactor

```
RIESGO: Plan Anual mal categorizado

ANTES:
  Probabilidad: ████████░░ (80% ALTO)
  Impacto:      ██████████ (100% CRÍTICO)
  Exposición:   80/100 = CRÍTICA 🔴

DESPUÉS:
  Probabilidad: █░░░░░░░░░ (10% BAJO)
  Impacto:      ██████████ (100% - no cambia)
  Exposición:   10/100 = BAJO 🟢

─────────────────────────────────────

RIESGO: Cambio de fórmula no propagado

ANTES:
  Probabilidad: ███████░░░ (70% ALTO)
  Impacto:      ████████░░ (80% ALTO)
  Exposición:   56/100 = ALTA 🟡

DESPUÉS:
  Probabilidad: ░░░░░░░░░░ (0% - 1 lugar!)
  Impacto:      ████████░░ (80% - igual)
  Exposición:   0/100 = NINGUNO ✅

─────────────────────────────────────

RIESGO: Test coverage insuficiente

ANTES:
  Probabilidad: ██████████ (100% SEGURO)
  Impacto:      ██████░░░░ (60% - bugs silenciosos)
  Exposición:   60/100 = MEDIA 🟡

DESPUÉS:
  Probabilidad: ░░░░░░░░░░ (0% - 80%+ coverage)
  Impacto:      ██████░░░░ (60% - igual)
  Exposición:   0/100 = BAJO ✅
```

---

## 9️⃣ DIAGRAMA: Timeline de Implementación

```
SEMANA 1: ANÁLISIS & DECISIÓN
├─ Lunes: Presentar auditoría
├─ Martes: Junta Directiva aprueba
├─ Miércoles: Crear rama `refactor/centralizacion`
└─ Viernes: Preparar documentación

SEMANA 2: DESARROLLO FASE 1 (P0 - CRÍTICO)
├─ Lunes-Martes: Crear core/calculos_oficial.py
│  └─ Función calcular_cumplimiento()
│  └─ Casos especiales (Meta=0, Ejec=0)
│
├─ Miércoles: Reemplazar en data_loader.py
│  └─ Eliminar lambda inline
│
├─ Jueves: Reemplazar en strategic_indicators.py
│  └─ Eliminar _nivel_desde_cumplimiento()
│  └─ Usar función oficial
│
└─ Viernes: Tests + Validación
   └─ Merge a develop

SEMANA 3: DESARROLLO FASE 2 (P1 - ALTA)
├─ Lunes-Miércoles: Actualizar 12 dashboards
│  └─ Eliminar inline
│  └─ Importar funciones
│
├─ Jueves: Crear tests exhaustivos
│  └─ 50+ test cases
│
└─ Viernes: Code review + Merge a develop

SEMANA 4: FASE 3 (P2 - DOCS) + DEPLOY
├─ Lunes-Martes: Documentación
│  └─ Guía "Cómo agregar indicador"
│  └─ Docstrings mejorados
│
├─ Miércoles: Final testing
│  └─ Validar pipeline completo
│
├─ Jueves: PR review + Merge a main
│
└─ Viernes: DEPLOY A PRODUCCIÓN ✅

```

---

## 🔟 DIAGRAMA: Ganancia de Mantenibilidad

```
ANTES: Duplicación = Cambios lentos

  ┌─ Cambio en calcular_cumplimiento
  │  ├─ Actualizar core/calculos.py ← 30 min
  │  ├─ Actualizar core/semantica.py
  │  ├─ Actualizar services/strategic_indicators.py
  │  ├─ Actualizar 9 dashboards
  │  ├─ Validar 9 dashboards
  │  └─ Riesgo: Olvidar uno ⚠️
  │
  └─ TOTAL: 30 minutos


DESPUÉS: Centralización = Cambios rápidos

  ┌─ Cambio en calcular_cumplimiento
  │  ├─ Actualizar core/calculos_oficial.py ← 1 minuto
  │  ├─ Ejecutar tests (auto-validación)
  │  └─ Deploy (1 minuto)
  │
  └─ TOTAL: 2 minutos

MEJORA: 30 min → 2 min = -93% ⏱️
```

---

## CONCLUSIÓN VISUAL

```
┌─────────────────────────────────────────────────────┐
│     ANTES: Arquitectura Dispersa (Frágil)          │
│                                                     │
│  ❌ Múltiples funciones de lo mismo                │
│  ❌ 12 lugares con lógica duplicada                │
│  ❌ Plan Anual mal soportado                       │
│  ❌ Cambios lentos (30 min)                        │
│  ❌ Riesgo de inconsistencia: ALTO                 │
└─────────────────────────────────────────────────────┘
                         │
                         │ REFACTORIZACIÓN
                         │ 44 horas
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│   DESPUÉS: Arquitectura Centralizada (Robusta)     │
│                                                     │
│  ✅ 1 función oficial                              │
│  ✅ 1 lugar con lógica                             │
│  ✅ Plan Anual siempre soportado                   │
│  ✅ Cambios rápidos (1 min)                        │
│  ✅ Riesgo de inconsistencia: BAJO                 │
└─────────────────────────────────────────────────────┘
```

---

**Documento de diagramas completado:** 21 de abril de 2026
