"""
tests/test_problema_2_casos_especiales.py

Tests para PROBLEMA #2: Casos Especiales Divergentes

Valida que:
1. Meta=0 & Ejec=0 → 1.0 (éxito perfecto)
2. Negativo & Ejec=0 → 1.0 (cero es perfecto)
3. Umbrales se aplican correctamente (tope PA vs Regular)
4. Función centralizada en core/semantica.py es usada
"""

import pytest
import pandas as pd
import numpy as np
from core.semantica import recalcular_cumplimiento_faltante


class TestCasosEspeciales:
    """Tests para casos especiales de cumplimiento"""

    # ══════════════════════════════════════════════════════════════════════════════
    # CASO ESPECIAL 1: Meta=0 & Ejecución=0 → 1.0
    # ══════════════════════════════════════════════════════════════════════════════

    def test_meta_0_ejec_0_regular_retorna_100(self):
        """Meta=0 & Ejec=0 (Regular) debe retornar 1.0 (100% éxito perfecto)"""
        resultado = recalcular_cumplimiento_faltante(0, 0, sentido="Positivo")
        assert resultado == 1.0, f"Esperado 1.0, obtenido {resultado}"

    def test_meta_0_ejec_0_negativo_retorna_100(self):
        """Meta=0 & Ejec=0 (Negativo) debe retornar 1.0 (100% éxito perfecto)"""
        resultado = recalcular_cumplimiento_faltante(0, 0, sentido="Negativo")
        assert resultado == 1.0, f"Esperado 1.0, obtenido {resultado}"

    def test_meta_0_ejec_0_plan_anual_retorna_100(self):
        """Meta=0 & Ejec=0 (Plan Anual) debe retornar 1.0 (100% éxito perfecto)"""
        resultado = recalcular_cumplimiento_faltante(0, 0, sentido="Positivo", id_indicador="1")
        assert resultado == 1.0, f"Esperado 1.0, obtenido {resultado}"

    # ══════════════════════════════════════════════════════════════════════════════
    # CASO ESPECIAL 2: Negativo & Ejecución=0 (Meta>0) → 1.0
    # ══════════════════════════════════════════════════════════════════════════════

    def test_negativo_ejec_0_meta_positiva_retorna_100(self):
        """Negativo & Ejec=0 & Meta>0 debe retornar 1.0 (cero es perfecto)"""
        # Ejemplo: Accidentalidad con meta=1.6 accidentes permitidos, ejecutado=0
        resultado = recalcular_cumplimiento_faltante(1.6, 0, sentido="Negativo")
        assert resultado == 1.0, f"Esperado 1.0, obtenido {resultado}"

    def test_negativo_ejec_0_meta_grande_retorna_100(self):
        """Negativo & Ejec=0 & Meta grande debe retornar 1.0"""
        resultado = recalcular_cumplimiento_faltante(100, 0, sentido="Negativo")
        assert resultado == 1.0, f"Esperado 1.0, obtenido {resultado}"

    def test_negativo_ejec_0_plan_anual_retorna_100(self):
        """Negativo & Ejec=0 (Plan Anual) debe retornar 1.0"""
        resultado = recalcular_cumplimiento_faltante(1.6, 0, sentido="Negativo", id_indicador="45")
        assert resultado == 1.0, f"Esperado 1.0, obtenido {resultado}"

    # ══════════════════════════════════════════════════════════════════════════════
    # CÁLCULOS ESTÁNDAR: Positivo
    # ══════════════════════════════════════════════════════════════════════════════

    def test_positivo_50_pct_cumplimiento(self):
        """Positivo: ejec=50, meta=100 → 0.5 (50%)"""
        resultado = recalcular_cumplimiento_faltante(100, 50, sentido="Positivo")
        assert abs(resultado - 0.5) < 0.001, f"Esperado 0.5, obtenido {resultado}"

    def test_positivo_100_pct_cumplimiento(self):
        """Positivo: ejec=100, meta=100 → 1.0 (100%)"""
        resultado = recalcular_cumplimiento_faltante(100, 100, sentido="Positivo")
        assert abs(resultado - 1.0) < 0.001, f"Esperado 1.0, obtenido {resultado}"

    def test_positivo_150_pct_sobrecumplimiento(self):
        """Positivo: ejec=150, meta=100 → 1.5 (150%, pero tope 1.3)"""
        resultado = recalcular_cumplimiento_faltante(100, 150, sentido="Positivo")
        assert resultado == 1.3, f"Esperado 1.3 (tope), obtenido {resultado}"

    def test_positivo_150_pct_plan_anual_tope_100(self):
        """Positivo PA: ejec=150, meta=100 → 1.5 (150%, pero tope PA 1.0)"""
        resultado = recalcular_cumplimiento_faltante(
            100, 150, sentido="Positivo", id_indicador="45"
        )
        assert resultado == 1.0, f"Esperado 1.0 (tope PA), obtenido {resultado}"

    # ══════════════════════════════════════════════════════════════════════════════
    # CÁLCULOS ESTÁNDAR: Negativo
    # ══════════════════════════════════════════════════════════════════════════════

    def test_negativo_50_pct_cumplimiento(self):
        """Negativo: meta=100, ejec=50 → 2.0 (200%, pero tope 1.3)"""
        # "Menos es mejor": si permitimos 100 unidades de gasto y gastamos 50, superamos meta
        resultado = recalcular_cumplimiento_faltante(100, 50, sentido="Negativo")
        assert resultado == 1.3, f"Esperado 1.3 (tope), obtenido {resultado}"

    def test_negativo_100_pct_cumplimiento(self):
        """Negativo: meta=100, ejec=100 → 1.0 (100%)"""
        resultado = recalcular_cumplimiento_faltante(100, 100, sentido="Negativo")
        assert abs(resultado - 1.0) < 0.001, f"Esperado 1.0, obtenido {resultado}"

    def test_negativo_200_pct_incumplimiento(self):
        """Negativo: meta=100, ejec=200 → 0.5 (50%, incumplimiento)"""
        resultado = recalcular_cumplimiento_faltante(100, 200, sentido="Negativo")
        assert abs(resultado - 0.5) < 0.001, f"Esperado 0.5, obtenido {resultado}"

    # ══════════════════════════════════════════════════════════════════════════════
    # VALIDACIONES: Entradas Inválidas
    # ══════════════════════════════════════════════════════════════════════════════

    def test_meta_none_retorna_nan(self):
        """Meta=None debe retornar NaN"""
        resultado = recalcular_cumplimiento_faltante(None, 50)
        assert pd.isna(resultado), f"Esperado NaN, obtenido {resultado}"

    def test_ejec_none_retorna_nan(self):
        """Ejecución=None debe retornar NaN"""
        resultado = recalcular_cumplimiento_faltante(100, None)
        assert pd.isna(resultado), f"Esperado NaN, obtenido {resultado}"

    def test_ambos_none_retorna_nan(self):
        """Meta=None & Ejec=None debe retornar NaN"""
        resultado = recalcular_cumplimiento_faltante(None, None)
        assert pd.isna(resultado), f"Esperado NaN, obtenido {resultado}"

    # ══════════════════════════════════════════════════════════════════════════════
    # VALIDACIONES: Valores Inválidos
    # ══════════════════════════════════════════════════════════════════════════════

    def test_meta_string_invalido_retorna_nan(self):
        """Meta='abc' debe retornar NaN (no convertible)"""
        resultado = recalcular_cumplimiento_faltante("abc", 50)
        assert pd.isna(resultado), f"Esperado NaN, obtenido {resultado}"

    def test_ejec_string_invalido_retorna_nan(self):
        """Ejecución='xyz' debe retornar NaN (no convertible)"""
        resultado = recalcular_cumplimiento_faltante(100, "xyz")
        assert pd.isna(resultado), f"Esperado NaN, obtenido {resultado}"

    def test_meta_nan_retorna_nan(self):
        """Meta=NaN debe retornar NaN"""
        resultado = recalcular_cumplimiento_faltante(np.nan, 50)
        assert pd.isna(resultado), f"Esperado NaN, obtenido {resultado}"

    def test_ejec_nan_retorna_nan(self):
        """Ejecución=NaN debe retornar NaN"""
        resultado = recalcular_cumplimiento_faltante(100, np.nan)
        assert pd.isna(resultado), f"Esperado NaN, obtenido {resultado}"

    # ══════════════════════════════════════════════════════════════════════════════
    # VALIDACIONES: Casos No Válidos (No Especiales)
    # ══════════════════════════════════════════════════════════════════════════════

    def test_positivo_meta_0_ejec_positivo_retorna_nan(self):
        """Positivo & Meta=0 & Ejec>0 debe retornar NaN (división por cero)"""
        resultado = recalcular_cumplimiento_faltante(0, 50, sentido="Positivo")
        assert pd.isna(resultado), f"Esperado NaN, obtenido {resultado}"

    def test_negativo_meta_0_ejec_positivo_retorna_0(self):
        """Negativo & Meta=0 & Ejec>0 retorna 0.0 (cumpl = 0/50 = 0.0, incumplimiento)"""
        # Meta=0 significa "cero es la meta (cero negativo)"
        # Ejec=50 significa "ejecutamos 50 del negativo"
        # Cumplimiento = Meta/Ejec = 0/50 = 0.0 (NO cumplimos)
        resultado = recalcular_cumplimiento_faltante(0, 50, sentido="Negativo")
        assert resultado == 0.0, f"Esperado 0.0, obtenido {resultado}"

    # ══════════════════════════════════════════════════════════════════════════════
    # CONVERSIÓN DE TIPOS
    # ══════════════════════════════════════════════════════════════════════════════

    def test_string_meta_y_ejec_convertidos(self):
        """Meta y Ejecución como strings deben convertirse a float"""
        resultado = recalcular_cumplimiento_faltante("100", "50")
        assert abs(resultado - 0.5) < 0.001, f"Esperado 0.5, obtenido {resultado}"

    def test_string_numerico_con_decimales(self):
        """Strings numéricos con decimales deben convertirse correctamente"""
        resultado = recalcular_cumplimiento_faltante("100.5", "50.25")
        esperado = 50.25 / 100.5
        assert abs(resultado - esperado) < 0.001, f"Esperado {esperado}, obtenido {resultado}"

    # ══════════════════════════════════════════════════════════════════════════════
    # SENTIDO GENÉRICO (lowercase, con espacios, etc)
    # ══════════════════════════════════════════════════════════════════════════════

    def test_sentido_positivo_mayuscula(self):
        """Sentido='POSITIVO' debe funcionar (case-insensitive)"""
        resultado = recalcular_cumplimiento_faltante(100, 50, sentido="POSITIVO")
        assert abs(resultado - 0.5) < 0.001, f"Esperado 0.5, obtenido {resultado}"

    def test_sentido_negativo_con_espacios(self):
        """Sentido=' NEGATIVO ' debe funcionar (strip automático)"""
        resultado = recalcular_cumplimiento_faltante(100, 50, sentido=" NEGATIVO ")
        assert resultado == 1.3, f"Esperado 1.3 (tope), obtenido {resultado}"

    def test_sentido_desconocido_asume_positivo(self):
        """Sentido desconocido debe asumir Positivo"""
        resultado = recalcular_cumplimiento_faltante(100, 50, sentido="Extraño")
        assert abs(resultado - 0.5) < 0.001, f"Esperado 0.5 (asume Positivo), obtenido {resultado}"

    # ══════════════════════════════════════════════════════════════════════════════
    # PLAN ANUAL vs REGULAR (TOPES)
    # ══════════════════════════════════════════════════════════════════════════════

    def test_tope_regular_130_pct(self):
        """Regular: sobrecumplimiento máximo 1.3 (130%)"""
        resultado = recalcular_cumplimiento_faltante(
            100, 200, sentido="Positivo", id_indicador="999"
        )
        assert resultado == 1.3, f"Esperado 1.3 (tope regular), obtenido {resultado}"

    def test_tope_plan_anual_100_pct(self):
        """Plan Anual: sobrecumplimiento máximo 1.0 (100%)"""
        resultado = recalcular_cumplimiento_faltante(100, 200, sentido="Positivo", id_indicador="1")
        assert resultado == 1.0, f"Esperado 1.0 (tope PA), obtenido {resultado}"

    def test_tope_regular_no_afecta_normales(self):
        """Tope no afecta cumplimientos normales (< tope)"""
        resultado = recalcular_cumplimiento_faltante(100, 80, sentido="Positivo")
        assert abs(resultado - 0.8) < 0.001, f"Esperado 0.8, obtenido {resultado}"

    def test_tope_pa_no_afecta_normales(self):
        """Tope PA no afecta cumplimientos normales (< tope)"""
        resultado = recalcular_cumplimiento_faltante(100, 50, sentido="Positivo", id_indicador="1")
        assert abs(resultado - 0.5) < 0.001, f"Esperado 0.5, obtenido {resultado}"

    # ══════════════════════════════════════════════════════════════════════════════
    # MÍNIMO 0 (No negativos)
    # ══════════════════════════════════════════════════════════════════════════════

    def test_resultado_nunca_negativo(self):
        """Cumplimiento nunca puede ser negativo (mínimo 0)"""
        # Negativo: meta=10, ejec=100 → 10/100 = 0.1 (cumple bien)
        # Pero si meta=1, ejec=100 → 1/100 = 0.01 (casi no cumple)
        resultado = recalcular_cumplimiento_faltante(1, 100, sentido="Negativo")
        assert resultado >= 0.0, f"Cumplimiento no puede ser negativo, obtenido {resultado}"


class TestIntegracionProblema2:
    """Tests de integración para PROBLEMA #2"""

    def test_data_loader_migration(self):
        """Simula reemplazo de lógica en data_loader.py"""

        # ANTES (defectuosa):
        #   if meta == 0: return NaN (incorrecto)
        # DESPUÉS (oficial):
        def recalc_cumpl_row(row):
            return recalcular_cumplimiento_faltante(
                row.get("Meta"), row.get("Ejecucion"), row.get("Sentido", "Positivo"), row.get("Id")
            )

        # Test caso especial
        row_especial = {"Meta": 0, "Ejecucion": 0, "Sentido": "Positivo", "Id": "999"}
        assert recalc_cumpl_row(row_especial) == 1.0

    def test_strategic_indicators_migration(self):
        """Simula reemplazo de lógica en strategic_indicators.py"""

        # Simula lambda en apply
        def recalc_cumpl_row(row):
            return recalcular_cumplimiento_faltante(
                row.get("Meta"), row.get("Ejecucion"), row.get("Sentido", "Positivo"), row.get("Id")
            )

        # Test caso especial Negativo
        row_accidentalidad = {
            "Meta": 1.6,
            "Ejecucion": 0,
            "Sentido": "Negativo",
            "Id": "accidentalidad_id",
        }
        assert recalc_cumpl_row(row_accidentalidad) == 1.0

    def test_cumplimiento_py_equivalencia(self):
        """Valida que la función centralizada es equivalente a cumplimiento.py"""
        # La lógica debe ser idéntica a scripts/etl/cumplimiento.py:_calc_cumpl

        # Test 1: Meta=0 & Ejec=0
        assert recalcular_cumplimiento_faltante(0, 0) == 1.0

        # Test 2: Negativo & Ejec=0
        assert recalcular_cumplimiento_faltante(1.6, 0, "Negativo") == 1.0

        # Test 3: Cálculo normal
        assert abs(recalcular_cumplimiento_faltante(100, 50) - 0.5) < 0.001


class TestCobertura:
    """Tests para cobertura de rama (branch coverage)"""

    def test_caso_especial_1_rama_positivo(self):
        """Rama: Meta=0 & Ejec=0 con sentido Positivo"""
        assert recalcular_cumplimiento_faltante(0.0, 0.0, "Positivo") == 1.0

    def test_caso_especial_1_rama_negativo(self):
        """Rama: Meta=0 & Ejec=0 con sentido Negativo"""
        assert recalcular_cumplimiento_faltante(0.0, 0.0, "Negativo") == 1.0

    def test_caso_especial_2_rama(self):
        """Rama: Negativo & Ejec=0 & Meta>0"""
        assert recalcular_cumplimiento_faltante(5.0, 0.0, "Negativo") == 1.0

    def test_calculo_positivo_rama(self):
        """Rama: Cálculo estándar Positivo"""
        resultado = recalcular_cumplimiento_faltante(10.0, 5.0, "Positivo")
        assert abs(resultado - 0.5) < 0.001

    def test_calculo_negativo_rama(self):
        """Rama: Cálculo estándar Negativo"""
        resultado = recalcular_cumplimiento_faltante(10.0, 5.0, "Negativo")
        assert resultado == 1.3  # Tope aplicado (10/5 = 2.0, tope 1.3)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
