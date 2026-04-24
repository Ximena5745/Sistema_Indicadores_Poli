"""
services/cmi_filters.py — Lógica de filtrado GLOBAL para CMI Estratégico vs CMI por Procesos

═══════════════════════════════════════════════════════════════════════════════
DOCUMENTACIÓN DE USO
═══════════════════════════════════════════════════════════════════════════════

Basado en: data/raw/Indicadores por CMI.xlsx · Hoja Worksheet

REGLAS DE NEGOCIO (fuente autoritativa):
----------------------------------------------
1. CMI Estratégico:
   - Indicadores Plan estrategico == 1
   - AND Proyecto != 1

2. CMI por Procesos:
   - Subprocesos == 1

EJEMPLO DE USO:
----------------------------------------------
```python
from services.cmi_filters import (
    filter_df_for_cmi_estrategico,
    filter_df_for_cmi_procesos,
    get_cmi_estrategico_ids,
    get_cmi_procesos_ids
)

# Opción 1: Filtrar un DataFrame completo
df_estrategico = filter_df_for_cmi_estrategico(df, id_column="Id")
df_procesos = filter_df_for_cmi_procesos(df, id_column="Id")

# Opción 2: Obtener solo los IDs válidos
ids_estrategico = get_cmi_estrategico_ids()  # retorna set de strings
ids_procesos = get_cmi_procesos_ids()        # retorna set de strings

# Ejemplo: verificar si un indicador pertenece a CMI Estratégico
if str(indicador_id) in get_cmi_estrategico_ids():
    print("Es un indicador estratégico")
```

NOTAS IMPORTANTES:
----------------------------------------------
- Los IDs se normalizan automáticamente a strings
- Los valores float se convierten a int antes de convertir a string
- El cache de Streamlit se usa para evitar lecturas repetidas del Excel
- Las funciones son seguras: retornan DataFrames/sets vacíos si hay errores

═══════════════════════════════════════════════════════════════════════════════
"""

from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
CMI_XLSX = ROOT / "data" / "raw" / "Indicadores por CMI.xlsx"


def _normalize_flag_series(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.isna().any():
        raw = series.astype(str).str.strip().str.lower()
        mapped = raw.map(
            {
                "1": 1,
                "1.0": 1,
                "si": 1,
                "true": 1,
                "x": 1,
                "0": 0,
                "0.0": 0,
                "no": 0,
                "false": 0,
                "": 0,
            }
        )
        numeric = numeric.fillna(mapped)
    return numeric


def _normalize_id_value(val) -> str:
    if pd.isna(val):
        return ""
    if isinstance(val, int):
        return str(val)
    if isinstance(val, float):
        return str(int(val)) if val.is_integer() else str(val).strip()
    text = str(val).strip()
    try:
        num = float(text)
        if num.is_integer():
            return str(int(num))
    except Exception:
        return text
    return text


@st.cache_data(ttl=3600, show_spinner=False)
def load_cmi_worksheet() -> pd.DataFrame:
    """
    Carga la hoja Worksheet de Indicadores por CMI.xlsx.

    Returns:
        DataFrame con columnas: Id, Indicador, Indicadores Plan estrategico,
        Proyecto, Subprocesos, entre otras.
    """
    if not CMI_XLSX.exists():
        print("Error: El archivo 'Indicadores por CMI.xlsx' no existe en la ruta esperada.")
        return pd.DataFrame()

    try:
        df = pd.read_excel(CMI_XLSX, sheet_name="Worksheet", engine="openpyxl")
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        print(f"Error al cargar la hoja 'Worksheet': {e}")
        return pd.DataFrame()


def get_cmi_estrategico_ids() -> set[str]:
    """
    Retorna el conjunto de IDs de indicadores para CMI Estratégico.

    Criterio: Indicadores Plan estrategico == 1 AND Proyecto != 1
    """
    df = load_cmi_worksheet()
    if df.empty:
        print("Advertencia: El DataFrame cargado desde 'Indicadores por CMI.xlsx' está vacío.")
        return set()

    # Verificar columnas necesarias
    required_columns = ["Indicadores Plan estrategico", "Proyecto", "Id"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Error: Faltan las columnas requeridas {missing_columns} en 'Indicadores por CMI.xlsx'.")
        return set()

    # Aplicar filtros con normalizacion de banderas
    flag_estrategico = _normalize_flag_series(df["Indicadores Plan estrategico"])
    flag_proyecto = _normalize_flag_series(df["Proyecto"])
    mask = (flag_estrategico == 1) & (flag_proyecto != 1)

    filtered = df[mask]

    # Limpiar IDs
    ids = set()
    if "Id" in filtered.columns:
        for val in filtered["Id"].dropna():
            ids.add(_normalize_id_value(val))

    if not ids:
        print("Advertencia: No se encontraron IDs válidos para CMI Estratégico.")

    return ids


def get_cmi_procesos_ids() -> set[str]:
    """
    Retorna el conjunto de IDs de indicadores para CMI por Procesos.

    Criterio: Subprocesos == 1 Y 'Ind act' == 1
    """
    df = load_cmi_worksheet()
    if df.empty:
        return set()

    # Verificar columnas necesarias
    required_columns = ["Subprocesos", "Ind act", "Id"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Error: Faltan las columnas requeridas {missing_columns} en 'Indicadores por CMI.xlsx'.")
        return set()

    # Aplicar filtro con normalización de banderas
    flag_subprocesos = _normalize_flag_series(df["Subprocesos"])
    flag_ind_act = _normalize_flag_series(df["Ind act"])
    mask = (flag_subprocesos == 1) & (flag_ind_act == 1)
    filtered = df[mask]

    # Limpiar IDs
    ids = set()
    if "Id" in filtered.columns:
        for val in filtered["Id"].dropna():
            ids.add(_normalize_id_value(val))

    return ids


def filter_df_for_cmi_estrategico(df: pd.DataFrame, id_column: str = "Id") -> pd.DataFrame:
    """
    Filtra un DataFrame para quedarse solo con indicadores de CMI Estratégico.

    Args:
        df: DataFrame a filtrar
        id_column: Nombre de la columna que contiene el ID del indicador

    Returns:
        DataFrame filtrado
    """
    if df.empty or id_column not in df.columns:
        return df

    valid_ids = get_cmi_estrategico_ids()
    if not valid_ids:
        return df

    # Validación adicional para inspeccionar los IDs obtenidos
    print("IDs válidos obtenidos para CMI Estratégico:", valid_ids)

    df_copy = df.copy()
    df_copy[f"{id_column}_norm"] = df_copy[id_column].apply(_normalize_id_value)

    filtered = df_copy[df_copy[f"{id_column}_norm"].isin(valid_ids)]
    return filtered.drop(columns=[f"{id_column}_norm"])


def filter_df_for_cmi_procesos(df: pd.DataFrame, id_column: str = "Id") -> pd.DataFrame:
    """
    Filtra un DataFrame para quedarse solo con indicadores de CMI por Procesos.

    Args:
        df: DataFrame a filtrar
        id_column: Nombre de la columna que contiene el ID del indicador

    Returns:
        DataFrame filtrado
    """
    if df.empty or id_column not in df.columns:
        return df

    valid_ids = get_cmi_procesos_ids()
    if not valid_ids:
        return df

    df_copy = df.copy()
    df_copy[f"{id_column}_norm"] = df_copy[id_column].apply(_normalize_id_value)

    filtered = df_copy[df_copy[f"{id_column}_norm"].isin(valid_ids)]
    return filtered.drop(columns=[f"{id_column}_norm"])
