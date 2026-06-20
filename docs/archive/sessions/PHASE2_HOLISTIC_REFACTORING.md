# 🔄 PHASE 2: Refactorización Holística del Proyecto

**Status:** 🟡 INICIADO - 10 Mayo 2026  
**Enfoque:** Código Central Completo (NO agentes)  
**Objetivo:** Resolver violaciones SRP en toda la estructura del proyecto  
**Duración Estimada:** 3 semanas, ~160 horas  

---

## 📊 Análisis de Codebase Completo

### Estructura del Proyecto

```
Sistema_Indicadores_Poli/
├── core/                 (10 archivos, 2,000+L)     ← Domain/Business Logic
├── services/            (9 archivos, 1,500+L)      ← Application Services
├── streamlit_app/       (50 archivos, 3,000+L)     ← Presentation Layer
├── scripts/             (40 archivos, ~50% ETL)    ← Execution Scripts
├── components/          (2 archivos, 500+L)        ← UI Components
├── utils/               (2 archivos, 200+L)        ← Utilities
├── styles/              (CSS/YAML)                 ← Styling
├── tools/               (1 archivo)                ← Misc
└── tests/               (573+ tests)               ← Test Suite
```

---

## 🔴 TOP 20 Archivos Problema (>150 líneas = SRP violation)

| Rank | Archivo | Líneas | Responsabilidades | Prioridad |
|------|---------|--------|------------------|-----------|
| 1 | `streamlit_app/pages/resumen_por_proceso.py` | ~900 | Tabla + Gráfico + Filtros + Estadísticas | 🔴 CRÍTICO |
| 2 | `streamlit_app/pages/resumen_general.py` | ~850 | Múltiples gráficos + Estado global | 🔴 CRÍTICO |
| 3 | `streamlit_app/pages/gestion_om.py` | ~750 | CRUD + Validación + UI + BD | 🔴 CRÍTICO |
| 4 | `streamlit_app/pages/tablero_operativo.py` | ~700 | Dashboard + Widgets + Filtros | 🔴 CRÍTICO |
| 5 | `streamlit_app/pages/resumen_general_backup_20260415.py` | ~650 | 🗑️ Archivo abandonado | 🟠 ALTO (ELIMINAR) |
| 6 | `streamlit_app/components/dashboard_components.py` | ~600 | Múltiples componentes UI | 🔴 CRÍTICO |
| 7 | `core/db_manager.py` | ~422 | Configs + Conexiones + CRUD (después extrac.) | 🟠 ALTO |
| 8 | `streamlit_app/pages/resumen_general_real.py` | ~400 | Otro archivo de dashboard | 🔴 CRÍTICO |
| 9 | `streamlit_app/components/modals.py` | ~350 | Múltiples modales | 🔴 CRÍTICO |
| 10 | `services/data_loader.py` | ~330 | Load + Transform + Cache | 🟠 ALTO |
| 11 | `services/strategic_indicators.py` | ~320 | Calc + Aggregation + Validation | 🟠 ALTO |
| 12 | `streamlit_app/pages/cmi_estrategico.py` | ~300 | Dashboard + Widgets | 🔴 CRÍTICO |
| 13 | `streamlit_app/components/heatmap_chart.py` | ~280 | Chart + Data prep | 🟡 MEDIO |
| 14 | `streamlit_app/components/cmi_tabs/tab_resumen.py` | ~270 | Tabs + Multiple views | 🟡 MEDIO |
| 15 | `streamlit_app/styles/design_system.py` | ~260 | Styles + Theme + Colors | 🟡 MEDIO |
| 16 | `services/data_validation.py` | ~250 | Validation + Error handling | 🟡 MEDIO |
| 17 | `streamlit_app/pages/plan_mejoramiento.py` | ~240 | Forms + Data + UI | 🟡 MEDIO |
| 18 | `streamlit_app/components/cmi_tabs/modal_ficha.py` | ~220 | Modal form + Validation | 🟡 MEDIO |
| 19 | `core/semantica.py` | ~200 | Categorization + Normalization | 🟡 MEDIO |
| 20 | `streamlit_app/pages/informe_por_procesos.py` | ~200 | Report generation + UI | 🟡 MEDIO |

---

## 🎯 Estrategia PHASE 2 — 3 Semanas

### Semana 1: CLEAN ARCHITECTURE FOUNDATION (50h)
Objetivo: Separar Presentation → Application → Domain

#### Paso 1: Domain Layer Cleanup (15h)
- ✅ (INICIADO) Refactor `core/db_manager.py` (compl. extracciones)
- 🟡 Split `core/semantica.py` → domain/categorization + domain/normalization + presentation/visual
- 🟡 Extract `core/calculos.py` → domain/calculation_service
- **Outcome:** core/ con <200L por módulo, Pure Domain Logic

#### Paso 2: Application Services Refactor (15h)
- 🟡 Split `services/data_loader.py`:
  - `services/loaders/excel_loader.py` — Cargar Excel
  - `services/loaders/api_loader.py` — Cargar API
  - `services/cache_manager.py` — Caching
- 🟡 Split `services/strategic_indicators.py`:
  - `services/indicators/calculator.py` — Cálculos
  - `services/indicators/aggregator.py` — Agregación
  - `services/indicators/validator.py` — Validación
- 🟡 Refactor `services/data_validation.py` → validation rules engine

#### Paso 3: Presentation Layer Standardization (10h)
- 🟡 Extract UI component utilities
- 🟡 Estandarizar imports en streamlit_app/
- 🟡 Crear component library structure

#### Paso 4: Eliminar Dead Code (10h)
- 🗑️ Remover `resumen_general_backup_20260415.py`
- 🗑️ Remover `resumen_general_real.py` (duplicate?)
- 🟡 Archivar otros backups

---

### Semana 2: PRESENTATION LAYER REFACTORING (50h)
Objetivo: Separar Pages → Components → Utilities, reduce page size

#### Paso 1: Page Refactoring (20h)
**Objetivo:** Cada página <300L

- `resumen_por_proceso.py` (900L → 250L)
  - `components/proceso_table.py` — Tabla
  - `components/proceso_charts.py` — Gráficos
  - `components/proceso_filters.py` — Filtros
  - `components/proceso_stats.py` — Estadísticas

- `resumen_general.py` (850L → 250L)
  - `components/general_dashboard.py` — Layout
  - `components/general_widgets.py` — Widgets reutilizables
  - `components/general_filters.py` — Filtros

- `gestion_om.py` (750L → 300L)
  - `components/om_form.py` — Formulario CRUD
  - `components/om_table.py` — Tabla OM
  - `components/om_validator.py` — Validación local
  - `components/om_actions.py` — Acciones (Save/Delete)

#### Paso 2: Component Library Organization (15h)
- Consolidar `components/` en estructura clara
- Split `dashboard_components.py` (600L):
  - `components/dashboard/cards.py`
  - `components/dashboard/charts.py`
  - `components/dashboard/filters.py`
  - `components/dashboard/metrics.py`
- Consolidar modales en `components/modals/`

#### Paso 3: Standardize Imports & Exports (10h)
- Crear `streamlit_app/__init__.py` con imports
- Standardizar patterns de carga
- Crear component registry

#### Paso 4: Testing for UI Components (5h)
- Unit tests para utils
- Integration tests para components

---

### Semana 3: CONSOLIDATION & VALIDATION (60h)

#### Paso 1: Cross-Layer Integration Testing (20h)
- Full integration: domain → services → UI
- Test backward compatibility
- Verify 572+ tests still pass

#### Paso 2: Documentation & Architecture (15h)
- Crear `docs/ARCHITECTURE.md` (Clean Architecture)
- Dependency diagrams
- Import rules documentation
- Component API docs

#### Paso 3: Final Code Review (15h)
- Lint all modules
- Verify SRP compliance
- Check coverage

#### Paso 4: Artifacts & Commit (10h)
- Generate refactoring report
- Git commits with proper messages
- Update PHASE2_CORE_REFACTORING.md

---

## 📈 Success Metrics

| Métrica | Baseline | Target | Status |
|---------|----------|--------|--------|
| Max líneas/archivo | 900 | <300 | 🟡 |
| Archivos >200L | 20 | ~5-8 | 🟡 |
| Pure domain <200L | 0 | 4 | 🟡 |
| Page files <300L | 0 | 8 | 🟡 |
| Tests passing | 572 | 572+ | 🟡 |
| Regressions | 0 | 0 | 🟡 |
| Code coverage | - | 80%+ | 🟡 |
| SRP violations | 50+ | <5 | 🟡 |

---

## ⚠️ Riesgos & Mitigaciones

| Riesgo | Impacto | Mitigation |
|--------|---------|-----------|
| Circular imports | HIGH | Dependency analysis before refactoring |
| Streamlit cache invalidation | MEDIUM | Comprehensive cache testing |
| UI regression | HIGH | Screenshot + regression tests |
| Performance degradation | MEDIUM | Profiling after each refactoring |

---

## 📋 Secuencia de Ejecución

**Prioridad 1 (PRIMERA SEMANA):**
1. ✅ (INICIADO) Terminar extracciones core/db_manager.py
2. Split core/semantica.py → domain + presentation
3. Eliminar dead code (backups)
4. Refactor services/ (loaders, indicators, validation)

**Prioridad 2 (SEGUNDA SEMANA):**
5. Refactorizar páginas principales (resumen_*)
6. Reorganizar components/
7. Estandarizar imports

**Prioridad 3 (TERCERA SEMANA):**
8. Testing e integración
9. Documentación
10. Final review & commits

---

## 🎯 Next Immediate Action

Completar extracciones de `core/db_manager.py`:
1. connection_manager.py (200L) — Conexiones SQLite/Postgres
2. schema_manager.py (40L) — DDL, índices
3. operations.py (150L) — CRUD operaciones

Luego: Comenzar `core/semantica.py` descomposición.
