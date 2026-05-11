"""
services/cmi_filters/loaders.py
===============================

Data loading from CMI and Kawak sources.

Responsibility: Load CMI worksheet and Kawak active IDs.
"""

from pathlib import Path
from typing import Optional
import re

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
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
    from .utils import _normalize_id_value
    
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
