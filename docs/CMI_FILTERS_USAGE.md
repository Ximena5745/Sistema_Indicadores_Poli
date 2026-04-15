# Uso de CMI Filters - Módulo Global

Este documento explica cómo usar el módulo `services/cmi_filters.py` en todo el proyecto.

## 📋 Reglas de Negocio

Basado en: `data/raw/Indicadores por CMI.xlsx` · Hoja `Worksheet`

### CMI Estratégico
- **Criterio**: `Indicadores Plan estrategico == 1` AND `Proyecto != 1`
- **Total de indicadores**: ~53

### CMI por Procesos  
- **Criterio**: `Subprocesos == 1`
- **Total de indicadores**: ~494

---

## 🚀 Ejemplos de Uso

### 1. Filtrar un DataFrame completo

```python
from services.cmi_filters import filter_df_for_cmi_estrategico, filter_df_for_cmi_procesos

# Filtrar para CMI Estratégico
df_estrategico = filter_df_for_cmi_estrategico(df, id_column="Id")

# Filtrar para CMI por Procesos
df_procesos = filter_df_for_cmi_procesos(df, id_column="Id")
```

### 2. Obtener IDs válidos

```python
from services.cmi_filters import get_cmi_estrategico_ids, get_cmi_procesos_ids

# Obtener conjunto de IDs válidos
ids_estrategico = get_cmi_estrategico_ids()  # retorna set de strings
ids_procesos = get_cmi_procesos_ids()        # retorna set de strings

# Verificar si un indicador pertenece a un CMI
if str(indicador_id) in ids_estrategico:
    print("Es un indicador estratégico")
```

### 3. Uso en páginas de Streamlit

```python
# En streamlit_app/pages/cmi_estrategico.py
from services.cmi_filters import filter_df_for_cmi_estrategico

def render():
    # ... obtener datos ...
    df = preparar_pdi_con_cierre(anio, mes)
    
    # Aplicar filtro autoritativo
    df = filter_df_for_cmi_estrategico(df, id_column="Id")
    
    # ... continuar con visualizaciones ...
```

---

## 📁 Archivos que usan este módulo

- ✅ `streamlit_app/pages/cmi_estrategico.py` - Aplica filtro de CMI Estratégico
- 🔄 `streamlit_app/pages/resumen_general.py` - Pendiente integración
- 🔄 `streamlit_app/pages/resumen_por_proceso.py` - Pendiente integración

---

## ⚙️ Características Técnicas

- **Cache**: Usa `@st.cache_data(ttl=3600)` para evitar lecturas repetidas del Excel
- **Normalización de IDs**: Convierte automáticamente floats a int antes de string
- **Seguridad**: Retorna DataFrames/sets vacíos en caso de error
- **Ubicación**: `services/cmi_filters.py` (global, puede importarse desde cualquier módulo)

---

## 🔍 Funciones Disponibles

| Función | Retorno | Descripción |
|---------|---------|-------------|
| `load_cmi_worksheet()` | `pd.DataFrame` | Carga hoja Worksheet del Excel |
| `get_cmi_estrategico_ids()` | `set[str]` | IDs de CMI Estratégico |
| `get_cmi_procesos_ids()` | `set[str]` | IDs de CMI por Procesos |
| `filter_df_for_cmi_estrategico(df, id_column)` | `pd.DataFrame` | Filtra DataFrame para CMI Estratégico |
| `filter_df_for_cmi_procesos(df, id_column)` | `pd.DataFrame` | Filtra DataFrame para CMI por Procesos |

---

## 📝 Notas Importantes

1. **IDs como strings**: Todos los IDs se manejan como strings para evitar problemas de comparación
2. **Columna ID**: Por defecto asume `"Id"`, pero se puede especificar otra columna
3. **Datos source**: El archivo Excel debe existir en `data/raw/Indicadores por CMI.xlsx`
4. **Hoja requerida**: `Worksheet` (case-sensitive)

---

## 🐛 Troubleshooting

### Error: "No se encuentra el archivo"
- Verifica que existe `data/raw/Indicadores por CMI.xlsx`
- Verifica que la hoja se llama exactamente `Worksheet`

### No retorna registros
- Verifica que las columnas existan: `Indicadores Plan estrategico`, `Proyecto`, `Subprocesos`
- Verifica que los valores sean exactamente `1` (no `1.0` como texto)

### IDs no coinciden
- Los IDs se normalizan automáticamente, pero asegúrate de usar strings en comparaciones
- Ejemplo correcto: `if str(my_id) in get_cmi_estrategico_ids()`
