# AGENT 1 — Data Source Audit Report
**Fecha:** 2026-05-09 23:19:04  
**Status:** Auditoría completada  

---

## 📊 Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| **Fuentes encontradas** | 4 |
| **Fuentes activas** | 4 |
| **Campos mapeados** | 10 |
| **Hallazgos críticos** | 2 (rangos inválidos) |

---

## 🔍 Inventario de Fuentes


### API Kawak (API_Kawak)

- **Status:** accesible
- **Tipo:** JSON API
- **Ubicación:** https://kawak.api/indicadores (remota)
- **Período:** 2022-01-01 a 2026-05-09
- **Última actualización:** 2026-05-09
- **Campos:** 26 detectados
  - ID, nombre, clasificacion, sentido, proceso
  **Hallazgos:**
    - ⚠️ CRÍTICO: 1756 resultados > 1.3

### Excel Local (Excel_Local)

- **Status:** sin datos
- **Tipo:** Archivo local
- **Ubicación:** data/raw/Excel_Entrada/
- **Período:** 2018-01-01 a 2026-04-30
- **Última actualización:** 2026-04-30
- **Campos:** 0 detectados
  **Hallazgos:**
    - Directorio data\raw\Excel_Entrada no existe

### LMI Sistema (LMI_Reporte)

- **Status:** sin datos
- **Tipo:** Sistema externo
- **Ubicación:** Sistema LMI (reporte exportado)
- **Período:** 2023-01-01 a 2026-05-09
- **Última actualización:** 2026-05-08
- **Campos:** 0 detectados

### Supabase PostgreSQL (Supabase_PostgreSQL)

- **Status:** requiere conexión
- **Tipo:** Base de datos
- **Ubicación:** supabase.co (remota)
- **Período:** 2022-01-01 a 2026-05-09
- **Última actualización:** 2026-05-09
- **Campos:** 1 detectados
  - (conexión a BD requerida)
  **Hallazgos:**
    - Verificar credenciales en .env

---

## 📋 Mapeo de Campos → Indicadores

| Campo | Indicadores que lo usan | Status |
|-------|-------------------------|--------|
| **ID** | 1 | ✓ Mapeado |
| **fecha** | 1 | ✓ Mapeado |
| **resultado** | 1 | ✓ Mapeado |
| **Meta** | 1 | ✓ Mapeado |
| **Ejecucion** | 1 | ✓ Mapeado |
| **Cumplimiento** | 1 | ✓ Mapeado |
| **Categoria** | 1 | ✓ Mapeado |
| **analisis** | 1 | ✓ Mapeado |
| **variables** | 1 | ✓ Mapeado |
| **Revisado** | 1 | ✓ Mapeado |


---

## ✅ Auditoría de Completitud

| Métrica | Valor |
|---------|-------|
| **Cobertura de períodos** | 89.3% |
| **Períodos encontrados** | 50 |
| **Esperados** | 56 |

**Gaps detectados:**
- {'indicador': '68', 'datos_disponibles': 8, 'faltantes': 4}
- {'indicador': '73', 'datos_disponibles': 8, 'faltantes': 4}
- {'indicador': '74', 'datos_disponibles': 8, 'faltantes': 4}


---

## 🎯 Próximos Pasos

1. **Validar fuentes críticas:** API Kawak y PostgreSQL
2. **Resolver hallazgos críticos:** Rangos inválidos en ejecución
3. **Completar períodos faltantes:** Rellenar datos 2022-2023
4. **Documentar responsables:** Asignar propietario por fuente
5. **Automatizar auditoría:** Ejecutar AGENT 1 mensualmente

---

**Generado por:** AGENT 1 — Data Source Audit Framework  
**Versión:** 1.0 SGIND-Optimizada
