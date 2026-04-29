# 04 - DASHBOARD Y VISUALIZACIÓN

**Documento:** 04_Dashboard.md  
**Versión:** 1.0  
**Fecha:** 22 de abril de 2026  
**Status:** ✅ Consolidado MDV

---

## 1. Páginas del Dashboard

| Página | Descripción | Fuente Principal |
|--------|-------------|------------------|
| **Resumen General** | Dashboard principal KPIs | Consolidado Cierres |
| **CMI Estratégico** | Indicadores PDI por líneas | Consolidado Cierres + Indicadores por CMI |
| **Plan de Mejoramiento** | Indicadores CNA | Consolidado Cierres + Indicadores por CMI |
| **Gestión OM** | Oportunidades de mejora | Consolidado Historico |
| **Resumen por Proceso** | Vista por proceso | Consolidado Semestral |

---

## 2. Catálogo de Gráficos

### 2.1 Gráficos Disponibles

| ID | Nombre | Tipo Chart | Uso |
|----|--------|------------|-----|
| `BAR_H` | Barra Horizontal | bar | Comparaciones por categoría |
| `BAR_V` | Barra Vertical | bar | Tendencias temporales |
| `LINE` | Línea | line | Evolución histórica |
| `PIE` | Pie | pie | Distribución proporcional |
| `SCATTER` | Dispersión | scatter | Correlaciones |
| `TABLE` | Tabla | table | Datos detallados |
| `GAUGE` | Medidor | gauge | Valores únicos vs umbral |
| `BOLINDER` | Bollinger | line | Bandas de volatilidad |
| `TREEMAP` | Treemap | treemap | Jerarquías |

### 2.2 Colores por Categoría

| Categoría | Color | Uso |
|-----------|-------|-----|
| Peligro | `#D32F2F` 🔴 | Cumplimiento < 80% |
| Alerta | `#FBAF17` 🟡 | Cumplimiento 80-99% |
| Cumplimiento | `#43A047` 🟢 | Cumplimiento 100%+ |
| Sobrecumplimiento | `#6699FF` 🔵 | Cumplimiento ≥ 105% |
| Sin Dato | `#9E9E9E` ⚪ | Sin información |

### 2.3 Personalización

```python
# Paleta personalizada
colores_personalizados = {
    "Peligro": "#D32F2F",
    "Alerta": "#FBAF17", 
    "Cumplimiento": "#43A047",
    "Sobrecumplimiento": "#6699FF"
}

# Aplicar a gráfico
fig = px.bar(df, x="mes", y="valor", color="categoria",
             color_discrete_map=colores_personalizados)
```

---

## 3. Indicadores Clave (KPIs)

### Dashboard Principal

| KPI | Descripción | Cálculo |
|-----|-------------|---------|
| Total Indicadores | Cantidad total | COUNT(*) |
| En Peligro | Indicadores < 80% | COUNT WHERE cumplimiento < 0.80 |
| En Alerta | Indicadores 80-99% | COUNT WHERE cumplimiento 0.80-0.99 |
| Cumpliendo | Indicadores ≥ 100% | COUNT WHERE cumplimiento ≥ 1.00 |
| % Cumplimiento Global | Promedio ponderado | SUM(ejecución) / SUM(meta) |

---

## 4. Filtros por Página

### Resumen General
- **Año:** Dropdown selección año
- **Período:** Semestre/Mes

### CMI Estratégico
- **Línea:** Dropdown líneas PDI
- **Objetivo:** Dropdown objetivos por línea
- **Indicador:** Búsqueda por ID/Nombre

### Plan de Mejoramiento
- **Factor:** Dropdown factores CNA
- **Característica:** Dropdown características
- **Estado OM:** Activa/Cerrada/Nueva

### Gestión OM
- **Estado OM:** Dropdown estados
- **Avance:** Slider rango %
- **Fecha creación:** Range date

---

## 5. Fuentes por Página

### Fuentes Detalladas

| Página | Función | Archivo | Hoja |
|--------|---------|---------|------|
| resumen_general | `_load_consolidado_cierres()` | Resultados Consolidados.xlsx | Consolidado Cierres |
| cmi_estrategico | `load_cierres()` | Resultados Consolidados.xlsx | Consolidado Cierres |
| cmi_estrategico | `load_pdi_catalog()` | Indicadores por CMI.xlsx | Worksheet |
| plan_mejoramiento | `load_cna_catalog()` | Indicadores por CMI.xlsx | Worksheet |
| plan_mejoramiento | `cargar_acciones_mejora()` | acciones_mejora.xlsx | Acciones |
| gestion_om | `cargar_dataset_historico()` | Resultados Consolidados.xlsx | **Consolidado Historico** |
| gestion_om | `_cargar_avance_om()` | Plan de accion/PA_*.xlsx | Primera hoja |
| resumen_por_proceso | `_load_calidad_data()` | Monitoreo_Informacion_Procesos 2025.xlsx | Primera |

---

## 6. Resumen General - Modo Dinámico

### 6.1 Selector de Vista

La página **Resumen General** cuenta con un selector de modo que adapta la visualización según el tipo de datos:

| Modo | Descripción | Datos Mostrados |
|------|-------------|-----------------|
| **Indicadores** | Vista de indicadores PDI | Fichas, chips, Sunburst, narrativa de indicadores |
| **Proyectos** | Vista de proyectos institucionales | Chips de proyectos (cerrados/ejecución/planeación), Gantt 2022-2025 |
| **Plan de Retos** | Vista de retos | Chips de retos, tabla por línea estratégica |
| **Consolidado** | Vista combinada | Integración de indicadores + proyectos + retos |

### 6.2 Funciones de Carga Unificada

```python
# Función principal de carga de datos
_load_base_data_by_type(category: str, year: int)
```

**Parámetros:**
- `category`: "Indicadores" | "Proyectos" | "Plan de Retos" | "Consolidado"
- `year`: Año a consultar

**Retorna:** `(linea_summary, objetivo_df, pdi_base_df, historico_df, pdi_estrategico)`

**Nota importante - Carga de Proyectos:**
Los proyectos se cargan directamente desde `load_cierres()` (no desde `preparar_pdi_con_cierre`), filtrando por el flag `Proyecto == 1` en el archivo `Indicadores por CMI.xlsx`. Se obtiene el último registro por proyecto para el año seleccionado, y se agrega la Línea estratégica desde `worksheet_flags`.

### 6.3 Chips por Categoría

| Categoría | Chips Mostrados |
|-----------|-----------------|
| Indicadores | Total, Sobrecumplimiento, Cumplimiento, Alerta, Peligro |
| Proyectos | Total Proyectos, Cerrados (100%), En Ejecución, Planeación |
| Plan de Retos | Total Retos, % Meta Esperada, % Avance Real, Cumplimiento |
| Consolidado | Total, Indicadores, Proyectos, Retos |

### 6.4 Visualizaciones por Categoría

| Categoría | Visualización Principal |
|-----------|------------------------|
| Indicadores | Tablas: "Indicadores que mejoraron" / "Indicadores en riesgo" |
| Proyectos | Gráfico Gantt (barras horizontales) 2022-2025 con % cumplimiento |
| Plan de Retos | Tarjetas por línea con número de retos y cumplimiento |
| Consolidado | Vista combinada de las tres anteriores |

### 6.5 Narrativa Ejecutiva Dinámica

La función `_generate_narrative()` genera texto personalizado según la categoría:

- **Indicadores**: Habla de "indicadores PDI", salud institucional, alertas
- **Proyectos**: Menciona "proyectos cerrados", "en ejecución", "en planeación"
- **Retos**: Se enfoca en "retos completados" y avance vs metas
- **Consolidado**: Vista combinada general

---

## 7. Dashboard HTML Estáticos

### Archivos Disponibles

| Archivo | Descripción |
|---------|-------------|
| `dashboard_profesional.html` | Dashboard profesional completo |
| `dashboard_diplomatic.html` | Diseño diplomático |
| `dashboard_mini.html` | Versión mínima |
| `dashboard_prueba.html` | Pruebas |

### Características Comunes
- Renderizado con Jinja2
- Datos embebidos en HTML
- Sin servidor backend
- Portables y auditables

---

## 8. Referencias

- **Catálogo gráficos:** [`CATALOGO_GRAFICOS_v2.md`](../../10-GUIAS-ESTANDARES/CATALOGO_GRAFICOS_v2.md)
- **Guía colores:** [`GUIA_PERSONALIZACION_COLORES.md`](../../10-GUIAS-ESTANDARES/GUIA_PERSONALIZACION_COLORES.md)
- **Diagnósticos:** [`diagnostico_dashboard.md`](../../09-DIAGNOSTICOS/diagnostico_dashboard.md)
