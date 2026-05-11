"""Utilities for plan_mejoramiento page."""

import pandas as pd
import plotly.express as px
import streamlit as st

from streamlit_app.services.strategic_indicators import NIVEL_COLOR_EXT, load_cna_catalog
from streamlit_app.utils.formatting import formatear_meta_ejecucion_df
from streamlit_app.pages.plan_mejoramiento_config import (
    COLUMNAS_CNA_BASE,
    COLUMNAS_CNA_OPCIONALES,
    COLUMNAS_RENAME_CNA,
    CORTE_SEMESTRAL,
    NIVEL_ICONS_CNA,
    STREAMLIT_COLUMN_CONFIG,
)


def build_cna_table(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Build and format CNA indicators table.
    
    Args:
        df: DataFrame with CNA indicators
    
    Returns:
        Tuple of (formatted_table, column_config_dict)
    """
    _cols_cna = COLUMNAS_CNA_BASE.copy()
    for extra_col in COLUMNAS_CNA_OPCIONALES:
        if extra_col in df.columns:
            _cols_cna.append(extra_col)
    
    tabla = df[[c for c in _cols_cna if c in df.columns]].copy()
    tabla = tabla.rename(columns=COLUMNAS_RENAME_CNA)
    tabla["Cumplimiento (%)"] = pd.to_numeric(tabla["Cumplimiento (%)"], errors="coerce").round(1)
    tabla = formatear_meta_ejecucion_df(tabla, meta_col="Meta", ejec_col="Ejecución")
    
    if "Nivel" in tabla.columns:
        tabla["Nivel"] = tabla["Nivel"].apply(
            lambda n: f'{NIVEL_ICONS_CNA.get(str(n), "")} {n}' if pd.notna(n) else n
        )
    
    _sort_cols = [c for c in ["Factor", "Característica", "Id"] if c in tabla.columns]
    tabla = tabla.sort_values(_sort_cols, na_position="last")
    
    # Build column config
    column_config = {}
    for col_name, col_def in STREAMLIT_COLUMN_CONFIG.items():
        if col_name in tabla.columns:
            if col_def["type"] == "text":
                column_config[col_name] = st.column_config.TextColumn(col_name, width=col_def["width"])
            elif col_def["type"] == "number":
                column_config[col_name] = st.column_config.NumberColumn(
                    col_name, format=col_def["format"], width=col_def["width"]
                )
            elif col_def["type"] == "datetime":
                column_config[col_name] = st.column_config.DatetimeColumn(col_name, width=col_def["width"])
    
    return tabla, column_config


def build_factor_characteristics_tree(df: pd.DataFrame, factor_color_map: dict) -> pd.DataFrame:
    """Build hierarchical data for factor/characteristic treemap.
    
    Args:
        df: Input DataFrame
        factor_color_map: Mapping of factor names to colors
    
    Returns:
        DataFrame with factor/characteristic counts
    """
    df_tree = df[["Factor", "Caracteristica"]].copy()
    df_tree["Factor"] = df_tree["Factor"].astype(str).str.strip()
    df_tree["Caracteristica"] = df_tree["Caracteristica"].astype(str).str.strip()
    df_tree = df_tree[
        df_tree["Factor"].ne("")
        & df_tree["Caracteristica"].ne("")
        & ~df_tree["Factor"].isna()
        & ~df_tree["Caracteristica"].isna()
    ]
    df_tree = (
        df_tree.groupby(["Factor", "Caracteristica"], as_index=False)
        .size()
        .rename(columns={"size": "Cantidad"})
    )
    return df_tree


def build_improvement_actions_kpis(df_acc: pd.DataFrame, id_col_acc: str, ids_cna: set) -> dict:
    """Calculate KPIs for improvement actions linked to CNA indicators.
    
    Args:
        df_acc: DataFrame with improvement actions
        id_col_acc: Column name containing indicator ID
        ids_cna: Set of CNA indicator IDs to match
    
    Returns:
        Dict with KPI metrics
    """
    df_acc_v = df_acc.copy()
    df_acc_v["_id_norm"] = df_acc_v[id_col_acc].apply(
        lambda x: (
            str(int(float(x))) if str(x).replace(".", "").isdigit() else str(x).strip()
        )
    )
    df_acc_cna = df_acc_v[df_acc_v["_id_norm"].isin(ids_cna)].copy()
    
    if df_acc_cna.empty:
        return {"total": 0, "cerradas": 0, "abiertas": 0, "avance_prom": None, "vencidas": None}
    
    total_acc = len(df_acc_cna)
    estado_col = "ESTADO" if "ESTADO" in df_acc_cna.columns else None
    cerradas = int((df_acc_cna[estado_col] == "Cerrada").sum()) if estado_col else 0
    abiertas = total_acc - cerradas
    
    avance_ser = pd.to_numeric(
        df_acc_cna.get("AVANCE", pd.Series(dtype=float)), errors="coerce"
    ).dropna()
    avance_prom = float(avance_ser.mean()) if not avance_ser.empty else None
    
    vencidas = (
        int((df_acc_cna.get("Estado_Tiempo", "") == "Vencida").sum())
        if "Estado_Tiempo" in df_acc_cna.columns
        else None
    )
    
    return {
        "total": total_acc,
        "cerradas": cerradas,
        "abiertas": abiertas,
        "avance_prom": avance_prom,
        "vencidas": vencidas,
        "df_cna": df_acc_cna,
        "estado_col": estado_col,
    }


def get_factor_color_map(df: pd.DataFrame) -> dict:
    """Generate color map for factors using Plotly color palettes.
    
    Args:
        df: DataFrame with Factor column
    
    Returns:
        Dictionary mapping factor names to colors
    """
    factor_palette = (
        px.colors.qualitative.Set3 + px.colors.qualitative.Pastel + px.colors.qualitative.Bold
    )
    factor_list = sorted(df["Factor"].dropna().astype(str).unique().tolist())
    return {
        f: factor_palette[i % len(factor_palette)] for i, f in enumerate(factor_list)
    }


def build_metrics_summary(df: pd.DataFrame, cna_catalog: pd.DataFrame) -> dict:
    """Build summary metrics for the page.
    
    Args:
        df: Filtered CNA data DataFrame
        cna_catalog: CNA catalog DataFrame
    
    Returns:
        Dictionary with summary metrics
    """
    total = len(df)
    con_dato = int(df["cumplimiento_pct"].notna().sum())
    prom = float(df["cumplimiento_pct"].mean()) if con_dato else 0.0
    n_fact = int(df["Factor"].nunique())
    n_car = int(df["Caracteristica"].nunique())
    total_fact_catalogo = int(cna_catalog["Factor"].nunique()) if not cna_catalog.empty else n_fact
    total_car_catalogo = (
        int(cna_catalog["Caracteristica"].nunique()) if not cna_catalog.empty else n_car
    )
    
    return {
        "total": total,
        "con_dato": con_dato,
        "prom": prom,
        "n_fact": n_fact,
        "n_car": n_car,
        "total_fact_catalogo": total_fact_catalogo,
        "total_car_catalogo": total_car_catalogo,
    }


def apply_cna_filters(df: pd.DataFrame, factor_sel: str, car_sel: str, nombre_q: str) -> tuple[pd.DataFrame, list]:
    """Apply CNA indicator filters to DataFrame.
    
    Args:
        df: CNA indicators DataFrame
        factor_sel: Selected factor or "Todos"
        car_sel: Selected characteristic or "Todas"
        nombre_q: Search query for indicator name
    
    Returns:
        Tuple of (filtered_df, active_filters_list)
    """
    if factor_sel != "Todos":
        df = df[df["Factor"] == factor_sel]
    if car_sel != "Todas":
        df = df[df["Caracteristica"] == car_sel]
    if nombre_q.strip():
        df = df[df["Indicador"].astype(str).str.contains(nombre_q.strip(), case=False, na=False)]
    
    activos = []
    if factor_sel != "Todos":
        activos.append(f"Factor: {factor_sel}")
    if car_sel != "Todas":
        activos.append(f"Característica: {car_sel}")
    if nombre_q.strip():
        activos.append(f"Indicador contiene: {nombre_q.strip()}")
    
    return df, activos


def get_cna_factor_options(cna_catalog: pd.DataFrame, df: pd.DataFrame) -> list:
    """Get available factors from CNA catalog or data.
    
    Args:
        cna_catalog: CNA catalog DataFrame
        df: CNA data DataFrame
    
    Returns:
        Sorted list of factor options
    """
    if not cna_catalog.empty:
        return sorted(cna_catalog["Factor"].dropna().astype(str).unique().tolist())
    else:
        return sorted(df["Factor"].dropna().astype(str).unique().tolist())


def get_cna_characteristics(cna_catalog: pd.DataFrame, df: pd.DataFrame, factor_sel: str) -> list:
    """Get available characteristics filtered by factor.
    
    Args:
        cna_catalog: CNA catalog DataFrame
        df: CNA data DataFrame
        factor_sel: Selected factor or "Todos"
    
    Returns:
        Sorted list of characteristic options
    """
    if not cna_catalog.empty:
        car_pool = (
            cna_catalog if factor_sel == "Todos"
            else cna_catalog[cna_catalog["Factor"] == factor_sel]
        )
    else:
        df_car = df if factor_sel == "Todos" else df[df["Factor"] == factor_sel]
        car_pool = df_car
    
    return sorted(car_pool["Caracteristica"].dropna().astype(str).unique().tolist())
