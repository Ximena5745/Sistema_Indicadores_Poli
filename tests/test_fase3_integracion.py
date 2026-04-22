"""
PASO 5: TESTS DE INTEGRACIÓN FASE 2-3
Validar el flujo end-to-end: data_loader → semantica → dashboards

Objetivo: Verificar que la centralización de lógica de categorización
funciona correctamente en toda la cadena sin regresiones.
"""
import unittest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Agregar proyecto a path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.semantica import (
    normalizar_y_categorizar,
    categorizar_cumplimiento,
    normalizar_valor_a_porcentaje
)
from core.config import IDS_PLAN_ANUAL, UMBRAL_PELIGRO, UMBRAL_ALERTA, UMBRAL_SOBRECUMPLIMIENTO


class TestIntegracionDataLoaderSemantica(unittest.TestCase):
    """Validar que data_loader usa categorizar_cumplimiento correctamente"""
    
    def test_valores_tipicos_data_loader(self):
        """Simular valores típicos que vienen de data_loader"""
        # Valores como los que retorna load_consolidado_cierres()
        df = pd.DataFrame({
            "cumplimiento_pct": [95.0, 80.0, 105.0, 50.0, 100.0],
            "Id": ["1", "9999", "1", "9999", "1"],  # Mix Plan Anual y Regular
        })
        
        # Aplicar categorización (como hace strategic_indicators.py)
        resultados = []
        for _, row in df.iterrows():
            cat = categorizar_cumplimiento(
                row["cumplimiento_pct"] / 100.0,  # Convertir a decimal
                id_indicador=row["Id"]
            )
            resultados.append(cat)
        
        # Validar resultados
        self.assertEqual(resultados[0], "Cumplimiento")      # 95% Plan Anual (>= 95%)
        self.assertEqual(resultados[1], "Alerta")            # 80% Regular (< 100%)
        self.assertEqual(resultados[2], "Sobrecumplimiento") # 105% Plan Anual (>= 105%)
        self.assertEqual(resultados[3], "Peligro")           # 50% Regular (< 80%)
        self.assertEqual(resultados[4], "Cumplimiento")      # 100% Plan Anual (>= 95%)
    
    def test_flujo_completo_con_normalizar_wrapper(self):
        """Test con wrapper centralizado (como hace gestion_om.py)"""
        df = pd.DataFrame({
            "cumplimiento_pct": [95.0, 80.0, 105.0, 100.0],
            "Id": ["1", "9999", "1", "9999"],
        })
        
        resultados = []
        for _, row in df.iterrows():
            cat = normalizar_y_categorizar(
                row["cumplimiento_pct"],
                es_porcentaje=True,
                id_indicador=row["Id"]
            )
            resultados.append(cat)
        
        expected = ["Cumplimiento", "Alerta", "Sobrecumplimiento", "Cumplimiento"]
        self.assertEqual(resultados, expected)


class TestIntegracionPlanAnualDetection(unittest.TestCase):
    """Validar que Plan Anual es detectado automáticamente en toda la cadena"""
    
    def test_plan_anual_auto_detection(self):
        """Verificar que IDs en IDS_PLAN_ANUAL son categorizados con umbrales PA"""
        # IDs que SÍ son Plan Anual
        plan_anual_ids = ["1", "2", "3", "15", "23"]  # Algunos de los verdaderos
        
        for id_pa in plan_anual_ids:
            # 95% debe ser Cumplimiento en Plan Anual
            cat = categorizar_cumplimiento(0.95, id_indicador=id_pa)
            self.assertEqual(cat, "Cumplimiento", f"ID {id_pa} (Plan Anual) con 95% debe ser Cumplimiento")
            
            # Pero 94% debe ser Alerta
            cat = categorizar_cumplimiento(0.94, id_indicador=id_pa)
            self.assertEqual(cat, "Alerta", f"ID {id_pa} (Plan Anual) con 94% debe ser Alerta")
    
    def test_regular_regime_different_umbral(self):
        """Verificar que IDs NO Plan Anual usan umbrales regulares"""
        # IDs que NO son Plan Anual
        regular_ids = ["9999", "10000", "50000"]
        
        for id_reg in regular_ids:
            # 95% debe ser Alerta en régimen regular
            cat = categorizar_cumplimiento(0.95, id_indicador=id_reg)
            self.assertEqual(cat, "Alerta", f"ID {id_reg} (Regular) con 95% debe ser Alerta")
            
            # 100% debe ser Cumplimiento
            cat = categorizar_cumplimiento(1.00, id_indicador=id_reg)
            self.assertEqual(cat, "Cumplimiento", f"ID {id_reg} (Regular) con 100% debe ser Cumplimiento")


class TestIntegracionCasosEspeciales(unittest.TestCase):
    """Validar casos especiales manejados uniformemente"""
    
    def test_caso_meta_cero_ejecucion_cero(self):
        """Meta=0 & Ejecución=0 → Cumplimiento en toda la cadena"""
        # Este caso especial debe ser manejado por recalcular_cumplimiento_faltante()
        # y luego categorizado uniformemente
        
        # Simular: ambos reciben 1.0 como cumplimiento normalizado
        cat = categorizar_cumplimiento(1.0)  # 100%
        self.assertEqual(cat, "Cumplimiento")
    
    def test_valores_nan_manejados_uniformemente(self):
        """NaN/None → "Sin dato" en toda la cadena"""
        df = pd.DataFrame({
            "valor": [np.nan, None, float('nan')],
        })
        
        for val in df["valor"]:
            cat = normalizar_y_categorizar(val, es_porcentaje=True)
            self.assertEqual(cat, "Sin dato")
    
    def test_negativos_retornan_peligro(self):
        """Valores negativos → Peligro"""
        for negativo in [-10, -50, -100]:
            cat = normalizar_y_categorizar(negativo, es_porcentaje=True)
            self.assertEqual(cat, "Peligro")
    
    def test_muy_alto_cumplimiento(self):
        """Valores muy altos (200%+) → Sobrecumplimiento"""
        for alto in [130, 200, 500]:
            cat = normalizar_y_categorizar(alto, es_porcentaje=True)
            self.assertEqual(cat, "Sobrecumplimiento")


class TestIntegracionConsistenciaUmbrales(unittest.TestCase):
    """Validar que los umbrales son consistentes en toda la cadena"""
    
    def test_umbral_peligro_consistente(self):
        """UMBRAL_PELIGRO (0.80) es respetado en todas partes"""
        # Justo debajo del umbral
        cat_bajo = categorizar_cumplimiento(UMBRAL_PELIGRO - 0.01)
        self.assertEqual(cat_bajo, "Peligro")
        
        # Justo encima
        cat_encima = categorizar_cumplimiento(UMBRAL_PELIGRO + 0.01)
        self.assertEqual(cat_encima, "Alerta")
    
    def test_umbral_alerta_consistente(self):
        """UMBRAL_ALERTA (1.00) es respetado en todas partes"""
        # Justo debajo
        cat_bajo = categorizar_cumplimiento(UMBRAL_ALERTA - 0.01)
        self.assertEqual(cat_bajo, "Alerta")
        
        # Justo encima
        cat_encima = categorizar_cumplimiento(UMBRAL_ALERTA + 0.01)
        self.assertEqual(cat_encima, "Cumplimiento")
    
    def test_umbral_sobrecumplimiento_consistente(self):
        """UMBRAL_SOBRECUMPLIMIENTO (1.05) es respetado"""
        # Justo debajo
        cat_bajo = categorizar_cumplimiento(UMBRAL_SOBRECUMPLIMIENTO - 0.01)
        self.assertEqual(cat_bajo, "Cumplimiento")
        
        # Justo encima
        cat_encima = categorizar_cumplimiento(UMBRAL_SOBRECUMPLIMIENTO + 0.01)
        self.assertEqual(cat_encima, "Sobrecumplimiento")


class TestIntegracionStringParsing(unittest.TestCase):
    """Validar que strings con % se parsean correctamente"""
    
    def test_string_con_porcentaje_auto_detectable(self):
        """String "95%" debe ser auto-detectado como 95% porcentaje"""
        cat = normalizar_y_categorizar("95%", es_porcentaje=None)  # Auto-detect
        self.assertIn(cat, ["Alerta", "Cumplimiento"])  # Depende del ID
    
    def test_string_sin_porcentaje(self):
        """String "95" sin % pero es_porcentaje=True"""
        cat = normalizar_y_categorizar("95", es_porcentaje=True)
        self.assertEqual(cat, "Alerta")  # Regular regime: 95% < 100%
    
    def test_string_invalido_retorna_sin_dato(self):
        """String inválido → "Sin dato" """
        cat = normalizar_y_categorizar("invalid", es_porcentaje=True)
        self.assertEqual(cat, "Sin dato")


class TestIntegracionDataFrameOperations(unittest.TestCase):
    """Validar operaciones en DataFrames (como hace strategic_indicators.py)"""
    
    def test_apply_categorizar_en_serie(self):
        """Aplicar categorización a todo un DataFrame"""
        df = pd.DataFrame({
            "cumplimiento_dec": [0.95, 0.80, 1.05, 0.50, 1.00],
            "Id": ["1", "9999", "1", "9999", "1"],
        })
        
        # Simular lo que hace load_cierres()
        df["Nivel"] = df.apply(
            lambda row: categorizar_cumplimiento(
                row["cumplimiento_dec"],
                id_indicador=row["Id"]
            ),
            axis=1
        )
        
        # Validar resultados
        expected = ["Cumplimiento", "Alerta", "Sobrecumplimiento", "Peligro", "Cumplimiento"]
        self.assertEqual(df["Nivel"].tolist(), expected)
    
    def test_convertir_pct_a_decimal_luego_categorizar(self):
        """Patrón: % → decimal → categorizar"""
        df = pd.DataFrame({
            "cumplimiento_pct": [95.0, 80.0, 105.0, 50.0],
            "Id": ["1", "9999", "1", "9999"],
        })
        
        # Paso 1: Convertir a decimal
        df["cumplimiento_dec"] = df["cumplimiento_pct"] / 100.0
        
        # Paso 2: Categorizar (como hace strategic_indicators.py)
        df["Nivel"] = df.apply(
            lambda row: categorizar_cumplimiento(
                row["cumplimiento_dec"],
                id_indicador=row["Id"]
            ),
            axis=1
        )
        
        expected = ["Cumplimiento", "Alerta", "Sobrecumplimiento", "Peligro"]
        self.assertEqual(df["Nivel"].tolist(), expected)


class TestIntegracionSustitucionesYConsistencia(unittest.TestCase):
    """Validar que las sustituciones de PASO 2 funcionan correctamente"""
    
    def test_gestion_om_patrón_anterior(self):
        """Test del patrón ANTES (conversión manual)"""
        cumpl_pct = 95.0
        
        # ANTES: Manual
        cumpl_decimal_manual = cumpl_pct / 100.0
        cat_manual = categorizar_cumplimiento(cumpl_decimal_manual)
        
        # DESPUÉS: Wrapper
        cat_wrapper = normalizar_y_categorizar(cumpl_pct, es_porcentaje=True)
        
        # Deben ser iguales
        self.assertEqual(cat_manual, cat_wrapper)
    
    def test_pdi_acreditacion_patrón(self):
        """Test del patrón en pdi_acreditacion"""
        cumpl = 75.0
        id_ind = "9999"
        
        # ANTES
        cumpl_pct = float(cumpl)
        cumpl_decimal = cumpl_pct / 100.0
        cat_antes = categorizar_cumplimiento(cumpl_decimal, id_indicador=id_ind)
        
        # DESPUÉS
        cat_despues = normalizar_y_categorizar(cumpl_pct, es_porcentaje=True, id_indicador=id_ind)
        
        # Deben ser iguales
        self.assertEqual(cat_antes, cat_despues)
    
    def test_resumen_general_patrón(self):
        """Test del patrón en resumen_general.py"""
        cumpl_pct = 100.0
        id_indicador = "1"
        
        # Patrón antiguo
        cumpl_decimal_old = cumpl_pct / 100.0
        cat_old = categorizar_cumplimiento(cumpl_decimal_old, id_indicador=id_indicador)
        
        # Patrón nuevo
        cat_new = normalizar_y_categorizar(cumpl_pct, es_porcentaje=True, id_indicador=id_indicador)
        
        self.assertEqual(cat_old, cat_new)


class TestEdgeCasesAvanzados(unittest.TestCase):
    """Tests de edge cases que podrían causarRegresiones"""
    
    def test_valor_exacto_umbral_pa_95(self):
        """Valor exacto en umbral de Plan Anual (95%)"""
        cat = categorizar_cumplimiento(0.95, id_indicador="1")  # Plan Anual
        self.assertEqual(cat, "Cumplimiento")  # Debería incluir el umbral
    
    def test_valor_exacto_umbral_regular_100(self):
        """Valor exacto en umbral regular (100%)"""
        cat = categorizar_cumplimiento(1.00, id_indicador="9999")  # Regular
        self.assertEqual(cat, "Cumplimiento")  # Debería incluir el umbral
    
    def test_muy_proximo_umbral_peligro(self):
        """Valor muy próximo al umbral de Peligro"""
        cat_bajo = categorizar_cumplimiento(0.7999)
        cat_exacto = categorizar_cumplimiento(0.80)
        cat_alto = categorizar_cumplimiento(0.8001)
        
        self.assertEqual(cat_bajo, "Peligro")
        self.assertEqual(cat_exacto, "Alerta")  # Debería pasar a Alerta
        self.assertEqual(cat_alto, "Alerta")
    
    def test_decimales_muy_pequenos(self):
        """Valores con muchos decimales se manejan correctamente"""
        cat = normalizar_y_categorizar(99.99999, es_porcentaje=True)
        self.assertEqual(cat, "Alerta")  # Regular: < 100%
    
    def test_valor_cero_es_peligro(self):
        """0% → Peligro"""
        cat = categorizar_cumplimiento(0.0)
        self.assertEqual(cat, "Peligro")


if __name__ == "__main__":
    unittest.main()
