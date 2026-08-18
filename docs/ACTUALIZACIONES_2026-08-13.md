# Actualizaciones de Indicadores — 2026-08-13

**Fecha de implementación:** 12-13 de agosto de 2026
**Cambios:** 3 correcciones al ETL — extracción de cronograma de proyectos 2026, purga que borraba datos reales, y decimales de visualización inconsistentes
**Archivos modificados:** 3 (`builders.py`, `purga.py`, `signos.py`) + recuperación/recálculo puntual de datos en `Resultados Consolidados.xlsx`

---

## 📋 Resumen de Cambios

### 1️⃣ Avance real/esperado de proyectos 2026 vacío (símbolos de variable cambiaron) ✅

**Síntoma reportado:** varios proyectos estratégicos de 2026 (PRY-26…PRY-54) no mostraban avance
esperado ni avance real, aunque el dato sí existía en la fuente.

**Causa raíz:**
`extraer_cronograma_proyectos()` en `scripts/etl/builders.py` tenía hardcodeados los símbolos de
variable `PARPR` (avance real) / `PAEPR` (avance esperado) para **todos** los años. Kawak cambió
esos símbolos para el indicador padre de 2026 (id 603) a `PARPRO`/`PAEPROY`. Como el código seguía
buscando `PARPR`/`PAEPR`, la búsqueda fallaba siempre para 2026 y el registro quedaba
`Meta=None, Ejecucion=None, es_na=True` — sin caer a `serie["resultado"]`/`serie["meta"]` por
diseño (esos campos no son el avance real: ver `docs/LOGICA_INDICADORES_ESPECIALES.md` §4).

**Dónde está implementado:**
- `scripts/etl/builders.py` → nuevo mapa `_SIMBOLOS_CRONOGRAMA_PROYECTOS: Dict[str, Tuple[str,str]]`
  (mismo patrón que `_SIMBOLOS_PLAN_ANUAL`), con una entrada por `id_padre`:
  - `"441"` (2024) → `("PARPR", "PAEPR")`
  - `"509"` (2025) → `("PARPR", "PAEPR")`
  - `"603"` (2026) → `("PARPRO", "PAEPROY")`
- `extraer_cronograma_proyectos()` ahora resuelve el par de símbolos por `id_padre` de la fila en
  vez de usar un par fijo global.

**Indicadores afectados:** 13 proyectos activos en 2026 (PRY-26, PRY-27, PRY-28, PRY-30, PRY-31,
PRY-32, PRY-36, PRY-40, PRY-42, PRY-51, PRY-52, PRY-53, PRY-54) — 52 registros mensuales
(abril-julio 2026) recuperados al re-ejecutar el pipeline.

**Documentación actualizada:**
- ✅ `docs/LOGICA_INDICADORES_ESPECIALES.md` — §4 "Cronograma de proyectos estratégicos": lógica de
  extracción actualizada (ya no dice `Ejecucion = serie.resultado`), tabla de símbolos por año y
  nota de alerta sobre el cambio de símbolos.

**Nota para el futuro:** si Kawak vuelve a cambiar los símbolos de variable para un año nuevo,
agregar la entrada correspondiente a `_SIMBOLOS_CRONOGRAMA_PROYECTOS` — no asumir que el par por
defecto (`PARPR`/`PAEPR`) sigue vigente.

---

### 2️⃣ Purga de filas "fuera del catálogo Kawak" borraba datos reales de años sin API ✅

**Síntoma reportado:** indicadores que sí tenían dato cargado para 2022 en la fuente original
(`data/raw/Resultados_Consolidados_Fuente.xlsx`) aparecían vacíos para 2022 en
`Resultados Consolidados.xlsx` — sin relación con el cambio del punto 1.

**Causa raíz:**
`purgar_filas_invalidas()` en `scripts/etl/purga.py` (paso 7 del pipeline) elimina filas cuyo par
`(Id, año)` no existe en el catálogo `Indicadores Kawak.xlsx` (reconstruido cada corrida desde
`data/raw/API/{año}.xlsx`). A diferencia de la función vecina `purgar_filas_antes_fecha_desde()`
—que solo borra si Meta **y** Ejecución están vacías—, esta función no verificaba si la fila tenía
dato real antes de borrarla.

Varios indicadores empezaron a reportarse por la API/Kawak recién en 2023 (ej. 323, 276, 423), pero
sí tenían valores cargados manualmente para 2022 en la fuente original del pipeline. Como
`Resultados Consolidados.xlsx` nunca se re-siembra desde esa fuente en corridas posteriores —el
pipeline solo actualiza incrementalmente el propio archivo de salida—, una vez que la purga borró
esas filas (en una corrida anterior a cualquier backup disponible) quedaron perdidas
permanentemente en cada corrida siguiente.

**Alcance verificado:** 631 filas con dato real, en las 3 hojas, coincidían exactamente con este
patrón (`(Id, año)` fuera del catálogo Kawak **y** con Meta/Ejecución reales, años 2022-2026):
266 en Consolidado Histórico, 228 en Semestral, 137 en Cierres.

> Se detectaron además otras ~250-400 filas por hoja presentes en la fuente original pero ausentes
> del consolidado que **no** calzan con este mecanismo (mayormente IDs `PRY-x` de proyectos y otros
> indicadores recalculados por lógica de builders más nueva) — esas **no** se tocaron porque su
> ausencia puede ser un recálculo intencional y restaurarlas a ciegas podría reintroducir valores
> obsoletos. Quedan pendientes de revisión aparte si se necesita.

**Dónde está implementado:**
- `scripts/etl/purga.py` → `purgar_filas_invalidas()`: la condición de purga por catálogo Kawak
  ahora exige además que Meta y Ejecución estén ambas vacías/0 (mismo helper `_vacio()` que ya usa
  `purgar_filas_antes_fecha_desde()`), antes de borrar la fila.
- Recuperación puntual (una sola vez, no forma parte del pipeline recurrente): script ad-hoc que
  reinsertó en `Resultados Consolidados.xlsx` las 631 filas identificadas arriba, tomando el valor
  desde `data/raw/Resultados_Consolidados_Fuente.xlsx` (`INPUT_FILE`), y luego se re-ejecutó el
  pipeline completo para que los pasos de reparación existentes (signos, fórmulas, deduplicación)
  normalizaran esas filas igual que cualquier otra.

**Documentación actualizada:**
- ✅ `docs/core/09_ETL_Pipeline.md` — tabla de fases internas, paso 7: aclara que la purga por
  catálogo Kawak ahora es "sin dato real", igual que la purga por Fecha Desde.

---

### 3️⃣ Decimales de Meta/Ejecución inconsistentes — valores decimales mostrados como enteros ✅

**Síntoma reportado:** el indicador 332 "Índice de rotación" (valores tipo 0.98, 1.30) se mostraba
redondeado a entero en los períodos de 2025-2026, aunque el dato real sí tenía decimales.

**Causa raíz:**
`obtener_signos()` en `scripts/etl/signos.py` (usada para decidir cuántos decimales mostrar al
escribir filas nuevas) leía las 3 hojas en orden fijo Histórico → Semestral → Cierres y dejaba que
la hoja procesada **al final** sobrescribiera sin condición el valor de `Decimales_Meta`/
`Decimales_Ejecucion` de las anteriores — sin comparar fechas ni validar el valor. Para el
indicador 332, `Consolidado Cierres` tenía `Decimales_Ejecucion=0` desde su primer registro en
2022 (un defecto de origen independiente, ya antiguo, en cómo Cierres nunca llegó a setear bien
sus propios decimales). Como Cierres se procesa último, ese `0` terminaba ganando siempre y
"envenenaba" los decimales usados al escribir filas nuevas en Histórico/Semestral — por eso 2022-
2024 (escritas antes de que este mecanismo tomara el control) se veían bien con 2 decimales, y
2025-2026 (escritas después) quedaron en 0.

**Alcance verificado:** 203 indicadores con el mismo patrón — Ejecución genuinamente decimal en su
período más reciente pero `Decimales_Ejecucion=0` — incluyendo el bloque "Nivel de Satisfacción
Servicios Prestados" (108.1-108.15), varios "% de..." y "Cumplimiento...".

**Dónde está implementado:**
- `scripts/etl/signos.py` → `obtener_signos()`: `dec_meta`/`dec_ejec` ya no siguen la regla
  "última hoja procesada gana"; se calculan como la **moda de los valores no-cero** vistos para ese
  Id en cualquier fila de cualquier hoja. `0` es el valor default pasivo que usa `escribir_filas`
  cuando no sabe nada — no una señal real de "0 decimales" — así que solo se usa si nunca se vio
  otro valor para ese Id (evita fabricar una precisión que nunca existió: indicadores como el 410 y
  el 345, que **siempre** tuvieron `Decimales_Ejecucion=0` en las 3 hojas, se dejaron intactos en 0
  a propósito, aunque su Ejecución también sea decimal — no hay evidencia de qué precisión
  correspondía).
- Recálculo puntual (una sola vez): script ad-hoc que recalculó `Decimales_Meta`/
  `Decimales_Ejecucion` en las 3 hojas de `Resultados Consolidados.xlsx` con la misma lógica de
  moda — 2,000 celdas corregidas (1,017 Histórico, 549 Semestral, 434 Cierres) — y luego se
  re-ejecutó el pipeline completo para confirmar estabilidad.

---

## 🔍 Cómo verificar

```python
import pandas as pd
df = pd.read_excel("data/output/Resultados Consolidados.xlsx", sheet_name="Consolidado Historico")
df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
df["Id"] = df["Id"].astype(str)

# Proyectos 2026 (punto 1)
print(df[(df["Id"].isin(["PRY-31", "PRY-42"])) & (df["Fecha"].dt.year == 2026)]
      [["Id", "Fecha", "Meta", "Ejecucion"]])

# 2022 recuperado (punto 2)
print(df[(df["Id"].isin(["323", "276", "423"])) & (df["Fecha"].dt.year == 2022)]
      [["Id", "Fecha", "Meta", "Ejecucion"]])

# Decimales consistentes (punto 3)
print(df[df["Id"] == "332"]
      [["Id", "Fecha", "Meta", "Ejecucion", "Decimales_Meta", "Decimales_Ejecucion"]])
```
