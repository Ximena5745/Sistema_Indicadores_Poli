# Estandar Global de Formato: Meta y Ejecucion

Fecha: 15 de abril de 2026  
Estado: Vigente  
Alcance: Todas las fichas, tablas, graficas, tooltips y modales donde se muestren valores de Meta y Ejecucion.

## Objetivo

Definir y centralizar una unica logica de formateo para Meta y Ejecucion, evitando reglas duplicadas por pagina o componente.

La implementacion oficial esta en:

- `streamlit_app/utils/formatting.py`
  - `ejecucion_his_signo(row)`
  - `meta_his_signo(row)`
  - `formatear_meta_ejecucion_df(df, meta_col="Meta", ejec_col="Ejecucion")`

## Fuentes oficiales de Meta y Ejecucion

Meta y Ejecucion existen en 3 hojas oficiales del mismo archivo `data/output/Resultados Consolidados.xlsx`:

1. `Consolidado Historico`
2. `Consolidado Semestral`
3. `Consolidado Cierres`

Este estandar aplica a las 3 fuentes. La logica de formato es unica, independiente de la hoja de origen.

## Regla de trazabilidad por hoja fuente

Cada vista puede consumir una hoja distinta. Por lo tanto:

1. Siempre identificar y documentar la hoja fuente de la vista.
2. Formatear Meta/Ejecucion con los helpers globales sin duplicar reglas por pagina.
3. Si una vista mezcla datos de varias hojas, preservar la trazabilidad con un campo `HojaFuente` y aplicar el formato despues de consolidar.

### Matriz funcional oficial (fuente por vista)

Esta matriz define la hoja fuente oficial para Meta/Ejecucion segun funcionalidad:

1. `Gestion OM` -> `Consolidado Historico` (logica mensual).
2. `Resumen General` para `CMI estrategico` (corte diciembre 2025) -> `Consolidado Cierres`.
3. `Resumen General` para `CMI por procesos` (corte semestral) -> `Consolidado Semestral`.
4. `Resumen estrategico` / `CMI Estratégico` -> `Consolidado Cierres`.
5. Regla de corte para `CMI Estratégico`:
    - Años finalizados: `Diciembre`.
    - Años no finalizados: `Junio` mientras la fecha actual sea posterior al 20 de julio.
    - Si la fecha actual es igual o anterior al 20 de julio: `Diciembre`.
    - Fuente: `Consolidado Cierres`.
6. `Resumen por procesos` -> `Consolidado Historico`.

Nota: una pagina puede mostrar informacion derivada de otra capa; lo obligatorio es mantener clara la hoja origen de Meta/Ejecucion y aplicar el mismo formateo global.

## Script base aprobado

```python
def ejecucion_his_signo(row):
    ejec_s = row.get("Ejecución s")
    ejec = row.get("Ejecución", 0)
    dec_eje = row.get("DecimalesEje", 0)
    dec = row.get("Decimales", 0)

    # 1. Estados base
    if ejec_s == "Sin reporte":
        return "Pendiente"

    if ejec_s == "Linea Base":
        return "Linea Base"

    # 2. Enteros
    if ejec_s == "ENT":
        if ejec == 0:
            return "0"
        return f"{round(ejec):,}"

    # 3. Porcentaje o unidades tipo kWh
    if ejec_s in ["%", "kWh"]:
        if dec_eje > 0:
            value = round(ejec, dec_eje)
            return f"{value:,.{dec_eje}f}{ejec_s}"
        else:
            return f"{round(ejec):,}{ejec_s}"

    # 4. Moneda
    if ejec_s == "$":
        if dec > 0:
            value = round(ejec, dec_eje)
            return f"${value:,.{dec_eje}f}"
        else:
            return f"${round(ejec):,}"

    # 5. Decimal puro
    if ejec_s == "DEC":
        if dec > 0:
            value = round(ejec, dec_eje)
            return f"{value:,.{dec_eje}f}"
        else:
            return f"{round(ejec):,}"

    # 6. Unidades con sufijo separado
    if ejec_s in ["m3", "Kg", "tCO2e"]:
        return f"{round(ejec):,} {ejec_s}"

    # 7. Default
    if dec > 0:
        value = round(ejec, dec_eje)
        return f"{value:,.{dec_eje}f}"

    return f"{round(ejec):,}"
```

## Regla operativa global

1. No implementar formato local de Meta/Ejecucion en paginas o componentes.
2. Usar helpers centralizados de `streamlit_app/utils/formatting.py`.
3. Para DataFrames, usar `formatear_meta_ejecucion_df(...)` antes de renderizar.
4. Para cards/modales con diccionarios, usar `meta_his_signo(...)` y `ejecucion_his_signo(...)`.
5. El origen (`Consolidado Historico`, `Consolidado Semestral`, `Consolidado Cierres`) no cambia la logica de formato; solo cambia la procedencia del dato.

## Mapeo de campos soportados

La implementacion global contempla variantes de nombres de columna para robustez:

- Signo ejecucion: `Ejecución s`, `Ejecucion s`, `Ejecucion_s`, `Ejecucion_Signo`, `EjecS`
- Signo meta: `Meta s`, `Meta_Signo`, `MetaS`
- Valor ejecucion: `Ejecución`, `Ejecucion`
- Valor meta: `Meta`
- Decimales ejecucion: `DecimalesEje`, `Decimales_Ejecucion`, `DecEjec`
- Decimales meta: `Decimales`, `Decimales_Meta`, `DecMeta`

## Componentes y paginas que ya usan este estandar

- `streamlit_app/pages/cmi_estrategico.py`
- `streamlit_app/pages/plan_mejoramiento.py`
- `streamlit_app/pages/gestion_om.py`
- `streamlit_app/pages/resumen_por_proceso.py`
- `streamlit_app/pages/pdi_acreditacion.py`
- `streamlit_app/components/interactive_cards.py`
- `streamlit_app/components/modals.py`
- `components/charts.py`

## Mantenimiento

Cuando se agregue una nueva vista que muestre Meta/Ejecucion:

1. Importar los helpers globales desde `streamlit_app/utils/formatting.py`.
2. Evitar formatos ad-hoc con f-strings locales para Meta/Ejecucion.
3. Validar los casos de signo: `Sin reporte`, `Linea Base`, `ENT`, `%`, `kWh`, `$`, `DEC`, `m3`, `Kg`, `tCO2e`.
