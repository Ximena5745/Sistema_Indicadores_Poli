"""
Tests for Problema #9: Hardcoding lambda en gestion_om.py (VERSIÓN CORREGIDA)

LÓGICA CORRECTA:
- Si tiene "%": es porcentaje → mantener valor
- Si NO tiene "%": es decimal → multiplicar por 100

Cumplimiento SIEMPRE es porcentaje (0-130%).
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.semantica import normalizar_valor_a_porcentaje


class TestNormalizarValorP9Simple:
    """Tests for corrected normalizar_valor_a_porcentaje() API."""

    def test_decimal_0_5_to_50(self):
        """0.5 (decimal) → 50%"""
        result = normalizar_valor_a_porcentaje(0.5, tiene_porcentaje=False)
        assert result == 50.0

    def test_decimal_0_95_to_95(self):
        """0.95 (decimal) → 95%"""
        result = normalizar_valor_a_porcentaje(0.95, tiene_porcentaje=False)
        assert result == 95.0

    def test_decimal_1_3_to_130(self):
        """1.3 (decimal, tope) → 130%"""
        result = normalizar_valor_a_porcentaje(1.3, tiene_porcentaje=False)
        assert result == 130.0

    def test_porcentaje_50_stays_50(self):
        """50 (porcentaje) → 50 (sin cambio)"""
        result = normalizar_valor_a_porcentaje(50.0, tiene_porcentaje=True)
        assert result == 50.0

    def test_porcentaje_95_stays_95(self):
        """95 (porcentaje) → 95 (sin cambio)"""
        result = normalizar_valor_a_porcentaje(95.0, tiene_porcentaje=True)
        assert result == 95.0

    def test_porcentaje_100_stays_100(self):
        """100 (porcentaje) → 100 (sin cambio)"""
        result = normalizar_valor_a_porcentaje(100.0, tiene_porcentaje=True)
        assert result == 100.0

    def test_string_85pct_detecta_pct(self):
        """'85%' → detecta % automáticamente → 85"""
        result = normalizar_valor_a_porcentaje("85%")
        assert result == 85.0

    def test_string_0_85_sin_pct(self):
        """'0.85' → detecta que NO tiene % → 85"""
        result = normalizar_valor_a_porcentaje("0.85")
        assert result == 85.0

    def test_nan_handled(self):
        """NaN → NaN"""
        result = normalizar_valor_a_porcentaje(np.nan)
        assert pd.isna(result)

    def test_zero_decimal_to_zero(self):
        """0.0 (decimal) → 0"""
        result = normalizar_valor_a_porcentaje(0.0, tiene_porcentaje=False)
        assert result == 0.0

    def test_negative_decimal_to_negative_pct(self):
        """-0.5 (decimal) → -50"""
        result = normalizar_valor_a_porcentaje(-0.5, tiene_porcentaje=False)
        assert result == -50.0

    # ─────────────────────────────────────────────────────────────────────────────────
    # REAL DATA from Resultados_Consolidados
    # ─────────────────────────────────────────────────────────────────────────────────

    def test_real_id_1_feb_2023(self):
        """Real: ID=1, Feb 2023, Cumplimiento=0.121212 → 12.12%"""
        result = normalizar_valor_a_porcentaje(0.121212, tiene_porcentaje=False)
        assert abs(result - 12.1212) < 0.01

    def test_real_id_1_ene_2023(self):
        """Real: ID=1, Jan 2023, Cumplimiento=1.300000 → 130%"""
        result = normalizar_valor_a_porcentaje(1.300000, tiene_porcentaje=False)
        assert result == 130.0

    def test_real_id_1_mayo_2023(self):
        """Real: ID=1, May 2023, Cumplimiento=1.071429 → 107.14%"""
        result = normalizar_valor_a_porcentaje(1.071429, tiene_porcentaje=False)
        assert abs(result - 107.1429) < 0.01

    # ─────────────────────────────────────────────────────────────────────────────────
    # DataFrame.apply() scenarios
    # ─────────────────────────────────────────────────────────────────────────────────

    def test_series_all_decimales(self):
        """Series of decimals"""
        series = pd.Series([0.5, 0.95, 1.2])
        result = series.apply(lambda v: normalizar_valor_a_porcentaje(v, tiene_porcentaje=False))
        expected = pd.Series([50.0, 95.0, 120.0])
        pd.testing.assert_series_equal(result, expected)

    def test_series_all_porcentajes(self):
        """Series of percentages"""
        series = pd.Series([50.0, 100.0, 130.0])
        result = series.apply(lambda v: normalizar_valor_a_porcentaje(v, tiene_porcentaje=True))
        expected = pd.Series([50.0, 100.0, 130.0])
        pd.testing.assert_series_equal(result, expected)

    def test_series_with_nan_values(self):
        """Series with NaN values"""
        series = pd.Series([0.5, np.nan, 1.2])
        result = series.apply(
            lambda v: normalizar_valor_a_porcentaje(v, tiene_porcentaje=False) if pd.notna(v) else v
        )
        expected = pd.Series([50.0, np.nan, 120.0])
        pd.testing.assert_series_equal(result, expected)

    def test_format_as_percentage_strings(self):
        """Format normalized values as percentage strings"""
        series = pd.Series([0.5, 0.95, 1.2])
        normalized = series.apply(
            lambda v: normalizar_valor_a_porcentaje(v, tiene_porcentaje=False)
        )
        formatted = normalized.apply(lambda v: f"{v:.1f}%")
        expected = pd.Series(["50.0%", "95.0%", "120.0%"])
        pd.testing.assert_series_equal(formatted, expected)

    # ─────────────────────────────────────────────────────────────────────────────────
    # Integration: gestion_om.py usage patterns
    # ─────────────────────────────────────────────────────────────────────────────────

    def test_integration_parse_avance_pattern(self):
        """Simulates _parse_avance() pattern"""
        # Values without % symbol (detected as has_percent=False)
        test_cases = [
            (0.5, False, 50.0),
            (0.95, False, 95.0),
            (1.0, False, 100.0),
            (1.2, False, 120.0),
        ]
        for valor, tiene_pct, expected in test_cases:
            result = normalizar_valor_a_porcentaje(valor, tiene_porcentaje=tiene_pct)
            assert result == expected

    def test_integration_cumplimiento_normalization(self):
        """Simulates Cumplimiento normalization from gestion_om.py"""
        df = pd.DataFrame({"Cumplimiento": [0.8, 0.95, 1.0, 1.05, 1.2]})
        # Cumplimiento always comes as decimal (0-1.3)
        df["Cumplimiento_pct"] = (
            df["Cumplimiento"]
            .apply(
                lambda v: (
                    normalizar_valor_a_porcentaje(v, tiene_porcentaje=False) if pd.notna(v) else v
                )
            )
            .round(1)
        )

        expected = pd.Series([80.0, 95.0, 100.0, 105.0, 120.0], name="Cumplimiento_pct")
        pd.testing.assert_series_equal(df["Cumplimiento_pct"], expected)

    # ─────────────────────────────────────────────────────────────────────────────────
    # Verify no hardcoding
    # ─────────────────────────────────────────────────────────────────────────────────

    def test_code_uses_tiene_porcentaje_not_threshold(self):
        """Verify function uses tiene_porcentaje logic, not hardcoded thresholds"""
        import inspect

        source = inspect.getsource(normalizar_valor_a_porcentaje)
        assert "tiene_porcentaje" in source
        assert "if tiene_porcentaje" in source

    def test_gestion_om_refactored(self):
        """Verify gestion_om.py uses new API"""
        gestion_om_path = Path(__file__).parent.parent / "streamlit_app" / "pages" / "gestion_om.py"
        if gestion_om_path.exists():
            with open(gestion_om_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Should import normalizar_valor_a_porcentaje
            assert "normalizar_valor_a_porcentaje" in content
            # Should NOT have old hardcoding patterns with umbral_decimal
            assert "umbral_decimal=1.5" not in content or "tiene_porcentaje" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
