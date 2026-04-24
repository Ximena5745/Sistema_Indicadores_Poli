# Componentes de Pestañas (CMI Estratégico)

Este módulo contiene los componentes individuales para cada pestaña de la vista del CMI Estratégico Tabulado.

## Estructura

- `tab_resumen.py`: Tarjetas de KPI principales, gráfico de distribución y panel de insights automáticos.
- `tab_objetivos.py`: Vista jerárquica (Línea -> Objetivo -> Indicador) utilizando un gráfico Sunburst y tabla de detalles con filtros anidados.
- `tab_analisis.py`: Análisis de tendencias históricas, indicadores en nivel crítico (ranking) y mapa de calor de cumplimiento por periodo.
- `tab_listado.py`: Tabla completa de indicadores, búsqueda rápida, filtrado de estados, paginación delegada al componente de tabla y exportación a Excel.
- `tab_ficha.py`: Detalle específico de un indicador con gráfico tipo gauge, métricas comparativas (meta vs ejecución) y detalles históricos y descriptivos.
- `tab_alertas.py`: Centro de notificaciones basado en umbrales de desempeño, mostrando indicadores críticos y de monitoreo constante.

## Integración

Las pestañas se importan y ensamblan en el archivo de vista `streamlit_app/pages/cmi_estrategico_tabulado.py`.
Todas comparten el mismo DataFrame `df` filtrado globalmente (año, corte semestral, línea, objetivo).
La navegación entre pestañas (ej. Listado -> Ficha) se apoya en el estado de la sesión (`st.session_state["cmi_tab_selected"]`).
