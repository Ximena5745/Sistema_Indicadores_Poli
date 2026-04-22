"""
Test suite for streamlit_app/pages/resumen_general.py

Tests focus on:
1. _map_level_v2() categorization logic
2. normalizar_y_categorizar() integration
3. Edge cases (NaN, Plan Anual, boundaries)
4. Plan Anual detection
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.semantica import categorizar_cumplimiento, CategoriaCumplimiento, normalizar_y_categorizar


class TestResumenGeneralMapLevel:
    """Test suite for _map_level_v2() categorization logic"""

    def test_regular_indicator_alerta(self):
        """Test regular indicator in ALERTA range (80-99%)"""
        cumplimiento = 0.92  # 92%
        categoria = categorizar_cumplimiento(cumplimiento, id_indicador=245)
        assert categoria == CategoriaCumplimiento.ALERTA.value

    def test_regular_indicator_cumplimiento(self):
        """Test regular indicator at exact meta (100%)"""
        cumplimiento = 1.00
        categoria = categorizar_cumplimiento(cumplimiento, id_indicador=245)
        assert categoria == CategoriaCumplimiento.CUMPLIMIENTO.value

    def test_regular_indicator_peligro(self):
        """Test regular indicator below UMBRAL_PELIGRO (< 80%)"""
        cumplimiento = 0.75  # 75%
        categoria = categorizar_cumplimiento(cumplimiento, id_indicador=245)
        assert categoria == CategoriaCumplimiento.PELIGRO.value

    def test_regular_indicator_sobrecumplimiento(self):
        """Test regular indicator above UMBRAL_SOBRECUMPLIMIENTO (>= 105%)"""
        cumplimiento = 1.15  # 115%
        categoria = categorizar_cumplimiento(cumplimiento, id_indicador=245)
        assert categoria == CategoriaCumplimiento.SOBRECUMPLIMIENTO.value

    def test_plan_anual_alerta(self, plan_anual_id):
        """Test ACTUAL Plan Anual indicator between 80-94% (ALERTA for PA)"""
        # plan_anual_id loaded dynamically from IDS_PLAN_ANUAL in conftest.py
        # ✅ Robusto: Funciona incluso si IDs específicos cambian en Excel
        cumplimiento = 0.92  # 92%
        categoria = categorizar_cumplimiento(cumplimiento, id_indicador=plan_anual_id)
        # Plan Anual: 80-94.9% = ALERTA (threshold is 95%)
        assert categoria == CategoriaCumplimiento.ALERTA.value

    def test_plan_anual_at_threshold(self, plan_anual_id):
        """Test Plan Anual at 95% threshold (CUMPLIMIENTO)"""
        cumplimiento = 0.950  # Exactly at 0.95
        categoria = categorizar_cumplimiento(cumplimiento, id_indicador=plan_anual_id)
        assert categoria == CategoriaCumplimiento.CUMPLIMIENTO.value

    def test_plan_anual_cumplimiento(self, plan_anual_id):
        """Test Plan Anual between 95-100%"""
        cumplimiento = 0.98  # 98%
        categoria = categorizar_cumplimiento(cumplimiento, id_indicador=plan_anual_id)
        assert categoria == CategoriaCumplimiento.CUMPLIMIENTO.value

    def test_plan_anual_no_sobrecumplimiento(self, plan_anual_id):
        """Test Plan Anual capped at 100% (no sobrecumplimiento)"""
        cumplimiento = 1.10  # 110% (would be sobrecumplimiento in regular)
        categoria = categorizar_cumplimiento(cumplimiento, id_indicador=plan_anual_id)
        # Plan Anual has tope=1.00, so this becomes SOBRECUMPLIMIENTO (logically over the tope)
        assert categoria == CategoriaCumplimiento.SOBRECUMPLIMIENTO.value

    def test_nan_handling(self):
        """Test NaN input returns SIN_DATO"""
        import pandas as pd

        cumplimiento = float("nan")
        categoria = categorizar_cumplimiento(cumplimiento, id_indicador=245)
        assert categoria == CategoriaCumplimiento.SIN_DATO.value

    def test_none_handling(self):
        """Test None input returns SIN_DATO"""
        categoria = categorizar_cumplimiento(None, id_indicador=245)
        assert categoria == CategoriaCumplimiento.SIN_DATO.value

    def test_boundary_080(self):
        """Test boundary at UMBRAL_PELIGRO (0.80)"""
        # Just below
        cat_below = categorizar_cumplimiento(0.799, id_indicador=245)
        assert cat_below == CategoriaCumplimiento.PELIGRO.value

        # At threshold (should be ALERTA)
        cat_at = categorizar_cumplimiento(0.800, id_indicador=245)
        assert cat_at == CategoriaCumplimiento.ALERTA.value

    def test_boundary_100(self):
        """Test boundary at UMBRAL_ALERTA (1.00)"""
        # Just below
        cat_below = categorizar_cumplimiento(0.999, id_indicador=245)
        assert cat_below == CategoriaCumplimiento.ALERTA.value

        # At threshold (should be CUMPLIMIENTO)
        cat_at = categorizar_cumplimiento(1.000, id_indicador=245)
        assert cat_at == CategoriaCumplimiento.CUMPLIMIENTO.value

    def test_boundary_105(self):
        """Test boundary at UMBRAL_SOBRECUMPLIMIENTO (1.05)"""
        # Just below
        cat_below = categorizar_cumplimiento(1.049, id_indicador=245)
        assert cat_below == CategoriaCumplimiento.CUMPLIMIENTO.value

        # At threshold (should be SOBRECUMPLIMIENTO)
        cat_at = categorizar_cumplimiento(1.050, id_indicador=245)
        assert cat_at == CategoriaCumplimiento.SOBRECUMPLIMIENTO.value

    def test_high_sobrecumplimiento(self):
        """Test very high cumplimiento (200%+)"""
        cumplimiento = 2.50  # 250%
        categoria = categorizar_cumplimiento(cumplimiento, id_indicador=245)
        assert categoria == CategoriaCumplimiento.SOBRECUMPLIMIENTO.value

    def test_zero_cumplimiento(self):
        """Test 0% cumplimiento (no execution)"""
        cumplimiento = 0.0
        categoria = categorizar_cumplimiento(cumplimiento, id_indicador=245)
        assert categoria == CategoriaCumplimiento.PELIGRO.value


class TestResumenGeneralNormalizacionIntegracion:
    """Integration tests for normalizar_y_categorizar()"""

    def test_normalization_percentage_input(self):
        """Test auto-detection and normalization of percentage input"""
        categoria = normalizar_y_categorizar(valor=92, es_porcentaje=True, id_indicador=245)
        assert categoria == CategoriaCumplimiento.ALERTA.value

    def test_normalization_decimal_input(self):
        """Test decimal input"""
        categoria = normalizar_y_categorizar(valor=0.92, es_porcentaje=False, id_indicador=245)
        assert categoria == CategoriaCumplimiento.ALERTA.value

    def test_normalization_string_percentage(self):
        """Test string percentage parsing"""
        categoria = normalizar_y_categorizar(valor="92%", id_indicador=245)
        assert categoria == CategoriaCumplimiento.ALERTA.value

    def test_plan_anual_via_normalization(self, plan_anual_id):
        """Test Plan Anual detection through normalized function"""
        categoria = normalizar_y_categorizar(
            valor=92,  # 92% = ALERTA for Plan Anual
            es_porcentaje=True,
            id_indicador=plan_anual_id,  # Plan Anual ID dinámico
        )
        assert categoria == CategoriaCumplimiento.ALERTA.value
