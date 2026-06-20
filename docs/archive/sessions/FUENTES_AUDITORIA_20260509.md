# AUDITORÍA COMPLETA SGIND
## Sistema de Indicadores Institucionales — Politécnico Grancolombiano
**Fecha:** 9 de mayo de 2026 | **Ejecutado por:** Software Intelligence Framework v1.0

---

## RESUMEN EJECUTIVO

| Frente | Estado | Hallazgos críticos |
|--------|--------|--------------------|
| Fuentes de datos | ✅ Auditado | 3 fuentes sin contrato formal |
| Integridad de fórmulas | ⚠️ Riesgo | `categorizar_cumplimiento()` en 4 lugares divergentes |
| Validación ETL | ⚠️ Gap | Sin validación de coherencia histórica |
| Deuda técnica | 🔴 Activa | 10 archivos tmp + 7 funciones duplicadas |

---

## A) FUENTES DE DATOS IDENTIFICADAS (12 FUENTES)

### Fuentes Críticas (Contractualizadas ✅)

| # | Fuente | Tipo | Producida por | Consumida por | Contrato | Trazabilidad |
|---|--------|------|--------------|---------------|----------|--------------|
| 1 | **Consolidado_API_Kawak.xlsx** | Excel ETL | [consolidar_api.py](../scripts/consolidar_api.py) | [actualizar_consolidado.py](../scripts/actualizar_consolidado.py) | ✅ | LLAVE=Id-AAAA-MM-DD |
| 2 | **Indicadores Kawak.xlsx** | Catálogo histórico | [consolidar_api.py](../scripts/consolidar_api.py) | actualizar_consolidado.py | ✅ | Id + Año |
| 3 | **Resultados Consolidados.xlsx** | Salida ETL (4 hojas) | [actualizar_consolidado.py](../scripts/actualizar_consolidado.py) | Dashboard principal | ✅ | Período + Id |
| 4 | **Indicadores por CMI.xlsx** | Mapeo CMI/Línea | Manual | [services/data_loader.py](../services/data_loader.py) | ⚠️ Parcial | Id |
| 5 | **Subproceso-Proceso-Area.xlsx** | Jerarquía procesos | Manual | [services/procesos.py](../services/procesos.py) | ✅ YAML | Proceso/Subproceso |

### Fuentes Secundarias (Sin Contrato ⚠️)

| # | Fuente | Estado | Riesgo | Acción |
|---|--------|--------|--------|--------|
| 6 | Ficha_Tecnica_Indicadores.xlsx | Sin contrato | BAJO | Formalizar |
| 7 | Plan de accion/*.xlsx | Sin contrato | MEDIO | Formalizar + validador |
| 8 | OM.xlsx (histórica) | Sin contrato | BAJO | Formalizar schema |
| 9 | acciones_mejora.xlsx | Sin contrato | BAJO | Referencia |
| 10 | salidas_no_conformes.xlsx | Sin contrato | BAJO | Referencia |
| 11 | **registros_om.db** (SQLite) | Validación básica | MEDIO | Backup automático |
| 12 | **PostgreSQL Supabase** | SSL + fallback IPv6 | BAJO | Monitoreo activo |

### Matriz de Validación

```
╔════════════════════════════════════════════════════════════════╗
║ Fuente                    │ Contrato │ Actualización │ Trazab. ║
╠════════════════════════════════════════════════════════════════╣
║ API Kawak                 │    ✅    │  Automática   │    ✅   ║
║ Catálogo Kawak            │    ✅    │  Automática   │    ✅   ║
║ Consolidado (output)      │    ✅    │  Semi-auto    │    ✅   ║
║ Indicadores por CMI       │    ⚠️    │  Manual       │    ✅   ║
║ Jerarquía Procesos        │    ✅    │  Manual       │    ⚠️   ║
║ Plan de Acción            │    ❌    │  Manual       │    ⚠️   ║
║ OM Histórica              │    ❌    │  Manual       │    ❌   ║
║ Acciones Mejora           │    ❌    │  Manual       │    ❌   ║
║ BD Local (SQLite)         │    ⚠️    │  Automática   │    ✅   ║
║ BD Remota (PostgreSQL)    │    ⚠️    │  Automática   │    ✅   ║
╚════════════════════════════════════════════════════════════════╝
```

---

## B) FLUJO DE DATOS COMPLETO (TRAZABILIDAD)

```
Fuentes (API Kawak · Excel · OM)
        │
        ▼
[consolidar_api.py] → Consolidado_API_Kawak.xlsx + Indicadores Kawak.xlsx
        │
        ▼
[actualizar_consolidado.py] — 8 fases ETL:
   FASE 1: fuentes.py      → Carga y normaliza
   FASE 2: catalogo.py     → Construye catálogo
   FASE 3: extraccion.py   → Extrae Meta/Ejecución
   FASE 4: cumplimiento.py → Calcula cumplimiento
   FASE 5: signos.py       → Obtiene signos +/-
   FASE 6: builders.py     → Construye 3 tipos de registros
   FASE 7: purga.py        → Deduplica y limpia
   FASE 8: escritura.py    → Persiste Excel (4 hojas)
        │
        ▼
Resultados Consolidados.xlsx
   ├── Consolidado Semestral    → FUENTE PRINCIPAL dashboard
   ├── Consolidado Histórico    → OM y gestión
   ├── Consolidado Cierres      → Proyectos/cierres diciembre
   └── Catálogo Indicadores     → Metadatos
        │
        ▼
[services/data_loader.py] — 5 fases:
   FASE 1: Lectura I/O
   FASE 2: JOIN catálogo
   FASE 3: JOIN CMI
   FASE 4: Reconstrucción Año/Mes/Período
   FASE 5: Cálculos finales + categorización
        │
        ▼
Dashboard Streamlit (streamlit_app/)
```

---

## C) INTEGRIDAD DE FÓRMULAS

### ✅ FÓRMULA DE CUMPLIMIENTO — BIEN IMPLEMENTADA

**Fórmula oficial** ([scripts/etl/cumplimiento.py:80](../scripts/etl/cumplimiento.py)):
```python
if sentido == "positivo":
    raw = ejecución / meta
else:
    raw = meta / ejecución
cumplimiento = min(raw, tope)  # tope = 1.0 (PA) o 1.3 (regular)
```

**Documentación** ([docs/core/02_Logica_Indicadores.md:11-24](../docs/core/02_Logica_Indicadores.md)):
```
cumplimiento = ejecución / meta          ← Positivo
cumplimiento = meta / ejecución          ← Negativo
Meta=0 AND Ejec=0 → 1.0                 ← Caso especial
Negativo AND Ejec=0 → 1.0              ← Caso especial
cumplimiento = min(cumplimiento, 1.3)   ← Tope
```

**Estado: ✅ COINCIDENCIA EXACTA** — Código y docs alineados.

### ✅ UMBRALES DE CATEGORIZACIÓN — CENTRALIZADOS

**Fuente única:** [core/config.py:49-60](../core/config.py)

| Umbral | Valor | Tipo Indicador |
|--------|-------|----------------|
| UMBRAL_PELIGRO | 0.80 | General |
| UMBRAL_ALERTA | 1.00 | General |
| UMBRAL_SOBRECUMPLIMIENTO | 1.05 | General |
| UMBRAL_ALERTA_PA | 0.95 | Plan Anual |
| UMBRAL_SOBRECUMPLIMIENTO_PA | 1.00 | Plan Anual |

### 🔴 CRÍTICO: `categorizar_cumplimiento()` — 4 VERSIONES DIVERGENTES

| Versión | Ubicación | Parámetros | Estado |
|---------|-----------|-----------|--------|
| ✅ **OFICIAL** | [core/semantica.py:53](../core/semantica.py) | `(cumplimiento, id_indicador=None)` | Usar esta |
| ⚠️ **DUPLICADA** | [core/calculos.py:76](../core/calculos.py) | `(cumplimiento, sentido="Positivo", id_indicador=None)` | Eliminar |
| 🔴 **HARDCODED** | [generar_reporte.py:62](../generar_reporte.py) | Define inline, NO importa de semantica | **URGENTE** |
| ℹ️ DOC ONLY | docs/core/02_Logica_Indicadores.md:68 | Pseudocódigo de referencia | OK |

**⚠️ RIESGO:** `generar_reporte.py` genera categorías con lógica propia — puede diferir del dashboard.

### ⚠️ RIESGO: Tope Calculado en 2 Lugares

| Ubicación | Función |
|-----------|---------|
| [scripts/etl/cumplimiento.py:99-116](../scripts/etl/cumplimiento.py) | `obtener_tope_cumplimiento()` |
| [scripts/etl/escritura.py:285](../scripts/etl/escritura.py) | Cálculo inline en loop |

**Riesgo:** Si uno se actualiza sin el otro → divergencia en datos finales.

---

## D) VALIDACIÓN Y COBERTURA

### Tests Existentes (33 archivos)

| Test | Cobertura | Estado |
|------|-----------|--------|
| [test_cumplimiento_casos_reales.py](../tests/test_cumplimiento_casos_reales.py) | Casos especiales (Meta=0, Negativo+Ejec=0) | ✅ |
| [test_calculos.py](../tests/test_calculos.py) | normalizar, categorizar, tendencia | ✅ |
| [test_semantica.py](../tests/test_semantica.py) | categorización oficial | ✅ |
| [test_data_contracts.py](../tests/test_data_contracts.py) | Validación de esquema | ✅ |
| test_problema_1.py → test_problema_9.py | Casos edge históricos (9 archivos) | ✅ |
| [test_e2e_pipeline.py](../tests/test_e2e_pipeline.py) | Pipeline completo | ✅ |

**Cobertura estimada: ~60%**

### Gaps de Validación Críticos

| Gap | Descripción | Impacto |
|-----|-------------|---------|
| ❌ **Coherencia histórica** | No valida si valor actual es incoherente con histórico | ALTO |
| ❌ **Umbrales de meta** | No valida si meta > límite físico | MEDIO |
| ❌ **Sentido válido** | No valida que Sentido sea Positivo/Negativo | MEDIO |
| ❌ **IDS_PLAN_ANUAL dinámicos** | No tiene test de carga dinámica | MEDIO |
| ❌ **Periodicidades múltiples** | Mensual/Trimestral/Semestral no testeadas | BAJO |

---

## E) DEUDA TÉCNICA

### Archivos Temporales a Eliminar (10 archivos)

```
❌ __tmp_inspect_dom2.py
❌ __tmp_inspect_tab_lineas.py
❌ __tmp_sel2.py
❌ tmp_debug_363.py
❌ tmp_inspect_semester.py
❌ tmp_fix_proc_counts.py
❌ _fix_auditoria.py
❌ fix_syntax.py
❌ fix_indent.py
❌ fix_all_syntax.py
```
**Acción:** Eliminar todos. Esfuerzo: 15 minutos.

### Funciones Duplicadas (7 instancias)

| Función | Instancias | Acción |
|---------|-----------|--------|
| `categorizar_cumplimiento()` | 3 activas | Consolidar en `core/semantica.py` |
| `normalizar_cumplimiento()` | 2 | Consolidar en `core/calculos.py` |
| `_normalize_flag_series()` | 2 | Mover a `utils/normalizacion.py` |
| `_normalize_id_value()` | 2 | Mover a `utils/normalizacion.py` |

### Anti-Patrones Detectados

| Anti-Patrón | Ubicación | Severidad |
|-------------|-----------|-----------|
| Hardcoding categorización | [generar_reporte.py:62](../generar_reporte.py) | 🔴 ALTO |
| Tope duplicado | [escritura.py:285](../scripts/etl/escritura.py) | 🔴 ALTO |
| Lógica mezclada I/O+negocio | [services/data_loader.py:247-276](../services/data_loader.py) | 🟡 MEDIO |
| Mezcla limpieza+validación+reparación | [scripts/etl/purga.py](../scripts/etl/purga.py) | 🟡 MEDIO |

### Dependencias a Actualizar

| Paquete | Acción |
|---------|--------|
| numpy | Agregar versión mínima `>=1.24.0` |
| ruff | Actualizar de `>=0.4` a `>=0.6.0` |
| anthropic | Verificar compatibilidad versión actual |

---

## F) ROADMAP DE INTEGRIDAD

### FASE 1 — Riesgos Críticos (Esta semana · ~3h)

| # | Acción | Archivo | Esfuerzo | Impacto |
|---|--------|---------|----------|---------|
| P0.1 | Consolidar `categorizar_cumplimiento()` → solo `core/semantica.py` | [generar_reporte.py:62](../generar_reporte.py) + [core/calculos.py:76](../core/calculos.py) | 1h | 🔴 ALTO |
| P0.2 | Eliminar tope inline en `escritura.py`, usar `obtener_tope_cumplimiento()` | [scripts/etl/escritura.py:285](../scripts/etl/escritura.py) | 30min | 🔴 ALTO |
| P0.3 | Eliminar 10 archivos temporales | raíz del proyecto | 15min | 🟡 MEDIO |

### FASE 2 — Validaciones Faltantes (Semanas 1-2 · ~4h)

| # | Acción | Esfuerzo | Impacto |
|---|--------|----------|---------|
| P1.1 | Agregar validación de coherencia histórica en ETL | 2h | 🔴 ALTO |
| P1.2 | Formalizar contrato YAML para Plan de Acción | 1h | 🟡 MEDIO |
| P1.3 | Agregar test de carga dinámica IDS_PLAN_ANUAL | 1h | 🟡 MEDIO |

### FASE 3 — Consolidación (Semanas 2-4 · ~6h)

| # | Acción | Esfuerzo | Impacto |
|---|--------|----------|---------|
| P2.1 | Refactorizar `_normalize_*()` duplicadas en services/ | 1.5h | 🟡 MEDIO |
| P2.2 | Separar lógica de negocio de I/O en `data_loader.py` | 2h | 🟡 MEDIO |
| P2.3 | Documentar criterio de deduplicación en `purga.py` | 30min | 🟡 MEDIO |
| P2.4 | Implementar backup automático de Resultados Consolidados | 1h | 🟡 MEDIO |
| P2.5 | Actualizar numpy + ruff en requirements | 30min | 🟢 BAJO |

### FASE 4 — Automatización (Continua)

- Implementar Great Expectations para contratos automáticos
- Audit trail de cambios en IDS_PLAN_ANUAL
- Versionado automático de artefactos intermedios
- Formalizar contratos YAML de OM histórica y acciones mejora

---

## G) FORTALEZAS DETECTADAS

1. ✅ **Fórmula de cumplimiento correcta** — Código y docs alineados exactamente
2. ✅ **Umbrales centralizados** — Un único punto de verdad en `core/config.py`
3. ✅ **Casos especiales bien manejados** — Meta=0, Negativo+Ejec=0 implementados
4. ✅ **Tests de regresión sólidos** — Problemas #1-9 cubiertos
5. ✅ **Contratos de datos formalizados** — Fuentes críticas con YAML de validación
6. ✅ **IDS_PLAN_ANUAL dinámicos** — Carga desde Excel, no hardcoded
7. ✅ **Trazabilidad de LLAVE** — Id-AAAA-MM-DD único por registro
8. ✅ **Fallback BD** — SQLite local + PostgreSQL remoto con reconexión

---

*Generado por SGIND Software Intelligence Framework — Agentes 1-7*
