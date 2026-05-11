"""
Utility functions for cmi_estrategico_tabulado page.
"""

from datetime import date as _date
import pandas as pd


def default_anio(anios: list[int]) -> int:
    """
    Get default year for CMI page.
    
    Prefers 2025 if available, else most recent year, else current year.
    
    Args:
        anios: List of available years
        
    Returns:
        Default year as integer
    """
    if 2025 in anios:
        return 2025
    if anios:
        return anios[-1]
    return _date.today().year


def default_corte(anio: int | None) -> str:
    """
    Get default corte (semester) for CMI page.
    
    Logic:
    - If anio < current year: return "Diciembre" (full year)
    - If anio == current year:
      - If today > July 20: return "Junio"
      - Else: return "Diciembre"
    
    Args:
        anio: Year to calculate corte for
        
    Returns:
        Corte as string ("Junio" or "Diciembre")
    """
    if anio is None:
        return "Diciembre"
    today = _date.today()
    if int(anio) < today.year:
        return "Diciembre"
    if today > _date(today.year, 7, 20):
        return "Junio"
    return "Diciembre"


def prepare_cmi_data(
    anio: int,
    mes: int,
    pdi_catalog: pd.DataFrame | None = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare CMI data for rendering.
    
    Args:
        anio: Year to prepare data for
        mes: Month to prepare data for
        pdi_catalog: Optional PDI catalog dataframe
        
    Returns:
        Tuple of (prepared_df, pdi_catalog)
    """
    from services.strategic_indicators import (
        preparar_pdi_con_cierre,
        load_pdi_catalog,
    )
    from services.cmi_filters import filter_df_for_cmi_estrategico
    from services.data_loader import cargar_ficha_tecnica as _cft

    # Prepare and filter data
    df = preparar_pdi_con_cierre(int(anio), int(mes))
    df = filter_df_for_cmi_estrategico(df, id_column="Id")

    if df.empty:
        return df, pdi_catalog or pd.DataFrame()

    # Load PDI catalog if not provided
    if pdi_catalog is None or pdi_catalog.empty:
        pdi_catalog = load_pdi_catalog(include_ids=True)

    df_filtrado = df.copy()

    # Enrich with metadata from Ficha Técnica
    try:
        _ft = _cft()
        if not _ft.empty and "Id" in _ft.columns:
            # Find description column (case-insensitive, handles encoding issues)
            _desc_col = next(
                (c for c in _ft.columns if "descripci" in c.lower()),
                None,
            )
            _wanted = [
                c for c in [
                    _desc_col,
                    "Responsable del calculo",
                    "Fuente V1",
                    "Formula",
                    "Frecuencia",
                ]
                if c and c in _ft.columns
            ]
            _ft_sub = _ft[["Id"] + _wanted].drop_duplicates(subset="Id", keep="first").copy()
            if _desc_col and _desc_col in _ft_sub.columns:
                _ft_sub = _ft_sub.rename(columns={_desc_col: "Descripcion"})

            # Normalize keys to string for join
            df_filtrado["Id"] = df_filtrado["Id"].astype(str)
            _ft_sub["Id"] = _ft_sub["Id"].astype(str)
            df_filtrado = df_filtrado.merge(_ft_sub, on="Id", how="left")
    except Exception:
        pass  # If join fails, render with available fields

    return df_filtrado, pdi_catalog or pd.DataFrame()
