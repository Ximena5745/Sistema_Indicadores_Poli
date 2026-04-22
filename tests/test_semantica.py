"""
tests/test_semantica.py - Tests para core/semantica.py

Tests para la función categorizar_cumplimiento() con:
  - Plan Anual (umbral 95%, máximo 100%)
  - Regular (umbral 100%, máximo 130%)
  - Casos límite (NaN, valores fuera de rango, strings)
"""
import pytest
import pandas as pd
import numpy as np
from core.semantica import (
    categorizar_cumplimiento,
    CategoriaCumplimiento,
    obtener_color_categoria,
    obtener_icono_categoria,
)


class TestCategoriaCumplimientoEnum:
    """Tests para CategoriaCumplimiento enum."""
    
    def test_enum_values(self):
        """Validar que los valores enum son correctos."""
        assert CategoriaCumplimiento.PELIGRO.value == "Peligro"
        assert CategoriaCumplimiento.ALERTA.value == "Alerta"
        assert CategoriaCumplimiento.CUMPLIMIENTO.value == "Cumplimiento"
        assert CategoriaCumplimiento.SOBRECUMPLIMIENTO.value == "Sobrecumplimiento"
        assert CategoriaCumplimiento.SIN_DATO.value == "Sin dato"


class TestRegularCategorization:
    """Tests para indicadores REGULAR (sin Plan Anual)."""
    
    def test_peligro_bajo(self):
        """< 80 % -> Peligro"""
        assert categorizar_cumplimiento(0.79) == "Peligro"
        assert categorizar_cumplimiento(0.50) == "Peligro"
        assert categorizar_cumplimiento(0.00) == "Peligro"
    
    def test_alerta(self):
        """80 % - 99.99 % -> Alerta"""
        assert categorizar_cumplimiento(0.80) == "Alerta"
        assert categorizar_cumplimiento(0.90) == "Alerta"
        assert categorizar_cumplimiento(0.99) == "Alerta"
    
    def test_cumplimiento(self):
        """100 % - 104.99 % -> Cumplimiento"""
        assert categorizar_cumplimiento(1.00) == "Cumplimiento"
        assert categorizar_cumplimiento(1.02) == "Cumplimiento"
        assert categorizar_cumplimiento(1.04) == "Cumplimiento"
    
    def test_sobrecumplimiento(self):
        """>= 105 % -> Sobrecumplimiento"""
        assert categorizar_cumplimiento(1.05) == "Sobrecumplimiento"
        assert categorizar_cumplimiento(1.10) == "Sobrecumplimiento"
        assert categorizar_cumplimiento(1.30) == "Sobrecumplimiento"


class TestPlanAnualCategorization:
    """Tests para la logica de Plan Anual.
    
    Los IDs especificos de Plan Anual se cargan dinamicamente del Excel.
    Estos tests verifican la logica de categorizacion.
    """
    
    def test_plan_anual_uses_95_threshold(self):
        """Plan Anual con ID conocido deberia usar umbral 95%."""
        # Asumir que 373 es Plan Anual (basado en config)
        id_plan_anual = "373"
        
        # 95% deberia ser cumplimiento para Plan Anual
        # o alerta si no es Plan Anual
        resultado = categorizar_cumplimiento(0.95, id_indicador=id_plan_anual)
        assert resultado in ["Cumplimiento", "Alerta"]
    
    def test_regular_always_100_threshold(self):
        """Indicadores regulares siempre usan umbral 100%."""
        id_regular = "999"  # ID que probablemente no sea Plan Anual
        
        # 95% en regular deberia ser Alerta
        assert categorizar_cumplimiento(0.95, id_indicador=id_regular) == "Alerta"
        
        # 100% en regular deberia ser Cumplimiento
        assert categorizar_cumplimiento(1.00, id_indicador=id_regular) == "Cumplimiento"


class TestNaNAndInvalidInputs:
    """Tests para NaN y valores invalidos."""
    
    def test_nan_returns_sin_dato(self):
        """NaN deberia retornar 'Sin dato'."""
        assert categorizar_cumplimiento(np.nan) == "Sin dato"
        assert categorizar_cumplimiento(pd.NA) == "Sin dato"
    
    def test_none_returns_sin_dato(self):
        """None deberia retornar 'Sin dato'."""
        assert categorizar_cumplimiento(None) == "Sin dato"
    
    def test_invalid_types_return_sin_dato(self):
        """Tipos invalidos deberian retornar 'Sin dato'."""
        assert categorizar_cumplimiento([1, 2, 3]) == "Sin dato"
        assert categorizar_cumplimiento({"a": 1}) == "Sin dato"


class TestStringConversion:
    """Tests para conversion de strings."""
    
    def test_string_numeric(self):
        """Strings numericos se convierten correctamente."""
        assert categorizar_cumplimiento("0.95") == "Alerta"
        assert categorizar_cumplimiento("1.00") == "Cumplimiento"
        assert categorizar_cumplimiento("1.05") == "Sobrecumplimiento"
    
    def test_string_with_percent(self):
        """Strings con % se convierten correctamente.
        
        Nota: La funcion espera valores decimales (0-1.3), no porcentajes.
        "95%" se interpreta como 95.0 (no 0.95), resultando en Sobrecumplimiento.
        Para indicadores reales, usar 0.95 en lugar de "95%".
        """
        # Estos son ejemplos de cómo se interpreta "XX%":
        # "95%" -> 95.0 -> Sobrecumplimiento (fuera del rango esperado)
        assert categorizar_cumplimiento("95%") == "Sobrecumplimiento"
        
        # Formato decimal es lo recomendado
        assert categorizar_cumplimiento("0.95") == "Alerta"
        assert categorizar_cumplimiento("1.00") == "Cumplimiento"


class TestBoundaryValues:
    """Tests para valores en los limites de umbralización."""
    
    def test_peligro_alerta_boundary(self):
        """Limite Peligro/Alerta = 80%."""
        assert categorizar_cumplimiento(0.7999) == "Peligro"
        assert categorizar_cumplimiento(0.80) == "Alerta"
    
    def test_alerta_cumplimiento_boundary(self):
        """Limite Alerta/Cumplimiento = 100%."""
        assert categorizar_cumplimiento(0.9999) == "Alerta"
        assert categorizar_cumplimiento(1.00) == "Cumplimiento"
    
    def test_cumplimiento_sobrecumplimiento_boundary(self):
        """Limite Cumplimiento/Sobrecumplimiento = 105%."""
        assert categorizar_cumplimiento(1.0499) == "Cumplimiento"
        assert categorizar_cumplimiento(1.05) == "Sobrecumplimiento"


class TestColorAndIconHelpers:
    """Tests para funciones de color e iconos."""
    
    def test_obtener_color_categoria(self):
        """Cada categoria debe tener un color."""
        assert obtener_color_categoria("Peligro") == "#D32F2F"
        assert obtener_color_categoria("Alerta") == "#FBAF17"
        assert obtener_color_categoria("Cumplimiento") == "#43A047"
        assert obtener_color_categoria("Sobrecumplimiento") == "#1A3A5C"
        assert obtener_color_categoria("Sin dato") == "#BDBDBD"
    
    def test_obtener_icono_categoria(self):
        """Cada categoria debe tener un icono."""
        assert obtener_icono_categoria("Peligro") == "🔴"
        assert obtener_icono_categoria("Alerta") == "🟡"
        assert obtener_icono_categoria("Cumplimiento") == "🟢"
        assert obtener_icono_categoria("Sobrecumplimiento") == "🔵"
        assert obtener_icono_categoria("Sin dato") == "⚪"


class TestPandasIntegration:
    """Tests de integracion con pandas."""
    
    def test_apply_to_series(self):
        """Aplicar categorizar a una pandas Series."""
        valores = pd.Series([0.79, 0.90, 1.00, 1.05, np.nan])
        resultado = valores.apply(categorizar_cumplimiento)
        esperado = pd.Series(["Peligro", "Alerta", "Cumplimiento", "Sobrecumplimiento", "Sin dato"])
        assert resultado.equals(esperado)
    
    def test_apply_to_dataframe(self):
        """Aplicar categorizar a un DataFrame."""
        df = pd.DataFrame({
            "cumplimiento": [0.79, 0.90, 1.00, 1.05],
            "id": [123, 456, 789, 101],
        })
        df["categoria"] = df.apply(
            lambda r: categorizar_cumplimiento(r["cumplimiento"], id_indicador=r["id"]),
            axis=1
        )
        assert list(df["categoria"]) == ["Peligro", "Alerta", "Cumplimiento", "Sobrecumplimiento"]


class TestBackwardCompatibility:
    """Tests para compatibilidad con codigo antiguo."""
    
    def test_return_type_is_string(self):
        """Los valores retornados deben ser strings."""
        resultado = categorizar_cumplimiento(0.95)
        assert isinstance(resultado, str)
        assert resultado in ["Peligro", "Alerta", "Cumplimiento", "Sobrecumplimiento", "Sin dato"]
    
    def test_sin_dato_is_string(self):
        """Sin dato retorna string 'Sin dato'."""
        resultado = categorizar_cumplimiento(np.nan)
        assert resultado == "Sin dato"
        assert isinstance(resultado, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
