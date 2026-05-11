"""
Utility functions for pdi_acreditacion page.
"""

import pandas as pd
from core.semantica import normalizar_y_categorizar


def calcular_brecha(row):
    """
    Calculate gap between Meta and Ejecucion.
    
    Args:
        row: DataFrame row
        
    Returns:
        Gap value or None
    """
    try:
        return float(row.get("Meta", 0)) - float(row.get("Ejecucion", 0))
    except Exception:
        return None


def clasificar_estado(cumpl, id_indicador=None):
    """
    Classify compliance status.
    
    Uses centralizado wrapper from core.semantica.
    
    Args:
        cumpl: Compliance percentage (0-100 or 0-130)
        id_indicador: Indicator ID for detection (optional)
        
    Returns:
        Status: "Peligro", "Alerta", "Cumplimiento", "Sobrecumplimiento", "Sin dato"
    """
    if pd.isna(cumpl):
        return "Sin dato"

    try:
        cumpl_pct = float(cumpl)
    except Exception:
        return "Sin dato"

    return normalizar_y_categorizar(cumpl_pct, es_porcentaje=True, id_indicador=id_indicador)


def enriquecer_datos_cna(df, df_cna):
    """
    Enrich dataframe with CNA catalog metadata.
    
    Args:
        df: Main dataframe to enrich
        df_cna: CNA catalog dataframe
        
    Returns:
        Enriched dataframe
    """
    for col in ["Linea", "Objetivo", "Indicador"]:
        if col not in df.columns and not df_cna.empty and col in df_cna.columns:
            df = df.merge(df_cna[["Id", col]], on="Id", how="left")
    return df


def extraer_columna_cumplimiento(df):
    """
    Find and extract compliance column from dataframe.
    
    Tries multiple column names (case variations).
    
    Args:
        df: Dataframe to search
        
    Returns:
        Tuple of (column_name, Series) or raises error if not found
    """
    for c in ["Cumplimiento", "Cumplimiento_norm", "cumplimiento", "cumplimiento_norm"]:
        if c in df.columns:
            return c, pd.to_numeric(df[c], errors="coerce") * 100
    
    raise ValueError("No compliance column found in dataframe")


def preparar_datos_acciones(df):
    """
    Prepare dataframe with Estado classification and gaps.
    
    Args:
        df: Dataframe to prepare
        
    Returns:
        Prepared dataframe
    """
    df = df.copy()
    df["brecha"] = df.apply(calcular_brecha, axis=1)
    
    def _clasificar_con_id(row):
        id_ind = row.get("Id", None)
        return clasificar_estado(row["cumplimiento_pct"], id_indicador=id_ind)
    
    df["Estado"] = df.apply(_clasificar_con_id, axis=1)
    return df


def aplicar_filtros(df, filters_dict):
    """
    Apply multiple filters to dataframe.
    
    Args:
        df: Dataframe to filter
        filters_dict: Dictionary with filter criteria
        
    Returns:
        Filtered dataframe
    """
    df = df.copy()
    
    if filters_dict.get("estado") and filters_dict["estado"] != "Todos":
        df = df[df["Estado"] == filters_dict["estado"]]
    
    if filters_dict.get("macro") and filters_dict["macro"] != "Todos":
        df = df[df["Linea"] == filters_dict["macro"]]
    
    if filters_dict.get("horizonte"):
        df = df[df["Periodo"] == filters_dict["horizonte"]]
    
    return df
