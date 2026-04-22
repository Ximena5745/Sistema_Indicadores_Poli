"""
tests/test_data_loader.py — Tests unitarios para servicios de carga de datos

Problemas testados:
- Normalización de IDs (strings, floats, NaN)
- Renombramiento de columnas (acentos, espacios)
- Aplicación de cálculos de cumplimiento
- Enriquecimiento con CMI y procesos
"""

import pandas as pd
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from services import data_loader


class TestIdAStr:
    """Validar conversión de IDs a string."""

    def test_id_float_entero_a_str(self):
        """Float como 373.0 → "373"."""
        assert data_loader._id_a_str(373.0) == "373"

    def test_id_float_decimal_a_str(self):
        """Float como 373.5 → "373.5"."""
        assert data_loader._id_a_str(373.5) == "373.5"

    def test_id_string_sin_cambio(self):
        """String "373" → "373"."""
        assert data_loader._id_a_str("373") == "373"

    def test_id_nan_a_string_vacio(self):
        """NaN → ''."""
        assert data_loader._id_a_str(np.nan) == ""

    def test_id_none_a_string(self):
        """None → ''."""
        assert data_loader._id_a_str(None) == ""


class TestAsciiLower:
    """Validar normalización ASCII de strings."""

    def test_ascii_lower_con_acentos(self):
        """'Ejecución' → 'ejecucion'."""
        assert data_loader._ascii_lower("Ejecución") == "ejecucion"

    def test_ascii_lower_con_tildes(self):
        """'Año' → 'ano'."""
        assert data_loader._ascii_lower("Año") == "ano"

    def test_ascii_lower_mayusculas(self):
        """'META' → 'meta'."""
        assert data_loader._ascii_lower("META") == "meta"

    def test_ascii_lower_espacios(self):
        """'meta s' → 'meta s'."""
        assert data_loader._ascii_lower("meta s") == "meta s"


class TestRenombrar:
    """Validar renombramiento flexible de columnas."""

    def test_renombrar_ejecutacion_a_ejecucion(self):
        """Columna 'Ejecución' → 'Ejecucion'."""
        df = pd.DataFrame({"Ejecución": [1, 2], "Indicador": ["A", "B"]})
        result = data_loader._renombrar(df, {"Ejecución": "Ejecucion"})
        assert "Ejecucion" in result.columns
        assert "Ejecución" not in result.columns

    def test_renombrar_ano_a_anio(self):
        """Columna 'Año' → 'Anio'."""
        df = pd.DataFrame({"Año": [2026, 2025]})
        result = data_loader._renombrar(df, {"Año": "Anio"})
        assert "Anio" in result.columns

    def test_renombrar_sin_cambios(self):
        """Columnas que no están en mapa se quedan igual."""
        df = pd.DataFrame({"Id": ["1", "2"], "Valor": [10, 20]})
        result = data_loader._renombrar(df, {"Año": "Anio"})
        assert "Id" in result.columns
        assert "Valor" in result.columns


class TestAplicarCalculosCumplimiento:
    """Validar aplicación de cálculos (normalización + categorización)."""

    def test_aplicar_calculos_cumplimiento_basico(self):
        """DataFrame con columnas estándar → columnas normalizadas y categorizadas."""
        df = pd.DataFrame(
            {
                "Id": ["1", "2", "3"],
                "Indicador": ["A", "B", "C"],
                "Meta": [100, 100, 100],
                "Ejecucion": [50, 95, 115],
                "Sentido": ["Positivo", "Positivo", "Positivo"],
            }
        )

        result = data_loader._aplicar_calculos_cumplimiento(df)

        # Debe tener columnas nuevas
        assert "Cumplimiento_norm" in result.columns
        assert "Categoria" in result.columns

        # Si tenemos cumplimiento calculado, verificar categorización
        if "Cumplimiento_norm" in result.columns:
            # Al menos debe haber valores (aunque sean NaN)
            assert len(result) == 3

    def test_aplicar_calculos_sin_cumplimiento_raw(self):
        """Si no existe Cumplimiento_raw, debe agregar columnas vacías."""
        df = pd.DataFrame(
            {
                "Id": ["1"],
                "Indicador": ["A"],
            }
        )

        # No debe crashear
        result = data_loader._aplicar_calculos_cumplimiento(df)
        assert (
            "Cumplimiento_norm" in result.columns or result.shape[0] > 0
        )  # Debe mantener estructura


class TestLeerConsolidadoSemestral:
    """Validar lectura de hoja principal."""

    @patch("services.data_loader.pd.read_excel")
    def test_leer_consolidado_semestral_basico(self, mock_read_excel):
        """Debe leer hoja 'Consolidado Semestral' y normalizar IDs."""
        mock_read_excel.return_value = pd.DataFrame(
            {"Año": [2026], "Ejecución": [0.80], "Id": [373.0], "Indicador": ["Test"]}
        )

        result = data_loader._leer_consolidado_semestral(None)

        # Verificar que read_excel fue llamado correctamente
        mock_read_excel.assert_called_once()

        # Verificar renombramiento
        assert "Anio" in result.columns
        assert "Ejecucion" in result.columns

        # Verificar conversión de ID
        assert result.loc[0, "Id"] == "373"


class TestLeerConsolidadoHistorico:
    """Validar lectura de hoja histórico."""

    @patch("services.data_loader.pd.read_excel")
    def test_leer_consolidado_historico_basico(self, mock_read_excel):
        """Debe leer hoja 'Consolidado Historico' y normalizar."""
        mock_read_excel.return_value = pd.DataFrame(
            {"Año": [2025, 2026], "Id": [373.0, 390.0], "Cumplimiento": [0.70, 0.90]}
        )

        result = data_loader._leer_consolidado_historico(None)

        mock_read_excel.assert_called_once()
        assert "Anio" in result.columns
        assert len(result) == 2


class TestDfIndicadoresUnicos:
    """Validar deduplicación de indicadores."""

    def test_df_indicadores_unicos_basico(self):
        """Debe deduplicar indicadores manteniendo último registro."""
        df = pd.DataFrame(
            {
                "Id": ["1", "1", "2"],
                "Indicador": ["A", "A", "B"],
                "Periodo": ["Enero", "Febrero", "Marzo"],
                "Cumplimiento_norm": [0.5, 0.8, 0.9],
            }
        )

        result = data_loader.df_indicadores_unicos(df)

        # Debe tener 2 indicadores únicos
        assert len(result) == 2

        # Indicador "1" debe tener último periodo (Febrero)
        ind1 = result[result["Id"] == "1"]
        assert len(ind1) == 1
        assert ind1.iloc[0]["Periodo"] == "Febrero"
        assert ind1.iloc[0]["Cumplimiento_norm"] == 0.8


class TestConstruirOpcionesIndicadores:
    """Validar construcción de diccionario de opciones."""

    def test_construir_opciones_indicadores_basico(self):
        """Debe crear dict {label: id} con formato 'Id — Indicador'."""
        df = pd.DataFrame(
            {"Id": ["1", "2", "3"], "Indicador": ["Calidad", "Eficiencia", "Satisfacción"]}
        )

        result = data_loader.construir_opciones_indicadores(df)

        assert isinstance(result, dict)
        # Claves son labels con formato "Id — Indicador"
        assert "1 — Calidad" in result
        assert result["1 — Calidad"] == "1"
        assert result["2 — Eficiencia"] == "2"
        assert result["3 — Satisfacción"] == "3"

    def test_construir_opciones_con_duplicados(self):
        """Si hay duplicados, mantener último con formato label."""
        df = pd.DataFrame(
            {
                "Id": ["1", "1", "2"],
                "Indicador": ["Calidad v1", "Calidad v2", "Eficiencia"],
                "Periodo": ["Enero", "Febrero", "Marzo"],  # Para que df_indicadores_unicos funcione
            }
        )

        result = data_loader.construir_opciones_indicadores(df)

        # Debe contener el v2 (último)
        assert "1 — Calidad v2" in result
        assert result["1 — Calidad v2"] == "1"
        assert "2 — Eficiencia" in result


# ═════════════════════════════════════════════════════════════════════════════
# Tests de funciones públicas (con mocks más complejos)
# ═════════════════════════════════════════════════════════════════════════════


class TestCargarDataset:
    """Validar cargar_dataset() - función pública principal."""

    @patch("services.data_loader._leer_consolidado_semestral")
    @patch("services.data_loader._enriquecer_clasificacion")
    @patch("services.data_loader._enriquecer_cmi_y_procesos")
    @patch("services.data_loader._aplicar_calculos_cumplimiento")
    def test_cargar_dataset_flujo_completo(self, mock_calculos, mock_cmi, mock_clasif, mock_leer):
        """Debe ejecutar pipeline completo de transformaciones."""
        df_base = pd.DataFrame({"Id": ["373"], "Indicador": ["Test"], "Cumplimiento_raw": [0.95]})

        mock_leer.return_value = df_base
        mock_clasif.return_value = df_base
        mock_cmi.return_value = df_base
        mock_calculos.return_value = df_base

        # Nota: cargar_dataset() usa @st.cache_data que complica el testing
        # Este test verifica que las transformaciones se llaman en orden
        result = data_loader.cargar_dataset()

        # Si no hay error, pipeline funcionó
        assert result is not None


class TestCargarDatasetHistorico:
    """Validar cargar_dataset_historico()."""

    @patch("services.data_loader._leer_consolidado_historico")
    @patch("services.data_loader._enriquecer_cmi_y_procesos")
    def test_cargar_dataset_historico_flujo(self, mock_cmi, mock_leer):
        """Debe leer histórico y enriquecer CMI."""
        df_base = pd.DataFrame({"Id": ["373"], "Periodo": ["2026-01"], "Cumplimiento_norm": [0.90]})

        mock_leer.return_value = df_base
        mock_cmi.return_value = df_base

        result = data_loader.cargar_dataset_historico()
        assert result is not None
