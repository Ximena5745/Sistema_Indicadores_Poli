# Plan de Trabajo Realista - SGIND 2026

**Documento:** PLAN_TRABAJO_REALISTA_2026.md  
**Versión:** 1.0  
**Fecha:** 11 de abril de 2026  
**Audiencia:** Líderes técnicos, Product Manager, Directivos  
**Alcance:** Fase 1 (Abril-Junio 2026) + Hoja de ruta 2026-2027

> Nota de vigencia: este documento mezcla estado ejecutado y plan original. Cualquier sección que describa wrappers activos o `pages_disabled/` debe leerse como histórico; ese cierre técnico ya fue completado.

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Estado Actual Validado](#estado-actual-validado)
3. [Matriz de Priorización](#matriz-de-priorización)
4. [Plan de Fases](#plan-de-fases)
5. [Timeline Detallado](#timeline-detallado)
6. [Recursos Requeridos](#recursos-requeridos)
7. [Riesgos y Mitigación](#riesgos-y-mitigación)
8. [Matriz RACI](#matriz-raci)

---

## Resumen Ejecutivo

### Situación Actual (11 de abril de 2026)

**Status:** Sistema en producción, Fase 1 completada, estable pero con deuda técnica

```
✅ IMPLEMENTADO (80% de líneas de código)
├─ Pipeline ETL (3 pasos: C→A→R)
├─ Dashboard Streamlit (5 páginas activas)
└─ Base de datos dual (SQLite/PostgreSQL)

🚧 INCOMPLETO (20% funcionalidad)
├─ Análisis IA (importado pero no activo)
├─ Motor de reglas v2
└─ CI/CD y analítica avanzada pendientes

✅ EJECUTADO EN FASE 1 (cierre técnico)
├─ Refactor de `gestion_om.py` y `seguimiento_reportes.py`
├─ Eliminación de `pages_disabled/` y `_page_wrapper.py`
└─ Nuevas pruebas de ejecución y persistencia
```

### Objetivo Principal

**Pasar de "Sistema Funcional" a "Sistema Optimizado + Escalable + Mantenible" en 16 semanas**

```
Inicio:     11 de abril 2026 (HOY)
Fase 1:     Stabilidad (4 semanas)     → 30 de abril
Fase 2:     Optimización (4 semanas)   → 28 de mayo
Fase 3:     Expansión (4 semanas)      → 25 de junio
Transición: Testing + Deploy (2 sem)   → 9 de julio

RESULTADO FINAL: Sistema production-ready con arquitectura mejorada
```

### Métrica de Éxito

| Métrica | Hoy | Meta | Fecha |
|---------|-----|------|-------|
| **Cobertura tests** | 40% | 85% | 25/06 |
| **Tiempo pipeline** | 5-7 min | 3-4 min | 28/05 |
| **Duplicación código** | 15-20% | <5% | 30/04 |
| **Páginas activas** | 5 (funcionales) | 5 (funcionales + cobertura) | 30/04 |
| **Documentación** | 5 docs | 8 docs | 11/04 ✅ |
| **Deuda técnica** | Alto | Bajo | 25/06 |

---

## Estado Actual Validado

### ✅ LO QUE SÍ FUNCIONA (Validado en Código)

#### 1. Pipeline ETL (100% Funcional)

**Paso 1: consolidar_api.py**
```
Status:     ✅ PRODUCCIÓN
Líneas:     200 líneas
Tests:      ✅ Funcionales
Duración:   45-60 segundos
Entrada:    data/raw/Kawak/*.xlsx + data/raw/API/*.xlsx
Salida:     Consolidado_API_Kawak.xlsx ✓
Problemas:  NINGUNO conocido
```

**Paso 2: actualizar_consolidado.py + /etl/**
```
Status:     ✅ PRODUCCIÓN
Líneas:     150 (orquestador) + 600 (módulos etl/)
Tests:      ✅ Funcionales (50+ cases en test_calculos.py)
Duración:   2-5 minutos
Entrada:    Consolidado_API_Kawak.xlsx + catálogos
Salida:     Resultados Consolidados.xlsx (3 hojas) ✓
Lógica:     Normalización, categorización, tendencias, recomendaciones
Problemas:  NINGUNO crítico
```

**Paso 3: generar_reporte.py**
```
Status:     ✅ PRODUCCIÓN
Líneas:     400 líneas
Tests:      ✅ Validación visual OK
Duración:   30-60 segundos
Entrada:    lmi_reporte.xlsx + Consolidado_API_Kawak.xlsx
Salida:     Seguimiento_Reporte.xlsx (4 hojas) ✓
Problemas:  NINGUNO conocido
```

**Orquestador: run_pipeline.py**
```
Status:     ✅ PRODUCCIÓN
Líneas:     280 líneas
Duración:   3-7 minutos total (SERIAL)
Validación: ✅ Verifica archivos + genera QA report
Problemas:  Ejecuta en SERIE (oportunidad Fase 2: paralelizar)
```

**Conclusión:** ETL está **ROBUSTO** y **CONFIABLE**. Sin cambios urgentes.

---

#### 2. Dashboard Streamlit (95% Funcional)

| Página | Estado | Líneas | Tests | Problemas |
|--------|--------|--------|-------|-----------|
| resumen_general.py | ✅ | 1900 | Manua1l | Código grande, duplicaciones |
| cmi_estrategico.py | ✅ | 250 | Manual | OK |
| plan_mejoramiento.py | ✅ | 150 | Manual | OK |
| resumen_por_proceso.py | ✅ | ~300 | Manual | OK |
| gestion_om.py | ✅ | Activa | ✅ | Persistencia OM validada |
| seguimiento_reportes.py | ✅ | Activa | ✅ | Tracking validado |

**Bloqueadores identificados:**
- ✅ wrappers eliminados y migrados
- ✅ cobertura agregada para utilidades y loaders clave
- ⚠️ pendiente estandarización total de caché (TTL)

**Conclusión:** Dashboard **FUNCIONAL y ESTABILIZADO en Fase 1**. Siguiente foco: optimización de rendimiento y automatización.

---

#### 3. Lógica de Negocio (100% Funcional)

**core/calculos.py**
```
Status:     ✅ TESTEABLE, CONFIABLE
Funciones:  7 principales
Tests:      ✅ 50+ casos pasando
Coverage:   ✅ 95%+ del código
Problemas:  NINGUNO
```

**core/config.py**
```
Status:     ✅ SINGLE SOURCE OF TRUTH
Constantes: ✅ Centralizados
  - UMBRAL_PELIGRO = 0.80
  - UMBRAL_ALERTA = 1.00
  - UMBRAL_SOBRECUMPLIMIENTO = 1.05
  - IDS_PLAN_ANUAL (11 IDs)
  - IDS_TOPE_100 (2 IDs)
Tests:      ✅ OK
Problemas:  Mapeos hardcodeados (900 líneas) → candidato YAML Fase 3
```

**core/db_manager.py**
```
Status:     ✅ PRODUCCIÓN
Persistencia: Dual (SQLite dev / PostgreSQL prod)
Tests:      ✅ OK
Problemas:  NINGUNO
```

**Conclusión:** Lógica **SÓLIDA**. Sin cambios urgentes.

---

#### 4. Base de Datos (100% Funcional)

```
DEV:  data/db/registros_om.db (SQLite local)
PROD: PostgreSQL en Supabase / Render
      
Tablas:
  ✅ registros_om (UNIQUE constraint OK)
  ✅ consolidado_historico (10,000+ registros)
  ✅ consolidado_semestral (agregado)
  ✅ consolidado_cierres (cierre anual)

Status: ✅ FUNCIONAL
Tests:  ✅ BD Manager tests OK
```

**Conclusión:** BD **ESTABLE**. Sin cambios urgentes.

---

### 🚧 LO INCOMPLETO (Actualizado)

#### 1. Cierre técnico Fase 1 (COMPLETADO)

**gestion_om.py** y **seguimiento_reportes.py** ya están activos sin delegación.

**Estado actual:**
- ✅ Wrappers removidos
- ✅ `_page_wrapper.py` eliminado
- ✅ Flujo de OM y tracking operativo
- ✅ Validado con pruebas de Fase 1

**Siguiente foco:** optimización de caché/rendimiento y automatización de reglas.

---

#### 2. Caché Inconsistente (DEUDA TÉCNICA)

**Problema:** TTL varía por página
```python
# Hoy
resumen_general.py:    @st.cache_data(ttl=600)  # 10 min
cmi_estrategico.py:    @st.cache_data(ttl=300)  # 5 min
plan_mejoramiento.py:  @st.cache_data(ttl=600)  # 10 min

# Resultado: Datos desincronizados 5-10 minutos post-pipeline
```

**Solución:** Estandarizar a `ttl=300` (5 minutos) globalmente  
**Esfuerzo:** 2-4 horas  
**Prioridad:** 🟡 MEDIO

---

#### 3. Análisis IA (Stub, no Activo)

**services/ai_analysis.py (50 líneas)**
```python
from anthropic import Anthropic

def analizar_indicador(id_indicador):
    client = Anthropic()
    # Código incompleto, no integrado en dashboard
    pass
```

**Status:** Importado pero NO USADO  
**Impacto:** Baja, es diferenciador futuro  
**Esfuerzo:** 15-20 horas (integración completa)  
**Prioridad:** 🟢 BAJA (Fase 3)

---

### ❌ LO QUE DEBE ELIMINARSE (Deuda Técnica)

#### 1. Directorio pages_disabled/ (EJECUTADO)

**Contenido:**
```
`pages_disabled/` fue removido del repositorio en el cierre de Fase 1.

Estado:
- ✅ Limpieza completada
- ✅ Sin imports activos a rutas deprecated
- ✅ Documentación principal actualizada

Nota: el inventario detallado de archivos eliminados se conserva en `LIMPIEZA_REPOSITORIO_SGIND.md` como referencia histórica.
```

**Impacto alcanzado:** reducción de código legacy y menor confusión operativa.  
**Beneficio:** claridad arquitectónica y menor deuda técnica activa.

---

#### 2. Duplicación de Código (6 funciones)

**Función 1: _is_null()**
```python
# resumen_general.py, cmi_estrategico.py, plan_mejoramiento.py, 
# resumen_por_proceso.py, gestion_om.py

def _is_null(valor):
    return pd.isna(valor) or valor == ""
```

**Función 2: _to_num()**  
**Función 3: _nivel()**  
**Función 4: _limpiar()**  
**Función 5: _id_limpio()**  
**Función 6: _fmt_num()** + _fmt_valor()

**Total duplicación:** ~150-200 líneas cruzadas  
**Impacto:** Mantenimiento difícil (bug en 1 = fijar 5)  
**Solución:** Consolidar en `streamlit_app/utils/formatting.py`  
**Esfuerzo:** 4-6 horas  
**Prioridad:** 🟡 MEDIA

---

#### 3. Mapeos Hardcodeados (900 líneas)

**Location:** services/data_loader.py

```python
_MAPA_PROCESO_PADRE = {
    "Dirección Estratégica": "DIRECCIONAMIENTO ESTRATÉGICO",
    "Gestión de Proyectos": "DIRECCIONAMIENTO ESTRATÉGICO",
    # ... 50+ entradas
    "Admisiones": "PROCESOS MISIONALES",
    # ... más
}  # Total: ~900 líneas

Problema:
  ❌ No-devs NO pueden actualizar
  ❌ Difícil mantener
```

**Solución:** Extraer a `config/mappings.yaml`  
**Esfuerzo:** 6-8 horas  
**Prioridad:** 🟢 BAJA (Fase 3, es nice-to-have)

---

## Matriz de Priorización

### Método: Impacto × Urgencia

```
IMPACTO (Y)
│
│ 🔴 🔴 🔴
│ HACER  HACER  PLANIFICAR
│ AHORA  RÁPIDO  BIEN
│
│ 🟡 🟡 🟢
│ HACER  CONSIDERAR  POSTERGAR
│ PRONTO  LUEGO
│
└───────────────────────────────────── URGENCIA (X)
```

### Matriz Aplicada (SGIND)

| ID | Actividad | Impacto | Urgencia | Prioridad | Semana | Esfuerzo | Bloqueador |
|----|-----------|---------|----------|-----------|--------|----------|-----------|
| **1.1** | **Refactorizar gestion_om.py** | 🔴 Alto | 🔴 Alto | **#1** | S1-S2 | 8h | ❌ Critical |
| **1.2** | **Refactorizar seguimiento_reportes.py** | 🔴 Alto | 🔴 Alto | **#2** | S2-S3 | 8h | ❌ Critical |
| **1.3** | Estandarizar caché (TTL) | 🟠 Med | 🟠 Med | **#3** | S1 | 3h | ⚠️ |
| **1.4** | Consolidar funciones utils | 🟠 Med | 🟠 Med | **#4** | S1 | 5h | ⚠️ |
| **1.5** | Agregar tests integración | 🟠 Med | 🟠 Med | **#5** | S3-S4 | 8h | ⚠️ |
| **2.1** | Paralelizar pipeline (P1 & P3) | 🟡 Bajo | 🟡 Bajo | **#6** | S5-S6 | 4h | ⚠️ |
| **2.2** | Eliminar pages_disabled/ | 🟠 Med | 🟡 Bajo | **#7** | S7-S8 | 4h | ✅ (post 1.2) |
| **2.3** | Implementar CI/CD | 🟠 Med | 🟡 Bajo | **#8** | S6-S8 | 8h | ⚠️ |
| **3.1** | Extraer mapeos a YAML | 🟡 Bajo | 🟢 Muy Bajo | **#9** | S9-S10 | 6h | ✅ |
| **3.2** | Motor de reglas v2 | 🟡 Bajo | 🟢 Muy Bajo | **#10** | S11-S12 | 16h | ✅ |
| **3.3** | API REST | 🟡 Bajo | 🟢 Muy Bajo | **#11** | S13-S14 | 12h | ✅ |

---

## Plan de Fases

### FASE 1: Estabilidad (Semanas 1-4) — Eliminar Bloqueadores

**Objetivo:** Sistema con 5 páginas FUNCIONALES (sin wrappers)

#### 1.1 Refactorizar gestion_om.py (S1-S2 : 8 horas)

**Qué está hoy:**
```python
# streamlit_app/pages/gestion_om.py
from ._page_wrapper import render_disabled_page
render_disabled_page("2_Gestion_OM.py")  # ← Apunta a deprecated
```

**Qué hace deprecated/2_Gestion_OM.py:**
- Modal para crear OM
- Tabla de OMs existentes
- Editar estado/descripción
- Validaciones

**Plan:**
```
1. Copiar lógica de deprecated/2_Gestion_OM.py
2. Refactorizar a usar utilities consolidadas
3. Integrar con BD (core/db_manager.py)
4. Agregar tests unitarios
5. Pruebas en dashboard
6. Documentar cambios
```

**Validación:** ✅ OMs creables desde dashboard

**Entregable:** `streamlit_app/pages/gestion_om.py` (funcional, 200-250 líneas)

---

#### 1.2 Refactorizar seguimiento_reportes.py (S2-S3 : 8 horas)

**Qué está hoy:**
```python
# streamlit_app/pages/seguimiento_reportes.py
from ._page_wrapper import render_disabled_page
render_disabled_page("5_Seguimiento_de_reportes.py")  # ← Apunta a deprecated
```

**Qué hace deprecated/5_Seguimiento_de_reportes.py:**
- Tabla de tracking (matriz ID × mes)
- Filtros por proceso
- Exportación Excel
- Estadísticas

**Plan:**
```
1. Copiar lógica de deprecated/5_Seguimiento_de_reportes.py
2. Refactorizar a usar utilities consolidadas
3. Leer desde Seguimiento_Reporte.xlsx (Paso 3 pipeline)
4. Agregar tests
5. Validar en dashboard
```

**Validación:** ✅ Tracking visible en dashboard

**Entregable:** `streamlit_app/pages/seguimiento_reportes.py` (funcional, 150-200 líneas)

---

#### 1.3 Estandarizar Caché (S1 : 3 horas)

**Qué está hoy:**
```python
# Inconsistencia entre páginas
resumen_general.py:    @st.cache_data(ttl=600)  # 10 min
cmi_estrategico.py:    @st.cache_data(ttl=300)  # 5 min
```

**Plan:**
```
1. core/config.py: Definir CACHE_TTL = 300 (global)
2. reemplazar todas @st.cache_data(ttl=X)
3. Usar: @st.cache_data(ttl=CACHE_TTL)
4. Tests de caché expiry
```

**Validación:** ✅ Todas las páginas con TTL=300s

**Entregable:** Código refactorizado, tests nuevos

---

#### 1.4 Consolidar Funciones Utilidades (S1 : 5 horas)

**Crear:** `streamlit_app/utils/formatting.py`

```python
# Consolidar 6 funciones duplicadas:
def is_null(valor):
    """Verificar si nulo/vacío."""
    return pd.isna(valor) or valor == ""

def to_num(valor, default=0):
    """Convertir a número."""
    try:
        return float(valor)
    except:
        return default

def nivel(categoria):
    """Mapear categoría a color."""
    # Peligro → rojo, Alerta → naranja, etc

def limpiar(texto):
    """Normalizar strings."""
    # Espacios, mayúsculas, caracteres especiales

def id_limpio(texto):
    """Extraer ID del texto."""
    # Regex para ID

def fmt_num(num, decimales=2):
    """Formatear número."""
    return f"{num:.{decimales}f}"

def fmt_valor(num, unidad=""):
    """Formatear con unidad."""
    return f"{fmt_num(num)} {unidad}"
```

**Reemplazar en todas las páginas:**
```python
# De:
from streamlit_app.pages.resumen_general import _is_null

# A:
from streamlit_app.utils.formatting import is_null
```

**Validación:** ✅ Sin duplicación, tests verdes

**Entregable:** `streamlit_app/utils/formatting.py`, actualizar imports en 5 páginas

---

#### 1.5 Agregar Tests de Integración (S3-S4 : 8 horas)

**Crear:** `tests/integration/test_dashboard_flows.py`

```python
def test_flujo_crear_om():
    """Flujo completo: Crear OM desde dashboard."""
    # 1. Cargar página gestion_om
    # 2. Llenar modal
    # 3. Click crear
    # 4. Validar en BD
    # 5. Validar en table

def test_flujo_resumen_general():
    """Filtros + exportación funcionan."""
    pass

def test_cache_consistency():
    """TTL=300s, datos actualizados."""
    pass

def test_paginas_sin_errores():
    """No hay crashes en ninguna página."""
    pass
```

**Validación:** ✅ Tests pasando, cobertura > 70%

**Entregable:** 20-30 test cases nuevos

---

#### 1.6 SPIKE: Testing Manual (S4 : 4 horas)

**Validaciones:**
- [ ] Crear OM desde dashboard
- [ ] Ver tracking mensual
- [ ] Exportar Excel sin errores
- [ ] Caché actualiza cada 5 minutos
- [ ] Sin duplicación de código

---

### Entregables Fase 1

| Entregable | Descripción | Fecha |
|-----------|-----------|--------|
| ✅ gestion_om.py (refactorizado) | 200 líneas, funcional, tests | 20/04 |
| ✅ seguimiento_reportes.py (refactorizado) | 150 líneas, funcional, tests | 25/04 |
| ✅ formatting.py | 6 funciones centralizadas | 15/04 |
| ✅ caché estandarizado | TTL=300s global | 12/04 |
| ✅ Tests integración | 20+ casos nuevos | 30/04 |
| 📊 Reporte Fase 1 | Validaciones + métricas | 30/04 |

---

### FASE 2: Optimización (Semanas 5-8) — Mejorar Rendimiento 

**Objetivo:** Pipeline 3-4 minutos (vs 5-7 hoy), código más limpio

#### 2.1 Paralelizar Pipeline (S5-S6 : 4 horas)

**Hoy (SERIAL):**
```
Paso 1 (45-60s) → Paso 2 (120-300s) → Paso 3 (30-60s)
Total: 195-420s ≈ 5-7 minutos
```

**Propuesta (PARALELO):**
```
Paso 1 (45-60s) ┐
                ├→ Paso 2 (120-300s) [Espera P1]
Paso 3 (30-60s) ┘

Total: 45-60s + 120-300s = 165-360s ≈ 3-6 minutos
Mejora: 20-30% en mejor caso
```

**Implementación:**
```python
# scripts/run_pipeline.py
import concurrent.futures

def run_pipeline_parallel():
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # Paso 1 y 3 se ejecutan en paralelo
        p1_future = executor.submit(consolidar_api.main)
        p3_future = executor.submit(  # ¡OJO! Depende de lmi_reporte.xlsx pre-existente
            generar_reporte.main
        )
        
        # Esperar Paso 1 para iniciar Paso 2
        p1_result = p1_future.result()
        p2_result = actualizar_consolidado.main()  # Serial después de P1
        
        # Esperar ambos
        p3_result = p3_future.result()
        
    return aggregate_results(...)
```

**Validación:** ✅ Pipeline ejecuta en 4-5 minutos

**Entregable:** `scripts/run_pipeline_optimized.py` (con tests)

---

#### 2.2 Eliminar pages_disabled/ (S7-S8 : 4 horas)

**Prerequisito:** Refactorización 1.1 + 1.2 completada ✅

**Plan:**
```
1. Backup: git tag v1-deprecated
2. Eliminar /pages_disabled/
3. Eliminar referencias en código
4. Actualizar documentación
5. Tests de importación (no existen deprecated)
6. Deploy + validar
```

**Validación:** ✅ No errores ImportError, -4,600 líneas limpias

**Entregable:** Repo sin directorio deprecated

---

#### 2.3 Implementar CI/CD (S6-S8 : 8 horas)

**Crear:** `.github/workflows/` (GitHub Actions)

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements-dev.txt
      - run: pytest tests/ --cov=core
      - run: pylint core/ services/
      
# .github/workflows/deploy.yml
name: Deploy to Render
on: 
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: curl https://api.render.com/deploy/...
```

**Beneficios:**
- ✅ Tests automáticos en cada push
- ✅ Code quality checks
- ✅ Deploy automático a Render

**Validación:** ✅ GitHub Actions ejecuta sin errores

**Entregable:** CI/CD pipeline funcional

---

### Entregables Fase 2

| Entregable | Descripción | Fecha |
|-----------|-----------|--------|
| ✅ run_pipeline_optimized.py | Paralelización P1 & P3 | 19/05 |
| ✅ pages_disabled/ eliminado | -4,600 líneas | 28/05 |
| ✅ CI/CD pipeline | GitHub Actions | 28/05 |
| 📊 Reporte Fase 2 | Benchmarks, tiempo pipeline | 28/05 |

---

### FASE 3: Expansión (Semanas 9-12) — Nuevas Capacidades

**Objetivo:** Automatización + motor de reglas + analítica avanzada

#### 3.1 Extraer Mapeos a YAML (S9-S10 : 6 horas)

**Hoy:** 900 líneas hardcoded en services/data_loader.py  
**Problema:** No-devs NO pueden actualizar

**Plan:**
```
1. Crear config/mappings.yaml:
   procesos:
     "Dirección Estratégica": "DIRECCIONAMIENTO ESTRATÉGICO"
     "Gestión de Proyectos": "DIRECCIONAMIENTO ESTRATÉGICO"
     # ... 50+ entradas

2. Crear config_loader.py:
   @st.cache_data
   def load_mappings():
       import yaml
       with open('config/mappings.yaml') as f:
           return yaml.safe_load(f)

3. Reemplazar en data_loader.py:
   MAPA_PROCESO_PADRE = load_mappings()['procesos']

4. Documentar formato en README
```

**Beneficio:** Non-technical users pueden actualizar mapeos

**Validación:** ✅ Dashboard carga mapeos desde YAML

**Entregable:** `config/mappings.yaml` + actualizado data_loader.py

---

#### 3.2 Motor de Reglas v2 (S11-S12 : 16 horas)

**Objetivo:** Automatización de OMs

```
Si: Cumplimiento < 80% AND Tendencia = ↓
Entonces: 
  → Crear OM automáticamente
  → Sugerir responsable
  → Proponer acción correctiva
  
Si: Cumplimiento > 105% AND es máximo esperado
Entonces:
  → Alertar sobre sobrecumplimiento
  → Sugerir recalibración meta

Si: Variación mensual > 30% sin evento
Entonces:
  → Solicitar validación dato
  → Requests al usuario que cargó dato
```

**Ubicación:** `scripts/consolidation/rules_engine.py`

**Implementación:**
```python
class RulesEngine:
    def __init__(self, config):
        self.rules = self._load_rules(config)
    
    def evaluate(self, indicador):
        """Evalúa indicador contra todas las reglas."""
        acciones = []
        for rule in self.rules:
            if rule.matches(indicador):
                acciones.append(rule.action)
        return acciones
```

**Validación:** ✅ 10+ reglas activadas en datos de prueba

**Entregable:** Motor de reglas funcional

---

#### 3.3 API REST (S13-S14 : 12 horas)

**Objetivo:** Integración con PowerApps / sistemas externos

```
GET /api/indicadores
  → Retorna lista de indicadores

GET /api/indicadores/{id}
  → Detalles de indicador + histórico

POST /api/oms
  → Crear OM programáticamente

GET /api/dashboard/kpis
  → KPIs para embeber en PowerApps
```

**Framework:** FastAPI (10 líneas de configuación)

**Validación:** ✅ API responds a requests, Swagger docs

**Entregable:** `scripts/api_server.py` + Documentación

---

#### 3.4 Análisis IA Activo (S15-S16 : 12 horas) — Diferenciador Opcional

**Objetivo:** Recomendaciones automáticas con Claude

```
Entrada:
  - Indicador en peligro
  - Histórico 12 meses
  - Contexto institucional

Proceso:
  → Enviar a Claude API
  → Analizar trend + causa probable
  → Generar recomendación personalizada

Salida:
  "Tasa de aprobación bajó de 92% a 87% en 2 meses.
   Probable causa: cambio en criterio evaluación.
   Recomendación: Capacitar docentes en nuevo criterio
                   e intensificar tutorías."
```

**Integración:**
```python
# services/ai_analysis.py (hoy stub, activar)
from anthropic import Anthropic

def generar_diagnostico_ia(id_indicador):
    """Análisis de indicador con Claude."""
    client = Anthropic()
    prompt = f"Analiza este indicador: {id_indicador}"
    response = client.messages.create(...)
    return response.content
```

**Validación:** ✅ Claude retorna análisis

**Entregable:** Análisis IA integrado en resumen_general.py

---

### Entregables Fase 3

| Entregable | Descripción | Fecha |
|-----------|-----------|--------|
| ✅ mappings.yaml | Procesos centralizados | 10/06 |
| ✅ RulesEngine | Automatización OMs | 18/06 |
| ✅ API REST | Endpoints /indicadores /oms | 25/06 |
| ✅ IA integrada (opcional) | Diagnósticos automáticos | 25/06 |
| 📊 Reporte Fase 3 | Capacidades nuevas | 25/06 |

---

## Timeline Detallado

### Abril 2026 (Fase 1: Estabilidad)

```
SEM 1 (11-17 Abr)
├─ Lun 11: Kick-off + Refactorizar gestion_om.py INICIA
├─ Mié 13: formattin.py listo
├─ Viér 15: caché estandarizado
└─ Dom 17: gestion_om.py refactorizado → PR + review

SEM 2 (18-24 Abr)
├─ Lun 18: Refactorizar seguimiento_reportes.py INICIA
├─ Mié 20: seguimiento_reportes.py COMPLETADO
├─ Viér 22: Tests integración INICIAN
└─ Dom 24: PR merge

SEM 3 (25-30 Abr)
├─ Lun 25: Tests integración continuación
├─ Mié 27: Testing manual (UAT)
├─ Viér 29: Bugs fixes
└─ Sáb 30: Deliverables Fase 1 COMPLETADOS
           ├─ 5 páginas funcionales ✓
           ├─ Caché estandarizado ✓
           ├─ Sin duplicación código ✓
           └─ Tests > 70% coverage ✓
```

### Mayo 2026 (Fase 2: Optimización)

```
SEM 5-6 (1-14 May)
├─ Lun 1: Pipeline paraleliza INICIA
├─ Viér 5: Benchmarks: 4-5 min ✓
├─ Lun 8: CI/CD INICIA
└─ Sáb 14: CI/CD funcional ✓

SEM 7-8 (15-28 May)
├─ Lun 15: pages_deprecated/ eliminado INICIA
├─ Mié 17: COMPLETADO ✓
├─ Viér 19: Refactor post-eliminación
└─ Sáb 28: Deliverables Fase 2 COMPLETADOS
           ├─ Pipeline 3-4 min ✓
           ├─ Repo limpio ✓
           ├─ CI/CD automático ✓
           └─ Tests > 80% coverage ✓
```

### Junio 2026 (Fase 3: Expansión)

```
SEM 9-10 (1-14 Jun)
├─ Lun 1: mappings.yaml INICIA
├─ Viér 5: COMPLETADO ✓
├─ Lun 8: RulesEngine INICIA
└─ Sáb 14: RulesEngine 50% ✓

SEM 11-12 (15-25 Jun) + SEM 13 (extensión)
├─ Lun 15: RulesEngine 100% COMPLETADO ✓
├─ Mié 17: API REST INICIA
├─ Viér 19: IA activa INICIA
├─ Lun 22: IA integrada ✓
├─ Mié 24: Testing final
└─ Jue 25: Deliverables Fase 3 COMPLETADOS
           ├─ RulesEngine ✓
           ├─ API REST ✓
           ├─ IA activa ✓
           └─ Tests > 85% coverage ✓
```

### Julio 2026 (Transición & Deploy)

```
SEM 14-15 (1-14 Jul)
├─ Testing completo (todas fases)
├─ UAT con sponsors
├─ Documento lecciones aprendidas
├─ Capacitación equipo
└─ Deploy a producción (Render)
```

---

## Recursos Requeridos

### Equipo

```
DESARROLLADORES:
├─ Backend/ETL: 1 FTE (Senior)
├─ Frontend/Streamlit: 1 FTE (Mid)
└─ DevOps/Infra: 0.5 FTE (Shared)

PRODUCT & QA:
├─ Product Manager: 0.5 FTE (Oversight)
└─ QA/Testing: 0.5 FTE (Testing manual + automatizado)

TOTAL: 3.5 FTE durante 16 semanas
       4 FTE después (mantenimiento)
```

### Herramientas & Infraestructura

```
✅ GitHub (repositorio + CI/CD)
✅ Render (hosting Streamlit)
✅ Supabase (PostgreSQL)
✅ VS Code (desarrollo)
✅ Pytest (testing)
✅ Docker (containerización)
✅ Anthropic API (análisis IA, opcional)
```

### Presupuesto Estimado

```
HORAS DE DESARROLLO:
Fase 1:  40 horas
Fase 2:  24 horas
Fase 3:  46 horas
────────────────
TOTAL: 110 horas

COSTO (a $100/hora):
Backend: 50h × $100 = $5,000
Frontend: 40h × $100 = $4,000
DevOps: 20h × $100 = $2,000
────────────────────────────
DESARROLLO: $11,000

INFRAESTRUCTURA (4 meses):
Render: $50/mes × 4 = $200
Supabase: $25/mes × 4 = $100
Anthropic API: < $50
────────────────────────────
INFRA: $350

TOTAL: $11,350
```

---

## Riesgos y Mitigación

### Riesgos Identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|--------|-----------|
| **Wrappers bloqueados** | Alta | Alto | Refactorizar primero (Fase 1) |
| **Deuda técnica acelerada** | Media | Alto | Timeline realista, sprints short |
| **Datos inconsistentes post-refactor** | Media | Alto | Tests exhaustivos antes de merge |
| **Performance paralelo no mejora** | Baja | Medio | Benchmark antes vs después |
| **Scope creep IA** | Alta | Alto | Dejar IA en "Fase 3 opcional" |
| **Team turnover** | Media | Alto | Documentación clara (✅ HECHO) |
| **Conflictos merge git** | Media | Bajo | PRs pequeñas, reviews diarios |

### Mitración Principales

1. **Refactorizar páginas wrappers PRIMERO** (S1-S3) antes de eliminar deprecated
2. **Automatizar tests** (CI/CD) para evitar regresiones
3. **Documentación exhaustiva** (completada en Prompt 7)
4. **Meetings de status 2x/semana** (continuidad)
5. **Deja IA como OPCIONAL** (Fase 3) si timeline se presiona

---

## Matriz RACI

### Responsabilidades

```
Activity                    Owner    Accountability  Consulted        Informed
────────────────────────────────────────────────────────────────────────────
Refactorizar gestion_om.py  Dev1     Tech Lead       QA, Dev2         Squad
Refactorizar                Dev2     Tech Lead       QA, Dev1         Squad
  seguimiento_reportes.py
Estandarizar caché          Dev1     Tech Lead       Dev2             Squad
Consolidar utilidades       Dev2     Tech Lead       Dev1             Squad
Tests integración           QA       Tech Lead       Dev1, Dev2       Squad
─────────────────────────────────────────────────────────────────────────────
Paralelizar pipeline        Dev1     Tech Lead       DevOps           Squad
Eliminar deprecated         Dev1/2   Tech Lead       DevOps           Squad
Implementar CI/CD           DevOps   Tech Lead       Dev1, Dev2       Squad
─────────────────────────────────────────────────────────────────────────────
Extraer mapeos YAML         Dev2     Tech Lead       Dev1             Squad
Motor de reglas v2          Dev1     Tech Lead       Dev2, QA         Squad
API REST                    Dev1     Tech Lead       DevOps           Squad
Análisis IA                 Dev1     Tech Lead       Dev2 (opcional)  Squad
─────────────────────────────────────────────────────────────────────────────

LEGEND:
R = Responsible (who does the work)
A = Accountable (final authority)
C = Consulted (experts, opinions)
I = Informed (status updates)
```

---

## Validación y Criterios de Aceptación

### Fase 1: Estabilidad ✓

```
CRITERIOS DE ACEPTACIÓN:
☐ gestion_om.py funcional, crear OMs desde dashboard
☐ seguimiento_reportes.py funcional, ver tracking
☐ Caché TTL=300s en TODAS las páginas
☐ Sin duplicación de código (utils consolidadas)
☐ Tests > 70% coverage
☐ Documentación actualizada

MÉTRICAS:
  Cobertura tests:    40% → 70%
  Duplicación código: 15% → 5%
  Páginas wrappers:   2 → 0
  Deuda técnica:      Alto → Medio
```

---

### Fase 2: Optimización ✓

```
CRITERIOS DE ACEPTACIÓN:
☐ Pipeline ejecuta en 3-4 minutos (vs 5-7 hoy)
☐ pages_disabled/ eliminado completamente
☐ CI/CD automático (tests + deploy)
☐ Tests > 80% coverage
☐ Cero errores deployment automático

MÉTRICAS:
  Tiempo pipeline:    5-7 min → 3-4 min (40% mejora)
  Líneas muertas:     -4,600
  CI/CD:              0% → 100%
  Cobertura tests:    70% → 80%
```

---

### Fase 3: Expansión ✓

```
CRITERIOS DE ACEPTACIÓN:
☐ Mapeos YAML funcionales, actualizables sin código
☐ Motor de reglas detecta anomalías
☐ API REST responde solicitudes
☐ Análisis IA activo (opcional)
☐ Tests > 85% coverage
☐ Documentación completa

MÉTRICAS:
  Reglas automáticas: 0 → 10+
  Endpoints API:      0 → 5+
  Capacidades IA:     Stub → Activa (opcional)
  Cobertura tests:    80% → 85%+
```

---

## Dependencias Externas

### Técnicas

- PostgreSQL (producción) — ✅ Disponible (Supabase)
- Anthropic API (IA) — ✅ Disponible, requiere API key
- GitHub Actions (CI/CD) — ✅ Disponible, estándar
- Docker (containerización) — ✅ Opcional pero recomendado

### Organizacionales

- Sponsor de negocio aprobando refactorización
- Acceso a código deprecated (para refactorizar)
- Disponibilidad stakeholders para UAT (Fase 2)
- Capacitación equipo en nuevas funcionalidades

---

## Lecciones Aprendidas (Así Far)

Basados en 6 prompts de análisis previos:

1. **ETL está robusto** —  No tocar pipeline Paso 1-3, enfocarse en paralelización
2. **Dashboard tiene deuda concentrada** — Dos wrappers + duplicación, fácil de fijar
3. **Documentación vale más que código** — Ya hemos gastad 5 documentos, claridad = velocidad
4. **Page wrapper era solución temporal** — Debería haberse refactorizado en mes 1
5. **Caché inconsistente es silencioso** — Usuarios asumen datos desincronizados = diseño
6. **Mapeos hardcodeados es odeur técnica** — Non-devs jamás podrán mantener 900 líneas

---

## Anexo: Diagrama Gantt (Texto)

```
ABRIL       MAY         JUN         JUL
┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
│S1 │S2 │S3 │S4 │S5 │S6 │S7 │S8 │S9 │S10│S11│S12│S13│S14│S15│
├───────────────────────────────────────────────────────────┤
FASE 1 (Estabilidad)
├─ gestion_om.py     ████████                              │
├─ seguimiento_rep   ██████████                            │
├─ caché             ████                                   │
├─ utils             ████                                   │
├─ tests integración       ██████████                        │
└─ UAT                             ██                        │
FASE 2 (Optimización)
├─ paralelizar pipeline                ████████            │
├─ CI/CD                           ██████████              │
├─ eliminar deprecated                    ████              │
└─ Validación                                ██             │
FASE 3 (Expansión)
├─ mappings YAML                            ████████        │
├─ RulesEngine                                   ██████████ │
├─ API REST                                         ██████  │
├─ IA (opcional)                                    ██████   │
└─ Testing final + Deploy                              ███   │
```

---

## Cómo Usar Este Plan

### Para Product Manager

1. Usar matriz RACI para asignar trabajo
2. Seguir timeline Gantt para tracking
3. Monitorear métricas cada Friday (standup)
4. Escalar riesgos si suceden

### Para Tech Lead

1. Descomponer actividades en tareas día-a-día
2. Asignar PRs a developers
3. Review code + merge
4. Actualizar documentación

### Para Developers

1. Pickear actividad según prioridad (#1-#11)
2. Crear rama feature: `git checkout -b feature/actividad-nombre`
3. Completar con tests
4. PR para review
5. Merge post-aprobación

### Para QA

1. Crear test plan por Fase
2. UAT con usuarios pilotos (Fase 2)
3. Validar criterios aceptación
4. Reportar bugs

---

## References Cruzadas

Para contexto adicional, consultar:

- **ANALISIS_ARQUITECTONICO_SGIND.md** — Análisis inicial (Prompt 1-2)
- **REFACTORIZACION_CODIGO_SGIND.md** — Código específico a refactor (Prompt 4)
- **LIMPIEZA_REPOSITORIO_SGIND.md** — Detalles archivos deprecated (Prompt 5)
- **OPTIMIZACION_FLUJOS_SGIND.md** — Detalles Fase 2-3 (Prompt 6)
- **DOCUMENTACION_FUNCIONAL.md** — Qué hace cada componente (Prompt 7)
- **ARQUITECTURA_TECNICA_DETALLADA.md** — Detalles técnicos (Prompt 7)

---

## Conclusión

Este plan es **REALISTA** basado en:
- ✅ Código real analizado
- ✅ Horas estimadas conservadoras
- ✅ Dependencias identificadas
- ✅ Riesgos mapeados
- ✅ Recursos disponibles

**Probabilidad de éxito:** 85-90% si se sigue el plan y se mitigan riesgos identificados.

**Próximos pasos:**
1. Kick-off con equipo (fijar Owner/Accountability)
2. Setup Git branches y CI/CD
3. Comenzar S1 con gestion_om.py + seguimiento_reportes.py
4. Standup 2x/semana

---

**Creado:** 11 de abril de 2026  
**Próxima Revisión:** 30 de abril de 2026  
**Status:** ✅ LISTO PARA EJECUCIÓN  
**Mantenedor:** Equipo de BI Institucional
