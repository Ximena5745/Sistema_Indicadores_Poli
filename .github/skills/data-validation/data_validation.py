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

        # Normalize subprocess names for merge
        df_procesos["Subproceso_norm"] = df_procesos["Subproceso"].astype(str).str.strip()
        df["Subproceso_norm"] = df["Subproceso"].astype(str).str.strip()

        # Merge by subprocess to get parent process
        merge_cols = ["Subproceso_norm", "Proceso", "Unidad", "Tipo de proceso"]
        df = df.merge(
            df_procesos[merge_cols].drop_duplicates("Subproceso_norm"),
            on="Subproceso_norm",
            how="left",
            suffixes=("", "_excel")
        )

        # Use Excel data if available, otherwise keep existing
        df["Proceso"] = df["Proceso_excel"].fillna(df["Proceso"])
        df["Unidad"] = df["Unidad"].fillna("")
        df["Tipo de proceso"] = df["Tipo de proceso"].fillna("")

        # Clean up temporary columns
        df = df.drop(columns=["Subproceso_norm", "Proceso_excel"], errors="ignore")

        

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