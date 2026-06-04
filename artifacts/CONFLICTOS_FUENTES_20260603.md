# CONFLICTOS ENTRE FUENTES — AGENT 1
**Fecha:** 2026-06-03  
**Fuente de datos:** `Consolidado_API_Kawak.xlsx` + estado git del repositorio

---

## Matriz de validación

| ID | Escenario | Fuente A | Fuente B | Status | Detalle |
|----|-----------|----------|----------|--------|---------|
| CONF-01 | Raw sin consolidar | `API/2025.xlsx` | `Consolidado_API_Kawak.xlsx` | ⚠️ DESFASE | Git: modificado localmente, no re-procesado |
| CONF-02 | Raw sin consolidar | `Kawak/2026.xlsx` | `Consolidado_API_Kawak.xlsx` | ⚠️ DESFASE | Git: modificado localmente, no re-procesado |
| CONF-03 | Rango resultado | API Kawak | Contrato [0, 1.3] | 🔴 CONFLICTO | 1.756 registros con `resultado > 1.3` |
| CONF-04 | Versión REV | `Consolidado_API_Kawak.xlsx` | `Consolidado_API_Kawak_REV.xlsx` | ⚠️ AMBIGÜEDAD | REV es solo auditoría; no usar en ETL |
| CONF-05 | Excel legacy | `Excel_Entrada/` | API Kawak | ✅ RESUELTO | Directorio legacy no existe; migración completa |
| CONF-06 | LMI ausente | `lmi_reporte.xlsx` | ETL | ⚠️ GAP | Script Agent 1 no lee LMI; ETL usa set vacío si falta |

---

## CONF-03 — Detalle: resultados fuera de rango

| Atributo | Valor |
|----------|-------|
| Archivo | `data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx` |
| Registros afectados | 1.756 |
| Regla esperada | `resultado ∈ [0, 1.3]` |
| Hipótesis | Valores en escala 0–100 (85 en lugar de 0.85) o indicadores sin capping |
| Impacto | Cumplimiento y semáforos incorrectos en dashboard |
| Acción | Validar escala en origen; aplicar normalización/capping en `consolidar_api.py` |

---

## Recomendaciones de reconciliación

1. **Inmediato:** Ejecutar pipeline completo tras cambios en raw (`consolidar_api` → `actualizar_consolidado`).
2. **Corto plazo:** Investigar muestra de los 1.756 registros > 1.3 por `Id` y `fecha`.
3. **Mediano plazo:** Cruzar API vs Resultados Consolidados post-ETL con script de validación automatizada.

---

*Generado por AGENT 1 — Data Source Audit*
