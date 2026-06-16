# Mapeo de paridad: 4 módulos Streamlit → sgind-v2

Documento de referencia para **Informe por Procesos**, **Plan de Mejoramiento**, **Seguimiento Operativo** y **Gestión OM**.

## Estado de implementación (2026-06-13)

| Módulo Streamlit | Ruta Next.js | API | Paridad estimada |
|------------------|--------------|-----|------------------|
| `informe_por_procesos.py` | `/informe-procesos` | `GET /informe/dashboard` | ~85% |
| `plan_mejoramiento.py` | `/plan-mejoramiento` | `GET /plan-mejoramiento/dashboard` | ~90% |
| `seguimiento_reportes.py` | `/seguimiento-operativo` | `GET /seguimiento/dashboard`, `/export` | ~90% |
| `gestion_om.py` | `/gestion-om` | `GET /om/matriz`, `POST /om` | ~75% |

---

## 1. Informe por Procesos

### Tabs (orden Streamlit → Next.js)

1. Resumen Ejecutivo — KPIs score/cumplimiento/alertas, comparativa años, críticos, distribución
2. Indicadores — listado paginado + ficha (reutiliza `CmiProcesosListadoTab`)
3. Calidad de Datos — `CmiProcesosCalidadSection` + `calidad_builders.py`
4. Auditoría — `auditoria_resultado.xlsx` vía `informe_builders.load_auditoria`
5. Propuestas — `Indicadores Propuestos.xlsx` (4 fuentes)
6. Análisis IA — heurística umbrales 80/100

### Filtros

Año, Mes, Clasificación, Frecuencia, Unidad, Proceso, Subproceso — mismos defaults que CMI Procesos (`cmi/procesos/filtros`).

### Backend

- `InformeService` compone `CMIService.get_procesos_dashboard` + resumen ejecutivo + auditoría + propuestas
- Archivos: `informe_builders.py`, `informe_service.py`, `endpoints/informe.py`

### Gaps restantes

- Cards HTML premium del resumen Streamlit (gradientes `design_system`)
- Indicadores por subproceso en tabs anidadas (cards 15/pág) — hoy usa listado tabular CMI
- Gráfico dual-axis histórico en modal (parcial en ficha CMI)

---

## 2. Plan de Mejoramiento

### Secciones

1. Filtros corte (año + Junio/Diciembre)
2. Filtros CNA (factor, característica, búsqueda)
3. 5 KPIs CNA
4. Gráficos: bar factor, donut niveles, stacked factor×nivel, treemap
5. Tabla indicadores CNA
6. Acciones de mejora (KPIs + tabla)

### Fuentes

- `Resultados Consolidados.xlsx` → cierres (`StrategicLoaders.load_cierres`)
- `Indicadores por CMI.xlsx` → `FlagCNA`, catálogo (`load_cna_catalog`)
- `acciones_mejora.xlsx` hoja Acciones

### Backend

- `StrategicProcessors.preparar_cna_con_cierre` (nuevo)
- `plan_mejoramiento_builders.py`, `plan_mejoramiento_service.py`

### Colores semáforo

`NIVEL_COLOR_EXT` en `plan_mejoramiento_builders.py` — paridad con `core/config.py` legacy.

---

## 3. Seguimiento Operativo

### Secciones

1. Filtros: Año, Mes, Proceso, Estado
2. KPIs: Registros, Reportados, Pendientes, No aplica
3. Alertas vencidos / por vencer (ventanas periodicidad)
4. Stacked bar Proceso × Estado
5. Detalle + export Excel

### Fuente

- `data/output/Seguimiento_Reporte.xlsx` → hoja **Tracking Mensual**

### Backend

- `seguimiento_builders.py` — `_detectar_vencidos`, filtros, KPIs
- `GET /seguimiento/export` — Excel filtrado

### Colores estado

Reportado `#28a745`, Pendiente `#ffc107`, No aplica `#6c757d`

---

## 4. Gestión OM

### Secciones

1. Filtros: Año, Mes, Proceso, Subproceso, checkbox Alerta
2. KPIs: Peligro, Alerta, Con OM, Avance OM
3. Tabla matriz 12 columnas con badges y barra avance
4. Formulario asociar OM (`POST /om`)

### Fuentes

- `Consolidado Historico` vía `ETLPipelineService(historico=True)`
- Postgres `registros_om`
- `data/raw/Plan de accion/*.xlsx` → avance OM

### Backend

- `om_builders.py`, `OMMatrizService`, `GET /om/matriz`

### Gaps restantes

- Expansión fila con detalle plan de acción (expand Streamlit)
- Vista alternativa dataframe interactivo
- Integración acciones de mejora en matriz (legacy usa df vacío)

---

## Endpoints nuevos

```
GET  /api/v1/seguimiento/dashboard
GET  /api/v1/seguimiento/export
GET  /api/v1/plan-mejoramiento/dashboard
GET  /api/v1/informe/dashboard
GET  /api/v1/om/matriz
POST /api/v1/om          (existente — formulario OM)
```

## Verificación

```powershell
# Backend
cd sgind-v2/backend
$env:SGIND_DATA_PATH="..\..\data"
$env:PYTHONPATH="."
pytest tests/test_operational_modules.py -q

# Frontend
cd sgind-v2/frontend
npm run build

# Docker (ver UI actualizada)
cd sgind-v2
docker compose up -d --build frontend backend
```
