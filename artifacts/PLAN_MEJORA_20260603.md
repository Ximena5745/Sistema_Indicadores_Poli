# PLAN DE MEJORA — AGENT 1 Data Source Audit
**Fecha:** 2026-06-03  
**Basado en:** Auditoría ejecutada 2026-06-03 22:15:15

---

## Acciones priorizadas

| Prioridad | ID | Acción | Esfuerzo | Responsable |
|-----------|-----|--------|----------|-------------|
| **P0** | A1 | Re-ejecutar pipeline tras cambios en `API/2025.xlsx` y `Kawak/2026.xlsx` | 30 min | Analista ETL |
| **P0** | A2 | Investigar 1.756 registros con `resultado > 1.3` | 1h | Analista de datos |
| **P0** | A3 | Backup automático con timestamp para `Resultados Consolidados.xlsx` | 1h | Desarrollador |
| **P1** | A4 | Auditar `Dataset_Unificado.xlsx` — confirmar uso o archivar | 30 min | Analista |
| **P1** | A5 | Crear contrato YAML para `Plan de accion/PA_*.xlsx` | 1h | Desarrollador |
| **P1** | A6 | Ampliar `agent1_data_source_audit.py` a 12 fuentes reales | 2h | Desarrollador |
| **P1** | A7 | Corregir detección de campos huérfanos (lista vs contratos YAML) | 1h | Desarrollador |
| **P2** | A8 | Audit trail en `mapeos_procesos.yaml` | 30 min | Calidad |
| **P2** | A9 | Script backup diario `registros_om.db` | 1h | Desarrollador |
| **P2** | A10 | Formalizar contrato `lmi_reporte.xlsx` | 45 min | Desarrollador |
| **P3** | A11 | Implementar Great Expectations sobre contratos YAML | 4h | Desarrollador |
| **P3** | A12 | Inventariar `Monitoreo/`, `Retos/` (decisión S2-2026) | 1h | Calidad |

---

## Quick wins (esta semana)

1. Ejecutar: `python scripts/consolidar_api.py` y `python scripts/actualizar_consolidado.py`
2. Ejecutar Agent 1 mensualmente: `python scripts/agent1_data_source_audit.py` (usar `$env:PYTHONIOENCODING="utf-8"` en Windows)
3. Documentar en README la regla: solo `Consolidado_API_Kawak.xlsx` es fuente ETL válida (no `_REV`)

---

## Métricas objetivo post-mejoras

| Métrica | Actual | Objetivo |
|---------|--------|----------|
| Cobertura períodos | 89.3% | ≥ 95% |
| Registros `resultado > 1.3` | 1.756 | 0 |
| Fuentes con contrato YAML | ~60% | 100% críticas |
| Raw vs consolidado sincronizados | ⚠️ Desfase | ✅ Mismo día |

---

*Generado por AGENT 1 — Data Source Audit / SGIND*
