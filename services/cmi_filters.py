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


@st.cache_data(ttl=3600, show_spinner=False)
def load_cmi_worksheet() -> pd.DataFrame:
    """
    Carga la hoja Worksheet de Indicadores por CMI.xlsx.

    Returns:
        DataFrame con columnas: Id, Indicador, Indicadores Plan estrategico,
        Proyecto, Subprocesos, entre otras.
    """
    if not CMI_XLSX.exists():
        return pd.DataFrame()

    try:
        df = pd.read_excel(CMI_XLSX, sheet_name="Worksheet", engine="openpyxl")
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


def get_cmi_estrategico_ids() -> set[str]:
    """
    Retorna el conjunto de IDs de indicadores para CMI Estratégico.

    Criterio: Indicadores Plan estrategico == 1 AND Proyecto != 1
    """
    df = load_cmi_worksheet()
    if df.empty:
        return set()

    # Aplicar filtros
    mask = (df["Indicadores Plan estrategico"] == 1) & (df["Proyecto"] != 1)

    filtered = df[mask]

    # Limpiar IDs
    ids = set()
    if "Id" in filtered.columns:
        for val in filtered["Id"].dropna():
            try:
                # Convertir a entero si es posible
                if isinstance(val, float):
                    ids.add(str(int(val)))
                else:
                    ids.add(str(val).strip())
            except:
                ids.add(str(val).strip())

    return ids


def get_cmi_procesos_ids() -> set[str]:
    """
    Retorna el conjunto de IDs de indicadores para CMI por Procesos.

    Criterio: Subprocesos == 1
    """
    df = load_cmi_worksheet()
    if df.empty:
        return set()

    # Aplicar filtro
    mask = df["Subprocesos"] == 1
    filtered = df[mask]

    # Limpiar IDs
    ids = set()
    if "Id" in filtered.columns:
        for val in filtered["Id"].dropna():
            try:
                if isinstance(val, float):
                    ids.add(str(int(val)))
                else:
                    ids.add(str(val).strip())
            except:
                ids.add(str(val).strip())

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

    # Normalizar IDs en el DataFrame
    def normalize_id(val):
        if pd.isna(val):
            return ""
        try:
            if isinstance(val, float):
                return str(int(val))
            return str(val).strip()
        except:
            return str(val).strip()

    df_copy = df.copy()
    df_copy[f"{id_column}_norm"] = df_copy[id_column].apply(normalize_id)

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

    # Normalizar IDs
    def normalize_id(val):
        if pd.isna(val):
            return ""
        try:
            if isinstance(val, float):
                return str(int(val))
            return str(val).strip()
        except:
            return str(val).strip()

    df_copy = df.copy()
    df_copy[f"{id_column}_norm"] = df_copy[id_column].apply(normalize_id)

    filtered = df_copy[df_copy[f"{id_column}_norm"].isin(valid_ids)]
    return filtered.drop(columns=[f"{id_column}_norm"])
