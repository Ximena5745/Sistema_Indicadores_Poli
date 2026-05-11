"""
Utility functions for seguimiento_reportes page.
"""

from datetime import date
import pandas as pd
import streamlit as st

from core.config import CACHE_TTL
from streamlit_app.utils.formatting import id_limpio
from .seguimiento_config import RUTA_SEGUIMIENTO, VENTANA_MESES, MESES_OPCIONES


def normalize_string(s: str) -> str:
    """
    Normalize string to lowercase without accents.
    
    Args:
        s: String to normalize
        
    Returns:
        Normalized string
    """
    s = str(s or "").strip().lower()
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u")):
        s = s.replace(a, b)
    return s


def get_ventana(periodicidad: str) -> int:
    """
    Get reporting window (in months) for given periodicity.
    
    Args:
        periodicidad: Periodicity string (mensual, trimestral, etc.)
        
    Returns:
        Window in months
    """
    return VENTANA_MESES.get(normalize_string(periodicidad), 1)


def detectar_vencidos(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Detect overdue indicators based on last report date.
    
    Logic:
    - For each indicator, find last record with Estado=="Reportado"
    - Compare year-month of that record with current month
    - If difference exceeds periodicity window → Overdue
    - If difference between 80-100% of window → About to expire
    
    Args:
        df: DataFrame with indicator records
        
    Returns:
        Tuple of (vencidos_df, por_vencer_df)
    """
    hoy = date.today()
    ym_actual = hoy.year * 12 + hoy.month

    needed = {"Id", "Año", "Mes", "Estado"}
    if not needed.issubset(df.columns):
        return pd.DataFrame(), pd.DataFrame()

    df_rep = df[df["Estado"].astype(str).str.strip() == "Reportado"].copy()
    df_rep["ym"] = pd.to_numeric(df_rep["Año"], errors="coerce").fillna(0).astype(
        int
    ) * 12 + pd.to_numeric(df_rep["Mes"], errors="coerce").fillna(0).astype(int)
    ultimo = df_rep.groupby("Id")["ym"].max().reset_index().rename(columns={"ym": "ultimo_ym"})

    # Base metadata per indicator
    meta_cols = [c for c in ["Id", "Periodicidad", "Proceso", "Indicador"] if c in df.columns]
    meta = df[meta_cols].drop_duplicates(subset=["Id"])

    merged = meta.merge(ultimo, on="Id", how="left")
    merged["ultimo_ym"] = merged["ultimo_ym"].fillna(0).astype(int)
    merged["ventana"] = merged.get("Periodicidad", pd.Series("mensual", index=merged.index)).apply(
        get_ventana
    )
    merged["diff_meses"] = ym_actual - merged["ultimo_ym"]

    vencidos = merged[merged["diff_meses"] > merged["ventana"]].copy()
    por_vencer = merged[
        (merged["diff_meses"] <= merged["ventana"])
        & (merged["diff_meses"] >= (merged["ventana"] * 0.8).astype(int))
        & (merged["diff_meses"] > 0)
    ].copy()

    return vencidos, por_vencer


@st.cache_data(ttl=CACHE_TTL, show_spinner="Cargando Tracking Mensual...")
def cargar_tracking() -> pd.DataFrame:
    """
    Load tracking data from Excel file.
    
    Returns:
        Tracking DataFrame
    """
    if not RUTA_SEGUIMIENTO.exists():
        return pd.DataFrame()
    try:
        df = pd.read_excel(str(RUTA_SEGUIMIENTO), sheet_name="Tracking Mensual", engine="openpyxl")
    except Exception:
        return pd.DataFrame()

    df.columns = [str(c).strip() for c in df.columns]
    if "Id" in df.columns:
        df["Id"] = df["Id"].apply(id_limpio)
    if "Año" in df.columns:
        df["Año"] = pd.to_numeric(df["Año"], errors="coerce").astype("Int64")
    if "Mes" in df.columns:
        df["Mes"] = pd.to_numeric(df["Mes"], errors="coerce").astype("Int64")
    return df
