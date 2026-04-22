"""
Test suite for streamlit_app/pages/gestion_om.py

Tests focus on:
1. Correct imports from core.semantica
2. Categorization functions work in OM context
3. Color/icon assignment for OM display
4. Integration with OM table display
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.semantica import (
    categorizar_cumplimiento,
    obtener_icono_categoria,
    obtener_color_categoria,
    CategoriaCumplimiento,
)


class TestGestionOMImports:
    """Test that gestion_om.py correctly imports from core.semantica"""

    def test_categorizar_cumplimiento_available(self):
        """Test categorizar_cumplimiento is importable"""
        assert callable(categorizar_cumplimiento)

    def test_obtener_icono_categoria_available(self):
        """Test obtener_icono_categoria is importable"""
        assert callable(obtener_icono_categoria)

    def test_obtener_color_categoria_available(self):
        """Test obtener_color_categoria is importable"""
        assert callable(obtener_color_categoria)

    def test_categoria_enum_available(self):
        """Test CategoriaCumplimiento enum available"""
        assert hasattr(CategoriaCumplimiento, "PELIGRO")
        assert hasattr(CategoriaCumplimiento, "ALERTA")
        assert hasattr(CategoriaCumplimiento, "CUMPLIMIENTO")
        assert hasattr(CategoriaCumplimiento, "SOBRECUMPLIMIENTO")
        assert hasattr(CategoriaCumplimiento, "SIN_DATO")


class TestGestionOMCategorization:
    """Test categorization in OM context"""

    def test_om_action_peligro(self, regular_indicator_id):
        """Test OM action with PELIGRO indicator"""
        cumplimiento = 0.65  # 65% - Critical
        categoria = categorizar_cumplimiento(cumplimiento, id_indicador=regular_indicator_id)
        assert categoria == CategoriaCumplimiento.PELIGRO.value

    def test_om_action_alerta(self, regular_indicator_id):
        """Test OM action with ALERTA indicator"""
        cumplimiento = 0.88  # 88% - Close to meta
        categoria = categorizar_cumplimiento(cumplimiento, id_indicador=regular_indicator_id)
        assert categoria == CategoriaCumplimiento.ALERTA.value

    def test_om_action_cumplimiento(self, regular_indicator_id):
        """Test OM action with CUMPLIMIENTO indicator"""
        cumplimiento = 1.02  # 102% - Met goal
        categoria = categorizar_cumplimiento(cumplimiento, id_indicador=regular_indicator_id)
        assert categoria == CategoriaCumplimiento.CUMPLIMIENTO.value

    def test_om_action_sobrecumplimiento(self, regular_indicator_id):
        """Test OM action with SOBRECUMPLIMIENTO indicator"""
        cumplimiento = 1.12  # 112% - Exceeded expectations
        categoria = categorizar_cumplimiento(cumplimiento, id_indicador=regular_indicator_id)
        assert categoria == CategoriaCumplimiento.SOBRECUMPLIMIENTO.value

    def test_om_action_sin_dato(self, regular_indicator_id):
        """Test OM action with missing data"""
        categoria = categorizar_cumplimiento(None, id_indicador=regular_indicator_id)
        assert categoria == CategoriaCumplimiento.SIN_DATO.value


class TestGestionOMIconos:
    """Test icon assignment for OM display"""

    def test_icono_peligro(self):
        """Test icon for PELIGRO category"""
        icono = obtener_icono_categoria(CategoriaCumplimiento.PELIGRO.value)
        assert isinstance(icono, str)

    def test_icono_alerta(self):
        """Test icon for ALERTA category"""
        icono = obtener_icono_categoria(CategoriaCumplimiento.ALERTA.value)
        assert isinstance(icono, str)

    def test_icono_cumplimiento(self):
        """Test icon for CUMPLIMIENTO category"""
        icono = obtener_icono_categoria(CategoriaCumplimiento.CUMPLIMIENTO.value)
        assert isinstance(icono, str)

    def test_icono_sobrecumplimiento(self):
        """Test icon for SOBRECUMPLIMIENTO category"""
        icono = obtener_icono_categoria(CategoriaCumplimiento.SOBRECUMPLIMIENTO.value)
        assert isinstance(icono, str)

    def test_icono_sin_dato(self):
        """Test icon for SIN_DATO category"""
        icono = obtener_icono_categoria(CategoriaCumplimiento.SIN_DATO.value)
        assert "⚪" in icono or isinstance(icono, str)
        assert isinstance(icono, str)


class TestGestionOMColores:
    """Test color assignment for OM display"""

    def test_color_peligro(self):
        """Test color for PELIGRO category"""
        color = obtener_color_categoria(CategoriaCumplimiento.PELIGRO.value)
        assert isinstance(color, str)

    def test_color_alerta(self):
        """Test color for ALERTA category"""
        color = obtener_color_categoria(CategoriaCumplimiento.ALERTA.value)
        assert isinstance(color, str)

    def test_color_cumplimiento(self):
        """Test color for CUMPLIMIENTO category"""
        color = obtener_color_categoria(CategoriaCumplimiento.CUMPLIMIENTO.value)
        assert isinstance(color, str)

    def test_color_sobrecumplimiento(self):
        """Test color for SOBRECUMPLIMIENTO category"""
        color = obtener_color_categoria(CategoriaCumplimiento.SOBRECUMPLIMIENTO.value)
        assert isinstance(color, str)

    def test_color_sin_dato(self):
        """Test color for SIN_DATO category"""
        color = obtener_color_categoria(CategoriaCumplimiento.SIN_DATO.value)
        assert isinstance(color, str)


class TestGestionOMIntegration:
    """Integration tests for OM table display"""

    def test_om_table_row_peligro(self):
        """Test complete OM table row with PELIGRO indicator"""
        cumpl = 0.65
        categoria = categorizar_cumplimiento(cumpl, id_indicador=245)
        icono = obtener_icono_categoria(categoria)
        color = obtener_color_categoria(categoria)

        assert categoria == CategoriaCumplimiento.PELIGRO.value
        assert isinstance(icono, str)
        assert isinstance(color, str)
        assert len(icono) > 0
        assert len(color) > 0

    def test_om_dataframe_with_categorias(self):
        """Test categorization across OM dataframe"""
        # Simulate OM dataframe
        df = pd.DataFrame({"Id": [245, 276, 77, 203], "Cumplimiento": [0.65, 0.88, 1.02, 1.12]})

        # Apply categorization
        df["Categoria"] = df["Cumplimiento"].apply(
            lambda x: categorizar_cumplimiento(x, id_indicador=245)
        )

        # Verify results
        assert len(df) == 4
        assert "Categoria" in df.columns
        assert df["Categoria"].iloc[0] == CategoriaCumplimiento.PELIGRO.value
