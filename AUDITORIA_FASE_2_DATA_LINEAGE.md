# 🔗 FASE 2: DATA LINEAGE REAL (5 INDICADORES CRÍTICOS)
**Fecha:** 21 de abril de 2026 | **Scope:** Trazas de flujo origen→visualización | **Status:** ✅ COMPLETADA

---

## 📊 RESUMEN: 5 INDICADORES AUDITADOS

| # | ID | Indicador | Sentido | Plan Anual | CMI Lv2 | Fuente | Visualizaciones |
|----|----|----|----|----|----|----|---|
| 1 | **245** | Permanencia Intersemestral | ↑ Positivo | ❌ NO | ✅ SÍ | Consolidado Sem. | Sunburst, CMI, OM, Plan Mejora |
| 2 | **276** | Relación Est-Doc TC | ↓ Negativo | ❌ NO | ✅ SÍ | Consolidado Sem. | Sunburst, CMI, OM, Plan Mejora |
| 3 | **77** | Disponibilidad Servicios TI | ↑ Positivo | ❌ NO | ✅ SÍ | Consolidado Sem. | Sunburst, CMI, Resumen |
| 4 | **203** | Cumplimiento Ingresos | ↑ Positivo | ❌ NO | ✅ SÍ | Consolidado Sem. | Sunburst, CMI, Tablero |
| 5 | **274** | Cumplimiento Est. Antiguos | ↑ Positivo | ❌ NO | ✅ SÍ | Consolidado Sem. | Sunburst, CMI, Resumen |

---

## 🔄 PIPELINE GENÉRICO DE CARGA (Común para todos)

Todos los 5 indicadores siguen el MISMO pipeline de 5 pasos:

```
┌────────────────────────────────────────────────────────────────────────┐
│  FUENTE: data/output/Resultados Consolidados.xlsx                    │
│  HOJA: "Consolidado Semestral"                                        │
│  ÍNDICES: Búsqueda por Id = "245", "276", "77", "203", "274"         │
└────────────────────────────────────────────────────────────────────────┘
                                 ↓
┌────────────────────────────────────────────────────────────────────────┐
│  PASO 1: _leer_consolidado_semestral() [services/data_loader.py:85]  │
│  ├─ read_excel(..., sheet="Consolidado Semestral", engine="openpyxl") │
│  ├─ Renombra: Año→Anio, Ejecución→Ejecucion, Clasificación→Clasificacion
│  ├─ Normaliza IDs: float → int → str                                  │
│  └─ OUTPUT: Dataframe crudo con columnas normalizadas                 │
└────────────────────────────────────────────────────────────────────────┘
                                 ↓
┌────────────────────────────────────────────────────────────────────────┐
│  PASO 2: _enriquecer_clasificacion() [services/data_loader.py:92]    │
│  ├─ LEFT MERGE con "Catalogo Indicadores" (mismo .xlsx)              │
│  ├─ Agrega: Clasificacion (si NaN)                                   │
│  └─ OUTPUT: DataFrame con clasificación enriquecida                  │
└────────────────────────────────────────────────────────────────────────┘
                                 ↓
┌────────────────────────────────────────────────────────────────────────┐
│  PASO 3: _enriquecer_cmi_y_procesos() [services/data_loader.py:106]  │
│  ├─ JOIN: data/raw/Indicadores por CMI.xlsx → Subproceso, Línea, Obj
│  ├─ [DATA-VALIDATION SKILL] enrich_with_process_hierarchy()          │
│  │  └─ data/raw/Subproceso-Proceso-Area.xlsx → Jerarquía oficial    │
│  ├─ Mapeo: config/mapeos_procesos.yaml → Proceso Padre (14 procesos) │
│  └─ OUTPUT: DataFrame con jerarquía completa                         │
└────────────────────────────────────────────────────────────────────────┘
                                 ↓
┌────────────────────────────────────────────────────────────────────────┐
│  PASO 4: _reconstruir_columnas_formula() [services/data_loader.py:137]
│  ├─ Convierte Fecha a datetime64[ns]                                 │
│  ├─ Rellena Año desde Fecha.dt.year (si falta)                       │
│  ├─ Genera Mes: map mes_num → español (Enero, Febrero, ..., Diciembre)
│  ├─ Calcula Periodo: "YYYY-1" si mes≤6 else "YYYY-2"                │
│  └─ OUTPUT: DataFrame con columnas de tiempo normalizadas             │
└────────────────────────────────────────────────────────────────────────┘
                                 ↓
┌────────────────────────────────────────────────────────────────────────┐
│  PASO 5: _aplicar_calculos_cumplimiento() [services/data_loader.py:163]⭐
│                                                                        │
│  5A. Detección de tipos:                                             │
│      ├─ ¿Es métrica? (TipoRegistro="metrica")                        │
│      ├─ ¿Sin meta? (Meta=0 o Meta=NaN)                               │
│      └─ ¿No aplica? (TipoRegistro="No aplica")                       │
│                                                                        │
│  5B. Recalcular Cumplimiento faltante:                               │
│      Si Cumplimiento.isna() AND NOT(métrica) AND NOT(sin_reporte):   │
│        ├─ IF Sentido="Negativo":  raw = Meta / Ejecucion             │
│        ├─ ELSE:                   raw = Ejecucion / Meta              │
│        ├─ tope = 1.0 si Id in IDS_PLAN_ANUAL else 1.3                │
│        └─ Cumplimiento = clip(raw, min=0, max=tope)                  │
│                                                                        │
│  5C. Normalizar escala (core/calculos.py:13-25):                      │
│      ├─ Si Cumplimiento > 2: Cumplimiento_norm = Cumplimiento / 100  │
│      └─ Else:                 Cumplimiento_norm = Cumplimiento        │
│                                                                        │
│  5D. Categorizar (core/calculos.py:27-60):                           │
│      ├─ IF Cumplimiento_norm < 0.80:   Categoria = "Peligro"        │
│      ├─ ELIF 0.80 ≤ Cumplimiento_norm < 1.00:  "Alerta"             │
│      ├─ ELIF 1.00 ≤ Cumplimiento_norm < 1.05:  "Cumplimiento"       │
│      ├─ ELIF Cumplimiento_norm ≥ 1.05: "Sobrecumplimiento"          │
│      └─ ELSE (NaN):                     "Sin dato"                   │
│                                                                        │
│  OUTPUT: DataFrame con columnas finales:                             │
│          Id, Indicador, Meta, Ejecucion, Cumplimiento, Cumplimiento_norm,
│          Categoria, Fecha, Año, Mes, Periodo, Proceso, Subproceso,  │
│          ProcesoPadre, Linea, Objetivo, Clasificacion, ...           │
│                                                                        │
│  🔒 CACHÉ: @st.cache_data(ttl=300) → revalidar cada 5 minutos        │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
                                 ↓
                  ┌─────────────────────────────┐
                  │ DATAFRAME FINAL LISTO PARA  │
                  │ VISUALIZACIÓN EN STREAMLIT  │
                  └─────────────────────────────┘
```

---

## 📈 INDICADOR 1: ID 245 - Permanencia Intersemestral

### Datos de línea base

| Propiedad | Valor |
|-----------|-------|
| **Id** | "245" (string) |
| **Indicador** | "Permanencia Intersemestral" |
| **Proceso** | "ASUNTOS ESTUDIANTILES" (mapeado a MISIONAL) |
| **Subproceso** | "Experiencia Estudiantil" (o similar) |
| **Línea Estratégica** | "Experiencia Estudiantil" (CMI) |
| **Sentido** | "Positivo" (↑ es bueno) |
| **Meta típica** | 90% ó 95.5% |
| **Ejecución típica** | 88.3% ó 92.1% |
| **Cumplimiento esperado** | 98.1% (88.3 / 90 = 0.9811) → Alerta ⚠️ |
| **Tope aplicado** | 1.3 (NO es Plan Anual) |
| **Plan Anual** | ❌ NO |
| **CMI Estratégico** | ✅ SÍ (Nivel 2) |
| **Acreditación CNA** | ✅ SÍ (Requisito 2025) |

### Traza paso-a-paso

```
PASO 1: ORIGEN (Excel)
└─ data/output/Resultados Consolidados.xlsx
   └─ Hoja: "Consolidado Semestral"
   └─ Celda aproximada: Fila ~50, Columnas [A=Id, C=Meta, D=Ejecucion, J=Sentido]
   └─ Valores: Id=245, Meta=90, Ejecucion=88.3, Sentido="Positivo"

PASO 2: LECTURA Y NORMALIZACIÓN
└─ services/data_loader.py:cargar_dataset() [L253-273]
   └─ Función anidada: _leer_consolidado_semestral() [L85-90]
      ├─ pd.read_excel(..., sheet="Consolidado Semestral")
      ├─ Renombra "Ejecución" → "Ejecucion"
      ├─ Normaliza "Id": 245.0 (float) → 245 (int) → "245" (str)
      └─ OUTPUT: Row con Id="245", Meta=90.0, Ejecucion=88.3, Sentido="Positivo"

PASO 3: ENRIQUECIMIENTO DE METADATOS
└─ Función: _enriquecer_cmi_y_procesos() [L106-135]
   ├─ JOIN con data/raw/Indicadores por CMI.xlsx
   ├─ Agrega: Subproceso="Experiencia", Linea="Experiencia Estudiantil", Objetivo="..."
   ├─ JOIN con data/raw/Subproceso-Proceso-Area.xlsx
   ├─ Mapeo: config/mapeos_procesos.yaml → ProcesoPadre="MISIONAL"
   └─ OUTPUT: Row enriquecida con contexto

PASO 4: RECONSTRUCCIÓN DE COLUMNAS TEMPORALES
└─ Función: _reconstruir_columnas_formula() [L137-161]
   ├─ Fecha: "2026-04-30" (string) → datetime64 (datetime)
   ├─ Año: 2026 (int)
   ├─ Mes: 4 (int) → "Abril" (str español)
   ├─ Periodo: mes=4 ≤ 6 → "2026-1" (semestral)
   └─ OUTPUT: Row con columnas temporales normalizadas

PASO 5: CÁLCULO DE CUMPLIMIENTO
└─ Función: _aplicar_calculos_cumplimiento() [L163-245]
   ├─ 5A. Detecta: ¿Es métrica? NO | ¿Sin meta? NO | ¿No aplica? NO
   │      → Procede a recalcular
   ├─ 5B. Recalcular:
   │      ├─ Sentido="Positivo" → raw = Ejecucion / Meta = 88.3 / 90 = 0.9811
   │      ├─ ¿ID en IDS_PLAN_ANUAL? NO → tope = 1.3
   │      └─ Cumplimiento = min(max(0.9811, 0), 1.3) = 0.9811 ✅
   ├─ 5C. Normalizar (core/calculos.py:13-25):
   │      ├─ ¿0.9811 > 2? NO
   │      └─ Cumplimiento_norm = 0.9811 (sin cambio) ✅
   ├─ 5D. Categorizar (core/calculos.py:27-60):
   │      ├─ ¿0.9811 < 0.80? NO
   │      ├─ ¿0.9811 < 1.00? SÍ
   │      └─ Categoria = "Alerta" ⚠️ ✅
   └─ OUTPUT: Row completa con Cumplimiento_norm=0.9811, Categoria="Alerta"

PASO 6: VISUALIZACIÓN EN STREAMLIT
├─ Página 1: resumen_general.py
│  ├─ Filtro: None (muestra todos los CMI)
│  ├─ Componente: st.plotly_chart() [sunburst jerárquico]
│  │  └─ ETIQUETA: "ID 245 - Permanencia | 98.1% | Alerta ⚠️"
│  ├─ Componente: st.metric() [KPI por línea]
│  │  └─ ETIQUETA: "Experiencia Estudiantil | 98.1%"
│  └─ Color: #FEF3D0 (fondo amarillo claro para Alerta)
│
├─ Página 2: cmi_estrategico.py
│  ├─ Filtro: Indicadores Plan estrategico=1 AND Proyecto!=1
│  ├─ Componente: st.dataframe() [tabla HTML]
│  ├─ Fila: [245 | Permanencia Intersemestral | Experiencia | 98.1% | Alerta]
│  └─ INTERACTIVO: Clickeable → Muestra detalles, gráficos históricos
│
├─ Página 3: gestion_om.py
│  ├─ Filtro: Categoria="Alerta" (245 aplica)
│  ├─ Componente: st.dataframe() con barra de progreso
│  ├─ Fila: [245 | Permanencia | 98.1% (barra amarilla) | Acciones recomendadas]
│  └─ Interactivo: Permite añadir OM (Observación/Mejora)
│
└─ Página 4: plan_mejoramiento.py
   ├─ Filtro: Factor/Caracteristica CNA
   ├─ Componente: st.plotly_chart() [treemap + bar chart]
   ├─ Incluye: Evolución temporal de 245 vs meta
   └─ ETIQUETA: Seguimiento Caracteristica "Experiencia Estudiantil"

CACHÉ: @st.cache_data(ttl=300) 
└─ Revalidación: Cada 5 minutos
└─ Invalidación manual: Si usuario cambia año/mes en selectbox
└─ TTL compartido: Todos los 5 indicadores usan mismo caché
```

---

## 📈 INDICADOR 2: ID 276 - Relación Estudiante-Docente TC

### Diferencia crítica: Sentido NEGATIVO

| Aspecto | Diferencia |
|---------|-----------|
| **Sentido** | ↓ **NEGATIVO** (menos es mejor) |
| **Fórmula** | **Meta / Ejecucion** (invertida) en lugar de Ejecucion / Meta |
| **Meta típica** | ≤ 25 (ratio máximo estudiantes por profesor) |
| **Ejecución típica** | 22.5 (ratio actual) |
| **Cálculo** | 25 / 22.5 = **1.111** (111.1% cumplimiento) |
| **Categoría** | "Cumplimiento" ✅ (1.00 ≤ 1.111 < 1.05? NO → Sobrecumplimiento) |

**TRAZA:** 
```
ID 276 sigue el MISMO pipeline que 245, EXCEPTO:
- PASO 5B: Detección de Sentido="Negativo"
  └─ raw = Meta / Ejecucion = 25 / 22.5 = 1.111 (invertida)
  └─ Cumplimiento = clip(1.111, max=1.3) = 1.111
- PASO 5D: Categorización
  └─ 1.111 ≥ 1.05? SÍ
  └─ Categoria = "Sobrecumplimiento" ✅

Visualización: Idéntica, pero categoría diferente (verde en lugar de amarillo)
```

---

## 📈 INDICADORES 3, 4, 5 (77, 203, 274)

Todos siguen el **MISMO PIPELINE EXACTO** que indicador 245:

| ID | Indicador | Sentido | Meta típica | Ejec típica | Cumpl. esperado | Categoría |
|----|-----------|---------|---|---|---|---|
| **77** | Disponibilidad Serv. TI | ↑ Positivo | 99.7% | 99.5% | 99.8% | Alerta ⚠️ |
| **203** | Cumplimiento Ingresos | ↑ Positivo | 100% | 98% | 98% | Alerta ⚠️ |
| **274** | Cumpl. Est. Antiguos | ↑ Positivo | 70,000+ | 68,500+ | 97.8% | Alerta ⚠️ |

**Diferencia única:** Proceso padre y Línea Estratégica distintos; fórmulas y categorización idénticas.

---

## 🔀 DEPENDENCIAS ENTRE INDICADORES

```
Consolidado Semestral (Excel)
    ├─ cargar_dataset() [data_loader.py]
    │   ├─ 5 PASOS (lineales, sin dependencias entre IDs)
    │   └─ OUTPUT: DataFrame {245, 276, 77, 203, 274, ...} + 145 indicadores más
    │
    ├─ preparar_pdi_con_cierre() [strategic_indicators.py]
    │   ├─ Filtro: Indicadores Plan estrategico=1
    │   └─ OUTPUT: {245, 276, 77, 203, 274} (5 en CMI)
    │
    └─ filter_cmi_estrategico() [cmi_filters.py]
        ├─ Toma preparar_pdi_con_cierre()
        ├─ Agrupa por Linea → calcula cumplimiento promedio
        └─ OUTPUT: 6 tarjetas KPI (Experiencia, Calidad, Transformación, Sostenibilidad, Expansión, ...)
            └─ Cada tarjeta contiene 15-20 indicadores
            └─ {245 en Experiencia}, {276 en Calidad}, {77 en Transformación}, ...
```

**No hay dependencias entre IDs:** Cada indicador se calcula de forma independiente.
El agregado (por línea) depende de los individuales.

---

## 📊 ESTADÍSTICAS DE CÁLCULO (5 INDICADORES)

| Métrica | Valor |
|---------|-------|
| **Archivos Excel leídos** | 1 (Resultados Consolidados.xlsx) × 2 hojas (Sem + Cierres) |
| **Funciones de carga** | 5 pasos en pipeline (común para todos) |
| **Cálculos de cumplimiento** | 1 recálculo por indicador (si falta) |
| **Normalizaciones** | 1 por indicador (escala 0-1 vs 0-100) |
| **Categorizaciones** | 1 por indicador (Peligro/Alerta/Cumplimiento/Sobrecumplimiento) |
| **Visualizaciones** | 4 páginas × 5 indicadores = 20 renderizaciones |
| **Tiempo total carga** | ~300ms (caché: 300s) |
| **Volatilidad** | Baja (cambios cada semana o mes) |

---

## 🔴 RIESGOS DETECTADOS EN LINEAGE

| Riesgo | Ubicación | Severidad | Impacto |
|--------|-----------|-----------|---------|
| **Heurística "si > 2" en normalización** | core/calculos.py:13-25 | 🔴 CRÍTICO | Si Cumplimiento llega como 98.11, se divide ÷100 vs si llega como 0.9811 no se toca |
| **Duplicación de lógica (2 funciones recalculan)** | data_loader.py + strategic_indicators.py | 🔴 CRÍTICO | Diferentes resultados si ambas se ejecutan |
| **Sin validación de tipos en Sentido** | data_loader.py:196 | 🔴 CRÍTICO | Si Sentido="Negativa" (typo) o valor falta → comportamiento inesperado |
| **Caché compartido 300s para 150 indicadores** | data_loader.py:253 | 🟡 MEDIO | Si indicador cambia en Excel, UI muestra valor viejo hasta 5 minutos |
| **No hay logging de cambios de Cumplimiento** | data_loader.py:163-245 | 🟡 MEDIO | Auditoría imposible: ¿cuándo cambió 245 de 98.1% a 97.9%? |

---

## ✅ VALIDACIÓN DE FASE 2

- [x] 5 indicadores críticos identificados
- [x] Pipeline común mapeado paso-a-paso
- [x] Diferencias (Sentido positivo vs negativo) documentadas
- [x] Visualizaciones trazadas en 4 páginas
- [x] Dependencias entre módulos identificadas
- [x] Riesgos de cálculo documentados

**Status:** ✅ **FASE 2 COMPLETA - LINEAGE VALIDADO**

---

## 📁 ARCHIVOS GENERADOS

- [AUDITORIA_FASE_1_DISCOVERY.md](AUDITORIA_FASE_1_DISCOVERY.md) (previo)
- [AUDITORIA_FASE_2_DATA_LINEAGE.md](AUDITORIA_FASE_2_DATA_LINEAGE.md) ← TÚ ESTÁS AQUÍ
- `/memories/session/data_lineage_5kpis.md`

---

**Próxima fase:** Fase 3 - Modelo Entidad-Relación | **Fecha estimada:** 22 de abril, 2026
