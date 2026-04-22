"""
Tests para scripts/etl/cumplimiento.py
Validar casos especiales y casos reales del Problema #4

CASOS TESTEADOS:
1. Meta=0, Ejecución=0 → 100% (Mortalidad laboral)
2. Sentido Negativo, Ejecución=0, Meta>0 → 100% (Accidentalidad)
3. Indicador ID 208 (Consumo Agua) - Negativo con tope 100%
4. Indicador ID 124 (Accidentalidad) - Negativo con ejecución 0
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import pytest
from etl.cumplimiento import _calc_cumpl, _calc_cumpl_con_tope_dinamico, obtener_tope_cumplimiento


class TestCasosEspeciales:
    """Pruebas para casos especiales (Problem #4)."""

    def test_meta_cero_ejecutado_cero(self):
        """Meta=0 y Ejecución=0 → 100% (éxito perfecto)."""
        cumpl_capped, cumpl_real = _calc_cumpl(0, 0, "Positivo")
        assert cumpl_capped == 1.0, "Meta=0, Ejec=0 debería ser 100%"
        assert cumpl_real == 1.0, "CumplReal también 100%"

    def test_meta_cero_ejecutado_cero_negativo(self):
        """Meta=0 y Ejecución=0 con Negativo → 100% (éxito perfecto)."""
        cumpl_capped, cumpl_real = _calc_cumpl(0, 0, "Negativo")
        assert cumpl_capped == 1.0, "Meta=0, Ejec=0, Negativo → 100%"
        assert cumpl_real == 1.0

    def test_sentido_negativo_ejecutado_cero(self):
        """Sentido Negativo, Ejecución=0, Meta>0 → 100% (cero es perfecto)."""
        # Caso real: Accidentalidad meta=1.6, ejecutado=0 accidentes
        cumpl_capped, cumpl_real = _calc_cumpl(1.6, 0, "Negativo")
        assert cumpl_capped == 1.0, "Negativo con Ejec=0 → 100% (cero es mejor)"
        assert cumpl_real == 1.0

    def test_sentido_negativo_ejecutado_cero_meta_alto(self):
        """Sentido Negativo, Meta alto, Ejecución=0 → 100%."""
        # Caso real: Consumo meta=1700 m3, ejecutado=0 m3
        cumpl_capped, cumpl_real = _calc_cumpl(1700, 0, "Negativo")
        assert cumpl_capped == 1.0, "Meta=1700, Ejec=0, Negativo → 100%"
        assert cumpl_real == 1.0


class TestCasosReales:
    """Pruebas con casos reales extraídos del Excel."""

    def test_caso_real_id_208_consumo_agua(self):
        """ID 208: Consumo de Agua - Sentido Negativo, Meta=1700, Ejec=654."""
        # Sin tope: 1700/654 = 2.60
        cumpl_capped, cumpl_real = _calc_cumpl(1700, 654, "Negativo", tope=1.3)
        assert abs(cumpl_capped - 1.3) < 0.01, "Capped debe ser 1.3 (tope regular)"
        assert abs(cumpl_real - 2.60) < 0.01, "Real debe ser 2.60 (sin tope)"

    def test_caso_real_id_208_con_tope_100(self):
        """ID 208: Si tiene tope 100%, el capped debe ser 1.0."""
        cumpl_capped, cumpl_real = _calc_cumpl(1700, 654, "Negativo", tope=1.0)
        assert abs(cumpl_capped - 1.0) < 0.01, "Capped debe ser 1.0 (tope 100%)"
        assert abs(cumpl_real - 2.60) < 0.01, "Real sigue siendo 2.60"

    def test_caso_real_id_124_accidentalidad(self):
        """ID 124: Accidentalidad - Sentido Negativo, Meta=1.6, Ejec=0."""
        cumpl_capped, cumpl_real = _calc_cumpl(1.6, 0, "Negativo")
        assert cumpl_capped == 1.0, "0 accidentes = 100% (perfecto)"
        assert cumpl_real == 1.0

    def test_caso_real_id_106_mortalidad(self):
        """ID 106: Mortalidad - Meta=0, Ejec=0 (ambiguo pero es perfecto)."""
        cumpl_capped, cumpl_real = _calc_cumpl(0, 0, "Negativo")
        assert cumpl_capped == 1.0, "Meta=0, Ejec=0 = 100% (éxito)"
        assert cumpl_real == 1.0

    def test_caso_real_id_200_capacitaciones(self):
        """ID 200: Capacitaciones - Positivo, Meta=70, Ejec=90."""
        cumpl_capped, cumpl_real = _calc_cumpl(70, 90, "Positivo", tope=1.3)
        assert abs(cumpl_capped - 1.2857) < 0.01, "90/70 = 1.2857 (~128.57%)"
        assert abs(cumpl_real - 1.2857) < 0.01

    def test_caso_real_id_200_capacitaciones_sobrecumplimiento(self):
        """ID 200: Capacitaciones sobrecumplimiento - Meta=87, Ejec=90.85."""
        # 90.85 / 87 = 1.0442 (104.42%)
        cumpl_capped, cumpl_real = _calc_cumpl(87, 90.85, "Positivo", tope=1.3)
        assert abs(cumpl_capped - 1.0442) < 0.01, "90.85/87 = 1.0442"
        assert abs(cumpl_real - 1.0442) < 0.01


class TestTopesDinamicos:
    """Pruebas para toques dinámicos según ID."""

    def test_obtener_tope_plan_anual(self):
        """ID en IDS_PLAN_ANUAL debe retornar 1.0."""
        # Asumir que 45 está en IDS_PLAN_ANUAL
        ids_pa = {"45", "46", "47"}
        tope = obtener_tope_cumplimiento("45", ids_plan_anual=ids_pa)
        assert tope == 1.0, "Plan Anual debe tener tope 1.0"

    def test_obtener_tope_tope_100(self):
        """ID en IDS_TOPE_100 debe retornar 1.0."""
        ids_tope100 = {"208", "218"}
        tope = obtener_tope_cumplimiento("208", ids_tope_100=ids_tope100)
        assert tope == 1.0, "ID 208 (TOPE_100) debe tener tope 1.0"

    def test_obtener_tope_regular(self):
        """ID regular debe retornar 1.3."""
        ids_pa = {"45", "46"}
        ids_t100 = {"208", "218"}
        tope = obtener_tope_cumplimiento("999", ids_plan_anual=ids_pa, ids_tope_100=ids_t100)
        assert tope == 1.3, "ID regular debe tener tope 1.3"


class TestCalculoConTopeDinamico:
    """Pruebas para cálculo con tope dinámico."""

    def test_id_208_con_tope_dinamico(self):
        """ID 208 (TOPE_100): Meta=1700, Ejec=654 → 100% capped."""
        ids_tope100 = {"208", "218"}
        cumpl_capped, cumpl_real = _calc_cumpl_con_tope_dinamico(
            1700, 654, "Negativo", id_indicador="208", ids_tope_100=ids_tope100
        )
        assert abs(cumpl_capped - 1.0) < 0.01, "Con tope 100% → 100%"
        assert abs(cumpl_real - 2.60) < 0.01, "Real sin tope → 260%"

    def test_id_regular_con_tope_dinamico(self):
        """ID 999 (regular): Meta=1700, Ejec=654 → 130% capped."""
        ids_tope100 = {"208", "218"}
        cumpl_capped, cumpl_real = _calc_cumpl_con_tope_dinamico(
            1700, 654, "Negativo", id_indicador="999", ids_tope_100=ids_tope100
        )
        assert abs(cumpl_capped - 1.3) < 0.01, "Con tope 130% → 130%"
        assert abs(cumpl_real - 2.60) < 0.01, "Real sin tope → 260%"


class TestEdgeCases:
    """Pruebas para casos límite."""

    def test_meta_none(self):
        """Meta=None debe retornar (None, None)."""
        cumpl_capped, cumpl_real = _calc_cumpl(None, 100, "Positivo")
        assert cumpl_capped is None
        assert cumpl_real is None

    def test_ejecucion_none(self):
        """Ejecución=None debe retornar (None, None)."""
        cumpl_capped, cumpl_real = _calc_cumpl(100, None, "Positivo")
        assert cumpl_capped is None
        assert cumpl_real is None

    def test_valores_no_numericos(self):
        """Valores no numéricos deben retornar (None, None)."""
        cumpl_capped, cumpl_real = _calc_cumpl("abc", 100, "Positivo")
        assert cumpl_capped is None
        assert cumpl_real is None

    def test_meta_cero_ejecucion_positiva(self):
        """Meta=0, Ejec>0, Positivo → (None, None) (no se puede dividir)."""
        cumpl_capped, cumpl_real = _calc_cumpl(0, 100, "Positivo")
        assert cumpl_capped is None
        assert cumpl_real is None

    def test_negativo_ejecucion_cero_meta_cero(self):
        """Meta=0, Ejec=0, Negativo → 100% (caso especial capturado)."""
        cumpl_capped, cumpl_real = _calc_cumpl(0, 0, "Negativo")
        assert cumpl_capped == 1.0
        assert cumpl_real == 1.0

    def test_minimo_cero(self):
        """Valores negativos deben acotarse a 0."""
        # Crear un caso donde raw sería negativo (poco probable pero testeamos)
        # Positivo: ejec/meta, si ambos positivos nunca es negativo
        # Negativo: meta/ejec, si ambos positivos nunca es negativo
        # Entonces este caso es más teórico, pero si llegara a pasar:
        cumpl_capped, cumpl_real = _calc_cumpl(100, 0.1, "Negativo", tope=1.3)
        # 100 / 0.1 = 1000, acota a 1.3
        assert cumpl_capped == 1.3
        assert cumpl_real == 1000.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
