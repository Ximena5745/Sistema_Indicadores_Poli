# Archived Exploratory Tests

**Status:** 🗂️ ARCHIVED  
**Date:** 21 de abril de 2026  
**Reason:** Exploratory/POC code moved out of main test suite

## Contents

| Test | Purpose | Status | Notes |
|------|---------|--------|-------|
| `test_consol.py` | Consolidation exploratory | ⏸️ Replaced | Logic now in test_semantica.py |
| `test_filter.py` | Filter logic POC | ⏸️ Replaced | Logic in core modules |
| `test_sunburst.py` | Sunburst chart testing | ⏸️ Replaced | Visual testing moved to E2E suite |

## Why Archived?

These tests were used during **Fase 1-4 Discovery** to explore and validate approaches. Now that the codebase has matured:

- ✅ Core logic consolidated into `core/semantica.py`
- ✅ Official test suites created (test_semantica.py, test_pages_*.py, etc.)
- ✅ No pytest assertions in exploratory tests (not executed by CI)
- ✅ Safe to archive without losing functionality

## To Re-activate

If needed for historical reference or re-implementation:

1. Copy files back to `tests/`
2. Update imports to match current module structure
3. Add to pytest configuration
4. Ensure CI/CD includes them

## Current Test Suites (Active)

See `../` for active test suite:
- `test_semantica.py` - Core categorization logic (28 tests)
- `test_calculos.py` - Calculations validation
- `test_pages_resumen_general.py` - UI integration (15 tests)
- `test_pages_resumen_por_proceso.py` - UI integration (10 tests)
- `test_pages_gestion_om.py` - UI integration (8 tests)
- `test_strategic_indicators.py` - Strategic indicators
- `test_problema_*.py` - Problem tracking suites
- `test_e2e_*.py` - End-to-end pipeline tests (TBD)
