# PLAN DE EJECUCIÓN CONTROLADA — MIGRACIÓN SGIND
# STREAMLIT → NEXT.JS + FASTAPI + POSTGRESQL

**Versión:** 1.0  
**Fecha:** 13 de junio de 2026  
**Estado:** Plan de Ejecución  
**Proyecto:** SGIND - Sistema de Gestión de Indicadores Institucionales  
**Institución:** Politécnico Grancolombiano  

---

## RESUMEN EJECUTIVO DEL PROYECTO

| Aspecto | Detalle |
|---------|---------|
| **Sistema actual** | Streamlit (Python 3.11/3.12), ~22,900 líneas, ~98 archivos |
| **Sistema destino** | Next.js 14 (Frontend), FastAPI (Backend), PostgreSQL |
| **Páginas** | 9 activas + 2 Beta (todas críticas) |
| **Tests actuales** | 696 tests, 100% passing, 18% cobertura global |
| **Dependencias** | 20 producción + 17 desarrollo |
| **ETL** | 25 módulos, pipeline 3 fases, ~45-50 seg |
| **IA** | 3 prompts Claude (haiku + opus), heuristic fallbacks |
| **Auth** | Microsoft OIDC, whitelist emails, 3 roles |
| **Datos** | 100,000+ registros, Excel como fuente de verdad |
| **Usuarios** | ~100 total, ~40 mensuales |
| **Estrategia** | Parallel run (Streamlit se mantiene) |
| **Cronograma** | 28 semanas (7 meses) |

---

# FASE 0 — LEVANTAMIENTO Y AUDITORÍA DEL SISTEMA ACTUAL

## Objetivo
Comprender completamente el sistema Streamlit existente: funcionalidades, arquitectura, integraciones, datos, IA, tests y deuda técnica. Generar documento de referencia para todas las fases posteriores.

## Alcance
- Inventario funcional de las 9 páginas activas + 2 Beta
- Inventario técnico de ~98 archivos Python (~22,900 líneas)
- Inventario de integraciones (Kawak API, Claude AI, PostgreSQL/Supabase, Microsoft OIDC)
- Inventario de datos (33 archivos Excel raw, 15 output, 2 bases de datos)
- Inventario de dashboards (10+ tipos de gráficos Plotly)
- Inventario de IA (3 prompts, 2 modelos Claude, heuristic fallbacks)
- Inventario de tests (696 tests, 48 archivos)
- Inventario de deuda técnica

## Actividades

### A0.1 — Inventario Funcional
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A0.1.1 | Leer y documentar cada página (`streamlit_app/pages/`) | Tabla de páginas con funciones, campos, filtros |
| A0.1.2 | Documentar componentes reutilizables (`streamlit_app/components/`) | Catálogo de componentes |
| A0.1.3 | Documentar navegación (`navigation.py`, sidebar) | Mapa de navegación |
| A0.1.4 | Documentar flujos de usuario por rol | Diagramas de flujo |

### A0.2 — Inventario Técnico
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A0.2.1 | Contar líneas por módulo (pages, components, core, services) | Métricas de código |
| A0.2.2 | Identificar dependencias (`requirements.txt`) | Matriz de dependencias |
| A0.2.3 | Documentar estructura de configuración (`settings.toml`, `config.py`) | Diccionario de config |
| A0.2.4 | Identificar deuda técnica (paths frágiles, duplicación, legacy) | Lista de deuda |

### A0.3 — Inventario de Integraciones
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A0.3.1 | Documentar integración Kawak API (fuentes, frecuencia) | Mapa de fuentes |
| A0.3.2 | Documentar integración Claude AI (prompts, modelos, costos) | Catálogo de prompts |
| A0.3.3 | Documentar integración PostgreSQL/Supabase (esquema, operaciones) | Diagrama ER |
| A0.3.4 | Documentar integración Microsoft OIDC (flujo, roles) | Diagrama de auth |

### A0.4 — Inventario de Datos
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A0.4.1 | Mapear todas las fuentes Excel (33 raw + 15 output) | Catálogo de fuentes |
| A0.4.2 | Documentar data contracts (`data_contracts.yaml`) | Diccionario de datos |
| A0.4.3 | Documentar ETL pipeline (3 fases, 25 módulos) | Diagrama de flujo ETL |
| A0.4.4 | Documentar esquema SQLite y PostgreSQL | Scripts SQL |

### A0.5 — Inventario de IA
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A0.5.1 | Extraer los 3 prompts exactos de `ai_analysis.py` | Templates de prompts |
| A0.5.2 | Documentar modelos, temperaturas, tokens, costos | Configuración IA |
| A0.5.3 | Documentar fallbacks heurísticos | Lógica alternativa |

### A0.6 — Auditoría de Tests
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A0.6.1 | Contar tests por categoría | Matriz de cobertura |
| A0.6.2 | Identificar gaps de cobertura | Plan de mejora |
| A0.6.3 | Ejecutar suite completa y verificar estado | Reporte de tests |

## Dependencias
- Ninguna (fase inicial)

## Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Documentación incompleta o desactualizada | Media | Alto | Verificar contra código fuente, no contra docs |
| Módulos legacy sin documentar | Alta | Medio | Búsqueda exhaustiva con grep/glob |
| Dependencias circulares ocultas | Baja | Alto | Análisis de imports |

## Mitigaciones
- Usar herramientas de análisis estático (grep, ast parsing)
- Verificar cada hallazgo contra el código fuente
- Involucrar al equipo en validación

## Entregables

| # | Entregable | Formato |
|---|------------|---------|
| E0.1 | Documento Funcional del Sistema Actual | Markdown |
| E0.2 | Documento Técnico del Sistema Actual | Markdown |
| E0.3 | Mapa de Procesos y Flujos | Diagrama Mermaid |
| E0.4 | Inventario de Componentes | Tabla |
| E0.5 | Catálogo de Fuentes de Datos | Tabla |
| E0.6 | Catálogo de Prompts IA | Tabla |
| E0.7 | Matriz de Tests | Tabla |
| E0.8 | Lista de Deuda Técnica | Tabla priorizada |

## Casos de Prueba

| ID | Prueba | Resultado Esperado |
|----|--------|-------------------|
| TP-0.1 | Verificar que todas las páginas están documentadas | 9/9 activas + 2 Beta documentadas |
| TP-0.2 | Verificar que todas las funciones de services/ están documentadas | ~75 funciones documentadas |
| TP-0.3 | Verificar que todos los prompts IA están extraídos | 3 prompts documentados |
| TP-0.4 | Verificar que el ETL está completamente mapeado | 3 fases, 25 módulos documentados |
| TP-0.5 | Verificar que los tests ejecutan correctamente | 696/696 passing |
| TP-0.6 | Verificar que no existen módulos sin documentar | 0 módulos huérfanos |

## Evidencias Requeridas
- Tabla de páginas con línea-count y función-count
- Tabla de dependencias con versiones
- Diagrama de arquitectura actual
- Catálogo de fuentes Excel con rutas exactas
- Templates de prompts IA
- Reporte de ejecución de tests
- Lista priorizada de deuda técnica

## Auditoría
- Revisión cruzada: cada módulo documentado debe tener correspondencia en código
- Validación: los 696 tests deben pasar sin errores
- Cobertura: 100% de archivos Python inventariados

## Checklist

- [ ] 9 páginas activas documentadas
- [ ] 2 páginas Beta documentadas
- [ ] ~20 componentes documentados
- [ ] ~75 funciones de services documentadas
- [ ] ~50 funciones de core documentadas
- [ ] 25 módulos ETL documentados
- [ ] 3 prompts IA extraídos
- [ ] 33 fuentes Excel mapeadas
- [ ] 14 procesos mapeados
- [ ] 696 tests verificados
- [ ] 13 variables de entorno documentadas
- [ ] 20 dependencias producción documentadas
- [ ] Deuda técnica priorizada

## Criterios de Aceptación
1. 100% de funcionalidades identificadas y documentadas
2. 100% de módulos Python inventariados
3. Todos los tests ejecutan correctamente
4. No existen módulos huérfanos sin documentar
5. Documento aprobado por stakeholders

## Estimación de Esfuerzo
- **Duración:** 1 semana (5 días)
- **Esfuerzo:** 40 horas
- **Responsable:** Arquitecto de Software + Analista funcional

## Responsable Sugerido
**Arquitecto de Software** (liderazgo técnico) + **Product Owner** (validación funcional)

## Prompt Específico para Ejecutar la Fase mediante IA

```
Eres un Auditor Técnico Senior. Realiza una auditoría completa del sistema
SGIND en Streamlit ubicado en [RUTA_PROYECTO].

Genera los siguientes documentos:

1. DOCUMENTO FUNCIONAL: Para cada página (streamlit_app/pages/), documenta:
   - Nombre, propósito, líneas de código
   - Todos los componentes Streamlit utilizados
   - Todos los filtros disponibles
   - Todas las visualizaciones
   - Todas las exportaciones
   - Todas las integraciones IA

2. DOCUMENTO TÉCNICO: Para cada módulo, documenta:
   - Funciones públicas con firma completa
   - Dependencias internas y externas
   - Patrones de diseño utilizados
   - Deuda técnica identificada

3. MAPA DE PROCESOS: Genera diagrama Mermaid del flujo ETL completo

4. INVENTARIO DE DATOS: Tabla de todas las fuentes Excel con:
   - Ruta exacta
   - Hojas utilizadas
   - Consumidor (qué función la lee)
   - Frecuencia de uso

5. CATÁLOGO DE IA: Para cada integración con Claude:
   - Prompt template exacto
   - Modelo utilizado
   - Temperature y max_tokens
   - Fallback heurístico

Usa las herramientas de lectura para verificar cada hallazgo contra el código fuente.
No asumas nada — verifica todo.
```

## Cierre Formal de Fase 0
**Estado:** ✅ COMPLETADA | ⏳ PENDIENTE | ❌ BLOQUEADA
**Fecha de cierre:** ___________
**Aprobada por:** ___________

---

# FASE 1 — ARQUITECTURA EMPRESARIAL

## Objetivo
Diseñar la arquitectura futura del sistema: lógica, física, de datos, de seguridad y DevOps. Generar ADRs (Architecture Decision Records) para cada decisión clave.

## Alcance
- Arquitectura lógica (capas, módulos, dependencias)
- Arquitectura física (servidores, red, almacenamiento)
- Arquitectura de datos (PostgreSQL + Excel)
- Arquitectura de seguridad (OIDC, RBAC, OWASP)
- Arquitectura DevOps (Docker, CI/CD, Azure)
- ADRs para decisiones críticas

## Actividades

### A1.1 — Arquitectura Lógica
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A1.1.1 | Definir capas: Presentation → API → Service → Domain → Data | Diagrama de capas |
| A1.1.2 | Definir módulos Next.js (pages, components, hooks, services) | Estructura de carpetas |
| A1.1.3 | Definir módulos FastAPI (routers, services, models, schemas) | Estructura de carpetas |
| A1.1.4 | Definir contratos entre capas (interfaces, DTOs) | Diagrama de componentes |

### A1.2 — Arquitectura Física
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A1.2.1 | Definir infraestructura Docker (frontend, backend, DB) | docker-compose.yml |
| A1.2.2 | Definir red interna entre servicios | Diagrama de red |
| A1.2.3 | Definir almacenamiento (volumes para Excel) | Configuración volumes |

### A1.3 — Arquitectura de Datos
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A1.3.1 | Definir estrategia: Excel como fuente de verdad + PostgreSQL para OM/Auth | ADR-001 |
| A1.3.2 | Definir patrón de acceso a Excel (reader service) | Interface de servicio |
| A1.3.3 | Definir patrón de acceso a PostgreSQL (SQLAlchemy async) | Interface de repositorio |

### A1.4 — Arquitectura de Seguridad
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A1.4.1 | Definir flujo OIDC con Azure AD/Microsoft | Diagrama de secuencia |
| A1.4.2 | Definir RBAC: 3 roles (Procesos, Calidad, Desempeño) | Matriz de permisos |
| A1.4.3 | Definir estrategia de JWT (emisión, refresh, revocación) | ADR-002 |

### A1.5 — Arquitectura DevOps
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A1.5.1 | Definir pipeline CI/CD (GitHub Actions) | Workflow YAML |
| A1.5.2 | Definir ambientes (DEV, QA, PROD) | Configuración |
| A1.5.3 | Definir estrategia de despliegue (Docker → Azure) | ADR-003 |

### A1.6 — ADRs
| # | ADR | Decisión |
|---|-----|----------|
| ADR-001 | Persistencia | Excel como fuente de verdad, PostgreSQL para OM/Auth/Usuarios |
| ADR-002 | Frontend | Next.js 14 (App Router, SSR opcional, TypeScript) |
| ADR-003 | Backend | FastAPI (async, Pydantic v2, SQLAlchemy 2.0) |
| ADR-004 | Auth | Microsoft Entra ID (OIDC), JWT en cookie httpOnly |
| ADR-005 | Gráficos | Recharts/Plotly.js en frontend (migrar desde Plotly Python) |
| ADR-006 | Cache | React Query (frontend) + caché en memoria FastAPI (backend) |
| ADR-007 | IA | Claude API (evaluar proveedor), 3 prompts existentes |
| ADR-008 | Despliegue | Docker multi-stage, Azure Container Apps (MVP → producción) |

## Dependencias
- Fase 0 completada (inventario completo)

## Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Decisión de arquitectura rechazada | Baja | Alto | Validar con stakeholders antes de implementar |
| Complejidad de Next.js para equipo Python | Media | Medio | Capacitación en Fase 1, componentes progresivos |
| Costos de Azure superiores al presupuesto | Media | Alto | MVP en Render/VPS, migrar a Azure post-validación |

## Mitigaciones
- Presentar ADRs para aprobación antes de implementar
- Capacitación básica de Next.js en semana 1
- Plan de costos con escenarios (MVP vs producción)

## Entregables

| # | Entregable | Formato |
|---|------------|---------|
| E1.1 | Diagrama de Arquitectura Lógica | Mermaid/draw.io |
| E1.2 | Diagrama de Arquitectura Física | Mermaid/draw.io |
| E1.3 | Diagrama de Arquitectura de Datos | Mermaid/ERD |
| E1.4 | Diagrama de Secuencia Auth | Mermaid |
| E1.5 | 8 ADRs documentados | Markdown |
| E1.6 | Matriz de permisos RBAC | Tabla |

## Casos de Prueba

| ID | Prueba | Resultado Esperado |
|----|--------|-------------------|
| TP-1.1 | Verificar que la arquitectura de capas es consistente | 5 capas definidas |
| TP-1.2 | Verificar que los ADRs tienen Alternativas y Consequences | 8 ADRs completos |
| TP-1.3 | Verificar que la matriz RBAC cubre todos los endpoints | 100% endpoints cubiertos |
| TP-1.4 | Verificar que Docker compose levanta todos los servicios | 3 servicios (fe, be, db) |

## Evidencias Requeridas
- Diagramas de arquitectura en formato Mermaid o draw.io
- ADRs en formato Markdown con Status, Context, Decision, Alternatives, Consequences
- Matriz RBAC completa
- docker-compose.yml funcional

## Auditoría
- Revisión de ADRs con el equipo
- Validación de que la arquitectura soporta todos los requisitos no funcionales
- Verificación de que no hay puntos únicos de falla

## Checklist

- [ ] Arquitectura lógica documentada (5 capas)
- [ ] Arquitectura física documentada (Docker)
- [ ] Arquitectura de datos documentada (Excel + PostgreSQL)
- [ ] Arquitectura de seguridad documentada (OIDC + RBAC)
- [ ] Arquitectura DevOps documentada (CI/CD)
- [ ] 8 ADRs aprobados
- [ ] docker-compose.yml funcional
- [ ] Matriz RBAC completa

## Criterios de Aceptación
1. Arquitectura aprobada por stakeholders
2. Todos los ADRs tienen Alternativas y Consequences
3. docker-compose.yml levanta sin errores
4. La arquitectura soporta los requisitos no funcionales (rendimiento, seguridad, escalabilidad)
5. No existen puntos únicos de falla no mitigados

## Estimación de Esfuerzo
- **Duración:** 1 semana (5 días)
- **Esfuerzo:** 40 horas
- **Responsable:** Arquitecto Empresarial + Arquitecto de Software

## Responsable Sugerido
**Arquitecto Empresarial** (decisiones de alto nivel) + **Especialista en Seguridad** (ADR-004)

## Prompt Específico para Ejecutar la Fase mediante IA

```
Eres un Arquitecto Empresarial Senior. Diseña la arquitectura para migrar
SGIND de Streamlit a Next.js + FastAPI + PostgreSQL.

Contexto del sistema actual:
- Frontend: Streamlit (9 páginas, ~10,000 líneas UI)
- Backend: Python monolítico (core/ + services/)
- BD: Excel como fuente primaria, PostgreSQL para OM
- Auth: Microsoft OIDC (OIDC)
- IA: Claude API (3 prompts)
- ETL: Pipeline batch cada 10 días

Requisitos:
- Frontend: Next.js 14 (App Router, TypeScript)
- Backend: FastAPI (async, SQLAlchemy 2.0)
- BD: PostgreSQL (OM, Auth, Usuarios) + Excel (lectura)
- Auth: Microsoft Entra ID (OIDC), JWT
- Deploy: Docker → Azure Container Apps
- Ambientes: DEV, QA, PROD

Genera:
1. Diagrama de Arquitectura Lógica (capas)
2. Diagrama de Arquitectura Física (Docker)
3. Diagrama de Arquitectura de Datos
4. Diagrama de Secuencia de Autenticación
5. 8 ADRs en formato Markdown
6. Matriz RBAC (3 roles × endpoints)
7. docker-compose.yml funcional

Usa Mermaid para diagramas. Sé específico con tecnologías y versiones.
```

## Cierre Formal de Fase 1
**Estado:** ✅ COMPLETADA | ⏳ PENDIENTE | ❌ BLOQUEADA
**Fecha de cierre:** ___________
**Aprobada por:** ___________

---

# FASE 2 — MODELO DE DATOS

## Objetivo
Diseñar el esquema PostgreSQL: modelo conceptual, lógico y físico. Generar scripts SQL de creación, diccionario de datos y validaciones.

## Alcance
- Modelo conceptual (entidades y relaciones)
- Modelo lógico (tablas, columnas, tipos, constraints)
- Modelo físico (índices, particiones, optimizaciones)
- Migración del esquema SQLite actual
- Compatibilidad con fuentes Excel existentes

## Actividades

### A2.1 — Modelo Conceptual
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A2.1.1 | Identificar entidades: User, Role, RegistroOM, Accion, AuditLog, AIConfig, AIPrompt | Diagrama ER |
| A2.1.2 | Definir cardinalidades y relaciones | Diagrama ER |
| A2.1.3 | Validar contra requisitos del sistema actual | Matriz de cobertura |

### A2.2 — Modelo Lógico
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A2.2.1 | Definir tablas con tipos de datos exactos | Script SQL |
| A2.2.2 | Definir constraints (PK, FK, UNIQUE, CHECK, NOT NULL) | Script SQL |
| A2.2.3 | Definir valores por defecto | Script SQL |
| A2.2.4 | Definir triggers de auditoría | Script SQL |

### A2.3 — Modelo Físico
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A2.3.1 | Definir índices para queries frecuentes | Script SQL |
| A2.3.2 | Analizar necesidad de particionado | Decisión |
| A2.3.3 | Optimizar para queries de lectura (dashboard) | Script SQL |

### A2.4 — Migración SQLite → PostgreSQL
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A2.4.1 | Mapear esquema SQLite actual a PostgreSQL | Script de migración |
| A2.4.2 | Crear script de migración de datos | Script SQL |
| A2.4.3 | Validar integridad post-migración | Reporte de migración |

## Dependencias
- Fase 0 completada (inventario de datos)
- Fase 1 completada (arquitectura aprobada)

## Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Esquema no soporta queries del dashboard | Media | Alto | Prototipar queries críticas antes de implementar |
| Migración SQLite → PostgreSQL pierde datos | Baja | Alto | Script de migración con validación post-migración |
| Performance degradación en Excel con 100K registros | Media | Medio | Caché en capa de servicio + índices PostgreSQL |

## Mitigaciones
- Prototipar las 5 queries más críticas del dashboard
- Script de migración con rollback
- Benchmark de lectura Excel con volumen real

## Entregables

| # | Entregable | Formato |
|---|------------|---------|
| E2.1 | Diagrama ER completo | Mermaid/draw.io |
| E2.2 | Script SQL de creación de tablas | SQL |
| E2.3 | Diccionario de datos completo | Tabla Markdown |
| E2.4 | Script de migración SQLite → PostgreSQL | SQL |
| E2.5 | Script de migración de datos | SQL/Python |
| E2.6 | Índices y optimizaciones | SQL |

## Casos de Prueba

| ID | Prueba | Resultado Esperado |
|----|--------|-------------------|
| TP-2.1 | Ejecutar script de creación en PostgreSQL limpio | Tablas creadas sin errores |
| TP-2.2 | Insertar registro OM y verificar UPSERT | Funciona con constraint UNIQUE |
| TP-2.3 | Ejecutar query de dashboard principal | Resultado en < 500ms |
| TP-2.4 | Migrar datos SQLite → PostgreSQL | 100% registros migrados |
| TP-2.5 | Verificar integridad referencial | Sin FK violations |

## Evidencias Requeridas
- Script SQL ejecutado sin errores
- Diagrama ER validado
- Benchmark de queries (5 críticas)
- Reporte de migración SQLite → PostgreSQL

## Auditoría
- Revisión de normalización (3NF mínimo)
- Verificación de que no hay redundancias
- Validación de que el esquema soporta todos los endpoints

## Checklist

- [ ] Modelo conceptual documentado
- [ ] Modelo lógico documentado
- [ ] Modelo físico documentado
- [ ] Script SQL de creación probado
- [ ] Diccionario de datos completo
- [ ] Script de migración probado
- [ ] Índices definidos
- [ ] 5 queries críticas prototipadas

## Criterios de Aceptación
1. Esquema PostgreSQL creado sin errores
2. Todas las entidades del sistema actual están representadas
3. UPSERT funciona correctamente (ON CONFLICT)
4. Las 5 queries críticas ejecutan en < 500ms
5. Migración SQLite → PostgreSQL completa con 100% de registros

## Estimación de Esfuerzo
- **Duración:** 1 semana (5 días)
- **Esfuerzo:** 40 horas
- **Responsable:** Arquitecto de Datos + Backend Developer

## Responsable Sugerido
**Arquitecto de Software** (diseño) + **Backend Developer** (implementación SQL)

## Prompt Específico para Ejecutar la Fase mediante IA

```
Eres un Arquitecto de Datos Senior. Diseña el esquema PostgreSQL para SGIND.

El sistema actual tiene estas entidades en SQLite:
- registros_om: id, id_indicador, nombre_indicador, proceso, periodo, anio,
  tiene_om, tipo_accion, numero_om, comentario, registrado_por, fecha_registro
  UNIQUE(id_indicador, periodo, anio)

Nuevas entidades necesarias:
- users: id (UUID), email, name, role, azure_oid, created_at, updated_at
- audit_log: id, user_id, action, entity, entity_id, details (JSONB), created_at
- ai_configs: id, provider, model, api_key_encrypted, temperature, max_tokens, is_active
- ai_prompts: id, name, template, max_tokens, is_active

El sistema lee ~100,000 registros desde Excel (Resultados Consolidados.xlsx).
PostgreSQL solo almacena: OM, usuarios, roles, auditoría, configuración IA.

Genera:
1. Diagrama ER en Mermaid
2. Script SQL completo (CREATE TABLE, constraints, indexes, triggers)
3. Diccionario de datos
4. Script de migración SQLite → PostgreSQL
5. Queries de dashboard más críticas
```

## Cierre Formal de Fase 2
**Estado:** ✅ COMPLETADA | ⏳ PENDIENTE | ❌ BLOQUEADA
**Fecha de cierre:** ___________
**Aprobada por:** ___________

---

# FASE 3 — DISEÑO UX/UI

## Objetivo
Diseñar la experiencia de usuario: wireframes, mockups, navegación, sistema de diseño, paleta corporativa, responsive.

## Alcance
- Wireframes de baja fidelidad para las 9 páginas
- Mockups de alta fidelidad para las 3 páginas principales
- Sistema de diseño (colores, tipografía, espaciado, componentes)
- Navegación y arquitectura de información
- Responsive (desktop, tablet, móvil)

## Actividades

### A3.1 — Investigación de UX
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A3.1.1 | Analizar UX actual del Streamlit (fricciones, mejoras) | Reporte de auditoría UX |
| A3.1.2 | Definir personas de usuario (4 roles) | Personas documentadas |
| A3.1.3 | Definir journey maps por rol | Journey maps |

### A3.2 — Sistema de Diseño
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A3.2.1 | Definir paleta de colores corporativa | Paleta documentada |
| A3.2.2 | Definir tipografía | Guía de tipografía |
| A3.2.3 | Definir espaciado y grid | Guía de espaciado |
| A3.2.4 | Definir componentes base (Button, Card, Table, Filter, KPI) | Catálogo de componentes |
| A3.2.5 | Definir iconografía | Catálogo de iconos |

### A3.3 — Wireframes
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A3.3.1 | Wireframe Resumen General (dashboard principal) | Wireframe |
| A3.3.2 | Wireframe CMI Estratégico | Wireframe |
| A3.3.3 | Wireframe CMI por Procesos | Wireframe |
| A3.3.4 | Wireframe Gestión OM | Wireframe |
| A3.3.5 | Wireframe Plan de Mejoramiento | Wireframe |
| A3.3.6 | Wireframe Seguimiento Reportes | Wireframe |
| A3.3.7 | Wireframe PDI Acreditación | Wireframe |
| A3.3.8 | Wireframe Tablero Operativo | Wireframe |
| A3.3.9 | Wireframe Diagnóstico | Wireframe |

### A3.4 — Mockups
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A3.4.1 | Mockup Resumen General (desktop) | Mockup |
| A3.4.2 | Mockup Resumen General (responsive) | Mockup |
| A3.4.3 | Mockup CMI Estratégico (desktop) | Mockup |
| A3.4.4 | Mockup Gestión OM (desktop + mobile) | Mockup |

### A3.5 — Navegación
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A3.5.1 | Definir estructura de menú lateral | Diagrama de navegación |
| A3.5.2 | Definir breadcrumbs | Patrón de breadcrumbs |
| A3.5.3 | Definir responsive behavior | Guía responsive |

## Dependencias
- Fase 0 completada (inventario funcional)
- Fase 1 completada (arquitectura aprobada)

## Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| No hay diseñador UX disponible | Alta | Alto | Usar shadcn/ui como base + personalización corporativa |
| Cambios de UX retrasan desarrollo | Media | Medio | Definir UX antes de Fase 5, freeze de diseño |
| Responsive complejo para dashboards | Media | Medio | Priorizar desktop, responsive progresivo |

## Mitigaciones
- Usar shadcn/ui (componentes pre-diseñados, accesibles)
- Definir design system completo antes de implementar
- Prototipar responsive con CSS Grid/Tailwind

## Entregables

| # | Entregable | Formato |
|---|------------|---------|
| E3.1 | Paleta de colores corporativa | Tabla + hex codes |
| E3.2 | Guía de tipografía | Tabla |
| E3.3 | Guía de espaciado y grid | Tabla |
| E3.4 | Wireframes (9 páginas) | Imágenes o ASCII |
| E3.5 | Mockups (4 pantallas clave) | Imágenes |
| E3.6 | Diagrama de navegación | Mermaid |
| E3.7 | Catálogo de componentes base | Tabla |

## Casos de Prueba

| ID | Prueba | Resultado Esperado |
|----|--------|-------------------|
| TP-3.1 | Verificar contraste WCAG AA en todos los colores | 100% contraste ≥ 4.5:1 |
| TP-3.2 | Verificar que el diseño es responsive | Desktop + tablet + móvil |
| TP-3.3 | Verificar que los wireframes cubren todas las páginas | 9/9 páginas |
| TP-3.4 | Verificar que el sistema de diseño es consistente | Colores, tipografía, espaciado definidos |

## Evidencias Requeridas
- Paleta de colores con valores hex
- Wireframes de todas las páginas
- Mockups de las 4 pantallas clave
- Diagrama de navegación
- Catálogo de componentes

## Auditoría
- Revisión de accesibilidad (WCAG 2.1 AA)
- Validación de responsive en 3 breakpoints
- Verificación de consistencia visual

## Checklist

- [ ] Paleta de colores definida (corporativa)
- [ ] Tipografía definida
- [ ] Espaciado y grid definidos
- [ ] 9 wireframes creados
- [ ] 4 mockups creados
- [ ] Navegación documentada
- [ ] Componentes base definidos
- [ ] WCAG AA verificado

## Criterios de Aceptación
1. Diseño aprobado por stakeholders
2. WCAG 2.1 AA compliance
3. Responsive en 3 breakpoints
4. 9 wireframes completos
5. 4 mockups de alta fidelidad

## Estimación de Esfuerzo
- **Duración:** 1.5 semanas (8 días)
- **Esfuerzo:** 60 horas
- **Responsable:** Especialista UX/UI

## Responsable Sugerido
**Especialista UX/UI** (diseño) + **Product Owner** (validación)

## Prompt Específico para Ejecutar la Fase mediante IA

```
Eres un Especialista UX/UI Senior. Diseña la experiencia de usuario para
SGIND (React + Next.js).

El sistema actual tiene 9 páginas en Streamlit:
1. Resumen General - Dashboard principal con KPIs, treeline, semáforo
2. CMI Estratégico - Balanced Scorecard, 4 perspectivas, tabs
3. CMI por Procesos - Vista por proceso/subproceso, alertas
4. Plan de Mejoramiento - Indicadores CNA, tracking OM
5. Gestión OM - CRUD de Oportunidades de Mejora
6. Seguimiento Reportes - Tracking mensual
7. PDI Acreditación - Indicadores acreditación
8. Tablero Operativo - Kanban Level 3
9. Diagnóstico - Validación datos

Colores corporativos del Politécnico Grancolombiano: [consultar]
Usuarios: 4 roles (Directivos, Líderes de Proceso, Calidad, Analistas)

Genera:
1. Paleta de colores corporativa con hex codes
2. Guía de tipografía (familias, tamaños, pesos)
3. Wireframes ASCII para las 9 páginas
4. Diagrama de navegación (sidebar + breadcrumbs)
5. Catálogo de componentes base (Button, Card, Table, KPI, Filter)
6. Guía responsive (3 breakpoints)
```

## Cierre Formal de Fase 3
**Estado:** ✅ COMPLETADA | ⏳ PENDIENTE | ❌ BLOQUEADA
**Fecha de cierre:** ___________
**Aprobada por:** ___________

---

# FASE 4 — BACKEND (FastAPI)

## Objetivo
Construir el backend API con FastAPI: estructura modular, ORM, autenticación, endpoints para todas las funcionalidades del sistema.

## Alcance
- Estructura modular FastAPI (routers, services, models, schemas)
- ORM SQLAlchemy 2.0 con PostgreSQL
- Autenticación Microsoft OIDC + JWT
- Endpoints para las 9 páginas + ETL + IA
- Swagger/OpenAPI documentado
- Tests unitarios y de integración (cobertura 80%)

## Actividades

### A4.1 — Estructura Base
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A4.1.1 | Crear proyecto FastAPI con estructura modular | Estructura de carpetas |
| A4.1.2 | Configurar SQLAlchemy 2.0 (async) | Configuración DB |
| A4.1.3 | Configurar Pydantic v2 (schemas) | Schemas base |
| A4.1.4 | Configurar CORS, middleware, error handling | Configuración |
| A4.1.5 | Configurar health check | Endpoint /health |

### A4.2 — Servicio de Excel
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A4.2.1 | Crear ExcelReaderService (lee todos los Excel del proyecto) | Servicio |
| A4.2.2 | Implementar caché de lectura (TTL configurable) | Caché |
| A4.2.3 | Implementar validación de archivos | Validación |

### A4.3 — Auth Endpoints
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A4.3.1 | Implementar `/api/auth/login` (Microsoft OIDC redirect) | Endpoint |
| A4.3.2 | Implementar `/api/auth/callback` (OIDC callback) | Endpoint |
| A4.3.3 | Implementar `/api/auth/me` (current user) | Endpoint |
| A4.3.4 | Implementar `/api/auth/logout` | Endpoint |
| A4.3.5 | Implementar middleware JWT validation | Middleware |

### A4.4 — Dashboard Endpoints
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A4.4.1 | `GET /api/dashboard/kpis` — KPIs principales | Endpoint |
| A4.4.2 | `GET /api/dashboard/treeline` — Treeline/waterfall | Endpoint |
| A4.4.3 | `GET /api/dashboard/semaphore` — Semáforo por categoría | Endpoint |
| A4.4.4 | `GET /api/dashboard/trend` — Tendencia histórica | Endpoint |
| A4.4.5 | `GET /api/indicators` — Lista indicadores con filtros | Endpoint |
| A4.4.6 | `GET /api/indicators/{id}` — Detalle indicador | Endpoint |

### A4.5 — CMI Endpoints
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A4.5.1 | `GET /api/cmi/estrategico` — CMI estratégico (4 perspectivas) | Endpoint |
| A4.5.2 | `GET /api/cmi/procesos` — CMI por procesos | Endpoint |
| A4.5.3 | `GET /api/cmi/alertas` — Alertas de indicadores | Endpoint |

### A4.6 — OM Endpoints
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A4.6.1 | `GET /api/om` — Listar OM | Endpoint |
| A4.6.2 | `POST /api/om` — Crear OM | Endpoint |
| A4.6.3 | `PUT /api/om/{id}` — Actualizar OM | Endpoint |
| A4.6.4 | `DELETE /api/om/{id}` — Eliminar OM | Endpoint |

### A4.7 — IA Endpoints
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A4.7.1 | `POST /api/ia/analyze` — Análisis de texto | Endpoint |
| A4.7.2 | `POST /api/ia/ficha` — Análisis ficha CMI | Endpoint |
| A4.7.3 | `POST /api/ia/linea` — Análisis línea CMI | Endpoint |
| A4.7.4 | `POST /api/ia/chat` — Chat con datos (NUEVO) | Endpoint |
| A4.7.5 | `GET /api/ia/anomalies` — Detección anomalías (NUEVO) | Endpoint |

### A4.8 — ETL Endpoints
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A4.8.1 | `POST /api/etl/run` — Ejecutar ETL | Endpoint |
| A4.8.2 | `GET /api/etl/status` — Estado del ETL | Endpoint |
| A4.8.3 | `POST /api/etl/download-kawak` — Descarga manual Kawak | Endpoint |

### A4.9 — Export Endpoints
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A4.9.1 | `GET /api/export/excel` — Exportar a Excel | Endpoint |
| A4.9.2 | `GET /api/export/pdf` — Exportar ficha a PDF | Endpoint |

### A4.10 — Tests
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A4.10.1 | Tests unitarios para services | pytest |
| A4.10.2 | Tests de integración para endpoints | pytest |
| A4.10.3 | Tests de seguridad (auth, RBAC) | pytest |
| A4.10.4 | Coverage ≥ 80% | Reporte de coverage |

## Dependencias
- Fase 0 completada
- Fase 1 completada (arquitectura)
- Fase 2 completada (modelo de datos)

## Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Lectura Excel lenta con 100K registros | Media | Alto | Caché agresivo + lazy loading |
| Auth OIDC complejo de configurar | Media | Medio | Seguir guía oficial Microsoft |
| Tests incompletos | Alta | Medio | TDD, coverage gate en CI |

## Mitigaciones
- Caché en memoria con TTL (ya existe patrón en Streamlit)
- Usar biblioteca `msal` para OIDC
- TDD: escribir tests antes que la implementación

## Entregables

| # | Entregable | Formato |
|---|------------|---------|
| E4.1 | Backend FastAPI funcional | Código |
| E4.2 | Swagger/OpenAPI documentado | URL /docs |
| E4.3 | Tests unitarios (cobertura 80%) | pytest |
| E4.4 | Tests de integración | pytest |
| E4.5 | Reporte de coverage | HTML |

## Casos de Prueba

| ID | Prueba | Resultado Esperado |
|----|--------|-------------------|
| TP-4.1 | GET /api/health retorna 200 | {"status": "healthy"} |
| TP-4.2 | GET /api/dashboard/kpis sin auth retorna 401 | 401 Unauthorized |
| TP-4.3 | GET /api/om con role "procesos" retorna 403 | 403 Forbidden |
| TP-4.4 | POST /api/om con role "calidad" crea registro | 201 Created |
| TP-4.5 | GET /api/indicators con filtro año retorna datos | 200 + JSON |
| TP-4.6 | POST /api/ia/analyze con texto retorna análisis | 200 + JSON |
| TP-4.7 | Coverage ≥ 80% | Pass |

## Evidencias Requeridas
- Código fuente FastAPI
- Swagger UI funcional
- Tests ejecutándose
- Reporte de coverage ≥ 80%

## Auditoría
- Revisión de seguridad (OWASP Top 10)
- Revisión de performance (response time < 500ms)
- Revisión de código (linting, type checking)

## Checklist

- [ ] Estructura modular creada
- [ ] SQLAlchemy ORM configurado
- [ ] Auth OIDC implementado
- [ ] JWT middleware funcional
- [ ] 30+ endpoints implementados
- [ ] Swagger documentado
- [ ] Tests unitarios (80%+ coverage)
- [ ] Tests de integración
- [ ] Linting sin errores
- [ ] Type checking sin errores

## Criterios de Aceptación
1. Backend ejecuta sin errores
2. Swagger/OpenAPI funcional con todos los endpoints documentados
3. Auth OIDC funcional (login/logout/callback)
4. RBAC funcional (3 roles, permisos correctos)
5. Coverage ≥ 80%
6. Response time < 500ms para queries estándar
7. Sin vulnerabilidades OWASP Top 10

## Estimación de Esfuerzo
- **Duración:** 4 semanas (20 días)
- **Esfuerzo:** 160 horas
- **Responsable:** Backend Developer Senior

## Responsable Sugerido
**Ingeniero Full Stack Senior** (implementación) + **Especialista en Seguridad** (revisión)

## Prompt Específico para Ejecutar la Fase mediante IA

```
Eres un Ingeniero Full Stack Senior especializado en FastAPI. Construye el
backend API para SGIND.

Requisitos:
- FastAPI con estructura modular (routers/, services/, models/, schemas/)
- SQLAlchemy 2.0 async con PostgreSQL
- Auth: Microsoft OIDC (msal) + JWT
- RBAC: 3 roles (procesos=lectura, calidad=admin, desempeño=admin)
- Endpoints: dashboard, indicators, CMI, OM, IA, ETL, export
- Excel: servicio para leer archivos Excel del proyecto
- Tests: pytest con coverage ≥ 80%

Archivos del sistema actual a migrar:
- core/config.py → backend/app/core/config.py
- core/semantica.py → backend/app/core/semantica.py
- core/calculos.py → backend/app/core/calculos.py
- core/db/ → backend/app/models/
- services/ai_analysis.py → backend/app/services/ai_service.py
- services/data_loader.py → backend/app/services/excel_reader.py

Genera:
1. Estructura de carpetas completa
2. Archivos base (main.py, config.py, database.py)
3. Todos los endpoints con lógica de negocio
4. Tests para cada endpoint
5. docker-compose.yml funcional

Sé específico con versiones de dependencias.
```

## Cierre Formal de Fase 4
**Estado:** ✅ COMPLETADA | ⏳ PENDIENTE | ❌ BLOQUEADA
**Fecha de cierre:** ___________
**Aprobada por:** ___________

---

# FASE 5 — FRONTEND (Next.js)

## Objetivo
Construir la interfaz de usuario con Next.js 14: layout, navegación, dashboards, formularios, tablas, gráficos, responsive.

## Alcance
- Layout base (sidebar, header, footer)
- 9 páginas completas
- Componentes reutilizables (KPI, Chart, Table, Filter, Card)
- Gráficos (Recharts/Plotly.js)
- Formularios (Gestión OM)
- Tablas con sorting, filtering, paginación
- Responsive (3 breakpoints)
- Conexión con backend FastAPI

## Actividades

### A5.1 — Setup Proyecto
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A5.1.1 | Crear proyecto Next.js 14 (App Router, TypeScript) | package.json |
| A5.1.2 | Configurar Tailwind CSS + shadcn/ui | Configuración |
| A5.1.3 | Configurar React Query (data fetching) | Configuración |
| A5.1.4 | Configurar Zustand (estado global) | Configuración |
| A5.1.5 | Configurar Axios (HTTP client) | Configuración |

### A5.2 — Layout y Navegación
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A5.2.1 | Crear layout principal (sidebar + header + content) | Layout |
| A5.2.2 | Crear sidebar con menú de 9 páginas | Sidebar |
| A5.2.3 | Crear header con usuario + rol + logout | Header |
| A5.2.4 | Implementar responsive sidebar (overlay en móvil) | Responsive |
| A5.2.5 | Implementar breadcrumbs | Breadcrumbs |

### A5.3 — Design System
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A5.3.1 | Implementar paleta de colores en Tailwind | tailwind.config.ts |
| A5.3.2 | Crear componentes base (Button, Card, Badge, Input) | Componentes |
| A5.3.3 | Crear componente KPI Card | Componente |
| A5.3.4 | Crear componente Filter Panel | Componente |
| A5.3.5 | Crear componente Data Table | Componente |
| A5.3.6 | Crear componente Chart wrapper | Componente |

### A5.4 — Página: Resumen General
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A5.4.1 | KPIs principales (5 cards) | Página |
| A5.4.2 | Selector de modo (Indicadores/Proyectos/Retos/Consolidado) | Página |
| A5.4.3 | Treeline/waterfall chart | Gráfico |
| A5.4.4 | Tabla de indicadores con sorting | Tabla |
| A5.4.5 | Filtros (año, período) | Filtros |
| A5.4.6 | Exportación Excel | Botón |

### A5.5 — Página: CMI Estratégico
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A5.5.1 | Tabs (Resumen/Líneas/Listado/Alertas) | Página |
| A5.5.2 | Vista por perspectiva (4 perspectivas) | Página |
| A5.5.3 | Análisis IA por indicador | Componente IA |
| A5.5.4 | Filtros (línea, objetivo, período) | Filtros |

### A5.6 — Página: CMI por Procesos
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A5.6.1 | Vista por proceso/subproceso | Página |
| A5.6.2 | Datos de calidad | Página |
| A5.6.3 | KPIs de proceso | KPIs |
| A5.6.4 | Alertas | Alertas |

### A5.7 — Página: Plan de Mejoramiento
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A5.7.1 | Indicadores CNA por factor | Página |
| A5.7.2 | Tracking de OM | Página |
| A5.7.3 | Filtros (factor, estado OM) | Filtros |

### A5.8 — Página: Gestión OM
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A5.8.1 | Tabla de OM | Tabla |
| A5.8.2 | Modal de creación/edición | Modal |
| A5.8.3 | Análisis IA al crear/editar | Componente IA |
| A5.8.4 | Avance de OM | Página |

### A5.9 — Páginas Secundarias
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A5.9.1 | Seguimiento Reportes | Página |
| A5.9.2 | PDI Acreditación | Página |
| A5.9.3 | Tablero Operativo | Página |
| A5.9.4 | Diagnóstico | Página |

### A5.10 — IA en Frontend
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A5.10.1 | Componente de chat con datos | Componente |
| A5.10.2 | Panel de recomendaciones | Componente |
| A5.10.3 | Indicador de anomalías | Componente |

## Dependencias
- Fase 3 completada (diseño UX/UI)
- Fase 4 completada (backend API)

## Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Complejidad de gráficos en React | Media | Medio | Usar Recharts (más simple) o Plotly.js |
| Performance con muchos datos | Media | Alto | Paginación server-side + virtual scrolling |
| Responsive complejo para dashboards | Media | Medio | Mobile-first, progresivo |

## Mitigaciones
- Usar Recharts para gráficos simples, Plotly.js para complejos
- React Query con paginación + staleTime
- Tailwind responsive classes

## Entregables

| # | Entregable | Formato |
|---|------------|---------|
| E5.1 | Frontend Next.js funcional | Código |
| E5.2 | 9 páginas implementadas | Páginas |
| E5.3 | Componentes reutilizables | Librería |
| E5.4 | Tests de responsive | Evidencia |
| E5.5 | Lighthouse score > 90 | Reporte |

## Casos de Prueba

| ID | Prueba | Resultado Esperado |
|----|--------|-------------------|
| TP-5.1 | Navegación entre 9 páginas funciona | Sin errores |
| TP-5.2 | Responsive en desktop (1024px+) | Layout correcto |
| TP-5.3 | Responsive en tablet (768-1023px) | Layout correcto |
| TP-5.4 | Responsive en móvil (< 768px) | Layout correcto |
| TP-5.5 | Filtros retornan datos | API call + render |
| TP-5.6 | Gráficos renderizan | Sin errores |
| TP-5.7 | Exportación Excel descarga archivo | Archivo generado |
| TP-5.8 | Lighthouse performance > 90 | Score ≥ 90 |

## Evidencias Requeridas
- Código fuente Next.js
- Screenshots de cada página
- Evidencia de responsive (3 breakpoints)
- Reporte Lighthouse

## Auditoría
- Lighthouse audit (performance, accessibility, best practices, SEO)
- Revisión de accesibilidad (WCAG 2.1 AA)
- Revisión de performance (bundle size, load time)

## Checklist

- [ ] Proyecto Next.js configurado
- [ ] Tailwind + shadcn/ui configurados
- [ ] Layout principal funcional
- [ ] Sidebar responsive funcional
- [ ] 9 páginas implementadas
- [ ] Componentes base creados
- [ ] Gráficos funcionales
- [ ] Formularios funcionales
- [ ] Tablas con sorting/filtering
- [ ] Responsive verificado
- [ ] Lighthouse > 90

## Criterios de Aceptación
1. Todas las 9 páginas funcionales
2. Responsive en 3 breakpoints
3. Lighthouse score > 90
4. Navegación sin errores
5. Conexión con backend funcional
6. Exportación Excel funcional

## Estimación de Esfuerzo
- **Duración:** 5 semanas (25 días)
- **Esfuerzo:** 200 horas
- **Responsable:** Frontend Developer Senior

## Responsable Sugerido
**Ingeniero Full Stack Senior** (implementación) + **Especialista UX/UI** (validación)

## Prompt Específico para Ejecutar la Fase mediante IA

```
Eres un Ingeniero Frontend Senior especializado en Next.js. Construye el
frontend para SGIND.

Requisitos:
- Next.js 14 (App Router, TypeScript)
- Tailwind CSS + shadcn/ui
- React Query (data fetching)
- Zustand (estado global)
- Recharts (gráficos)
- Responsive (desktop, tablet, móvil)

Las 9 páginas a implementar:
1. Resumen General - Dashboard con KPIs, treeline, semáforo
2. CMI Estratégico - Tabs, 4 perspectivas, análisis IA
3. CMI por Procesos - Vista por proceso, alertas
4. Plan de Mejoramiento - CNA, tracking OM
5. Gestión OM - CRUD con modal, IA
6. Seguimiento Reportes - Tracking mensual
7. PDI Acreditación - Indicadores acreditación
8. Tablero Operativo - Kanban
9. Diagnóstico - Validación datos

Backend: FastAPI en http://localhost:8000

Genera:
1. Estructura de carpetas completa
2. Layout con sidebar responsive
3. Todas las páginas con componentes
4. Conexión con backend (React Query)
5. Responsive completo
6. Tests básicos

Sé específico con implementación de cada componente.
```

## Cierre Formal de Fase 5
**Estado:** ✅ COMPLETADA | ⏳ PENDIENTE | ❌ BLOQUEADA
**Fecha de cierre:** ___________
**Aprobada por:** ___________

---

# FASE 6 — AUTENTICACIÓN Y SEGURIDAD

## Objetivo
Implementar autenticación completa con Azure AD/Microsoft 365, RBAC, auditoría, y validación OWASP Top 10.

## Alcance
- Integración Azure AD (Microsoft Entra ID)
- JWT (emisión, validación, refresh)
- RBAC (3 roles: Procesos, Calidad, Desempeño)
- Auditoría de acciones
- Headers de seguridad
- OWASP Top 10 validation

## Actividades

### A6.1 — Azure AD Integration
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A6.1.1 | Registrar aplicación en Azure AD | Configuración Azure |
| A6.1.2 | Configurar OIDC flow (authorization code) | Configuración |
| A6.1.3 | Implementar login redirect | Endpoint |
| A6.1.4 | Implementar callback handler | Endpoint |
| A6.1.5 | Implementar token exchange | Servicio |

### A6.2 — JWT
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A6.2.1 | Implementar JWT signing (RS256) | Servicio |
| A6.2.2 | Implementar JWT validation middleware | Middleware |
| A6.2.3 | Implementar refresh token flow | Endpoint |
| A6.2.4 | Implementar logout (token revocation) | Endpoint |

### A6.3 — RBAC
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A6.3.1 | Implementar roles en PostgreSQL (users table) | Migración |
| A6.3.2 | Crear decorator `require_role()` | Middleware |
| A6.3.3 | Aplicar a cada endpoint según matriz RBAC | Endpoints |
| A6.3.4 | Implementar endpoints de gestión de usuarios | CRUD |

### A6.4 — Auditoría
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A6.4.1 | Implementar audit_log table | Migración |
| A6.4.2 | Crear middleware de auditoría | Middleware |
| A6.4.3 | Implementar query de auditoría | Endpoint |

### A6.5 — Seguridad
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A6.5.1 | Configurar headers de seguridad (HSTS, CSP, X-Frame) | Middleware |
| A6.5.2 | Implementar rate limiting | Middleware |
| A6.5.3 | Configurar CORS restrictivo | Configuración |
| A6.5.4 | Validar OWASP Top 10 | Checklist |

## Dependencias
- Fase 2 completada (modelo de datos con users, audit_log)
- Fase 4 completada (backend base)

## Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Azure AD configuration compleja | Media | Alto | Seguir guía oficial, testing con usuario de prueba |
| JWT key management | Baja | Alto | Usar RS256 con rotación de claves |
| RBAC incompleto | Media | Alto | Matriz RBAC completa antes de implementar |

## Mitigaciones
- Usar librería `msal` para Azure AD
- JWT con expiración corta (15 min) + refresh token
- Auditoría completa de cada endpoint

## Entregables

| # | Entregable | Formato |
|---|------------|---------|
| E6.1 | Auth OIDC funcional | Código |
| E6.2 | JWT middleware funcional | Código |
| E6.3 | RBAC implementado | Código |
| E6.4 | Auditoría implementada | Código |
| E6.5 | Reporte OWASP Top 10 | Checklist |
| E6.6 | Tests de seguridad | pytest |

## Casos de Prueba

| ID | Prueba | Resultado Esperado |
|----|--------|-------------------|
| TP-6.1 | Login con Microsoft redirige correctamente | 302 → Azure AD |
| TP-6.2 | Callback genera JWT válido | 200 + JWT |
| TP-6.3 | Request sin JWT retorna 401 | 401 |
| TP-6.4 | Request con JWT expirado retorna 401 | 401 |
| TP-6.5 | User con role "procesos" no puede crear OM | 403 |
| TP-6.6 | User con role "calidad" puede crear OM | 201 |
| TP-6.7 | Acción de auditoría registrada | audit_log entry |
| TP-6.8 | Rate limiting activo | 429 después de N requests |

## Evidencias Requeridas
- Auth funcional (login/logout/callback)
- JWT validation funcionando
- RBAC aplicado a todos los endpoints
- Auditoría registrando acciones
- Reporte OWASP Top 10

## Auditoría
- Penetration testing básico
- OWASP Top 10 checklist
- Revisión de código de seguridad

## Checklist

- [ ] Azure AD registrado
- [ ] OIDC flow funcional
- [ ] JWT signing/validation
- [ ] Refresh token flow
- [ ] RBAC (3 roles) implementado
- [ ] Auditoría funcionando
- [ ] Headers de seguridad
- [ ] Rate limiting
- [ ] OWASP Top 10 validado

## Criterios de Aceptación
1. Login/logout funcional con Microsoft
2. JWT con expiración y refresh
3. RBAC aplicado a 100% de endpoints
4. Auditoría registrando todas las acciones CRUD
5. Sin vulnerabilidades OWASP Top 10 críticas
6. Tests de seguridad pasando

## Estimación de Esfuerzo
- **Duración:** 2 semanas (10 días)
- **Esfuerzo:** 80 horas
- **Responsable:** Especialista en Seguridad + Backend Developer

## Responsable Sugerido
**Especialista en Seguridad** (diseño + auditoría) + **Backend Developer** (implementación)

## Prompt Específico para Ejecutar la Fase mediante IA

```
Eres un Especialista en Seguridad Senior. Implementa autenticación y
seguridad para SGIND.

Requisitos:
- Azure AD (Microsoft Entra ID) OIDC
- JWT (RS256, 15 min expiry, refresh token)
- RBAC: 3 roles (procesos=lectura, calidad=admin, desempeño=admin)
- Auditoría: log de cada acción CRUD
- OWASP Top 10: mitigaciones completas

Genera:
1. Configuración Azure AD (pseudocódigo de registro)
2. OIDC flow (login redirect, callback, token exchange)
3. JWT middleware (signing, validation, refresh)
4. RBAC decorator + matriz de permisos
5. Audit middleware
6. Headers de seguridad
7. Rate limiting
8. Tests de seguridad
9. OWASP Top 10 checklist completo
```

## Cierre Formal de Fase 6
**Estado:** ✅ COMPLETADA | ⏳ PENDIENTE | ❌ BLOQUEADA
**Fecha de cierre:** ___________
**Aprobada por:** ___________

---

# FASE 7 — MIGRACIÓN DE DATOS

## Objetivo
Migrar datos históricos, configurar ETL pipeline, automatizar descarga de Kawak cada 10 días, y asegurar integridad de datos.

## Alcance
- Migración SQLite → PostgreSQL (registros OM)
- Configuración de ETL pipeline en FastAPI
- Automatización de descarga Kawak (cada 10 días)
- Validación de integridad (99.9% consistencia)
- Conciliación con sistema Streamlit

## Actividades

### A7.1 — Migración SQLite → PostgreSQL
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A7.1.1 | Ejecutar script de migración de esquema | Tablas creadas |
| A7.1.2 | Migrar datos de registros_om | Datos migrados |
| A7.1.3 | Migrar datos de acciones | Datos migrados |
| A7.1.4 | Validar integridad post-migración | Reporte |

### A7.2 — ETL Pipeline en FastAPI
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A7.2.1 | Portar lógica ETL de Python a FastAPI service | Servicio |
| A7.2.2 | Implementar background tasks para ETL | Background task |
| A7.2.3 | Implementar endpoints de control ETL | Endpoints |
| A7.2.4 | Implementar notificaciones de finalización | Notificación |

### A7.3 — Automatización Kawak
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A7.3.1 | Implementar descarga automática Kawak (cada 10 días) | Cron job |
| A7.3.2 | Implementar interfaz web para descarga manual | UI |
| A7.3.3 | Implementar validación de archivos descargados | Validación |

### A7.4 — Validación
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A7.4.1 | Comparar datos Streamlit vs React (100 indicadores muestra) | Reporte |
| A7.4.2 | Validar fórmulas de cumplimiento | Verificación |
| A7.4.3 | Validar categorías (Peligro/Alerta/Cumplimiento/Sobrecumplimiento) | Verificación |

## Dependencias
- Fase 2 completada (modelo de datos)
- Fase 4 completada (backend con endpoints ETL)
- Fase 6 completada (auth para endpoints protegidos)

## Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Pérdida de datos en migración | Baja | Alto | Backup completo antes de migrar |
| ETL pipeline falla en nuevo entorno | Media | Alto | Tests de integración ETL |
| Descarga Kawak falla | Media | Medio | Retry + alertas |

## Mitigaciones
- Backup completo antes de migración
- Tests E2E del pipeline ETL
- Monitoreo de descargas Kawak

## Entregables

| # | Entregable | Formato |
|---|------------|---------|
| E7.1 | Datos migrados (SQLite → PostgreSQL) | Reporte |
| E7.2 | ETL pipeline en FastAPI | Código |
| E7.3 | Automatización Kawak | Código |
| E7.4 | Reporte de conciliación | Documento |

## Casos de Prueba

| ID | Prueba | Resultado Esperado |
|----|--------|-------------------|
| TP-7.1 | Migración SQLite → PostgreSQL completa | 100% registros |
| TP-7.2 | UPSERT en PostgreSQL funciona | Sin duplicados |
| TP-7.3 | ETL pipeline ejecuta en FastAPI | Output generado |
| TP-7.4 | Descarga Kawak automática funciona | Archivo descargado |
| TP-7.5 | Conciliación Streamlit vs React | 99.9% consistencia |

## Evidencias Requeridas
- Datos migrados exitosamente
- ETL ejecutándose en FastAPI
- Descarga Kawak automatizada
- Reporte de conciliación

## Auditoría
- Verificación de integridad de datos
- Comparación de resultados entre sistemas
- Validación de fórmulas de cumplimiento

## Checklist

- [ ] SQLite migrado a PostgreSQL
- [ ] Datos OM migrados
- [ ] Datos acciones migrados
- [ ] ETL pipeline funcional
- [ ] Kawak automatizado (cada 10 días)
- [ ] Descarga manual funcional
- [ ] Conciliación 99.9%

## Criterios de Aceptación
1. 100% de datos migrados
2. ETL pipeline ejecuta correctamente
3. Kawak se descarga automáticamente cada 10 días
4. Conciliación ≥ 99.9% con sistema Streamlit
5. Sin pérdida de datos

## Estimación de Esfuerzo
- **Duración:** 2 semanas (10 días)
- **Esfuerzo:** 80 horas
- **Responsable:** Backend Developer + Data Engineer

## Responsable Sugerido
**Backend Developer** (implementación) + **Data Engineer** (validación)

## Prompt Específico para Ejecutar la Fase mediante IA

```
Eres un Data Engineer Senior. Migra los datos de SGIND de Streamlit a
la nueva arquitectura.

Sistema actual:
- SQLite: data/db/registros_om.db (tabla registros_om)
- Excel: data/output/Resultados Consolidados.xlsx (100K+ registros)
- ETL: scripts/actualizar_consolidado.py + scripts/etl/ (25 módulos)

Sistema destino:
- PostgreSQL: registros_om, users, audit_log
- FastAPI: endpoints de ETL
- Automatización: Kawak cada 10 días

Genera:
1. Script de migración SQLite → PostgreSQL
2. Servicio ETL en FastAPI
3. Servicio de descarga Kawak
4. Script de conciliación (Streamlit vs React)
5. Tests de migración
6. Reporte de migración
```

## Cierre Formal de Fase 7
**Estado:** ✅ COMPLETADA | ⏳ PENDIENTE | ❌ BLOQUEADA
**Fecha de cierre:** ___________
**Aprobada por:** ___________

---

# FASE 8 — DASHBOARDS E INDICADORES

## Objetivo
Construir todas las visualizaciones, KPIs, reportes y dashboards. Validar que los cálculos de cumplimiento son equivalentes al sistema original.

## Alcance
- Dashboard principal (Resumen General) con treeline, semáforo, KPIs
- CMI Estratégico (4 perspectivas, tabs)
- CMI por Procesos
- Plan de Mejoramiento
- Gestión OM
- Seguimiento Reportes
- PDI Acreditación
- Tablero Operativo
- Diagnóstico
- Exportación Excel/PDF

## Actividades

### A8.1 — Gráficos Principales
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A8.1.1 | Treeline/waterfall chart (línea → objetivo → meta → indicador) | Gráfico |
| A8.1.2 | Semáforo interactivo (donut charts por categoría) | Gráfico |
| A8.1.3 | Heatmap (período × cumplimiento) | Gráfico |
| A8.1.4 | Time series (tendencia histórica) | Gráfico |
| A8.1.5 | Bar charts (comparaciones por proceso) | Gráfico |
| A8.1.6 | KPI cards (5 métricas principales) | Componente |

### A8.2 — Fórmulas de Cumplimiento
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A8.2.1 | Implementar `normalizar_cumplimiento()` en TypeScript | Función |
| A8.2.2 | Implementar `categorizar_cumplimiento()` (PA-aware) | Función |
| A8.2.3 | Implementar `recalcular_cumplimiento_faltante()` | Función |
| A8.2.4 | Validar contra casos de prueba del sistema actual | Tests |

### A8.3 — Filtros
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A8.3.1 | Filtro por año | Componente |
| A8.3.2 | Filtro por período | Componente |
| A8.3.3 | Filtro por proceso | Componente |
| A8.3.4 | Filtro por línea estratégica | Componente |
| A8.3.5 | Filtro por categoría | Componente |
| A8.3.6 | Búsqueda por ID/nombre | Componente |

### A8.4 — Reportes
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A8.4.1 | Exportación Excel (formato corporativo) | Función |
| A8.4.2 | Exportación PDF (ficha técnica) | Función |
| A8.4.3 | Reporte por proceso | Página |

### A8.5 — Validación
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A8.5.1 | Comparar KPIs Streamlit vs React | Reporte |
| A8.5.2 | Comparar gráficos Streamlit vs React | Evidencia visual |
| A8.5.3 | Comparar filtros Streamlit vs React | Verificación |

## Dependencias
- Fase 4 completada (backend endpoints)
- Fase 5 completada (frontend páginas)
- Fase 7 completada (datos migrados)

## Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Gráficos no son equivalentes al sistema actual | Media | Alto | Comparación visual directa |
| Cálculos de cumplimiento difieren | Baja | Alto | Tests de regresión con datos reales |
| Performance con 100K registros | Media | Medio | Paginación + lazy loading |

## Mitigaciones
- Tests de regresión con datos reales
- Comparación visual side-by-side
- Optimización de queries

## Entregables

| # | Entregable | Formato |
|---|------------|---------|
| E8.1 | Todos los gráficos implementados | Código |
| E8.2 | Fórmulas de cumplimiento validadas | Tests |
| E8.3 | Filtros funcionales | Código |
| E8.4 | Exportaciones funcionales | Código |
| E8.5 | Reporte de validación | Documento |

## Casos de Prueba

| ID | Prueba | Resultado Esperado |
|----|--------|-------------------|
| TP-8.1 | KPIs calculados son equivalentes | Diferencia < 0.01% |
| TP-8.2 | Categorías calculadas son equivalentes | 100% match |
| TP-8.3 | Treeline muestra misma jerarquía | Visual match |
| TP-8.4 | Filtros funcionan correctamente | Datos filtrados |
| TP-8.5 | Exportación Excel genera archivo válido | Archivo abierto |
| TP-8.6 | Dashboard carga en < 3 segundos | Tiempo < 3s |

## Evidencias Requeridas
- Todos los gráficos funcionales
- Tests de fórmulas pasando
- Comparación visual Streamlit vs React
- Exportaciones funcionales

## Auditoría
- Comparación visual side-by-side
- Validación de fórmulas con datos reales
- Performance audit (load time)

## Checklist

- [ ] Treeline chart funcional
- [ ] Semáforo interactivo funcional
- [ ] Heatmap funcional
- [ ] Time series funcional
- [ ] KPI cards funcionales
- [ ] Fórmulas validadas
- [ ] Filtros funcionales
- [ ] Exportación Excel funcional
- [ ] Exportación PDF funcional
- [ ] Dashboard carga < 3s

## Criterios de Aceptación
1. Todos los gráficos son visualesmente equivalentes
2. Fórmulas de cumplimiento 100% equivalentes
3. Filtros funcionan correctamente
4. Exportaciones generan archivos válidos
5. Dashboard carga en < 3 segundos

## Estimación de Esfuerzo
- **Duración:** 3 semanas (15 días)
- **Esfuerzo:** 120 horas
- **Responsable:** Frontend Developer + Backend Developer

## Responsable Sugerido
**Ingeniero Full Stack** (implementación) + **Product Owner** (validación visual)

## Prompt Específico para Ejecutar la Fase mediante IA

```
Eres un Ingeniero Frontend especializado en visualización de datos.
Implementa todos los dashboards y gráficos de SGIND.

El sistema actual usa Plotly para:
- Treeline/waterfall (jerarquía institucional)
- Donut charts (semáforo por categoría)
- Heatmap (período × cumplimiento)
- Time series (tendencia histórica)
- Bar charts (comparaciones)
- KPI cards (5 métricas)

Fórmulas de cumplimiento (DEBEN ser idénticas):
- Positivo: cumplimiento = ejecución / meta
- Negativo: cumplimiento = meta / ejecución
- PA: cumple desde 95%, tope 100%
- Regular: cumple desde 100%, alerta desde 80%, sobrecumplimiento ≥ 105%

Genera:
1. Implementación de cada gráfico en Recharts/Plotly.js
2. Fórmulas de cumplimiento en TypeScript (idénticas a Python)
3. Componentes de filtros
4. Componentes de exportación
5. Tests de fórmulas con casos del sistema actual
6. Validación visual (screenshots)
```

## Cierre Formal de Fase 8
**Estado:** ✅ COMPLETADA | ⏳ PENDIENTE | ❌ BLOQUEADA
**Fecha de cierre:** ___________
**Aprobada por:** ___________

---

# FASE 9 — IA Y AUTOMATIZACIONES

## Objetivo
Implementar capacidades de IA: migrar prompts existentes, agregar chat con datos, anomaly detection, y recomendaciones proactivas.

## Alcance
- Migrar 3 prompts existentes (texto, ficha CMI, línea CMI)
- Implementar chat con datos (NUEVO)
- Implementar anomaly detection (NUEVO)
- Implementar recomendaciones proactivas (NUEVO)
- Evaluar proveedor de IA (Claude vs OpenAI vs Gemini)
- Rate limiting y caché de respuestas IA

## Actividades

### A9.1 — Migración de Prompts
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A9.1.1 | Migrar prompt de análisis de texto | Servicio |
| A9.1.2 | Migrar prompt de ficha CMI | Servicio |
| A9.1.3 | Migrar prompt de línea CMI | Servicio |
| A9.1.4 | Migrar fallbacks heurísticos | Servicio |

### A9.2 — Evaluación de Proveedor
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A9.2.1 | Evaluar Claude (Anthropic) | Comparativa |
| A9.2.2 | Evaluar OpenAI (GPT-4) | Comparativa |
| A9.2.3 | Evaluar Gemini (Google) | Comparativa |
| A9.2.4 | Seleccionar proveedor óptimo | Decisión |

### A9.3 — Chat con Datos (NUEVO)
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A9.3.1 | Diseñar interfaz de chat | Wireframe |
| A9.3.2 | Implementar endpoint `/api/ia/chat` | Endpoint |
| A9.3.3 | Implementar contexto de conversación | Servicio |
| A9.3.4 | Implementar sugerencias predefinidas | UI |

### A9.4 — Anomaly Detection (NUEVO)
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A9.4.1 | Implementar detección de anomalías estadísticas | Algoritmo |
| A9.4.2 | Implementar alertas de anomalías | UI |
| A9.4.3 | Implementar dashboard de anomalías | Página |

### A9.5 — Recomendaciones Proactivas (NUEVO)
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A9.5.1 | Implementar generación de recomendaciones | Servicio |
| A9.5.2 | Implementar panel de recomendaciones | UI |
| A9.5.3 | Implementar priorización de recomendaciones | Algoritmo |

### A9.6 — Optimización
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A9.6.1 | Implementar rate limiting para API IA | Middleware |
| A9.6.2 | Implementar caché de respuestas IA | Caché |
| A9.6.3 | Monitorear costos de IA | Dashboard |

## Dependencias
- Fase 4 completada (backend endpoints IA)
- Fase 5 completada (frontend componentes IA)

## Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Costos de IA escalan | Media | Medio | Rate limiting + caché |
| Calidad de respuestas IA variable | Media | Medio | Fallbacks heurísticos |
| Latencia de API IA alta | Media | Medio | Caché + loading states |

## Mitigaciones
- Caché agresivo de respuestas IA
- Fallbacks heurísticos cuando IA falla
- Rate limiting por usuario

## Entregables

| # | Entregable | Formato |
|---|------------|---------|
| E9.1 | 3 prompts migrados | Código |
| E9.2 | Evaluación de proveedores | Documento |
| E9.3 | Chat con datos | Código |
| E9.4 | Anomaly detection | Código |
| E9.5 | Recomendaciones proactivas | Código |
| E9.6 | Monitoreo de costos | Dashboard |

## Casos de Prueba

| ID | Prueba | Resultado Esperado |
|----|--------|-------------------|
| TP-9.1 | Análisis de texto retorna respuesta | 200 + JSON |
| TP-9.2 | Ficha CMI retorna análisis | 200 + Markdown |
| TP-9.3 | Chat con datos responde pregunta | 200 + JSON |
| TP-9.4 | Anomaly detection identifica anomalía | Lista de anomalías |
| TP-9.5 | Rate limiting bloquea exceso | 429 después de N |
| TP-9.6 | Caché evita llamadas repetidas | Sin llamada a API |

## Evidencias Requeridas
- Prompts migrados y funcionales
- Evaluación de proveedores
- Chat con datos funcional
- Anomaly detection funcionando
- Monitoreo de costos

## Auditoría
- Revisión de calidad de respuestas IA
- Verificación de fallbacks
- Monitoreo de costos

## Checklist

- [ ] 3 prompts migrados
- [ ] Fallbacks heurísticos funcionales
- [ ] Evaluación de proveedores completada
- [ ] Chat con datos funcional
- [ ] Anomaly detection funcionando
- [ ] Recomendaciones proactivas
- [ ] Rate limiting activo
- [ ] Caché de respuestas IA
- [ ] Monitoreo de costos

## Criterios de Aceptación
1. Los 3 prompts originales funcionan igual que en Streamlit
2. Chat con datos responde preguntas relevantes
3. Anomaly detection identifica anomalías reales
4. Rate limiting previene abuso
5. Costos de IA monitoreados

## Estimación de Esfuerzo
- **Duración:** 2 semanas (10 días)
- **Esfuerzo:** 80 horas
- **Responsable:** Backend Developer + AI Specialist

## Responsable Sugerido
**Backend Developer** (implementación) + **AI/ML Engineer** (modelos)

## Prompt Específico para Ejecutar la Fase mediante IA

```
Eres un AI/ML Engineer Senior. Implementa las capacidades de IA para SGIND.

Prompts existentes (MIGRAR):
1. Análisis de texto: {nombre}, {proceso}, {categoria}, {cumplimiento}, {analisis}
   → insights + oportunidades de mejora
2. Ficha CMI: {nombre}, {linea}, {objetivo}, {meta}, {ejecucion}, {nivel}, {cumplimiento}
   → diagnóstico + factor de riesgo + recomendación táctica
3. Línea CMI: {linea}, {cumplimiento_promedio}, {total_ind}, {total_riesgo}, {tabla_json}
   → análisis sintético + indicador urgente + 2 directrices

Nuevas capacidades:
4. Chat con datos: preguntas en lenguaje natural sobre indicadores
5. Anomaly detection: detección estadística de anomalías en tendencias
6. Recomendaciones: generación automática basada en riesgo

Genera:
1. Servicio de IA en FastAPI (3 prompts + 3 nuevos)
2. Evaluación de proveedores (Claude vs OpenAI vs Gemini)
3. Endpoint de chat con datos
4. Algoritmo de anomaly detection
5. Generador de recomendaciones
6. Rate limiting y caché
7. Tests de cada capacidad
```

## Cierre Formal de Fase 9
**Estado:** ✅ COMPLETADA | ⏳ PENDIENTE | ❌ BLOQUEADA
**Fecha de cierre:** ___________
**Aprobada por:** ___________

---

# FASE 10 — QA INTEGRAL

## Objetivo
Ejecutar suite completa de pruebas: unitarias, integración, E2E, carga, stress. Generar evidencias y reportes.

## Alcance
- Tests unitarios (backend + frontend)
- Tests de integración (API endpoints)
- Tests E2E (flujo completo de usuario)
- Tests de carga (100 concurrentes)
- Tests de stress (degradación controlada)
- Tests de seguridad (penetration testing)
- Reporte de cobertura

## Actividades

### A10.1 — Tests Unitarios
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A10.1.1 | Tests unitarios backend (services, core) | pytest |
| A10.1.2 | Tests unitarios frontend (components, hooks) | Jest |
| A10.1.3 | Tests de fórmulas de cumplimiento | pytest |
| A10.1.4 | Tests de categorización | pytest |

### A10.2 — Tests de Integración
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A10.2.1 | Tests de endpoints API | pytest |
| A10.2.2 | Tests de auth (OIDC flow) | pytest |
| A10.2.3 | Tests de RBAC | pytest |
| A10.2.4 | Tests de ETL pipeline | pytest |

### A10.3 — Tests E2E
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A10.3.1 | Flujo: Login → Dashboard → Filtro → Drill-down | Playwright |
| A10.3.2 | Flujo: Login → Gestión OM → Crear → Editar → Eliminar | Playwright |
| A10.3.3 | Flujo: Login → CMI → Análisis IA | Playwright |
| A10.3.4 | Flujo: Login → Exportación Excel | Playwright |

### A10.4 — Tests de Carga
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A10.4.1 | 100 usuarios concurrentes (lectura) | k6/locust |
| A10.4.2 | 50 usuarios concurrentes (escritura OM) | k6/locust |
| A10.4.3 | Medición de response time | Métricas |

### A10.5 — Tests de Stress
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A10.5.1 | Carga progresiva hasta degradación | k6/locust |
| A10.5.2 | Identificar punto de quiebre | Métricas |
| A10.5.3 | Verificar recuperación | Métricas |

### A10.6 — Tests de Seguridad
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A10.6.1 | OWASP Top 10 validation | Checklist |
| A10.6.2 | SQL injection testing | Reporte |
| A10.6.3 | XSS testing | Reporte |
| A10.6.4 | Authentication bypass testing | Reporte |

## Dependencias
- Fase 4-9 completadas (todo el sistema funcional)

## Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Tests E2E frágiles | Alta | Medio | Page Object Model, waits explícitos |
| Tests de carga requieren infraestructura | Media | Medio | Usar k6 cloud (gratuito) |
| Cobertura insuficiente | Media | Alto | TDD, coverage gate en CI |

## Mitigaciones
- Page Object Model para E2E
- k6 cloud para carga
- Coverage gate en CI (≥ 80%)

## Entregables

| # | Entregable | Formato |
|---|------------|---------|
| E10.1 | Suite de tests unitarios | Código |
| E10.2 | Suite de tests de integración | Código |
| E10.3 | Suite de tests E2E | Código |
| E10.4 | Reporte de carga | Documento |
| E10.5 | Reporte de stress | Documento |
| E10.6 | Reporte de seguridad | Documento |
| E10.7 | Reporte de cobertura | HTML |

## Casos de Prueba

| ID | Prueba | Resultado Esperado |
|----|--------|-------------------|
| TP-10.1 | Tests unitarios pasan | 100% pass |
| TP-10.2 | Tests de integración pasan | 100% pass |
| TP-10.3 | Tests E2E pasan | 100% pass |
| TP-10.4 | 100 usuarios concurrentes | Response < 2s |
| TP-10.5 | Punto de quiebre identificado | Métricas |
| TP-10.6 | Sin vulnerabilidades críticas | OWASP pass |
| TP-10.7 | Cobertura ≥ 80% | Reporte |

## Evidencias Requeridas
- Todos los tests ejecutándose
- Reporte de cobertura
- Reporte de carga
- Reporte de stress
- Reporte de seguridad

## Auditoría
- Revisión de cobertura de código
- Revisión de calidad de tests
- Validación de resultados

## Checklist

- [ ] Tests unitarios backend (≥ 80% coverage)
- [ ] Tests unitarios frontend (≥ 80% coverage)
- [ ] Tests de integración (100% endpoints)
- [ ] Tests E2E (4 flujos principales)
- [ ] Tests de carga (100 concurrentes)
- [ ] Tests de stress
- [ ] Tests de seguridad (OWASP)
- [ ] Reporte de cobertura generado

## Criterios de Aceptación
1. 100% de tests críticos pasan
2. Cobertura ≥ 80%
3. 100 usuarios concurrentes sin degradación
4. Sin vulnerabilidades OWASP Top 10 críticas
5. Response time < 2s bajo carga normal

## Estimación de Esfuerzo
- **Duración:** 2 semanas (10 días)
- **Esfuerzo:** 80 horas
- **Responsable:** Especialista QA

## Responsable Sugerido
**Especialista QA** (diseño + ejecución) + **DevOps** (infraestructura de tests)

## Prompt Específico para Ejecutar la Fase mediante IA

```
Eres un Especialista QA Senior. Diseña y ejecuta la suite de pruebas para
SGIND.

El sistema tiene:
- Backend: FastAPI (30+ endpoints)
- Frontend: Next.js (9 páginas)
- Auth: Microsoft OIDC + JWT
- BD: PostgreSQL + Excel
- IA: Claude API (3 prompts)
- ETL: Pipeline batch

Genera:
1. Suite de tests unitarios (pytest + Jest)
2. Suite de tests de integración (API endpoints)
3. Suite de tests E2E (Playwright)
4. Plan de tests de carga (k6)
5. Plan de tests de seguridad (OWASP)
6. Matriz de trazabilidad (requisitos → tests)
7. Reporte de cobertura

Prioriza: auth, RBAC, fórmulas de cumplimiento, ETL, exportaciones.
```

## Cierre Formal de Fase 10
**Estado:** ✅ COMPLETADA | ⏳ PENDIENTE | ❌ BLOQUEADA
**Fecha de cierre:** ___________
**Aprobada por:** ___________

---

# FASE 11 — DEVOPS

## Objetivo
Configurar infraestructura DevOps: Docker, CI/CD, GitHub Actions, ambientes DEV/QA/PROD, monitoreo.

## Alcance
- Docker multi-stage (frontend + backend)
- docker-compose.yml (desarrollo local)
- GitHub Actions (CI/CD)
- Ambientes (DEV, QA, PROD)
- Monitoreo y alertas
- Backup y recuperación

## Actividades

### A11.1 — Docker
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A11.1.1 | Dockerfile frontend (multi-stage) | Dockerfile |
| A11.1.2 | Dockerfile backend (multi-stage) | Dockerfile |
| A11.1.3 | docker-compose.yml (fe + be + db + nginx) | docker-compose |
| A11.1.4 | Health checks | Configuración |

### A11.2 — CI/CD
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A11.2.1 | Workflow: test (push/PR) | YAML |
| A11.2.2 | Workflow: lint (push/PR) | YAML |
| A11.2.3 | Workflow: build (push to main) | YAML |
| A11.2.4 | Workflow: deploy DEV (push to develop) | YAML |
| A11.2.5 | Workflow: deploy QA (manual) | YAML |
| A11.2.6 | Workflow: deploy PROD (manual + approval) | YAML |

### A11.3 — Ambientes
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A11.3.1 | Configurar ambiente DEV | Configuración |
| A11.3.2 | Configurar ambiente QA | Configuración |
| A11.3.3 | Configurar ambiente PROD | Configuración |
| A11.3.4 | Variables de entorno por ambiente | Secrets |

### A11.4 — Monitoreo
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A11.4.1 | Health check endpoints | Endpoints |
| A11.4.2 | Logging estructurado | Configuración |
| A11.4.3 | Métricas básicas (request count, latency) | Middleware |
| A11.4.4 | Alertas de error | Configuración |

### A11.5 — Backup
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A11.5.1 | Backup automático PostgreSQL | Script |
| A11.5.2 | Backup de archivos Excel | Script |
| A11.5.3 | Estrategia de retención | Configuración |

## Dependencias
- Fase 4-10 completadas (sistema funcional)

## Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Docker build falla | Media | Medio | Tests de build en CI |
| Deploy falla en producción | Baja | Alto | Deploy manual con approval |
| Variables de entorno mal configuradas | Media | Alto | Validation en CI |

## Mitigaciones
- Tests de build en cada PR
- Deploy con approval manual
- Environment validation en startup

## Entregables

| # | Entregable | Formato |
|---|------------|---------|
| E11.1 | Dockerfiles (frontend + backend) | Código |
| E11.2 | docker-compose.yml funcional | YAML |
| E11.3 | 6 workflows GitHub Actions | YAML |
| E11.4 | Configuración de ambientes | Documento |
| E11.5 | Scripts de backup | Código |
| E11.6 | Configuración de monitoreo | Código |

## Casos de Prueba

| ID | Prueba | Resultado Esperado |
|----|--------|-------------------|
| TP-11.1 | docker-compose up levanta todo | 4 servicios |
| TP-11.2 | CI ejecuta tests en PR | Tests pasan |
| TP-11.3 | Deploy a DEV automático | Deploy exitoso |
| TP-11.4 | Backup se ejecuta | Archivo generado |
| TP-11.5 | Health check retorna 200 | {"status": "healthy"} |

## Evidencias Requeridas
- Docker compose funcional
- CI/CD pipelines ejecutándose
- Ambientes configurados
- Backup funcionando

## Auditoría
- Revisión de configuración de seguridad
- Validación de pipelines
- Test de recuperación

## Checklist

- [ ] Dockerfiles multi-stage
- [ ] docker-compose.yml funcional
- [ ] CI workflow (test + lint)
- [ ] CD workflow (deploy DEV/QA/PROD)
- [ ] Ambientes configurados
- [ ] Variables de entorno en secrets
- [ ] Health checks funcionales
- [ ] Logging estructurado
- [ ] Backup automático
- [ ] Monitoreo básico

## Criterios de Aceptación
1. docker-compose up levanta todos los servicios
2. CI ejecuta tests en cada PR
3. Deploy a DEV es automático
4. Deploy a PROD requiere approval
5. Backup se ejecuta diariamente
6. Health checks funcionales

## Estimación de Esfuerzo
- **Duración:** 1.5 semanas (8 días)
- **Esfuerzo:** 60 horas
- **Responsable:** Especialista DevOps

## Responsable Sugerido
**Especialista DevOps** (implementación) + **Backend Developer** (colaboración)

## Prompt Específico para Ejecutar la Fase mediante IA

```
Eres un Especialista DevOps Senior. Configura la infraestructura DevOps para
SGIND.

Stack:
- Frontend: Next.js (Node.js)
- Backend: FastAPI (Python)
- BD: PostgreSQL
- Docker multi-stage

Genera:
1. Dockerfile frontend (multi-stage: build + production)
2. Dockerfile backend (multi-stage: build + production)
3. docker-compose.yml (fe + be + db + nginx)
4. 6 GitHub Actions workflows (test, lint, build, deploy DEV/QA/PROD)
5. Scripts de backup PostgreSQL
6. Configuración de monitoreo (health checks, logging)
7. Variables de entorno por ambiente
8. nginx.conf para reverse proxy

Sé específico con configuraciones y versiones.
```

## Cierre Formal de Fase 11
**Estado:** ✅ COMPLETADA | ⏳ PENDIENTE | ❌ BLOQUEADA
**Fecha de cierre:** ___________
**Aprobada por:** ___________

---

# FASE 12 — PRODUCCIÓN

## Objetivo
Preparar y ejecutar el Go Live: checklist, documentación, monitoreo post-producción, soporte.

## Alcance
- Checklist Go Live
- Manual técnico
- Manual funcional (usuario)
- Manual de administrador
- Smoke test final
- Migración de datos final
- Cutover de Streamlit
- Monitoreo post-producción
- Plan de soporte

## Actividades

### A12.1 — Preparación
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A12.1.1 | Completar checklist Go Live | Checklist |
| A12.1.2 | Verificar todos los tests pasan | Reporte |
| A12.1.3 | Verificar backup funcional | Evidencia |
| A12.1.4 | Verificar monitoreo activo | Dashboard |

### A12.2 — Documentación
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A12.2.1 | Manual técnico (instalación, configuración) | Documento |
| A12.2.2 | Manual funcional (guía de usuario) | Documento |
| A12.2.3 | Manual de administrador (usuarios, roles, backup) | Documento |
| A12.2.4 | Runbook de troubleshooting | Documento |

### A12.3 — Migración Final
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A12.3.1 | Migrar datos finales SQLite → PostgreSQL | Migración |
| A12.3.2 | Validar integridad post-migración | Reporte |
| A12.3.3 | Migrar usuarios y roles | Migración |

### A12.4 — Cutover
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A12.4.1 | Ejecutar smoke test final | Reporte |
| A12.4.2 | Cambiar DNS hacia nuevo sistema | DNS |
| A12.4.3 | Desactivar Streamlit (mantener por 1 mes) | Configuración |
| A12.4.4 | Notificar a usuarios | Comunicación |

### A12.5 — Monitoreo Post-Producción
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A12.5.1 | Monitorear errores 24h post-cutover | Dashboard |
| A12.5.2 | Monitorear performance | Métricas |
| A12.5.3 | Recopilar feedback de usuarios | Encuesta |
| A12.5.4 | Corregir issues críticos | Hotfix |

### A12.6 — Soporte
| # | Actividad | Evidencia |
|---|-----------|-----------|
| A12.6.1 | Definir canal de soporte | Configuración |
| A12.6.2 | Definir SLA de soporte | Documento |
| A12.6.3 | Capacitación a usuarios | Sesiones |

## Dependencias
- Fase 10 completada (QA aprobado)
- Fase 11 completada (DevOps configurado)

## Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Errores en producción post-cutover | Media | Alto | Monitoreo 24h + hotfix rápido |
| Usuarios no adoptan nuevo sistema | Media | Alto | Capacitación + soporte dedicado |
| Performance degrada en producción | Baja | Alto | Monitoreo + escalabilidad |

## Mitigaciones
- Monitoreo intensivo 24h post-cutover
- Capacitación antes del cutover
- Rollback plan documentado

## Entregables

| # | Entregable | Formato |
|---|------------|---------|
| E12.1 | Checklist Go Live completo | Checklist |
| E12.2 | Manual técnico | Documento |
| E12.3 | Manual funcional | Documento |
| E12.4 | Manual de administrador | Documento |
| E12.5 | Runbook de troubleshooting | Documento |
| E12.6 | Reporte de smoke test | Documento |
| E12.7 | Reporte de migración final | Documento |

## Casos de Prueba

| ID | Prueba | Resultado Esperado |
|----|--------|-------------------|
| TP-12.1 | Smoke test completo | 100% pass |
| TP-12.2 | Login funciona en producción | 200 |
| TP-12.3 | Dashboard carga en producción | < 3s |
| TP-12.4 | Todos los gráficos funcionan | Sin errores |
| TP-12.5 | Exportaciones funcionan | Archivo generado |
| TP-12.6 | Backup se ejecuta | Archivo generado |

## Evidencias Requeridas
- Checklist completo
- Manuales documentados
- Smoke test aprobado
- Migración validada

## Auditoría
- Revisión de todos los entregables
- Validación de que el sistema cumple requisitos
- Verificación de que el plan de rollback está documentado

## Checklist

- [ ] Checklist Go Live completo
- [ ] Manual técnico documentado
- [ ] Manual funcional documentado
- [ ] Manual de administrador documentado
- [ ] Runbook de troubleshooting
- [ ] Smoke test aprobado
- [ ] Migración final completada
- [ ] DNS actualizado
- [ ] Streamlit desactivado
- [ ] Monitoreo activo
- [ ] Soporte configurado
- [ ] Rollback plan documentado

## Criterios de Aceptación
1. Smoke test 100% aprobado
2. Todos los manuales documentados
3. Migración de datos completada
4. DNS hacia nuevo sistema
5. Monitoreo activo
6. Soporte configurado
7. Rollback plan documentado

## Estimación de Esfuerzo
- **Duración:** 1 semana (5 días)
- **Esfuerzo:** 40 horas
- **Responsable:** Tech Lead + Product Owner

## Responsable Sugerido
**Tech Lead** (coordinación) + **Product Owner** (aprobación)

## Prompt Específico para Ejecutar la Fase mediante IA

```
Eres un Tech Lead Senior. Prepara el Go Live de SGIND.

El sistema migrado tiene:
- Frontend: Next.js (Docker)
- Backend: FastAPI (Docker)
- BD: PostgreSQL
- Auth: Microsoft OIDC
- 9 páginas funcionales
- Tests aprobados (80%+ coverage)

Genera:
1. Checklist Go Live completo (100+ items)
2. Manual técnico (instalación, configuración, troubleshooting)
3. Manual funcional (guía de usuario para 9 páginas)
4. Manual de administrador (usuarios, roles, backup, monitoreo)
5. Runbook de troubleshooting (20+ escenarios)
6. Plan de rollback (pasos para revertir)
7. Plan de comunicación a usuarios
8. Cronograma de cutover (hora por hora)
```

## Cierre Formal de Fase 12
**Estado:** ✅ COMPLETADA | ⏳ PENDIENTE | ❌ BLOQUEADA
**Fecha de cierre:** ___________
**Aprobada por:** ___________

---

# ENTREGABLES FINALES

## ROADMAP COMPLETO

```
SEMANA 1-2:   FASE 0 (Levantamiento) + FASE 1 (Arquitectura)
SEMANA 3:     FASE 2 (Modelo de Datos)
SEMANA 4-5:   FASE 3 (Diseño UX/UI)
SEMANA 6-9:   FASE 4 (Backend FastAPI)
SEMANA 10-14: FASE 5 (Frontend Next.js)
SEMANA 15-16: FASE 6 (Auth + Seguridad)
SEMANA 17-18: FASE 7 (Migración de Datos)
SEMANA 19-21: FASE 8 (Dashboards + Indicadores)
SEMANA 22-23: FASE 9 (IA + Automatizaciones)
SEMANA 24-25: FASE 10 (QA Integral)
SEMANA 26-27: FASE 11 (DevOps)
SEMANA 28:    FASE 12 (Producción)
```

## WBS (Work Breakdown Structure)

```
1.0 SGIND Migration
├── 1.1 Phase 0: Levantamiento
│   ├── 1.1.1 Inventario Funcional
│   ├── 1.1.2 Inventario Técnico
│   ├── 1.1.3 Inventario Integraciones
│   ├── 1.1.4 Inventario Datos
│   ├── 1.1.5 Inventario IA
│   └── 1.1.6 Auditoría Tests
├── 1.2 Phase 1: Arquitectura
│   ├── 1.2.1 Arquitectura Lógica
│   ├── 1.2.2 Arquitectura Física
│   ├── 1.2.3 Arquitectura Datos
│   ├── 1.2.4 Arquitectura Seguridad
│   ├── 1.2.5 Arquitectura DevOps
│   └── 1.2.6 ADRs
├── 1.3 Phase 2: Modelo de Datos
│   ├── 1.3.1 Modelo Conceptual
│   ├── 1.3.2 Modelo Lógico
│   ├── 1.3.3 Modelo Físico
│   └── 1.3.4 Migración SQLite
├── 1.4 Phase 3: Diseño UX/UI
│   ├── 1.4.1 Investigación UX
│   ├── 1.4.2 Sistema de Diseño
│   ├── 1.4.3 Wireframes
│   ├── 1.4.4 Mockups
│   └── 1.4.5 Navegación
├── 1.5 Phase 4: Backend
│   ├── 1.5.1 Estructura Base
│   ├── 1.5.2 Servicio Excel
│   ├── 1.5.3 Auth Endpoints
│   ├── 1.5.4 Dashboard Endpoints
│   ├── 1.5.5 CMI Endpoints
│   ├── 1.5.6 OM Endpoints
│   ├── 1.5.7 IA Endpoints
│   ├── 1.5.8 ETL Endpoints
│   ├── 1.5.9 Export Endpoints
│   └── 1.5.10 Tests
├── 1.6 Phase 5: Frontend
│   ├── 1.6.1 Setup Proyecto
│   ├── 1.6.2 Layout + Navegación
│   ├── 1.6.3 Design System
│   ├── 1.6.4 Resumen General
│   ├── 1.6.5 CMI Estratégico
│   ├── 1.6.6 CMI por Procesos
│   ├── 1.6.7 Plan Mejoramiento
│   ├── 1.6.8 Gestión OM
│   ├── 1.6.9 Páginas Secundarias
│   └── 1.6.10 IA Frontend
├── 1.7 Phase 6: Auth + Seguridad
│   ├── 1.7.1 Azure AD
│   ├── 1.7.2 JWT
│   ├── 1.7.3 RBAC
│   ├── 1.7.4 Auditoría
│   └── 1.7.5 OWASP
├── 1.8 Phase 7: Migración Datos
│   ├── 1.8.1 SQLite → PostgreSQL
│   ├── 1.8.2 ETL en FastAPI
│   ├── 1.8.3 Automatización Kawak
│   └── 1.8.4 Validación
├── 1.9 Phase 8: Dashboards
│   ├── 1.9.1 Gráficos
│   ├── 1.9.2 Fórmulas
│   ├── 1.9.3 Filtros
│   ├── 1.9.4 Reportes
│   └── 1.9.5 Validación
├── 1.10 Phase 9: IA
│   ├── 1.10.1 Migración Prompts
│   ├── 1.10.2 Evaluación Proveedor
│   ├── 1.10.3 Chat con Datos
│   ├── 1.10.4 Anomaly Detection
│   ├── 1.10.5 Recomendaciones
│   └── 1.10.6 Optimización
├── 1.11 Phase 10: QA
│   ├── 1.11.1 Tests Unitarios
│   ├── 1.11.2 Tests Integración
│   ├── 1.11.3 Tests E2E
│   ├── 1.11.4 Tests Carga
│   ├── 1.11.5 Tests Stress
│   └── 1.11.6 Tests Seguridad
├── 1.12 Phase 11: DevOps
│   ├── 1.12.1 Docker
│   ├── 1.12.2 CI/CD
│   ├── 1.12.3 Ambientes
│   ├── 1.12.4 Monitoreo
│   └── 1.12.5 Backup
└── 1.13 Phase 12: Producción
    ├── 1.13.1 Preparación
    ├── 1.13.2 Documentación
    ├── 1.13.3 Migración Final
    ├── 1.13.4 Cutover
    ├── 1.13.5 Monitoreo
    └── 1.13.6 Soporte
```

## GANTT (Representación Textual)

```
FASE    | S1  S2  S3  S4  S5  S6  S7  S8  S9  S10 S11 S12 S13 S14 S15 S16 S17 S18 S19 S20 S21 S22 S23 S24 S25 S26 S27 S28
--------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----
FASE 0  |█████|█████|     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |
FASE 1  |     |█████|█████|     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |
FASE 2  |     |     |█████|     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |
FASE 3  |     |     |     |█████|█████|     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |
FASE 4  |     |     |     |     |     |█████|█████|█████|█████|     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |
FASE 5  |     |     |     |     |     |     |     |     |     |█████|█████|█████|█████|█████|     |     |     |     |     |     |     |     |     |     |     |     |     |
FASE 6  |     |     |     |     |     |     |     |     |     |     |     |     |     |     |█████|█████|     |     |     |     |     |     |     |     |     |     |     |
FASE 7  |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |█████|█████|     |     |     |     |     |     |     |     |     |
FASE 8  |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |█████|█████|█████|     |     |     |     |     |     |
FASE 9  |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |█████|█████|     |     |     |     |
FASE 10 |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |█████|█████|     |     |
FASE 11 |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |█████|█████|
FASE 12 |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |█████|
```

## BACKLOG (Priorizado)

### Must Have (MVP)
1. Auth Microsoft OIDC con JWT
2. RBAC (3 roles)
3. Dashboard Resumen General
4. CMI Estratégico
5. CMI por Procesos
6. Plan de Mejoramiento
7. Gestión OM (CRUD)
8. Responsive
9. Ambientes DEV/QA/PROD

### Should Have
10. Seguimiento Reportes
11. PDI Acreditación
12. Tablero Operativo
13. Diagnóstico
14. ETL automatizado (Kawak cada 10 días)
15. Exportación Excel/PDF

### Could Have
16. Chat con datos (IA)
17. Anomaly detection
18. Recomendaciones proactivas
19. Notificaciones por correo

### Won't Have (esta migración)
20. App móvil nativa
21. Integración SharePoint
22. Redis cache
23. Power BI embebido

## HISTORIAS DE USUARIO (46)

| ID | Épica | Historia | Story Points | Prioridad |
|----|-------|----------|-------------|-----------|
| US-1.1 | E1 Infra | Como dev, quiero proyecto Next.js configurado | 3 | Must |
| US-1.2 | E1 Infra | Como dev, quiero backend FastAPI estructurado | 5 | Must |
| US-1.3 | E1 Infra | Como usuario, quiero autenticarme con Microsoft | 8 | Must |
| US-1.4 | E1 Infra | Como admin, quiero definir roles (3) | 5 | Must |
| US-1.5 | E1 Infra | Como dev, quiero servicio de lectura Excel | 5 | Must |
| US-1.6 | E1 Infra | Como dev, quiero design system con componentes | 8 | Must |
| US-2.1 | E2 Dashboard | Como directivo, quiero ver KPIs principales | 5 | Must |
| US-2.2 | E2 Dashboard | Como directivo, quiero treeline/waterfall | 8 | Must |
| US-2.3 | E2 Dashboard | Como directivo, quiero filtrar por año/período | 3 | Must |
| US-2.4 | E2 Dashboard | Como directivo, quiero drill-down institución→indicador | 8 | Must |
| US-2.5 | E2 Dashboard | Como directivo, quiero cambiar modos (4) | 5 | Must |
| US-2.6 | E2 Dashboard | Como directivo, quiero exportar a Excel | 5 | Should |
| US-2.7 | E2 Dashboard | Como directivo, quiero semáforos interactivos | 3 | Must |
| US-3.1 | E3 CMI | Como analista, quiero ver 4 perspectivas | 5 | Must |
| US-3.2 | E3 CMI | Como analista, quiero análisis IA por indicador | 5 | Should |
| US-3.3 | E3 CMI | Como analista, quiero navegar por tabs | 3 | Must |
| US-3.4 | E3 CMI | Como analista, quiero filtrar por línea/objetivo | 3 | Must |
| US-4.1 | E4 Procesos | Como líder, quiero ver mis indicadores con calidad | 5 | Must |
| US-4.2 | E4 Procesos | Como líder, quiero KPIs y alertas de proceso | 5 | Must |
| US-4.3 | E4 Procesos | Como líder, quiero filtrar por proceso/subproceso | 3 | Must |
| US-4.4 | E4 Procesos | Como líder, quiero ver análisis histórico | 5 | Should |
| US-5.1 | E5 Plan | Como calidad, quiero ver CNA por factor | 5 | Must |
| US-5.2 | E5 Plan | Como calidad, quiero tracking de OM | 5 | Must |
| US-5.3 | E5 Plan | Como calidad, quiero filtrar por estado OM | 3 | Must |
| US-6.1 | E6 OM | Como admin, quiero crear OM con modal | 5 | Must |
| US-6.2 | E6 OM | Como admin, quiero editar OM | 5 | Must |
| US-6.3 | E6 OM | Como admin, quiero análisis IA al crear OM | 5 | Should |
| US-6.4 | E6 OM | Como admin, quiero ver avance de OM | 5 | Should |
| US-6.5 | E6 OM | Como admin, quiero eliminar OM | 3 | Must |
| US-7.1 | E7 Secund | Como analista, quiero tracking reportes | 5 | Should |
| US-7.2 | E7 Secund | Como acreditación, quiero PDI acreditación | 5 | Should |
| US-7.3 | E7 Secund | Como directivo, quiero tablero operativo | 8 | Should |
| US-7.4 | E7 Secund | Como dev, quiero diagnóstico | 5 | Should |
| US-8.1 | E8 IA | Como usuario, quiero mantener 3 prompts | 5 | Should |
| US-8.2 | E8 IA | Como usuario, quiero chatear con datos | 13 | Could |
| US-8.3 | E8 IA | Como usuario, quiero recomendaciones proactivas | 8 | Could |
| US-8.4 | E8 IA | Como usuario, quiero anomaly detection | 8 | Could |
| US-9.1 | E9 ETL | Como sistema, quiero descargar Kawak cada 10 días | 8 | Should |
| US-9.2 | E9 ETL | Como usuario, quiero interfaz descarga manual | 8 | Should |
| US-9.3 | E9 ETL | Como sistema, quiero ejecutar ETL post-descarga | 8 | Should |
| US-9.4 | E9 ETL | Como admin, quiero notificación de ETL | 3 | Could |
| US-10.1 | E10 QA | Como dev, quiero tests E2E completos | 8 | Must |
| US-10.2 | E10 QA | Como devops, quiero ambientes separados | 5 | Must |
| US-10.3 | E10 QA | Como dev, quiero CI/CD automatizado | 5 | Must |
| US-10.4 | E10 QA | Como usuario, quiero documentación | 5 | Must |
| US-10.5 | E10 QA | Como admin, quiero migración validada | 8 | Must |

## ÉPICAS

| ID | Épica | Historias | Story Points | Semanas |
|----|-------|-----------|-------------|---------|
| E1 | Infraestructura Base | 6 | 34 | 1-3 |
| E2 | Dashboard Ejecutivo | 7 | 40 | 4-5 |
| E3 | CMI Estratégico | 4 | 16 | 6-7 |
| E4 | CMI por Procesos | 4 | 18 | 7-8 |
| E5 | Plan de Mejoramiento | 3 | 13 | 8-9 |
| E6 | Gestión OM | 5 | 23 | 9-10 |
| E7 | Módulos Secundarios | 4 | 23 | 11-14 |
| E8 | IA + Chat | 4 | 34 | 15-17 |
| E9 | ETL Automatizado | 4 | 27 | 10,14 |
| E10 | QA + Deploy | 5 | 31 | 18-20 |
| **TOTAL** | | **46** | **259** | **20** |

## RIESGOS DEL PROYECTO

| ID | Riesgo | Probabilidad | Impacto | Mitigación | Dueño |
|----|--------|-------------|---------|------------|-------|
| R1 | Complejidad Next.js para equipo Python | Media | Alto | Capacitación Fase 1 | Tech Lead |
| R2 | Auth Azure AD complejo | Media | Alto | Guía oficial + testing | Security |
| R3 | Performance Excel 100K registros | Media | Medio | Caché + lazy loading | Backend |
| R4 | Gráficos no equivalentes | Media | Alto | Comparación visual | QA |
| R5 | Costos Azure superiores | Media | Alto | MVP en Render/VPS | DevOps |
| R6 | Scope creep (9 páginas críticas) | Alta | Alto | Fases estrictas | PO |
| R7 | Parallel run = doble mantenimiento | Alta | Medio | Automatización | DevOps |
| R8 | IA costs escalando | Media | Bajo | Rate limiting + caché | Backend |
| R9 | Datos migrados con errores | Baja | Alto | Validación exhaustiva | Data |
| R10 | Usuarios no adoptan | Media | Alto | Capacitación + soporte | PO |

## ESTRATEGIA DE DESPLIEGUE

### Ambientes
| Ambiente | Uso | Infraestructura | URL |
|----------|-----|-----------------|-----|
| DEV | Desarrollo | Docker local | localhost |
| QA | Testing | Docker compose | qa.sgind.edu.co |
| PROD | Producción | Azure Container Apps | sgind.edu.co |

### Pipeline de Despliegue
```
Push to develop → CI (test + lint) → Auto-deploy DEV
Push to main → CI (test + lint) → Manual approval → Deploy QA
QA approved → Manual approval → Deploy PROD
```

### Blue-Green Deployment
```
PROD (Blue): v1.0 ← tráfico actual
PROD (Green): v1.1 ← nuevo deploy
Validación → Switch tráfico → Blue se convierte en old
```

## ESTRATEGIA DE ROLLBACK

### Trigger de Rollback
- Error rate > 5% en 5 minutos
- Response time > 5s por 3 minutos
- Health check falla 3 veces consecutivas

### Pasos de Rollback
1. Detectar anomalía (monitoreo)
2. Notificar al equipo (Slack)
3. Cambiar DNS hacia versión anterior
4. Verificar que versión anterior funciona
5. Investigar causa raíz
6. Corregir y re-deploy

### Tiempo de Rollback
- **Target:** < 5 minutos
- **Máximo:** < 15 minutos

## ESTRATEGIA DE MONITOREO

### Métricas Clave
| Métrica | Target | Alerta |
|---------|--------|--------|
| Error rate | < 1% | > 5% |
| Response time (p95) | < 500ms | > 2s |
| Response time (p99) | < 1s | > 5s |
| Uptime | 99.5% | < 99% |
| CPU usage | < 70% | > 85% |
| Memory usage | < 80% | > 90% |
| DB connections | < 50 | > 80 |

### Herramientas
- **Logs:** Structured logging (JSON) → Azure Monitor / Seq
- **Metrics:** Application Insights / Prometheus
- **Alertas:** Azure Monitor / Slack
- **Uptime:** Azure Monitor / UptimeRobot

## ESTRATEGIA DE SOPORTE POST-PRODUCCIÓN

### Niveles de Soporte
| Nivel | Canal | SLA | Responsable |
|-------|-------|-----|-------------|
| L1 | Email + chat | 4h | Help Desk |
| L2 | Ticket system | 24h | Dev Team |
| L3 | Escalation | 48h | Tech Lead |

### Horario de Soporte
- **L-V:** 8:00 - 18:00
- **Emergencias:** 24/7 (L3)

### Capacitación
- **Sesión 1:** Dashboard y filtros (1h)
- **Sesión 2:** Gestión OM (1h)
- **Sesión 3:** Exportaciones (30min)
- **Sesión 4:** Administración de usuarios (30min)

---

## CIERRE DEL PLAN

Este plan de ejecución controlada cubre las 13 fases (0-12) con:
- **13 fases** detalladas con objetivos, actividades, entregables, riesgos, casos de prueba
- **46 historias de usuario** en 10 épicas
- **259 story points** estimados
- **28 semanas** de cronograma
- **10 riesgos** identificados y mitigados
- **Estrategias** de despliegue, rollback, monitoreo y soporte

**Cada fase debe cerrarse formalmente antes de avanzar a la siguiente.**

---

**Documento generado el:** 13 de junio de 2026
**Versión:** 1.0
**Estado:** Plan de Ejecución
