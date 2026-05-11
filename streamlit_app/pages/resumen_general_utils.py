"""Utility functions for resumen_general page."""

import os
import re
import unicodedata
from pathlib import Path
import pandas as pd
import numpy as np

from streamlit_app.pages.resumen_general_config import (
    MES_MAP, 
    THRESHOLD_SOBRECUMPLIMIENTO,
    THRESHOLD_CUMPLIMIENTO, 
    THRESHOLD_ALERTA,
    TEXT_COLS_NORMALIZE,
    PATH_CONSOLIDADO,
    PATH_RETOS,
)
from core.config import DATA_OUTPUT
from core.semantica import categorizar_cumplimiento
from services.strategic_indicators import preparar_pdi_con_cierre, load_cierres, load_worksheet_flags
from services.cmi_filters import filter_df_for_cmi_estrategico


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names and replace underscores in text columns."""
    df.columns = [str(c).strip() for c in df.columns]
    
    if "Cumplimiento" in df.columns and "cumplimiento_pct" not in df.columns:
        df = df.rename(columns={"Cumplimiento": "cumplimiento_pct"})
    
    for col in TEXT_COLS_NORMALIZE:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace("_", " ", regex=False).str.strip()
            df[col] = df[col].replace("nan", pd.NA)
    
    return df


def _parse_month(value):
    """Convert month value (int/float/string) to month number (1-12)."""
    if pd.isna(value):
        return None
    
    if isinstance(value, (int, float)):
        try:
            return int(value)
        except Exception:
            return None
    
    text = str(value).strip()
    if text.isdigit():
        return int(text)
    
    return MES_MAP.get(text.lower())


def _norm_key(value: str) -> str:
    """Normalize string for lookup (lowercase, remove accents, collapse whitespace)."""
    if pd.isna(value):
        return ""
    
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("_", " ")
    text = re.sub(r"[^0-9a-z]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _categorize_compliance(pct: float) -> str:
    """Categorize compliance percentage into level."""
    if pd.isna(pct):
        return "Sin dato"
    
    pct = float(pct)
    if pct >= THRESHOLD_SOBRECUMPLIMIENTO:
        return "Sobrecumplimiento"
    elif pct >= THRESHOLD_CUMPLIMIENTO:
        return "Cumplimiento"
    elif pct >= THRESHOLD_ALERTA:
        return "Alerta"
    else:
        return "Peligro"


def _ensure_nivel_cumplimiento(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure 'Nivel de cumplimiento' column exists, creating it if needed."""
    if "Nivel de cumplimiento" in df.columns:
        return df
    
    df = df.copy()
    if "cumplimiento_pct" in df.columns:
        df["Nivel de cumplimiento"] = df["cumplimiento_pct"].apply(_categorize_compliance)
    else:
        df["Nivel de cumplimiento"] = "Sin dato"
    
    return df


def _load_consolidado_cierres() -> pd.DataFrame:
    """Load consolidated data from Consolidado Cierres sheet."""
    if not PATH_CONSOLIDADO.exists():
        return pd.DataFrame()
    
    try:
        df = pd.read_excel(PATH_CONSOLIDADO, sheet_name="Consolidado Cierres", engine="openpyxl")
    except Exception:
        return pd.DataFrame()
    
    df = _normalize_columns(df)
    
    # Ensure year column
    if "Año" in df.columns:
        df["Año"] = pd.to_numeric(df["Año"], errors="coerce")
    elif "Anio" in df.columns:
        df["Año"] = pd.to_numeric(df["Anio"], errors="coerce")
    
    # Parse month
    if "Mes" in df.columns:
        df["Mes_num"] = df["Mes"].apply(_parse_month)
    else:
        df["Mes_num"] = None
    
    # Ensure compliance percentage is 0-100 scale
    if "cumplimiento_pct" in df.columns:
        df["cumplimiento_pct"] = pd.to_numeric(df["cumplimiento_pct"], errors="coerce")
        # Convert 0-1 scale to 0-100 if needed
        if (df["cumplimiento_pct"] > 0).any() and (df["cumplimiento_pct"] <= 1).all():
            df["cumplimiento_pct"] = df["cumplimiento_pct"] * 100
    
    os.makedirs("artifacts", exist_ok=True)
    
    return df


def _load_plan_retos_data(year: int):
    """Load Plan de retos data (Linea and Objetivo sheets) for given year."""
    if not PATH_RETOS.exists():
        return pd.DataFrame(), pd.DataFrame()
    
    try:
        linea_df = pd.read_excel(PATH_RETOS, sheet_name="Linea", engine="openpyxl")
        obj_df = pd.read_excel(PATH_RETOS, sheet_name="Objetivo", engine="openpyxl")
    except Exception:
        return pd.DataFrame(), pd.DataFrame()
    
    # Normalize column names
    linea_df.columns = [str(c).strip() for c in linea_df.columns]
    obj_df.columns = [str(c).strip() for c in obj_df.columns]
    
    # Filter by year
    if "Año" in linea_df.columns:
        linea_df = linea_df[linea_df["Año"] == year].copy()
    if "Año" in obj_df.columns:
        obj_df = obj_df[obj_df["Año"] == year].copy()
    
    # Normalize column names for sunburst
    if "Línea Estratégica" in linea_df.columns:
        linea_df = linea_df.rename(columns={"Línea Estratégica": "Linea"})
    if "Línea Estratégica" in obj_df.columns:
        obj_df = obj_df.rename(columns={"Línea Estratégica": "Linea"})
    
    if "Cumplimiento" in linea_df.columns:
        linea_df = linea_df.rename(columns={"Cumplimiento": "cumplimiento_pct"})
    if "Cumplimiento" in obj_df.columns:
        obj_df = obj_df.rename(columns={"Cumplimiento": "cumplimiento_pct"})
    
    # Convert compliance from decimal to percentage if needed
    if "cumplimiento_pct" in linea_df.columns:
        linea_df["cumplimiento_pct"] = linea_df["cumplimiento_pct"] * 100
    if "cumplimiento_pct" in obj_df.columns:
        obj_df["cumplimiento_pct"] = obj_df["cumplimiento_pct"] * 100
    
    # Ensure Objetivo column
    if "Objetivo" not in obj_df.columns:
        obj_df["Objetivo"] = None
    
    return linea_df, obj_df


def _load_plan_retos_planes(year: int) -> pd.DataFrame:
    """Load plan counts by line from Planes sheet for given year."""
    if not PATH_RETOS.exists():
        return pd.DataFrame(columns=["Linea", "N_Planes"])
    
    try:
        df = pd.read_excel(PATH_RETOS, sheet_name="Planes", engine="openpyxl")
    except Exception:
        return pd.DataFrame(columns=["Linea", "N_Planes"])
    
    df.columns = [str(c).strip() for c in df.columns]
    
    if "Año" in df.columns:
        df = df[df["Año"] == year].copy()
    
    if "Desglose" in df.columns:
        df = df.rename(columns={"Desglose": "Linea"})
    
    if "N°" in df.columns:
        df = df.rename(columns={"N°": "N_Planes"})
    elif "N" in df.columns:
        df = df.rename(columns={"N": "N_Planes"})
    
    if "Linea" not in df.columns or "N_Planes" not in df.columns:
        return pd.DataFrame(columns=["Linea", "N_Planes"])
    
    df = df[["Linea", "N_Planes"]].copy()
    df["Linea"] = df["Linea"].astype(str).str.strip()
    df["N_Planes"] = pd.to_numeric(df["N_Planes"], errors="coerce").fillna(0).astype(int)
    
    return df


def _get_proyectos_ids() -> set:
    """Get set of IDs marked as Proyecto==1 in CMI worksheet."""
    try:
        from services.cmi_filters import load_cmi_worksheet
        df = load_cmi_worksheet()
        if df.empty or "Proyecto" not in df.columns or "Id" not in df.columns:
            return set()
        return set(str(int(x)) if isinstance(x, float) else str(x).strip() 
                  for x in df.loc[df["Proyecto"] == 1, "Id"].dropna())
    except Exception:
        return set()


def _build_linea_summary_from_df(df: pd.DataFrame, nivel_col: str = "Nivel de cumplimiento", 
                                 unique_count_col: str | None = None) -> pd.DataFrame:
    """Build summary by strategic line with indicators count and compliance levels."""
    if df.empty or "Linea" not in df.columns:
        return pd.DataFrame(columns=["Linea", "N_Indicadores", "Cumpl_Promedio", 
                                    "Sobrecumplimiento", "Cumplimiento", "Alerta", "Peligro"])
    
    df = df.copy()
    if nivel_col not in df.columns:
        df = _ensure_nivel_cumplimiento(df)
        nivel_col = "Nivel de cumplimiento"
    
    if unique_count_col and unique_count_col in df.columns:
        count_agg = (unique_count_col, 
                    lambda s: s.dropna().astype(str).str.strip().replace("", pd.NA).dropna().nunique())
    else:
        count_agg = ("Indicador", "count") if "Indicador" in df.columns else (df.columns[0], "size")
    
    resumen = (
        df.groupby("Linea", dropna=False)
        .agg(
            N_Indicadores=count_agg,
            Cumpl_Promedio=("cumplimiento_pct", "mean"),
            Sobrecumplimiento=(nivel_col, lambda s: (s == "Sobrecumplimiento").sum()),
            Cumplimiento=(nivel_col, lambda s: (s == "Cumplimiento").sum()),
            Alerta=(nivel_col, lambda s: (s == "Alerta").sum()),
            Peligro=(nivel_col, lambda s: (s == "Peligro").sum()),
        )
        .reset_index()
    )
    
    return resumen


def _build_linea_summary_from_retos(linea_df: pd.DataFrame, 
                                   objetivo_df: pd.DataFrame | None = None,
                                   planes_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Build summary by line for Plan de Retos."""
    if linea_df.empty or "Linea" not in linea_df.columns:
        return pd.DataFrame(columns=["Linea", "N_Indicadores", "Cumpl_Promedio",
                                    "Sobrecumplimiento", "Cumplimiento", "Alerta", "Peligro"])
    
    df = linea_df.copy()
    df["Nivel de cumplimiento"] = df["cumplimiento_pct"].apply(_categorize_compliance)
    
    if objetivo_df is not None and "Linea" in objetivo_df.columns and "Objetivo" in objetivo_df.columns:
        objetivos_count = (
            objetivo_df.groupby("Linea", dropna=False)
            .agg(N_Indicadores=("Objetivo", 
                              lambda s: s.dropna().astype(str).str.strip().replace("", pd.NA).dropna().nunique()))
            .reset_index()
        )
    else:
        objetivos_count = (
            df.groupby("Linea", dropna=False)
            .agg(N_Indicadores=("cumplimiento_pct", "size"))
            .reset_index()
        )
    
    resumen = (
        df.groupby("Linea", dropna=False)
        .agg(
            Cumpl_Promedio=("cumplimiento_pct", "mean"),
            Sobrecumplimiento=("Nivel de cumplimiento", lambda s: (s == "Sobrecumplimiento").sum()),
            Cumplimiento=("Nivel de cumplimiento", lambda s: (s == "Cumplimiento").sum()),
            Alerta=("Nivel de cumplimiento", lambda s: (s == "Alerta").sum()),
            Peligro=("Nivel de cumplimiento", lambda s: (s == "Peligro").sum()),
        )
        .reset_index()
    )
    
    resumen = resumen.merge(objetivos_count, on="Linea", how="left")
    
    if planes_df is not None and "Linea" in planes_df.columns and "N_Planes" in planes_df.columns:
        planes_df = planes_df.copy()
        planes_df["Linea_norm"] = planes_df["Linea"].astype(str).apply(_norm_key)
        planes_count = (
            planes_df.groupby("Linea_norm", dropna=False)
            .agg(N_Planes=("N_Planes", "sum"))
            .reset_index()
        )
        resumen["Linea_norm"] = resumen["Linea"].astype(str).apply(_norm_key)
        resumen = resumen.merge(planes_count, on="Linea_norm", how="left")
        resumen["N_Indicadores"] = resumen["N_Planes"].fillna(resumen["N_Indicadores"]).astype(int)
        resumen = resumen.drop(columns=["Linea_norm", "N_Planes"])
    
    return resumen


def calcular_cascada(df: pd.DataFrame) -> pd.DataFrame:
    """Build 4-level cascade (Line → Objective → Meta → Indicator)."""
    # Level 4: Indicator (leaf)
    nivel4 = df.copy()
    nivel4["Nivel"] = 4
    nivel4["Total_Indicadores"] = 1
    nivel4 = nivel4[[
        "Nivel", "Linea", "Objetivo", "Meta_PDI", "Indicador", "cumplimiento_pct", "Total_Indicadores"
    ]]
    nivel4 = nivel4.rename(columns={"cumplimiento_pct": "Cumplimiento"})
    
    # Level 3: Meta_PDI
    nivel3 = (
        df.groupby(["Linea", "Objetivo", "Meta_PDI"], dropna=False)
        .agg(Cumplimiento=("cumplimiento_pct", "mean"), 
             Total_Indicadores=("Indicador", "count"))
        .reset_index()
    )
    nivel3["Nivel"] = 3
    nivel3["Indicador"] = None
    nivel3 = nivel3[["Nivel", "Linea", "Objetivo", "Meta_PDI", "Indicador", 
                     "Cumplimiento", "Total_Indicadores"]]
    
    # Level 2: Objective
    nivel2 = (
        df.groupby(["Linea", "Objetivo"], dropna=False)
        .agg(Cumplimiento=("cumplimiento_pct", "mean"),
             Total_Indicadores=("Indicador", "count"))
        .reset_index()
    )
    nivel2["Nivel"] = 2
    nivel2["Meta_PDI"] = None
    nivel2["Indicador"] = None
    nivel2 = nivel2[["Nivel", "Linea", "Objetivo", "Meta_PDI", "Indicador",
                     "Cumplimiento", "Total_Indicadores"]]
    
    # Level 1: Line
    nivel1 = (
        df.groupby(["Linea"], dropna=False)
        .agg(Cumplimiento=("cumplimiento_pct", "mean"),
             Total_Indicadores=("Indicador", "count"))
        .reset_index()
    )
    nivel1["Nivel"] = 1
    nivel1["Objetivo"] = None
    nivel1["Meta_PDI"] = None
    nivel1["Indicador"] = None
    nivel1 = nivel1[["Nivel", "Linea", "Objetivo", "Meta_PDI", "Indicador",
                     "Cumplimiento", "Total_Indicadores"]]
    
    # Concatenate all levels
    cascada = pd.concat([nivel1, nivel2, nivel3, nivel4], ignore_index=True)
    return cascada


def _available_years(df: pd.DataFrame) -> list:
    """Get list of available years from dataframe."""
    if "Año" not in df.columns:
        return []
    
    years = pd.to_numeric(df["Año"], errors="coerce").dropna().astype(int).unique()
    return sorted(years.tolist())


def _available_months_for_year(df: pd.DataFrame, year: int) -> list:
    """Get list of available months for given year."""
    if "Año" not in df.columns or "Mes_num" not in df.columns:
        return []
    
    df_year = df[pd.to_numeric(df["Año"], errors="coerce") == year]
    if df_year.empty:
        return []
    
    months = pd.to_numeric(df_year["Mes_num"], errors="coerce").dropna().astype(int).unique()
    return sorted(months.tolist())


def _latest_month_for_year(df: pd.DataFrame, year: int) -> int | None:
    """Get latest month registered for given year."""
    months = _available_months_for_year(df, year)
    return max(months) if months else None


def _filter_consolidado_by_year_month(df: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
    """Filter consolidado data by year and month."""
    if df.empty:
        return df
    
    df = df.copy()
    if "Año" in df.columns:
        df = df[pd.to_numeric(df["Año"], errors="coerce") == year]
    
    if "Mes_num" in df.columns:
        df = df[pd.to_numeric(df["Mes_num"], errors="coerce") == month]
    
    return df


def _compute_trends(current: pd.DataFrame, previous: pd.DataFrame) -> tuple:
    """Compute improvements and declines between periods."""
    if current.empty or previous.empty:
        return [], []
    
    # TODO: Implement trend computation logic
    improvements = []
    declines = []
    
    return improvements, declines


def _merge_consolidado_summaries(s1: pd.DataFrame, s2: pd.DataFrame, s3: pd.DataFrame,
                                 o1: pd.DataFrame, o2: pd.DataFrame, o3: pd.DataFrame) -> tuple:
    """Merge summaries from three data sources (PDI, Cierres, Retos).
    
    Args:
        s1, s2, s3: Line summaries from PDI Catalog, Cierres, and Retos
        o1, o2, o3: Objective data from same sources
    
    Returns:
        Tuple of (merged_linea_summary, merged_objetivo_df)
    """
    # Merge line summaries
    linea_summary = pd.DataFrame()
    
    # Concatenate all summaries
    summaries = [s for s in [s1, s2, s3] if not s.empty]
    if summaries:
        linea_summary = pd.concat(summaries, ignore_index=True)
        # Group by Linea if present
        if "Linea" in linea_summary.columns:
            linea_summary = linea_summary.groupby("Linea", as_index=False).agg({
                col: "sum" if pd.api.types.is_numeric_dtype(linea_summary[col]) else "first"
                for col in linea_summary.columns if col != "Linea"
            })
    
    # Merge objectives
    objetivo_df = pd.DataFrame()
    objetivos = [o for o in [o1, o2, o3] if not o.empty]
    if objetivos:
        objetivo_df = pd.concat(objetivos, ignore_index=True)
        # Remove duplicates keeping first
        if "Objetivo" in objetivo_df.columns:
            objetivo_df = objetivo_df.drop_duplicates(subset=["Objetivo"], keep="first")
    
    return linea_summary, objetivo_df
