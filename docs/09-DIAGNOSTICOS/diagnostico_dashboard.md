# Diagnóstico Estructurado de Dashboard

## 1. INVENTARIO DEL DASHBOARD

### Pestañas / Vistas
- Resumen general
- Resumen Estratégico (subtabs: CMI Estratégico, Plan de Mejoramiento, Gestión y Acreditación)
- Resumen por procesos
- Seguimiento operativo (subtabs: Tablero Operativo, Seguimiento reportes, Gestión de OM)

### Componentes Visuales
- **Gráficos**:
  - Sunburst: Jerarquía Linea → Objetivo con cumplimiento promedio
  - Barras: Ranking de riesgo IRIP por indicador, cumplimiento por perspectiva CMI, cumplimiento promedio por factor
  - Líneas: Tendencia de anomalías detectadas, histórico de ejecuciones de cargas
  - Pie: Distribución de niveles de cumplimiento
  - Treemap: Indicadores por factor y característica
- **KPIs**: Total indicadores, En peligro, En alerta, Cumplimiento, Sobrecumplimiento, Indicadores CNA, Factores visibles, Características visibles, Con cumplimiento, Promedio cumplimiento, Total acciones de mejora, Acciones cerradas/abiertas/vencidas
- **Tablas**: Detalle de indicadores, acciones de mejora, reportes, validaciones
- **Filtros**: Año, Mes, Modalidad, Proceso, Estado de reporte, Factor CNA, Característica CNA, Búsqueda por nombre de indicador
- **Navegación**: Sidebar con opción_menu, tabs internas, selectbox, segmented_control

### Propósito de cada elemento
- Visualizar el estado y evolución de indicadores institucionales
- Detectar riesgos, anomalías y alertas
- Analizar cumplimiento por línea, objetivo, proceso y factor
- Monitorear acciones de mejora y reportes operativos
- Facilitar la exploración y filtrado de información clave

## 2. ESTRUCTURA Y STORYTELLING
- Flujo lógico: Inicio (KPIs y alertas) → Resumen ejecutivo → Detalle por proceso/factor → Análisis operativo → Monitoreo de datos
- Narrativa: Parcial, con algunos insights y alertas, pero falta conexión entre hallazgos y recomendaciones
- Redundancias: KPIs similares en varias vistas, tablas extensas sin resumen visual, gráficos repetidos en tabs

## 3. ANÁLISIS DE UX/UI
- Jerarquía visual: Inconsistente entre tabs y subtabs
- Colores: Paleta variable, categorías no siempre consistentes
- Tipografía: Cambia entre componentes, falta unificación
- Espaciado: Variable, algunas vistas saturadas
- Problemas detectados:
  - Saturación de métricas en la vista principal
  - Falta de foco en insights clave
  - Gráficos con leyendas poco descriptivas
  - Tablas extensas sin paginación ni resumen visual
  - Filtros dispersos y no persistentes

## 4. INFORMACIÓN ACTUAL VS FALTANTE
- **Actual**:
  - Cumplimiento por línea, objetivo, meta, indicador
  - Ranking de riesgo IRIP
  - Tendencia de anomalías
  - Cumplimiento por perspectiva CMI
  - Distribución de niveles de cumplimiento
  - Detalle de acciones de mejora
  - Estado de reportes por proceso y periodicidad
  - Alertas de indicadores vencidos o próximos a vencer
  - Detalle de cargas de archivos y validaciones
- **Faltante**:
  - Proyecciones de cumplimiento futuro
  - Comparativos históricos entre periodos (más allá de dos últimos)
  - Alertas personalizadas por usuario o rol
  - Explicaciones contextuales de cada KPI o gráfico
  - Narrativa guiada (storytelling) que conecte los hallazgos
  - Visualización de tendencias a nivel de proceso y subproceso
  - Benchmarks externos o metas institucionales comparativas
  - Integración de comentarios o anotaciones colaborativas

## 5. CLASIFICACIÓN DEL DASHBOARD
- Mixto: Estratégico, Táctico y Operativo (según tab)

## 6. OPORTUNIDADES DE MEJORA
- Unificar paleta de colores y tipografía
- Reorganizar tabs por nivel (estratégico, táctico, operativo)
- Agregar cards de insights narrativos y recomendaciones
- Incluir proyecciones y tendencias históricas en KPIs
- Implementar alertas visuales y notificaciones contextuales
- Agregar tooltips y descripciones en todos los gráficos y métricas
- Permitir personalización de vistas y filtros por usuario
- Modernizar visuales usando cards, infografías y layouts responsivos

## 7. OUTPUT ESTRUCTURADO PARA OTRA IA

```
{
  "tabs": [
    "Resumen general",
    "Resumen Estratégico (con subtabs: CMI Estratégico, Plan de Mejoramiento, Gestión y Acreditación)",
    "Resumen por procesos",
    "Seguimiento operativo (con subtabs: Tablero Operativo, Seguimiento reportes, Gestión de OM)"
  ],
  "visuals": [
    {"type": "sunburst", "location": "Resumen general", "purpose": "Visualizar jerarquía Linea → Objetivo con cumplimiento promedio"},
    {"type": "bar", "location": "Resumen general", "purpose": "Ranking de riesgo IRIP por indicador"},
    {"type": "line", "location": "Resumen general", "purpose": "Tendencia de anomalías detectadas"},
    {"type": "bar", "location": "Resumen general", "purpose": "Cumplimiento por perspectiva CMI"},
    {"type": "metric", "location": "Resumen general", "purpose": "KPIs globales: Total indicadores, En peligro, En alerta, Cumplimiento, Sobrecumplimiento"},
    {"type": "pie", "location": "Plan de Mejoramiento", "purpose": "Distribución de niveles de cumplimiento"},
    {"type": "bar", "location": "Plan de Mejoramiento", "purpose": "Cumplimiento promedio por factor"},
    {"type": "treemap", "location": "Plan de Mejoramiento", "purpose": "Mapa de indicadores por factor y característica"},
    {"type": "table", "location": "Todas", "purpose": "Detalle de indicadores, acciones de mejora, reportes, validaciones"},
    {"type": "line", "location": "Panel de Monitoreo", "purpose": "Histórico de ejecuciones de cargas"},
    {"type": "bar", "location": "Seguimiento reportes", "purpose": "Indicadores por proceso y estado de reporte"}
  ],
  "kpis": [
    "Total indicadores",
    "En peligro",
    "En alerta",
    "Cumplimiento",
    "Sobrecumplimiento",
    "Indicadores CNA",
    "Factores visibles",
    "Características visibles",
    "Con cumplimiento",
    "Promedio cumplimiento",
    "Total acciones de mejora",
    "Acciones cerradas/abiertas/vencidas"
  ],
  "filters": [
    "Año",
    "Mes",
    "Modalidad",
    "Proceso",
    "Estado de reporte",
    "Factor CNA",
    "Característica CNA",
    "Búsqueda por nombre de indicador"
  ],
  "current_info": [
    "Cumplimiento por línea, objetivo, meta, indicador",
    "Ranking de riesgo IRIP",
    "Tendencia de anomalías",
    "Cumplimiento por perspectiva CMI",
    "Distribución de niveles de cumplimiento",
    "Detalle de acciones de mejora",
    "Estado de reportes por proceso y periodicidad",
    "Alertas de indicadores vencidos o próximos a vencer",
    "Detalle de cargas de archivos y validaciones"
  ],
  "missing_info": [
    "Proyecciones de cumplimiento futuro",
    "Comparativos históricos entre periodos (más allá de dos últimos)",
    "Alertas personalizadas por usuario o rol",
    "Explicaciones contextuales de cada KPI o gráfico",
    "Narrativa guiada (storytelling) que conecte los hallazgos",
    "Visualización de tendencias a nivel de proceso y subproceso",
    "Benchmarks externos o metas institucionales comparativas",
    "Integración de comentarios o anotaciones colaborativas"
  ],
  "ux_issues": [
    "Jerarquía visual inconsistente entre tabs y subtabs",
    "Saturación de métricas en la vista principal",
    "Falta de foco en insights clave (storytelling débil)",
    "Colores de categorías no siempre consistentes entre vistas",
    "Tipografía y espaciado variables según componente",
    "Tablas extensas sin paginación ni resumen visual",
    "Gráficos con leyendas poco descriptivas o sin explicación",
    "Filtros dispersos y no persistentes entre vistas"
  ],
  "improvement_opportunities": [
    "Unificar paleta de colores y tipografía para todo el dashboard",
    "Reorganizar tabs para separar claramente niveles estratégico, táctico y operativo",
    "Agregar cards de insights narrativos y recomendaciones automáticas",
    "Incluir proyecciones y tendencias históricas en todos los KPIs clave",
    "Implementar alertas visuales y notificaciones contextuales",
    "Agregar tooltips y descripciones en todos los gráficos y métricas",
    "Permitir personalización de vistas y filtros por usuario",
    "Modernizar visuales usando cards, infografías y layouts responsivos"
  ],
  "proposed_structure": [
    {
      "tab": "Inicio / Resumen Ejecutivo",
      "sections": [
        "Hero section con ISI y alertas",
        "KPIs principales (cards)",
        "Narrativa de insights y recomendaciones",
        "Sunburst de cumplimiento por línea/objetivo",
        "Ranking de riesgo y anomalías"
      ]
    },
    {
      "tab": "Estrategia",
      "sections": [
        "CMI estratégico (gráficos de cumplimiento por perspectiva)",
        "Plan de mejoramiento (filtros dependientes, cards de avance, treemap de factores)",
        "Gestión y acreditación (detalle de indicadores CNA, acciones de mejora)"
      ]
    },
    {
      "tab": "Operación",
      "sections": [
        "Tablero operativo (KPIs y alertas de operación)",
        "Seguimiento de reportes (estado, vencidos, próximos a vencer, gráficos de barras)",
        "Gestión OM (detalle de acciones y cumplimiento operativo)"
      ]
    },
    {
      "tab": "Procesos",
      "sections": [
        "Resumen por proceso (filtros, KPIs, tendencia histórica, comparativos)",
        "Detalle de indicadores por proceso/subproceso"
      ]
    },
    {
      "tab": "Monitoreo de datos",
      "sections": [
        "Panel de cargas y validaciones (histórico, alertas, detalle por archivo)"
      ]
    }
  ]
}
```

## 8. IMPLEMENTACIÓN DE FALTANTES

### Proyecciones de Cumplimiento Futuro
- Implementar un modelo predictivo basado en datos históricos para proyectar el cumplimiento futuro.
- Visualización sugerida: Gráfico de líneas con proyecciones a 6 meses.

### Comparativos Históricos
- Ampliar los gráficos existentes para incluir comparativos históricos más allá de los dos últimos períodos.
- Visualización sugerida: Gráfico de barras apiladas con períodos históricos.

### Personalización de Vistas y Filtros
- Permitir a los usuarios guardar configuraciones personalizadas de filtros y vistas.
- Implementar un sistema de perfiles de usuario para almacenar preferencias.

### Explicaciones Contextuales
- Agregar tooltips detallados en cada KPI y gráfico para explicar su propósito y cálculo.
- Ejemplo: "Este KPI mide el porcentaje de cumplimiento basado en...".

### Narrativa Guiada
- Conectar hallazgos clave con recomendaciones automáticas.
- Implementar una sección de "Insights Narrativos" en cada tab.

### Alertas Personalizadas
- Configurar alertas específicas por usuario o rol.
- Ejemplo: "Indicadores en peligro para el área asignada".

### Benchmarks Externos
- Comparar los indicadores actuales con metas institucionales o benchmarks externos.
- Visualización sugerida: Gráfico de radar o barras comparativas.

---

**Próximos Pasos:**
1. Validar los datos necesarios para las proyecciones y comparativos históricos.
2. Diseñar los nuevos gráficos y componentes interactivos.
3. Implementar las funcionalidades en el código base.
