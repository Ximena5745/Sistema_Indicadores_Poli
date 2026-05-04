# Propuesta Integral de Mejora
## CMI por Procesos (UI-UX, Storytelling, Rendimiento y Gobierno de Datos)

Fecha: 2026-05-04
Alcance: Frontend + backend de la seccion CMI por procesos
Publico objetivo: Lideres de procesos y equipos

---

## 1) Resumen ejecutivo

La seccion actual de CMI por procesos presenta cuatro problemas estructurales:

1. Informacion mal distribuida: se combina vista ejecutiva, comparativas y propuesta en un flujo largo sin progresion narrativa clara.
2. Paginas pesadas: hay bloques duplicados de graficos/tablas y calculo en tiempo de render.
3. Filtros no compactos: la interfaz de filtros no usa patron visual consistente (fondo, color, jerarquia, persistencia).
4. Desalineacion documentacion-codigo: la documentacion de filtros/fuentes no refleja completamente la implementacion real y viceversa.

La propuesta define una arquitectura de experiencia por capas narrativas (Estado -> Causas -> Riesgos -> Accion), con filtros compactos y persistentes, visuales orientados a decisiones, y un plan de optimizacion tecnica para reducir latencia y complejidad.

---

## 2) Hallazgos de auditoria (backend + frontend)

### 2.1 Hallazgos de frontend

1. Flujo largo y cargado en una sola pantalla
- La pagina principal concentra multiples secciones y comparativas en una sola vista.
- Referencia: streamlit_app/pages/resumen_por_proceso.py (render principal).

2. Duplicacion funcional visible
- El bloque de comparativa de procesos (grafico + tabla + insights) esta repetido entre pestanas.
- Esto incrementa peso cognitivo y costo de mantenimiento.
- Referencia: streamlit_app/pages/resumen_por_proceso.py.

3. Estilos globales superpuestos
- Existen estilos en streamlit_app/styles/main.css y streamlit_app/styles/styles.css con bloques solapados para sidebar, base visual y tipografia.
- Riesgo: inconsistencia visual por orden de carga y dificultad para mantener tokens.
- Referencias: streamlit_app/styles/main.css, streamlit_app/styles/styles.css.

4. Filtros poco compactos y sin jerarquia visual fuerte
- Filtros operan como controles sueltos, no como bloque compacto de contexto.
- El usuario no percibe claramente niveles: globales vs contextuales.

### 2.2 Hallazgos de backend / datos

1. Reglas CMI por procesos centralizadas, pero con diferencia documental
- El filtro tecnico usa Subprocesos == 1 e Ind act == 1 para IDs validos de CMI por procesos.
- Referencia: services/cmi_filters.py.
- Riesgo: esta condicion no siempre esta explicitada en la documentacion de filtros por pagina.

2. Fuente de datos principal correcta, pero narrativa de fuente no uniforme
- DataService usa cargar_dataset() desde Consolidado Semestral para seguimiento de procesos.
- Referencia: streamlit_app/services/data_service.py.
- La documentacion de dashboard incluye partes de resumen_por_proceso con otras fuentes de apoyo y puede inducir confusion de fuente principal vs fuentes complementarias.
- Referencias: docs/core/04_Dashboard.md, docs/archive/FUENTES_POR_PAGINA.md.

3. Error estructural activo en codigo de la pagina
- El archivo presenta error de sangria y referencias fuera de alcance en la seccion de indicadores propuestos.
- Esto es un riesgo critico de estabilidad.
- Referencia: streamlit_app/pages/resumen_por_proceso.py (zona final).

---

## 3) Contraste documentacion vs implementacion

### 3.1 Filtros

- Documentacion MDV lista filtros para Resumen General, CMI Estrategico, Plan y Gestion OM, pero no explicita con el mismo detalle los filtros actuales de CMI por procesos (anio, mes, proceso padre, subproceso, cortes globales comparativos).
- Referencia: docs/core/04_Dashboard.md.

### 3.2 Fuentes

- Para Resumen por Proceso, la documentacion de fuentes por pagina indica Consolidado Semestral via DataService (correcto), junto a fuentes complementarias de calidad/auditoria.
- Referencia: docs/archive/FUENTES_POR_PAGINA.md.
- En la implementacion, el subtitulo de algunas secciones menciona Consolidado Cierres mientras el flujo de datos arranca desde tracking consolidado y filtros en semestral para CMI por procesos.
- Esto debe homogenizarse en etiquetas de UI y documentacion.

---

## 4) Propuesta de rediseno UI-UX con storytelling

### 4.1 Arquitectura narrativa para lideres de proceso

Se recomienda reemplazar la lectura vertical extensa por una secuencia de 4 bloques:

1. Estado actual (Que esta pasando)
- 4 tarjetas ejecutivas maximas: Indicadores activos, Cumplimiento promedio, En riesgo, Variacion vs base.
- 1 visual unico de contexto: distribucion por tipo de proceso.

2. Causas (Por que pasa)
- Top 5 procesos con mayor caida.
- Top 5 procesos con mayor mejora.
- Tabla corta explicativa con una sola columna de insight accionable.

3. Riesgo y prioridad (Donde actuar primero)
- Matriz prioridad (Impacto x Severidad) con clasificacion A/B/C.
- Lista priorizada de 8-12 indicadores criticos con responsable sugerido.

4. Accion (Que hacer ahora)
- Recomendaciones por proceso con botones de seguimiento (OM, plan, evidencia, auditoria).
- Export ejecutivo (1 pagina) y export analitico (detalle).

Resultado esperado: reducir tiempo de comprension de 8-10 minutos a 2-3 minutos por lider.

### 4.2 Estructura de navegacion sugerida

Pestanas recomendadas para CMI por procesos:

1. Resumen Ejecutivo
2. Causas y Variaciones
3. Riesgos y Alertas
4. Plan de Accion
5. Detalle Analitico

Regla UX: cada pestana debe responder una pregunta unica y evitar duplicar visuales.

### 4.3 Rediseno de filtros (compactos y con formato)

Disenar una barra de filtros fija superior con dos niveles:

1. Nivel global (persistente en session)
- Anio
- Mes
- Frecuencia
- Tipo de indicador

2. Nivel contextual (depende de seleccion)
- Proceso padre
- Subproceso
- Tipo de proceso

Patrones visuales:

- Fondo del bloque de filtros: surface suave institucional
- Chips de estado activo con contraste alto
- Boton Limpiar y boton Restablecer vista
- Etiqueta de contexto siempre visible: Corte + proceso + subproceso

### 4.4 Sistema visual orientado a decisiones

Eliminar o reducir:

- Graficos repetidos por pestana
- Tablas largas sin resumen
- Visuales sin pregunta de negocio asociada

Conservar e impulsar:

1. Barra comparativa 2026 vs base
2. Heatmap de cumplimiento por unidad/periodo
3. Pareto de riesgo (80/20)
4. Tabla de prioridad accionable (max 12 filas)

Regla de valor para cada grafico:
- Si no habilita una decision concreta en menos de 30 segundos, no se publica en vista ejecutiva.

---

## 5) Paleta y sistema de diseno (alineado a documentacion)

Tomar como fuente oficial del sistema de diseno:

- streamlit_app/styles/design_system.py
- docs/core/04_Dashboard.md

Semaforo institucional:

- Peligro: #D32F2F
- Alerta: #FBAF17
- Cumplimiento: #43A047
- Sobrecumplimiento: #6699FF
- Sin dato: #9E9E9E

Lineas estrategicas oficiales:

- Expansion: #FBAF17
- Transformacion organizacional: #42F2F2
- Calidad: #EC0677
- Experiencia: #1FB2DE
- Sostenibilidad: #A6CE38
- Educacion para toda la vida: #0F385A

Regla UI: mover colores hardcodeados de tarjetas/plots a tokens centralizados para evitar divergencia visual.

---

## 6) Propuesta tecnica para reducir peso y mejorar performance

### 6.1 Frontend

1. Extraer componentes
- Separar render en componentes por pestana y evitar bloques duplicados.

2. Lazy rendering
- Calcular y pintar solo la pestana activa.

3. Paginacion y resumen previo
- Mostrar top N por defecto y detalle bajo demanda.

4. CSS unificado
- Mantener un solo archivo maestro de tema y tokens.
- Dejar estilos por componente solo para casos especificos.

### 6.2 Backend / datos

1. Cache por nivel de agregacion
- Cache para dataset base, cache para agregados por proceso y cache para comparativas.

2. Preagregados mensuales
- Generar tabla materializada por anio-mes-proceso-subproceso para evitar groupby repetitivos en render.

3. Contrato de datos de filtros
- Definir un contrato unico de filtros y opciones validas (orden, labels, llaves).

4. Homologacion de fuentes en UI
- Etiqueta de fuente unificada por bloque: principal y complementaria.

### 6.3 Meta de rendimiento

Objetivos operativos:

1. Tiempo de carga inicial: <= 2.5 s
2. Cambio de filtro global: <= 1.2 s
3. Cambio de pestana: <= 0.7 s
4. Memoria en sesion: reduccion >= 30%

---

## 7) Plan de implementacion por fases

### Fase 0 (estabilidad y limpieza) - 1 semana

1. Corregir errores estructurales en resumen_por_proceso.py
2. Eliminar duplicaciones de bloque de comparativa
3. Unificar tema visual basico (tokens)

### Fase 1 (rediseno UX base) - 2 semanas

1. Nueva barra de filtros compacta y persistente
2. Nueva pestana Resumen Ejecutivo
3. Nueva pestana Causas y Variaciones

### Fase 2 (storytelling y accion) - 2 semanas

1. Pestana Riesgos y Alertas
2. Pestana Plan de Accion con prioridades
3. Export ejecutivo y analitico

### Fase 3 (performance y gobierno de datos) - 2 semanas

1. Preagregados y cache por capa
2. Contrato de filtros y verificacion automatica
3. Actualizacion de documentacion MDV + pruebas

---

## 8) Indicadores de exito

### UX / negocio

1. Tiempo medio para identificar top 3 riesgos: -60%
2. Tasa de uso de filtros contextuales: +40%
3. Disminucion de scroll medio por sesion: -50%
4. Satisfaccion de lideres (encuesta): >= 4.5/5

### tecnico

1. Reduccion de lineas en modulo de pagina principal: -35% a -50%
2. Reduccion de duplicacion de logica de visuales: >= 70%
3. Cobertura de pruebas de CMI por procesos: >= 80% en logica de filtros/agregados

---

## 9) Backlog priorizado (accionable)

Prioridad alta:

1. Corregir errores de sintaxis/alcance en resumen_por_proceso.py
2. Eliminar duplicacion de bloque comparativo
3. Introducir componentes por pestana
4. Unificar fuentes y etiquetas en UI
5. Redisenar barra de filtros compacta

Prioridad media:

1. Matriz de priorizacion riesgo (impacto x severidad)
2. Tabla accionable con responsable y proxima accion
3. Heatmap por unidad y periodo

Prioridad baja:

1. Personalizacion por perfil de usuario
2. Recomendaciones asistidas por IA

---

## 10) Recomendacion final

Para el publico objetivo (lideres de proceso y equipos), la mejora clave no es agregar mas graficos, sino reducir complejidad y ordenar la historia de decision:

Estado -> Causas -> Riesgo -> Accion.

Si se ejecuta el plan por fases, la seccion CMI por procesos pasara de una vista informativa extensa a un tablero de decision institucional, mas rapido, consistente con la documentacion y visualmente alineado con la paleta oficial del proyecto.
