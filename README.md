# Sistema de Indicadores Institucionales (SGIND)

**Versión:** 2026 Q1  
**Estado:** 🟢 Producción — **Fase 1 COMPLETADA** ✅  
**Última actualización:** 11 de abril de 2026

📄 **[VER CIERRE FORMAL FASE 1](CIERRE_FASE_1.md)** — Entregables, métricas, validación y roadmap a Fase 2.

---

## 📋 Descripción General

**SGIND** es una plataforma integrada de **consolidación, reporte y análisis de indicadores de desempeño institucional** diseñada para Politécnico Grancolombiano.

### Propósito Principal

Centralizar y automatizar:
- 🎯 **Consolidación** de datos desde múltiples fuentes (API Kawak, Excel local, bases de datos)
- 📊 **Cálculo** de métricas de cumplimiento, tendencias y categorización de riesgo
- 📈 **Reportería** dashboards interactivos para toma de decisiones
- 🔔 **Monitoreo** de indicadores en tiempo real con alertas de desempeño
- 📋 **Gestión** de Oportunidades de Mejora (OM) vinculadas a indicadores

### Audiencias

- **Directivos:** KPIs estratégicos, alertas de desempeño institucional
- **Líderes de Proceso:** Seguimiento de indicadores por área, comparativas
- **Equipo de Calidad:** Registros de OM, planes de mejoramiento
- **Analistas de BI:** Exportación de datos, análisis avanzado

---

## 🎯 Funcionalidades Clave

### 1. Dashboard Consolidado
- **Resumen General:** Vista 360° de todos los indicadores con filtros dinámicos
- **Semáforo Interactivo:** Categorización por riesgo (Peligro/Alerta/Cumplimiento/Sobrecumplimiento)
- **Drill-Down:** Desde institución → proceso → subproceso → indicador
- **Exportación:** Generación de reportes Excel con formato corporativo

### 2. Análisis Estratégico
- **CMI Estratégico:** Indicadores alineados a 4 perspectivas (Financiera, Procesos, Aprendizaje, Usuario)
- **Tendencias:** Visualización de mejora/empeoramiento en últimos períodos
- **Comparativas:** Análisis entre períodos, procesos, sedes

### 3. Gestión de Mejora
- **Oportunidades de Mejora:** Registro vinculado a indicadores en incumplimiento
- **Plan de Mejoramiento:** Seguimiento de acciones correctivas por indicador
- **Tracking:** Estado de avance de cada OM (abierta/en ejecución/cerrada)

### 4. Reportería Automática
- **Seguimiento Mensual:** Tracking de cuáles indicadores fueron reportados vs. pendientes
- **Generación de Reportes:** Automático POST-consolidación
- **Históricos:** Acceso a datos de períodos anteriores

---

## 🏗️ Arquitectura de Alto Nivel

```
┌──────────────────────────────────────────────────────────────┐
│                    FUENTES DE DATOS                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ API Kawak    │  │ Excel Local  │  │ LMI Reporte  │       │
│  │ (2022-2026)  │  │ (Histórico)  │  │ (Tracking)   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└────────────────────────┬─────────────────────────────────────┘
                         ↓
         ┌───────────────────────────────────┐
         │    CAPA DE CONSOLIDACIÓN (ETL)    │
         ├───────────────────────────────────┤
         │  • consolidar_api.py              │
         │  • actualizar_consolidado.py      │
         │  • generar_reporte.py             │
         │  • Duración: 3-7 minutos          │
         └───────────────────────────────────┘
                         ↓
         ┌───────────────────────────────────┐
         │    ARTEFACTOS INTERMEDIOS         │
         ├───────────────────────────────────┤
         │  • Consolidado_API_Kawak.xlsx     │
         │  • Indicadores Kawak.xlsx         │
         │  • Resultados Consolidados.xlsx   │
         │  • Seguimiento_Reporte.xlsx       │
         └───────────────────────────────────┘
                         ↓
         ┌───────────────────────────────────┐
         │   CAPA DE LÓGICA DE NEGOCIO       │
         ├───────────────────────────────────┤
         │  • core/calculos.py               │
         │    - normalizar_cumplimiento()    │
         │    - categorizar_cumplimiento()   │
         │    - calcular_tendencia()         │
         │    - generar_recomendaciones()    │
         │                                   │
         │  • core/config.py                 │
         │    - Umbrales (0.80, 1.00, 1.05) │
         │    - Colores semáforo             │
         │    - Mapeos especiales            │
         │                                   │
         │  • core/db_manager.py             │
         │    - Persistencia OM (BD dual)    │
         └───────────────────────────────────┘
                         ↓
         ┌───────────────────────────────────┐
         │    CAPAS DE PRESENTACIÓN          │
         ├───────────────────────────────────┤
         │                                   │
         │  🖥️ WEB (Streamlit)              │
         │  ├─ Resumen General              │
         │  ├─ CMI Estratégico              │
         │  ├─ Plan Mejoramiento            │
         │  ├─ Resumen por Proceso          │
         │  └─ Gestión OM                   │
         │                                   │
         │  📊 EXCEL (Consultas directas)   │
         │  └─ Acceso a datos brutos        │
         │                                   │
         │  📱 API (Futuro)                 │
         │  └─ Para integraciones            │
         └───────────────────────────────────┘
```

---

## 📁 Estructura del Proyecto

```
sistema_indicadores_poli/
│
├── 📄 README.md                          ← Estás aquí
├── 📄 ARQUITECTURA_TECNICA_DETALLADA.md  ← Detalles técnicos
├── 📄 DOCUMENTACION_FUNCIONAL.md         ← Casos de uso
├── 📄 GUIA_INSTALACION_EJECUCION.md     ← Instalación
│
├── 📁 core/                              ← Lógica de negocio (testeable)
│   ├── config.py                         ← Umbrales, colores, constantes
│   ├── calculos.py                       ← Cálculo cumplimiento, tendencias
│   ├── db_manager.py                     ← Persistencia OM (SQLite/PostgreSQL)
│   ├── niveles.py                        ← [DEPRECADO] Usar config.py
│   └── __init__.py
│
├── 📁 services/                          ← Servicios (con caché Streamlit)
│   ├── data_loader.py                    ← Carga datos con @st.cache_data
│   ├── ai_analysis.py                    ← [FUTURO] Análisis con Claude
│   └── __init__.py
│
├── 📁 streamlit_app/                     ← Aplicación web
│   ├── main.py                           ← Punto de entrada (st.run)
│   ├── pages/
│   │   ├── resumen_general.py            ← Dashboard principal (1900 líneas)
│   │   ├── cmi_estrategico.py            ← CMI alineado a 4 perspectivas
│   │   ├── plan_mejoramiento.py          ← Seguimiento OM
│   │   ├── resumen_por_proceso.py        ← Vista por subproceso
│   │   ├── gestion_om.py                 ← Registro OM modal
│   │   └── seguimiento_reportes.py       ← Tracking mensual de reportes
│   │
│   ├── components/
│   │   ├── charts.py                     ← Gráficos Plotly reutilizables
│   │   ├── filters.py                    ← Dropdowns de filtro
│   │   └── __init__.py
│   │
│   ├── services/
│   │   ├── strategic_indicators.py       ← Lógica CMI
│   │   └── __init__.py
│   │
│   └── assets/                           ← Imágenes, estilos
│
├── 📁 scripts/                           ← Orquestación y ETL
│   ├── run_pipeline.py                   ← [MAIN] Ejecuta 3 pasos en orden
│   ├── consolidar_api.py                 ← Consolida Kawak + API
│   ├── actualizar_consolidado.py         ← Motor ETL v8 (calcular cumpl)
│   ├── generar_reporte.py                ← Genera tracking mensual
│   ├── agent_runner.py                   ← [FUTURO] Diagnóstico Claude
│   │
│   ├── etl/                              ← Módulos internos ETL
│   │   ├── config.py                     ← Configuración ETL (carga settings.toml)
│   │   ├── fuentes.py                    ← Carga de datos desde archivos
│   │   ├── catalogo.py                   ← Construcción catálogo
│   │   ├── normalizacion.py              ← Limpieza de datos
│   │   ├── signos.py                     ← Detección de unidades (%, $, etc)
│   │   ├── formulas_excel.py             ← Reescritura de fórmulas
│   │   ├── escritura.py                  ← Persistencia a Excel
│   │   ├── purga.py                      ← Validación de datos
│   │   ├── builders.py                   ← Construcción de hojas
│   │   └── workbook_io.py                ← I/O seguro de workbooks
│   │
│   ├── consolidation/                    ← [FUTURO] Motor de reglas v2
│   │   ├── core/
│   │   │   ├── rules_engine.py           ← Reglas configurables
│   │   │   ├── audit.py                  ← Auditoría de cambios
│   │   │   ├── config_loader.py          ← Cargador YAML
│   │   │   └── utils.py
│   │   │
│   │   └── pipeline/
│   │       └── orchestrator.py           ← Coordinador de pasos
│   │
│   └── analytics/                        ← [FUTURO] Análisis avanzado
│       └── data_preparator.py
│
├── 📁 config/                            ← Configuración centralizda
│   ├── settings.toml                     ← [MAIN] Configuración anual
│   ├── data_contract.yaml                ← [REFERENCIAL] Contrato de datos (fase futura)
│   └── mappings.yaml                     ← [FUTURO] Mapeos procesos
│
├── 📁 data/                              ← Datos (NO versionados)
│   ├── raw/
│   │   ├── Kawak/                        ← Catálogos anuales (2022-2026.xlsx)
│   │   ├── API/                          ← Resultados históricos (2022-2026.xlsx)
│   │   ├── Fuentes Consolidadas/         ← [Generated] Outputs paso 1
│   │   └── lmi_reporte.xlsx              ← Tracking LMI
│   │
│   ├── output/                           ← [Generated] Outputs finales
│   │   ├── Resultados Consolidados.xlsx  ← 3 hojas (Hist, Sem, Cierres)
│   │   └── Seguimiento_Reporte.xlsx      ← Tracking mensual
│   │
│   ├── db/                               ← Base de datos local
│   │   └── registros_om.db               ← SQLite (OM registry)
│   │
│   └── mock/                             ← Datos de prueba
│
├── 📁 tests/                             ← Suite de pruebas
│   ├── test_calculos.py                  ← [ACTIVO] 50+ test cases
│   ├── test_visual_validation.py         ← [ACTIVO] Validación outputs
│   ├── test_phase1_execution.py          ← [ACTIVO] Cobertura Fase 1 páginas/utilidades
│   ├── test_db_manager.py                ← [ACTIVO] Persistencia OM (SQLite/PostgreSQL)
│   │
│   └── consolidation/
│       └── test_utils.py                 ← Tests para v2 motor
│
├── 📁 docs/                              ← Documentación del proyecto
│   ├── analisis_sistema_indicadores.md   ← Análisis funcional
│   ├── calculos_actualizar_consolidado.md ← Fórmulas matemáticas
│   ├── fase3_*.md                        ← Documentación Phase 3 (Futuro)
│   └── ...
│
├── 📁 deploy/                            ← Deployment
│   ├── README.md                         ← Instrucciones Render
│   └── [Config para producción]
│
├── 📁 artifacts/                         ← [Generated] Logs + reportes
│   ├── pipeline_run_YYYYMMDD_*.json      ← QA report
│   └── pipeline_run_YYYYMMDD_*.log       ← Logs de ejecución
│
├── 📁 components/                        ← [Legacy] Mantener sólo mientras se migra a streamlit_app/
├── 📁 utils/                             ← [Partial] Funciones compartidas
│
├── 🐳 Dockerfile                         ← Contenedorización
├── 🐳 docker-compose.yml                 ← Stack completo (app + DB)
├── 📄 .env.example                       ← Variables de entorno
├── 📄 requirements.txt                   ← Dependencias Python
├── 📄 requirements-dev.txt                ← Dev dependencies (pytest, etc)
│
└── 🌐 [Configuración Control de Versiones]
    ├── .git/
    ├── .gitignore
    ├── .gitattributes
    └── render.yaml                       ← Config para Render.com
```

---

## ⚡ Inicio Rápido

### Instalación (5 minutos)

```bash
# 1. Clonar repositorio
git clone https://github.com/poli/sistema-indicadores.git
cd sistema-indicadores

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate    # Linux/Mac
# o en PowerShell: .venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar archivo .env
cp .env.example .env
# Editar .env con DATABASE_URL si usas PostgreSQL
```

### Ejecutar Pipeline (Fase 1 - Consolidación)

```bash
# Opción A: Con orquestador (recomendado)
python scripts/run_pipeline.py

# Opción B: Scripts individuales (para debugging)
python scripts/consolidar_api.py
python scripts/actualizar_consolidado.py
python scripts/generar_reporte.py
```

**Salida esperada:** 3-7 minutos
- ✓ `Resultados Consolidados.xlsx` (3 hojas)
- ✓ `Seguimiento_Reporte.xlsx` (4 hojas)
- ✓ `artifacts/pipeline_run_*.json` (QA report)

### Ejecutar Dashboard Web

```bash
# Terminal 1: Ejecutar app Streamlit
streamlit run streamlit_app/main.py

# Abrirá en http://localhost:8501
# Páginas disponibles:
#   - 📊 Resumen General (Dashboard principal)
#   - 📈 CMI Estratégico (Balaced Scorecard)
#   - ✅ Plan Mejoramiento (OMs)
#   - 🔍 Resumen por Proceso (Drill-down)
```

---

## 🔑 Conceptos Clave

### Indicadores de Cumplimiento

```
ESCALA DECIMAL [0 a n]:
  - Ejecución / Meta = Cumplimiento
  - Rango: 0.00 (0%) a ~2.00+ (>200%)

CATEGORIZACIÓN (UMBRALES):
  - 0.00 - 0.79   → 🔴 PELIGRO      (< 80%)
  - 0.80 - 0.99   → 🟡 ALERTA       (80-99%)
  - 1.00 - 1.04   → 🟢 CUMPLIMIENTO (100-104%)
  - 1.05+         → 🔵 SOBRECUMPL.  (≥ 105%)

ESPECIALES:
  - Plan Anual (IDs: 373, 390, 414-420, 469-471):
    Umbral bajo: 0.95 (en lugar de 1.00)
    Tope: 100% (no permite sobrecumplimiento)

  - Indicadores Negativo (menor es mejor):
    Meta / Ejecución (inversión de fórmula)
```

### Oportunidades de Mejora (OM)

```
DEFINICIÓN:
  Acción correctiva para indicador en incumplimiento
  
VINCULACIÓN:
  1 OM ← N indicadores
  Pero tracking por período específico

ESTADOS:
  - Abierta (recién creada)
  - En ejecución (con avance)
  - Cerrada (completada en plazo)
  - Retrasada (vencida sin cierre)

CONTROL:
  Almacenados en BD (SQLite local o PostgreSQL prod)
  Tabla: registros_om (id_indicador, numero_om, periodo, anio, sede)
```

### Pipeline ETL (Fase 1)

```
PASO 1: Consolidar API (45-60 seg)
  Entrada:
    - data/raw/Kawak/*.xlsx (catálogos anuales)
    - data/raw/API/*.xlsx (resultados históricos 2022-2026)
  Salida:
    - Indicadores Kawak.xlsx (maestro de IDs activos)
    - Consolidado_API_Kawak.xlsx (histórico con metadatos)

PASO 2: Actualizar Consolidado (2-5 min) ← Motor ETL principal
  Entrada:
    - Consolidado_API_Kawak.xlsx (del Paso 1)
    - config/settings.toml (umbrales, año cierre)
    - Catálogos auxiliares (CMI, LMI, mapeos)
  Operaciones:
    - Detección N/A (análisis contiene "no aplica")
    - Normalización cumplimiento (% → decimal)
    - Categorización (Peligro/Alerta/Cumpl/Sobre)
    - Cálculo tendencias (mejora/empeora)
    - Deduplicación por LLAVE (id-fecha-sede)
    - Validación de metas y ejecuciones
  Salida:
    - Resultados Consolidados.xlsx (3 hojas)
      * Consolidado Histórico (todos registros)
      * Consolidado Semestral (agregado por semestre)
      * Consolidado Cierres (cierre anual)

PASO 3: Generar Reporte (30-60 seg)
  Entrada:
    - LMI reporte (estructura de tracking)
    - Consolidado_API_Kawak (para mapear "Reportado")
  Salida:
    - Seguimiento_Reporte.xlsx (hojas por periodicidad)
      * Tracking Mensual (matriz Id × mes, Reportado/Pendiente/N/A)
      * Seguimiento (copia enriquecida de LMI)
      * Resumen (estadísticas por periodicidad)
```

---

## 📚 Documentación Completa

### Por Rol

| Rol | Documentos Recomendados |
|-----|--------------------------|
| **Usuario Final** | GUIA_INSTALACION_EJECUCION.md, DOCUMENTACION_FUNCIONAL.md |
| **Desarrollador** | ARQUITECTURA_TECNICA_DETALLADA.md, Docstrings en código |
| **DevOps** | GUIA_INSTALACION_EJECUCION.md, Dockerfile, docker-compose.yml |
| **Data Analyst** | DOCUMENTACION_FUNCIONAL.md, docs/calculos_actualizar_consolidado.md |

### Por Tema

- 📖 **Instalación & Configuración** → `GUIA_INSTALACION_EJECUCION.md`
- 🏗️ **Arquitectura técnica** → `ARQUITECTURA_TECNICA_DETALLADA.md`
- 💼 **Casos de uso & procesos** → `DOCUMENTACION_FUNCIONAL.md`
- 🔢 **Fórmulas y cálculos** → `docs/calculos_actualizar_consolidado.md`
- 🎯 **Análisis del sistema** → `docs/analisis_sistema_indicadores.md`

---

## 🔄 Estados del Proyecto

### ✅ Completado (Fase 1)

- [x] Pipeline ETL (consolidar + actualizar + reporte)
- [x] Dashboard Resumen General
- [x] CMI Estratégico
- [x] Plan Mejoramiento
- [x] Gestión OM (registro en BD)
- [x] Suite de pruebas (50+ casos)
- [x] Persistencia dual (SQLite/PostgreSQL)
- [x] Documentación técnica completa

### 🚧 En Desarrollo (Fase 2)

- [x] Refactorización de páginas (eliminar wrappers)
- [x] Limpieza de `pages_disabled/` y `_page_wrapper.py`
- [ ] Análisis con IA (Claude API integrado)
- [ ] Motor de reglas v2 (scripts/consolidation/)
- [ ] Caché estratificada (300s estándar)
- [ ] Extracciones YAML de mapeos

### 📋 Planificado (Fase 3)

- [ ] API REST (exposición de datos)
- [ ] Dashboards embebidos PowerApps
- [ ] Alertas automáticas por correo
- [ ] Anomaly detection (modelos predictivos)
- [ ] Reportería PDF automática

---

## 🤝 Contribución

### Requisitos para Contribuir

1. Fork del repositorio
2. Rama feature: `git checkout -b feature/tu-feature`
3. Tests: `pytest tests/ -v`
4. Documentación: Update docstrings y README
5. Pull Request con descripción clara

### Estándares de Código

```python
# ✅ CORRECTO
def normalizar_cumplimiento(valor: float) -> float:
    """Convierte escala (% → decimal si valor > 2).
    
    Args:
        valor: Cumplimiento en escala % (95) o decimal (0.95)
    
    Returns:
        Valor normalizado en escala decimal [0..n]
    """
    if valor > 2:
        valor = valor / 100
    return valor

# ❌ INCORRECTO
def norm_cum(v):
    if v > 2: v = v / 100
    return v
```

---

## 📞 Soporte

### Problemas Comunes

**P: "Pipeline tarda 7 minutos"**  
R: Normal en Fase 1 (validaciones exhaustivas). Optimización en Fase 2 reducirá a 3-4 min.

**P: "Datos del dashboard NO cambian después de ejecutar pipeline"**  
R: Caché Streamlit TTL=300s. Espera 5 minutos o:
```python
st.cache_data.clear()  # Limpiar caché manualmente
```

**P: "Error: 'Consolidado_API_Kawak.xlsx not found'"**  
R: Ejecuta primero `python scripts/consolidar_api.py` antes de actualizar_consolidado.py

### Contacto

- **Issues:** GitHub Issues (repositorio)
- **Documentación:** Ver sección "📚 Documentación Completa"
- **Equipo:** Contactar a lider@sistema-indicadores

---

## 📝 Licencia

Propiedad de Politécnico Grancolombiano — 2026

---

**Última revisión:** 11 de abril de 2026  
**Próxima revisión:** 15 de mayo de 2026  
**Mantenedor:** Equipo de BI Institucional
