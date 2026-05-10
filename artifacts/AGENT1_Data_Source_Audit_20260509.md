# AGENT 1 — DATA SOURCE AUDIT
## Auditoría de Fuentes de Datos — SGIND
**Sistema:** Sistema de Indicadores Institucionales — Politécnico Grancolombiano  
**Fecha de auditoría:** 9 de mayo de 2026  
**Agente:** Agent 1 / Data Source Audit  
**Framework:** Software Intelligence Platform — SGIND v1.0  

---

## 1. INVENTARIO DE FUENTES (12 fuentes identificadas)

### Clasificación por criticidad

| Nivel | Fuentes | Descripción |
|-------|---------|-------------|
| 🔴 CRÍTICAS | 3 | Sin estas fuentes el ETL no funciona |
| 🟡 IMPORTANTES | 2 | Enriquecen el dashboard y CMI estratégico |
| 🟢 SECUNDARIAS | 4 | Gestión OM, referencias históricas |
| 🔵 PERSISTENCIA | 2 | Bases de datos operativas |
| ⚪ HUÉRFANAS | 1 | Presente pero origen y uso no claros |

---

## 2. FUENTES CRÍTICAS — El ETL no arranca sin estas

---

### FUENTE 1: Archivos Kawak anuales (`data/raw/Kawak/*.xlsx`)

| Atributo | Valor |
|----------|-------|
| **Ruta** | `data/raw/Kawak/` |
| **Archivos** | `2022.xlsx`, `2023.xlsx`, `2024.xlsx`, `2025.xlsx`, `2026.xlsx` ✅ (todos presentes) |
| **Tipo** | Excel — Catálogos anuales de indicadores |
| **Producida por** | Descarga manual desde plataforma Kawak |
| **Consumida por** | [scripts/consolidar_api.py](../scripts/consolidar_api.py) (COLS_KAWAK, línea 37) |
| **Columnas esperadas** | `Año`, `Id`, `Indicador`, `Clasificacion`, `Proceso`, `Tipo`, `Tipo de variable`, `Periodicidad`, `Sentido` |
| **Contrato formal** | ✅ Definido en [config/data_contracts.yaml](../config/data_contracts.yaml) |
| **Trazabilidad** | ✅ Por `Id` + `Año` |
| **Validación en uso** | `_encontrar_col()` por alias insensible a mayúsculas; `_id_str()` normaliza `474.0 → "474"` |
| **Problema conocido** | Entidades HTML sin decodificar en origen (`&oacute;` → `ó` se aplica en `_limpiar_html()`) |

**Campos normalizados en ingesta:**

```
Id            → _id_str() quita ".0" de floats
Indicador     → _limpiar_html() decodifica entidades HTML
```

**Estado:** ✅ COBERTURA COMPLETA 2022–2026

---

### FUENTE 2: Archivos API anuales (`data/raw/API/*.xlsx`)

| Atributo | Valor |
|----------|-------|
| **Ruta** | `data/raw/API/` |
| **Archivos** | `2022.xlsx`, `2023.xlsx`, `2024.xlsx`, `2025.xlsx`, `2026.xlsx` ✅ |
| **Tipo** | Excel — Resultados ejecutados por período |
| **Producida por** | Exportación/descarga desde API Kawak |
| **Consumida por** | [scripts/consolidar_api.py](../scripts/consolidar_api.py) → genera `Consolidado_API_Kawak.xlsx` |
| **Columnas esperadas** | `fecha`, `Id`, `Indicador`, `resultado`, `meta`, `analisis`, `variables`, `series`, etc. |
| **Contrato formal** | ✅ En `config/data_contracts.yaml` (sección `kawak_consolidado`) |
| **Trazabilidad** | ✅ Campo `LLAVE = Id-AAAA-MM-DD` creado en consolidación |
| **Campo "No Aplica"** | Detectado cuando `analisis` contiene "no aplica" O `resultado=NaN` sin variables/series |

**Estado:** ✅ COBERTURA COMPLETA 2022–2026

---

### FUENTE 3: Resultados Consolidados (`data/output/Resultados Consolidados.xlsx`)

| Atributo | Valor |
|----------|-------|
| **Ruta** | `data/output/Resultados Consolidados.xlsx` |
| **Tipo** | Excel — Salida oficial del ETL (4 hojas) |
| **Producida por** | [scripts/actualizar_consolidado.py](../scripts/actualizar_consolidado.py) (Orquestador ETL v8) |
| **Consumida por** | Dashboard principal (todas las páginas excepto Gestión OM) |
| **Contrato formal** | ✅ COMPLETO en `config/data_contracts.yaml` (sección `resultados_consolidados`) |
| **Trazabilidad** | ✅ `Id` + `Fecha` por período |
| **Backup disponible** | `Resultados Consolidados.bak.xlsx` ⚠️ Manual — sin versionado automático |
| **Archivos relacionados** | `Resultados Consolidados VALORES.xlsx`, `Seguimiento_Reporte.xlsx` |

**Hojas contenidas (4 hojas oficiales):**

| Hoja | Propósito | Campos clave |
|------|-----------|--------------|
| **Consolidado Semestral** | Fuente principal del dashboard | `Id`, `Indicador`, `Fecha`, `Meta`, `Ejecución`, `Cumplimiento`, `Sentido`, `Categoría` |
| **Consolidado Histórico** | Histórico completo para Gestión OM | Igual + histórico extendido |
| **Consolidado Cierres** | Proyectos / cierres diciembre | Semestral, tope diciembre |
| **Catálogo Indicadores** | Metadatos de indicadores | `Id`, `Clasificación`, `Proceso`, `Periodicidad`, `tipo_api` |

**Estado:** ✅ CRÍTICO — Fuente de verdad para el dashboard

---

## 3. FUENTES IMPORTANTES — Enriquecen el análisis

---

### FUENTE 4: Indicadores por CMI (`data/raw/Indicadores por CMI.xlsx`)

| Atributo | Valor |
|----------|-------|
| **Ruta** | `data/raw/Indicadores por CMI.xlsx` |
| **Tipo** | Excel — Mapeo de indicadores a perspectivas CMI y Líneas PDI |
| **Producida por** | Gestión manual (equipo de calidad) |
| **Consumida por** | [services/data_loader.py](../services/data_loader.py), páginas CMI estratégico |
| **Contrato formal** | ⚠️ PARCIAL en `config/data_contracts.yaml` (sección `indicadores_cmi`) |
| **Campos clave** | `Id`, `Línea`, `Objetivo`, `CMI`, `Plan anual`, `Proyecto`, `Subproceso`, `Ind act` |
| **Impacto crítico** | **ALTO** — Determina qué indicadores usan umbral 95% vs 100% |
| **Carga dinámica** | ✅ `IDS_PLAN_ANUAL` se carga desde esta fuente en [core/config.py:63-110](../core/config.py) |
| **Campo deprecado** | `Ind act` — Documentado como deprecado; usar `Subproceso==1` + validación cruzada con Kawak |

**⚠️ ALERTA:** Campo `Ind act` está marcado como deprecado en el contrato pero puede estar activo en código.

**Estado:** ⚠️ CONTRATO PARCIAL — Falta formalizar validaciones de Línea/Objetivo

---

### FUENTE 5: Jerarquía de Procesos (`data/raw/Subproceso-Proceso-Area.xlsx`)

| Atributo | Valor |
|----------|-------|
| **Ruta** | `data/raw/Subproceso-Proceso-Area.xlsx` |
| **Tipo** | Excel — Mapeo jerárquico autorizado de procesos |
| **Producida por** | Gestión manual (actualización 11-abr-2026) |
| **Consumida por** | [services/procesos.py](../services/procesos.py), [services/data_loader.py](../services/data_loader.py) |
| **Contrato formal** | ✅ Exportado a [config/mapeos_procesos.yaml](../config/mapeos_procesos.yaml) |
| **Trazabilidad** | ⚠️ Manual — sin audit trail de cambios en el YAML |
| **Estructura** | 15 procesos padre con 70+ subprocesos |
| **Caché** | ✅ Invalidación automática al cambiar |

**Estado:** ✅ BIEN GESTIONADA — Mejora: agregar audit trail de cambios

---

## 4. FUENTES SECUNDARIAS — Gestión OM e históricas

---

### FUENTE 6: Planes de Acción (`data/raw/Plan de accion/`)

| Atributo | Valor |
|----------|-------|
| **Ruta** | `data/raw/Plan de accion/` |
| **Archivos** | `PA_1.xlsx`, `PA_2.xlsx` |
| **Tipo** | Excel — Registros de acciones correctivas por período |
| **Producida por** | Gestión manual |
| **Consumida por** | [streamlit_app/pages/gestion_om.py](../streamlit_app/pages/) |
| **Contrato formal** | ❌ SIN CONTRATO |
| **Trazabilidad** | ⚠️ Por `Id_OM` — deduplicación manual al concatenar archivos |
| **Riesgo** | MEDIO — Datos inconsistentes posibles, sin validación automática |

**Estado:** ❌ SIN CONTRATO — Acción requerida: formalizar schema YAML

---

### FUENTE 7: OM Histórica (`data/raw/OM.xlsx`)

| Atributo | Valor |
|----------|-------|
| **Ruta** | `data/raw/OM.xlsx` |
| **Tipo** | Excel — Historial de Oportunidades de Mejora |
| **Consumida por** | [services/data_loader.py](../services/data_loader.py) |
| **Contrato formal** | ❌ SIN CONTRATO |
| **Trazabilidad** | ❌ Sin campos de auditoría definidos |

**Estado:** ❌ SIN CONTRATO — Referencia histórica, formalizar schema

---

### FUENTE 8: Acciones de Mejora (`data/raw/acciones_mejora.xlsx`)

| Atributo | Valor |
|----------|-------|
| **Ruta** | `data/raw/acciones_mejora.xlsx` |
| **Tipo** | Excel — Registro de acciones |
| **Consumida por** | [services/data_loader.py](../services/data_loader.py) |
| **Contrato formal** | ❌ SIN CONTRATO |

**Estado:** ❌ SIN CONTRATO — Baja prioridad

---

### FUENTE 9: Ficha Técnica (`data/raw/Ficha_Tecnica_Indicadores.xlsx`)

| Atributo | Valor |
|----------|-------|
| **Ruta** | `data/raw/Ficha_Tecnica_Indicadores.xlsx` |
| **Tipo** | Excel — Documentación técnica de indicadores |
| **Consumida por** | [services/data_loader.py](../services/data_loader.py) (si existe en disco) |
| **Contrato formal** | ❌ SIN CONTRATO |

**Estado:** ❌ SIN CONTRATO — Baja prioridad, referencia documental

---

## 5. FUENTES DE PERSISTENCIA

---

### FUENTE 10: SQLite Local (`data/db/registros_om.db`)

| Atributo | Valor |
|----------|-------|
| **Ruta** | `data/db/registros_om.db` |
| **Tipo** | SQLite — Persistencia local |
| **Tabla** | `registros_om` |
| **Producida por** | App Streamlit — inserciones manuales de OM |
| **Consumida por** | [core/db_manager.py](../core/db_manager.py), páginas Gestión OM |
| **Contrato formal** | ⚠️ Validación básica en `core/db_manager.py` |
| **Trazabilidad** | ✅ Cada registro con timestamp |
| **Backup automático** | ❌ NO EXISTE — Riesgo de pérdida de datos |

**Estado:** ⚠️ SIN BACKUP — Acción requerida: implementar backup automático

---

### FUENTE 11: PostgreSQL / Supabase (producción)

| Atributo | Valor |
|----------|-------|
| **Host** | Supabase (db.project_ref.supabase.co) |
| **Tabla** | `public.registros_om` |
| **Producida por** | App Streamlit Cloud |
| **Consumida por** | [core/db_manager.py](../core/db_manager.py) |
| **SSL** | ✅ `sslmode=require` |
| **Fallback IPv6** | ✅ Implementado para entornos sin salida AAAA |
| **Prioridad de conexión** | `DATABASE_URL → SUPABASE_POOLER_URL → SUPABASE_URL + password` |

**Estado:** ✅ BIEN CONFIGURADA

---

## 6. FUENTE HUÉRFANA DETECTADA

### FUENTE 12: Dataset Unificado (`data/raw/Dataset_Unificado.xlsx`)

| Atributo | Valor |
|----------|-------|
| **Ruta** | `data/raw/Dataset_Unificado.xlsx` |
| **Tipo** | Excel — Origen y uso sin documentar |
| **Consumida por** | ❓ DESCONOCIDO — No referenciada en `data_contracts.yaml` ni en `docs/core/03_Modelo_Datos.md` |
| **Contrato formal** | ❌ NINGUNO |
| **Riesgo** | Si alguien la usa como fuente → resultados no auditables |

**⚠️ ALERTA:** Confirmar si esta fuente está activa. Si no se usa → archivar o eliminar. Si se usa → documentar y añadir contrato.

---

## 7. FLUJO DE DATOS — TRAZABILIDAD COMPLETA

```
data/raw/Kawak/2022-2026.xlsx  ──┐
data/raw/API/2022-2026.xlsx    ──┤
                                  ▼
                       [scripts/consolidar_api.py]
                       Duración: ~10 segundos
                                  │
                    ┌─────────────┴────────────────┐
                    ▼                              ▼
  Indicadores Kawak.xlsx              Consolidado_API_Kawak.xlsx
  (catálogo histórico)                (resultados por período)
  data/raw/Fuentes Consolidadas/      data/raw/Fuentes Consolidadas/
                    │
                    ▼
    + Indicadores por CMI.xlsx
    + Subproceso-Proceso-Area.xlsx
    + config/settings.toml
                    │
                    ▼
      [scripts/actualizar_consolidado.py]
      Orquestador ETL v8 — 8 fases
      Duración: ~45-50 segundos
                    │
                    ▼
       Resultados Consolidados.xlsx (4 hojas)
       data/output/
       ├── Consolidado Semestral   ← FUENTE PRINCIPAL DASHBOARD
       ├── Consolidado Histórico   ← OM y análisis longitudinal
       ├── Consolidado Cierres     ← Proyectos / diciembre
       └── Catálogo Indicadores    ← Metadatos
                    │
                    ▼
       [services/data_loader.py] — 5 fases
       + JOIN Indicadores por CMI.xlsx
       + JOIN Subproceso-Proceso-Area.xlsx
                    │
                    ▼
          Dashboard Streamlit
          (streamlit_app/pages/)
```

---

## 8. DICCIONARIO DE CAMPOS — FLUJO NORMALIZADO

| Campo interno | Tipo | Descripción | Transformación aplicada |
|---------------|------|-------------|------------------------|
| `Id` | string | Identificador único del indicador | `_id_str()` elimina `.0` de floats |
| `Indicador` | string | Nombre del indicador | `_limpiar_html()` decodifica entidades |
| `Fecha` | date | Fecha de corte del registro | `pd.to_datetime()` |
| `Año` / `Anio` | integer | Año derivado | Extraído de `Fecha` |
| `Mes` | string | Mes en español | Mapa `MESES_ES` |
| `Período` / `Semestre` | string | Período `AAAA-S` | Derivado de `Fecha` |
| `Proceso` | string | Proceso padre | JOIN con `mapeos_procesos.yaml` |
| `Subproceso` | string | Subproceso | Mapeado desde `Indicadores por CMI.xlsx` |
| `Periodicidad` | categorical | Frecuencia de medición | Valores: `Mensual`, `Trimestral`, `Semestral`, `Anual`, `Bimestral` |
| `Sentido` | categorical | Dirección del indicador | Valores: `Positivo`, `Negativo` |
| `Meta` | float | Meta establecida | Puede ser `None` en casos especiales |
| `Ejecución` | float | Valor ejecutado | `None` cuando es "No Aplica" |
| `Cumplimiento` | float | Porcentaje normalizado | Rango: `[0.0, 1.3]` |
| `CumplReal` | float | Cumplimiento sin tope | Para análisis sin límite superior |
| `Categoría` | categorical | Semaforización | `Peligro`, `Alerta`, `Cumplimiento`, `Sobrecumplimiento`, `Sin dato` |
| `LLAVE` | string | Identificador único global | Formato `Id-AAAA-MM-DD` |
| `Tipo_Registro` | categorical | Marca especial | `Metrica`, `No Aplica` |
| `Fuente` | string | Origen del dato | `Kawak2025`, `API`, `Kawak_old` |
| `Clasificación` | categorical | Tipo de indicador | `Estratégico`, `Operativo` |
| `Línea` | string | Línea PDI | Desde `Indicadores por CMI.xlsx` |
| `Objetivo` | string | Objetivo PDI | Desde `Indicadores por CMI.xlsx` |

---

## 9. CONTRATOS DE DATOS — ESTADO

### Formalizados ✅

| Fuente | Sección en YAML | Validaciones |
|--------|----------------|--------------|
| `Resultados Consolidados.xlsx` | `resultados_consolidados` | 15+ reglas por hoja: tipo, rango, requerido, patrón |
| `Consolidado_API_Kawak.xlsx` | `kawak_consolidado` | Formato, rango, no-nulos |
| `Indicadores Kawak.xlsx` | `kawak_catalogo` | Deduplicación, validación ID |
| `Indicadores por CMI.xlsx` | `indicadores_cmi` | Campos clave (parcial) |
| `Subproceso-Proceso-Area.xlsx` | `mapeos_procesos.yaml` | Estructura YAML exportada |

### Sin formalizar ❌

| Fuente | Impacto | Prioridad |
|--------|---------|-----------|
| `Plan de accion/PA_*.xlsx` | MEDIO — datos manuales sin validar | **P1** |
| `OM.xlsx` | BAJO — referencia histórica | P2 |
| `acciones_mejora.xlsx` | BAJO | P3 |
| `Ficha_Tecnica_Indicadores.xlsx` | BAJO | P3 |
| `Dataset_Unificado.xlsx` | ⚠️ DESCONOCIDO | **Auditar primero** |

### Great Expectations
**Estado:** 🚫 **NO IMPLEMENTADO**  
Referenciado en `docs/core/01_Arquitectura.md` como mejora futura. Los contratos existen en YAML pero la validación es manual.

---

## 10. HALLAZGOS Y RECOMENDACIONES

### 🔴 CRÍTICOS

| ID | Problema | Evidencia | Impacto | Acción |
|----|----------|-----------|---------|--------|
| **C1** | Backup manual de Resultados Consolidados | `data/output/Resultados Consolidados.bak.xlsx` sin versionado | Pérdida total si se corrompe | Implementar backup automático con timestamp |
| **C2** | Planes de Acción sin contrato | `data/raw/Plan de accion/PA_1.xlsx`, `PA_2.xlsx` | Datos OM no auditables | Crear `data_contracts.yaml` → sección `plan_accion` |
| **C3** | Dataset Unificado huérfano | `data/raw/Dataset_Unificado.xlsx` — sin referencia en contratos ni docs | Uso no auditable, fuente de verdad desconocida | Auditar uso real; si no se usa → archivar |

### 🟡 ADVERTENCIAS

| ID | Problema | Evidencia | Impacto | Acción |
|----|----------|-----------|---------|--------|
| **W1** | Campo `Ind act` deprecado activo | `config/data_contracts.yaml:333` | Regla CMI ambigua | Actualizar docs + verificar código |
| **W2** | Sin audit trail de `mapeos_procesos.yaml` | `config/mapeos_procesos.yaml` — sin historial de quién cambió qué proceso | Cambios de jerarquía sin trazabilidad | Agregar comentario de fecha/responsable en cada cambio |
| **W3** | `Consolidado_API_Kawak_REV.xlsx` sin documentar | `data/raw/Fuentes Consolidadas/` — archivo REV sin explicación | Confusión sobre cuál es la versión oficial | Documentar o eliminar |
| **W4** | SQLite sin backup automático | `data/db/registros_om.db` | Pérdida de registros OM locales | Script de backup diario |

### 🔵 MENORES

| ID | Problema | Acción |
|----|----------|--------|
| **M1** | Formatos de fecha inconsistentes entre fuentes (API vs Excel) | Normalizar a ISO 8601 en ingesta |
| **M2** | Archivos en `data/raw/Auditoria/`, `Monitoreo/`, `Retos/` sin inventario | Documentar o archivar |

---

## 11. MATRIZ DE COMPLETITUD

```
╔════════════════════════════════════════════════════════════════════════╗
║ Fuente                      │ Existe │ Contrato │ Trazab. │ Backup   ║
╠════════════════════════════════════════════════════════════════════════╣
║ API Kawak (raw)             │   ✅   │    ✅    │    ✅   │   ⚠️ Man ║
║ Kawak catálogo (raw)        │   ✅   │    ✅    │    ✅   │   ⚠️ Man ║
║ Consolidado_API_Kawak.xlsx  │   ✅   │    ✅    │    ✅   │   ❌     ║
║ Resultados Consolidados     │   ✅   │    ✅    │    ✅   │   ⚠️ Man ║
║ Indicadores por CMI.xlsx    │   ✅   │    ⚠️    │    ✅   │   ❌     ║
║ Subproceso-Proceso-Area     │   ✅   │    ✅    │    ⚠️   │   ❌     ║
║ Plan de accion/PA_*.xlsx    │   ✅   │    ❌    │    ⚠️   │   ❌     ║
║ OM.xlsx                     │   ✅   │    ❌    │    ❌   │   ❌     ║
║ acciones_mejora.xlsx        │   ✅   │    ❌    │    ❌   │   ❌     ║
║ Ficha_Tecnica.xlsx          │   ✅   │    ❌    │    ❌   │   ❌     ║
║ Dataset_Unificado.xlsx      │   ✅   │    ❌    │    ❌   │   ❌     ║ ← HUÉRFANO
║ registros_om.db (SQLite)    │   ✅   │    ⚠️    │    ✅   │   ❌     ║
║ PostgreSQL / Supabase       │   ✅   │    ⚠️    │    ✅   │   ✅ Auto║
╚════════════════════════════════════════════════════════════════════════╝
```

---

## 12. ACCIONES PRIORIZADAS

| Prioridad | Acción | Esfuerzo | Responsable |
|-----------|--------|----------|-------------|
| **P0** | Auditar `Dataset_Unificado.xlsx` — ¿se usa? ¿quién lo produce? | 30 min | Analista de datos |
| **P0** | Backup automático con timestamp para `Resultados Consolidados.xlsx` | 1h | Desarrollador |
| **P1** | Crear contrato YAML para `Plan de accion/PA_*.xlsx` | 1h | Desarrollador |
| **P1** | Documentar `Consolidado_API_Kawak_REV.xlsx` o eliminarlo | 15 min | Analista |
| **P2** | Agregar audit trail en `mapeos_procesos.yaml` (fecha + autor de cada cambio) | 30 min | Calidad |
| **P2** | Script de backup diario para `registros_om.db` | 1h | Desarrollador |
| **P3** | Implementar Great Expectations para validación automática | 4h | Desarrollador |
| **P3** | Inventariar y documentar `data/raw/Auditoria/`, `Monitoreo/`, `Retos/` | 1h | Calidad |

---

*Informe generado por AGENT 1 — Data Source Audit / SGIND Software Intelligence Framework*  
*Archivos inspeccionados: `consolidar_api.py`, `actualizar_consolidado.py`, `config/data_contracts.yaml`, `core/config.py`, `docs/core/03_Modelo_Datos.md`, estructura de directorios real*
