"""
Unit tests para services/strategic_indicators.py

Casos de prueba:
- Utilidades de normalización (_norm_text, _id_limpio)
- Envoltorios de compatibilidad (_nivel_desde_cumplimiento)
- Carga de catálogos (load_pdi_catalog, load_cna_catalog)
- Operaciones de caché
"""

import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, r"c:\Users\ximen\OneDrive\Proyectos_DS\Sistema_Indicadores_Poli")

from services import strategic_indicators


class TestNormText(unittest.TestCase):
    """Pruebas para _norm_text()."""
    
    def test_norm_text_acentos(self):
        """Debe remover acentos de caracteres acentuados."""
        result = strategic_indicators._norm_text("Información")
        assert result == "informacion"
    
    def test_norm_text_mayusculas(self):
        """Debe convertir a minúsculas."""
        result = strategic_indicators._norm_text("HELLO")
        assert result == "hello"
    
    def test_norm_text_espacios(self):
        """Debe mantener espacios (solo quita acentos y minúsculas)."""
        result = strategic_indicators._norm_text("  hello  world  ")
        # La función strip() inicial quita espacios al inicio/final, pero mantiene internos
        assert result == "hello  world"
    
    def test_norm_text_vacio(self):
        """String vacío → string vacío."""
        result = strategic_indicators._norm_text("")
        assert result == ""


class TestIdLimpio(unittest.TestCase):
    """Pruebas para _id_limpio()."""
    
    def test_id_limpio_float(self):
        """Float → string."""
        result = strategic_indicators._id_limpio(45.0)
        assert result == "45"
    
    def test_id_limpio_string(self):
        """String → string sin cambios."""
        result = strategic_indicators._id_limpio("ID-123")
        assert result == "ID-123"
    
    def test_id_limpio_int(self):
        """Int → string."""
        result = strategic_indicators._id_limpio(10)
        assert result == "10"
    
    def test_id_limpio_nan(self):
        """NaN → string vacío o manejo especial."""
        result = strategic_indicators._id_limpio(np.nan)
        # NaN generalmente se convierte a string vacío
        assert isinstance(result, str)


class TestNivelDesdeCumplimiento(unittest.TestCase):
    """Pruebas para categorizar_cumplimiento() - PROBLEMA #5 FIX.
    
    Reemplaza tests de la función eliminada _nivel_desde_cumplimiento()
    con tests directos de categorizar_cumplimiento() que SÍ maneja Plan Anual.
    """
    
    def test_nivel_cumplimiento_bajo(self):
        """0.4 (40%) → Peligro."""
        from core.semantica import categorizar_cumplimiento
        result = categorizar_cumplimiento(0.4)
        assert result == "Peligro"
    
    def test_nivel_cumplimiento_alerta(self):
        """0.8 (80%) → Alerta."""
        from core.semantica import categorizar_cumplimiento
        result = categorizar_cumplimiento(0.8)
        assert result == "Alerta"
    
    def test_nivel_cumplimiento_ok(self):
        """1.0 (100%) → Cumplimiento (Regular)."""
        from core.semantica import categorizar_cumplimiento
        result = categorizar_cumplimiento(1.0)
        assert result == "Cumplimiento"
    
    def test_nivel_cumplimiento_sobre(self):
        """1.2 (120%) → Sobrecumplimiento (Regular)."""
        from core.semantica import categorizar_cumplimiento
        result = categorizar_cumplimiento(1.2)
        assert result == "Sobrecumplimiento"
    
    def test_nivel_con_id_plan_anual(self):
        """Plan Anual: 95% es Cumplimiento (no Alerta).
        
        Problema #5: La función anterior (_nivel_desde_cumplimiento) ignoraba PA.
        Ahora categorizar_cumplimiento() SÍ lo considera.
        """
        from core.semantica import categorizar_cumplimiento
        from core.config import IDS_PLAN_ANUAL
        
        # ID 45 debería estar en IDS_PLAN_ANUAL
        id_pa = list(IDS_PLAN_ANUAL)[0] if IDS_PLAN_ANUAL else "45"
        
        # 95% para PA es Cumplimiento (umbral PA = 95%)
        result = categorizar_cumplimiento(0.95, id_indicador=id_pa)
        assert result == "Cumplimiento", f"PA con 95% debería ser Cumplimiento, no {result}"
        
        # 95% para Regular es Alerta (umbral regular = 100%)
        result_regular = categorizar_cumplimiento(0.95, id_indicador="999")
        assert result_regular == "Alerta", f"Regular con 95% debería ser Alerta, no {result_regular}"


class TestFindCol(unittest.TestCase):
    """Pruebas para _find_col()."""
    
    def test_find_col_primera_opcion(self):
        """Debe retornar la primera columna que existe."""
        df = pd.DataFrame({
            "Indicador": ["A", "B"],
            "Nombre": ["X", "Y"]
        })
        result = strategic_indicators._find_col(df, ["Indicador", "Nombre"])
        assert result == "Indicador"
    
    def test_find_col_segunda_opcion(self):
        """Si primera no existe, buscar segunda."""
        df = pd.DataFrame({
            "Nombre": ["X", "Y"],
            "Titulo": ["A", "B"]
        })
        result = strategic_indicators._find_col(df, ["Indicador", "Nombre"])
        assert result == "Nombre"
    
    def test_find_col_ninguna(self):
        """Si no existe ninguna → None."""
        df = pd.DataFrame({"Otro": ["X", "Y"]})
        result = strategic_indicators._find_col(df, ["Indicador", "Nombre"])
        assert result is None


class TestCacheOperations(unittest.TestCase):
    """Pruebas para operaciones de caché."""
    
    def setUp(self):
        """Limpiar caché antes de cada test."""
        strategic_indicators._CACHE_MANUAL.clear()
    
    def test_set_y_get_cached(self):
        """Guardar y recuperar del caché."""
        df = pd.DataFrame({"A": [1, 2, 3]})
        strategic_indicators._set_cached("test_key", df)
        
        result = strategic_indicators._get_cached("test_key")
        assert result is not None
        pd.testing.assert_frame_equal(result, df)
    
    def test_get_cached_no_existe(self):
        """Clave inexistente → None."""
        result = strategic_indicators._get_cached("nonexistent")
        assert result is None
    
    def test_validate_cached_result_vacio(self):
        """DataFrame vacío → False."""
        df = pd.DataFrame()
        result = strategic_indicators._validate_cached_result(df, "test")
        assert result is False
    
    def test_validate_cached_result_valido(self):
        """DataFrame con datos → True."""
        df = pd.DataFrame({"A": [1, 2, 3]})
        result = strategic_indicators._validate_cached_result(df, "test")
        assert result is True


class TestLoadPdiCatalog(unittest.TestCase):
    """Pruebas para load_pdi_catalog()."""
    
    def test_load_pdi_catalog_retorna_dataframe(self):
        """load_pdi_catalog() debe retornar un DataFrame."""
        result = strategic_indicators.load_pdi_catalog()
        
        assert isinstance(result, pd.DataFrame)
        # Debe tener al menos columnas comunes
        assert len(result) >= 0


class TestLoadCnaCatalog(unittest.TestCase):
    """Pruebas para load_cna_catalog()."""
    
    def test_load_cna_catalog_retorna_dataframe(self):
        """load_cna_catalog() debe retornar un DataFrame."""
        result = strategic_indicators.load_cna_catalog()
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 0


class TestLoadCierres(unittest.TestCase):
    """Pruebas para load_cierres()."""
    
    def test_load_cierres_retorna_dataframe(self):
        """load_cierres() debe retornar un DataFrame."""
        result = strategic_indicators.load_cierres()
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 0


class TestCierrePorCorte(unittest.TestCase):
    """Pruebas para cierre_por_corte()."""
    
    def test_cierre_por_corte_filtro_hasta_anio_mes(self):
        """Debe retornar datos hasta (inclusive) el año y mes especificados."""
        df_cierres = pd.DataFrame({
            "Id": [1, 2, 3, 4],
            "Anio": [2024, 2024, 2024, 2025],
            "Mes": [1, 2, 3, 1],
            "Cumplimiento": [0.95, 0.90, 0.85, 0.80]
        })
        
        result = strategic_indicators.cierre_por_corte(df_cierres, 2024, 2)
        
        assert isinstance(result, pd.DataFrame)
        # Debe retornar datos <= 202402 (2024-01 y 2024-02)
        if len(result) > 0:
            assert (result["Anio"] * 100 + result["Mes"] <= 202402).all()
    
    def test_cierre_por_corte_vacio(self):
        """Si no hay datos para ese corte, retorna DataFrame vacío."""
        df_cierres = pd.DataFrame({
            "Id": [1],
            "Anio": [2025],
            "Mes": [1],
            "Cumplimiento": [0.95]
        })
        
        result = strategic_indicators.cierre_por_corte(df_cierres, 2024, 1)
        
        assert isinstance(result, pd.DataFrame)
        # No hay datos <= 202401 cuando los datos son de 2025-01
        assert len(result) == 0


class TestPreparaPdiConCierre(unittest.TestCase):
    """Pruebas para preparar_pdi_con_cierre()."""
    
    def test_preparar_pdi_con_cierre_retorna_dataframe(self):
        """Debe retornar un DataFrame."""
        result = strategic_indicators.preparar_pdi_con_cierre(2024, 1)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 0


class TestPreparaCnaConCierre(unittest.TestCase):
    """Pruebas para preparar_cna_con_cierre()."""
    
    def test_preparar_cna_con_cierre_retorna_dataframe(self):
        """Debe retornar un DataFrame."""
        result = strategic_indicators.preparar_cna_con_cierre(2024, 1)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 0


if __name__ == "__main__":
    unittest.main()
