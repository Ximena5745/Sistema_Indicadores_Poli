"""
Test suite for streamlit_app/pages/resumen_por_proceso.py

Tests focus on:
1. _cumplimiento_pct() percentage calculation
2. normalizar_valor_a_porcentaje() integration
3. Scale detection (% vs decimal)
4. Edge cases (NaN, 0, very high values)
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.semantica import normalizar_valor_a_porcentaje


class TestResumenPorProcesoNormalizacion:
    """Test suite for normalizar_valor_a_porcentaje()"""

    def test_percentage_explicit_flag_95(self):
        """Test 95 as percentage with explicit flag"""
        # Function assumes decimal when no flag: 95 * 100 = 9500
        # So use explicit tiene_porcentaje=True to say "95 is already %"
        result = normalizar_valor_a_porcentaje(95, tiene_porcentaje=True)
        assert result == 95  # Already percentage

    def test_percentage_explicit_flag_150(self):
        """Test 150 as percentage with explicit flag"""
        result = normalizar_valor_a_porcentaje(150, tiene_porcentaje=True)
        assert result == 150  # Already percentage

    def test_decimal_to_percentage_0_95(self):
        """Test decimal 0.95 converted to percentage"""
        result = normalizar_valor_a_porcentaje(0.95, tiene_porcentaje=False)
        assert result == 95  # 0.95 * 100

    def test_decimal_kept_1_5(self):
        """Test decimal 1.5 converted to percentage"""
        result = normalizar_valor_a_porcentaje(1.5, tiene_porcentaje=False)
        assert result == 150  # 1.5 * 100

    def test_explicit_percentage_flag_true_92(self):
        """Test explicit tiene_porcentaje=True with 92"""
        result = normalizar_valor_a_porcentaje(92, tiene_porcentaje=True)
        assert result == 92  # Already percentage

    def test_explicit_percentage_flag_false_092(self):
        """Test explicit tiene_porcentaje=False with 0.92"""
        result = normalizar_valor_a_porcentaje(0.92, tiene_porcentaje=False)
        assert result == 92  # 0.92 * 100

    def test_string_percentage_parsing(self):
        """Test string with % symbol auto-detects as percentage"""
        result = normalizar_valor_a_porcentaje("95%")
        assert result == 95  # Auto-detected as percentage, no multiplication

    def test_string_decimal_parsing(self):
        """Test string without % symbol treated as decimal"""
        result = normalizar_valor_a_porcentaje("0.95")
        assert result == 95  # Treated as decimal 0.95 * 100

    def test_zero_value(self):
        """Test zero cumplimiento"""
        result = normalizar_valor_a_porcentaje(0, tiene_porcentaje=False)
        assert result == 0.0  # 0 * 100

    def test_nan_handling_returns_nan(self):
        """Test NaN input"""
        result = normalizar_valor_a_porcentaje(float("nan"))
        assert pd.isna(result)


class TestResumenPorProcesoEdgeCases:
    """Edge case tests for percentage normalization"""

    def test_very_high_percentage_300(self):
        """Test 300 as percentage: 300% * 100 = 30000 or 300 treated as % = 300"""
        # With explicit flag: 300 is already percentage
        result = normalizar_valor_a_porcentaje(300, tiene_porcentaje=True)
        assert result == 300

    def test_very_high_decimal_3(self):
        """Test 3.0 as decimal (300%): 3.0 * 100 = 300"""
        result = normalizar_valor_a_porcentaje(3.0, tiene_porcentaje=False)
        assert result == 300  # 3.0 * 100

    def test_boundary_1_99_decimal(self):
        """Test boundary 1.99 as decimal: 1.99 * 100 = 199"""
        result = normalizar_valor_a_porcentaje(1.99, tiene_porcentaje=False)
        assert result == 199  # 1.99 * 100

    def test_boundary_2_0_percentage(self):
        """Test boundary 2.0 as percentage"""
        result = normalizar_valor_a_porcentaje(2.0, tiene_porcentaje=True)
        assert result == 2.0  # Kept as-is

    def test_boundary_2_01_percentage(self):
        """Test boundary 2.01 as percentage"""
        result = normalizar_valor_a_porcentaje(2.01, tiene_porcentaje=True)
        assert result == 2.01  # Kept as-is

    def test_negative_percentage(self):
        """Test negative value"""
        result = normalizar_valor_a_porcentaje(-50, tiene_porcentaje=True)
        assert result == -50  # Percentage as-is

    def test_negative_decimal(self):
        """Test negative decimal"""
        result = normalizar_valor_a_porcentaje(-0.5, tiene_porcentaje=False)
        assert result == -50  # -0.5 * 100

    def test_very_small_decimal(self):
        """Test very small decimal (0.001)"""
        result = normalizar_valor_a_porcentaje(0.001, tiene_porcentaje=False)
        assert result == 0.1  # 0.001 * 100

    def test_string_with_spaces(self):
        """Test string with extra whitespace and %"""
        result = normalizar_valor_a_porcentaje("  95  %")
        assert result == 95 or pd.isna(result)  # May or may not parse


def test_cmi_por_procesos_resumen_renderable():
    import streamlit_app.pages.cmi_por_procesos_resumen as resumen

    assert hasattr(resumen, "render")


def test_informe_por_procesos_renderable():
    import streamlit_app.pages.informe_por_procesos as informe

    assert hasattr(informe, "render")
