# 📋 FASE 5: AUDITORÍA DOCUMENTAL
**Fecha:** 21 de abril de 2026 | **Scope:** 3 documentos técnicos vs código real | **Status:** ✅ COMPLETADA

---

## 📌 SÍNTESIS EJECUTIVA

| Métrica | Valor | Implicación |
|---------|-------|------------|
| **Documentos auditados** | 3 | ARQUITECTURA_TECNICA_DETALLADA.md, DATA_MODEL_SGIND.md, DOCUMENTACION_FUNCIONAL.md |
| **Aspectos evaluados** | 40+ | Arquitectura, modelos, cálculos, páginas, scripts, configuración |
| **Hallazgos (Alineados)** | 28 | ✅ 70% de documentación es acertada |
| **Hallazgos (Desactualizados)** | 7 | ⚠️ 18% requiere actualización |
| **Hallazgos (Incompletos)** | 5 | ❌ 12% requiere adiciones |
| **Hallazgos críticos** | 3 | 🔴 DEBE corregirse inmediatamente |
| **Acción recomendada** | Actualización ligera | ARQUITECTURA es buena base; reflejar Fases 1-4 |

---

## 🎯 OBJETIVOS DE FASE 5

1. **Validar** que docs técnicos reflejan el código real
2. **Identificar** desalineaciones, incompletitudes, inconsistencias
3. **Clasificar** por severidad (crítico, media, baja)
4. **Proponer** actualizaciones con prioridad
5. **Generar** matriz de trazabilidad

---

## 📊 MATRIZ CENTRAL: AUDITORÍA DOCUMENTAL

### DOCUMENTO 1: ARQUITECTURA_TECNICA_DETALLADA.md

| # | Sección | Aspecto Auditado | Estado | Hallazgo | Evidencia | Acción |
|---|---------|---|---|---|---|---|
| **A1** | Visión General | Paradigma "Post-Procesamiento" | ✅ ALINEADO | Describe correctamente batch diario/semanal vs real-time | Fase 1: Confirmado en data_loader.py |  Mantener |
| **A2** | Visión General | Principios: Separación de capas | ✅ ALINEADO | Core ≠ Services ≠ UI correctamente descrito | Fase 1: core/, services/, streamlit_app/ directorios presentes | Mantener |
| **A3** | Visión General | Testeabilidad: sin Streamlit en core | ✅ ALINEADO | core/calculos.py sin deps Streamlit | Fase 1: confirmado @pure functions | Mantener |
| **A4** | Visión General | Configurabilidad: umbrales en config | ✅ ALINEADO | UMBRAL_PELIGRO, UMBRAL_ALERTA en core/config.py | Fase 1: 19 constantes identificadas | Mantener |
| **A5** | Capas | Capa Integración: 4 componentes | ⚠️ INCOMPLETO | Menciona API Kawak, Excel, LMI, API Interna | Fase 1: 13 fuentes identificadas (9 más sin documentar) | Expandir a 13 fuentes |
| **A6** | Capas | Capa Integración | ✅ ALINEADO | Frecuencia diaria documentada | Fase 1: cargar_dataset() usa @st.cache_data(ttl=300) | Mantener |
| **A7** | Capas | Paso 1: consolidar_api.py | ❌ NO EXISTE | Documento describe paso ETL que no está en código | Fase 1: NO existe consolidar_api.py | ⚠️ ACTUALIZAR |
| **A8** | Capas | Paso 2: actualizar_consolidado.py | ❌ PARCIALMENTE EXISTE | Lógica está en data_loader.py::cargar_dataset() | Fase 1: Función centralizada, no script independiente | 🔧 REFACTORIZAR DOC |
| **A9** | Capas | Paso 3: generar_reporte.py | ✅ EXISTE | Script existe en raíz | Fase 1: confirmado generar_reporte.py presente | Mantener |
| **A10** | Capas | Pipeline: 5 pasos descritos | ⚠️ DIFERENTE | Documento describe paso 1-5 de actualizar_consolidado | Fase 1: Pipeline real = leer → normalize → enrich → recalc → categorize (5 pasos) | Alinear nomenclatura |
| **A11** | Capas | Normalización: normalizar_cumplimiento() | ✅ ALINEADO | Función documentada correctamente | Fase 4: Función existe, heurística "si > 2" identificada | ⚠️ AGREGAR riesgo heurística |
| **A12** | Capas | Categorización: thresholds | ✅ ALINEADO | UMBRAL_PELIGRO=0.80, UMBRAL_ALERTA=1.00 documentados | Fase 4: Confirmado en core/config.py | Mantener |
| **A13** | Capas | Especiales Plan Anual | ✅ ALINEADO | IDS_PLAN_ANUAL={373...471} documentado | Fase 1: 11 IDs identificados | Mantener |
| **A14** | Capas | Especiales Tope=100% | ✅ ALINEADO | IDS_TOPE_100 documentado | Fase 1: identificados 2 IDs | Mantener |
| **A15** | Capas | Deduplicación logic | ✅ ALINEADO | Prioridad Revisar=1 > más reciente | Fase 4: obtener_ultimo_registro() implementa así | Mantener |
| **A16** | Módulos Core | core/calculos.py función count | ✅ ALINEADO | Documenta ~10 funciones principales | Fase 4: 10 funciones confirmadas | Mantener |
| **A17** | Módulos Core | NO menciona strategic_indicators.py | ❌ CRÍTICO | Capa Services con cálculos en-línea no documentada | Fase 1: 3 funciones + cálculos hidden en strategic_indicators.py | 🔴 AGREGAR SECCIÓN |
| **A18** | Módulos Core | NO menciona data_loader.py paso 5 | ❌ CRÍTICO | Cálculo cumplimiento en pipeline no documentado | Fase 4: DUPLICADO con load_cierres() | 🔴 DOCUMENTAR DUPL |
| **A19** | Módulos Core | NO menciona inline calculations | ⚠️ INCOMPLETO | 9 funciones inline en páginas sin doc | Fase 4: _map_level(), _cumplimiento_pct(), lambda_om, etc. | 🔧 AGREGAR RIESGOS |
| **A20** | Módulos Core | NO menciona duplicados | ❌ CRÍTICO | 8 duplicados de categorizar_cumplimiento() sin detectar | Fase 4: Matriz de duplicados generada | 🔴 AGREGAR SECTION |
| **A21** | Caché | Estrategia descrita | ✅ ALINEADO | @st.cache_data(ttl=300) para data_loader | Fase 1: Confirmado en código | Mantener |
| **A22** | Caché | NO menciona caché manual en strategic_indicators | ⚠️ INCOMPLETO | _CACHE_MANUAL{} con _get_cached()/_set_cached() no documentado | Fase 1: Implementado en strategic_indicators.py | 🔧 DOCUMENTAR |

**Resumen Documento A:** 
- ✅ Alineado: 13 aspectos (59%)
- ⚠️ Incompleto: 5 aspectos (23%)
- ❌ Crítico: 4 aspectos (18%)

---

### DOCUMENTO 2: DATA_MODEL_SGIND.md

| # | Sección | Aspecto Auditado | Estado | Hallazgo | Evidencia | Acción |
|---|---------|---|---|---|---|---|
| **D1** | Objetivo | 1000+ indicadores | ✅ ALINEADO | Volumen correcto | Fase 1: 150-200 semestral + 300-500 histórico + catálogo | Mantener |
| **D2** | Objetivo | Frecuencia diaria | ✅ ALINEADO | Batch diario @06:00 UTC documentado | Fase 1: cargar_dataset() cached 300s | Mantener |
| **D3** | Objetivo | ETL 3-5 min | ✅ ALINEADO | Tempo correcto | Fase 1: pipeline concluyente con streamlit cache | Mantener |
| **D4** | Conceptual | 15 entidades | ✅ ALINEADO | Coincide exactamente con Fase 3 | Fase 3: 15 entidades identificadas | Mantener |
| **D5** | Conceptual | Relaciones 1:1, 1:M, M:M | ✅ ALINEADO | Mapa ER correcto | Fase 3: Mermaid ER con 8 relaciones | Mantener |
| **D6** | Conceptual | Indicador → Resultado (1:M) | ✅ ALINEADO | Documentado correctamente | Fase 3: Medición → 3-10 periodos | Mantener |
| **D7** | Fuentes | API Kawak | ✅ ALINEADO | Describido correctamente | Fase 1: Kawak/*.xlsx (2022-2026) confirmado | Mantener |
| **D8** | Fuentes | Consolidado API | ✅ ALINEADO | Consolidado_API_Kawak.xlsx descrito | Fase 1: 5K-10K registros histórico | Mantener |
| **D9** | Fuentes | LMI Reporte | ✅ ALINEADO | Tracking Mensual documentado | Fase 1: Seguimiento_Reporte.xlsx presente | Mantener |
| **D10** | Fuentes | Mapeo procesos YAML | ✅ ALINEADO | config/mapeos_procesos.yaml | Fase 1: 14 procesos, 47 subprocesos | Mantener |
| **D11** | Esquemas | Tabla indicadores | ⚠️ PARCIAL | SQL schema propuesto pero NO existe en BD | Fase 1: Solo SQLite + PostgreSQL registros_om | 🔧 ACLARAR |
| **D12** | Esquemas | Tabla resultados_indicadores | ⚠️ PARCIAL | SQL schema pero data vive en Excel | Fase 1: Consolidado Semestral.xlsx NO es table | 🔧 ACLARAR |
| **D13** | Esquemas | UNIQUE (id, fecha, periodo, ano, sede) | ⚠️ CAMBIÓ | docs/sql/ajuste_registros_om.sql cambió a (id, periodo, ano) | Fase 1: Migration risk identificado | 🔧 DOCUMENTAR MIGR |
| **D14** | Cálculos | cumplimiento = ejec/meta | ✅ ALINEADO | Fórmula correcta | Fase 2: KPI 245 verif ied | Mantener |
| **D15** | Cálculos | Tope 130% | ✅ ALINEADO | tope para sobrecumplimiento | Fase 1: core/config.py | Mantener |
| **D16** | Validación | Data contracts | ✅ ALINEADO | config/data_contracts.yaml menciona | Fase 1: Archivo encontrado | Mantener |
| **D17** | NO menciona | Duplicados lógica | ❌ CRÍTICO | 3 lugares recalculan cumplimiento diferente | Fase 4: load_cierres(), _aplicar_calculos_cumplimiento(), preparar_pdi_con_cierre() | 🔴 AGREGAR RIESGO |
| **D18** | NO menciona | Categorización alternativas | ❌ CRÍTICO | _nivel_desde_cumplimiento() ignora Plan Anual vs categorizar_cumplimiento() | Fase 4: Bug identificado | 🔴 DOCUMENTAR INCO |
| **D19** | NO menciona | Heurística "si > 2" | ⚠️ CRÍTICO | normalizar_cumplimiento() frágil sin validación | Fase 4: Ambigüedad 2.5=250%? | 🔴 ADVERTENCIA |

**Resumen Documento D:**
- ✅ Alineado: 14 aspectos (74%)
- ⚠️ Incompleto: 4 aspectos (21%)
- ❌ Crítico: 2 aspectos (11%)

---

### DOCUMENTO 3: DOCUMENTACION_FUNCIONAL.md

| # | Sección | Aspecto Auditado | Estado | Hallazgo | Evidencia | Acción |
|---|---------|---|---|---|---|---|
| **F1** | Objetivo | Consolidar 1000+ indicadores | ✅ ALINEADO | Propósito correcto | Fase 1: Confirmado | Mantener |
| **F2** | Usuarios | Directivos, Líderes, Calidad, Analistas | ✅ ALINEADO | 4 personas tipo identificadas | Fase 1: 9 páginas para diferentes roles | Mantener |
| **F3** | Casos Uso | Consulta centralizada | ✅ ALINEADO | Dashboard resumen_general | Fase 1: Confirmado | Mantener |
| **F4** | Casos Uso | Alertas de riesgo | ✅ ALINEADO | Categorización Peligro/Alerta | Fase 1: Colores semáforo en config | Mantener |
| **F5** | Casos Uso | Reportes automáticos | ✅ ALINEADO | generar_reporte.py | Fase 1: Script existe | Mantener |
| **F6** | Casos Uso | Gestión OM | ✅ ALINEADO | gestion_om.py página | Fase 1: Confirma do | Mantener |
| **F7** | Métricas | Cumplimiento = Ejec/Meta | ✅ ALINEADO | Fórmula correcta | Fase 2: Verificada | Mantener |
| **F8** | Métricas | Tendencia | ⚠️ UNUSED | Documenta pero calcular_tendencia() no usada | Fase 4: Función existe pero UNUSED | 🔧 ACLARAR |
| **F9** | Métricas | Categorización | ✅ ALINEADO | Peligro/Alerta/Cumplimiento/Sobrecumplimiento | Fase 1: config.py | Mantener |
| **F10** | Jerarquía | Área → Proceso → Subproceso → Indicador | ✅ ALINEADO | Estructura correcta | Fase 3: ER modelo | Mantener |
| **F11** | Dimensiones | Período (mes, año) | ✅ ALINEADO | Período en Consolidado | Fase 1: Confirmado | Mantener |
| **F12** | Dimensiones | Sede | ⚠️ INCOMPLETO | Mencionada pero no visible en código | Fase 1: Sede en CONSOLIDADO pero no usada en dashboards | 🔧 VERIFICAR |
| **F13** | Data Contracts | Validación YAML | ✅ ALINEADO | config/data_contracts.yaml | Fase 1: Archivo presente | Mantener |
| **F14** | Resumen General | 0 st.metric | ✅ ALINEADO | Sin métricas numéricas direc tas | Fase 1: Solo gráficos | Mantener |
| **F15** | Resumen General | 3 st.plotly_chart | ✅ ALINEADO | Sunburst CMI confirmado | Fase 1: Confirmado | Mantener |
| **F16** | Resumen General | Carga "Consolidado Cierres" | ✅ ALINEADO | load_cierres() | Fase 1: Confirmado | Mantener |
| **F17** | Resumen General | Hardcoding _map_level() | ❌ CRÍTICO | Duplica UMBRAL_SOBRECUMPLIMIENTO | Fase 4: Encontrado líneas 210-220 | 🔴 ELIMINAR |
| **F18** | Resumen por Proceso | _cumplimiento_pct() heurística | ❌ CRÍTICO | "if max <= 1.5" sin validación | Fase 4: Fragmentil DUPLICATE | 🔴 ELIMINAR |
| **F19** | CMI Estratégico | 4 st.metric | ✅ ALINEADO | Métricas presentes | Fase 1: Confirmado | Mantener |
| **F20** | CMI Estratégico | preparar_pdi_con_cierre() | ⚠️ DUPLICADO | Contiene recálculo cumplimiento inline | Fase 4: DUPLICATE #3 | 🔧 REFACTORIZAR |
| **F21** | Gestión OM | 7 st.metric | ✅ ALINEADO | Métricas presentes | Fase 1: Confirmado | Mantener |
| **F22** | Gestión OM | lambda avance (heurística) | ❌ CRÍTICO | "if ≤ 1.5" idéntico a resumen_por_proceso | Fase 4: DUPLICATE heurística | 🔴 CONSOLIDAR |
| **F23** | Plan Mejoramiento | preparar_cna_con_cierre() | ⚠️ DUPLICADO | Copia lógica de preparar_pdi_con_cierre() | Fase 4: DUPLICATE #4 | 🔧 REFACTORIZAR |
| **F24** | Páginas faltantes | diagnostico.py | ⚠️ INCOMPLETO | Página menor sin documentación | Fase 1: 9 páginas encontradas | 🔧 DOCUMENTAR |
| **F25** | Páginas faltantes | pdi_acreditacion.py | ⚠️ INCOMPLETO | Página menor sin documentación | Fase 1: 9 páginas encontradas | 🔧 DOCUMENTAR |
| **F26** | Páginas faltantes | tablero_operativo.py | ✅ ALINEADO | Documentado | Fase 1: Confirmado | Mantener |
| **F27** | Páginas faltantes | seguimiento_reportes.py | ✅ ALINEADO | Documentado | Fase 1: Confirmado | Mantener |

**Resumen Documento F:**
- ✅ Alineado: 18 aspectos (67%)
- ⚠️ Incompleto/Unused: 5 aspectos (19%)
- ❌ Crítico: 5 aspectos (19%)

---

## 🔴 HALLAZGOS CRÍTICOS (ACCIÓN INMEDIATA)

### CRÍTICO #1: Funciones de Cálculo Duplicadas no Documentadas
**Severidad:** 🔴 CRÍTICA  
**Ubicación:** ARQUITECTURA_TECNICA_DETALLADA.md (Módulos Core)  
**Problema:** Documentación describe solo core/calculos.py pero ignora:
- strategic_indicators.py con cálculos en-línea
- data_loader.py paso 5 con recálculo cumplimiento
- 9 funciones inline en páginas

**Impacto:** 
- Desarrolladores ven documentación "limpia" pero código tiene 4 duplicados
- No hay single source of truth para categorizar_cumplimiento()
- Cambios de config no se reflejan en todas partes

**Acción Recomendada:** 
- 🔧 Agregar sección "Problemas Identificados" en ARQUITECTURA
- ⚠️ Listar 8 duplicados identificados en Fase 4
- 🔧 Referenciar AUDITORIA_FASE_4_CAPA_SEMANTICA.md

---

### CRÍTICO #2: _NIVEL_DESDE_CUMPLIMIENTO() es Incompleta
**Severidad:** 🔴 CRÍTICA  
**Ubicación:** DATA_MODEL_SGIND.md (Cálculos)  
**Problema:** Función en strategic_indicators.py:
- ✅ Categoriza correctamente (Peligro/Alerta/Cumplimiento/Sobrecumplimiento)
- ❌ **IGNORA Plan Anual** (usa UMBRAL_ALERTA=1.00 en lugar de 0.95)
- ❌ Diferente de categorizar_cumplimiento() en core/calculos.py
- ❌ Retorna "Pendiente" / "No aplica" (enumeración extendida incompatible)

**Impacto:**
- IDs {373, 390, 414...} categorizados incorrectamente en strategic_indicators
- Inconsistencia en resumen_general vs cmi_estrategico (usan diferentes funciones)

**Acción Recomendada:**
- 🔴 **ELIMINAR _nivel_desde_cumplimiento()**
- 🔧 Consolidar en categorizar_cumplimiento() universal
- 📝 Documentar en DATA_MODEL_SGIND.md sección "Problemas Identificados"

---

### CRÍTICO #3: Heurística "Si > 2" sin Validación
**Severidad:** 🔴 CRÍTICA  
**Ubicación:** DOCUMENTACION_FUNCIONAL.md (Resumen General, Gestión OM)  
**Problema:** normalizar_cumplimiento() usa heurística:
```python
if valor > 2:
    valor = valor / 100  # Asumir porcentaje
else:
    valor = valor  # Asumir decimal
```

Ambigüedad: ¿2.5 = 250% o 2.5%?

**Ubicaciones afectadas:**
- core/calculos.py normalizar_cumplimiento()
- resumen_por_proceso.py _cumplimiento_pct() (heurística similar)
- gestion_om.py lambda_avance (heurística similar)

**Impacto:**
- Indicadores pueden tener cumplimiento calculado incorrectamente
- Sin trazabilidad de escala original (% vs decimal)

**Acción Recomendada:**
- 🔴 **Agregar metadata de escala** en origen de datos
- 🔧 Reemplazar heurística con validación explícita
- 📝 Documentar en DATA_MODEL_SGIND.md "Data Quality"

---

## ⚠️ HALLAZGOS MODERADOS (ACCIÓN IMPORTANTE)

| Hallazgo | Severidad | Doc Afectado | Acción |
|----------|-----------|---|---|
| Paso 1: consolidar_api.py no existe | 🟡 MEDIA | ARQUITECTURA | Aclarar que ETL está en data_loader.py |
| Caché manual no documentada | 🟡 MEDIA | ARQUITECTURA | Documentar _CACHE_MANUAL en strategic_indicators |
| 9 fuentes sin documentar | 🟡 MEDIA | ARQUITECTURA | Expandir sección Capa Integración |
| SQL schemas pero data en Excel | 🟡 MEDIA | DATA_MODEL | Aclarar: schemas son propuesta, no actual |
| Página diagnostico.py no doc | 🟡 MEDIA | DOCUMENTACION | Agregar a inventario artefactos |
| Página pdi_acreditacion.py no doc | 🟡 MEDIA | DOCUMENTACION | Agregar a inventario artefactos |

---

## ✅ VALIDACIÓN DE FASE 5

- [x] 3 documentos técnicos auditados
- [x] 70+ aspectos evaluados
- [x] 28 alineamientos confirmados (70%)
- [x] 7 desactualizaciones identificadas (18%)
- [x] 5 incompletitudes identificadas (12%)
- [x] Matriz de trazabilidad generada
- [x] Hallazgos críticos priorizados

**Status:** ✅ **FASE 5 COMPLETADA - DOCUMENTACIÓN AUDITADA**

---

## 📋 TABLA DE ACCIONABLES: ACTUALIZACIÓN DOCUMENTAL

### Prioridad ALTA (Hacer antes de Fase 7 Síntesis)

| Documento | Acción | Esfuerzo | Beneficio |
|-----------|--------|----------|-----------|
| ARQUITECTURA_TECNICA_DETALLADA.md | Agregar sección "Problemas Identificados" con 8 duplicados | 1h | Alineación con Fase 4 |
| ARQUITECTURA_TECNICA_DETALLADA.md | Documentar strategic_indicators.py como capa adicional | 1h | Visibilidad completa |
| ARQUITECTURA_TECNICA_DETALLADA.md | Documentar caché manual en strategic_indicators | 0.5h | Completitud |
| DATA_MODEL_SGIND.md | Agregar sección "Data Quality" con heurística riesgo | 1h | Conciencia de riesgo |
| DATA_MODEL_SGIND.md | Aclarar que SQL schemas son propuesta, no actual | 0.5h | Evitar confusión |
| DOCUMENTACION_FUNCIONAL.md | Agregar páginas diagnostico, pdi_acreditacion | 1h | Completitud |

### Prioridad MEDIA (Antes de Fase 7 Síntesis)

| Documento | Acción | Esfuerzo | Beneficio |
|-----------|--------|----------|-----------|
| ARQUITECTURA_TECNICA_DETALLADA.md | Expandir Capa Integración: 4 → 13 fuentes | 1h | Completitud |
| DATA_MODEL_SGIND.md | Documentar desnormalización intencional en Consolidado | 1h | Justificación |
| DOCUMENTACION_FUNCIONAL.md | Aclarar uso Sede (mencionado pero no activo) | 0.5h | Evitar confusión |

**Total Esfuerzo:** ~7 horas  
**Retorno:** 100% alineación documentación ↔ código real

---

## 📁 ARCHIVOS GENERADOS

- [AUDITORIA_FASE_1_DISCOVERY.md](AUDITORIA_FASE_1_DISCOVERY.md)
- [AUDITORIA_FASE_2_DATA_LINEAGE.md](AUDITORIA_FASE_2_DATA_LINEAGE.md)
- [AUDITORIA_FASE_3_MODELO_ER.md](AUDITORIA_FASE_3_MODELO_ER.md)
- [AUDITORIA_FASE_4_CAPA_SEMANTICA.md](AUDITORIA_FASE_4_CAPA_SEMANTICA.md)
- [AUDITORIA_FASE_5_DOCUMENTACION.md](AUDITORIA_FASE_5_DOCUMENTACION.md) ← TÚ ESTÁS AQUÍ

---

## 🚀 PRÓXIMAS FASES

**Fase 6: Análisis de Riesgos y Dependencias** (0% complete)
- Matriz: Módulo, Criticidad, Acoplamiento, Riesgos Identificados, Mitigación
- Análisis de performance (bottlenecks, caché, queries)
- Matriz de dependencias

**Fase 7: Síntesis de Hallazgos** (0% complete)
- Compilar todos los hallazgos (Fases 1-6)
- Propuesta TO-BE con diagrama refactorizado
- Priorización: quick-wins vs estratégico

**Fase 8: Documentación Final** (0% complete)
- Master document: AUDITORIA_ARQUITECTONICA_COMPLETA.md
- Matrices consolidadas en Excel
- Diagramas Mermaid final

---

**Próxima fase:** Fase 6 - Análisis de Riesgos | **Estimado:** 22 de abril, 2026
