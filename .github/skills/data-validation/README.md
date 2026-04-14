# Data Validation Skill

Este skill proporciona lógica reutilizable para validar y enriquecer datasets usando fuentes de datos oficiales, particularmente `Subproceso-Proceso-Area.xlsx` como fuente maestra de jerarquías de procesos.

## Estructura del Skill

```
.github/skills/data-validation/
├── SKILL.md                    # Documentación del skill
├── data_validation.py          # Funciones reutilizables
├── test_validation.py          # Pruebas unitarias
└── README.md                   # Esta documentación
```

## Funciones Principales

### `enrich_with_process_hierarchy(df, excel_path)`

Enriquece un dataset con la jerarquía oficial de procesos desde `Subproceso-Proceso-Area.xlsx`.

**Parámetros:**
- `df`: DataFrame con columna 'Subproceso'
- `excel_path`: Ruta al archivo Excel de referencia

**Retorna:** DataFrame enriquecido con columnas 'Proceso', 'Unidad', 'Tipo de proceso'

### `validate_process_sources(dataset_df, excel_path)`

Valida que los procesos del dataset coincidan con la fuente oficial.

**Retorna:** Diccionario con resultados de validación incluyendo:
- Cantidad de procesos en cada fuente
- Procesos faltantes/extras
- Estado de consistencia

### `get_process_filter_options(dataset_df)`

Genera opciones validadas para filtros de UI relacionados con procesos.

**Retorna:** Diccionario con listas de opciones para filtros

### `apply_process_filters(df, filters)`

Aplica filtros relacionados con procesos al dataset.

## Uso en el Proyecto

### Integración en Data Loader

```python
# En services/data_loader.py
from data_validation import enrich_with_process_hierarchy

@st.cache_data
def cargar_dataset():
    # ... lógica de carga existente ...
    df = enrich_with_process_hierarchy(df, DATA_RAW / "Subproceso-Proceso-Area.xlsx")
    return df
```

### Validación de Datos

```python
# Validar fuentes de datos
from data_validation import validate_process_sources

result = validate_process_sources(df, DATA_RAW / "Subproceso-Proceso-Area.xlsx")
if not result["validation_passed"]:
    st.warning(f"Faltan {len(result['missing_processes_in_dataset'])} procesos en el dataset")
```

### Filtros en UI

```python
# Generar opciones de filtro
from data_validation import get_process_filter_options, apply_process_filters

options = get_process_filter_options(df)
proceso_sel = st.selectbox("Proceso", options["procesos"])

# Aplicar filtros
filters = {"proceso": proceso_sel}
df_filtrado = apply_process_filters(df, filters)
```

## Jerarquía de Procesos

El skill implementa la jerarquía oficial:
- **Proceso** = Padre (nivel superior)
- **Subproceso** = Hijo (nivel inferior)

Esta relación se mantiene consistente en todo el sistema.

## Dependencias

- pandas
- openpyxl
- pathlib
- streamlit (para feedback en UI)

## Pruebas

Ejecutar las pruebas unitarias:

```bash
cd .github/skills/data-validation
python test_validation.py
```

## Mantenimiento

- Actualizar el skill cuando se agreguen nuevas fuentes de referencia
- Mantener la documentación sincronizada con los cambios
- Ejecutar pruebas después de modificaciones
- Validar que la jerarquía padre-hijo se mantenga correcta