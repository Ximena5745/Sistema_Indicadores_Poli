# AGENT 1 — DATA SOURCE AUDIT
## Auditoría de Fuentes de Datos — SGIND
**Sistema:** Sistema de Indicadores Institucionales — Politécnico Grancolombiano  
**Fecha de auditoría:** 3 de junio de 2026  
**Agente:** Agent 1 / Data Source Audit  
**Framework:** Software Intelligence Platform — SGIND v1.0  
**Ejecución:** `python scripts/agent1_data_source_audit.py` (2026-06-03 22:15:15)

---

## Resumen ejecutivo

| Métrica | Valor | Estado |
|---------|-------|--------|
| Fuentes inventariadas (modelo ampliado) | 12 | Documentadas |
| Fuentes auditadas por script | 4 | API, Excel legacy, LMI, Supabase |
| Fuentes críticas para ETL | 3 | Kawak raw, API raw, Resultados Consolidados |
| Registros en Consolidado_API_Kawak | 12.703 | Accesible |
| Cobertura temporal API | 89.3% | 50/56 períodos mensuales |
| Hallazgo crítico | 1.756 registros `resultado > 1.3` | Requiere validación/capping |
| Cambios raw sin consolidar | 2 archivos | `API/2025.xlsx`, `Kawak/2026.xlsx` |

**Artefactos generados en esta ejecución:**
- `artifacts/AGENT1_DATA_SOURCE_AUDIT_20260603_221511.md` (reporte automático)
- `artifacts/AGENT1_FIELD_MAPPING_20260603_221511.json` (mapeo + gaps)
- `artifacts/GAPS_PERIODOS_20260603.csv`
- `artifacts/MAPEO_CAMPOS_20260603.csv`
- `artifacts/CONFLICTOS_FUENTES_20260603.md`
- `artifacts/PLAN_MEJORA_20260603.md`

---

## 1. Inventario de fuentes (12 identificadas)

### Clasificación por criticidad

| Nivel | Fuentes | Descripción |
|-------|---------|-------------|
| CRÍTICAS | 3 | Sin estas fuentes el ETL no funciona |
| IMPORTANTES | 2 | Enriquecen dashboard y CMI estratégico |
| SECUNDARIAS | 4 | Gestión OM, referencias históricas |
| PERSISTENCIA | 2 | Bases de datos operativas |
| HUÉRFANAS | 1 | Origen y uso no claros |

### Fuentes críticas

| # | Fuente | Ubicación | Consumida por | Contrato |
|---|--------|-----------|---------------|----------|
| 1 | Kawak anual | `data/raw/Kawak/*.xlsx` | `scripts/consolidar_api.py` | ✅ `data_contracts.yaml` |
| 2 | API anual | `data/raw/API/*.xlsx` | `scripts/consolidar_api.py` | ✅ `kawak_consolidado` |
| 3 | Resultados Consolidados | `data/output/Resultados Consolidados.xlsx` | Dashboard Streamlit | ✅ Completo |

**Salidas intermedias:**
- `data/raw/Fuentes Consolidadas/Indicadores Kawak.xlsx`
- `data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx`

**Cambios pendientes (git):** `data/raw/API/2025.xlsx` y `data/raw/Kawak/2026.xlsx` modificados localmente. Re-ejecutar pipeline: `consolidar_api.py` → `actualizar_consolidado.py`.

### Fuentes importantes

| Fuente | Ubicación | Uso | Contrato |
|--------|-----------|-----|----------|
| Indicadores por CMI | `data/raw/Indicadores por CMI.xlsx` | Umbral 95% vs 100%, PDI | ⚠️ Parcial |
| Jerarquía procesos | `data/raw/Subproceso-Proceso-Area.xlsx` | Mapeo proceso/subproceso | ✅ → `mapeos_procesos.yaml` |

### Fuentes secundarias

| Fuente | Ubicación | Contrato |
|--------|-----------|----------|
| Plan de acción | `data/raw/Plan de accion/PA_*.xlsx` | ❌ Sin contrato |
| OM histórica | `data/raw/OM.xlsx` | ❌ Sin contrato |
| Acciones mejora | `data/raw/acciones_mejora.xlsx` | ❌ Sin contrato |
| Ficha técnica | `data/raw/Ficha_Tecnica*.xlsx` | ❌ Referencia documental |
| Dataset Unificado | `data/raw/Dataset_Unificado.xlsx` | ⚠️ Huérfano |

### Persistencia

| Fuente | Ubicación | Uso | Backup |
|--------|-----------|-----|--------|
| SQLite local | `data/db/registros_om.db` | OM local | ❌ Manual |
| Supabase PostgreSQL | `public.registros_om` | OM remoto | ✅ Automático |

### Resultado script automatizado (4 fuentes modelo)

| Fuente | Status | Hallazgo |
|--------|--------|----------|
| API Kawak | ✅ accesible (26 cols, 12.703 filas) | 1.756 `resultado > 1.3` |
| Excel Local | ❌ sin datos | `data/raw/Excel_Entrada/` no existe (migrado) |
| LMI | ⚠️ sin lectura | Ruta real: `data/raw/lmi_reporte.xlsx` |
| Supabase | ⚠️ requiere `.env` | Solo OM, no consolidado principal |

---

## 2. Mapeo de campos → indicadores

### Campos core del pipeline

| Campo origen | Transformación ETL | Campo destino | Indicadores |
|--------------|-------------------|---------------|-------------|
| `Id` | `_id_str()` | `Id` | Todos |
| `fecha` | `pd.to_datetime()` | `Fecha` | Todos |
| `resultado` | Capping [0, 1.3] | `Ejecución` | Todos base |
| `meta` | Normalización | `Meta` | Con meta definida |
| — | `core/calculos.py` | `Cumplimiento` | Post-ETL |
| — | Semaforización | `Categoría` | Post-ETL |
| `analisis` | Detección "No Aplica" | `Tipo_Registro` | Casos especiales |
| `variables`, `series` | Desagregación | — | Indicadores compuestos |

### Campos en Consolidado_API_Kawak (18 detectados como "huérfanos" por script)

El script los marca por lista hardcodeada incompleta. Varios **sí se usan** en ETL:

| Campo | Filas | Uso real |
|-------|-------|----------|
| `meta`, `sentido`, `proceso`, `clasificacion` | 12.703 | Metadatos y joins |
| `cumplimiento`, `alerta`, `peligro`, `exceso` | ~2.350 | Precalculados en origen Kawak |
| `series`, `variables` | 738+ | Indicadores desagregados |
| `año_archivo`, `fecha_corte` | 12.703 | Trazabilidad de ingesta |

Ver detalle en `artifacts/MAPEO_CAMPOS_20260603.csv`.

---

## 3. Trazabilidad fuente → dashboard

```
data/raw/Kawak/2022-2026.xlsx  ──┐
data/raw/API/2022-2026.xlsx    ──┤
                                  ▼
                       scripts/consolidar_api.py
                                  │
                    ┌─────────────┴────────────────┐
                    ▼                              ▼
  Indicadores Kawak.xlsx              Consolidado_API_Kawak.xlsx
                    │
    + lmi_reporte.xlsx (IDs Métrica)
    + Indicadores por CMI.xlsx
    + Subproceso-Proceso-Area.xlsx
    + config/settings.toml
                    ▼
      scripts/actualizar_consolidado.py
                    ▼
       Resultados Consolidados.xlsx (4 hojas)
                    ▼
       services/data_loader.py → Streamlit
```

**Integridad:** Trazabilidad por `Id` + `Fecha` + `LLAVE` (`Id-AAAA-MM-DD`).

---

## 4. Completitud de períodos

| Métrica | Valor |
|---------|-------|
| Períodos esperados (2022–2026 mensual) | 56 |
| Períodos encontrados | 50 |
| Cobertura | **89.3%** |

**Gaps por indicador (muestra):**

| Indicador | Datos | Faltantes |
|-----------|-------|-----------|
| 68 | 8 | 4 |
| 73 | 8 | 4 |
| 74 | 8 | 4 |

Ver `artifacts/GAPS_PERIODOS_20260603.csv`.

---

## 5. Consistencia entre fuentes

| Escenario | Status | Evidencia |
|-----------|--------|-----------|
| API vs Resultados Consolidados | ⚠️ Pendiente re-sync | Raw API/Kawak modificados |
| `Consolidado_API_Kawak_REV.xlsx` | ⚠️ Documentado | Solo referencia; no usar en ETL |
| Excel legacy vs API | ✅ Migrado | `Excel_Entrada/` no existe |
| LMI vs catálogo Kawak | ⚠️ Parcial | LMI filtra IDs tipo "Métrica" |
| `resultado > 1.3` | 🔴 1.756 registros | Posible escala % vs decimal |

Ver `artifacts/CONFLICTOS_FUENTES_20260603.md`.

---

## 6. Matriz de cobertura

```
Fuente                      │ Existe │ Contrato │ Trazab. │ Backup
────────────────────────────┼────────┼──────────┼─────────┼────────
Kawak raw (2022-2026)       │   ✅   │    ✅    │    ✅   │   ⚠️ Man
API raw (2022-2026)         │   ✅*  │    ✅    │    ✅   │   ⚠️ Man
Consolidado_API_Kawak.xlsx  │   ✅   │    ✅    │    ✅   │   ❌
Resultados Consolidados     │   ✅   │    ✅    │    ✅   │   ⚠️ Man
Indicadores por CMI         │   ✅   │    ⚠️    │    ✅   │   ❌
lmi_reporte.xlsx            │   ⚠️   │    ❌    │    ⚠️   │   ❌
Plan de accion/PA_*.xlsx    │   ✅   │    ❌    │    ⚠️   │   ❌
Dataset_Unificado.xlsx      │   ⚠️   │    ❌    │    ❌   │   ❌
registros_om.db (SQLite)    │   ✅   │    ⚠️    │    ✅   │   ❌
PostgreSQL / Supabase       │   ✅   │    ⚠️    │    ✅   │   ✅ Auto
```
* API/2025 y Kawak/2026 con cambios locales pendientes de consolidar

---

## 7. Criterios de éxito

| Criterio | Cumple |
|----------|--------|
| Inventario completo de fuentes | ✅ |
| Mapeo campos core | ✅ |
| Trazabilidad documentada | ✅ |
| Gaps de período documentados | ✅ |
| Conflictos identificados | ✅ |
| Plan de mejora accionable | ✅ (`PLAN_MEJORA_20260603.md`) |

---

*Informe generado por AGENT 1 — Data Source Audit / SGIND Software Intelligence Framework*  
*Inspeccionado: `consolidar_api.py`, `actualizar_consolidado.py`, `config/data_contracts.yaml`, `Consolidado_API_Kawak.xlsx`*
