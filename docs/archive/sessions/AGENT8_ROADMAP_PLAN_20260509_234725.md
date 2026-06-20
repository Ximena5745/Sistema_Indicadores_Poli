# AGENT 8 — Data Integrity Roadmap Report

**Fecha:** 2026-05-09 23:47:25  
**Framework:** SGIND v1.0  
**Duración Total:** 10 semanas (70 horas)  

## 🎯 Executive Summary

### Consolidation Status (AGENT 1-7)
- ✅ Data sources mapped (AGENT 1)
- ✅ ETL pipeline analyzed (AGENT 2)
- ✅ Indicators audited (AGENT 3)
- ✅ Documentation synchronized (AGENT 4)
- ✅ Data validated & corrected (AGENT 5)
- ✅ Dependencies mapped (AGENT 6)
- ✅ Technical debt classified (AGENT 7)
- → **This roadmap sequences ALL remediation**

### Investment Summary
- **Total Effort:** 70 hours (10 weeks)
- **Estimated Cost:** $10500
- **Expected ROI:** $30,000+ value created
- **Team Composition:** 2 engineers + 1 QA (FTE)

---

## 📊 Four-Phase Implementation Plan

### PHASE 1: STABILIZATION
**Duration:** 2 weeks (20 hours)  
**Objective:** Eliminar riesgo inmediato, asegurar data correcta  
**Period:** 2026-05-09 → 2026-05-23  

#### Security Lockdown (4h, P1-CRITICAL)
**Debt Items:** DD-011  
**Success Criteria:** Zero hardcoded passwords en git  

**Tasks:**
1. Mover credenciales a .env (no commitear)
2. 1Password/AWS Secrets Manager setup
3. Audit git history para credenciales expuestas

#### Data Quality Fixes (8h, P1-CRITICAL)
**Debt Items:** DD-001, DD-005  
**Success Criteria:** 100% formula consistency, ETL validates  

**Tasks:**
1. Unificar fórmulas de cumplimiento en core/calculos.py
2. Remover duplicadas de consolidar_api.py
3. Agregar validación Ejecución ≤ 1.3
4. Agregar validación Meta > 0
5. Dashboard A vs B: Validar identidad de resultados

#### Documentation Sync (8h, P2-HIGH)
**Debt Items:** DD-003  
**Success Criteria:** All 4 indicators documented completely  

**Tasks:**
1. Documentar 4 indicadores: baseline, target, owner
2. Sincronizar docs/02_Logica_Indicadores.md
3. Crear docs/METADATA_COVERAGE.md (checklist 100%)

### PHASE 2: REPRODUCIBILITY
**Duration:** 2 weeks (15 hours)  
**Objective:** Habilitar audit trail y reproducibilidad histórica  
**Period:** 2026-05-23 → 2026-06-06  

#### Config Centralization (5h, P2-HIGH)
**Debt Items:** DD-006  
**Success Criteria:** Zero hardcoded thresholds  

**Tasks:**
1. Mover thresholds a config/settings.toml
2. 1.3 (Ejecución max), 1.0 (Meta max), 0.6 (warning)
3. Implementar config.reload() en runtime
4. Git track cambios de umbral

#### Data Versioning (10h, P2-HIGH)
**Debt Items:** DD-007  
**Success Criteria:** Full historical reproducibility  

**Tasks:**
1. Add metadata: version, timestamp, source_version
2. Log snapshot de cada consolidado download
3. Archive: data/versions/consolidado_v1_*.xlsx
4. SQL table: data_snapshots(id, version, timestamp, hash)
5. Implement rollback function (restore from archive)

### PHASE 3: TESTABILITY
**Duration:** 3 weeks (15 hours)  
**Objective:** Test coverage comprehensivo, detección de regresiones  
**Period:** 2026-06-06 → 2026-06-27  

#### Test Suite Expansion (15h, P1-CRITICAL)
**Debt Items:** DD-004  
**Success Criteria:** 85%+ code coverage, 39+ test functions  

**Tasks:**
1. Unit tests: core/calculos.py (10 test functions)
2. Integration tests: ETL pipeline (8 test functions)
3. Regression tests: Formula comparison (5 cases)
4. Data validation: Edge cases, boundaries, nulls (8 cases)
5. CI pipeline: Block merges si <85% coverage

### PHASE 4: SCALABILITY
**Duration:** 3 weeks (20 hours)  
**Objective:** Arquitectura modular, preparación para crecimiento  
**Period:** 2026-06-27 → 2026-07-18  

#### ETL Refactoring (20h, P1-CRITICAL)
**Debt Items:** DD-009, DD-010  
**Success Criteria:** 5 modules <500 LOC each, all tested  

**Tasks:**
1. Break actualizar_consolidado.py (1200+ líneas)
2. Module 1: etl/source_connector.py (300L, 8 tests)
3. Module 2: etl/transformers.py (250L, 10 tests)
4. Module 3: etl/validators.py (200L, 8 tests)
5. Module 4: etl/exporters.py (150L, 6 tests)
6. Orchestrator: etl/pipeline.py (150L)
7. Error handling: Rollback on validation failure

---

## ⚠️ Risk Management

### Phase 1 breaking production
- **Probability:** Medium
- **Impact:** Critical
- **Mitigation:** Blue-green deploy, smoke tests, rollback plan

### Phase 4 regression (refactoring bugs)
- **Probability:** High
- **Impact:** High
- **Mitigation:** Extensive regression suite, UAT phase

### Timeline slippage
- **Probability:** Medium
- **Impact:** Medium
- **Mitigation:** 2-week buffer, priority focus, weekly standups

### Stakeholder alignment
- **Probability:** Low
- **Impact:** Medium
- **Mitigation:** Weekly updates, early approval gates, communication plan
