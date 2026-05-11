"""
services/cmi_filters/ — CMI filtering logic (Estratégico vs Procesos)

Refactorización PHASE 2 (342L → 3 modules):
  - loaders.py: Load CMI worksheet and Kawak IDs (95L)
  - utils.py: Normalize flags and IDs (55L)
  - filters.py: CMI filtering business logic (180L)

Responsibility unique per module:
  - loaders: Load data from Excel and Kawak sources
  - utils: Normalize boolean/ID values
  - filters: Implement filtration rules

Business Rules:
  - CMI Estratégico: Indicadores Plan estrategico == 1 AND Proyecto != 1
  - CMI Procesos: Subprocesos == 1 (with optional Kawak cross-validation)

Usage:
    from services.cmi_filters import (
        filter_df_for_cmi_estrategico,
        filter_df_for_cmi_procesos,
        get_cmi_estrategico_ids,
        get_cmi_procesos_ids
    )

    # Filter a DataFrame
    df_estrategico = filter_df_for_cmi_estrategico(df, id_column="Id")
    df_procesos = filter_df_for_cmi_procesos(df, id_column="Id")

    # Get only the valid IDs
    ids_estrategico = get_cmi_estrategico_ids()  # returns set[str]
    ids_procesos = get_cmi_procesos_ids()        # returns set[str]
"""

# Re-export for backward compatibility
from .filters import (
    filter_df_for_cmi_estrategico,
    filter_df_for_cmi_procesos,
    filter_df_for_procesos,
    get_cmi_estrategico_ids,
    get_cmi_procesos_ids,
    get_cmi_procesos_subprocesos,
)
from .loaders import load_cmi_worksheet, load_kawak_active_ids

__all__ = [
    "load_kawak_active_ids",
    "load_cmi_worksheet",
    "get_cmi_estrategico_ids",
    "get_cmi_procesos_ids",
    "get_cmi_procesos_subprocesos",
    "filter_df_for_cmi_estrategico",
    "filter_df_for_cmi_procesos",
    "filter_df_for_procesos",
]
