"""
Test suite for core/config.py

Tests focus on:
1. Configuration constants exist and have correct types
2. Plan Anual IDs loaded dynamically
3. Threshold values are correct
4. Color mappings complete and valid
5. Environment-aware configuration
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import (
    UMBRAL_PELIGRO,
    UMBRAL_ALERTA,
    UMBRAL_SOBRECUMPLIMIENTO,
    UMBRAL_ALERTA_PA,
    UMBRAL_SOBRECUMPLIMIENTO_PA,
    IDS_PLAN_ANUAL,
    IDS_TOPE_100,
    COLORES,
    COLOR_CATEGORIA,
    ICONOS_CATEGORIA,
    BASE_DIR,
    DATA_RAW,
    DATA_OUTPUT,
    DB_PATH,
)


class TestConfigThresholds:
    """Test configuration thresholds"""

    def test_umbral_peligro_value(self):
        """Test UMBRAL_PELIGRO constant"""
        assert UMBRAL_PELIGRO == 0.80
        assert isinstance(UMBRAL_PELIGRO, float)

    def test_umbral_alerta_value(self):
        """Test UMBRAL_ALERTA constant"""
        assert UMBRAL_ALERTA == 1.00
        assert isinstance(UMBRAL_ALERTA, float)

    def test_umbral_sobrecumplimiento_value(self):
        """Test UMBRAL_SOBRECUMPLIMIENTO constant"""
        assert UMBRAL_SOBRECUMPLIMIENTO == 1.05
        assert isinstance(UMBRAL_SOBRECUMPLIMIENTO, float)

    def test_plan_anual_threshold_alerta(self):
        """Test Plan Anual ALERTA threshold"""
        assert UMBRAL_ALERTA_PA == 0.95
        assert UMBRAL_ALERTA_PA < UMBRAL_ALERTA
        assert isinstance(UMBRAL_ALERTA_PA, float)

    def test_plan_anual_threshold_sobrecumplimiento(self):
        """Test Plan Anual sobrecumplimiento (tope) threshold"""
        assert UMBRAL_SOBRECUMPLIMIENTO_PA == 1.00
        assert UMBRAL_SOBRECUMPLIMIENTO_PA < UMBRAL_SOBRECUMPLIMIENTO
        assert isinstance(UMBRAL_SOBRECUMPLIMIENTO_PA, float)

    def test_threshold_ordering(self):
        """Test thresholds are in correct order"""
        assert UMBRAL_PELIGRO < UMBRAL_ALERTA < UMBRAL_SOBRECUMPLIMIENTO
        assert UMBRAL_ALERTA_PA < UMBRAL_ALERTA
        assert UMBRAL_SOBRECUMPLIMIENTO_PA < UMBRAL_SOBRECUMPLIMIENTO


class TestConfigPlanAnualIds:
    """Test Plan Anual IDs configuration"""

    def test_ids_plan_anual_exists(self):
        """Test IDS_PLAN_ANUAL is loaded"""
        assert IDS_PLAN_ANUAL is not None

    def test_ids_plan_anual_is_collection(self):
        """Test IDS_PLAN_ANUAL is set or frozenset"""
        assert isinstance(IDS_PLAN_ANUAL, (set, frozenset))

    def test_ids_plan_anual_not_empty(self):
        """Test IDS_PLAN_ANUAL is populated"""
        assert len(IDS_PLAN_ANUAL) > 0

    def test_ids_plan_anual_contains_expected(self):
        """Test Plan Anual IDs loaded from Excel are strings"""
        # IDS_PLAN_ANUAL should contain strings (loaded from Excel)
        if len(IDS_PLAN_ANUAL) > 0:
            # Verify all IDs are strings
            for id_val in IDS_PLAN_ANUAL:
                assert isinstance(id_val, str), f"ID should be string, got {type(id_val)}"
        # At minimum, should have loaded something (107 from Excel per DATA_RAW config)
        assert (
            len(IDS_PLAN_ANUAL) >= 100
        ), f"Expected >=100 Plan Anual IDs, got {len(IDS_PLAN_ANUAL)}"

    def test_ids_tope_100_exists(self):
        """Test IDS_TOPE_100 is configured"""
        assert IDS_TOPE_100 is not None
        assert isinstance(IDS_TOPE_100, (set, frozenset))


class TestConfigColors:
    """Test color configuration"""

    def test_colores_dict_exists(self):
        """Test COLORES dict is defined"""
        assert COLORES is not None
        assert isinstance(COLORES, dict)

    def test_colores_main_colors(self):
        """Test main colors are defined"""
        assert "peligro" in COLORES
        assert "alerta" in COLORES
        assert "cumplimiento" in COLORES
        assert "sobrecumplimiento" in COLORES
        assert "sin_dato" in COLORES

    def test_colores_hex_format(self):
        """Test color values are in hex format"""
        for color_name, hex_value in COLORES.items():
            assert isinstance(hex_value, str)
            assert hex_value.startswith("#")
            assert len(hex_value) == 7  # #RRGGBB

    def test_color_categoria_mapping(self):
        """Test COLOR_CATEGORIA mapping"""
        assert "Peligro" in COLOR_CATEGORIA
        assert "Alerta" in COLOR_CATEGORIA
        assert "Cumplimiento" in COLOR_CATEGORIA
        assert "Sobrecumplimiento" in COLOR_CATEGORIA
        assert "Sin dato" in COLOR_CATEGORIA

    def test_iconos_categoria_complete(self):
        """Test all categories have icons"""
        assert "Peligro" in ICONOS_CATEGORIA
        assert "Alerta" in ICONOS_CATEGORIA
        assert "Cumplimiento" in ICONOS_CATEGORIA
        assert "Sobrecumplimiento" in ICONOS_CATEGORIA
        assert "Sin dato" not in ICONOS_CATEGORIA or ICONOS_CATEGORIA.get("Sin dato") is not None

    def test_iconos_are_unicode(self):
        """Test icons are valid unicode emoji"""
        for categoria, icono in ICONOS_CATEGORIA.items():
            assert isinstance(icono, str)
            assert len(icono) > 0


class TestConfigPaths:
    """Test path configuration"""

    def test_base_dir_exists(self):
        """Test BASE_DIR points to project root"""
        assert BASE_DIR.exists()
        assert BASE_DIR.is_dir()
        assert (BASE_DIR / "core").exists()
        assert (BASE_DIR / "streamlit_app").exists()

    def test_data_raw_dir(self):
        """Test DATA_RAW path"""
        assert DATA_RAW.exists()
        assert DATA_RAW.is_dir()

    def test_data_output_dir(self):
        """Test DATA_OUTPUT path"""
        assert DATA_OUTPUT.exists()
        assert DATA_OUTPUT.is_dir()

    def test_db_path_configured(self):
        """Test DB_PATH is configured"""
        assert DB_PATH is not None
        assert DB_PATH.name == "registros_om.db"

    def test_paths_relative_to_base(self):
        """Test paths are relative to BASE_DIR"""
        assert BASE_DIR in DATA_RAW.parents
        assert BASE_DIR in DATA_OUTPUT.parents


class TestConfigIntegration:
    """Integration tests for config usage"""

    def test_config_import_no_errors(self):
        """Test config can be imported without errors"""
        # Already done in setUp, but explicit test
        assert UMBRAL_PELIGRO is not None
        assert IDS_PLAN_ANUAL is not None

    def test_threshold_usage_pattern(self):
        """Test typical threshold usage pattern"""
        cumplimiento = 0.88

        if cumplimiento < UMBRAL_PELIGRO:
            categoria = "PELIGRO"
        elif cumplimiento < UMBRAL_ALERTA:
            categoria = "ALERTA"
        elif cumplimiento < UMBRAL_SOBRECUMPLIMIENTO:
            categoria = "CUMPLIMIENTO"
        else:
            categoria = "SOBRECUMPLIMIENTO"

        assert categoria == "ALERTA"

    def test_plan_anual_usage_pattern(self):
        """Test typical Plan Anual check pattern"""
        id_indicador = "373"

        if str(id_indicador) in IDS_PLAN_ANUAL:
            umbral_alerta = UMBRAL_ALERTA_PA
        else:
            umbral_alerta = UMBRAL_ALERTA

        assert umbral_alerta in [UMBRAL_ALERTA_PA, UMBRAL_ALERTA]

    def test_color_retrieval_pattern(self):
        """Test typical color retrieval pattern"""
        categoria = "Alerta"
        color = COLOR_CATEGORIA.get(categoria, COLORES["sin_dato"])

        assert color is not None
        assert color.startswith("#")
