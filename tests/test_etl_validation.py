"""
Tests básicos para módulos críticos del ETL.
Ejecutar: python -m pytest tests/test_etl_validation.py -v
"""

import pytest
import pandas as pd
import sys
from pathlib import Path

# Agregar directorio raíz al path
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

from scripts.etl.validation_gate import (
    ValidationResult,
    validar_consolidado_api_entrada,
    validar_consolidado_salida,
)


class TestValidationResult:
    """Tests para la clase ValidationResult."""
    
    def test_result_ok(self):
        result = ValidationResult(status="ok")
        assert result.status == "ok"
        assert result.error_count == 0
        assert result.warning_count == 0
    
    def test_result_with_errors(self):
        result = ValidationResult(
            status="error",
            error_count=2,
            errors=["Error 1", "Error 2"]
        )
        assert result.status == "error"
        assert result.error_count == 2
        assert len(result.errors) == 2
    
    def test_result_str(self):
        result = ValidationResult(status="ok")
        assert "Status: ok" in str(result)


class TestValidarConsolidadoAPIEntrada:
    """Tests para validar_consolidado_api_entrada."""
    
    def test_valid_data(self):
        df = pd.DataFrame({
            "ID": ["1", "2", "3"],
            "fecha": ["2025-01-01", "2025-02-01", "2025-03-01"],
            "resultado": [0.85, 0.90, 0.75]
        })
        result = validar_consolidado_api_entrada(df, verbose=False)
        assert result.status in ["ok", "warning"]
    
    def test_missing_columns(self):
        df = pd.DataFrame({
            "ID": ["1", "2"],
            "fecha": ["2025-01-01", "2025-02-01"]
        })
        result = validar_consolidado_api_entrada(df, verbose=False)
        # Debería fallar por columna faltante
        assert result.status == "error"
        assert result.error_count > 0
    
    def test_empty_dataframe(self):
        df = pd.DataFrame()
        result = validar_consolidado_api_entrada(df, verbose=False)
        assert result.status == "error"
    
    def test_null_ids(self):
        df = pd.DataFrame({
            "ID": [None, "1", "2"],
            "fecha": ["2025-01-01", "2025-02-01", "2025-03-01"],
            "resultado": [0.85, 0.90, 0.75]
        })
        result = validar_consolidado_api_entrada(df, verbose=False)
        # Nulos en ID es error
        assert result.status == "error"
    
    def test_duplicate_ids_warning(self):
        df = pd.DataFrame({
            "ID": ["1", "1", "2"],
            "fecha": ["2025-01-01", "2025-01-01", "2025-02-01"],
            "resultado": [0.85, 0.90, 0.75]
        })
        result = validar_consolidado_api_entrada(df, verbose=False)
        # Duplicados son warning, no error
        assert result.warning_count > 0


class TestValidarConsolidadoSalida:
    """Tests para validar_consolidado_salida."""
    
    def test_valid_output(self):
        # Crear 100 filas para pasar la validación de tamaño mínimo
        data = {
            "Id": [str(i) for i in range(100)],
            "Fecha": [f"2025-{(i%12)+1:02d}-01" for i in range(100)],
            "Meta": [1.0] * 100,
            "Ejecucion": [0.85] * 100,
            "Cumplimiento": [0.85] * 100,
            "Categoria": ["Verde"] * 100,
            "Anio": [2025] * 100,
            "Mes": [(i%12)+1 for i in range(100)]
        }
        df = pd.DataFrame(data)
        result = validar_consolidado_salida(df, min_rows=50)
        assert result.status == "ok"
    
    def test_negative_values_warning(self):
        df = pd.DataFrame({
            "Id": ["1", "2"],
            "Fecha": ["2025-01-01", "2025-02-01"],
            "Meta": [-0.5, 1.0],  # Negativo
            "Ejecucion": [0.85, 0.90],
            "Cumplimiento": [0.85, 0.90],
            "Categoria": ["Verde", "Verde"],
            "Anio": [2025, 2025],
            "Mes": [1, 2]
        })
        result = validar_consolidado_salida(df)
        # Valores negativos son warning
        assert result.warning_count > 0
    
    def test_over_max_values_warning(self):
        df = pd.DataFrame({
            "Id": ["1", "2"],
            "Fecha": ["2025-01-01", "2025-02-01"],
            "Meta": [1.5, 1.0],  # Mayor a 1.3
            "Ejecucion": [0.85, 0.90],
            "Cumplimiento": [0.85, 0.90],
            "Categoria": ["Verde", "Verde"],
            "Anio": [2025, 2025],
            "Mes": [1, 2]
        })
        result = validar_consolidado_salida(df)
        # Valores > 1.3 son warning
        assert result.warning_count > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
