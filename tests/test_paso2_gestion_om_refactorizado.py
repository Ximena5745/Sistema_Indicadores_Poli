"""
PASO 2: Validación de refactorización en gestion_om.py
Tests para confirmar que las conversiones manuales fueron reemplazadas correctamente.

ICONOS CORRECTOS:
- Cumplimiento: 🟢
- Alerta: 🟡
- Peligro: 🔴
- Sobrecumplimiento: 🔵
- Sin dato: ⚪
"""
import unittest
import pandas as pd
import sys
from pathlib import Path

# Agregar proyecto a path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.semantica import normalizar_y_categorizar


class TestGestionOMRefactorizado(unittest.TestCase):
    """Validar que gestion_om.py usa normalizar_y_categorizar correctamente"""
    
    def test_barra_avance_om_cumplimiento(self):
        """barra_avance_om: 100% Plan Anual → debe generar HTML con ícono correcto"""
        from streamlit_app.pages.gestion_om import barra_avance_om
        
        resultado = barra_avance_om(100)
        
        # Debe contener ícono de Cumplimiento (🟢)
        self.assertIn("🟢", resultado)
        self.assertIn("100.0%", resultado)
    
    def test_barra_avance_om_peligro(self):
        """barra_avance_om: 79% → Peligro"""
        from streamlit_app.pages.gestion_om import barra_avance_om
        
        resultado = barra_avance_om(79)
        
        # Debe contener ícono de Peligro (🔴)
        self.assertIn("🔴", resultado)
        self.assertIn("79.0%", resultado)
    
    def test_barra_avance_om_nan(self):
        """barra_avance_om: NaN → debe mostrar ⚪"""
        from streamlit_app.pages.gestion_om import barra_avance_om
        
        resultado = barra_avance_om(float('nan'))
        
        self.assertIn("⚪", resultado)
    
    def test_barra_avance_om_zero(self):
        """barra_avance_om: 0 → caso especial devuelve HTML con ⚪"""
        from streamlit_app.pages.gestion_om import barra_avance_om
        
        resultado = barra_avance_om(0)
        
        self.assertIn("⚪", resultado)
    
    def test_barra_cumplimiento_cumplimiento(self):
        """barra_cumplimiento: 100% → Cumplimiento"""
        from streamlit_app.pages.gestion_om import barra_cumplimiento
        
        resultado = barra_cumplimiento(100)
        
        self.assertIn("🟢", resultado)
        self.assertIn("100.0%", resultado)
    
    def test_barra_cumplimiento_alerta(self):
        """barra_cumplimiento: 95% → Alerta"""
        from streamlit_app.pages.gestion_om import barra_cumplimiento
        
        resultado = barra_cumplimiento(95)
        
        self.assertIn("🟡", resultado)
        self.assertIn("95.0%", resultado)
    
    def test_icono_cumplimiento_cumplimiento(self):
        """_icono_cumplimiento: 100% → 🟢"""
        from streamlit_app.pages.gestion_om import _icono_cumplimiento
        
        resultado = _icono_cumplimiento(100)
        
        self.assertEqual(resultado, "🟢")
    
    def test_icono_cumplimiento_peligro(self):
        """_icono_cumplimiento: 50% → 🔴"""
        from streamlit_app.pages.gestion_om import _icono_cumplimiento
        
        resultado = _icono_cumplimiento(50)
        
        self.assertEqual(resultado, "🔴")
    
    def test_icono_cumplimiento_nan(self):
        """_icono_cumplimiento: NaN → ⚪"""
        from streamlit_app.pages.gestion_om import _icono_cumplimiento
        
        resultado = _icono_cumplimiento(float('nan'))
        
        self.assertEqual(resultado, "⚪")
    
    def test_icono_cumplimiento_string_valido(self):
        """_icono_cumplimiento: String "100" → 🟢"""
        from streamlit_app.pages.gestion_om import _icono_cumplimiento
        
        resultado = _icono_cumplimiento("100")
        
        self.assertEqual(resultado, "🟢")


class TestGestionOMIntegracion(unittest.TestCase):
    """Tests de integración: Verificar que uso de normalizar_y_categorizar es correcto"""
    
    def test_consistencia_entre_funciones(self):
        """Verificar que barra_avance_om y _icono_cumplimiento usan misma lógica"""
        from streamlit_app.pages.gestion_om import barra_avance_om, _icono_cumplimiento
        
        # Para 95% (Alerta en régimen regular)
        html_result = barra_avance_om(95)
        icon_result = _icono_cumplimiento(95)
        
        # Ambos deben usar el mismo ícono
        self.assertIn(icon_result, html_result)  # El ícono debe estar en el HTML
    
    def test_valores_limites_pa(self):
        """Test: _icono_cumplimiento usa régimen REGULAR (sin id_indicador)"""
        from streamlit_app.pages.gestion_om import _icono_cumplimiento
        
        # 94% en régimen regular = Alerta (umbral 100%, no Plan Anual)
        self.assertEqual(_icono_cumplimiento(94), "🟡")
        
        # 95% en régimen regular = Alerta (umbral 100%, no Plan Anual)
        self.assertEqual(_icono_cumplimiento(95), "🟡")
    
    def test_valores_limites_regular(self):
        """Test con valores límite para régimen regular"""
        from streamlit_app.pages.gestion_om import _icono_cumplimiento
        
        # 99% en régimen regular = Alerta (umbral 100%)
        self.assertEqual(_icono_cumplimiento(99), "🟡")
        
        # 100% en régimen regular = Cumplimiento
        self.assertEqual(_icono_cumplimiento(100), "🟢")
        
        # 105% en régimen regular = Sobrecumplimiento (umbral 1.05 = 105%)
        self.assertEqual(_icono_cumplimiento(105), "🔵")


class TestEdgeCases(unittest.TestCase):
    """Tests de casos borde"""
    
    def test_valores_negativos(self):
        """Valores negativos → Peligro"""
        from streamlit_app.pages.gestion_om import _icono_cumplimiento
        
        resultado = _icono_cumplimiento(-10)
        
        self.assertEqual(resultado, "🔴")
    
    def test_valores_muy_altos(self):
        """Valores muy altos (200%) → Sobrecumplimiento"""
        from streamlit_app.pages.gestion_om import _icono_cumplimiento
        
        resultado = _icono_cumplimiento(200)
        
        # Debe categorizar como Sobrecumplimiento
        self.assertEqual(resultado, "🔵")
    
    def test_float_con_decimales(self):
        """Valores float con decimales se manejan correctamente"""
        from streamlit_app.pages.gestion_om import _icono_cumplimiento
        
        resultado = _icono_cumplimiento(99.99)
        
        # 99.99% en régimen regular = Alerta
        self.assertEqual(resultado, "🟡")


if __name__ == "__main__":
    unittest.main()
