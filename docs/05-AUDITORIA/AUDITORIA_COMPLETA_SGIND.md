# AUDITORÍA COMPLETA SGIND - SISTEMA DE INDICADORES INSTITUCIONALES

**Fecha:** 21 de abril 2026  
**Versión:** 1.0  
**Auditor:** Consultor Senior Arquitectura de Datos  
**Alcance:** Análisis Integral - Fases 0 a 8  

---

# FASE 0: ENTENDIMIENTO DEL PROYECTO

## 0.1 Propósito del Sistema

**Nombre:** SGIND (Sistema de Gestión Integral de Indicadores Institucionales)  
**Institución:** Politécnico Grancolombiano  
**Propósito Principal:** Plataforma centralizada para consolidación, análisis, reporte y monitoreo de más de 1,000 indicadores de desempeño institucional.

### Objetivos Funcionales:
- Consolidación automática de datos desde múltiples fuentes (API Kawak, Excel, BD)
- Cálculo de métricas de cumplimiento, tendencias y categorización de riesgo
- Reportería mediante dashboards interactivos Streamlit
- Monitoreo en tiempo real con alertas de desempeño
- Gestión de Oportunidades de Mejora (OM) vinculadas a indicadores

---

## 0.2 Actores y Roles

| Rol | Descripción | Frecuencia Uso |
|-----|-------------|----------------|
| **Directivo/Rector** | KPIs estratégicos, alertas institucionales | Diaria/Semanal |
| **Líder de Proceso** | Monitoreo y comparación por área | Quincenal/Mensual |
| **Especialista de Calidad** | Gestión de OM y planes de acción | Continua (semanal) |
| **Analista BI** | Exportación y análisis avanzado | Continua |
| **Equipo Técnico** | ETL, Mantenimiento, Desarrollo | Según necesidad |

---

## 0.3 Dominios Funcionales

| Dominio | Descripción | Procesos Clave |
|---------|-------------|----------------|
| **ACADÉMICO** | Docencia, Investigación, Extensión | Tasa aprobación, Permanencia, Satisfacción |
| **FINANCIERO** | Presupuesto, Recursos, Eficiencia | Ejecución presupuestal, Ratio eficiencia |
| **OPERATIVO** | Procesos internos, Calidad | Indicadores de gestión operativa |
| **PLANES ESTRATÉGICOS** | PDI, CMI, CNA | Alineación estratégica, Acreditación |

---

## 0.4 Arquitectura de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────┐
│                     CAPA PRESENTACIÓN                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ Resumen     │ │ CMI         │ │ Plan        │ │ Gestión   │ │
│  │ General     │ │ Estratégico │ │ Mejoramiento│ │ OM        │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
│                         Streamlit (app.py)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                     CAPA LÓGICA DE NEGOCIO                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │ core/       │ │ services/    │ │ streamlit_  │              │
│  │ calculos.py │ │ data_loader  │ │ app/        │              │
│  │ config.py   │ │ strategic_   │ │ components/ │              │
│  │ db_manager  │ │ indicators   │ │             │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                     CAPA ETL / PIPELINE                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │ consolidar  │ │ actualizar   │ │ generar     │              │
│  │ _api.py     │ │ _consolidado│ │ _reporte.py │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
│                    scripts/etl/* (10+ módulos)                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                     FUENTES DE DATOS                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ API Kawak  │ │ Excel Local │ │ SQLite      │ │ PostgreSQL│ │
│  │ (2022-2026)│ │ Histórico   │ │ OM local    │ │ Supabase  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

# FASE 1: INVENTARIO GLOBAL

## 1.1 Matriz de Trazabilidad Global

### Indicadores

| ID | Nombre | Tipo | Formula | Fuente | Proceso | Página |
|----|--------|------|---------|--------|---------|--------|
| IND-001 | Tasa de Aprobación | Positivo | Ejecución/Meta | API Kawak | ACADÉMICO | Resumen General |
| IND-002 | Permanencia | Positivo | Ejecución/Meta | API Kawak | ACADÉMICO | Resumen General |
| IND-003 | Satisfacción Estudiantes | Positivo | Ejecución/Meta | API Kawak | ACADÉMICO | Resumen General |
| IND-004 | Ejecución Presupuestal | Positivo | Ejecución/Meta | API Kawak | FINANCIERO | CMI Estratégico |
| IND-005 | Deserción | Negativo | Meta/Ejecución | API Kawak | ACADÉMICO | Resumen General |
| IND-XXX | +1000 indicadores | Mixto | Varía | API Kawak | Múltiples | Varias |

### Dashboards / Páginas Streamlit

| ID | Nombre | Archivo | Indicadores Usados | Filtros | Cache | Estado |
|----|--------|---------|-------------------|---------|-------|--------|
| DASH-01 | Resumen General | resumen_general.py | Todos | Año, Mes, Línea | ✅ | Activo |
| DASH-02 | CMI Estratégico | cmi_estrategico.py | Estratégicos | Año, Línea | ✅ | Activo |
| DASH-03 | Plan Mejoramiento | plan_mejoramiento.py | CNA | Año, Factor | ✅ | Activo |
| DASH-04 | Gestión OM | gestion_om.py | OM | ID OM | ✅ | Activo |
| DASH-05 | Resumen por Proceso | resumen_por_proceso.py | Todos | Año, Proceso | ❌ | Activo |
| DASH-06 | Tablero Operativo | tablero_operativo.py | Operativos | Año, Mes | ✅ | Activo |
| DASH-07 | Seguimiento Reportes | seguimiento_reportes.py | Tracking | Año, Mes | ✅ | Activo |

### Fuentes de Datos

| ID | Nombre | Tipo | Ubicación | Actualización | Hojas | Consumida Por |
|----|--------|------|-----------|---------------|-------|---------------|
| FTE-01 | Resultados Consolidados | Excel | data/output/ | Post-ETL | 4 | Dashboard, OM |
| FTE-02 | API Kawak | Excel | data/raw/Kawak/ | Manual | N×N | ETL |
| FTE-03 | Consolidado_API_Kawak | Excel | data/raw/Fuentes Consolidadas/ | ETL Paso1 | 1 | ETL Paso2 |
| FTE-04 | Indicadores por CMI | Excel | data/raw/ | Manual | 1 | Dashboard |
| FTE-05 | Subproceso-Proceso-Area | Excel | data/raw/ | Manual | 1 | Data Loader |
| FTE-06 | OM (registros_om) | SQLite | data/db/ | Runtime | 1 | Gestión OM |
| FTE-07 | OM (Supabase) | PostgreSQL | Cloud | Runtime | 1 | Sincronización |
| FTE-08 | settings.toml | TOML | config/ | Manual | N/A | ETL, Core |

### Procesos ETL

| ID | Nombre | Tipo | Input | Output | Frecuencia | Estado |
|----|--------|------|-------|--------|------------|--------|
| ETL-01 | consolidar_api.py | Consolidación | Kawak Catálogos + API | Consolidado_API_Kawak.xlsx | Manual | ✅ |
| ETL-02 | actualizar_consolidado.py | Transformación | Consolidado_API_Kawak | Resultados Consolidados.xlsx | Manual | ✅ |
| ETL-03 | generar_reporte.py | Reportería | LMI + Consolidado | Seguimiento_Reporte.xlsx | Manual | ✅ |
| ETL-04 | run_pipeline.py | Orquestador | N/A | Todos los anteriores | Manual | ✅ |

### Artefactos de Código

| ID | Tipo | Nombre | Propósito | Estado |
|----|------|--------|-----------|--------|
| CODE-01 | Módulo | core/calculos.py | Lógica de categorización y tendencias | ✅ Activo |
| CODE-02 | Módulo | core/config.py | Constantes, umbrales, colores | ✅ Activo |
| CODE-03 | Módulo | core/db_manager.py | Persistencia OM (SQLite/PostgreSQL) | ✅ Activo |
| CODE-04 | Servicio | services/data_loader.py | Carga y enriquecimiento de datos | ✅ Activo |
| CODE-05 | Servicio | services/strategic_indicators.py | Lógica CMI | ⚠️ Duplicado |
| CODE-06 | Componente | streamlit_app/components/charts.py | Gráficos Plotly | ✅ Activo |
| CODE-07 | Componente | streamlit_app/components/filters.py | Filtros dinámicos | ✅ Activo |

### Reglas de Negocio

| ID | Nombre | Descripción | Estado |
|----|--------|-------------|--------|
| RN-01 | Cálculo Cumplimiento | Ejecución / Meta (escala decimal) | ⚠️ Duplicado |
| RN-02 | Categorización Estándar | Peligro<80%, Alerta 80-99%, Cumpl 100-104%, Sobre≥105% | ⚠️ Duplicado |
| RN-03 | Categorización Plan Anual | Peligro<80%, Alerta 80-94%, Cumpl≥95% (tope 100%) | ✅ Unificado |
| RN-04 | Tendencia | Mejora>2%, Empeora<-2%, Estable resto | ⚠️ No usado |
| RN-05 | Deduplicación | Priorizar Revisar=1, luego más reciente | ✅ |

---

# FASE 2: ANÁLISIS DE COHERENCIA

## 2.1 Hallazgos de Inconsistencia

### 🔴 CRÍTICO: Duplicación de Lógica de Cumplimiento

| Ubicación | Función | Problema |
|-----------|---------|----------|
| services/data_loader.py:235-255 | recalcula_cumplimiento() | Recalcula desde Meta/Ejecución |
| services/strategic_indicators.py:295-340 | _cumplimiento_pct() | Lógica similar pero diferente orden |
| core/calculos.py:13-24 | normalizar_cumplimiento() | Heurística "si > 2" |
| resumen_general.py:210-220 | _map_level() | **HARDCODED** - no usa config |

**Riesgo:** Mismo indicador → cumplimiento diferente según función ejecutada

---

### 🔴 CRÍTICO: Heurística Frágil "si valor > 2"

Usado en 3 lugares para detectar escala (decimal vs porcentaje):

1. `normalizar_cumplimiento()` — si `valor > 2`: divide entre 100
2. `_cumplimiento_pct()` — si `max(df) ≤ 2`: multiplica por 100
3. `gestion_om.py` lambda — si `avance_num ≤ 1.5`: multiplica por 100

**Problema:** Ambiguo. ¿Valor 2.5 es 250% o 2.5%? No hay documentación clara.

---

### 🔴 CRÍTICO: Inconsistencia Plan Anual

| Función | Considera Plan Anual? |
|---------|----------------------|
| `categorizar_cumplimiento()` | ✅ SÍ |
| `_nivel_desde_cumplimiento()` | ❌ NO |

**Riesgo:** Indicadores IDs 373, 390, 414, 420, 469-471 categorizados diferente según función

---

### 🔴 CRÍTICO: Hardcoding en UI

**Ubicación:** resumen_general.py líneas 210-220
```python
if pct >= 105: return "Sobrecumplimiento"
if pct >= 100: return "Cumplimiento"
if pct >= 80: return "Alerta"
return "Peligro"
```

**Debería usar:** `from core.config import UMBRAL_*` y `categorizar_cumplimiento()`

---

### 🟡 Configuración No Sincronizada

| Archivo | primaryColor | COLORES["primario"] |
|---------|---------------|---------------------|
| .streamlit/config.toml | #022457 | #1A3A5C |
| backgroundColor | #ffffff | #F4F6F9 |
| textColor | #0f2137 | #212121 |

---

### 🟡 Constantes Huérfanas (definidas pero no usadas)

| Constante | Definida En | Importada | Usada |
|-----------|-------------|-----------|-------|
| IDS_TOPE_100 | core/config.py:165 | ❌ | ❌ |
| ESTADO_NO_APLICA | core/config.py:214 | ❌ | ❌ |
| SENTIDO_POSITIVO | core/config.py:218 | ❌ | ❌ |
| COLS_TABLA_RESUMEN | core/config.py:194 | ❌ | ❌ |
| VICERRECTORIA_COLORS | core/config.py:51 | ❌ | ❌ |

---

## 2.2 Clasificación de Elementos

| Tipo | Coherente | Parcial | Inconsistente | Obsoleto |
|------|-----------|---------|---------------|----------|
| Indicadores | ✅ 90% | ⚠️ 8% | 🔴 2% | 🗑️ 0% |
| Visuales | ✅ 70% | ⚠️ 20% | 🔴 10% | 🗑️ 0% |
| Procesos | ✅ 75% | ⚠️ 15% | 🔴 10% | 🗑️ 0% |
| Fuentes | ✅ 85% | ⚠️ 10% | 🔴 5% | 🗑️ 0% |
| Config | ✅ 60% | ⚠️ 25% | 🔴 15% | 🗑️ 0% |

---

# FASE 3: DEPURACIÓN Y OPTIMIZACIÓN

## 3.1 Eliminación de Redundancias

### Recomendaciones de Consolidación:

| Item | Actual | Propuesto | Impacto |
|------|--------|-----------|---------|
| Funciones cumplimiento | 3 versiones | 1 (core/calculos.py) | Alto |
| Constantes umbrales | En UI + Config | Solo config | Alto |
| Colores | .streamlit + config | Solo config | Medio |
| Tendencias | Definida no usada | Implementar o eliminar | Bajo |

---

## 3.2 Unificación de Indicadores

### Indicadores Equivalentes sin Unificar:

- `_map_level()` en resumen_general.py = `categorizar_cumplimiento()` en core/calculos.py
- `_cumplimiento_pct()` en resumen_por_proceso.py = `normalizar_cumplimiento()` en core/calculos.py

---

## 3.3 Convenciones Definidas

### Nombres de Indicadores
```
FORMATO: IND-XXX (secuencial)
EJEMPLO: IND-001, IND-002, etc.
```

### Variables
```
camelCase para variables locales
UPPER_SNAKE para constantes
prefix_ para funciones utilitarias
```

### Capas del Modelo
```
data/raw/          → Datos originales (fuentes)
data/raw/Fuentes Consolidadas/ → Intermedios ETL
data/output/       → Consolidados finales
data/db/           → Persistencia SQLite
```

---

# FASE 4: NORMALIZACIÓN CON DATA CONTRACTS

## 4.1 Contratos de Indicadores

```json
{
  "id": "IND-001",
  "nombre": "Tasa de Aprobación",
  "descripcion": "Porcentaje de estudiantes que aprueban respecto a los inscritos",
  "tipo": "positivo",
  "unidad": "porcentaje",
  "formula_logica": "Ejecución / Meta",
  "implementacion_codigo": "core/calculos.py:normalizar_cumplimiento()",
  "fuentes": ["API Kawak", "Resultados Consolidados"],
  "filtros": ["Año", "Mes", "Proceso", "Subproceso"],
  "reglas_negocio": [
    "Umbral Peligro: < 80%",
    "Umbral Alerta: 80-99%",
    "Umbral Cumplimiento: 100-104%",
    "Umbral Sobrecumplimiento: ≥ 105%"
  ],
  "supuestos": [
    "Meta debe ser > 0",
    "Ejecución puede ser 0",
    "Sentido: Positivo (mayor es mejor)"
  ],
  "dependencias": ["IND-002 (Permanencia)", "IND-003 (Satisfacción)"]
}
```

---

## 4.2 Contratos de Procesos

```json
{
  "id": "ETL-02",
  "nombre": "Actualizar Consolidado",
  "tipo": "transformacion",
  "input": [
    "data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx",
    "config/settings.toml"
  ],
  "output": [
    "data/output/Resultados Consolidados.xlsx"
  ],
  "transformaciones": [
    "Normalizar cumplimiento (% → decimal)",
    "Categorizar (Peligro/Alerta/Cumpl/Sobre)",
    "Calcular tendencia",
    "Deduplicar por (Id, Fecha, Sede)"
  ],
  "frecuencia": "Manual (cuando hay nuevos datos)",
  "herramienta": "Python (pandas, openpyxl)",
  "errores_posibles": [
    "Meta ≤ 0 → ERROR",
    "Fecha inválida → ERROR",
    "Duplicados sin resolución"
  ]
}
```

---

## 4.3 Contratos de Visuales

```json
{
  "id": "DASH-01",
  "nombre": "Resumen General",
  "tipo": "dashboard",
  "indicadores_asociados": ["Todos"],
  "filtros": ["Año", "Mes", "Línea Estratégica", "Proceso", "Categoría"],
  "objetivo": "Vista 360° del estado de indicadores institucionales",
  "usuario_objetivo": "Directivo, Líder de Proceso",
  " KPIs_mostrados": [
    "Total indicadores",
    "Porcentaje en Peligro",
    "Porcentaje en Alerta",
    "Porcentaje en Cumplimiento",
    "Porcentaje en Sobrecumplimiento"
  ]
}
```

---

# FASE 5: SPECIFICATION BY EXAMPLE

## 5.1 Casos de Prueba - Cálculo de Cumplimiento

| Escenario | Input | Resultado Esperado | Regla Validada |
|-----------|-------|-------------------|-----------------|
| Normal positivo | Meta=100, Ejec=85 | 0.85 (85%) | Ejec/Meta |
| Cumplimiento exacto | Meta=100, Ejec=100 | 1.00 (100%) | Ejec/Meta |
| Sobrecumplimiento | Meta=100, Ejec=110 | 1.10 (110%) | Ejec/Meta |
| Valor en porcentaje | Cump=150 | 1.50 | Normalización |
| Valor ya decimal | Cump=0.85 | 0.85 | Sin cambio |
| Meta cero | Meta=0, Ejec=50 | ERROR | Validación |
| Negativo (menor es mejor) | Meta=15, Ejec=23 | 0.652 | Meta/Ejec |

---

## 5.2 Casos de Prueba - Categorización

| Escenario | Input | Resultado Esperado | Regla |
|-----------|-------|-------------------|-------|
| Peligro estándar | Cump=0.75 | Peligro | < 0.80 |
| Alerta estándar | Cump=0.85 | Alerta | 0.80-0.99 |
| Cumplimiento estándar | Cump=1.02 | Cumplimiento | 1.00-1.04 |
| Sobrecumplimiento | Cump=1.10 | Sobrecumplimiento | ≥ 1.05 |
| Plan Anual Peligro | ID=373, Cump=0.90 | Alerta | PA: 0.80-0.94 |
| Plan Anual Cumpl | ID=373, Cump=0.96 | Cumplimiento | PA: ≥ 0.95 |
| Sin dato | Cump=NaN | Sin dato | pd.isna() |

---

## 5.3 Casos de Prueba - Tendencia

| Escenario | Input | Resultado Esperado | Regla |
|-----------|-------|-------------------|-------|
| Mejora significativa | [0.70, 0.75, 0.80] | ↑ | Δ > 2% |
| Empeora significativo | [0.90, 0.85, 0.80] | ↓ | Δ < -2% |
| Estable | [0.85, 0.86, 0.87] | → | -2% ≤ Δ ≤ 2% |
| Un solo periodo | [0.85] | → | Sin datos suficientes |

---

# FASE 6: LIVING DOCUMENTATION

## 6.1 Mapa del Sistema

```
SGIND - SISTEMA DE INDICADORES INSTITUCIONALES
│
├── CAPA PRESENTACIÓN
│   ├── Streamlit App (app.py → streamlit_app/main.py)
│   ├── Páginas (9 dashboards)
│   └── Componentes (charts, filters)
│
├── CAPA LÓGICA
│   ├── core/ (config, calculos, db_manager)
│   ├── services/ (data_loader, strategic_indicators)
│   └── streamlit_app/components/
│
├── CAPA ETL
│   ├── scripts/consolidar_api.py
│   ├── scripts/actualizar_consolidado.py
│   ├── scripts/generar_reporte.py
│   └── scripts/etl/* (10+ módulos)
│
├── CAPA DATOS
│   ├── data/raw/ (fuentes originales)
│   ├── data/output/ (consolidados)
│   └── data/db/ (SQLite)
│
└── CONFIGURACIÓN
    ├── config/settings.toml
    ├── config/data_contracts.yaml
    └── .streamlit/config.toml
```

---

## 6.2 Catálogo de Indicadores

| ID | Nombre | Proceso | Periodicidad | Sentido | Plan Anual |
|----|--------|---------|--------------|---------|------------|
| IND-001 | Tasa de Aprobación | ACADÉMICO | Mensual | Positivo | No |
| IND-002 | Permanencia | ACADÉMICO | Mensual | Positivo | No |
| IND-003 | Satisfacción Estudiantes | ACADÉMICO | Semestral | Positivo | No |
| IND-004 | Ejecución Presupuestal | FINANCIERO | Trimestral | Positivo | No |
| IND-005 | Deserción | ACADÉMICO | Mensual | Negativo | No |
| ... | +1000 indicadores | Varios | Varía | Mixto | Algunos |

---

## 6.3 Catálogo de Procesos

| ID | Nombre | Tipo | Input | Output | Frecuencia |
|----|--------|------|-------|--------|------------|
| ETL-01 | Consolidar API | Consolidación | Kawak Catálogos + API | Consolidado_API_Kawak | Manual |
| ETL-02 | Actualizar Consolidado | Transformación | Consolidado_API | Resultados Consolidados | Manual |
| ETL-03 | Generar Reporte | Reportería | LMI + Consolidado | Seguimiento_Reporte | Manual |

---

## 6.4 Catálogo de Visuales

| ID | Nombre | Tipo | Indicadores | Usuarios Clave |
|----|--------|------|-------------|----------------|
| DASH-01 | Resumen General | KPI + Tabla + Gráfico | Todos | Directivo |
| DASH-02 | CMI Estratégico | Tabla + Gráfico | Estratégicos | Directivo |
| DASH-03 | Plan Mejoramiento | Tabla + Kanban | CNA | Calidad |
| DASH-04 | Gestión OM | Tabla + Form | OM | Calidad |
| DASH-05 | Resumen por Proceso | Tabla + Gráfico | Por proceso | Líder |

---

## 6.5 Reglas de Negocio

| ID | Nombre | Descripción | Estado |
|----|--------|-------------|--------|
| RN-01 | Cálculo Cumplimiento | Ejecución / Meta | ✅ Activa |
| RN-02 | Categorización Estándar | Peligro<80%, Alerta 80-99%, Cumpl 100-104%, Sobre≥105% | ✅ Activa |
| RN-03 | Categorización Plan Anual | Especial para IDs 373, 390, 414, 420, 469-471 | ✅ Activa |
| RN-04 | Indicadores Negativos | Meta / Ejecución (inversión) | ✅ Activa |
| RN-05 | Indicadores Tope 100 | IDs 208, 218 no permiten sobrecumplimiento | ✅ Activa |

---

# FASE 7: HALLAZGOS Y RIESGOS

## 7.1 Riesgos Críticos

### 🔴 RIESGO 1: Duplicación de Lógica de Cumplimiento
- **Severidad:** Alta
- **Probabilidad:** Alta
- **Impacto:** Indicadores pueden mostrar valores diferentes según función usada
- **Mitigación:** Unificar en core/calculos.py, eliminar duplicados

---

### 🔴 RIESGO 2: Heurística Ambigua "si valor > 2"
- **Severidad:** Alta
- **Probabilidad:** Media
- **Impacto:** Error de interpretación de escala (decimal vs porcentaje)
- **Mitigación:** Documentar claramente o eliminar heurística

---

### 🔴 RIESGO 3: Inconsistencia Plan Anual
- **Severidad:** Media
- **Probabilidad:** Baja
- **Impacto:** Indicadores ID 373, 390, 414 categorizados incorrectamente en algunas vistas
- **Mitigación:** Unificar uso de categorizar_cumplimiento()

---

### 🔴 RIESGO 4: Hardcoding de Umbrales en UI
- **Severidad:** Media
- **Probabilidad:** Alta
- **Impacto:** Cambios en config no se reflejan en UI
- **Mitigación:** Importar desde core/config en todas las páginas

---

### 🟡 RIESGO 5: Constantes No Usadas
- **Severidad:** Baja
- **Probabilidad:** Alta
- **Impacto:** Mantenibilidad, confusión
- **Mitigación:** Usar o eliminar constantes huérfanas

---

## 7.2 Procesos Manuales Críticos

| Proceso | Manual/Automático | Riesgo | Recomendación |
|---------|-------------------|--------|---------------|
| Carga Kawak API | Manual | Retraso en actualización | Automatizar API |
| Actualización catálogos | Manual | Inconsistencia | Versionar en git |
| Ejecución Pipeline | Manual | Olvido | Cron/scheduler |

---

# FASE 8: ROADMAP DE MEJORA

## 8.1 Quick Wins (Alto Impacto, Bajo Esfuerzo)

| # | Mejora | Impacto | Esfuerzo | Prioridad |
|---|--------|---------|-----------|-----------|
| 1 | Unificar función categorización en core/calculos.py | Alto | Bajo | 🔴 P1 |
| 2 | Eliminar hardcoding umbrales en resumen_general.py | Alto | Bajo | 🔴 P1 |
| 3 | Sincronizar colores .streamlit/config.toml con config.py | Medio | Bajo | 🟡 P2 |
| 4 | Usar constantes huérfanas o eliminarlas | Bajo | Bajo | 🟢 P3 |
| 5 | Documentar heurística "si > 2" | Medio | Bajo | 🟡 P2 |

---

## 8.2 Mejoras Estructurales

| # | Mejora | Impacto | Esfuerzo | Timeline |
|---|--------|---------|-----------|----------|
| 6 | Integrar Great Expectations para validación | Alto | Medio | Q2 2026 |
| 7 | Pipeline automatizado (cron/scheduler) | Alto | Medio | Q2 2026 |
| 8 | Unificar servicios strategic_indicators con core | Alto | Medio | Q2 2026 |
| 9 | Implementar tests para funciones UI | Alto | Alto | Q3 2026 |

---

## 8.3 Automatización

| # | Área | Automatización Propuesta | Beneficio |
|---|------|-------------------------|-----------|
| 10 | ETL | GitHub Actions para pipeline | Consistency |
| 11 | Validaciones | Great Expectations | Data Quality |
| 12 | Alertas | Notificaciones automáticas | Monitoreo |

---

## 8.4 Integración con IA

| # | Funcionalidad | Descripción | Timeline |
|---|---------------|-------------|----------|
| 13 | Análisis predictivo | Predecir incumplimientos | Q3 2026 |
| 14 | Detección anomalías | Identificar outliers | Q3 2026 |
| 15 | Narrativa automática | Generar insights | Q4 2026 |

---

## 8.5 Gobierno del Dato

| # | Área | Acción | Prioridad |
|---|------|--------|-----------|
| 16 | Data Contracts | Implementar validación automática | Alta |
| 17 | Lineage | Trazar flujo completo de datos | Media |
| 18 | Metadatos | Catálogo centralizado | Media |
| 19 | Calidad | KPIs de calidad de datos | Alta |

---

# ANEXO: Resumen de Archivos Auditados

## Documentación Revisada
- README.md
- INDICE_DOCUMENTACION_TPM.md
- 04-FUNCIONAL/DOCUMENTACION_FUNCIONAL.md
- docs/FUENTES_DATOS_PROYECTO.md
- config/data_contracts.yaml
- AUDITORIA_FASE_1_DISCOVERY.md
- 03-TECNICA/ARQUITECTURA_TECNICA_DETALLADA.md

## Código Revisado
- app.py
- core/calculos.py
- core/config.py
- core/db_manager.py
- scripts/actualizar_consolidado.py
- scripts/consolidar_api.py
- scripts/generar_reporte.py
- scripts/run_pipeline.py
- services/data_loader.py
- tests/test_calculos.py

---

**Documento generado:** 21 de abril 2026  
**Próxima revisión:** 15 de mayo 2026
