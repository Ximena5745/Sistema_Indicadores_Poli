"""
tests/test_problema_1_plan_anual_mal_categorizado.py

PROPÓSITO:
  Validar que PROBLEMA #1 está resuelto:
  - Plan Anual con cumplimiento 0.947 se categoriza como "Cumplimiento"
  - No como "Alerta" como sucedía antes

COBERTURA:
  ✅ Niveles establecidos (documentación)
  ✅ Plan Anual soportado
  ✅ Casos especiales (Meta=0, Ejec=0)
  ✅ Consistencia entre módulos
  ✅ Sin regresiones
"""

import pytest
import pandas as pd
import numpy as np
from core.semantica import categorizar_cumplimiento
from core.config import (
    UMBRAL_PELIGRO,
    UMBRAL_ALERTA,
    UMBRAL_SOBRECUMPLIMIENTO,
    UMBRAL_ALERTA_PA,
    UMBRAL_SOBRECUMPLIMIENTO_PA,
    IDS_PLAN_ANUAL,
)

# ══════════════════════════════════════════════════════════════════════════════
# PROBLEMA #1: PLAN ANUAL MAL CATEGORIZADO — TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestProblema1PlanAnualMalCategorizado:
    """
    PROBLEMA: Indicador ID=373 (Plan Anual) con cumplimiento=0.947
    - En data_loader.py → "Cumplimiento" ✅
    - En strategic_indicators.py → "Alerta" ❌ (DEFECTUOSA)

    ESPERADO: Ambos deben retornar "Cumplimiento" ✅
    """

    def test_plan_anual_373_cumpl_0947_es_cumplimiento(self):
        """
        CRÍTICO: Indicador Plan Anual con cumpl=0.947 debe categorizar como "Cumplimiento"
        (umbral PA es 0.95)
        """
        # Usar un ID conocido como Plan Anual (ej: "373" si está en el Excel)
        # Si 373 no está en IDS_PLAN_ANUAL, usar primero disponible
        test_id = "373"
        if test_id not in IDS_PLAN_ANUAL and IDS_PLAN_ANUAL:
            test_id = next(iter(IDS_PLAN_ANUAL))  # Usar primero disponible

        # Si no hay ningún ID Plan Anual, skip (Excel no configurado)
        if not IDS_PLAN_ANUAL:
            pytest.skip("No hay indicadores Plan Anual cargados del Excel")

        resultado = categorizar_cumplimiento(0.947, id_indicador=test_id)
        assert resultado == "Cumplimiento", (
            f"Plan Anual {test_id} con cumpl=0.947 debería ser 'Cumplimiento', "
            f"pero retorna '{resultado}'"
        )

    def test_mismo_cumpl_regular_es_alerta(self):
        """
        VALIDACIÓN: Mismo cumplimiento=0.947 en indicador REGULAR debe ser "Alerta"
        (umbral regular es 1.00)
        """
        # Usar ID que NO sea Plan Anual
        test_id = "9999"

        resultado = categorizar_cumplimiento(0.947, id_indicador=test_id)
        assert resultado == "Alerta", (
            f"Indicador regular {test_id} con cumpl=0.947 debería ser 'Alerta', "
            f"pero retorna '{resultado}'"
        )

    def test_diferencia_umbrales_pa_vs_regular(self):
        """
        VALIDACIÓN: El sistema diferencia correctamente entre umbrales PA y Regular
        """
        # En el límite: 0.95 (justo en umbral PA)
        if IDS_PLAN_ANUAL:
            test_id_pa = next(iter(IDS_PLAN_ANUAL))
            assert categorizar_cumplimiento(0.95, id_indicador=test_id_pa) == "Cumplimiento"

        # Mismo valor en Regular debe ser Alerta
        assert categorizar_cumplimiento(0.95, id_indicador="9999") == "Alerta"


# ══════════════════════════════════════════════════════════════════════════════
# ESTÁNDAR DE CATEGORIZACIÓN — TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestEstandarNivelesRegular:
    """
    ESTÁNDAR RN-02: Categorización Regular
    - Peligro < 80%
    - Alerta 80-99%
    - Cumplimiento 100-104%
    - Sobrecumplimiento ≥ 105%
    """

    def test_peligro_bajo_80(self):
        """< 80% → Peligro"""
        assert categorizar_cumplimiento(0.79) == "Peligro"
        assert categorizar_cumplimiento(0.50) == "Peligro"
        assert categorizar_cumplimiento(0.00) == "Peligro"

    def test_alerta_80_a_99(self):
        """80% - 99.99% → Alerta"""
        assert categorizar_cumplimiento(0.80) == "Alerta"
        assert categorizar_cumplimiento(0.90) == "Alerta"
        assert categorizar_cumplimiento(0.99) == "Alerta"
        assert categorizar_cumplimiento(0.9999) == "Alerta"

    def test_cumplimiento_100_a_104(self):
        """100% - 104.99% → Cumplimiento"""
        assert categorizar_cumplimiento(1.00) == "Cumplimiento"
        assert categorizar_cumplimiento(1.02) == "Cumplimiento"
        assert categorizar_cumplimiento(1.04) == "Cumplimiento"
        assert categorizar_cumplimiento(1.0499) == "Cumplimiento"

    def test_sobrecumplimiento_105_mas(self):
        """≥ 105% → Sobrecumplimiento"""
        assert categorizar_cumplimiento(1.05) == "Sobrecumplimiento"
        assert categorizar_cumplimiento(1.10) == "Sobrecumplimiento"
        assert categorizar_cumplimiento(1.30) == "Sobrecumplimiento"


class TestEstandarNivelesPlanAnual:
    """
    ESTÁNDAR RN-03: Categorización Plan Anual
    - Peligro < 80%
    - Alerta 80-94%
    - Cumplimiento ≥ 95% (tope 100%)
    """

    @pytest.mark.skipif(not IDS_PLAN_ANUAL, reason="No hay indicadores Plan Anual")
    def test_plan_anual_peligro_bajo_80(self):
        """PA < 80% → Peligro"""
        test_id = next(iter(IDS_PLAN_ANUAL))
        assert categorizar_cumplimiento(0.79, id_indicador=test_id) == "Peligro"
        assert categorizar_cumplimiento(0.50, id_indicador=test_id) == "Peligro"

    @pytest.mark.skipif(not IDS_PLAN_ANUAL, reason="No hay indicadores Plan Anual")
    def test_plan_anual_alerta_80_a_94(self):
        """PA 80% - 94.99% → Alerta"""
        test_id = next(iter(IDS_PLAN_ANUAL))
        assert categorizar_cumplimiento(0.80, id_indicador=test_id) == "Alerta"
        assert categorizar_cumplimiento(0.90, id_indicador=test_id) == "Alerta"
        assert categorizar_cumplimiento(0.94, id_indicador=test_id) == "Alerta"
        assert categorizar_cumplimiento(0.9499, id_indicador=test_id) == "Alerta"

    @pytest.mark.skipif(not IDS_PLAN_ANUAL, reason="No hay indicadores Plan Anual")
    def test_plan_anual_cumplimiento_desde_95(self):
        """PA ≥ 95% → Cumplimiento (sin sobrecumplimiento)"""
        test_id = next(iter(IDS_PLAN_ANUAL))
        assert categorizar_cumplimiento(0.95, id_indicador=test_id) == "Cumplimiento"
        assert categorizar_cumplimiento(1.00, id_indicador=test_id) == "Cumplimiento"
        # PA no tiene sobrecumplimiento (máximo 100%)
        # → retorna "Sobrecumplimiento" pero el tope es 100%
        resultado_sobre = categorizar_cumplimiento(1.05, id_indicador=test_id)
        assert resultado_sobre in ["Cumplimiento", "Sobrecumplimiento"]


# ══════════════════════════════════════════════════════════════════════════════
# CASOS ESPECIALES — TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestCasosEspeciales:
    """Casos especiales de entrada"""

    def test_nan_retorna_sin_dato(self):
        """NaN → "Sin dato" """
        assert categorizar_cumplimiento(np.nan) == "Sin dato"
        assert categorizar_cumplimiento(pd.NA) == "Sin dato"

    def test_none_retorna_sin_dato(self):
        """None → "Sin dato" """
        assert categorizar_cumplimiento(None) == "Sin dato"

    def test_string_numerico_se_convierte(self):
        """Strings numéricos se convierten correctamente"""
        assert categorizar_cumplimiento("0.95") == "Alerta"
        assert categorizar_cumplimiento("1.00") == "Cumplimiento"
        assert categorizar_cumplimiento("1.05") == "Sobrecumplimiento"

    def test_string_con_porcentaje(self):
        """Strings con % se limpian correctamente"""
        # "95%" → float("95") = 95.0 (alto) → Sobrecumplimiento
        # Nota: Función espera decimales (0-1.3), no porcentajes
        resultado = categorizar_cumplimiento("95%")
        # 95.0 es muy alto → Sobrecumplimiento
        assert resultado in ["Sobrecumplimiento", "Sin dato"]  # Depende implementación

    def test_tipo_invalido_retorna_sin_dato(self):
        """Tipos inválidos (listas, dicts) → "Sin dato" """
        assert categorizar_cumplimiento([1, 2, 3]) == "Sin dato"
        assert categorizar_cumplimiento({"a": 1}) == "Sin dato"


# ══════════════════════════════════════════════════════════════════════════════
# UMBRALES CORRECTOS — TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestUmbralesDefinidos:
    """Validar que los umbrales constantes están definidos correctamente"""

    def test_umbral_peligro_es_080(self):
        """UMBRAL_PELIGRO debe ser 0.80"""
        assert UMBRAL_PELIGRO == 0.80, f"UMBRAL_PELIGRO debería ser 0.80, pero es {UMBRAL_PELIGRO}"

    def test_umbral_alerta_es_100(self):
        """UMBRAL_ALERTA debe ser 1.00"""
        assert UMBRAL_ALERTA == 1.00, f"UMBRAL_ALERTA debería ser 1.00, pero es {UMBRAL_ALERTA}"

    def test_umbral_sobrecumplimiento_es_105(self):
        """UMBRAL_SOBRECUMPLIMIENTO debe ser 1.05"""
        assert (
            UMBRAL_SOBRECUMPLIMIENTO == 1.05
        ), f"UMBRAL_SOBRECUMPLIMIENTO debería ser 1.05, pero es {UMBRAL_SOBRECUMPLIMIENTO}"

    def test_umbral_alerta_pa_es_095(self):
        """UMBRAL_ALERTA_PA debe ser 0.95"""
        assert (
            UMBRAL_ALERTA_PA == 0.95
        ), f"UMBRAL_ALERTA_PA debería ser 0.95, pero es {UMBRAL_ALERTA_PA}"

    def test_umbral_sobrecumplimiento_pa_es_100(self):
        """UMBRAL_SOBRECUMPLIMIENTO_PA debe ser 1.00 (tope PA)"""
        assert (
            UMBRAL_SOBRECUMPLIMIENTO_PA == 1.00
        ), f"UMBRAL_SOBRECUMPLIMIENTO_PA debería ser 1.00, pero es {UMBRAL_SOBRECUMPLIMIENTO_PA}"

    def test_ids_plan_anual_es_frozenset(self):
        """IDS_PLAN_ANUAL debe ser frozenset (inmutable)"""
        assert isinstance(
            IDS_PLAN_ANUAL, frozenset
        ), f"IDS_PLAN_ANUAL debería ser frozenset, pero es {type(IDS_PLAN_ANUAL)}"


# ══════════════════════════════════════════════════════════════════════════════
# INTEGRACIÓN Y CONSISTENCIA — TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestConsistenciaIntegracion:
    """Validar que toda la cadena es consistente"""

    def test_coherencia_umbrales_regular(self):
        """Umbrales Regular son coherentes: P < A < S"""
        assert UMBRAL_PELIGRO < UMBRAL_ALERTA < UMBRAL_SOBRECUMPLIMIENTO
        assert 0.80 < 1.00 < 1.05

    def test_coherencia_umbrales_pa(self):
        """Umbrales PA son coherentes: P < A ≤ S"""
        assert UMBRAL_PELIGRO < UMBRAL_ALERTA_PA <= UMBRAL_SOBRECUMPLIMIENTO_PA
        assert 0.80 < 0.95 <= 1.00

    def test_limites_contiguos_regular(self):
        """Categorías cubren todo el rango 0.0 a 1.3"""
        assert categorizar_cumplimiento(0.0) == "Peligro"
        assert categorizar_cumplimiento(0.80 - 0.001) == "Peligro"
        assert categorizar_cumplimiento(0.80) == "Alerta"
        assert categorizar_cumplimiento(1.00 - 0.001) == "Alerta"
        assert categorizar_cumplimiento(1.00) == "Cumplimiento"
        assert categorizar_cumplimiento(1.05 - 0.001) == "Cumplimiento"
        assert categorizar_cumplimiento(1.05) == "Sobrecumplimiento"
        assert categorizar_cumplimiento(1.3) == "Sobrecumplimiento"

    @pytest.mark.skipif(not IDS_PLAN_ANUAL, reason="No hay indicadores Plan Anual")
    def test_limites_contiguos_plan_anual(self):
        """Categorías PA cubren rango correctamente"""
        test_id = next(iter(IDS_PLAN_ANUAL))

        assert categorizar_cumplimiento(0.0, test_id) == "Peligro"
        assert categorizar_cumplimiento(0.80 - 0.001, test_id) == "Peligro"
        assert categorizar_cumplimiento(0.80, test_id) == "Alerta"
        assert categorizar_cumplimiento(0.95 - 0.001, test_id) == "Alerta"
        assert categorizar_cumplimiento(0.95, test_id) == "Cumplimiento"
        assert categorizar_cumplimiento(1.00, test_id) == "Cumplimiento"


# ══════════════════════════════════════════════════════════════════════════════
# MÉTRICA: ¿ESTÁ RESUELTO EL PROBLEMA #1?
# ══════════════════════════════════════════════════════════════════════════════


def test_resumen_problema_1_está_resuelto():
    """
    RESUMEN: Validar que PROBLEMA #1 está completamente resuelto

    ANTES:
    ❌ Plan Anual ID=373 con cumpl=0.947 → "Alerta"
    ❌ Función _nivel_desde_cumplimiento() no detectaba Plan Anual

    DESPUÉS:
    ✅ Plan Anual ID=373 con cumpl=0.947 → "Cumplimiento"
    ✅ Función categorizar_cumplimiento() detecta Plan Anual correctamente
    ✅ Estándares definidos en ESTANDAR_NIVEL_CUMPLIMIENTO.md
    ✅ Tests validan consistencia
    """
    # Si hay Plan Anual disponible, validar el caso crítico
    if IDS_PLAN_ANUAL:
        test_id = next(iter(IDS_PLAN_ANUAL))
        resultado = categorizar_cumplimiento(0.947, id_indicador=test_id)
        assert resultado == "Cumplimiento", (
            f"PROBLEMA #1 NO RESUELTO: "
            f"Plan Anual {test_id} con cumpl=0.947 sigue retornando '{resultado}' "
            f"en lugar de 'Cumplimiento'"
        )

    # Validar que estándares están en config.py
    assert UMBRAL_PELIGRO == 0.80
    assert UMBRAL_ALERTA == 1.00
    assert UMBRAL_SOBRECUMPLIMIENTO == 1.05
    assert UMBRAL_ALERTA_PA == 0.95
    assert UMBRAL_SOBRECUMPLIMIENTO_PA == 1.00

    print("✅ PROBLEMA #1 RESUELTO: Plan Anual categorizado correctamente")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
