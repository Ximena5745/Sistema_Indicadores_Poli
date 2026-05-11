"""
services/strategic_indicators/processors.py — Procesadores de datos

Responsabilidad única: Transformaciones y agregaciones (cierre por corte, filtrado)

Funciones públicas:
  - cierre_por_corte(): Filtra cierres por fecha de corte (año/mes)
  - preparar_pdi_con_cierre(): Prepara indicadores PDI con cierre
  - preparar_cna_con_cierre(): Prepara indicadores CNA con cierre
"""

import pandas as pd
import streamlit as st

from core.config import CACHE_TTL
from .loaders import (
    load_worksheet_flags,
    load_pdi_catalog,
    load_cna_catalog,
    load_cierres,
)


def cierre_por_corte(df_cierres: pd.DataFrame, anio: int, mes: int) -> pd.DataFrame:
    """
    Filtra cierres hasta una fecha de corte específica.
    
    Parámetros:
      df_cierres: DataFrame de cierres (de load_cierres)
      anio: Año de corte
      mes: Mes de corte
      
    Retorna: DataFrame con registros hasta la fecha especificada (última entrada por Id)
    """
    if df_cierres.empty:
        return df_cierres

    df = df_cierres.copy()
    cutoff = int(anio) * 100 + int(mes)
    cutoff_date = pd.Timestamp(int(anio), int(mes), 1) + pd.offsets.MonthEnd(0)

    if "Anio" in df.columns and "Mes" in df.columns:
        ym = pd.to_numeric(df["Anio"], errors="coerce") * 100 + pd.to_numeric(
            df["Mes"], errors="coerce"
        )
        by_period = ym.notna() & (ym <= cutoff)
        if "Fecha" in df.columns:
            by_date = (
                ym.isna()
                & df["Fecha"].notna()
                & (pd.to_datetime(df["Fecha"], errors="coerce") <= cutoff_date)
            )
            df = df[by_period | by_date].copy()
        else:
            df = df[by_period].copy()
    elif "Fecha" in df.columns:
        df = df[pd.to_datetime(df["Fecha"], errors="coerce") <= cutoff_date].copy()

    if df.empty:
        return df

    # Mantener último registro por Id
    if "Fecha" in df.columns:
        df = df.sort_values(["Id", "Fecha"]).drop_duplicates(subset=["Id"], keep="last")
    else:
        df = df.drop_duplicates(subset=["Id"], keep="last")
    
    return df.reset_index(drop=True)


def _preparar_indicadores_con_cierre(
    anio: int,
    mes: int,
    flag_column: str,
    catalog_loader,
    catalog_merge_cols: list,
) -> pd.DataFrame:
    """
    Función genérica para preparar indicadores estratégicos con cierre.
    
    Consolida lógica común de preparar_pdi_con_cierre y preparar_cna_con_cierre.
    
    Parámetros:
      anio: Año a consultar
      mes: Mes a consultar
      flag_column: Nombre columna de flag ("FlagPlanEstrategico", "FlagCNA")
      catalog_loader: Función que carga el catálogo (load_pdi_catalog, load_cna_catalog)
      catalog_merge_cols: Lista de columnas para merge del catálogo
                         ej: ["Linea", "Objetivo"] para PDI
                         ej: ["Factor", "Caracteristica"] para CNA
                         
    Retorna: DataFrame con indicadores enriquecidos + cierre + catálogo
    """
    base = load_worksheet_flags()
    catalog = catalog_loader()
    cierres = load_cierres()

    if base.empty or cierres.empty:
        return pd.DataFrame()

    def _normalize_flag_series(series: pd.Series) -> pd.Series:
        """Normaliza serie de flags a 0/1."""
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
        """Normaliza valores de ID a string."""
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

    # Filtrar por flag específico
    if flag_column not in base.columns:
        return pd.DataFrame()

    flag_vals = _normalize_flag_series(base[flag_column])
    indicators = base[flag_vals == 1].copy()
    if indicators.empty:
        return pd.DataFrame()

    # Excluir proyectos
    if "Proyecto" in indicators.columns:
        proyecto_vals = _normalize_flag_series(indicators["Proyecto"])
        indicators = indicators[proyecto_vals != 1].copy()
    if indicators.empty:
        return pd.DataFrame()

    # Normalizar IDs para merge
    indicators["Id"] = indicators["Id"].apply(_normalize_id_value)
    cierres_cut = cierre_por_corte(cierres, anio, mes)
    cierres_cut["Id"] = cierres_cut["Id"].apply(_normalize_id_value)

    # Merge con cierres
    result = indicators[["Id", "Indicador"] + catalog_merge_cols].merge(
        cierres_cut, on="Id", how="left"
    )

    # Merge con catálogo si existen las columnas necesarias
    if not catalog.empty and all(col in result.columns for col in catalog_merge_cols):
        result = result.merge(
            catalog,
            on=catalog_merge_cols,
            how="left",
        )

    return result.reset_index(drop=True)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def preparar_pdi_con_cierre(anio: int, mes: int) -> pd.DataFrame:
    """
    Prepara indicadores Plan Estratégico (PDI) con cierre hasta fecha especificada.
    
    Parámetros:
      anio: Año de corte
      mes: Mes de corte
      
    Retorna: DataFrame con indicadores PDI + cierres + jerarquía
    """
    return _preparar_indicadores_con_cierre(
        anio,
        mes,
        flag_column="FlagPlanEstrategico",
        catalog_loader=load_pdi_catalog,
        catalog_merge_cols=["Linea", "Objetivo"],
    )


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def preparar_cna_con_cierre(anio: int, mes: int) -> pd.DataFrame:
    """
    Prepara indicadores CNA con cierre hasta fecha especificada.
    
    Parámetros:
      anio: Año de corte
      mes: Mes de corte
      
    Retorna: DataFrame con indicadores CNA + cierres + jerarquía
    """
    return _preparar_indicadores_con_cierre(
        anio,
        mes,
        flag_column="FlagCNA",
        catalog_loader=load_cna_catalog,
        catalog_merge_cols=["Factor", "Caracteristica"],
    )
