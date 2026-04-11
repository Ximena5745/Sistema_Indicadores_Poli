# 📐 REESTRUCTURACIÓN ARQUITECTÓNICA
## SGIND como Plataforma de Post-Proceso de Indicadores

**Fecha:** 10 de abril de 2026  
**Enfoque:** Consolidación → Reportes → Reglas → Seguimiento & Análisis  
**Exclusiones:** Definición de indicadores, Gestión de fichas técnicas

---

## TABLA DE CONTENIDOS
1. [Definición del Nuevo Modelo](#definición-del-nuevo-modelo)
2. [Análisis de Módulos](#análisis-de-módulos)
3. [Matriz Decisional](#matriz-decisional)
4. [Plan de Implementación](#plan-de-implementación)

---

# 1. DEFINICIÓN DEL NUEVO MODELO

## 1.1 Los 4 Pilares del Post-Proceso

```
┌─────────────────────────────────────────────────────────────────┐
│                   POST-PROCESO DE INDICADORES                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. CONSOLIDACIÓN      →  2. REPORTES      →  3. REGLAS      │
│  de datos                 generación            aplicación    │
│  (múltiples              (seguimiento,         (categorías,   │
│   fuentes)               análisis)             umbrales)      │
│                                                                 │
│    ↓                         ↓                    ↓            │
│                                                                 │
│  4. SEGUIMIENTO & ANÁLISIS                                    │
│     (alertas, tendencias, oportunidades de mejora)           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Pilar 1: Consolidación de Datos
**Objetivo:** Unificar datos de múltiples fuentes (Excel, APIs, BD) en un único dataset confiable.

**Responsabilidades:**
- Detección de fuentes (Kawak, API, LMI, etc.)
- Normalización de estructura (columnas, tipos de datos)
- Validación de integridad (nulos, duplicados, rangos)
- Enriquecimiento (mapeos, cruces, cálculos derivados)
- Trazabilidad de cambios (qué vino de dónde, cuándo)

**Salida:** Dataset consolidado limpio, con auditabilidad completa

---

### Pilar 2: Generación de Reportes
**Objetivo:** Crear visualizaciones y exportaciones para diferentes audiencias.

**Responsabilidades:**
- Reportes ejecutivos (resumen por proceso, por periodo)
- Reportes operativos (detalle indicador, histórico)
- Reportes de seguimiento (tracking de reportes, cargas)
- Exportaciones (Excel, PDF, formatos específicos)
- Personalización por rol (estratégico, operativo, líder de proceso)

**Salida:** Reportes en múltiples formatos, actualizados automáticamente

---

### Pilar 3: Aplicación de Reglas de Negocio
**Objetivo:** Convertir datos crudos en información decisional aplicando lógica institucional.

**Reglas clave:**
- Categorización (Peligro, Alerta, Cumplimiento, Sobrecumplimiento)
- Umbrales especiales (Plan Anual, indicadores negativos)
- Cálculo de tendencias (mejorando, estable, empeorando)
- Generación de alertas (incumplimiento + tendencia negativa)
- Detección de oportunidades de mejora (automática)

**Salida:** Datos enriquecidos con atributos de negocio; alertas accionables

---

### Pilar 4: Seguimiento y Análisis
**Objetivo:** Monitorear cumplimiento, detectar patrones, facilitar toma de decisiones.

**Responsabilidades:**
- Monitoreo de indicadores en riesgo (alertas)
- Análisis de tendencias (histórico, proyecciones)
- Correlación entre indicadores (causa-efecto)
- Generación automática de planes de mejora
- Dashboard ejecutivo con KPIs agregados

**Salida:** Insights accionables; planes de seguimiento

---

## 1.2 Flujo de Datos en el Nuevo Modelo

```
FUENTES EXTERNAS
├─ Kawak (catálogo + histórico)
├─ LMI (reporte de avances)
├─ API institucional
├─ Fichas técnicas (referencia, NO transformación)
└─ Excel manuales

         ↓↓↓ CONSOLIDACIÓN ↓↓↓

      DATASET CONSOLIDADO
      ├─ Indicadores únicos
      ├─ Cumplimiento histórico
      ├─ Metadatos enriquecidos
      └─ Trazabilidad completa

         ↓↓↓ REGLAS DE NEGOCIO ↓↓↓

      DATOS ENRIQUECIDOS
      ├─ Categorías (Peligro/Alerta/Cumplimiento)
      ├─ Tendencias (↑/↓/→)
      ├─ Alertas automáticas
      └─ Oportunidades de mejora

         ↓↓↓ REPORTES ↓↓↓

      SALIDAS MÚLTIPLES
      ├─ Dashboard ejecutivo (estratégico)
      ├─ Dashboard operativo (por proceso)
      ├─ Reporte de seguimiento (detalle)
      ├─ Exportaciones Excel
      └─ Alertas distribuidas

         ↓↓↓ SEGUIMIENTO ↓↓↓

      TOMA DE DECISIONES
      ├─ Planes de mejora
      ├─ Asignación de responsables
      └─ Seguimiento de acciones
```

---

# 2. ANÁLISIS DE MÓDULOS

## 2.1 CORE (Lógica Pura)

### ✅ `core/config.py` 
**Estado:** **APORTA DIRECTAMENTE**

| Aspecto | Evaluación |
|---|---|
| **Post-proceso** | Centraliza umbrales, colores, configuración para todos los pilares |
| **Pilar 1 (Consolidación)** | Define reglas de validación (CACHE_TTL, rutas de datos) |
| **Pilar 2 (Reportes)** | Define paleta de colores, columnas de visualización |
| **Pilar 3 (Reglas)** | Define umbrales de categorización (PELIGRO=0.80, etc.) |
| **Pilar 4 (Análisis)** | Base para cálculos de salud institucional |
| **Impacto** | CRÍTICO — fuente única de verdad |
| **Decisión** | **MANTENER | FORTALECER** |

**Justificación:** Aunque está bien hecho, requiere expansión para ser verdaderamente "fuente única" de reglas de negocio (consolidar también formatos de reporte, reglas de alerta, mapeos).

**Ajustes recomendados:**
```python
# Expandir con:

# Reglas de alerta
ALERTAS = {
    'incumplimiento_negativo': {
        'condicion': 'categoria == "Peligro" AND tendencia == "negativa"',
        'accion': 'generar_om'
    }
}

# Mapeos de procesos (actualmente en data_loader.py)
MAPEOS_PROCESOS = {
    'gestion_docente': 'DOCENCIA',
    ...
}

# Reglas de reporte
FORMATOS_REPORTE = {
    'ejecutivo': ['Id', 'Indicador', 'Cumplimiento%', 'Categoria'],
    'operativo': ['Id', 'Indicador', 'Proceso', 'Histórico', 'Tendencia']
}
```

---

### ✅ `core/calculos.py`
**Estado:** **APORTA DIRECTAMENTE**

| Aspecto | Evaluación |
|---|---|
| **Post-proceso** | Núcleo de aplicación de reglas de negocio |
| **Pilar 1 (Consolidación)** | Normaliza cumplimiento; garantiza escala consistente |
| **Pilar 2 (Reportes)** | Calcula salud institucional, tendencias |
| **Pilar 3 (Reglas)** | **CRÍTICO**: categorización, cálculo de tendencias |
| **Pilar 4 (Análisis)** | Genera recomendaciones contextuales |
| **Impacto** | CRÍTICO — lógica de negocio central |
| **Decisión** | **MANTENER | EXPANDIR** |

**Justificación:** Excelente diseño (sin dependencias Streamlit, testeable). Pero incompleto: faltan alertas automáticas, decisiones de OM.

**Funciones clave:**
- `normalizar_cumplimiento()` ✅ Bien
- `categorizar_cumplimiento()` ✅ Bien
- `calcular_tendencia()` ✅ Bien
- `generar_recomendaciones()` ✅ Bien
- ❌ **FALTA**: `generar_alerta_automática()` → si Peligro + tendencia negativa → crear OM
- ❌ **FALTA**: `detectar_oportunidad_mejora()` → lógica más sofisticada

**Expansión recomendada:**
```python
def detecciones_automáticas(df_indicador, categoria, tendencia):
    """Genera alertas y sugerencias de OM basadas en reglas."""
    
    if categoria == "Peligro" and tendencia == "Empeorando":
        return {
            'alerta': 'CRÍTICA',
            'accion_sugerida': 'crear_om',
            'prioridad': 1
        }
    elif categoria in ["Alerta", "Cumplimiento"] and tendencia == "Empeorando":
        return {
            'alerta': 'PREVENTIVA',
            'accion_sugerida': 'revisar_causas',
            'prioridad': 2
        }
    return None
```

---

### ⚠️ `core/niveles.py`
**Estado:** **REQUIERE AJUSTE (Consolidación en config.py)**

| Aspecto | Evaluación |
|---|---|
| **Pilar 3 (Reglas)** | Duplica funciones de config.py |
| **Problema** | Riesgo de desincronización |
| **Uso** | Bajo; pocas importaciones |
| **Decisión** | **ELIMINAR** |

**Justificación:** 
- Alias innecesarios para umbrales ya definidos en `config.py`
- Crea confusion sobre fuente de verdad
- Funciones como `nivel_desde_pct()` pueden estar en `core/calculos.py`

**Plan:**
1. Migrar `nivel_desde_pct()` → `calculos.py` como función auxiliar interna
2. Eliminar imports de `niveles.py` en todas las páginas
3. Reemplazar con imports desde `config.py`
4. Eliminar archivo

---

### ✅ `core/db_manager.py`
**Estado:** **APORTA DIRECTAMENTE (Pilar 1 + 4)**

| Aspecto | Evaluación |
|---|---|
| **Pilar 1 (Consolidación)** | Persistencia de datos consolidados (tabla registros_om) |
| **Pilar 4 (Análisis/Seguimiento)** | Base de registros de OM para seguimiento |
| **Arquitectura** | Dual SQLite/PostgreSQL; buena abstracción |
| **Impacto** | CRÍTICO — almacenamiento de decisiones |
| **Decisión** | **MANTENER | EXPANDIR** |

**Funcionalidades actuales:**
- `upsert_om()` — registrar OM
- `obtener_om_indicador()` — consultar OM por indicador

**Expansión recomendada:**
```python
# Nuevas tablas para Pilar 4 (Seguimiento)

registros_alertas:
  id_alerta INTEGER PRIMARY KEY
  id_indicador TEXT
  tipo_alerta TEXT  # "incumplimiento", "tendencia_negativa", etc.
  fecha_creacion TIMESTAMP
  estado TEXT       # "activa", "mitigada", "ignorada"
  valor_medicion FLOAT
  
registros_om_acciones:
  id_om TEXT
  id_accion INTEGER
  descripcion TEXT
  responsable TEXT
  fecha_vencimiento DATE
  estado TEXT       # "abierta", "en_proceso", "vencida", "cerrada"
  % progreso INTEGER
```

---

## 2.2 SERVICES (Caché + Orquestación)

### ✅ `services/data_loader.py`
**Estado:** **APORTA DIRECTAMENTE (Pilar 1)**

| Aspecto | Evaluación |
|---|---|
| **Pilar 1 (Consolidación)** | Carga Excel, normaliza, mapea procesos |
| **Problema** | 900+ líneas de mapeo hardcodeado |
| **Caché** | st.cache_data bien aplicado |
| **Dependencias** | Funciona bien pero ineficiente |
| **Decisión** | **MANTENER | REFACTORIZAR** |

**Funcionalidades clave:**
- `cargar_dataset()` — carga Excel principal ✅
- `_renombrar()` — normaliza columnas ✅
- `_mapa_proceso_padre` — **HARDCODEADO** ⚠️
- `cargar_analisis_usuarios()` — enriquecimiento ✅

**Refactorización recomendada:**
1. Mover 900+ líneas de mapeos a `data/config/mapeos_procesos.json`
2. Precargarlo en inicio de servicio (no en caché Streamlit)
3. Crear función `consolidar_fuentes(kawak, lmi, api)` que unifique
4. Separar normalizacion de enriquecimiento

**Nueva estructura:**
```python
@st.cache_resource
def cargar_mapeos_procesos():
    """Carga mapeos una sola vez al inicio."""
    with open('data/config/mapeos_procesos.json') as f:
        return json.load(f)

@st.cache_data(ttl=300)
def consolidar_datos():
    """Unifica fuentes: Kawak + LMI + API → dataset único."""
    df_kawak = cargar_kawak()
    df_lmi = cargar_lmi()
    mapeos = cargar_mapeos_procesos()
    
    df_consolidado = unificar_fuentes(df_kawak, df_lmi, mapeos)
    return df_consolidado
```

---

### ⚠️ `services/ai_analysis.py`
**Estado:** **REQUIERE AJUSTE (Pilar 4 — Análisis)**

| Aspecto | Evaluación |
|---|---|
| **Pilar 4 (Análisis)** | Análisis de texto para entender causas |
| **Problema** | **NUNCA IMPORTADO** en el código actual |
| **Potencial** | Alto si se activa correctamente |
| **Dependencia** | Requiere ANTHROPIC_API_KEY |
| **Decisión** | **ACTIVAR | INTEGRAR EN FLUJO DE OM** |

**Justificación:**
- Concepto válido: extraer insights de análisis registrados por responsables
- Ubicación correcta: análisis enriquecido de indicadores en riesgo
- Necesidad de integración: sin interface, usuario no lo usa

**Plan de activación:**
1. Integrar en panel de detalle de indicador (`components/charts.py`)
2. Si hay análisis registrado + Peligro + tendencia negativa → invocar Claude
3. Mostrar insights y oportunidades de mejora sugeridas
4. Guardar en BD para auditoría

---

## 2.3 STREAMLIT_APP (Frontend / UI)

### ✅ `streamlit_app/pages/resumen_general.py`
**Estado:** **APORTA DIRECTAMENTE (Pilares 2 + 4)**

| Aspecto | Evaluación |
|---|---|
| **Pilar 2 (Reportes)** | Dashboard principal de visualización |
| **Pilar 4 (Análisis)** | Detalle de indicador con tendencias |
| **Funcionalidad** | Tabla pivote, drill-down, exportación Excel |
| **Impacto** | CRÍTICO — entrypoint principal |
| **Decisión** | **MANTENER | OPTIMIZAR** |

**Funcionalidades correctas:**
- Tabla pivote con filtros ✅
- Gráficos de tendencia ✅
- Exportación Excel ✅

**Optimizaciones:**
- Mover funciones de formato a `utils/formateo.py`
- Unificar caché (TTL inconsistente)
- Limpiar código duplicado (funciones locales _cargar_*)

---

### ✅ `streamlit_app/pages/cmi_estrategico.py`
**Estado:** **APORTA DIRECTAMENTE (Pilares 2 + 4)**

| Aspecto | Evaluación |
|---|---|
| **Pilar 2 (Reportes)** | Reporte ejecutivo por perspectiva CMI |
| **Pilar 4 (Análisis)** | Tendencias estratégicas |
| **Funcionalidad** | 4 perspectivas, gráficos históricos |
| **Decisión** | **MANTENER** |

---

### ✅ `streamlit_app/pages/plan_mejoramiento.py`
**Estado:** **APORTA DIRECTAMENTE (Pilares 3 + 4)**

| Aspecto | Evaluación |
|---|---|
| **Pilar 3 (Reglas)** | Aplicación de generación de OM |
| **Pilar 4 (Análisis)** | Seguimiento de planes |
| **Funcionalidad** | Tabla OM, seguimiento de acciones |
| **Decisión** | **MANTENER | COMPLETAR** |

**Expansión:**
- Integrar alertas automáticas (generadas por `core/calculos.py`)
- Dashboard de cumplimiento de acciones
- Sugerencia automática de responsables (basada en histórico)

---

### ✅ `streamlit_app/pages/resumen_por_proceso.py`
**Estado:** **APORTA DIRECTAMENTE (Pilar 2)**

| Aspecto | Evaluación |
|---|---|
| **Pilar 2 (Reportes)** | Reporte operativo por proceso |
| **Funcionalidad** | Heatmap proceso × período |
| **Decisión** | **MANTENER** |

---

### ✅ `streamlit_app/pages/seguimiento_reportes.py`
**Estado:** **APORTA DIRECTAMENTE (Pilar 1)**

| Aspecto | Evaluación |
|---|---|
| **Pilar 1 (Consolidación)** | Validación de fuentes cargadas |
| **Funcionalidad** | QA de reportes, logs de errores |
| **Decisión** | **MANTENER** |

---

### ⚠️ `streamlit_app/pages/gestion_om.py`
**Estado:** **REQUIERE AJUSTE (Pilar 4 — Incompleto)**

| Aspecto | Evaluación |
|---|---|
| **Pilar 4 (Seguimiento)** | Gestión de OM y acciones |
| **Problema** | **RESUELTO**: página activa sin delegación a `pages_disabled/` |
| **Impacto** | CRÍTICO — función central sin interface |
| **Decisión** | **COMPLETADO (Fase 1)** |

**Estado actualizado:**
1. Código funcional integrado en página activa
2. Integración de persistencia validada
3. Cobertura de pruebas añadida para flujo de OM
4. Dependencia a wrappers removida

---

### ✅ `streamlit_app/pages/pdi_acreditacion.py`
**Estado:** **APORTA DIRECTAMENTE (Pilar 2)**

| Aspecto | Evaluación |
|---|---|
| **Pilar 2 (Reportes)** | Reporte de PDI/Acreditación |
| **Funcionalidad** | Tracking con estados |
| **Decisión** | **MANTENER** |

---

### 🔴 `streamlit_app/components/filters.py`
**Estado:** **REQUIERE AJUSTE (Inconsistencia UX)**

| Aspecto | Evaluación |
|---|---|
| **Pilar 2 (Reportes)** | Soporte para filtrado |
| **Problema** | Cada página reimplementa; sin patrón |
| **Decisión** | **REFACTORIZAR** |

**Mejora recomendada:**
```python
# Consolidar patrones de filtro

class FiltrosPeriodo:
    """Componente reutilizable para filtro de período."""
    
    @staticmethod
    def render(key_prefix="", default_periodo=None):
        """Retorna {año, semestre} o None."""
        # Implementación única, usada en todas partes

class FiltrosProceso:
    """Componente reutilizable para filtro de proceso."""
    # Similar

# Uso en cualquier página:
periodo = FiltrosPeriodo.render(key_prefix="resumen_gen")
filtro_proc = FiltrosProceso.render(key_prefix="resumen_gen")
```

---

## 2.4 SCRIPTS (ETL + Orquestación)

### ✅ `scripts/ingesta_plantillas.py`
**Estado:** **NO ENTRA EN SCOPE (Excluido: Definición)**

| Aspecto | Evaluación |
|---|---|
| **Tipo** | PRE-PROCESO: detecta y valida plantillas |
| **Problema** | Orientado a definición de estructura, no post-proceso |
| **Decisión** | **EXCLUIR DEL SCOPE** |

**Justificación:** 
- Es útil pero pertenece a Fase 1 (gobierno de datos)
- PROMPT 3 excluye "Definición de indicadores, Gestión de fichas técnicas"
- Puede coexistir pero no es parte de post-proceso

---

### ✅ `scripts/consolidar_api.py` + `generar_reporte.py`
**Estado:** **APORTA DIRECTAMENTE (Pilares 1 + 2)**

| Aspecto | Evaluación |
|---|---|
| **Pilar 1 (Consolidación)** | Consolida Kawak + API en dataset único |
| **Pilar 2 (Reportes)** | Genera `Seguimiento_Reporte.xlsx` |
| **Arquitectura** | Dos fases distintas: catálogo + resultados |
| **Impacto** | CRÍTICO — fuente de datos consolidada |
| **Decisión** | **MANTENER | INTEGRAR EN PIPELINE** |

**Funcionalidades:**
- `consolidar_kawak()` — une catálogos de Kawak por año ✅
- `consolidar_api()` — une históricos de API ✅
- Generación de hojas por periodicidad ✅
- Tracking mensual con matriz Id × mes ✅

**Mejoras:**
```python
# Integrar en pipeline orchestrator que ejecute en secuencia:
pipeline = [
    'consolidar_api',       # Fase 1: catálogos
    'consolidar_resultados',# Fase 2: históricos
    'generar_reporte',      # Fase 3: reportes
    'aplicar_reglas',       # Fase 4: categorías + alertas
    'publicar_dashboards'   # Fase 5: actualizar UI
]
```

---

### ✅ `scripts/consolidation/`
**Estado:** **APORTA DIRECTAMENTE (Pilar 3 + 4)**

| Aspecto | Evaluación |
|---|---|
| **Pilar 3 (Reglas)** | Motor configurable de reglas de negocio |
| **Pilar 4 (Análisis)** | Auditoría y trazabilidad |
| **Madurez** | En desarrollo; estructura buena |
| **Decisión** | **COMPLETAR | INTEGRAR** |

**Componentes:**
- `core/rules_engine.py` — aplicar reglas configurables ✅
- `core/audit.py` — registrar cambios ✅
- `pipeline/orchestrator.py` — orquestar pasos ✅

**Próximos pasos:**
1. Validar con usuarios clave (reglas correctas)
2. Integrar alertas automáticas
3. Conectar con generación de OM

---

### ⚠️ `scripts/nivel3/`
**Estado:** **REQUIERE DEFINICIÓN (Scope unclear)**

| Aspecto | Evaluación |
|---|---|
| **Tipo** | Funcionalidad especializada sin docs |
| **Impacto** | Bajo (no usado actualmente) |
| **Decisión** | **DOCUMENTAR O ELIMINAR** |

**Preguntas:**
- ¿Qué es "Nivel 3"? (Operativo, Detalle, Táctico?)
- ¿Cuál es su relación con los 4 pilares?
- ¿Es crítico para post-proceso?

**Recomendación:** Documentar en 1 semana o archivar.

---

## 2.5 COMPONENTES Y UTILIDADES

### ✅ `components/charts.py`
**Estado:** **APORTA DIRECTAMENTE (Pilares 2 + 4)**

| Aspecto | Evaluación |
|---|---|
| **Pilar 2 (Reportes)** | Visualizaciones interactivas |
| **Pilar 4 (Análisis)** | Gráficos de tendencia, drill-down |
| **Funcionalidad** | Línea, scatter 3D, heatmap |
| **Decisión** | **MANTENER** |

---

### ✅ `pages_disabled/` (cierre ejecutado)
**Estado:** **COMPLETADO**

| Archivo | Propósito | Decisión |
|---|---|---|
| 1_Resumen_General.py | Tablero v1 | **ELIMINAR** (reemplazado) |
| 2_Gestion_OM.py | Gestión OM | **RECUPERAR** (refactoring incompleto) |
| 2_Indicadores_en_Riesgo.py | Vista filtrada | **ELIMINAR** (absorbido) |
| 3_Acciones_de_Mejora.py | Plan acciones | **EVALUAR** (reutilizable?) |
| analitica_ia.py | IA | **REACTIVAR / ELIMINAR** |
| auditorias.py | Trazabilidad | **ELIMINAR** (reemplazado por audit.py v2) |
| irip_predictivo.py | Predictivos | **MANTENER COMO STUB** (Plan Fase 3) |
| dad_detector.py | Anomalías | **MANTENER COMO STUB** (Plan Fase 3) |

**Resultado:**
1. Refactorización de páginas activas completada
2. Directorio `pages_disabled/` eliminado
3. Búsqueda de referencias activas sin resultados

---

# 3. MATRIZ DECISIONAL

## 3.1 Clasificación de Módulos

| Módulo | Pilar(es) | Estado | Decisión | Justificación |
|---|---|---|---|---|
| **core/config.py** | 1,2,3,4 | ✅ | FORTALECER | Fuente única de verdad; expandir reglas |
| **core/calculos.py** | 1,3,4 | ✅ | EXPANDIR | Lógica sólida; agregar alertas automáticas |
| **core/niveles.py** | 3 | ⚠️ | ELIMINAR | Duplica config.py; migrar funciones |
| **core/db_manager.py** | 1,4 | ✅ | EXPANDIR | Base sólida; agregar tablas de alertas/acciones |
| **services/data_loader.py** | 1 | ✅ | REFACTORIZAR | Mover mapeos a YAML; unificar caché |
| **services/ai_analysis.py** | 4 | ⚠️ | ACTIVAR | Concepto bueno; integrar en flujo de OM |
| **streamlit_app/pages/resumen_general.py** | 2,4 | ✅ | OPTIMIZAR | Limpiar duplicados; unificar caché |
| **streamlit_app/pages/cmi_estrategico.py** | 2,4 | ✅ | MANTENER | Bien según objetivo |
| **streamlit_app/pages/plan_mejoramiento.py** | 3,4 | ✅ | COMPLETAR | Integrar alertas; asignación automática |
| **streamlit_app/pages/resumen_por_proceso.py** | 2 | ✅ | MANTENER | Bien según objetivo |
| **streamlit_app/pages/seguimiento_reportes.py** | 1 | ✅ | MANTENER | Bien según objetivo |
| **streamlit_app/pages/gestion_om.py** | 4 | 🔴 | COMPLETAR | Refactoring crítico |
| **streamlit_app/pages/pdi_acreditacion.py** | 2 | ✅ | MANTENER | Bien según objetivo |
| **streamlit_app/components/filters.py** | 2 | ⚠️ | REFACTORIZAR | Unificar patrones |
| **scripts/consolidar_api.py** | 1 | ✅ | INTEGRAR | Consolidación; agregar a pipeline |
| **scripts/generar_reporte.py** | 1,2 | ✅ | INTEGRAR | Consolidación + reportes; agregar a pipeline |
| **scripts/consolidation/** | 3,4 | ✅ | COMPLETAR | Motor de reglas; validar + integrar |
| **scripts/ingesta_plantillas.py** | — | ⚠️ | EXCLUIR | PRE-PROCESO (fuera de scope) |
| **scripts/nivel3/** | ? | ❓ | DOCUMENTAR/ELIMINAR | Scope unclear; decisión en 1 semana |
| **components/charts.py** | 2,4 | ✅ | MANTENER | Visualizaciones sólidas |
| **pages_disabled/** | — | 🔴 | LIMPIAR | Archivar/recuperar según tipo |

---

## 3.2 Matriz de Impacto vs. Esfuerzo

```
ESFUERZO ALTO
     │
     │  core/config.py:FORTALECER  |  scripts/consolidation:COMPLETAR
     │  core/db_manager.py:EXPANDIR |  scripts/nivel3:DOCUMENTAR
     │                              |
     │                    ┌─────────┤
     │                    │          
     │  core/calculos.py:EXPANDIR    
     ├─ scripts/consolidar_api:INTEGRAR  
     │  services/data_loader:REFACTORIZAR
     │
     │  gestion_om.py:COMPLETAR
     │  services/ai_analysis.py:ACTIVAR
     │
ESFUERZO BAJO
     └──────────────────────────────┬───→ IMPACTO BAJO
     
     core/niveles.py:ELIMINAR  |  streamlit_app/pages/*:MANTENER
     pages_disabled/*:LIMPIAR   |  components/filters.py:REFACTORIZAR
                                │

                           ← IMPACTO ALTO →
```

---

# 4. PLAN DE IMPLEMENTACIÓN

## 4.1 Roadmap de 12 Semanas

### Fase 0: URGENTE (Semanas 1-2)
**Objetivo:** Desbloquear bloques críticos

| Tarea | Módulo | Esfuerzo | Responsable |
|---|---|---|---|
| Completar refactoring Gestión OM | `gestion_om.py` | 3d | Backend |
| Eliminar `core/niveles.py` | `core/config.py` + páginas | 2d | Backend |
| Estandarizar CACHE_TTL | `services/` + `pages/` | 2d | Backend |
| Documentar `scripts/nivel3/` | `scripts/nivel3/` | 1d | Arquitecto |

**Deliverable:** Sistema operativo sin bloques críticos

---

### Fase 1: CONSOLIDACIÓN (Semanas 3-5)
**Objetivo:** Pilar 1 robusto

| Tarea | Módulo | Esfuerzo | Responsable |
|---|---|---|---|
| Mover mapeos a YAML | `services/data_loader.py` | 3d | Backend |
| Expandir `core/db_manager.py` (alertas/acciones) | `core/db_manager.py` | 3d | Backend |
| Integrar `consolidar_api.py` en pipeline | `scripts/consolidation/` | 2d | Backend |
| Tests de consolidación | `core/` + `services/` | 3d | QA |

**Deliverable:** Consolidación robusta con trazabilidad

---

### Fase 2: REGLAS & ALERTAS (Semanas 6-8)
**Objetivo:** Pilar 3 completo

| Tarea | Módulo | Esfuerzo | ResRespuesta |
|---|---|---|---|
| Expandir `core/calculos.py` (alertas) | `core/calculos.py` | 3d | Backend |
| Validar reglas con usuarios | `scripts/consolidation/` | 2d | PM |
| Integrar alertas en pipeline | `scripts/consolidation/` | 2d | Backend |
| Activar OM automática | `core/db_manager.py` + `plan_mejoramiento.py` | 3d | Backend |

**Deliverable:** Alertas automáticas, OM generadas por reglas

---

### Fase 3: ANÁLISIS & IA (Semanas 9-10)
**Objetivo:** Pilar 4 funcional

| Tarea | Módulo | Esfuerzo | Responsable |
|---|---|---|---|
| Activar `services/ai_analysis.py` | `services/ai_analysis.py` | 2d | Backend |
| Integrar análisis en drill-down | `components/charts.py` | 2d | Frontend |
| Dashboard de seguimiento | `streamlit_app/pages/` | 3d | Frontend |

**Deliverable:** Análisis enriquecido con IA; seguimiento completo

---

### Fase 4: LIMPIEZA & OPTIMIZACIÓN (Semanas 11-12)
**Objetivo:** Código limpio, documentación completa

| Tarea | Módulo | Esfuerzo | Responsable |
|---|---|---|---|
| Unificar patrones de filtro | `streamlit_app/components/` | 2d | Frontend |
| Centralizar funciones de formato | `utils/formateo.py` | 1d | Backend |
| Documentación de arquitectura | `docs/` | 2d | Arquitecto |
| Limpieza `pages_disabled/` | `pages_disabled/` | 1d | Backend |

**Deliverable:** Código limpios, arquitectura documentada

---

## 4.2 Dependencias Críticas

```
Completa gestion_om.py
         ↓
    Fase 0 ✅
    (1-2 sem)
         ↓
    Expande calculos.py + db_manager.py
         ↓
    Fase 1 ✅ Consolidation
    (3-5 sem)
         ↓
    Integra alertas + OM automática
         ↓
    Fase 2 ✅ Reglas
    (6-8 sem)
         ↓
    Activa AI analysis + Dashboard
         ↓
    Fase 3 ✅ Análisis
    (9-10 sem)
         ↓
    Limpia + Documenta
         ↓
    Fase 4 ✅ Finales
    (11-12 sem)
```

---

## 4.3 Métricas de Éxito

### Post-Implementación (Semana 12):

| Métrica | Meta | Status |
|---|---|---|
| % Módulos alineados a 4 pilares | 90% | — |
| Cobertura de código lógica core | 60%+ | — |
| TTL caché consistente | 100% | — |
| OM generadas automáticamente | 50%+ | — |
| Alertas accionadas correctamente | 90%+ | — |
| Tiempo de consolidación diario | < 30 min | — |
| Deuda técnica reducida | 30% | — |

---

## 4.4 Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Refactoring gestion_om falla | MEDIA | ALTO | Diseño en Semana 1 con usuarios |
| Nuevas reglas rompen reportes | MEDIA | ALTO | Tests exhaustivos antes de go-live |
| API Kawak cambia estructura | BAJA | ALTO | Contract testing; abstraer formato |
| IA analysis invalida datos | MEDIA | MEDIO | Validar outputs; marcar como "sugerencia" |
| Consolidación lenta (>1h) | BAJA | ALTO | Optimizar con índices; paralelizar |

---

# RESUMEN FINAL

## Decisiones Clave

| Decisión | Justificación |
|---|---|
| **POST-PROCESO PURO** | Excluir definición/fichas técnicas; enfocarse en consolidación → reglas → reportes → análisis |
| **ELIMINAR core/niveles.py** | Duplicación; consolidar en core/config.py |
| **COMPLETAR gestion_om.py** | Función crítica a mitad de refactoring |
| **EXPANDIR core/calculos.py** | Agregar alertas automáticas; detectar OM automáticamente |
| **INTEGRAR scripts/consolidation/** | Motor de reglas; validar y activar en pipeline |
| **ACTIVAR services/ai_analysis.py** | Análisis enriquecido de causas |
| **ARCHIVAR pages_disabled/** | Limpiar; recuperar solo código útil |

## Beneficios Esperados

✅ **Arquitectura clara:** 4 pilares bien definidos con módulos específicos  
✅ **Automatización:** OM y alertas generadas automáticamente según reglas  
✅ **Escalabilidad:** Consolidación robusta; fácil agregar nuevas fuentes  
✅ **Mantenibilidad:** Deuda técnica reducida; código testeable  
✅ **Análisis avanzado:** IA integrada; seguimiento automático  

---

**Fin del Análisis PROMPT 3**  
Generado: 10 de abril de 2026
