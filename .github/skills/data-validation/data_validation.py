"""
Data Validation Skill - Reusable functions for data source validation and enrichment

This module provides functions to validate and enrich datasets using official reference sources,
particularly Subproceso-Proceso-Area.xlsx as the master source for process hierarchies.
"""

import unicodedata
from pathlib import Path
from typing import Dict, Set

import pandas as pd
import streamlit as st


def _normalize_text(text: str) -> str:
    """Normalize text for reliable comparison: lowercase, remove accents, strip whitespace."""
    if not isinstance(text, str):
        text = str(text or "")
    nfd = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn").strip()


def enrich_with_process_hierarchy(df: pd.DataFrame, excel_path: Path) -> pd.DataFrame:
    """
    Enrich dataset with official process hierarchy from Subproceso-Proceso-Area.xlsx

    Args:
        df: Dataset with 'Subproceso' column
        excel_path: Path to Subproceso-Proceso-Area.xlsx

    Returns:
        Enriched DataFrame with updated 'Proceso', 'Unidad', 'Tipo de proceso' columns
    """
    if not excel_path.exists():
        st.warning(f"Reference file not found: {excel_path}")
        return df

    try:
        df_procesos = pd.read_excel(excel_path, engine="openpyxl")

        # Required columns check
        required_cols = ["Subproceso", "Proceso", "Unidad", "Tipo de proceso"]
        missing_cols = [col for col in required_cols if col not in df_procesos.columns]
        if missing_cols:
            st.warning(f"Missing columns in reference file: {missing_cols}")
            return df

        # Normalize text for merge using accent-insensitive comparison
        df_procesos["Subproceso_norm"] = df_procesos["Subproceso"].astype(str).apply(_normalize_text)
        df_procesos["Proceso_norm"] = df_procesos["Proceso"].astype(str).apply(_normalize_text)
        df["Subproceso_norm"] = df["Subproceso"].astype(str).apply(_normalize_text)
        df["Proceso_norm"] = df["Proceso"].astype(str).apply(_normalize_text)

        # Merge by normalized subprocess name to get parent process fields.
        # Rename reference columns to avoid suffix conflicts when the dataset already has the same names.
        ref_cols = (
            df_procesos[["Subproceso_norm", "Proceso", "Unidad", "Tipo de proceso"]]
            .drop_duplicates("Subproceso_norm")
            .rename(
                columns={
                    "Proceso": "Proceso_ref",
                    "Unidad": "Unidad_ref",
                    "Tipo de proceso": "Tipo de proceso_ref",
                }
            )
        )
        df = df.merge(ref_cols, on="Subproceso_norm", how="left")

        # Use Excel data if available, otherwise keep existing
        df["Unidad"] = df.get("Unidad", "").fillna("")
        df["Unidad"] = df["Unidad"].mask(
            df["Unidad"].astype(str).str.strip() == "",
            df.get("Unidad_ref", ""),
        )
        df["Tipo de proceso"] = df.get("Tipo de proceso", "").fillna("")
        df["Tipo de proceso"] = df["Tipo de proceso"].mask(
            df["Tipo de proceso"].astype(str).str.strip() == "",
            df.get("Tipo de proceso_ref", ""),
        )

        # Fallback: if Subproceso didn't match, try matching Proceso text as subproceso value
        unidad_map_by_sub = df_procesos.set_index("Subproceso_norm")["Unidad"].to_dict()
        unidad_map_by_proc = df_procesos.set_index("Proceso_norm")["Unidad"].to_dict()
        df["Unidad"] = df["Unidad"].fillna(df["Proceso_norm"].map(unidad_map_by_sub))
        df["Unidad"] = df["Unidad"].fillna(df["Proceso_norm"].map(unidad_map_by_proc))

        # Fallback: if Proceso text itself is a subproceso alias, fill Tipo de proceso too
        tipo_map_by_sub = df_procesos.set_index("Subproceso_norm")["Tipo de proceso"].to_dict()
        df["Tipo de proceso"] = df["Tipo de proceso"].fillna(df["Proceso_norm"].map(tipo_map_by_sub))

        # Clean up temporary columns
        df = df.drop(columns=["Subproceso_norm", "Proceso_norm", "Proceso_excel", "Unidad_excel", "Tipo de proceso_excel"], errors="ignore")

        

    except Exception as e:
        st.error(f"❌ Error al enriquecer con jerarquía de procesos: {e}")

    return df


def validate_process_sources(dataset_df: pd.DataFrame, excel_path: Path) -> Dict:
    """
    Validate that dataset processes match official Excel source

    Args:
        dataset_df: Dataset to validate
        excel_path: Path to reference Excel file

    Returns:
        Validation results dictionary
    """
    if not excel_path.exists():
        return {"error": f"Reference file not found: {excel_path}"}

    try:
        df_excel = pd.read_excel(excel_path, engine="openpyxl")

        if "Proceso" not in df_excel.columns or "Proceso" not in dataset_df.columns:
            return {"error": "Missing 'Proceso' column in data sources"}

        # Normalize for comparison
        excel_processes = set(df_excel['Proceso'].dropna().astype(str).str.strip().str.upper())
        dataset_processes = set(dataset_df['Proceso'].dropna().astype(str).str.strip().str.upper())

        # Subprocess validation
        excel_subprocesses = set()
        dataset_subprocesses = set()

        if "Subproceso" in df_excel.columns:
            excel_subprocesses = set(df_excel['Subproceso'].dropna().astype(str).str.strip().str.upper())

        if "Subproceso" in dataset_df.columns:
            dataset_subprocesses = set(dataset_df['Subproceso'].dropna().astype(str).str.strip().str.upper())

        return {
            "excel_processes": len(excel_processes),
            "dataset_processes": len(dataset_processes),
            "excel_subprocesses": len(excel_subprocesses),
            "dataset_subprocesses": len(dataset_subprocesses),
            "missing_processes_in_dataset": excel_processes - dataset_processes,
            "extra_processes_in_dataset": dataset_processes - excel_processes,
            "missing_subprocesses_in_dataset": excel_subprocesses - dataset_subprocesses,
            "extra_subprocesses_in_dataset": dataset_subprocesses - excel_subprocesses,
            "process_hierarchy_consistent": len(excel_processes - dataset_processes) == 0,
            "subprocess_hierarchy_consistent": len(excel_subprocesses - dataset_subprocesses) == 0,
            "validation_passed": (
                len(excel_processes - dataset_processes) == 0 and
                len(excel_subprocesses - dataset_subprocesses) == 0
            )
        }

    except Exception as e:
        return {"error": f"Validation failed: {e}"}


def get_process_filter_options(dataset_df: pd.DataFrame) -> Dict[str, list]:
    """
    Get validated filter options for process-related UI components

    Args:
        dataset_df: Dataset with process columns

    Returns:
        Dictionary with filter options
    """
    options = {
        "procesos": ["Todos"],
        "subprocesos": ["Todos"],
        "unidades": ["Todos"],
        "tipos_proceso": ["Todos"]
    }

    if "Proceso" in dataset_df.columns:
        procesos = sorted(dataset_df["Proceso"].dropna().astype(str).unique().tolist())
        options["procesos"].extend(procesos)

    if "Subproceso" in dataset_df.columns:
        subprocesos = sorted(dataset_df["Subproceso"].dropna().astype(str).unique().tolist())
        options["subprocesos"].extend(subprocesos)

    if "Unidad" in dataset_df.columns:
        unidades = sorted(dataset_df["Unidad"].dropna().astype(str).unique().tolist())
        options["unidades"].extend(unidades)

    if "Tipo de proceso" in dataset_df.columns:
        tipos = sorted(dataset_df["Tipo de proceso"].dropna().astype(str).unique().tolist())
        options["tipos_proceso"].extend(tipos)

    return options


def apply_process_filters(df: pd.DataFrame, filters: Dict[str, str]) -> pd.DataFrame:
    """
    Apply process-related filters to dataset

    Args:
        df: Dataset to filter
        filters: Dictionary with filter values (use "Todos" for no filter)

    Returns:
        Filtered DataFrame
    """
    df_filtered = df.copy()

    filter_mappings = {
        "proceso": "Proceso",
        "subproceso": "Subproceso",
        "unidad": "Unidad",
        "tipo_proceso": "Tipo de proceso"
    }

    for filter_key, column in filter_mappings.items():
        filter_value = filters.get(filter_key, "Todos")
        if filter_value and filter_value != "Todos" and column in df_filtered.columns:
            df_filtered = df_filtered[df_filtered[column] == filter_value]

    return df_filtered