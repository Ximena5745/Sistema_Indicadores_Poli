"""
services/data_validation.py
============================

Data validation service — checks data quality against data_contracts.yaml.

Proporciona funciones para validar fuentes de datos y reportar issues.

Usage:
    from services.data_validation import validate_dataset, ValidationReport

    report = validate_dataset(df, source_name="resultados_consolidados")
    if not report.is_valid:
        report.print_issues()
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd
import yaml

_COLUMN_ALIASES: Dict[str, Set[str]] = {
    "ano": {"ano", "año", "a�o", "anio", "ano_archivo", "año_archivo", "a�o_archivo"},
    "anio": {"ano", "año", "a�o", "anio", "ano_archivo", "año_archivo", "a�o_archivo"},
    "id": {"id"},
    "fecha": {"fecha", "fecha_corte"},
    "valor": {"valor", "resultado"},
}

_CATEGORICAL_SYNONYMS: Dict[str, str] = {
    "positivo": "ascendente",
    "negativo": "descendente",
    "gestion": "gestion",
    "gestion": "gestion",
    "gesti n": "gestion",
    "estrat gico": "estrategico",
    "estrat eacute gico": "estrategico",
}


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class ValidationIssue:
    """Single data quality issue found during validation."""

    level: str  # "error" | "warning" | "info"
    rule: str  # Name of rule that failed
    sheet: Optional[str] = None
    column: Optional[str] = None
    row_count: int = 0
    description: str = ""
    values_sample: List[Any] = field(default_factory=list)  # Problematic values

    def __str__(self) -> str:
        level_icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}[self.level]
        sheet_info = f" [{self.sheet}]" if self.sheet else ""
        col_info = f" [{self.column}]" if self.column else ""
        sample_info = f" | Examples: {self.values_sample[:3]}" if self.values_sample else ""
        return (
            f"{level_icon} {self.rule}{sheet_info}{col_info} — {self.description} "
            f"({self.row_count} rows){sample_info}"
        )


@dataclass
class ValidationReport:
    """Report of all validation issues for a dataset."""

    source_name: str
    dataset_shape: tuple
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    issues: List[ValidationIssue] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        """True if no errors (warnings ok)."""
        return not any(i.level == "error" for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "warning")

    def add_issue(self, issue: ValidationIssue) -> None:
        """Register an issue."""
        self.issues.append(issue)

    def print_issues(self, level_filter: Optional[str] = None) -> None:
        """Print all issues (optionally filtered by level)."""
        print(f"\n📋 DataValidation Report — {self.source_name}")
        print(f"   Shape: {self.dataset_shape}")
        print(f"   Issues: {self.error_count} errors, {self.warning_count} warnings")
        print()

        for issue in self.issues:
            if level_filter and issue.level != level_filter:
                continue
            print(f"   {issue}")

        print()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict (for JSON export)."""
        return {
            "source_name": self.source_name,
            "timestamp": self.timestamp,
            "dataset_shape": self.dataset_shape,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "is_valid": self.is_valid,
            "issues": [
                {
                    "level": i.level,
                    "rule": i.rule,
                    "sheet": i.sheet,
                    "column": i.column,
                    "row_count": int(i.row_count),
                    "description": i.description,
                }
                for i in self.issues
            ],
        }


# ============================================================================
# VALIDATORS
# ============================================================================


def _load_contracts() -> Dict[str, Any]:
    """Load data contracts from config/data_contracts.yaml."""
    contracts_path = Path(__file__).parent.parent / "config" / "data_contracts.yaml"
    if not contracts_path.exists():
        raise FileNotFoundError(f"Data contracts not found: {contracts_path}")

    with open(contracts_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _normalize_text(value: Any) -> str:
    """Normalize text for tolerant comparisons across headers and categorical values."""
    if value is None:
        return ""

    text = str(value).strip()
    text = (
        text.replace("A�o", "Año")
        .replace("a�o", "año")
        .replace("Gesti�n", "Gestión")
        .replace("gesti�n", "gestión")
        .replace("&eacute;", "é")
        .replace("&Eacute;", "É")
    )
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.casefold()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _find_matching_column(columns: pd.Index, contract_column: str) -> Optional[str]:
    """Find a dataframe column matching a contract column using normalized names and aliases."""
    normalized_contract = _normalize_text(contract_column)
    aliases = {normalized_contract}
    aliases.update(
        _normalize_text(alias) for alias in _COLUMN_ALIASES.get(normalized_contract, set())
    )

    for column in columns:
        normalized_column = _normalize_text(column)
        if normalized_column in aliases:
            return str(column)

    return None


def _normalize_allowed_values(values: List[Any]) -> Set[str]:
    normalized_values: Set[str] = set()
    for value in values:
        normalized = _normalize_text(value)
        normalized_values.add(_CATEGORICAL_SYNONYMS.get(normalized, normalized))
    return normalized_values


def _normalize_series_values(series: pd.Series) -> pd.Series:
    return series.astype(str).map(
        lambda value: _CATEGORICAL_SYNONYMS.get(_normalize_text(value), _normalize_text(value))
    )


def _iter_hojas(
    contract: Dict[str, Any],
    target_sheet: Optional[str] = None,
) -> List[tuple[str, Dict[str, Any]]]:
    hojas = contract.get("hojas", {})
    if target_sheet is not None:
        hoja_spec = hojas.get(target_sheet)
        return [(target_sheet, hoja_spec or {})]
    return list(hojas.items())


def validate_required_columns(
    df: pd.DataFrame,
    contract: Dict[str, Any],
    target_sheet: Optional[str] = None,
) -> List[ValidationIssue]:
    """Check that required columns exist."""
    issues = []

    for hoja_name, hoja_spec in _iter_hojas(contract, target_sheet):
        columnas = hoja_spec.get("columnas", {})

        for col_name, col_spec in columnas.items():
            if col_spec.get("requerida", False):
                actual_col = _find_matching_column(df.columns, col_name)
                if actual_col is None:
                    issues.append(
                        ValidationIssue(
                            level="error",
                            rule="Required Column Missing",
                            sheet=hoja_name,
                            column=col_name,
                            description=f"Required column '{col_name}' not found",
                        )
                    )

    return issues


def validate_column_types(
    df: pd.DataFrame,
    contract: Dict[str, Any],
    target_sheet: Optional[str] = None,
) -> List[ValidationIssue]:
    """Check data types match contract."""
    issues = []

    for hoja_name, hoja_spec in _iter_hojas(contract, target_sheet):
        columnas = hoja_spec.get("columnas", {})

        for col_name, col_spec in columnas.items():
            actual_col = _find_matching_column(df.columns, col_name)
            if actual_col is None:
                continue

            col_type = col_spec.get("tipo", "string")
            col_data = df[actual_col].dropna()

            # Type check (basic)
            if col_type == "integer":
                non_int = col_data[~col_data.astype(str).str.match(r"^-?\d+$")]
                if len(non_int) > 0:
                    issues.append(
                        ValidationIssue(
                            level="warning",
                            rule="Type Mismatch",
                            sheet=hoja_name,
                            column=col_name,
                            row_count=len(non_int),
                            description=f"Column '{col_name}' should be integer but found non-integers",
                            values_sample=non_int.unique()[:3].tolist(),
                        )
                    )

            elif col_type == "float":
                try:
                    col_data.astype(float)
                except (ValueError, TypeError):
                    non_float = col_data[pd.to_numeric(col_data, errors="coerce").isna()]
                    issues.append(
                        ValidationIssue(
                            level="warning",
                            rule="Type Mismatch",
                            sheet=hoja_name,
                            column=col_name,
                            row_count=len(non_float),
                            description=f"Column '{col_name}' should be float but found non-floats",
                            values_sample=non_float.unique()[:3].tolist(),
                        )
                    )

    return issues


def validate_categorical_values(
    df: pd.DataFrame,
    contract: Dict[str, Any],
    target_sheet: Optional[str] = None,
) -> List[ValidationIssue]:
    """Check categorical values are in allowed set."""
    issues = []

    for hoja_name, hoja_spec in _iter_hojas(contract, target_sheet):
        columnas = hoja_spec.get("columnas", {})

        for col_name, col_spec in columnas.items():
            actual_col = _find_matching_column(df.columns, col_name)
            if actual_col is None:
                continue

            if col_spec.get("tipo") != "categorical":
                continue

            valores_permitidos = col_spec.get("valores_permitidos", [])
            if not valores_permitidos:
                continue

            normalized_allowed = _normalize_allowed_values(valores_permitidos)
            col_data = df[actual_col].dropna()
            normalized_data = _normalize_series_values(col_data)
            invalid_mask = ~normalized_data.isin(normalized_allowed)
            invalid_values = col_data[invalid_mask]

            if len(invalid_values) > 0:
                issues.append(
                    ValidationIssue(
                        level="warning",
                        rule="Invalid Categorical Value",
                        sheet=hoja_name,
                        column=col_name,
                        row_count=len(invalid_values),
                        description=f"Column '{col_name}' has values outside allowed set: {valores_permitidos}",
                        values_sample=invalid_values.unique()[:3].tolist(),
                    )
                )

    return issues


def validate_null_constraints(
    df: pd.DataFrame,
    contract: Dict[str, Any],
    target_sheet: Optional[str] = None,
) -> List[ValidationIssue]:
    """Check null value constraints."""
    issues = []

    for hoja_name, hoja_spec in _iter_hojas(contract, target_sheet):
        columnas = hoja_spec.get("columnas", {})

        for col_name, col_spec in columnas.items():
            actual_col = _find_matching_column(df.columns, col_name)
            if actual_col is None:
                continue

            if col_spec.get("requerida", False):
                null_count = df[actual_col].isna().sum()
                if null_count > 0:
                    issues.append(
                        ValidationIssue(
                            level="error",
                            rule="Null in Required Column",
                            sheet=hoja_name,
                            column=col_name,
                            row_count=null_count,
                            description=f"Column '{col_name}' has {null_count} null values but is required",
                        )
                    )

    return issues


def validate_numeric_ranges(
    df: pd.DataFrame,
    contract: Dict[str, Any],
    target_sheet: Optional[str] = None,
) -> List[ValidationIssue]:
    """Check minimum/maximum value constraints."""
    issues = []

    for hoja_name, hoja_spec in _iter_hojas(contract, target_sheet):
        columnas = hoja_spec.get("columnas", {})

        for col_name, col_spec in columnas.items():
            actual_col = _find_matching_column(df.columns, col_name)
            if actual_col is None:
                continue

            col_data = pd.to_numeric(df[actual_col], errors="coerce").dropna()

            # Min check
            min_val = col_spec.get("min")
            if min_val is not None:
                below_min = col_data[col_data < min_val]
                if len(below_min) > 0:
                    issues.append(
                        ValidationIssue(
                            level="warning",
                            rule="Value Below Minimum",
                            sheet=hoja_name,
                            column=col_name,
                            row_count=len(below_min),
                            description=f"Column '{col_name}' has {len(below_min)} values < {min_val}",
                            values_sample=below_min.unique()[:3].tolist(),
                        )
                    )

            # Max check
            max_val = col_spec.get("max")
            if max_val is not None:
                above_max = col_data[col_data > max_val]
                if len(above_max) > 0:
                    issues.append(
                        ValidationIssue(
                            level="warning",
                            rule="Value Above Maximum",
                            sheet=hoja_name,
                            column=col_name,
                            row_count=len(above_max),
                            description=f"Column '{col_name}' has {len(above_max)} values > {max_val}",
                            values_sample=above_max.unique()[:3].tolist(),
                        )
                    )

    return issues


# ============================================================================
# PUBLIC API
# ============================================================================


def validate_dataset(
    df: pd.DataFrame,
    source_name: str,
    sheet_name: Optional[str] = None,
) -> ValidationReport:
    """
    Validate a dataset against its data contract.

    Args:
        df: DataFrame to validate
        source_name: Name of data source (key in data_contracts.yaml)

    Returns:
        ValidationReport with all issues found
    """
    contracts = _load_contracts()

    if source_name not in contracts:
        report = ValidationReport(
            source_name=source_name,
            dataset_shape=df.shape,
        )
        report.add_issue(
            ValidationIssue(
                level="warning",
                rule="No Contract Found",
                description=f"No contract defined for '{source_name}' in data_contracts.yaml",
            )
        )
        return report

    contract = contracts[source_name]
    report = ValidationReport(
        source_name=source_name,
        dataset_shape=df.shape,
    )

    # Run all validators
    all_issues = []
    all_issues.extend(validate_required_columns(df, contract, target_sheet=sheet_name))
    all_issues.extend(validate_column_types(df, contract, target_sheet=sheet_name))
    all_issues.extend(validate_categorical_values(df, contract, target_sheet=sheet_name))
    all_issues.extend(validate_null_constraints(df, contract, target_sheet=sheet_name))
    all_issues.extend(validate_numeric_ranges(df, contract, target_sheet=sheet_name))

    for issue in all_issues:
        report.add_issue(issue)

    return report


def validate_source_file(
    source_name: str,
    file_path: Optional[Path] = None,
) -> ValidationReport:
    """Validate a configured source file, including every declared sheet."""
    contracts = _load_contracts()

    if source_name not in contracts:
        raise KeyError(f"No contract defined for '{source_name}'")

    contract = contracts[source_name]
    source_path = file_path or (Path(__file__).parent.parent / contract["archivo"])
    source_path = Path(source_path)

    aggregate = ValidationReport(source_name=source_name, dataset_shape=(0, 0))

    if not source_path.exists():
        aggregate.add_issue(
            ValidationIssue(
                level="error",
                rule="Source File Missing",
                description=f"Configured file not found: {source_path}",
            )
        )
        return aggregate

    total_rows = 0
    total_cols = 0

    if contract.get("tipo") == "excel":
        workbook = pd.ExcelFile(source_path)
        declared_sheets = contract.get("hojas", {})
        for sheet_name, sheet_spec in declared_sheets.items():
            if sheet_name not in workbook.sheet_names:
                aggregate.add_issue(
                    ValidationIssue(
                        level="error",
                        rule="Required Sheet Missing",
                        sheet=sheet_name,
                        description=f"Sheet '{sheet_name}' not found in {source_path.name}",
                    )
                )
                continue

            df = pd.read_excel(source_path, sheet_name=sheet_name)
            total_rows += len(df)
            total_cols = max(total_cols, len(df.columns))
            sheet_report = validate_dataset(df, source_name, sheet_name=sheet_name)
            for issue in sheet_report.issues:
                aggregate.add_issue(issue)
    else:
        df = pd.read_csv(source_path)
        total_rows = len(df)
        total_cols = len(df.columns)
        sheet_report = validate_dataset(df, source_name)
        for issue in sheet_report.issues:
            aggregate.add_issue(issue)

    aggregate.dataset_shape = (total_rows, total_cols)
    return aggregate


def validate_all_sources() -> Dict[str, ValidationReport]:
    """Validate every configured source and return reports keyed by source name."""
    contracts = _load_contracts()
    reports: Dict[str, ValidationReport] = {}
    for source_name, contract in contracts.items():
        if not isinstance(contract, dict) or "archivo" not in contract:
            continue
        reports[source_name] = validate_source_file(source_name)
    return reports


def check_data_freshness(
    df: pd.DataFrame,
    max_age_days: int = 7,
) -> bool:
    """
    Simple freshness check — look for date column and ensure not too old.

    Args:
        df: DataFrame to check
        max_age_days: Maximum allowed age in days

    Returns:
        True if data is fresh, False otherwise
    """
    # Look for datetime columns
    date_cols = df.select_dtypes(include=["datetime64"]).columns

    if len(date_cols) == 0:
        return True  # No date column, assume fresh

    latest_date = df[date_cols[0]].max()
    age = (datetime.now() - latest_date).days

    return age <= max_age_days


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python services/data_validation.py <xlsx_file> <source_name>")
        print("   or: python services/data_validation.py --all")
        sys.exit(1)

    if sys.argv[1] == "--all":
        reports = validate_all_sources()
        has_issues = False
        for report in reports.values():
            report.print_issues()
            if report.issues:
                has_issues = True
        sys.exit(1 if has_issues else 0)

    file_path = Path(sys.argv[1])
    source_name = sys.argv[2] if len(sys.argv) > 2 else "unknown"

    report = validate_source_file(source_name, file_path=file_path)
    report.print_issues()

    if report.issues:
        sys.exit(1)
