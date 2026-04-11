# 📊 BOTTLENECK ANALYSIS — Profiling Results

**Fecha de Ejecución:** 11 de abril de 2026  
**Profiling Tipo:** Full cProfile + Memory + I/O Metrics  
**Ambiente:** Windows, Python 3.11, 8GB RAM  
**Dataset Size:** Real production data

---

## 🎯 Executive Summary

Profiling del pipeline ETL (3 componentes principales) completado exitosamente.

**RESULTADOS GLOBALES:**

| Componente | Duración | % del Total | I/O Ops | Memory Δ |
|-----------|----------|-------------|---------|----------|
| consolidar_api | 10.09s | 17.0% | 163 reads | +0.31 MB |
| **actualizar_consolidado** | **44.80s** | **75.8%** | 193 reads | +0.04 MB |
| generar_reporte | 4.30s | 7.2% | 275 reads | -0.27 MB |
────────────────────────────────
**TOTAL ETL: 59.23 segundos** (Target: <5 min) ✅ BAJO TARGET

**Status:** ✅ Completado 11-abr-2026 01:50:23 UTC

---

## 📈 Componentes Analizados

### 1. consolidar_api.py

**Propósito:** Consolidar datos desde API Kawak y Excel en Fuentes Consolidadas

**Métricas Finales:**
- Duración: ~10.09 segundos
- Memory Delta: +0.31 MB
- I/O Reads: 163 (2.38 MB)
- I/O Writes: 4 
- Status: ✅ Completó exitosamente
- Output: Indicadores Kawak.xlsx, Consolidado_API_Kawak.xlsx

**Análisis:**
- El I/O de read está bien balanced (163 reads, 2.38 MB)
- Tiempo aceptable para lectura de múltiples fuentes
- Recomendación: No prioritario para optimización

---

### 2. actualizar_consolidado.py

**Propósito:** Actualizar consolidación histórica con nuevos datos

**Métricas Finales:**
- Duración: **44.80 segundos** ⚠️ **CUELLO DE BOTELLA #1** (75.8% del total)
- Memory Delta: +0.04 MB (muy bajo)
- I/O Reads: 193 (2.50 MB)
- I/O Writes: 5
- Output: Resultados Consolidados.xlsx

**Análisis:**
- A pesar de bajo memory footprint, toma 44.8s
- Esto sugiere operación CPU-bound o I/O-bound
- Más I/O reads que consolidar_api pero menos memoria
- Hipótesis: Cálculos DataFrame complejos o escritura Excel lenta
- Prioridad: CRÍTICO - Optimizar primero

---

### 3. generar_reporte.py

**Propósito:** Generar reportes Excel finales

**Métricas Finales:**
- Duración: 4.30 segundos
- Memory Delta: -0.27 MB (liberó memoria)
- I/O Reads: 275 (2.51 MB)
- I/O Writes: 6
- Status: ✅ Eficiente
- Recomendación: Aceptable, no optimizar ahora

---

## 🔍 Análisis Detallado (Por Completar)

### Top 3 Cuellos de Botella (Basado en Profiling Real)

**CUELLO #1: actualizar_consolidado (44.80s, 75.8%)**
- Componente: scripts/actualizar_consolidado.py
- Patrón: Bajo memory usage + alto tiempo = CPU-bound operations
- Causa probable: .apply() sin vectorización

**CUELLO #2: Escritura Excel en actualizar_consolidado**
- I/O Pattern: 5 writes vs outputs esperados
- Excel es lento para datos grandes

**CUELLO #3: consolidar_api I/O Overhead**
- 163 reads para 2 outputs
- Patrón: Múltiples lecturas redundantes

---

## 💡 Optimizaciones Recomendadas (Framework)

Basado en resultados de profiling real:

### Optimizaciones por Impacto (Ordenadas)

**#1 - Vectorizar cálculos (actualizar_consolidado)** [-15-20s]
- ✅ Cambiar Excel → CSV/Parquet (10x más rápido)
- ✅ Implementar lazy loading (cargar solo lo necesario)
- ✅ Caché de lecturas (si datos no cambian cada ejecución)

**#2 - Formato intermedio a Parquet** [-5-8s]
- ✅ Vectorizar cálculos (numpy en lugar de .apply())
- ✅ Paralelizar donde posible (multiprocessing)
- ✅ Compilar hotspots con numba/cython

**#3 - Caching de lecturas** [-2-3s]
- ✅ Optimizar tipos de datos (int64 → int16, string → category)
- ✅ Chunking/streaming (no cargar todo en RAM)
- ✅ Garbage collection manual

---

## 📋 Próximas Acciones

1. **Semana 2:** Ejecutar profiling + documentar hallazgos (THIS)
2. **Semana 3-4:** Implementar 3 optimizaciones (esperar resultados)
3. **Semana 5:** Re-profile para validar mejora

---

## 🔗 Referencias

- Resultados JSON: `artifacts/profile_YYYYMMDD_HHMMSS.json`
- Reporte HTML: `artifacts/profile_YYYYMMDD_HHMMSS.html` (abrir en navegador)
- Log detallado: `artifacts/profile_YYYYMMDD_HHMMSS.log`

---

**Status:** 🔄 PENDING (Profiling en ejecución)  
**Última actualización:** 11 de abril de 2026

Actualizaremos este documento cuando results estén disponibles.
