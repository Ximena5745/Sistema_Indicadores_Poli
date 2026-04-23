# PROJECT_RULES.md

# Sistema de Gobierno Técnico — Proyecto de Indicadores Estratégicos, CMI y Planeación Institucional

Este documento define las reglas obligatorias de operación para cualquier agente, desarrollador o proceso automatizado que realice modificaciones sobre el proyecto.

El objetivo principal es garantizar:

- consistencia funcional
- trazabilidad de indicadores
- unicidad de fórmulas
- reutilización de lógica
- estabilidad arquitectónica
- reducción de deuda técnica
- documentación viva y verificable
- minimización de regresiones

---

# 1. PRINCIPIO GENERAL

Antes de realizar cualquier cambio:

## SIEMPRE validar primero

Nunca modificar antes de entender.

Toda modificación debe iniciar con:

1. revisión del contexto funcional
2. revisión de arquitectura existente
3. revisión de documentación asociada
4. identificación de funciones reutilizables
5. análisis de impacto cruzado
6. validación de dependencias técnicas
7. verificación de contratos de datos
8. validación de fórmulas actuales
9. revisión de consistencia histórica

---

# 2. REGLAS DE DESARROLLO

## 2.1 Reutilización obligatoria

Nunca crear una nueva función si ya existe una función global con el mismo objetivo.

Priorizar siempre:

- funciones compartidas
- hooks globales
- servicios reutilizables
- componentes comunes
- helpers centralizados
- reglas de cálculo existentes
- estructuras ya normalizadas

Evitar:

- duplicación de lógica
- forks funcionales
- validaciones paralelas
- múltiples fuentes de verdad

---

## 2.2 No modificar lógica de negocio sin validación

Nunca cambiar:

- fórmulas
- cálculos de cumplimiento
- reglas de semaforización
- ponderaciones
- consolidaciones
- históricos
- reglas de aprobación
- lógica de estados

sin validar previamente:

- implementación actual
- documentación funcional
- dependencias relacionadas
- impacto en dashboards
- impacto en reportes PDF
- impacto en procesos de aprobación

---

## 2.3 Evitar deuda técnica

Está prohibido introducir:

- código muerto
- imports huérfanos
- rutas sin uso
- componentes duplicados
- lógica fragmentada
- hardcodes innecesarios
- cálculos locales inconsistentes
- bypass de arquitectura existente
- consultas SQL redundantes
- duplicación documental

---

# 3. REGLAS ESPECÍFICAS DE INDICADORES

## 3.1 Fuente única de cálculo

Cada indicador debe tener:

## UNA sola fórmula oficial

Nunca deben existir:

- múltiples fórmulas para el mismo indicador
- diferentes cálculos entre frontend y backend
- diferencias entre dashboard y reportes
- diferencias entre visualización y exportación

La fórmula oficial debe ser única, centralizada y trazable.

---

## 3.2 Validación obligatoria de indicadores

Todo indicador debe validar:

- definición clara
- objetivo funcional
- fórmula única
- unidad de medida
- meta definida
- línea base
- periodicidad
- responsable
- fuente de información
- trazabilidad histórica
- control de cambios
- consistencia entre periodos
- semaforización homogénea
- avance esperado vs avance real
- cumplimiento vs meta
- cumplimiento acumulado vs periodo

---

## 3.3 Semaforización

La lógica de semaforización debe ser homogénea.

Nunca permitir:

- colores inconsistentes
- reglas distintas para indicadores equivalentes
- cálculos manuales aislados

Toda semaforización debe provenir de funciones centralizadas.

---

# 4. REGLAS DE DASHBOARDS Y VISUALIZACIÓN

## 4.1 Jerarquía visual obligatoria

Todo dashboard debe permitir navegación:

## Macro → Meso → Micro

Orden obligatorio:

1. Resumen Ejecutivo
2. Línea Estratégica
3. Objetivo Estratégico
4. Meta Estratégica
5. Indicador
6. Detalle técnico

Nunca mostrar complejidad operativa antes del resumen ejecutivo.

---

## 4.2 Preferencia visual

Priorizar:

- tarjetas ejecutivas
- KPIs resumidos
- gráficos con contexto
- tablas condensadas
- tooltips explicativos
- drill-down progresivo
- alertas priorizadas
- indicadores en riesgo visibles

Evitar:

- fichas excesivamente técnicas
- tablas extensas sin resumen
- ruido visual
- navegación redundante
- exceso de scroll
- duplicidad de información

---

# 5. REGLAS DE SIDEBAR Y NAVEGACIÓN

Toda modificación sobre:

- sidebar
- pestañas
- módulos
- rutas
- navegación
- permisos

debe validar:

- consistencia de rutas
- imports relacionados
- guards/permisos
- breadcrumbs
- menús dependientes
- componentes hijos
- referencias cruzadas

Eliminar una pestaña implica eliminar también:

- rutas
- imports
- permisos
- componentes muertos
- referencias obsoletas

Nunca dejar navegación parcial.

---

# 6. REGLAS DE DOCUMENTACIÓN

## 6.1 Living Documentation obligatorio

La documentación debe reflejar el sistema real.

Nunca permitir:

- documentación obsoleta
- documentación duplicada
- reglas contradictorias
- especificaciones desconectadas del código

Aplicar:

- Living Documentation
- Data Contracts
- Specification by Example

---

## 6.2 Toda modificación debe validar coherencia con

- documentación funcional
- documentación técnica
- SQL
- procesos de negocio
- reglas de aprobación
- flujos institucionales
- indicadores regulatorios
- entes de control si aplica

---

# 7. REGLAS DE VALIDACIÓN FINAL

Antes de cerrar cualquier tarea validar obligatoriamente:

## Técnico

- build sin errores
- lint sin errores
- imports limpios
- rutas funcionales
- navegación correcta
- sin componentes rotos
- sin regresiones visibles
- sin código muerto
- sin duplicidad funcional

## Funcional

- cálculos consistentes
- fórmulas verificadas
- indicadores correctos
- filtros funcionales
- reportes correctos
- aprobaciones consistentes
- históricos intactos

## Documental

- documentación actualizada si aplica
- trazabilidad conservada

---

# 8. FORMATO OBLIGATORIO DE RESPUESTA DEL AGENTE

Toda respuesta debe incluir:

## 1. Hallazgos previos

Qué se encontró antes de modificar.

## 2. Archivos afectados

Qué archivos participan.

## 3. Cambios realizados

Qué se modificó exactamente.

## 4. Riesgos detectados

Qué podría verse afectado.

## 5. Validación final

Qué pruebas se ejecutaron.

## 6. Mejoras recomendadas

Qué conviene corregir después.

Nunca responder únicamente:
“listo”, “ajustado”, “hecho”.

Siempre justificar técnicamente.

---

# 9. REGLA FINAL

## Nunca asumir

Siempre verificar.

## Nunca duplicar

Siempre reutilizar.

## Nunca romper

Siempre validar.

## Nunca improvisar

Siempre documentar.