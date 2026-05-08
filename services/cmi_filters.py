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
import re
from typing import Optional

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
CMI_XLSX = ROOT / "data" / "raw" / "Indicadores por CMI.xlsx"


@st.cache_data(ttl=3600, show_spinner=False)
def load_kawak_active_ids(year: Optional[int] = None) -> set[str]:
    """
    Carga los IDs activos reportados por Kawak para un año dado.

    Busca en la carpeta `data/raw/Fuentes Consolidadas/` archivos Excel
    (p.ej. `Consolidado_API_Kawak.xlsx`, `Indicadores Kawak.xlsx`) y extrae
    la columna `Id` (o variantes). Si `year` es provisto, filtra por la
    columna `Anio`/`Año`/`Year` cuando exista, o intenta inferir el año
    desde el nombre del archivo (ej. "Consolidado_API_Kawak_2024.xlsx").

    Returns:
        set de IDs normalizados (strings)
    """
    folder = ROOT / "data" / "raw" / "Fuentes Consolidadas"
    if not folder.exists():
        return set()

    ids: set[str] = set()
    for f in folder.glob("*.xlsx"):
        try:
            df_k = pd.read_excel(f, engine="openpyxl")
            if df_k.empty:
                continue

            # Detectar columna de Id (case-insensitive)
            id_col = None
            for c in df_k.columns:
                if str(c).strip().lower() in ("id", "id_indicador", "idindicador"):
                    id_col = c
                    break
            if id_col is None:
                continue

            # Filtrar por año si se solicita
            if year is not None:
                year_col = None
                for yc in df_k.columns:
                    if str(yc).strip().lower() in ("anio", "año", "year"):
                        year_col = yc
                        break
                if year_col is not None:
                    df_k = df_k[pd.to_numeric(df_k[year_col], errors="coerce").fillna(0).astype(int) == int(year)]
                else:
                    # intentar inferir año desde el nombre de archivo
                    m = re.search(r"(20\d{2})", f.name)
                    if m:
                        file_year = int(m.group(1))
                        if file_year != int(year):
                            continue

            for val in df_k[id_col].dropna():
                ids.add(_normalize_id_value(val))
        except Exception:
            # no detener el proceso si un archivo falla
            continue

    return ids


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


def get_cmi_procesos_ids(
    year: Optional[int] = None,
    omit_if_no_cross: bool = True,
    use_kawak_cross: bool = True,
) -> set[str]:
    """
    Retorna el conjunto de IDs de indicadores para CMI por Procesos.

    Nueva lógica (oficial):
    - Base: `Subprocesos == 1` en `Indicadores por CMI.xlsx`.
    - `Ind act` queda deprecado y ya no se usa.
    - Si se provee `year` y `use_kawak_cross` es True, se realiza un cruce con
      los IDs reportados por Kawak para ese año (carpeta `data/raw/Fuentes Consolidadas/`).
      Si el cruce no arroja resultados y `omit_if_no_cross` es True,
      la función retorna un conjunto vacío (se omiten esos indicadores).
    """
    df = load_cmi_worksheet()
    if df.empty:
        return set()

    # Verificar columnas necesarias
    required_columns = ["Subprocesos", "Id"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Error: Faltan las columnas requeridas {missing_columns} en 'Indicadores por CMI.xlsx'.")
        return set()

    flag_subprocesos = _normalize_flag_series(df["Subprocesos"])
    filtered = df[flag_subprocesos == 1]

    # Limpiar IDs base
    base_ids: set[str] = set()
    if "Id" in filtered.columns:
        for val in filtered["Id"].dropna():
            base_ids.add(_normalize_id_value(val))

    # Si no se especifica año, retornar base_ids (comportamiento por compatibilidad)
    if year is None:
        return base_ids

    if year is None or not use_kawak_cross:
        return base_ids

    # Si se especifica año, cruzar con Kawak
    kawak_ids = load_kawak_active_ids(year)
    if not kawak_ids:
        if omit_if_no_cross:
            return set()
        return base_ids

    intersect = base_ids.intersection(kawak_ids)
    if intersect:
        return intersect
    if omit_if_no_cross:
        return set()
    return base_ids


def get_cmi_procesos_subprocesos(map_df: pd.DataFrame) -> set[str]:
    """
    Retorna el conjunto de subprocesos válidos para CMI por Procesos
    según el catálogo de Indicadores por CMI.xlsx y el mapeo maestro.
    """
    if map_df.empty:
        return set()

    cmi_df = load_cmi_worksheet()
    if cmi_df.empty or "Subprocesos" not in cmi_df.columns or "Subproceso" not in cmi_df.columns:
        return set()

    subprocesos_cmi = set(
        cmi_df.loc[_normalize_flag_series(cmi_df["Subprocesos"]) == 1, "Subproceso"]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
    )

    subprocesos_map = set(
        map_df["Subproceso"].dropna().astype(str).str.strip().tolist()
    ) if "Subproceso" in map_df.columns else set()

    return subprocesos_cmi & subprocesos_map


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


def filter_df_for_cmi_procesos(
    df: pd.DataFrame,
    id_column: str = "Id",
    year: Optional[int] = None,
    omit_if_no_cross: bool = True,
    use_kawak_cross: bool = True,
) -> pd.DataFrame:
    """
    Filtra un DataFrame para quedarse solo con indicadores de CMI por Procesos.

    Reglas oficiales:
    - Base: `Subprocesos == 1` en `Indicadores por CMI.xlsx`
    - `Ind act` está deprecado y no se usa como criterio de inclusión
    - Si `year` se pasa y `use_kawak_cross` es True, se valida el Id contra Kawak

    Args:
        df: DataFrame a filtrar
        id_column: Nombre de la columna que contiene el ID del indicador

    Returns:
        DataFrame filtrado
    """
    if df.empty or id_column not in df.columns:
        return df

    year_to_use = year

    valid_ids = get_cmi_procesos_ids(
        year=year_to_use,
        omit_if_no_cross=omit_if_no_cross,
        use_kawak_cross=use_kawak_cross,
    )
    if not valid_ids:
        if omit_if_no_cross:
            # retornar DataFrame vacío con mismas columnas para indicar que no hay indicadores activos
            return df.iloc[0:0]
        return df

    df_copy = df.copy()
    df_copy[f"{id_column}_norm"] = df_copy[id_column].apply(_normalize_id_value)

    filtered = df_copy[df_copy[f"{id_column}_norm"].isin(valid_ids)]
    return filtered.drop(columns=[f"{id_column}_norm"])


def filter_df_for_procesos(
    df: pd.DataFrame,
    id_column: str = "Id",
    year: Optional[int] = None,
    omit_if_no_cross: bool = True,
    use_kawak_cross: bool = True,
    map_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Alias estándar para el filtro de indicadores de CMI por Procesos.

    Esta función aplica la regla oficial de selección:
    - `Subprocesos == 1` para identificar los candidatos de CMI por Procesos
    - Si `year` se pasa, valida los IDs activos contra Kawak para ese año
    - Si `map_df` se provee, cruza subprocesos autorizados contra el mapeo maestro

    Args:
        df: DataFrame a filtrar
        id_column: Nombre de la columna que contiene el ID del indicador
        year: Año para validar activos en Kawak
        omit_if_no_cross: Si no hay cruce Kawak, retorna vacío cuando es True
        use_kawak_cross: Si es False, omite la validación anual de Kawak
        map_df: DataFrame maestro de mapeo de subprocesos/procesos

    Returns:
        DataFrame filtrado
    """
    filtered = filter_df_for_cmi_procesos(
        df,
        id_column=id_column,
        year=year,
        omit_if_no_cross=omit_if_no_cross,
        use_kawak_cross=use_kawak_cross,
    )

    if filtered.empty or map_df is None or "Subproceso" not in filtered.columns:
        return filtered

    valid_subs = get_cmi_procesos_subprocesos(map_df)
    if not valid_subs:
        return filtered

    filtered = filtered[filtered["Subproceso"].astype(str).str.strip().isin(valid_subs)].copy()
    return filtered
