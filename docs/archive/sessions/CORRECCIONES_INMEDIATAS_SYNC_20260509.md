# CORRECCIONES INMEDIATAS - AGENT 4 SYNC
**Prioridad:** CRÍTICA + ALTA  
**Fecha:** 9 de mayo de 2026  
**Duración:** 2-3 horas  

---

## ✅ TAREA 1: CORREGIR UMBRAL PLAN ANUAL (CRÍTICA)

### Archivo: [docs/core/02_Logica_Indicadores.md](../../docs/core/02_Logica_Indicadores.md)

### Cambio 1: Tabla de categorización PA (líneas 76-85)

**ANTES (INCORRECTO):**
```markdown
#### 📅 Indicadores PLAN ANUAL (Régimen Especial PA)

| Rango | Categoría | Código | Color |
|-------|-----------|--------|-------|
| **< 80%** | Peligro | `PEL` | `#D32F2F` 🔴 |
| **80% - 94.99%** | Alerta | `ALE` | `#FBAF17` 🟡 |
| **≥ 95% (máx 100%)** | Cumplimiento | `CUM` | `#43A047` 🟢 |
```

**DESPUÉS (CORRECTO):**
```markdown
#### 📅 Indicadores PLAN ANUAL (Régimen Especial PA)

| Rango | Categoría | Código | Color |
|-------|-----------|--------|-------|
| **< 80%** | Peligro | `PEL` | `#D32F2F` 🔴 |
| **80% - < 95%** | Alerta | `ALE` | `#FBAF17` 🟡 |
| **≥ 95% (máx 100%)** | Cumplimiento | `CUM` | `#43A047` 🟢 |
```

**Justificación:**
- `UMBRAL_ALERTA_PA = 0.95` en `core/config.py`
- Código usa `c < UMBRAL_ALERTA_PA` → c < 0.95
- Por lo tanto: 80% ≤ c < 95% es Alerta
- Y: c ≥ 95% es Cumplimiento

---

### Cambio 2: Umbrales configurados (líneas 60-65)

**VERIFICACIÓN (OK, no requiere cambio):**
```python
UMBRAL_ALERTA_PA = 0.95                    # ✅ Correcto
UMBRAL_SOBRECUMPLIMIENTO_PA = 1.00         # ✅ Correcto
```

---

### Cambio 3: Sección 1.2 - Características PA (líneas 75-78)

**DESPUÉS agregar nota de precisión:**
```markdown
**Características PA:**
- Cumplen desde 95% (vs 100% en regular)  
- **Nota:** 95% es INCLUSIVO: ≥ 95% = Cumplimiento
- Tope máximo 100% (no sobrecumplimiento)  
- Auto-detectados por ID desde Excel: `Indicadores por CMI.xlsx`
```

---

## ✅ TAREA 2: DOCUMENTAR FUNCIONES FALTANTES

### Archivo: [docs/core/02_Logica_Indicadores.md](../../docs/core/02_Logica_Indicadores.md)

### Ubicación: DESPUÉS de sección 9.3 (después de línea ~440)

### Nuevo contenido:

```markdown
### 9.4 Función: `obtener_color_categoria()`

**Ubicación:** [`core/semantica.py:168`](../../core/semantica.py#L168)

**Propósito:** Retorna el color hexadecimal asignado a una categoría de cumplimiento.

**Data Contract:**

```python
def obtener_color_categoria(categoria: str) -> str:
    """
    Retorna: color hex (ej: "#D32F2F")
    
    PARÁMETROS:
    - categoria: str - Una de: "Peligro", "Alerta", "Cumplimiento", 
                       "Sobrecumplimiento", "Sin dato"
    """
```

**Valores de Retorno:**

| Categoría | Color Hex | Uso |
|-----------|-----------|-----|
| Peligro | #D32F2F | 🔴 Rojo |
| Alerta | #FBAF17 | 🟡 Naranja |
| Cumplimiento | #43A047 | 🟢 Verde |
| Sobrecumplimiento | #6699FF | 🔵 Azul |
| Sin dato | #BDBDBD | ⚪ Gris |

**Ejemplo:**
```python
from core.semantica import obtener_color_categoria

color = obtener_color_categoria("Cumplimiento")
print(color)  # "#43A047"
```

---

### 9.5 Función: `obtener_icono_categoria()`

**Ubicación:** [`core/semantica.py:179`](../../core/semantica.py#L179)

**Propósito:** Retorna el emoji/ícono asignado a una categoría de cumplimiento.

**Data Contract:**

```python
def obtener_icono_categoria(categoria: str) -> str:
    """
    Retorna: emoji (ej: "🔴")
    
    PARÁMETROS:
    - categoria: str - Una de: "Peligro", "Alerta", "Cumplimiento", 
                       "Sobrecumplimiento", "Sin dato"
    """
```

**Valores de Retorno:**

| Categoría | Ícono |
|-----------|-------|
| Peligro | 🔴 |
| Alerta | 🟡 |
| Cumplimiento | 🟢 |
| Sobrecumplimiento | 🔵 |
| Sin dato | ⚪ |

**Ejemplo:**
```python
from core.semantica import obtener_icono_categoria

icono = obtener_icono_categoria("Alerta")
print(icono)  # "🟡"
```

---

### 9.6 Función: `recalcular_cumplimiento_faltante()`

**Ubicación:** [`core/semantica.py:187`](../../core/semantica.py#L187)

**Propósito:** Recalcula cumplimiento cuando falta por derivación de meta/ejecución.

**Data Contract:**

```python
def recalcular_cumplimiento_faltante(
    meta: float,
    ejecucion: float,
    sentido: str = "Positivo",
    id_indicador: str | int | None = None
) -> float:
    """
    Retorna: cumplimiento normalizado (0.0 a 1.3)
    
    PARÁMETROS:
    - meta: float - Valor de meta
    - ejecucion: float - Valor de ejecución
    - sentido: str - "Positivo" o "Negativo"
    - id_indicador: str - Para detectar Plan Anual (opcional)
    """
```

**Lógica:**
- **Positivo:** cumplimiento = ejecución / meta
- **Negativo:** cumplimiento = meta / ejecución
- **Casos especiales:**
  - Si meta=0 AND ejecución=0 → 1.0 (100%)
  - Si negativo AND ejecución=0 → 1.0 (100%)
- **Tope:** mín(cumplimiento, 1.3) = máximo 130%

**Ejemplo:**
```python
from core.semantica import recalcular_cumplimiento_faltante

# Indicador positivo: 85/100 = 0.85 (85%)
c1 = recalcular_cumplimiento_faltante(meta=100, ejecucion=85, sentido="Positivo")
print(c1)  # 0.85

# Indicador negativo: 10/8 = 1.25 (125%)
c2 = recalcular_cumplimiento_faltante(meta=10, ejecucion=8, sentido="Negativo")
print(c2)  # 1.25
```
```

---

## ✅ TAREA 3: DOCUMENTAR PÁGINAS FALTANTES

### Archivo: [docs/core/04_Dashboard.md](../../docs/core/04_Dashboard.md)

### Ubicación: REEMPLAZAR tabla "1. Páginas del Dashboard" (líneas 6-14)

**ANTES:**
```markdown
| Página | Descripción | Fuente Principal |
|--------|-------------|------------------|
| **Resumen General** | Dashboard principal KPIs | Consolidado Cierres |
| **CMI Estratégico** | Indicadores PDI por líneas | Consolidado Cierres + Indicadores por CMI |
| **Plan de Mejoramiento** | Indicadores CNA | Consolidado Cierres + Indicadores por CMI |
| **Gestión OM** | Oportunidades de mejora | Consolidado Historico |
| **Resumen por Proceso** | Vista por proceso/subproceso | Consolidado Semestral |
```

**DESPUÉS:**
```markdown
| Página | Descripción | Fuente Principal | Status |
|--------|-------------|------------------|--------|
| **Resumen General** | Dashboard principal KPIs | Consolidado Cierres | ✅ Producción |
| **CMI Estratégico** | Indicadores PDI por líneas | Consolidado Cierres + Indicadores por CMI | ✅ Producción |
| **CMI Estratégico Tabulado** | Vista tabular del CMI | Consolidado Cierres | ✅ Producción |
| **CMI por Procesos** | Indicadores por proceso | Consolidado Semestral | ✅ Producción |
| **Plan de Mejoramiento** | Indicadores CNA | Consolidado Cierres + Indicadores por CMI | ✅ Producción |
| **Gestión OM** | Oportunidades de mejora | Consolidado Historico | ✅ Producción |
| **Resumen por Proceso** | Vista por proceso/subproceso | Consolidado Semestral | ✅ Producción |
| **Seguimiento Reportes** | Tracking de envío de reportes | Registros internos | 🟡 Beta |
| **Diagnóstico** | Validación de datos y sincronización | Data contracts | 🟡 Beta |
| **Informe por Procesos** | Reporte detallado por proceso | Consolidado Semestral | 🟡 Beta |
| **PDI Acreditación** | Indicadores para acreditación | Indicadores por CMI | 🟡 Beta |
| **Tablero Operativo** | Vista ejecutiva operacional | Consolidado Cierres | 🟡 Beta |
```

---

### Agregar nueva sección: "1.1 Descripciones Detalladas"

```markdown
### 1.1 Descripciones Detalladas de Nuevas Páginas

#### CMI Estratégico Tabulado
- **Archivo:** `streamlit_app/pages/cmi_estrategico_tabulado.py`
- **Propósito:** Presentación tabular del CMI Estratégico (alternativa a viista jerárquica)
- **Datos:** Mismos indicadores que CMI Estratégico, diferentes visualización
- **Filtros:** Línea, Objetivo, Período

#### CMI por Procesos
- **Archivo:** `streamlit_app/pages/cmi_por_procesos_resumen.py`
- **Propósito:** Indicadores organizados por proceso y subproceso institucional
- **Datos:** Indicadores con jerarquía de procesos desde `Subproceso-Proceso-Area.xlsx`
- **Filtros:** Proceso, Subproceso, Período

#### Seguimiento Reportes (Beta)
- **Archivo:** `streamlit_app/pages/seguimiento_reportes.py`
- **Propósito:** Tracking de envío y entrega de reportes
- **Datos:** Registro interno (base datos local)
- **Filtros:** Período, Destinatario, Estado
- **Status:** Experimental - puede cambiar

#### Diagnóstico (Beta)
- **Archivo:** `streamlit_app/pages/diagnostico.py`
- **Propósito:** Validación automática de datos y sincronización entre fuentes
- **Datos:** Análisis de data contracts vs datos reales
- **Alertas:** Infracciones de tipos, datos faltantes, inconsistencias
- **Status:** Experimental

#### Informe por Procesos
- **Archivo:** `streamlit_app/pages/informe_por_procesos.py`
- **Propósito:** Reporte detallado de cumplimiento por proceso
- **Datos:** Consolidado Semestral + Jerarquía de procesos
- **Incluye:** Tablas, gráficos, resumen ejecutivo por proceso
- **Status:** Producción

#### PDI Acreditación
- **Archivo:** `streamlit_app/pages/pdi_acreditacion.py`
- **Propósito:** Indicadores específicos para proceso de acreditación institucional
- **Datos:** Indicadores con flag especial en `Indicadores por CMI.xlsx`
- **Filtros:** Año, Factor de acreditación
- **Status:** Producción

#### Tablero Operativo
- **Archivo:** `streamlit_app/pages/tablero_operativo.py`
- **Propósito:** Dashboard ejecutivo con vista consolidada de salud institucional
- **Datos:** Cierres semestrales + tendencias
- **KPIs:** Total, Peligro, Alerta, Cumplimiento, Sobrecumplimiento
- **Status:** Producción
```

---

### Actualizar "5. Fuentes por Página"

**AGREGAR filas después de tabla existente:**

```markdown
| Página | Función | Archivo | Entrada |
|--------|---------|---------|---------|
| cmi_estrategico | `load_cierres()` | Resultados Consolidados.xlsx | Consolidado Cierres |
| cmi_estrategico | `load_pdi_catalog()` | Indicadores por CMI.xlsx | Worksheet |
| **cmi_estrategico** | **`get_cmi_estrategico_ids()`** | **cmi_filters.py** | **Worksheet (flags)** |
| **cmi_estrategico** | **`ai_analysis.generate_narrative()`** | **ai_analysis.py** | **DataFrame** |
| cmi_estrategico_tabulado | `load_cierres()` | Resultados Consolidados.xlsx | Consolidado Cierres |
| cmi_por_procesos | `_load_calidad_data()` | Monitoreo_Informacion_Procesos.xlsx | Primera hoja |
| cmi_por_procesos | `load_procesos_map()` | Subproceso-Proceso-Area.xlsx | Worksheet |
| seguimiento_reportes | `load_reporte_tracking()` | (Interno) | registros_om.db |
| diagnostico | `validate_data_contracts()` | data_contracts.yaml | Config |
| diagnostico | `_validate_consolidado()` | Resultados Consolidados.xlsx | Todas hojas |
| informe_por_procesos | `_load_calidad_data()` | Monitoreo_Informacion_Procesos.xlsx | Primera |
| informe_por_procesos | `load_procesos_map()` | Subproceso-Proceso-Area.xlsx | Worksheet |
| pdi_acreditacion | `load_cierres()` | Resultados Consolidados.xlsx | Consolidado Cierres |
| pdi_acreditacion | `filter_acreditacion_indicators()` | Indicadores por CMI.xlsx | Flag acreditación |
| tablero_operativo | `_load_base_data_by_type()` | (Múltiples) | Múltiples |
| tablero_operativo | `_generate_narrative()` | ai_analysis.py | DataFrame |
```

---

## ✅ LISTA DE VERIFICACIÓN

### Cambios en 02_Logica_Indicadores.md
- [ ] Línea 77: Cambiar "80% - 94.99%" → "80% - < 95%"
- [ ] Línea 75-78: Agregar nota sobre inclusividad de 95%
- [ ] Línea ~440+: Agregar secciones 9.4, 9.5, 9.6 (funciones públicas)

### Cambios en 04_Dashboard.md
- [ ] Línea 6-14: Reemplazar tabla de páginas con 12 páginas
- [ ] Línea ~20+: Agregar sección 1.1 con descripciones
- [ ] Línea ~140+: Agregar filas en "Fuentes por Página"

### Validación Post-Cambios
- [ ] Ejecutar: `python -c "from docs.core.02_Logica_Indicadores import *"` ✓
- [ ] Verificar links en 04_Dashboard.md
- [ ] Ejecutar: `pytest tests/test_calculos.py::TestCategorizarCumplimiento::test_plan_anual*`
- [ ] Linter: `ruff check docs/core/`

---

## COMMITS RECOMENDADOS

### Commit 1: Fix Plan Anual Threshold Documentation
```
git commit -m "fix(docs): Corregir umbral Plan Anual a 95% en 02_Logica_Indicadores

- Cambiar rango 'Alerta' de '80%-94.99%' a '80%-<95%'
- Aclarar que UMBRAL_ALERTA_PA = 0.95 es inclusivo
- Alinear con implementación en core/config.py

Issue: #AGENT4-H-C1"
```

### Commit 2: Document Missing Functions in core/semantica.py
```
git commit -m "docs: Agregar funciones públicas faltantes en 02_Logica_Indicadores

- Documentar obtener_color_categoria()
- Documentar obtener_icono_categoria()
- Documentar recalcular_cumplimiento_faltante()
- Incluir ejemplos y data contracts

Issue: #AGENT4-H-A3"
```

### Commit 3: Document New Dashboard Pages
```
git commit -m "docs: Agregar 7 páginas nuevas a 04_Dashboard.md

- Documentar CMI Estratégico Tabulado
- Documentar CMI por Procesos
- Documentar Seguimiento Reportes (Beta)
- Documentar Diagnóstico (Beta)
- Documentar Informe por Procesos
- Documentar PDI Acreditación
- Documentar Tablero Operativo
- Actualizar tabla de fuentes

Issue: #AGENT4-H-A1 #AGENT4-H-A2"
```

---

## VERIFICACIÓN FINAL

Ejecutar después de todos los cambios:

```bash
# Validar sintaxis Markdown
npm install -D markdown-cli
markdown-cli docs/core/*.md

# Validar links
./scripts/validate_markdown_links.sh

# Validar consistencia código-docs
python scripts/auditoria_estandar_nivel_cumplimiento.py

# Ejecutar tests relacionados
pytest tests/test_calculos.py -v
pytest tests/test_semantica.py -v

# Resumen
echo "✅ Todas las correcciones completadas"
```

---

**Estimado de tiempo total:** 2-3 horas  
**Complejidad:** BAJA-MEDIA  
**Riesgo:** BAJO  
**Pasos seguros:** SÍ - Solo documentación, sin cambios en código.
