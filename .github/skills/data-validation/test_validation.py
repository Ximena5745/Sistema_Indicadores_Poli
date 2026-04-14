"""
Unit tests for Data Validation Skill
"""

import pandas as pd
import pytest
from pathlib import Path

# Import the skill functions
import sys
sys.path.append(str(Path(__file__).parent))
from data_validation import (
    enrich_with_process_hierarchy,
    validate_process_sources,
    get_process_filter_options,
    apply_process_filters,
    _normalize_text
)


class TestDataValidationSkill:
    """Test suite for data validation skill functions"""

    @pytest.fixture
    def sample_excel_data(self):
        """Sample data mimicking Subproceso-Proceso-Area.xlsx"""
        return pd.DataFrame({
            "Unidad": ["Unidad A", "Unidad B", "Unidad A"],
            "Proceso": ["Proceso Padre 1", "Proceso Padre 2", "Proceso Padre 1"],
            "Subproceso": ["Subproceso Hijo 1", "Subproceso Hijo 2", "Subproceso Hijo 3"],
            "Tipo de proceso": ["ESTRATÉGICO", "APOYO", "ESTRATÉGICO"]
        })

    @pytest.fixture
    def sample_dataset(self):
        """Sample dataset with subprocess column"""
        return pd.DataFrame({
            "Id": [1, 2, 3],
            "Indicador": ["Indicador 1", "Indicador 2", "Indicador 3"],
            "Subproceso": ["Subproceso Hijo 1", "Subproceso Hijo 2", "Subproceso Nuevo"],
            "Proceso": ["Proceso Viejo 1", "Proceso Viejo 2", "Proceso Viejo 3"]
        })

    def test_normalize_text(self):
        """Test text normalization function"""
        assert _normalize_text("HÉLLO WÖRLD") == "hello world"
        assert _normalize_text("  Test  ") == "test"
        assert _normalize_text("") == ""

    def test_enrich_with_process_hierarchy(self, sample_excel_data, sample_dataset, tmp_path):
        """Test enrichment with process hierarchy"""
        # Save sample Excel data
        excel_path = tmp_path / "test_procesos.xlsx"
        sample_excel_data.to_excel(excel_path, index=False)

        # Enrich dataset
        enriched = enrich_with_process_hierarchy(sample_dataset.copy(), excel_path)

        # Check that processes were updated
        assert "Proceso" in enriched.columns
        assert "Unidad" in enriched.columns
        assert "Tipo de proceso" in enriched.columns

        # Check specific enrichments
        row1 = enriched[enriched["Id"] == 1].iloc[0]
        assert row1["Proceso"] == "Proceso Padre 1"
        assert row1["Unidad"] == "Unidad A"
        assert row1["Tipo de proceso"] == "ESTRATÉGICO"

    def test_validate_process_sources(self, sample_excel_data, sample_dataset, tmp_path):
        """Test process source validation"""
        excel_path = tmp_path / "test_procesos.xlsx"
        sample_excel_data.to_excel(excel_path, index=False)

        result = validate_process_sources(sample_dataset, excel_path)

        assert "excel_processes" in result
        assert "dataset_processes" in result
        assert "validation_passed" in result
        assert isinstance(result["validation_passed"], bool)

    def test_get_process_filter_options(self, sample_dataset):
        """Test filter options generation"""
        # Add required columns to sample dataset
        sample_dataset["Unidad"] = ["Unidad A", "Unidad B", "Unidad C"]
        sample_dataset["Tipo de proceso"] = ["ESTRATÉGICO", "APOYO", "ESTRATÉGICO"]

        options = get_process_filter_options(sample_dataset)

        assert "procesos" in options
        assert "subprocesos" in options
        assert "unidades" in options
        assert "tipos_proceso" in options

        assert options["procesos"][0] == "Todos"
        assert len(options["procesos"]) > 1

    def test_apply_process_filters(self, sample_dataset):
        """Test filter application"""
        # Add filter columns
        sample_dataset["Unidad"] = ["Unidad A", "Unidad B", "Unidad A"]

        filters = {"unidad": "Unidad A"}
        filtered = apply_process_filters(sample_dataset, filters)

        assert len(filtered) == 2
        assert all(filtered["Unidad"] == "Unidad A")

    def test_missing_excel_file(self, sample_dataset, tmp_path):
        """Test behavior with missing Excel file"""
        missing_path = tmp_path / "missing.xlsx"
        result = enrich_with_process_hierarchy(sample_dataset, missing_path)

        # Should return original dataset unchanged
        pd.testing.assert_frame_equal(result, sample_dataset)


if __name__ == "__main__":
    # Run basic validation
    print("Running basic validation...")

    # Test normalize function
    assert _normalize_text("TÉST") == "test"
    print("✅ Text normalization works")

    print("✅ All basic tests passed")