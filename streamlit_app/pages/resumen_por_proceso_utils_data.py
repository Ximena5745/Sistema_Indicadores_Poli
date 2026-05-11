"""Data loading utilities for resumen_por_proceso page."""

import streamlit as st
import pandas as pd
from pathlib import Path

from streamlit_app.pages.resumen_por_proceso_config import (
    PATH_CALIDAD, PATH_CONSOLIDADO_ANALISIS, PATH_INDICADORES_CMI,
    TEXT_SUMMARY_CHARS
)


@st.cache_data
def _load_indicadores_por_cmi() -> pd.DataFrame:
    """Load indicators per CMI from Excel."""
    try:
        df = pd.read_excel(PATH_INDICADORES_CMI, sheet_name=0, engine="openpyxl")
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data
def _load_calidad_data() -> tuple[pd.DataFrame, str | None]:
    """Load quality monitoring data."""
    if not PATH_CALIDAD.exists():
        return pd.DataFrame(), None
    
    try:
        df = pd.read_excel(PATH_CALIDAD, sheet_name="LISTA DE CHEQUEO", engine="openpyxl")
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)


@st.cache_data
def _build_calidad_metrics(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build quality metrics by process and subprocess."""
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    # Aggregate quality data by process
    try:
        # Simplified aggregation - adjust based on actual data structure
        metrics = df.groupby("Proceso", dropna=False).size().reset_index(name="Count")
        return metrics, pd.DataFrame()
    except Exception:
        return pd.DataFrame(), pd.DataFrame()


@st.cache_data
def _load_analisis_indicadores() -> dict[str, str]:
    """Load indicator analysis from Kawak API."""
    if not PATH_CONSOLIDADO_ANALISIS.exists():
        return {}
    
    try:
        df = pd.read_excel(PATH_CONSOLIDADO_ANALISIS, engine="openpyxl")
        if "Indicador" in df.columns and "Análisis" in df.columns:
            return dict(zip(df["Indicador"], df["Análisis"]))
        return {}
    except Exception:
        return {}


@st.cache_data
def _load_analisis_periodos() -> dict[str, list[str]]:
    """Load periodic analysis history."""
    if not PATH_CONSOLIDADO_ANALISIS.exists():
        return {}
    
    try:
        df = pd.read_excel(PATH_CONSOLIDADO_ANALISIS, engine="openpyxl")
        if "Indicador" in df.columns:
            # Simplified - returns empty lists per indicator
            return {ind: [] for ind in df["Indicador"].unique()}
        return {}
    except Exception:
        return {}


def _prepare_tracking(df: pd.DataFrame, map_df: pd.DataFrame, month_num: int) -> pd.DataFrame:
    """Prepare tracking data with process mapping and calculations."""
    if df.empty:
        return df
    
    df = df.copy()
    
    # Add process mapping if available
    if not map_df.empty and "Proceso" in map_df.columns:
        merge_cols = [c for c in ["Id", "Indicador"] if c in df.columns]
        if merge_cols:
            try:
                df = df.merge(
                    map_df[["Proceso", "Subproceso", "Proceso_padre"]],
                    left_on=merge_cols[0] if merge_cols else "Indicador",
                    right_on="Indicador" if "Indicador" in map_df.columns else "Id",
                    how="left"
                )
            except Exception:
                pass
    
    # Add default columns if missing
    for col in ["Proceso_padre", "Subproceso", "Meta", "Ejecucion"]:
        if col not in df.columns:
            df[col] = None
    
    # Calculate compliance percentage if needed
    if "Cumplimiento_pct" not in df.columns:
        if "Meta" in df.columns and "Ejecucion" in df.columns:
            df["Cumplimiento_pct"] = (df["Ejecucion"] / df["Meta"] * 100).fillna(0)
        else:
            df["Cumplimiento_pct"] = 0
    
    return df


def _latest_per_indicator(df: pd.DataFrame) -> pd.DataFrame:
    """Get latest value per indicator, deduplicating."""
    if df.empty or "Indicador" not in df.columns:
        return df
    
    # Get last record per indicator
    return df.sort_values("Indicador").drop_duplicates(
        subset=["Indicador"], keep="last"
    )


def _latest_year_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Get latest year records."""
    if df.empty or "Anio" not in df.columns:
        return df
    
    latest_year = pd.to_numeric(df["Anio"], errors="coerce").max()
    if pd.isna(latest_year):
        return df
    
    return df[pd.to_numeric(df["Anio"], errors="coerce") == latest_year]


def _build_indicator_yearly(indicador: str, df: pd.DataFrame, 
                           subproceso: str | None = None,
                           month_num: int | None = None) -> pd.DataFrame:
    """Build yearly history for specific indicator."""
    if df.empty:
        return pd.DataFrame()
    
    # Filter by indicator
    df_ind = df[df["Indicador"].astype(str).str.contains(
        indicador, case=False, na=False, regex=False
    )]
    
    if not df_ind.empty:
        df_ind = df_ind.sort_values("Anio", ascending=False)
    
    return df_ind


def _resumir_analisis_texto(texto, max_chars: int = TEXT_SUMMARY_CHARS) -> str:
    """Extract and summarize analysis text."""
    if pd.isna(texto):
        return ""
    
    text = str(texto).strip()
    
    # Remove common API formatting
    text = text.replace("### ", "").replace("**", "").replace("##", "")
    
    # Get first 2 sentences or max_chars
    sentences = text.split(". ")
    summary = ". ".join(sentences[:2]) if len(sentences) >= 2 else text
    
    if len(summary) > max_chars:
        summary = summary[:max_chars] + "..."
    
    return summary


def _buscar_analisis_indicador(indicador: str, analisis_map: dict[str, str]) -> str:
    """Find analysis for specific indicator."""
    if not analisis_map:
        return ""
    
    for key, valor in analisis_map.items():
        if str(key).lower().strip() == str(indicador).lower().strip():
            return _resumir_analisis_texto(valor)
    
    return ""


def _buscar_analisis_periodos(indicador: str, analisis_periodos: dict) -> list[str]:
    """Get historical analysis for indicator."""
    if not analisis_periodos:
        return []
    
    return analisis_periodos.get(str(indicador), [])
