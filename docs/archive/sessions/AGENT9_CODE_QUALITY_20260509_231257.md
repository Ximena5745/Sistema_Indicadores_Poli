# AGENT 9 — Code Quality & Refactoring Report
**Fecha:** 2026-05-09 23:12:58  
**Status:** Análisis completado  

---

## 📊 Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| **Archivos Python** | 135 |
| **Funciones encontradas** | 1098 |
| **Hallazgos detectados** | 78 |
| **Críticos** | 2 |
| **Altos** | 37 |
| **Medios** | 39 |

---

## 📈 Métricas de Código

| Métrica | Valor | Estado |
|---------|-------|--------|
| **Complejidad promedio** | 1.5 | ⚠ |
| **Longitud promedio función** | 16 líneas | 🟡 |
| **Funciones complejas (>10)** | 31 | |
| **Funciones largas (>100)** | 16 | |
| **Funciones muchos parámetros** | 13 | |

---

## 🔍 Hallazgos Detectados


### CRÍTICO (2)

**CAQ-DUP-77 — Duplicación de Código**

- **Ubicación:** core\semantica.py,scripts\validar_cambio_plan_anual.py:0
- **Símbolo:** `Funciones: categorizar_cumplimiento, categorizar_antigua_defectuosa`
- **Descripción:** Múltiples versiones de categorizar*() en diferentes archivos
- **Impacto:** Inconsistencia en resultados, difícil de mantener
- **Solución:** Centralizar en core/semantica.py, usar desde todos lados
- **Esfuerzo:** 5.0 horas

---
**CAQ-DUP-78 — Duplicación de Código**

- **Ubicación:** scripts\debug_cascada.py,core\calculos.py,scripts\consolidation\core\utils.py:0
- **Símbolo:** `Funciones: calcular_salud_institucional, calcular_tendencia, calcular_meses_en_peligro, calcular_kpis, calcular_cumplimiento, calcular_cascada`
- **Descripción:** Múltiples versiones de calcular*() en diferentes archivos
- **Impacto:** Inconsistencia en resultados, difícil de mantener
- **Solución:** Centralizar en core/semantica.py, usar desde todos lados
- **Esfuerzo:** 5.0 horas

---

### ALTO (37)

**CAQ-CMP-1 — Complejidad Ciclomática**

- **Ubicación:** core\semantica.py:54
- **Símbolo:** `categorizar_cumplimiento`
- **Descripción:** Complejidad: 13 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 3.9 horas

---
**CAQ-CMP-2 — Complejidad Ciclomática**

- **Ubicación:** core\semantica.py:192
- **Símbolo:** `recalcular_cumplimiento_faltante`
- **Descripción:** Complejidad: 13 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 3.9 horas

---
**CAQ-CMP-4 — Complejidad Ciclomática**

- **Ubicación:** scripts\actualizar_consolidado.py:103
- **Símbolo:** `main`
- **Descripción:** Complejidad: 20 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 6.0 horas

---
**CAQ-CMP-9 — Complejidad Ciclomática**

- **Ubicación:** scripts\analytics\data_preparator.py:168
- **Símbolo:** `limpiar_datos`
- **Descripción:** Complejidad: 13 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 3.9 horas

---
**CAQ-CMP-11 — Complejidad Ciclomática**

- **Ubicación:** scripts\analytics\data_preparator.py:283
- **Símbolo:** `generar_features`
- **Descripción:** Complejidad: 11 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 3.3 horas

---
**CAQ-CMP-13 — Complejidad Ciclomática**

- **Ubicación:** scripts\analytics\predictor.py:181
- **Símbolo:** `predecir`
- **Descripción:** Complejidad: 11 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 3.3 horas

---
**CAQ-CMP-19 — Complejidad Ciclomática**

- **Ubicación:** scripts\debug_cascada.py:72
- **Símbolo:** `main`
- **Descripción:** Complejidad: 16 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 4.8 horas

---
**CAQ-CMP-21 — Complejidad Ciclomática**

- **Ubicación:** scripts\diagnose_niveles_proceso.py:37
- **Símbolo:** `main`
- **Descripción:** Complejidad: 28 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 8.4 horas

---
**CAQ-CMP-25 — Complejidad Ciclomática**

- **Ubicación:** scripts\etl\builders.py:101
- **Símbolo:** `construir_registros_semestral`
- **Descripción:** Complejidad: 13 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 3.9 horas

---
**CAQ-CMP-28 — Complejidad Ciclomática**

- **Ubicación:** scripts\etl\builders.py:221
- **Símbolo:** `construir_registros_cierres`
- **Descripción:** Complejidad: 14 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 4.2 horas

---
**CAQ-CMP-31 — Complejidad Ciclomática**

- **Ubicación:** scripts\etl\catalogo.py:29
- **Símbolo:** `cargar_catalogo_completo`
- **Descripción:** Complejidad: 15 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 4.5 horas

---
**CAQ-CMP-32 — Complejidad Ciclomática**

- **Ubicación:** scripts\etl\catalogo.py:146
- **Símbolo:** `construir_catalogo`
- **Descripción:** Complejidad: 15 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 4.5 horas

---
**CAQ-CMP-34 — Complejidad Ciclomática**

- **Ubicación:** scripts\etl\escritura.py:3
- **Símbolo:** `limpiar_ordenar_hoja`
- **Descripción:** Complejidad: 22 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 6.6 horas

---
**CAQ-CMP-35 — Complejidad Ciclomática**

- **Ubicación:** scripts\etl\extraccion.py:220
- **Símbolo:** `determinar_meta_ejec`
- **Descripción:** Complejidad: 21 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 6.3 horas

---
**CAQ-CMP-37 — Complejidad Ciclomática**

- **Ubicación:** scripts\etl\extraccion.py:331
- **Símbolo:** `_extraer_registro`
- **Descripción:** Complejidad: 38 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 11.4 horas

---
**CAQ-CMP-40 — Complejidad Ciclomática**

- **Ubicación:** scripts\etl\formulas_excel.py:136
- **Símbolo:** `_materializar_formula_año`
- **Descripción:** Complejidad: 12 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 3.6 horas

---
**CAQ-CMP-41 — Complejidad Ciclomática**

- **Ubicación:** scripts\etl\formulas_excel.py:212
- **Símbolo:** `_reescribir_formulas`
- **Descripción:** Complejidad: 12 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 3.6 horas

---
**CAQ-CMP-42 — Complejidad Ciclomática**

- **Ubicación:** scripts\etl\fuentes.py:69
- **Símbolo:** `cargar_kawak_2025`
- **Descripción:** Complejidad: 14 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 4.2 horas

---
**CAQ-CMP-43 — Complejidad Ciclomática**

- **Ubicación:** scripts\etl\fuentes.py:353
- **Símbolo:** `cargar_consolidado_api_kawak_lookup`
- **Descripción:** Complejidad: 13 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 3.9 horas

---
**CAQ-CMP-45 — Complejidad Ciclomática**

- **Ubicación:** scripts\etl\purga.py:26
- **Símbolo:** `purgar_filas_invalidas`
- **Descripción:** Complejidad: 11 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 3.3 horas

---
**CAQ-CMP-46 — Complejidad Ciclomática**

- **Ubicación:** scripts\etl\purga.py:87
- **Símbolo:** `limpiar_cierres_existentes`
- **Descripción:** Complejidad: 12 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 3.6 horas

---
**CAQ-CMP-47 — Complejidad Ciclomática**

- **Ubicación:** scripts\etl\purga.py:248
- **Símbolo:** `reparar_multiserie`
- **Descripción:** Complejidad: 11 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 3.3 horas

---
**CAQ-CMP-48 — Complejidad Ciclomática**

- **Ubicación:** scripts\etl\purga.py:312
- **Símbolo:** `reparar_semestral_agregados`
- **Descripción:** Complejidad: 13 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 3.9 horas

---
**CAQ-CMP-49 — Complejidad Ciclomática**

- **Ubicación:** scripts\etl\validacion_historica.py:45
- **Símbolo:** `validar_coherencia_historica`
- **Descripción:** Complejidad: 16 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 4.8 horas

---
**CAQ-CMP-51 — Complejidad Ciclomática**

- **Ubicación:** scripts\etl\validation_gate.py:48
- **Símbolo:** `validar_consolidado_api_entrada`
- **Descripción:** Complejidad: 25 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 7.5 horas

---
**CAQ-CMP-53 — Complejidad Ciclomática**

- **Ubicación:** scripts\ingesta_plantillas.py:241
- **Símbolo:** `validar_registros`
- **Descripción:** Complejidad: 17 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 5.1 horas

---
**CAQ-CMP-54 — Complejidad Ciclomática**

- **Ubicación:** scripts\panel_monitoreo.py:81
- **Símbolo:** `main`
- **Descripción:** Complejidad: 11 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 3.3 horas

---
**CAQ-CMP-56 — Complejidad Ciclomática**

- **Ubicación:** scripts\plot_templates.py:88
- **Símbolo:** `waterfall_chart`
- **Descripción:** Complejidad: 11 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 3.3 horas

---
**CAQ-CMP-57 — Complejidad Ciclomática**

- **Ubicación:** scripts\prototipo_nivel3.py:110
- **Símbolo:** `main`
- **Descripción:** Complejidad: 44 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 13.2 horas

---
**CAQ-CMP-59 — Complejidad Ciclomática**

- **Ubicación:** scripts\run_pipeline.py:46
- **Símbolo:** `_load_contract_yaml_minimal`
- **Descripción:** Complejidad: 11 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 3.3 horas

---
**CAQ-CMP-61 — Complejidad Ciclomática**

- **Ubicación:** scripts\run_pipeline.py:215
- **Símbolo:** `main`
- **Descripción:** Complejidad: 48 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 14.4 horas

---
**CAQ-CMP-63 — Complejidad Ciclomática**

- **Ubicación:** scripts\validar_cambio_plan_anual.py:76
- **Símbolo:** `validar_plan_anual`
- **Descripción:** Complejidad: 22 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 6.6 horas

---
**CAQ-CMP-68 — Complejidad Ciclomática**

- **Ubicación:** services\cmi_filters.py:64
- **Símbolo:** `load_kawak_active_ids`
- **Descripción:** Complejidad: 14 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 4.2 horas

---
**CAQ-CMP-70 — Complejidad Ciclomática**

- **Ubicación:** services\data_loader.py:474
- **Símbolo:** `cargar_plan_accion`
- **Descripción:** Complejidad: 14 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 4.2 horas

---
**CAQ-CMP-71 — Complejidad Ciclomática**

- **Ubicación:** services\data_loader.py:582
- **Símbolo:** `cargar_metadatos_kawak`
- **Descripción:** Complejidad: 11 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 3.3 horas

---
**CAQ-CMP-72 — Complejidad Ciclomática**

- **Ubicación:** services\ficha_pdf.py:60
- **Símbolo:** `_chart_to_png`
- **Descripción:** Complejidad: 12 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 3.6 horas

---
**CAQ-CMP-75 — Complejidad Ciclomática**

- **Ubicación:** services\strategic_indicators.py:456
- **Símbolo:** `_preparar_indicadores_con_cierre`
- **Descripción:** Complejidad: 19 (máximo recomendado: 10)
- **Impacto:** Función con excesivas ramificaciones
- **Solución:** Refactorizar en funciones más pequeñas
- **Esfuerzo:** 5.7 horas

---

### MEDIO (39)

**CAQ-LEN-3 — Función Larga**

- **Ubicación:** core\semantica.py:192
- **Símbolo:** `recalcular_cumplimiento_faltante`
- **Descripción:** Longitud: 153 líneas (máximo: 50)
- **Impacto:** Función demasiado larga, difícil de mantener
- **Solución:** Dividir en funciones más pequeñas
- **Esfuerzo:** 3.1 horas

---
**CAQ-LEN-5 — Función Larga**

- **Ubicación:** scripts\actualizar_consolidado.py:103
- **Símbolo:** `main`
- **Descripción:** Longitud: 337 líneas (máximo: 50)
- **Impacto:** Función demasiado larga, difícil de mantener
- **Solución:** Dividir en funciones más pequeñas
- **Esfuerzo:** 6.7 horas

---
**CAQ-PAR-6 — Muchos Parámetros**

- **Ubicación:** scripts\agent5_data_validation.py:31
- **Símbolo:** `log_finding`
- **Descripción:** Parámetros: 8 (máximo: 5)
- **Impacto:** Función con demasiados parámetros
- **Solución:** Usar objetos o dataclasses para agrupar parámetros
- **Esfuerzo:** 1.0 horas

---
**CAQ-PAR-7 — Muchos Parámetros**

- **Ubicación:** scripts\agent9_code_quality.py:167
- **Símbolo:** `log_finding`
- **Descripción:** Parámetros: 11 (máximo: 5)
- **Impacto:** Función con demasiados parámetros
- **Solución:** Usar objetos o dataclasses para agrupar parámetros
- **Esfuerzo:** 1.0 horas

---
**CAQ-LEN-8 — Función Larga**

- **Ubicación:** scripts\agent_runner.py:275
- **Símbolo:** `main`
- **Descripción:** Longitud: 101 líneas (máximo: 50)
- **Impacto:** Función demasiado larga, difícil de mantener
- **Solución:** Dividir en funciones más pequeñas
- **Esfuerzo:** 2.0 horas

---
**CAQ-LEN-10 — Función Larga**

- **Ubicación:** scripts\analytics\data_preparator.py:168
- **Símbolo:** `limpiar_datos`
- **Descripción:** Longitud: 113 líneas (máximo: 50)
- **Impacto:** Función demasiado larga, difícil de mantener
- **Solución:** Dividir en funciones más pequeñas
- **Esfuerzo:** 2.3 horas

---
**CAQ-LEN-12 — Función Larga**

- **Ubicación:** scripts\analytics\data_preparator.py:283
- **Símbolo:** `generar_features`
- **Descripción:** Longitud: 124 líneas (máximo: 50)
- **Impacto:** Función demasiado larga, difícil de mantener
- **Solución:** Dividir en funciones más pequeñas
- **Esfuerzo:** 2.5 horas

---
**CAQ-LEN-14 — Función Larga**

- **Ubicación:** scripts\analytics\predictor.py:413
- **Símbolo:** `generar`
- **Descripción:** Longitud: 125 líneas (máximo: 50)
- **Impacto:** Función demasiado larga, difícil de mantener
- **Solución:** Dividir en funciones más pequeñas
- **Esfuerzo:** 2.5 horas

---
**CAQ-LEN-15 — Función Larga**

- **Ubicación:** scripts\consolidation\cli.py:16
- **Símbolo:** `create_parser`
- **Descripción:** Longitud: 129 líneas (máximo: 50)
- **Impacto:** Función demasiado larga, difícil de mantener
- **Solución:** Dividir en funciones más pequeñas
- **Esfuerzo:** 2.6 horas

---
**CAQ-PAR-16 — Muchos Parámetros**

- **Ubicación:** scripts\consolidation\core\audit.py:139
- **Símbolo:** `registrar_operacion`
- **Descripción:** Parámetros: 12 (máximo: 5)
- **Impacto:** Función con demasiados parámetros
- **Solución:** Usar objetos o dataclasses para agrupar parámetros
- **Esfuerzo:** 1.0 horas

---
**CAQ-PAR-17 — Muchos Parámetros**

- **Ubicación:** scripts\consolidation\core\audit.py:188
- **Símbolo:** `versionar_artefacto`
- **Descripción:** Parámetros: 6 (máximo: 5)
- **Impacto:** Función con demasiados parámetros
- **Solución:** Usar objetos o dataclasses para agrupar parámetros
- **Esfuerzo:** 1.0 horas

---
**CAQ-PAR-18 — Muchos Parámetros**

- **Ubicación:** scripts\consolidation\extractors\base.py:15
- **Símbolo:** `__init__`
- **Descripción:** Parámetros: 6 (máximo: 5)
- **Impacto:** Función con demasiados parámetros
- **Solución:** Usar objetos o dataclasses para agrupar parámetros
- **Esfuerzo:** 1.0 horas

---
**CAQ-LEN-20 — Función Larga**

- **Ubicación:** scripts\debug_cascada.py:72
- **Símbolo:** `main`
- **Descripción:** Longitud: 125 líneas (máximo: 50)
- **Impacto:** Función demasiado larga, difícil de mantener
- **Solución:** Dividir en funciones más pequeñas
- **Esfuerzo:** 2.5 horas

---
**CAQ-LEN-22 — Función Larga**

- **Ubicación:** scripts\diagnose_niveles_proceso.py:37
- **Símbolo:** `main`
- **Descripción:** Longitud: 136 líneas (máximo: 50)
- **Impacto:** Función demasiado larga, difícil de mantener
- **Solución:** Dividir en funciones más pequeñas
- **Esfuerzo:** 2.7 horas

---
**CAQ-PAR-23 — Muchos Parámetros**

- **Ubicación:** scripts\etl\audit.py:94
- **Símbolo:** `registrar_cambio_datos`
- **Descripción:** Parámetros: 6 (máximo: 5)
- **Impacto:** Función con demasiados parámetros
- **Solución:** Usar objetos o dataclasses para agrupar parámetros
- **Esfuerzo:** 1.0 horas

---
**CAQ-PAR-24 — Muchos Parámetros**

- **Ubicación:** scripts\etl\builders.py:25
- **Símbolo:** `construir_registros_historico`
- **Descripción:** Parámetros: 10 (máximo: 5)
- **Impacto:** Función con demasiados parámetros
- **Solución:** Usar objetos o dataclasses para agrupar parámetros
- **Esfuerzo:** 1.0 horas

---
**CAQ-LEN-26 — Función Larga**

- **Ubicación:** scripts\etl\builders.py:101
- **Símbolo:** `construir_registros_semestral`
- **Descripción:** Longitud: 115 líneas (máximo: 50)
- **Impacto:** Función demasiado larga, difícil de mantener
- **Solución:** Dividir en funciones más pequeñas
- **Esfuerzo:** 2.3 horas

---
**CAQ-PAR-27 — Muchos Parámetros**

- **Ubicación:** scripts\etl\builders.py:101
- **Símbolo:** `construir_registros_semestral`
- **Descripción:** Parámetros: 11 (máximo: 5)
- **Impacto:** Función con demasiados parámetros
- **Solución:** Usar objetos o dataclasses para agrupar parámetros
- **Esfuerzo:** 1.0 horas

---
**CAQ-LEN-29 — Función Larga**

- **Ubicación:** scripts\etl\builders.py:221
- **Símbolo:** `construir_registros_cierres`
- **Descripción:** Longitud: 119 líneas (máximo: 50)
- **Impacto:** Función demasiado larga, difícil de mantener
- **Solución:** Dividir en funciones más pequeñas
- **Esfuerzo:** 2.4 horas

---
**CAQ-PAR-30 — Muchos Parámetros**

- **Ubicación:** scripts\etl\builders.py:221
- **Símbolo:** `construir_registros_cierres`
- **Descripción:** Parámetros: 10 (máximo: 5)
- **Impacto:** Función con demasiados parámetros
- **Solución:** Usar objetos o dataclasses para agrupar parámetros
- **Esfuerzo:** 1.0 horas

---
**CAQ-PAR-33 — Muchos Parámetros**

- **Ubicación:** scripts\etl\cumplimiento.py:154
- **Símbolo:** `_calc_cumpl_con_tope_dinamico`
- **Descripción:** Parámetros: 6 (máximo: 5)
- **Impacto:** Función con demasiados parámetros
- **Solución:** Usar objetos o dataclasses para agrupar parámetros
- **Esfuerzo:** 1.0 horas

---
**CAQ-LEN-36 — Función Larga**

- **Ubicación:** scripts\etl\extraccion.py:220
- **Símbolo:** `determinar_meta_ejec`
- **Descripción:** Longitud: 106 líneas (máximo: 50)
- **Impacto:** Función demasiado larga, difícil de mantener
- **Solución:** Dividir en funciones más pequeñas
- **Esfuerzo:** 2.1 horas

---
**CAQ-LEN-38 — Función Larga**

- **Ubicación:** scripts\etl\extraccion.py:331
- **Símbolo:** `_extraer_registro`
- **Descripción:** Longitud: 162 líneas (máximo: 50)
- **Impacto:** Función demasiado larga, difícil de mantener
- **Solución:** Dividir en funciones más pequeñas
- **Esfuerzo:** 3.2 horas

---
**CAQ-PAR-39 — Muchos Parámetros**

- **Ubicación:** scripts\etl\extraccion.py:331
- **Símbolo:** `_extraer_registro`
- **Descripción:** Parámetros: 7 (máximo: 5)
- **Impacto:** Función con demasiados parámetros
- **Solución:** Usar objetos o dataclasses para agrupar parámetros
- **Esfuerzo:** 1.0 horas

---
**CAQ-PAR-44 — Muchos Parámetros**

- **Ubicación:** scripts\etl\notifications.py:32
- **Símbolo:** `__init__`
- **Descripción:** Parámetros: 6 (máximo: 5)
- **Impacto:** Función con demasiados parámetros
- **Solución:** Usar objetos o dataclasses para agrupar parámetros
- **Esfuerzo:** 1.0 horas

---
**CAQ-LEN-50 — Función Larga**

- **Ubicación:** scripts\etl\validacion_historica.py:45
- **Símbolo:** `validar_coherencia_historica`
- **Descripción:** Longitud: 118 líneas (máximo: 50)
- **Impacto:** Función demasiado larga, difícil de mantener
- **Solución:** Dividir en funciones más pequeñas
- **Esfuerzo:** 2.4 horas

---
**CAQ-LEN-52 — Función Larga**

- **Ubicación:** scripts\etl\validation_gate.py:48
- **Símbolo:** `validar_consolidado_api_entrada`
- **Descripción:** Longitud: 118 líneas (máximo: 50)
- **Impacto:** Función demasiado larga, difícil de mantener
- **Solución:** Dividir en funciones más pequeñas
- **Esfuerzo:** 2.4 horas

---
**CAQ-LEN-55 — Función Larga**

- **Ubicación:** scripts\panel_monitoreo.py:81
- **Símbolo:** `main`
- **Descripción:** Longitud: 201 líneas (máximo: 50)
- **Impacto:** Función demasiado larga, difícil de mantener
- **Solución:** Dividir en funciones más pequeñas
- **Esfuerzo:** 4.0 horas

---
**CAQ-LEN-58 — Función Larga**

- **Ubicación:** scripts\prototipo_nivel3.py:110
- **Símbolo:** `main`
- **Descripción:** Longitud: 296 líneas (máximo: 50)
- **Impacto:** Función demasiado larga, difícil de mantener
- **Solución:** Dividir en funciones más pequeñas
- **Esfuerzo:** 5.9 horas

---
**CAQ-PAR-60 — Muchos Parámetros**

- **Ubicación:** scripts\run_pipeline.py:149
- **Símbolo:** `_run_step`
- **Descripción:** Parámetros: 6 (máximo: 5)
- **Impacto:** Función con demasiados parámetros
- **Solución:** Usar objetos o dataclasses para agrupar parámetros
- **Esfuerzo:** 1.0 horas

---
**CAQ-LEN-62 — Función Larga**

- **Ubicación:** scripts\run_pipeline.py:215
- **Símbolo:** `main`
- **Descripción:** Longitud: 366 líneas (máximo: 50)
- **Impacto:** Función demasiado larga, difícil de mantener
- **Solución:** Dividir en funciones más pequeñas
- **Esfuerzo:** 7.3 horas

---
**CAQ-LEN-64 — Función Larga**

- **Ubicación:** scripts\validar_cambio_plan_anual.py:76
- **Símbolo:** `validar_plan_anual`
- **Descripción:** Longitud: 220 líneas (máximo: 50)
- **Impacto:** Función demasiado larga, difícil de mantener
- **Solución:** Dividir en funciones más pequeñas
- **Esfuerzo:** 4.4 horas

---
**CAQ-LEN-65 — Función Larga**

- **Ubicación:** scripts\validar_indicadores_procesos.py:107
- **Símbolo:** `build_cross_validation_table`
- **Descripción:** Longitud: 115 líneas (máximo: 50)
- **Impacto:** Función demasiado larga, difícil de mantener
- **Solución:** Dividir en funciones más pequeñas
- **Esfuerzo:** 2.3 horas

---
**CAQ-PAR-66 — Muchos Parámetros**

- **Ubicación:** services\ai_analysis.py:58
- **Símbolo:** `analizar_texto_indicador`
- **Descripción:** Parámetros: 6 (máximo: 5)
- **Impacto:** Función con demasiados parámetros
- **Solución:** Usar objetos o dataclasses para agrupar parámetros
- **Esfuerzo:** 1.0 horas

---
**CAQ-PAR-67 — Muchos Parámetros**

- **Ubicación:** services\ai_analysis.py:222
- **Símbolo:** `analizar_ficha_cmi`
- **Descripción:** Parámetros: 7 (máximo: 5)
- **Impacto:** Función con demasiados parámetros
- **Solución:** Usar objetos o dataclasses para agrupar parámetros
- **Esfuerzo:** 1.0 horas

---
**CAQ-PAR-69 — Muchos Parámetros**

- **Ubicación:** services\cmi_filters.py:379
- **Símbolo:** `filter_df_for_procesos`
- **Descripción:** Parámetros: 6 (máximo: 5)
- **Impacto:** Función con demasiados parámetros
- **Solución:** Usar objetos o dataclasses para agrupar parámetros
- **Esfuerzo:** 1.0 horas

---
**CAQ-LEN-73 — Función Larga**

- **Ubicación:** services\ficha_pdf.py:164
- **Símbolo:** `build_ficha_pdf`
- **Descripción:** Longitud: 271 líneas (máximo: 50)
- **Impacto:** Función demasiado larga, difícil de mantener
- **Solución:** Dividir en funciones más pequeñas
- **Esfuerzo:** 5.4 horas

---
**CAQ-LEN-74 — Función Larga**

- **Ubicación:** services\strategic_indicators.py:284
- **Símbolo:** `load_cierres`
- **Descripción:** Longitud: 134 líneas (máximo: 50)
- **Impacto:** Función demasiado larga, difícil de mantener
- **Solución:** Dividir en funciones más pequeñas
- **Esfuerzo:** 2.7 horas

---
**CAQ-LEN-76 — Función Larga**

- **Ubicación:** services\strategic_indicators.py:456
- **Símbolo:** `_preparar_indicadores_con_cierre`
- **Descripción:** Longitud: 148 líneas (máximo: 50)
- **Impacto:** Función demasiado larga, difícil de mantener
- **Solución:** Dividir en funciones más pequeñas
- **Esfuerzo:** 3.0 horas

---

## ✅ Próximos Pasos

1. **Revisar hallazgos CRÍTICOS:** Duplicación (centralizar)
2. **Refactorizar funciones complejas:** Dividir en funciones menores
3. **Centralizar configuración:** Mover umbrales a core/config.py
4. **Mejorar tests:** Aumentar cobertura de funciones auditadas
5. **Modularizar:** Separar responsabilidades entre módulos

---

**Generado por:** AGENT 9 — Code Quality & Refactoring Framework  
**Versión:** 1.0 SGIND-Optimizada
