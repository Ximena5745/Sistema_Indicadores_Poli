"""
Tests para Problema #7: Hardcoding de umbrales en _map_level

SOLUCIÓN:
  ✅ Eliminado hardcoding de 105/100/80 de resumen_general_real.py
  ✅ Eliminado hardcoding de 105 de pdi_acreditacion.py
  ✅ Ambas usan ahora categorizar_cumplimiento() de core/semantica.py
  ✅ Plan Anual considerado correctamente

VALIDACIÓN:
  - Funciones retornan niveles válidos
  - Plan Anual con 95% = "Cumplimiento" (no "Alerta")
  - Regular con 95% = "Alerta" (no "Cumplimiento")
  - Consistencia con core/semantica.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import pandas as pd
import numpy as np
from streamlit_app.pages.resumen_general_real import _ensure_nivel_cumplimiento
from streamlit_app.pages.pdi_acreditacion import _clasificar_estado
from core.semantica import categorizar_cumplimiento
from core.config import IDS_PLAN_ANUAL


class TestProblema7ResumenGeneralReal:
    """Tests para _ensure_nivel_cumplimiento en resumen_general_real.py"""

    def test_ensure_nivel_con_cumplimiento_pct_vacio(self):
        """DataFrame vacío debe retornarse sin errores."""
        df = pd.DataFrame({"cumplimiento_pct": []})
        result = _ensure_nivel_cumplimiento(df)
        assert isinstance(result, pd.DataFrame)

    def test_ensure_nivel_con_cumplimiento_pct_100(self):
        """cumplimiento_pct=100 debe ser 'Cumplimiento'."""
        df = pd.DataFrame({"cumplimiento_pct": [100.0], "Id": ["100"]})
        result = _ensure_nivel_cumplimiento(df)
        assert "Nivel de cumplimiento" in result.columns
        assert result["Nivel de cumplimiento"].iloc[0] == "Cumplimiento"

    def test_ensure_nivel_con_cumplimiento_pct_105(self):
        """cumplimiento_pct=105 debe ser 'Sobrecumplimiento'."""
        df = pd.DataFrame({"cumplimiento_pct": [105.0], "Id": ["100"]})
        result = _ensure_nivel_cumplimiento(df)
        assert result["Nivel de cumplimiento"].iloc[0] == "Sobrecumplimiento"

    def test_ensure_nivel_con_cumplimiento_pct_80(self):
        """cumplimiento_pct=80 debe ser 'Alerta'."""
        df = pd.DataFrame({"cumplimiento_pct": [80.0], "Id": ["100"]})
        result = _ensure_nivel_cumplimiento(df)
        assert result["Nivel de cumplimiento"].iloc[0] == "Alerta"

    def test_ensure_nivel_con_cumplimiento_pct_60(self):
        """cumplimiento_pct=60 debe ser 'Peligro'."""
        df = pd.DataFrame({"cumplimiento_pct": [60.0], "Id": ["100"]})
        result = _ensure_nivel_cumplimiento(df)
        assert result["Nivel de cumplimiento"].iloc[0] == "Peligro"

    def test_ensure_nivel_plan_anual_95_es_cumplimiento(self):
        """Plan Anual con 95% debe ser 'Cumplimiento' (no 'Alerta')."""
        # ID 1 es Plan Anual
        if "1" in IDS_PLAN_ANUAL:
            df = pd.DataFrame({"cumplimiento_pct": [95.0], "Id": ["1"]})
            result = _ensure_nivel_cumplimiento(df)
            assert (
                result["Nivel de cumplimiento"].iloc[0] == "Cumplimiento"
            ), "Plan Anual con 95% debe ser Cumplimiento"

    def test_ensure_nivel_regular_95_es_alerta(self):
        """Regular con 95% debe ser 'Alerta' (no 'Cumplimiento')."""
        df = pd.DataFrame({"cumplimiento_pct": [95.0], "Id": ["100"]})  # ID regular, no Plan Anual
        result = _ensure_nivel_cumplimiento(df)
        assert (
            result["Nivel de cumplimiento"].iloc[0] == "Alerta"
        ), "Regular con 95% debe ser Alerta"

    def test_ensure_nivel_con_nan(self):
        """NaN debe retornar 'Pendiente de reporte'."""
        df = pd.DataFrame({"cumplimiento_pct": [np.nan], "Id": ["100"]})
        result = _ensure_nivel_cumplimiento(df)
        assert result["Nivel de cumplimiento"].iloc[0] == "Pendiente de reporte"

    def test_ensure_nivel_con_categoria_existente(self):
        """Si existe 'Categoria', usarla."""
        df = pd.DataFrame({"Categoria": ["Cumplimiento"], "cumplimiento_pct": [100.0]})
        result = _ensure_nivel_cumplimiento(df)
        assert result["Nivel de cumplimiento"].iloc[0] == "Cumplimiento"

    def test_ensure_nivel_con_nivel_existente(self):
        """Si existe 'Nivel de cumplimiento', no modificarlo."""
        df = pd.DataFrame({"Nivel de cumplimiento": ["Test"], "cumplimiento_pct": [100.0]})
        result = _ensure_nivel_cumplimiento(df)
        assert result["Nivel de cumplimiento"].iloc[0] == "Test"


class TestProblema7PDIAcreditacion:
    """Tests para _clasificar_estado en pdi_acreditacion.py"""

    def test_clasificar_estado_100(self):
        """Estado de 100% debe ser 'Cumplimiento'."""
        result = _clasificar_estado(100.0)
        assert result == "Cumplimiento"

    def test_clasificar_estado_105(self):
        """Estado de 105% debe ser 'Sobrecumplimiento'."""
        result = _clasificar_estado(105.0)
        assert result == "Sobrecumplimiento"

    def test_clasificar_estado_80(self):
        """Estado de 80% debe ser 'Alerta'."""
        result = _clasificar_estado(80.0)
        assert result == "Alerta"

    def test_clasificar_estado_60(self):
        """Estado de 60% debe ser 'Peligro'."""
        result = _clasificar_estado(60.0)
        assert result == "Peligro"

    def test_clasificar_estado_nan(self):
        """NaN debe retornar 'Sin dato'."""
        result = _clasificar_estado(np.nan)
        assert result == "Sin dato"

    def test_clasificar_estado_plan_anual_95(self):
        """Plan Anual con 95% debe ser 'Cumplimiento'."""
        # ID 1 es Plan Anual
        if "1" in IDS_PLAN_ANUAL:
            result = _clasificar_estado(95.0, id_indicador="1")
            assert result == "Cumplimiento", "Plan Anual con 95% debe ser Cumplimiento"

    def test_clasificar_estado_regular_95(self):
        """Regular con 95% debe ser 'Alerta'."""
        result = _clasificar_estado(95.0, id_indicador="100")
        assert result == "Alerta", "Regular con 95% debe ser Alerta"


class TestProblema7Consistencia:
    """Validar consistencia entre funciones."""

    def test_resumen_general_real_vs_pdi_acreditacion(self):
        """Ambas funciones deben dar el mismo resultado para valores sin ID."""
        test_values = [60.0, 80.0, 100.0, 105.0]

        for val in test_values:
            df = pd.DataFrame({"cumplimiento_pct": [val], "Id": ["100"]})
            result_resumen = _ensure_nivel_cumplimiento(df)["Nivel de cumplimiento"].iloc[0]
            result_pdi = _clasificar_estado(val, id_indicador="100")

            assert result_resumen == result_pdi, (
                f"Inconsistencia para valor {val}: "
                f"resumen_general_real={result_resumen}, pdi_acreditacion={result_pdi}"
            )

    def test_no_hardcoding_105(self):
        """Verificar que no existe hardcoding literal de 105 en lógica (no comentarios)."""
        import inspect
        import re

        # Revisar que _ensure_nivel_cumplimiento no tiene "105" en lógica
        source_resumen = inspect.getsource(_ensure_nivel_cumplimiento)
        # Buscar solo en código, no comentarios/docstrings
        lines_code = [
            l
            for l in source_resumen.split("\n")
            if not l.strip().startswith("#")
            and not l.strip().startswith('"""')
            and not l.strip().startswith("'''")
        ]
        code_only = "\n".join(lines_code)

        # Buscar comparaciones directas con 105 (if pct >= 105, if cumpl < 105, etc.)
        assert not re.search(
            r"(if|<|>|<=|>=)\s*\w+\s*[<>=]+\s*105", code_only
        ), "resumen_general_real._ensure_nivel_cumplimiento tiene hardcoding 105"

        # Revisar que _clasificar_estado no tiene "105" en lógica
        source_pdi = inspect.getsource(_clasificar_estado)
        lines_code_pdi = [
            l
            for l in source_pdi.split("\n")
            if not l.strip().startswith("#")
            and not l.strip().startswith('"""')
            and not l.strip().startswith("'''")
        ]
        code_only_pdi = "\n".join(lines_code_pdi)

        assert not re.search(
            r"(if|<|>|<=|>=)\s*\w+\s*[<>=]+\s*105", code_only_pdi
        ), "pdi_acreditacion._clasificar_estado tiene hardcoding 105"

    def test_valores_validos_retornados(self):
        """Verificar que solo se retornan valores válidos."""
        valid_levels = [
            "Peligro",
            "Alerta",
            "Cumplimiento",
            "Sobrecumplimiento",
            "Pendiente de reporte",
            "Sin dato",
        ]

        test_values = [0, 50, 75, 80, 95, 100, 105, 130]

        for val in test_values:
            result = _clasificar_estado(float(val))
            assert result in valid_levels, f"Nivel inválido para {val}: {result}"


class TestProblema7RealData:
    """Tests con datos simulados realistas."""

    def test_multiple_rows_consistentes(self):
        """Múltiples filas deben procesarse consistentemente."""
        df = pd.DataFrame(
            {
                "cumplimiento_pct": [60.0, 80.0, 95.0, 100.0, 105.0, 130.0],
                "Id": ["100", "100", "100", "100", "100", "100"],
                "Indicador": ["A", "B", "C", "D", "E", "F"],
            }
        )

        result = _ensure_nivel_cumplimiento(df)

        expected = [
            "Peligro",
            "Alerta",
            "Alerta",
            "Cumplimiento",
            "Sobrecumplimiento",
            "Sobrecumplimiento",
        ]
        for i, exp in enumerate(expected):
            assert (
                result["Nivel de cumplimiento"].iloc[i] == exp
            ), f"Fila {i}: esperado {exp}, obtuve {result['Nivel de cumplimiento'].iloc[i]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
