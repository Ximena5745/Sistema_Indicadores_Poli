"""
tests/test_ficha_pdf_utils.py
Cobertura de services/ficha_pdf/utils.py — funciones puras de PDF.

Cubre:
  - nivel_color(nivel) → color institucional o GRIS
  - safe(v) → str, convierte None/NaN a "—"
"""
import math

import numpy as np
import pytest

from services.ficha_pdf.utils import GRIS, NIVEL_COLORS, nivel_color, safe


# ─────────────────────────────────────────────────────────────────────────────
# nivel_color
# ─────────────────────────────────────────────────────────────────────────────

class TestNivelColor:
    def test_peligro_retorna_color_rojo(self):
        assert nivel_color("Peligro") == NIVEL_COLORS["Peligro"]

    def test_alerta_retorna_color_amarillo(self):
        assert nivel_color("Alerta") == NIVEL_COLORS["Alerta"]

    def test_cumplimiento_retorna_color_verde(self):
        assert nivel_color("Cumplimiento") == NIVEL_COLORS["Cumplimiento"]

    def test_sobrecumplimiento_retorna_color_azul(self):
        assert nivel_color("Sobrecumplimiento") == NIVEL_COLORS["Sobrecumplimiento"]

    def test_nivel_desconocido_retorna_gris(self):
        assert nivel_color("Desconocido") == GRIS

    def test_nivel_vacio_retorna_gris(self):
        assert nivel_color("") == GRIS

    def test_nivel_none_retorna_gris(self):
        assert nivel_color(None) == GRIS

    def test_nivel_mixedcase_no_encuentra(self):
        # "peligro" (minúscula) no está en el mapa → GRIS
        assert nivel_color("peligro") == GRIS

    def test_todos_los_niveles_conocidos_tienen_color(self):
        for nivel in ("Peligro", "Alerta", "Cumplimiento", "Sobrecumplimiento"):
            assert nivel_color(nivel) == NIVEL_COLORS[nivel]


# ─────────────────────────────────────────────────────────────────────────────
# safe
# ─────────────────────────────────────────────────────────────────────────────

class TestSafe:
    def test_none_retorna_dash(self):
        assert safe(None) == "—"

    def test_float_nan_retorna_dash(self):
        assert safe(float("nan")) == "—"

    def test_numpy_nan_retorna_dash(self):
        assert safe(np.nan) == "—"

    def test_string_nan_retorna_dash(self):
        assert safe("nan") == "—"

    def test_string_none_retorna_dash(self):
        assert safe("None") == "—"

    def test_string_vacio_retorna_dash(self):
        assert safe("") == "—"

    def test_string_con_solo_espacios_retorna_dash(self):
        assert safe("   ") == "—"

    def test_valor_float_retorna_string(self):
        assert safe(85.5) == "85.5"

    def test_valor_entero_retorna_string(self):
        assert safe(100) == "100"

    def test_valor_string_retorna_mismo(self):
        assert safe("Cumplimiento") == "Cumplimiento"

    def test_string_con_espacios_se_stripea(self):
        assert safe("  valor  ") == "valor"

    def test_cero_no_es_vacio(self):
        assert safe(0) == "0"

    def test_valor_negativo(self):
        assert safe(-5.0) == "-5.0"

    def test_string_numerico(self):
        assert safe("95.5%") == "95.5%"
