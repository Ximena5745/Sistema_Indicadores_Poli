"""
services/cmi_filters/filters.py
===============================

CMI filtering logic (Estratégico vs Procesos).

Responsibility: Implement business rules for CMI filtering.
"""

from typing import Optional

import pandas as pd

from .loaders import load_cmi_worksheet, load_kawak_active_ids
from .utils import _normalize_flag_series, _normalize_id_value


# ============================================================================
# ID GETTERS
# ============================================================================


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


# ============================================================================
# DATAFRAME FILTERS
# ============================================================================


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
        year: Año para validar activos en Kawak
        omit_if_no_cross: Si no hay cruce Kawak, retorna vacío
        use_kawak_cross: Si es False, omite la validación anual de Kawak

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
    map_df: Optional[pd.DataFrame] = None,
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
        omit_if_no_cross: Si no hay cruce Kawak, retorna vacío
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

    if map_df is not None and not map_df.empty and not filtered.empty:
        valid_subprocesos = get_cmi_procesos_subprocesos(map_df)
        if valid_subprocesos and "Subproceso" in filtered.columns:
            filtered = filtered[
                filtered["Subproceso"].astype(str).str.strip().isin(valid_subprocesos)
            ]

    return filtered
