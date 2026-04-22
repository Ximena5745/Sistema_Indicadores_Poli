# 06 - TESTING Y CALIDAD

**Documento:** 06_Testing_Calidad.md  
**Versión:** 1.0  
**Fecha:** 22 de abril de 2026  
**Status:** ✅ Consolidado MDV

---

## 1. Estado Actual

| Métrica | Valor | Estado |
|---------|-------|--------|
| **Tests Totales** | 149 | ✅ |
| **Tests Pasando** | 149 | ✅ 100% |
| **Coverage** | 41% | 🟡 |
| **Fase** | FASE 3 COMPLETA | ✅ |

---

## 2. Suites de Tests

### 2.1 test_e2e_pipeline.py (19 tests)

**Propósito:** Validar pipeline ETL end-to-end

**Área:** `services/data_loader.py`

**Tests:**
- `test_cargar_dataset_retorna_dataframe`
- `test_cargar_dataset_columnas_requeridas`
- `test_cargar_dataset_tiene_registros`
- `test_cargar_dataset_historico`
- `test_cargar_dataset_historico_columnas`
- `test_resumen_om_por_id`
- `test_calcular_cumplimiento`
- `test_normalizar_nombres`
- Y otros 11 tests adicionales

**Fixtures:**
- `plan_anual_id` - ID de indicador Plan Anual
- `regular_indicator_id` - ID de indicador regular

### 2.2 test_pages_resumen_por_proceso.py (19 tests)

**Propósito:** Validar página Resumen por Proceso

**Área:** `streamlit_app/pages/resumen_por_proceso.py`

**Tests:**
- `test_resumen_por_procesoPage`
- `test_procesar_dataframe_resumen`
- `test_filtrar_por_proceso`
- `test_calcular_totales`
- `test_tiene_porcentaje True/False`
- Y otros 14 tests adicionales

### 2.3 test_pages_gestion_om.py (21 tests)

**Propósito:** Validar página Gestión OM

**Área:** `streamlit_app/pages/gestion_om.py`

**Tests:**
- `test_gestionOMPage`
- `test_color_alerta`
- `test_color_peligro`
- `test_icono_alerta`
- `test_icono_peligro`
- `test_nombre_om_default`
- Y otros 15 tests adicionales

---

## 3. Ejecución de Tests

### 3.1 Comando Principal

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Con coverage
pytest tests/ --cov=. --cov-report=html

# Solo una suite
pytest tests/test_e2e_pipeline.py -v
```

### 3.2 CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest --cov=. --cov-report=xml --cov-report=term
      - uses: codecov/codecov-action@v3
```

---

## 4. Validación de Robustez

### 4.1 Áreas Críticas Testeadas

| Área | Descripción | Prioridad |
|------|-------------|-----------|
| Enum comparisons | Comparaciones enum vs strings | 🔴 Alta |
| Normalización | Casos con/sin porcentaje | 🔴 Alta |
| Color/Icon functions | Funciones que esperaban enums | 🔴 Alta |
| Data loading | Carga de datasets | 🟡 Media |
| Edge cases | Indicadores sin datos | 🟡 Media |

### 4.2 Patterns de Test

```python
# CORRECTO: Comparar con .value
assert cat == CategoriaCumplimiento.PELIGRO.value

# CORRECTO: Parámetros explícitos
df = preparar_dataframe(tiene_porcentaje=True)

# CORRECTO: Funciones con strings
color = color_alerta("Alerta")  # No pasar enums
```

---

## 5. Coverage Goals

| Threshold | Color | Descripción |
|-----------|-------|-------------|
| ≥ 80% | 🟢 Verde | Meta para producción |
| 60-79% | 🟡 Naranja | Aceptable, mejorable |
| < 60% | 🔴 Rojo | Requiere atención |

**Estado actual:** 41% → Necesita incremento

### 5.1 Plan de Mejora

1. **Corto plazo (S3-4):** Agregar tests para `core/semantica.py`
2. **Medio plazo (S5-6):** Coverage para `services/data_loader.py`
3. **Largo plazo (S7-8):** Tests de integración completos

---

## 6. Data Validation

### 6.1 Contratos de Datos

```yaml
# config/data_contracts.yaml
fuentes:
  resultados_consolidados:
    hoja: Consolidado Semestral
    columnas_requeridas:
      - Id
      - Fecha
      - Meta
      - Ejecución
      - Cumplimiento
    tipos:
      Id: string
      Meta: float
      Ejecución: float
      Cumplimiento: float
```

### 6.2 Validaciones Automáticas

- **Null checks:** Campos requeridos no nulos
- **Type checks:** Tipos de datos correctos
- **Range checks:** Valores dentro de rangos válidos
- **Uniqueness:** Llaves únicas

---

## 7. Referencias

- **Tests folder:** [`tests/`](../../tests/)
- **Fixtures:** [`tests/conftest.py`](../../tests/conftest.py)
- **Data contracts:** [`config/data_contracts.yaml`](../../config/data_contracts.yaml)
- **Validación robustness:** [`VALIDACION_TEST_ROBUSTNESS.md`](../../06-FASE3/VALIDACION_TEST_ROBUSTNESS.md)
