---
name: data-validation
description: '**DATA VALIDATION SKILL** — Validate and enrich dataset sources using official reference files. USE FOR: ensuring data consistency with master sources like Subproceso-Proceso-Area.xlsx; validating process hierarchies; enriching datasets with official process/subprocess mappings; checking data source integrity. DO NOT USE FOR: general data analysis; creating new data sources; modifying existing business logic. INVOKES: pandas operations, file system tools for data validation and enrichment.'
---

# Data Validation Skill

## Overview

This skill provides reusable logic for validating and enriching datasets using official reference sources, particularly `Subproceso-Proceso-Area.xlsx` as the master source for process and subprocess hierarchies.

## Key Components

### Process Hierarchy Validation

The skill implements the official hierarchy where:
- **Proceso** = Parent (Padre)
- **Subproceso** = Child (Hijo)

### Data Enrichment Logic

```python
def enrich_with_process_hierarchy(df: pd.DataFrame, excel_path: Path) -> pd.DataFrame:
    """
    Enrich dataset with official process hierarchy from Subproceso-Proceso-Area.xlsx

    Args:
        df: Dataset with 'Subproceso' column
        excel_path: Path to Subproceso-Proceso-Area.xlsx

    Returns:
        Enriched DataFrame with 'Proceso', 'Unidad', 'Tipo de proceso' columns
    """
    try:
        df_procesos = pd.read_excel(excel_path, engine="openpyxl")

        # Normalize names for merge
        df_procesos["Subproceso_norm"] = df_procesos["Subproceso"].astype(str).str.strip()
        df["Subproceso_norm"] = df["Subproceso"].astype(str).str.strip()

        # Merge by subprocess to get parent process
        df = df.merge(
            df_procesos[["Subproceso_norm", "Proceso", "Unidad", "Tipo de proceso"]]
            .drop_duplicates("Subproceso_norm"),
            on="Subproceso_norm",
            how="left",
            suffixes=("", "_excel")
        )

        # Use Excel process if available, otherwise keep existing
        df["Proceso"] = df["Proceso_excel"].fillna(df["Proceso"])
        df["Unidad"] = df["Unidad"].fillna("")
        df["Tipo de proceso"] = df["Tipo de proceso"].fillna("")

        # Clean up temporary columns
        df = df.drop(columns=["Subproceso_norm", "Proceso_excel"])

    except Exception as e:
        st.warning(f"Could not enrich with process hierarchy: {e}")

    return df
```

### Validation Functions

```python
def validate_process_sources(dataset_df: pd.DataFrame, excel_path: Path) -> dict:
    """
    Validate that dataset processes match official Excel source

    Returns:
        {
            "excel_processes": int,
            "dataset_processes": int,
            "missing_in_dataset": set,
            "extra_in_dataset": set,
            "hierarchy_consistent": bool
        }
    """
    df_excel = pd.read_excel(excel_path, engine="openpyxl")

    excel_processes = set(df_excel['Proceso'].dropna().str.strip().str.upper())
    dataset_processes = set(dataset_df['Proceso'].dropna().str.strip().str.upper())

    return {
        "excel_processes": len(excel_processes),
        "dataset_processes": len(dataset_processes),
        "missing_in_dataset": excel_processes - dataset_processes,
        "extra_in_dataset": dataset_processes - excel_processes,
        "hierarchy_consistent": len(excel_processes - dataset_processes) == 0
    }
```

## Usage Examples

### In Data Loader

```python
# In services/data_loader.py
@st.cache_data(ttl=300, show_spinner="Loading and validating data...")
def cargar_dataset() -> pd.DataFrame:
    # ... existing loading logic ...

    # Apply data validation skill
    from .data_validation import enrich_with_process_hierarchy
    df = enrich_with_process_hierarchy(df, DATA_RAW / "Subproceso-Proceso-Area.xlsx")

    return df
```

### Validation Check

```python
# Validate data sources
validation_result = validate_process_sources(df, DATA_RAW / "Subproceso-Proceso-Area.xlsx")
if not validation_result["hierarchy_consistent"]:
    st.warning(f"⚠️ {len(validation_result['missing_in_dataset'])} processes missing from dataset")
```

## Integration Points

- **services/data_loader.py**: Use `enrich_with_process_hierarchy()` in `cargar_dataset()`
- **Data validation**: Call `validate_process_sources()` to check data integrity
- **Process filters**: Ensure UI filters use validated process lists

## File Structure

```
.github/skills/data-validation/
├── SKILL.md                    # This file
├── data_validation.py          # Reusable functions
└── test_validation.py          # Unit tests
```

## Dependencies

- pandas
- openpyxl
- pathlib
- streamlit (for UI feedback)

## Best Practices

1. **Cache enrichment**: Use `@st.cache_data` for expensive operations
2. **Error handling**: Gracefully handle missing files or columns
3. **Normalization**: Always strip and normalize text for reliable matching
4. **Validation**: Run validation checks in development/testing environments
5. **Documentation**: Update this skill when new reference sources are added