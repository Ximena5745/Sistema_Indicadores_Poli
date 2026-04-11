# Índice de Documentación - SGIND

**Documento:** INDICE_DOCUMENTACION.md  
**Versión:** 1.0  
**Última actualización:** 11 de abril de 2026  
**Propósito:** Navegación central de toda la documentación del sistema

---

## 🎯 ¿Por Dónde Empezar?

### Según tu rol:

**👔 Si eres Directivo / Líder de Área:**
1. Comienza con → [README.md](README.md) (5 min) - Qué es SGIND y qué puede hacer
2. Luego lee → [DOCUMENTACION_FUNCIONAL.md](DOCUMENTACION_FUNCIONAL.md) (20 min) - Cómo usar el sistema

**👨‍💻 Si eres Desarrollador:**
1. Comienza con → [README.md](README.md) (5 min) - Visión general
2. Luego lee → [GUIA_INSTALACION_EJECUCION.md](GUIA_INSTALACION_EJECUCION.md) (15 min) - Instalación
3. Profundiza en → [ARQUITECTURA_TECNICA_DETALLADA.md](ARQUITECTURA_TECNICA_DETALLADA.md) (45 min) - Detalles técnicos

**🔧 Si eres DevOps / Administrador:**
1. Comienza con → [GUIA_INSTALACION_EJECUCION.md](GUIA_INSTALACION_EJECUCION.md) (20 min) - Instalación y deployment
2. Luego revisa → [ARQUITECTURA_TECNICA_DETALLADA.md](ARQUITECTURA_TECNICA_DETALLADA.md) § "Capa de Datos" (10 min) - BD y almacenamiento

**📊 Si eres Analista de Datos:**
1. Comienza con → [DOCUMENTACION_FUNCIONAL.md](DOCUMENTACION_FUNCIONAL.md) § "Para Analistas de BI" (20 min)
2. Luego lee → [ARQUITECTURA_TECNICA_DETALLADA.md](ARQUITECTURA_TECNICA_DETALLADA.md) § "Capa de Datos" (15 min) - Estructura de datos

---

## 📚 Índice Completo de Documentos

### Documentación Principal (Recién Creada)

| Documento | Audiencia | Duración | Propósito |
|-----------|----------|----------|----------|
| 📄 [README.md](README.md) | Todos | 15 min | Descripción general, inicio rápido, FAQs |
| 🏗️ [ARQUITECTURA_TECNICA_DETALLADA.md](ARQUITECTURA_TECNICA_DETALLADA.md) | Arquitectos, Seniors | 90 min | Detalles técnicos profundos, módulos, flujos |
| 💼 [DOCUMENTACION_FUNCIONAL.md](DOCUMENTACION_FUNCIONAL.md) | Usuarios, Analistas | 60 min | Casos de uso, procesos de negocio, procedimientos |
| ⚙️ [GUIA_INSTALACION_EJECUCION.md](GUIA_INSTALACION_EJECUCION.md) | DevOps, Desarrolladores | 45 min | Instalación, configuración, deployment, troubleshooting |

### Documentación Existente (Análisis Previos)

| Documento | Ubicación | Propósito |
|-----------|-----------|----------|
| 📖 ANALISIS_ARQUITECTONICO_SGIND.md | `/` | Análisis del sistema (Prompt 1-3) |
| 📊 ARQUITECTURA_POST_PROCESO_SGIND.md | `/` | Reevaluación bajo paradigma post-proceamiento |
| 🔄 REFACTORIZACION_CODIGO_SGIND.md | `/` | Duplicaciones y mejoras de código |
| 🧹 LIMPIEZA_REPOSITORIO_SGIND.md | `/` | Plan de eliminación de archivos deprecated |
| ⚡ OPTIMIZACION_FLUJOS_SGIND.md | `/` | Roadmap de optimizaciones (4 fases) |
| 📝 docs/analisis_sistema_indicadores.md | `/docs/` | Análisis funcional detallado |
| 🧮 docs/calculos_actualizar_consolidado.md | `/docs/` | Fórmulas matemáticas ETL |

---

## 🔍 Búsqueda por Tema

### Instalación y Setup

**¿Cómo instalar SGIND?**
→ [GUIA_INSTALACION_EJECUCION.md § Instalación Local](GUIA_INSTALACION_EJECUCION.md#Instalación-Local)

**¿Cómo usar Docker?**
→ [GUIA_INSTALACION_EJECUCION.md § Instalación con Docker](GUIA_INSTALACION_EJECUCION.md#Instalación-con-Docker)

**¿Qué requisitos necesito?**
→ [GUIA_INSTALACION_EJECUCION.md § Requisitos del Sistema](GUIA_INSTALACION_EJECUCION.md#Requisitos-del-Sistema)

---

### Uso del Dashboard

**¿Cómo ver el status institucional?**
→ [DOCUMENTACION_FUNCIONAL.md § CU-1: Directivo Consulta Status](DOCUMENTACION_FUNCIONAL.md#CU-1-Directivo-Consulta-Status)

**¿Cómo gestionar mis indicadores?**
→ [DOCUMENTACION_FUNCIONAL.md § CU-2: Líder de Proceso](DOCUMENTACION_FUNCIONAL.md#CU-2-Líder-de-Proceso-Gestiona)

**¿Cómo crear una Oportunidad de Mejora?**
→ [DOCUMENTACION_FUNCIONAL.md § CU-4: Gestión de OMs](DOCUMENTACION_FUNCIONAL.md#CU-4-Equipo-de-Calidad-Administra-OMs)

**¿Cómo hacer análisis avanzado?**
→ [DOCUMENTACION_FUNCIONAL.md § CU-3: Analista Monitorea](DOCUMENTACION_FUNCIONAL.md#CU-3-Analista-Monitorea-Tendencias)

---

### Arquitectura Técnica

**¿Cómo funciona el pipeline ETL?**
→ [ARQUITECTURA_TECNICA_DETALLADA.md § Pipeline ETL Detallado](ARQUITECTURA_TECNICA_DETALLADA.md#Pipeline-ETL-Detallado)

**¿Cuáles son los módulos core?**
→ [ARQUITECTURA_TECNICA_DETALLADA.md § Módulos Core](ARQUITECTURA_TECNICA_DETALLADA.md#Módulos-Core)

**¿Cómo está estructurada la base de datos?**
→ [ARQUITECTURA_TECNICA_DETALLADA.md § Capa de Datos](ARQUITECTURA_TECNICA_DETALLADA.md#Capa-de-Datos)

**¿Cómo funciona el caché?**
→ [ARQUITECTURA_TECNICA_DETALLADA.md § Estrategia de Caché](ARQUITECTURA_TECNICA_DETALLADA.md#Estrategia-de-Caché)

**¿Cuál es la hoja de ruta técnica?**
→ [ARQUITECTURA_TECNICA_DETALLADA.md § Hoja de Ruta Técnica](ARQUITECTURA_TECNICA_DETALLADA.md#Hoja-de-Ruta-Técnica)

---

### Conceptos de Negocio

**¿Qué es un indicador y cómo se calcula?**
→ [DOCUMENTACION_FUNCIONAL.md § Indicadores y Cumplimiento](DOCUMENTACION_FUNCIONAL.md#Indicadores-y-Cumplimiento)

**¿Qué significan los semáforos (Peligro/Alerta/Cumpl)?**
→ [DOCUMENTACION_FUNCIONAL.md § Semáforo de Riesgo](DOCUMENTACION_FUNCIONAL.md#Semáforo-de-Riesgo)

**¿Qué es una Oportunidad de Mejora?**
→ [DOCUMENTACION_FUNCIONAL.md § Oportunidades de Mejora](DOCUMENTACION_FUNCIONAL.md#Oportunidades-de-Mejora-OM)

**¿Qué casos especiales existen?**
→ [ARQUITECTURA_TECNICA_DETALLADA.md § Especiales de Negocio](ARQUITECTURA_TECNICA_DETALLADA.md#Especiales-de-Negocio)

---

### Ejecución y Operación

**¿Cómo ejecutar el pipeline ETL?**
→ [GUIA_INSTALACION_EJECUCION.md § Ejecución del Pipeline](GUIA_INSTALACION_EJECUCION.md#Ejecución-del-Pipeline)

**¿Cómo automatizar la ejecución diaria?**
→ [GUIA_INSTALACION_EJECUCION.md § Ejecución Programada](GUIA_INSTALACION_EJECUCION.md#Ejecución-Programada-Automatización)

**¿Cómo iniciar el dashboard?**
→ [GUIA_INSTALACION_EJECUCION.md § Ejecución del Dashboard](GUIA_INSTALACION_EJECUCION.md#Ejecución-del-Dashboard)

**¿Cómo ejecutar tests?**
→ [GUIA_INSTALACION_EJECUCION.md § Testing](GUIA_INSTALACION_EJECUCION.md#Testing)

---

### Deployment y Producción

**¿Cómo desplegar a Render?**
→ [GUIA_INSTALACION_EJECUCION.md § Deploy en Render.com](GUIA_INSTALACION_EJECUCION.md#Opción-1-Deploy-en-Rendercom)

**¿Cómo desplegar en VM propia?**
→ [GUIA_INSTALACION_EJECUCION.md § Deploy Manual](GUIA_INSTALACION_EJECUCION.md#Opción-2-Deploy-Manual-en-VMVPS)

**¿Cómo desplegar en Kubernetes?**
→ [GUIA_INSTALACION_EJECUCION.md § Deploy con Docker en K8s](GUIA_INSTALACION_EJECUCION.md#Opción-3-Deploy-con-Docker-en-Kubernetes)

**¿Cómo configurar Nginx como reverse proxy?**
→ [GUIA_INSTALACION_EJECUCION.md § Configuración de Nginx](GUIA_INSTALACION_EJECUCION.md#Configuración-de-Nginx-Reverse-Proxy)

---

### Troubleshooting

**¿Qué hacer si el pipeline falla?**
→ [GUIA_INSTALACION_EJECUCION.md § Troubleshooting](GUIA_INSTALACION_EJECUCION.md#Troubleshooting)

**¿Qué hacer si el dashboard no muestra datos?**
→ [GUIA_INSTALACION_EJECUCION.md § Troubleshooting Dashboard](GUIA_INSTALACION_EJECUCION.md#Troubleshooting-Dashboard)

**¿Cómo reportar problemas?**
→ [README.md § Soporte](README.md#Soporte)

---

## 📊 Matriz de Documentación por Nivel

### Nivel 1: Usuarios Finales (No técnicos)

Lecturas recomendadas:
1. [README.md](README.md) - Secciones: "¿Qué es SGIND?" + "Funcionalidades Clave"
2. [DOCUMENTACION_FUNCIONAL.md](DOCUMENTACION_FUNCIONAL.md) - Secciones: "Resumen Ejecutivo" + "Casos de Uso"
3. [DOCUMENTACION_FUNCIONAL.md](DOCUMENTACION_FUNCIONAL.md) § "Preguntas Frecuentes"

**Tiempo total:** 30-40 minutos

---

### Nivel 2: Técnicos (Developers, QA)

Lecturas recomendadas:
1. [README.md](README.md) - Todas las secciones
2. [GUIA_INSTALACION_EJECUCION.md](GUIA_INSTALACION_EJECUCION.md) - Instalación + Testing
3. [ARQUITECTURA_TECNICA_DETALLADA.md](ARQUITECTURA_TECNICA_DETALLADA.md) - Pipeline ETL + Módulos Core
4. [DOCUMENTACION_FUNCIONAL.md](DOCUMENTACION_FUNCIONAL.md) § "Conceptos de Negocio"

**Tiempo total:** 120-150 minutos

---

### Nivel 3: Arquitectos / Líderes Técnicos

Lecturas recomendadas:
1. Todos los documentos anteriores
2. [ARQUITECTURA_TECNICA_DETALLADA.md](ARQUITECTURA_TECNICA_DETALLADA.md) - Todas las secciones
3. [OPTIMIZACION_FLUJOS_SGIND.md](OPTIMIZACION_FLUJOS_SGIND.md) - Roadmap de mejoras
4. [LIMPIEZA_REPOSITORIO_SGIND.md](LIMPIEZA_REPOSITORIO_SGIND.md) - Plan de refactoring

**Tiempo total:** 180-240 minutos

---

## 🔗 Referencias Cruzadas por Tema

### Pipeline ETL

```
Ejecución:
  → GUIA_INSTALACION_EJECUCION.md § Ejecución del Pipeline
  
Detalles técnicos:
  → ARQUITECTURA_TECNICA_DETALLADA.md § Pipeline ETL Detallado
  
Qué hace cada paso:
  → DOCUMENTACION_FUNCIONAL.md § Proceso 1: Consolidación Diaria
  
Optimizaciones pendientes:
  → OPTIMIZACION_FLUJOS_SGIND.md § 4-Fase Roadmap
```

### Dashboard Streamlit

```
Inicio rápido:
  → README.md § Inicio Rápido
  
Cómo usar:
  → DOCUMENTACION_FUNCIONAL.md § Casos de Uso
  
Arquitectura:
  → ARQUITECTURA_TECNICA_DETALLADA.md § Capa de Presentación
  
Deployment:
  → GUIA_INSTALACION_EJECUCION.md § Ejecución del Dashboard
  
Problemas:
  → GUIA_INSTALACION_EJECUCION.md § Troubleshooting Dashboard
```

### Base de Datos

```
Estructura:
  → ARQUITECTURA_TECNICA_DETALLADA.md § Capa de Datos
  
Setup local (SQLite):
  → GUIA_INSTALACION_EJECUCION.md § Configuración del Entorno
  
Setup producción (PostgreSQL):
  → GUIA_INSTALACION_EJECUCION.md § Despliegue a Producción
  
Persistencia OM:
  → ARQUITECTURA_TECNICA_DETALLADA.md § core/db_manager.py
```

### Configuraciones

```
Variables de entorno:
  → GUIA_INSTALACION_EJECUCION.md § Configuración del Entorno
  
Umbrales de negocio:
  → ARQUITECTURA_TECNICA_DETALLADA.md § core/config.py
  
Streamlit settings:
  → GUIA_INSTALACION_EJECUCION.md § Configuración de Streamlit
  
Mapeos especiales:
  → DOCUMENTACION_FUNCIONAL.md § Conceptos de Negocio
  → ARQUITECTURA_TECNICA_DETALLADA.md § Mapings Hardcoded
```

---

## 📅 Cronología de Lectura Sugerida

### Semana 1: Entendimiento

**Día 1-2: Conceptual**
- README.md (15 min)
- DOCUMENTACION_FUNCIONAL.md § "Resumen Ejecutivo" (10 min)
- DOCUMENTACION_FUNCIONAL.md § "Conceptos de Negocio" (20 min)

**Día 3-4: Técnico básico**
- GUIA_INSTALACION_EJECUCION.md § "Instalación Local" (20 min)
- ARQUITECTURA_TECNICA_DETALLADA.md § "Visión General" (15 min)

**Día 5: Casos de uso**
- DOCUMENTACION_FUNCIONAL.md § "Casos de Uso Principales" (30 min)
- DOCUMENTACION_FUNCIONAL.md § "Guías por Rol" (15 min)

**Total Semana 1:** 135 minutos ≈ 2 horas 15 minutos

---

### Semana 2: Profundización

**Día 1-2: Arquitectura**
- ARQUITECTURA_TECNICA_DETALLADA.md § "Capas de Arquitectura" (60 min)
- ARQUITECTURA_TECNICA_DETALLADA.md § "Pipeline ETL Detallado" (45 min)

**Día 3: Módulos**
- ARQUITECTURA_TECNICA_DETALLADA.md § "Módulos Core" (45 min)

**Día 4: Flujos**
- ARQUITECTURA_TECNICA_DETALLADA.md § "Flujos de Datos" (30 min)

**Día 5: Problemas y roadmap**
- ARQUITECTURA_TECNICA_DETALLADA.md § "Problemas Identificados" (30 min)
- ARQUITECTURA_TECNICA_DETALLADA.md § "Hoja de Ruta Técnica" (20 min)

**Total Semana 2:** 230 minutos ≈ 3 horas 50 minutos

---

### Semana 3: Especialización

**Según tu rol:**

**Si DevOps:**
- GUIA_INSTALACION_EJECUCION.md § "Testing" + "Deployment" (90 min)
- ARQUITECTURA_TECNICA_DETALLADA.md § "Capa de Datos" (30 min)

**Si Backend:**
- DOCUMENTACION_FUNCIONAL.md § "Procesos Clave" (60 min)
- Leer código real en: core/, services/, scripts/

**Si Frontend:**
- ARQUITECTURA_TECNICA_DETALLADA.md § "Capa de Presentación" (45 min)
- Leer código real en: streamlit_app/pages/

**Si Analista:**
- DOCUMENTACION_FUNCIONAL.md § "Para Analistas de BI" (45 min)
- ARQUITECTURA_TECNICA_DETALLADA.md § "Capa de Datos" (30 min)

---

## 🎓 Learning Paths Recomendados

### Path 1: User (Director / Líder)
```
1. README.md (Visión)
   ↓
2. DOCUMENTACION_FUNCIONAL.md § CU-1 (Tu caso de uso)
   ↓
3. Dashboard en vivo (15 minutos explorando)
   ↓
4. DOCUMENTACION_FUNCIONAL.md § FAQs (Preguntas)
   ↓
LISTO - Tiempo: 1 hora
```

### Path 2: Developer Inicial
```
1. README.md (Contexto)
   ↓
2. GUIA_INSTALACION_EJECUCION.md § Instalación (Setup)
   ↓
3. Ejecutar pipeline localmente (experiencia práctica)
   ↓
4. ARQUITECTURA_TECNICA_DETALLADA.md § Módulos Core (Código)
   ↓
5. Leer código en: core/calculos.py (15 min)
   ↓
LISTO - Tiempo: 3 horas
```

### Path 3: Architecture Review
```
1. ANALISIS_ARQUITECTONICO_SGIND.md (Estado actual)
   ↓
2. ARQUITECTURA_TECNICA_DETALLADA.md (Detalles)
   ↓
3. OPTIMIZACION_FLUJOS_SGIND.md (Mejoras)
   ↓
4. LIMPIEZA_REPOSITORIO_SGIND.md (Refactoring)
   ↓
5. Reunión con equipo (decisiones)
   ↓
LISTO - Tiempo: 5 horas (+ 2h reunión)
```

### Path 4: Operational Setup
```
1. GUIA_INSTALACION_EJECUCION.md (Instalación completa)
   ↓
2. Desplegar en Render/VM/K8s (según infraestructura)
   ↓
3. Configurar monitoreo (logs, alertas)
   ↓
4. Crear runbooks (wikis internas)
   ↓
5. Capacitar equipo (documentación)
   ↓
LISTO - Tiempo: 8 horas (+ tiempo de infra)
```

---

## 📞 Cuándo Consultar Cada Documento

| Pregunta | Ir a |
|----------|------|
| "¿Qué es SGIND?" | [README.md](README.md) |
| "¿Cómo lo instalo?" | [GUIA_INSTALACION_EJECUCION.md](GUIA_INSTALACION_EJECUCION.md) |
| "¿Cómo lo uso?" | [DOCUMENTACION_FUNCIONAL.md](DOCUMENTACION_FUNCIONAL.md) |
| "¿Cómo funciona internamente?" | [ARQUITECTURA_TECNICA_DETALLADA.md](ARQUITECTURA_TECNICA_DETALLADA.md) |
| "¿Cuáles son los problemas conocidos?" | [ARQUITECTURA_TECNICA_DETALLADA.md § Problemas Identificados](ARQUITECTURA_TECNICA_DETALLADA.md#Problemas-Identificados) |
| "¿Qué mejoras se planean?" | [OPTIMIZACION_FLUJOS_SGIND.md](OPTIMIZACION_FLUJOS_SGIND.md) |
| "¿Qué puedo eliminar?" | [LIMPIEZA_REPOSITORIO_SGIND.md](LIMPIEZA_REPOSITORIO_SGIND.md) |
| "¿Cómo despliego a producción?" | [GUIA_INSTALACION_EJECUCION.md § Despliegue a Producción](GUIA_INSTALACION_EJECUCION.md#Despliegue-a-Producción) |
| "¿Por qué falla algo?" | [GUIA_INSTALACION_EJECUCION.md § Troubleshooting](GUIA_INSTALACION_EJECUCION.md#Troubleshooting) |

---

## 🗂️ Estructura de Documentación Ideal

```
/
├── README.md                              ← INICIO AQUÍ
├── INDICE_DOCUMENTACION.md (este archivo) ← Navegación
│
├── DOCUMENTACION_FUNCIONAL.md             ← Para usuarios
├── GUIA_INSTALACION_EJECUCION.md         ← Para técnicos
├── ARQUITECTURA_TECNICA_DETALLADA.md      ← Para arquitectos
│
└── /docs/
    ├── analisis_sistema_indicadores.md   ← Análisis previo
    ├── calculos_*.md                      ← Detalles matemáticos
    └── fase3_*.md                         ← Documentación futura
```

---

## 📈 Versioning y Actualizaciones

| Documento | Versión | Fecha | Próxima Revisión |
|-----------|---------|-------|------------------|
| README.md | 1.0 | 11/04/26 | 15/05/26 |
| DOCUMENTACION_FUNCIONAL.md | 1.0 | 11/04/26 | 15/05/26 |
| ARQUITECTURA_TECNICA_DETALLADA.md | 1.0 | 11/04/26 | 15/05/26 |
| GUIA_INSTALACION_EJECUCION.md | 1.0 | 11/04/26 | 15/05/26 |
| INDICE_DOCUMENTACION.md | 1.0 | 11/04/26 | 15/05/26 |

---

**Creado:** 11 de abril de 2026  
**Última actualización:** 11 de abril de 2026  
**Próxima revisión:** 15 de mayo de 2026  
**Mantenedor:** Equipo de BI Institucional

---

## 🚀 Próximos Pasos Sugeridos

1. **Hoy:** Lee README.md + DOCUMENTACION_FUNCIONAL.md
2. **Mañana:** Instala localmente siguiendo GUIA_INSTALACION_EJECUCION.md
3. **Semana 1:** Ejecuta pipeline + dashboard
4. **Semana 2:** Profundiza en ARQUITECTURA_TECNICA_DETALLADA.md
5. **Semana 3:** Considera optimizaciones de OPTIMIZACION_FLUJOS_SGIND.md
6. **Semana 4+:** Ejecuta mejoras según hoja de ruta

¡Bienvenido a SGIND! 🎉
