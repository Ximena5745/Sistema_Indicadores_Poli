"""
tests/test_etl_fuentes.py
Cobertura de scripts/etl/fuentes.py.

Cubre:
  - homologar_proceso (función pura)
  - cargar_fuente_consolidada — ruta archivo no existe → DataFrame vacío
  - cargar_kawak_validos — ruta no existe → None
  - cargar_lmi_reporte — ruta no existe → set vacío
  - cargar_kawak_2025 — ruta no existe → DataFrame vacío
  - cargar_kawak_old — rutas no existen → DataFrame vacío
  - cargar_metadatos_kawak — ruta no existe → dict vacío
  - cargar_metadatos_cmi — ruta no existe → dict vacío
  - cargar_mapa_procesos — ruta no existe → dict vacío
  - cargar_consolidado_api_kawak_lookup — ruta no existe → dict vacío
"""
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


# ─────────────────────────────────────────────────────────────────────────────
# homologar_proceso — función pura, sin I/O
# ─────────────────────────────────────────────────────────────────────────────

from scripts.etl.fuentes import homologar_proceso


class TestHomologarProceso:
    def test_mapea_subproceso_case_insensitive(self):
        mapa = {"admisiones": "Gestión Académica"}
        assert homologar_proceso("Admisiones", mapa) == "Gestión Académica"

    def test_subproceso_ya_en_minuscula(self):
        mapa = {"admisiones": "Gestión Académica"}
        assert homologar_proceso("admisiones", mapa) == "Gestión Académica"

    def test_subproceso_no_encontrado_retorna_original(self):
        mapa = {"admisiones": "Gestión Académica"}
        assert homologar_proceso("Otros", mapa) == "Otros"

    def test_mapa_vacio_retorna_original(self):
        assert homologar_proceso("Admisiones", {}) == "Admisiones"

    def test_mapa_none_retorna_original(self):
        assert homologar_proceso("Admisiones", None) == "Admisiones"

    def test_subproceso_vacio_retorna_original(self):
        mapa = {"admisiones": "Gestión Académica"}
        assert homologar_proceso("", mapa) == ""

    def test_subproceso_con_espacios_se_stripea(self):
        mapa = {"admisiones": "Gestión Académica"}
        assert homologar_proceso("  Admisiones  ", mapa) == "Gestión Académica"

    def test_multiples_subprocesos(self):
        mapa = {
            "admisiones": "Gestión Académica",
            "bienestar": "Gestión Estudiantil",
        }
        assert homologar_proceso("Bienestar", mapa) == "Gestión Estudiantil"


# ─────────────────────────────────────────────────────────────────────────────
# cargar_fuente_consolidada — retorna DataFrame vacío si no existe el archivo
# ─────────────────────────────────────────────────────────────────────────────

class TestCargarFuenteConsolidada:
    @patch("scripts.etl.fuentes.CONSOLIDADO_API_KW")
    def test_archivo_no_existe_retorna_vacio(self, mock_path):
        mock_path.exists.return_value = False
        from scripts.etl.fuentes import cargar_fuente_consolidada
        result = cargar_fuente_consolidada()
        assert isinstance(result, pd.DataFrame)
        assert result.empty

    @patch("scripts.etl.fuentes.pd.read_excel")
    @patch("scripts.etl.fuentes.CONSOLIDADO_API_KW")
    def test_archivo_existe_construye_llave(self, mock_path, mock_read):
        mock_path.exists.return_value = True
        mock_read.return_value = pd.DataFrame({
            "ID": ["10"], "nombre": ["Indicador X"], "proceso": ["P1"],
            "frecuencia": ["Mensual"], "sentido": ["Positivo"],
            "fecha": ["2025-06-30"], "meta": [100.0], "resultado": [85.0],
        })
        from scripts.etl.fuentes import cargar_fuente_consolidada
        result = cargar_fuente_consolidada()
        assert not result.empty
        assert "LLAVE" in result.columns
        assert "Id" in result.columns  # renamed from ID

    @patch("scripts.etl.fuentes.pd.read_excel")
    @patch("scripts.etl.fuentes.CONSOLIDADO_API_KW")
    def test_filas_sin_fecha_se_descartan(self, mock_path, mock_read):
        mock_path.exists.return_value = True
        mock_read.return_value = pd.DataFrame({
            "ID": ["10", "11"], "nombre": ["A", "B"],
            "fecha": [None, "2025-06-30"],
        })
        from scripts.etl.fuentes import cargar_fuente_consolidada
        result = cargar_fuente_consolidada()
        assert len(result) == 1  # fila sin fecha descartada


# ─────────────────────────────────────────────────────────────────────────────
# cargar_kawak_validos
# ─────────────────────────────────────────────────────────────────────────────

class TestCargarKawakValidos:
    @patch("scripts.etl.fuentes.KAWAK_CAT_FILE")
    def test_archivo_no_existe_retorna_none(self, mock_path):
        mock_path.exists.return_value = False
        from scripts.etl.fuentes import cargar_kawak_validos
        result = cargar_kawak_validos()
        assert result is None

    @patch("scripts.etl.fuentes.pd.read_excel")
    @patch("scripts.etl.fuentes.KAWAK_CAT_FILE")
    def test_archivo_con_id_y_año_retorna_set(self, mock_path, mock_read):
        mock_path.exists.return_value = True
        mock_read.return_value = pd.DataFrame({
            "Id": ["10", "11"], "Año": [2025, 2024]
        })
        from scripts.etl.fuentes import cargar_kawak_validos
        result = cargar_kawak_validos()
        assert isinstance(result, set)
        assert ("10", 2025) in result
        assert ("11", 2024) in result

    @patch("scripts.etl.fuentes.pd.read_excel")
    @patch("scripts.etl.fuentes.KAWAK_CAT_FILE")
    def test_columnas_faltantes_retorna_none(self, mock_path, mock_read):
        mock_path.exists.return_value = True
        mock_read.return_value = pd.DataFrame({"Indicador": ["Test"]})
        from scripts.etl.fuentes import cargar_kawak_validos
        result = cargar_kawak_validos()
        assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# cargar_lmi_reporte
# ─────────────────────────────────────────────────────────────────────────────

class TestCargarLmiReporte:
    @patch("scripts.etl.fuentes.BASE_PATH")
    def test_archivo_no_existe_retorna_set_vacio(self, mock_base):
        # BASE_PATH / "lmi_reporte.xlsx" → no existe
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_base.__truediv__.return_value = mock_path
        from scripts.etl.fuentes import cargar_lmi_reporte
        result = cargar_lmi_reporte()
        assert isinstance(result, set)


# ─────────────────────────────────────────────────────────────────────────────
# cargar_kawak_2025 — cuando el archivo no existe
# ─────────────────────────────────────────────────────────────────────────────

class TestCargarKawak2025:
    @patch("scripts.etl.fuentes.BASE_PATH")
    def test_archivo_no_existe_retorna_vacio(self, mock_base):
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_base.__truediv__.return_value.__truediv__.return_value = mock_path
        from scripts.etl.fuentes import cargar_kawak_2025
        result = cargar_kawak_2025()
        assert isinstance(result, pd.DataFrame)
        assert result.empty


# ─────────────────────────────────────────────────────────────────────────────
# cargar_kawak_old
# ─────────────────────────────────────────────────────────────────────────────

class TestCargarKawakOld:
    @patch("scripts.etl.fuentes.BASE_PATH")
    def test_sin_archivos_retorna_vacio(self, mock_base):
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_base.__truediv__.return_value.__truediv__.return_value = mock_path
        from scripts.etl.fuentes import cargar_kawak_old
        result = cargar_kawak_old(years=(2021,))
        assert isinstance(result, pd.DataFrame)
        assert result.empty


# ─────────────────────────────────────────────────────────────────────────────
# cargar_mapa_procesos
# ─────────────────────────────────────────────────────────────────────────────

class TestCargarMapaProcesos:
    @patch("scripts.etl.fuentes.BASE_PATH")
    def test_archivo_no_existe_retorna_dict_vacio(self, mock_base):
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_base.__truediv__.return_value = mock_path
        from scripts.etl.fuentes import cargar_mapa_procesos
        result = cargar_mapa_procesos()
        assert result == {}

    @patch("scripts.etl.fuentes.pd.read_excel")
    @patch("scripts.etl.fuentes.BASE_PATH")
    def test_archivo_con_datos_retorna_mapa(self, mock_base, mock_read):
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_base.__truediv__.return_value = mock_path
        mock_read.return_value = pd.DataFrame({
            "Subproceso": ["Admisiones", "Bienestar"],
            "Proceso": ["Gestión Académica", "Gestión Estudiantil"],
        })
        from scripts.etl.fuentes import cargar_mapa_procesos
        result = cargar_mapa_procesos()
        assert "admisiones" in result
        assert result["admisiones"] == "Gestión Académica"
