"""
tests/test_fase2_normalizacion_wrapper.py

Tests para la nueva función wrapper normalizar_y_categorizar().

Problema: 4+ conversiones manuales repetidas en dashboards
Solución: función centralizada que maneja automáticamente formato de entrada

NOTA: IDs Plan Anual válidos: '1', '2', '3', ... '925' (cargados del Excel)
      IDs NO Plan Anual: '900', '999', etc.
"""

import pytest
import pandas as pd
import numpy as np
from core.semantica import normalizar_y_categorizar


class TestNormalizarYCategorizar:
    """Suite de tests para normalizar_y_categorizar()"""
    
    def test_porcentaje_plan_anual_cumplimiento(self):
        """Plan Anual: 95% → Cumplimiento (ID '1' es Plan Anual)"""
        resultado = normalizar_y_categorizar(95, es_porcentaje=True, id_indicador="1")
        assert resultado == "Cumplimiento"
    
    def test_porcentaje_plan_anual_alerta(self):
        """Plan Anual: 90% → Alerta"""
        resultado = normalizar_y_categorizar(90, es_porcentaje=True, id_indicador="1")
        assert resultado == "Alerta"
    
    def test_porcentaje_plan_anual_peligro(self):
        """Plan Anual: 75% → Peligro"""
        resultado = normalizar_y_categorizar(75, es_porcentaje=True, id_indicador="1")
        assert resultado == "Peligro"
    
    def test_porcentaje_regular_cumplimiento(self):
        """Regular: 100% → Cumplimiento (ID '9999' NO es Plan Anual)"""
        resultado = normalizar_y_categorizar(100, es_porcentaje=True, id_indicador="9999")
        assert resultado == "Cumplimiento"
    
    def test_porcentaje_regular_alerta(self):
        """Regular: 95% → Alerta (usa umbral 100%)"""
        resultado = normalizar_y_categorizar(95, es_porcentaje=True, id_indicador="9999")
        assert resultado == "Alerta"
    
    def test_porcentaje_regular_sobrecumplimiento(self):
        """Regular: 105% → Sobrecumplimiento"""
        resultado = normalizar_y_categorizar(105, es_porcentaje=True, id_indicador="9999")
        assert resultado == "Sobrecumplimiento"
    
    def test_decimal_plan_anual_cumplimiento(self):
        """Plan Anual: 0.95 decimal → Cumplimiento"""
        resultado = normalizar_y_categorizar(0.95, es_porcentaje=False, id_indicador="1")
        assert resultado == "Cumplimiento"
    
    def test_decimal_regular_cumplimiento(self):
        """Regular: 1.00 decimal → Cumplimiento"""
        resultado = normalizar_y_categorizar(1.00, es_porcentaje=False, id_indicador="9999")
        assert resultado == "Cumplimiento"
    
    def test_string_con_porcentaje(self):
        """String con %: '95%' → detecta automáticamente"""
        resultado = normalizar_y_categorizar("95%", id_indicador="1")
        assert resultado == "Cumplimiento"
    
    def test_string_sin_porcentaje(self):
        """String sin %: '0.95' → tratado como decimal"""
        resultado = normalizar_y_categorizar("0.95", id_indicador="1")
        assert resultado == "Cumplimiento"
    
    def test_nan_valor(self):
        """NaN → Sin dato"""
        resultado = normalizar_y_categorizar(np.nan)
        assert resultado == "Sin dato"
    
    def test_none_valor(self):
        """None → Sin dato"""
        resultado = normalizar_y_categorizar(None)
        assert resultado == "Sin dato"
    
    def test_string_invalido(self):
        """String inválido → Sin dato"""
        resultado = normalizar_y_categorizar("ABC")
        assert resultado == "Sin dato"
    
    def test_sin_id_indicador_usa_regular(self):
        """Sin id_indicador → usa régimen Regular"""
        resultado = normalizar_y_categorizar(95, es_porcentaje=True)
        assert resultado == "Alerta"  # Régimen regular usa umbral 100%
    
    def test_deteccion_automatica_porcentaje(self):
        """Detección automática: sin es_porcentaje"""
        # Con % detecta como porcentaje
        resultado1 = normalizar_y_categorizar("95%")
        assert resultado1 == "Alerta"  # Regular: 95% → Alerta
        
        # Sin % detecta como decimal
        resultado2 = normalizar_y_categorizar("0.95")
        assert resultado2 == "Alerta"  # Regular: 0.95 = 95% → Alerta
    
    def test_regular_sobrecumplimiento_130(self):
        """Regular: 130% → Sobrecumplimiento"""
        resultado = normalizar_y_categorizar(130, es_porcentaje=True)
        assert resultado == "Sobrecumplimiento"
    
    def test_zero_valor(self):
        """0% → Peligro"""
        resultado = normalizar_y_categorizar(0, es_porcentaje=True)
        assert resultado == "Peligro"
    
    def test_muy_alto_valor(self):
        """200% → Sobrecumplimiento"""
        resultado = normalizar_y_categorizar(200, es_porcentaje=True)
        assert resultado == "Sobrecumplimiento"
    
    def test_negativo_valor(self):
        """Valor negativo → Peligro (< 0.80)"""
        resultado = normalizar_y_categorizar(-5, es_porcentaje=True)
        assert resultado == "Peligro"
    
    def test_float_con_decimales(self):
        """Float con decimales: 95.5% → Alerta/Cumpl según régimen"""
        resultado_pa = normalizar_y_categorizar(95.5, es_porcentaje=True, id_indicador="1")
        assert resultado_pa == "Cumplimiento"  # PA: 95.5% >= 95% → Cumpl
        
        resultado_reg = normalizar_y_categorizar(95.5, es_porcentaje=True)
        assert resultado_reg == "Alerta"  # Regular: 95.5% < 100% → Alerta


class TestNormalizarYCategorizarIntegracion:
    """Tests de integración con DataFrames (caso real de dashboards)"""
    
    def test_aplicar_en_series(self):
        """Aplicar en una Series (patrón típico de dashboards)"""
        df = pd.DataFrame({
            "Cumplimiento_pct": [95, 100, 105, 75],
            "Id": [1, 9999, 9999, 1]  # IDs válidos
        })
        
        df["Categoria"] = df.apply(
            lambda row: normalizar_y_categorizar(
                row["Cumplimiento_pct"],
                es_porcentaje=True,
                id_indicador=str(row["Id"])
            ),
            axis=1
        )
        
        assert df.loc[0, "Categoria"] == "Cumplimiento"  # 95 PA → Cumpl
        assert df.loc[1, "Categoria"] == "Cumplimiento"  # 100 Reg → Cumpl
        assert df.loc[2, "Categoria"] == "Sobrecumplimiento"  # 105 Reg → Sobrecu
        assert df.loc[3, "Categoria"] == "Peligro"  # 75 PA → Peligro


class TestEdgeCases:
    """Edge cases y valores extremos"""
    
    def test_muy_proximo_a_umbral_pa(self):
        """Valor justo en el umbral PA 95%"""
        assert normalizar_y_categorizar(94.99, es_porcentaje=True, id_indicador="1") == "Alerta"
        assert normalizar_y_categorizar(95.00, es_porcentaje=True, id_indicador="1") == "Cumplimiento"
        assert normalizar_y_categorizar(95.01, es_porcentaje=True, id_indicador="1") == "Cumplimiento"
    
    def test_muy_proximo_a_umbral_regular(self):
        """Valor justo en el umbral regular 100%"""
        assert normalizar_y_categorizar(99.99, es_porcentaje=True) == "Alerta"
        assert normalizar_y_categorizar(100.00, es_porcentaje=True) == "Cumplimiento"
        assert normalizar_y_categorizar(100.01, es_porcentaje=True) == "Cumplimiento"
    
    def test_peligro_umbral(self):
        """Valor justo en el umbral de Peligro 80%"""
        assert normalizar_y_categorizar(79.99, es_porcentaje=True) == "Peligro"
        assert normalizar_y_categorizar(80.00, es_porcentaje=True) == "Alerta"
        assert normalizar_y_categorizar(80.01, es_porcentaje=True) == "Alerta"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
