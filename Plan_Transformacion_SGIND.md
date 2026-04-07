# Plan de Transformación del Sistema de Indicadores SGIND

## 1. Diagnóstico estructurado

- **Datos:** Dependencia de archivos manuales (Excel/PDF), QA limitado, validaciones insuficientes, duplicidad de código, formatos preestablecidos pero heterogéneos.
- **Procesos:** ETL legacy, procesamiento fila a fila, falta de orquestación robusta, migración incompleta a framework modular.
- **Tecnología:** Scripts dispersos, baja modularidad, cobertura de tests insuficiente, falta de versionado de plantillas.
- **Analítica:** Dashboards planos, sin drill-down ni alertas inteligentes, sin modelos predictivos ni simulación.
- **Gobierno:** Roles poco definidos, trazabilidad limitada, documentación parcial, ausencia de políticas de almacenamiento y retroalimentación.

## 2. Fuentes de datos a utilizar

- Archivos Excel y PDF de auditoría ubicados en la carpeta `data/raw/`.
- Cada Excel tiene estructura preestablecida (por tipo de reporte), documentada en el catálogo de plantillas.
- No existen integraciones con sistemas transaccionales (ERP, LMS, etc.).

## 3. Modelo objetivo del sistema

- **Ingesta:** Extracción automatizada desde Excel/PDF, detección y mapeo de plantillas, control de versiones, monitoreo de cambios.
- **Procesamiento:** Validaciones automáticas por plantilla, consolidación multi-fuente, reglas de negocio centralizadas, artefactos QA.
- **Analítica:** Métricas descriptivas, semaforización, alertas, detección de anomalías, preparación para modelos predictivos y simulación.
- **Consumo:** Dashboards Streamlit interactivos, reportes ejecutivos automáticos, personalización por perfil, artefactos de auditoría.

## 4. Plan de trabajo por fases y entregables

### Fase 1: Gobierno y calidad de datos ✅ EN PROGRESO

**Entregables:**
- ✅ Catálogo de plantillas: Documento con estructura, campos, versiones y ejemplos de cada Excel/PDF. Ubicación: [docs/catalogo_plantillas.md](docs/catalogo_plantillas.md)
- ✅ Módulo de ingesta y validación: Scripts Python para extracción, validación y normalización por plantilla. Ubicación: [scripts/ingesta_plantillas.py](scripts/ingesta_plantillas.py)
- ✅ Artefactos de calidad y logs: JSON/CSV con resultados de validaciones, errores, duplicados, nulos, rangos y logs de ejecución. Ubicación: [data/output/artifacts/](data/output/artifacts/)
- ✅ Documentación técnica: Manual de reglas de negocio, validaciones y flujos de ingesta. Ubicación: [docs/documentacion_fase1.md](docs/documentacion_fase1.md)
- ✅ Panel de monitoreo de cargas: Dashboard Streamlit para visualizar estado de cargas, errores y calidad. Ubicación: [scripts/panel_monitoreo.py](scripts/panel_monitoreo.py)

**Estado:** Primeros entregables completados. Pendiente: validación con usuarios clave, documentación de reglas específicas por indicador, y refinamiento de validaciones.

### Fase 2: Motor de consolidación y reglas ✅ EN PROGRESO

**Entregables:**
- ✅ Framework modular de consolidación: Código en `consolidation/` con arquitectura modular para orquestar integración y transformación de datos.
- ✅ Motor de reglas y alertas: Módulo configurable para aplicar reglas de negocio, semaforización y alertas automáticas. Ubicación: [scripts/consolidation/core/rules_engine.py](scripts/consolidation/core/rules_engine.py)
- ✅ Artefactos de auditoría y versionado: Logs y reportes de cambios, versiones de archivos y resultados de consolidación. Ubicación: [scripts/consolidation/core/audit.py](scripts/consolidation/core/audit.py)
- ✅ Documentación de reglas y flujos: Esquemas de reglas implementadas, ejemplos y casos de uso. Ubicación: [docs/documentacion_fase2.md](docs/documentacion_fase2.md)

**Estado:** Motor de reglas y auditoría implementados. Pendiente: integración con orchestrator existente, validación con usuarios clave.

### Fase 3: Analítica descriptiva, diagnóstica y visualización avanzada
**Estado: NO INICIADA**

Esta fase aborda la sección 7 del documento de oportunidades ("Visualización estratégica y experiencia de usuario") y es crítica para la adopción del sistema.

#### 3.1 Arquitectura de dashboards (3 niveles)

| Nivel | Audiencia | Frecuencia | Enfoque |
|-------|-----------|------------|---------|
| **Nivel 1: CMI Estratégico** | Rectoría, Consejo Superior, Alta dirección | Trimestral | Scorecard con semáforos, mapa CMI, Índice Salud Institucional |
| **Nivel 2: Gestión y Cumplimiento** | Vicerrectores, Directores | Semanal/Mensual | Árbol objetivos, benchmark, gap análisis, matriz acreditación |
| **Nivel 3: Operativo y Calidad** | Coordinadores, Analistas | Diaria/Semanal | Kanban indicadores, seguimiento OM, validación datos |

**Entregables Nivel 1 (CMI):**
- Scorecard Estratégico: 6 líneas estratégicas, 11 objetivos
- Mapa CMI con 4 perspectivas
- Índice de Salud Institucional (0-100)
- Línea de Tiempo Predictiva con bandas de confianza

**Entregables Nivel 2 (Gestión):**
- Árbol de Objetivos: PDI → Procesos → Indicadores (drill-down)
- Comparativa vs Benchmark (universidades pares)
- Evolución de Brechas: planeado vs ejecutado vs proyectado
- Matriz de Acreditación: condiciones/factores con evidencia

**Entregables Nivel 3 (Operativo):**
- Kanban de Indicadores: Actualizado/Pendiente/Validado/Alerta
- Detalle de OM y Acciones con fechas compromiso
- Validación de Datos en tiempo real
- Trazabilidad: Hallazgo → Indicador → Plan de acción

#### 3.2 Catálogo de visualizaciones avanzadas (Plotly)

| # | Visualización | Tipo | Uso |
|---|---------------|------|-----|
| 1 | Cuadro de Mando Ejecutivo | KPIs + CMI | Home: 6 KPIs críticos + mapa CMI 4 perspectivas |
| 2 | Treemap | Jerárquico | Vista PDI por ejes estratégicos con % avance |
| 3 | Heatmap | Matriz | Cumplimiento proceso × periodo (color por semáforo) |
| 4 | Línea + bandas confianza | Tendencia | Histórico + proyección IA (horizonte 2 periodos, banda 80%) |
| 5 | Barras apiladas | Comparativo | Periodo actual vs anterior vs meta |
| 6 | Bubble chart | Riesgos | Tamaño=impacto, color=estado, eje=proceso/PDI |
| 7 | Sankey | Flujo | Hallazgos → indicadores → acciones |
| 8 | Sparklines | Mini gráfico | Tendencias en espacio reducido |
| 9 | Bullet chart | Comparativo | Actual vs objetivo vs zonas desempeño |
| 10 | Waterfall (Cascada) | Contribución | Desglose contribución procesos al cumplimiento PDI |
| 11 | Radar/Spider | Perfil | Comparación unidad vs promedio 6 dimensiones |
| 12 | Cohort heatmap | Evolución temporal | Filas=cohortes, columnas=tiempo, color=valor |
| 13 | Funnel | Proceso | OM: apertura → cierre, identifica cuellos botella |

#### 3.3 Sistema de navegación y contexto

**Barra Superior (Contexto Global)**
- Selector de Periodo (Mes/Año/Proyección)
- Selector de Unidad Organizativa
- Buscador Inteligente ("ir a indicador PR-05")

**Menú Lateral (Jerarquía Estratégica)**
- 🎯 Estratégico (PDI, CMI, Rectoría)
- 📋 Acreditación (Condiciones, Factores, Programas)
- ⚙️ Procesos (Mapa de procesos institucionales)
- 🔧 Mejoramiento (Hallazgos, OM, Acciones)
- 📊 Analítica Avanzada (IA, Predictivos, Simulaciones)
- ⚠️ Alertas y Tareas (Centro de notificaciones)

**Principios UX**
- Jerarquía Informativa Invertida: Lo más crítico primero, detalles bajo demanda
- Cognición Reducida: Máximo 3 clics para cualquier información
- Contexto Persistente: Usuario siempre sabe "dónde está" en la jerarquía
- Acción Inmediata: Cada alerta incluye botón de acción directa

#### 3.4 Paleta de colores y semaforización

| Estado | Color | Hex | Rango | Significado |
|--------|-------|-----|-------|-------------|
| Verde | Success | #28a745 | ≥95% | Meta cumplida, tendencia estable o positiva |
| Amarillo | Warning | #ffc107 | 80-94% | Atención requerida, riesgo moderado |
| Rojo | Danger | #dc3545 | <80% | Incumplimiento, riesgo alto |
| Azul | Info | #17a2b8 | >105% | Sobre-cumplimiento (posible desviación) |
| Gris | Secondary | #6c757d | N/A | Sin datos / Sin actualizar |

### Fase 4: Modelos predictivos, simulación e IA
**Estado: NO INICIADA**

Basado en secciones 5.1 y 6 del documento de oportunidades. Sistema transiciona de descriptivo a predictivo/consultivo.

#### 4.1 Modelos predictivos

| Modelo | Descripción | Entregable |
|--------|-------------|------------|
| **Índice Probabilidad Incumplimiento** | Predicción series de tiempo, horizonte 3 meses | Score 0-100 por indicador |
| **Score Salud Institucional** | Algoritmo pondera desviaciones indicadores críticos | Índice agregado 0-100 |
| **Análisis Sentimiento NLP** | NLP sobre textos auditoría para categorizar gravedad no conformidades | Categorización automática |
| **Recomendador dinámico metas** | Sugerencia automática basada en tendencias y benchmarks | Metas sugeridas |
| **Detector inconsistencias** | Variación >30% sin evento documentado | Solicitud validación |

#### 4.2 Reglas de negocio automatizadas

| Regla | Condición | Acción |
|-------|-----------|--------|
| Incumplimiento + tendencia negativa | cumplimiento <80% AND tendencia = decreciente | Generar OM, sugerir responsable |
| Sobre-cumplimiento | cumplimiento >105% AND meta = máximo | Alertar, sugerir recalibración |
| Variación abrupta | variación mensual >30% sin evento documentado | Solicitar validación dato |
| Indicador crítico sin actualizar | indicador crítico sin update >15 días | Escalar a jefe directo |

#### 4.3 Umbrales dinámicos
- Complementar metas fijas con reglas estadísticas (desviación estándar)
- Detectar anomalías relevantes reduciendo falsas alarmas

#### 4.4 Criterios depuración indicadores
- Cumplimiento sistemático >95% sin variación → no aportan diferenciación
- Meta >200% o <0% → mal definidos
- Sin acción asociada últimos 6 meses → candidate a retiro
- Múltiples indicadores midiendo lo mismo → consolidar

### Fase 5: Integración con auditoría, personalización y perfiles
**Estado: NO INICIADA**

Basado en secciones 8 y 9 del documento de oportunidades.

#### 5.1 Integración con auditoría

| Componente | Descripción |
|------------|-------------|
| **Correlación Hallazgo→Indicador→Acción** | Vincular hallazgos de auditoría con indicadores y planes de acción |
| **Detección vacío normativo** | Si auditoría señala brecha sin indicador → alerta automática |
| **Verificador validez** | Si hallazgo coincide con indicador 100% → falla en medición |
| **KPI Seguimiento Auditoría** | % hallazgos cerrados vs abiertos por proceso |

#### 5.2 Personalización por perfil

| Perfil | Audiencia | Enfoque | Recomendaciones | Acciones |
|--------|-----------|---------|------------------|----------|
| **Directivo** | Rectoría, Consejos, Decanaturas | Estratégico, predictivo, consolidado | Proyecciones de incumplimiento, planes de contingencia | Ajuste recursos, Escalamiento, Revisión estrategia |
| **Líder proceso** | Vicerrectores, Directores | Táctico, operativo, correctivo | Acciones más efectivas por tipo de problema | Abrir OM, Asignar capacitación, Revisar procedimiento |
| **Analista** | Coordinadores, Analistas | Operativo, validación, carga datos | Inconsistencias, anomalías, errores | Validar dato, Documentar anomalía, Corregir registro |

#### 5.3 Entregables
- Módulo integración auditoría: Hallazgo → Indicador → Plan acción → Cierre OM
- Detector vacíos normativos y verificador de validez
- Dashboards personalizados por 3 perfiles
- Sistema de retroalimentación de usuarios

## 5. Entregables transversales y de mejora continua

- **Orquestador de pipelines**: Script/configuración para automatizar la ejecución secuencial y paralela de procesos.
- **Data lineage visual**: Diagrama o dashboard que muestre el flujo y transformación de datos desde la ingesta hasta el consumo.
- **Plantillas mínimas y documentación de versiones**: Propuesta de formatos estándar y registro de cambios.
- **Política de almacenamiento y retención**: Documento con lineamientos para gestión de archivos y artefactos.
- **Mecanismo de retroalimentación de usuarios**: Encuesta, formulario o módulo en dashboard para capturar feedback.

## 6. Preguntas abiertas y riesgos

1. ¿Qué cambios no documentados pueden ocurrir en las plantillas de Excel/PDF?
2. ¿Qué reglas de negocio y validaciones son críticas para cada plantilla?
3. ¿Qué frecuencia y volumen de carga se espera por tipo de plantilla?
4. ¿Qué perfiles de usuario requieren personalización y con qué granularidad?
5. ¿Qué casos de uso de simulación y predicción son prioritarios?
6. ¿Qué herramientas de visualización y BI se prefieren?
7. ¿Qué políticas de almacenamiento y retención de archivos se deben cumplir?
8. ¿Qué mecanismos de retroalimentación de usuarios se consideran para iterar el sistema?

---

**Este plan es ejecutable y trazable, y puede ser utilizado como base para la coordinación de equipos técnicos, priorización de inversiones y evolución del sistema hacia analítica avanzada.**
