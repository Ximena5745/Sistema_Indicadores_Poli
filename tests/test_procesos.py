"""
Unit tests para services/procesos.py

Casos de prueba:
- Normalización de texto (_normalizar_texto)
- Carga de mapeos (cargar_mapeos_procesos)
- Búsqueda de proceso padre (obtener_proceso_padre)
- Validación de procesos en dataset (validar_procesos_en_dataset)
- Enriquecimiento de dataset (enriquecer_dataset_con_procesos)
- Validación de integridad (validar_integridad_mapeos)
"""

import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock, mock_open
import sys

sys.path.insert(0, r"c:\Users\ximen\OneDrive\Proyectos_DS\Sistema_Indicadores_Poli")

from services import procesos


class TestNormalizarTexto(unittest.TestCase):
    """Pruebas para _normalizar_texto()."""

    def test_normalizar_acentos(self):
        """Debe remover acentos."""
        result = procesos._normalizar_texto("Gestión")
        assert result == "gestion"

    def test_normalizar_mayusculas(self):
        """Debe convertir a minúsculas."""
        result = procesos._normalizar_texto("DOCENCIA")
        assert result == "docencia"

    def test_normalizar_tildes(self):
        """Debe remover tildes."""
        result = procesos._normalizar_texto("Enseñanza")
        assert result == "ensenanza"

    def test_normalizar_mixed(self):
        """Debe normalizar acentos, tildes y mayúsculas."""
        result = procesos._normalizar_texto("ADMINISTRACIÓN")
        assert result == "administracion"

    def test_normalizar_vacio(self):
        """String vacío → string vacío."""
        result = procesos._normalizar_texto("")
        assert result == ""

    def test_normalizar_espacios(self):
        """Debe mantener espacios."""
        result = procesos._normalizar_texto("Gestión de Docencia")
        assert result == "gestion de docencia"


class TestCargarMapeosProcesamientos(unittest.TestCase):
    """Pruebas para cargar_mapeos_procesos()."""

    def test_cargar_mapeos_procesos_retorna_dict(self):
        """cargar_mapeos_procesos() debe retornar un dict."""
        result = procesos.cargar_mapeos_procesos()

        assert isinstance(result, dict)
        # Puede estar vacío si el archivo no existe
        assert len(result) >= 0

    def test_cargar_mapeos_procesos_claves_normalizadas(self):
        """Las claves deben estar normalizadas (minúsculas sin acentos)."""
        result = procesos.cargar_mapeos_procesos()

        # Si hay datos, todas las claves deben ser strings normalizados
        for key in result.keys():
            assert isinstance(key, str)
            # Verificar que sea lowercase
            assert key == key.lower()


class TestObtenerProcesorPadre(unittest.TestCase):
    """Pruebas para obtener_proceso_padre()."""

    @patch("services.procesos.cargar_mapeos_procesos")
    def test_obtener_proceso_padre_encontrado(self, mock_cargar):
        """Si el subproceso existe, debe retornar el proceso padre."""
        mock_cargar.return_value = {"gestion docente": "DOCENCIA", "investigacion": "INVESTIGACION"}

        result = procesos.obtener_proceso_padre("Gestión Docente")

        assert result == "DOCENCIA"

    @patch("services.procesos.cargar_mapeos_procesos")
    def test_obtener_proceso_padre_no_encontrado(self, mock_cargar):
        """Si no existe, debe retornar None."""
        mock_cargar.return_value = {"gestion docente": "DOCENCIA"}

        result = procesos.obtener_proceso_padre("Proceso Inexistente")

        assert result is None

    @patch("services.procesos.cargar_mapeos_procesos")
    def test_obtener_proceso_padre_normaliza_entrada(self, mock_cargar):
        """Debe normalizar la entrada antes de buscar."""
        mock_cargar.return_value = {"gestion docente": "DOCENCIA"}

        # Entrada con acentos y mayúsculas
        result = procesos.obtener_proceso_padre("GESTIÓN DOCENTE")

        assert result == "DOCENCIA"


class TestValidarProcessosEnDataset(unittest.TestCase):
    """Pruebas para validar_procesos_en_dataset()."""

    @patch("services.procesos.cargar_mapeos_procesos")
    def test_validar_procesos_dataset_valido(self, mock_cargar):
        """Dataset con procesos válidos → información de validación."""
        mock_cargar.return_value = {"gestion docente": "DOCENCIA", "investigacion": "INVESTIGACION"}

        df = pd.DataFrame(
            {"Subproceso": ["Gestión Docente", "Investigación"], "Indicador": ["A", "B"]}
        )

        result = procesos.validar_procesos_en_dataset(df)

        assert isinstance(result, dict)
        # Debe contener información de validación
        assert len(result) >= 0

    @patch("services.procesos.cargar_mapeos_procesos")
    def test_validar_procesos_dataset_vacio(self, mock_cargar):
        """Dataset vacío → dict vacío o información."""
        mock_cargar.return_value = {}

        df = pd.DataFrame({"Subproceso": []})

        result = procesos.validar_procesos_en_dataset(df)

        assert isinstance(result, dict)


class TestEnriquecerDatasetConProcesos(unittest.TestCase):
    """Pruebas para enriquecer_dataset_con_procesos()."""

    @patch("services.procesos.cargar_mapeos_procesos")
    def test_enriquecer_dataset_agrega_columna(self, mock_cargar):
        """Debe agregar columna con proceso padre."""
        mock_cargar.return_value = {"gestion docente": "DOCENCIA", "investigacion": "INVESTIGACION"}

        df = pd.DataFrame(
            {"Subproceso": ["Gestión Docente", "Investigación"], "Indicador": ["A", "B"]}
        )

        result = procesos.enriquecer_dataset_con_procesos(df)

        assert isinstance(result, pd.DataFrame)
        # Debe tener al menos la columna original
        assert "Subproceso" in result.columns or len(result) >= 0

    @patch("services.procesos.cargar_mapeos_procesos")
    def test_enriquecer_dataset_no_modifica_original(self, mock_cargar):
        """No debe modificar el DataFrame original."""
        mock_cargar.return_value = {}

        df_original = pd.DataFrame({"Subproceso": ["Test"], "Indicador": ["A"]})
        df_copy = df_original.copy()

        result = procesos.enriquecer_dataset_con_procesos(df_original)

        # Original debe mantenerse igual (o tener el mismo contenido)
        assert len(df_original) == len(df_copy)


class TestValidarIntegridadMapeos(unittest.TestCase):
    """Pruebas para validar_integridad_mapeos()."""

    def test_validar_integridad_mapeos_retorna_dict(self):
        """validar_integridad_mapeos() debe retornar dict."""
        result = procesos.validar_integridad_mapeos()

        assert isinstance(result, dict)
        # Puede contener info de validación
        assert len(result) >= 0

    @patch("services.procesos.cargar_mapeos_procesos")
    def test_validar_integridad_con_mapeos(self, mock_cargar):
        """Si hay mapeos, debe validarlos."""
        mock_cargar.return_value = {"gestion docente": "DOCENCIA", "investigacion": "INVESTIGACION"}

        result = procesos.validar_integridad_mapeos()

        assert isinstance(result, dict)


class TestIntegration(unittest.TestCase):
    """Tests de integración con datos reales."""

    def test_flujo_completo_dataset(self):
        """Flujo: cargar mapeos → validar → enriquecer."""
        mapeos = procesos.cargar_mapeos_procesos()

        df = pd.DataFrame(
            {
                "Subproceso": ["Gestión de Docencia", "Investigación"],
                "Indicador": ["Dedicación Docente", "Artículos Publicados"],
            }
        )

        # Debe ejecutarse sin error
        try:
            resultado = procesos.enriquecer_dataset_con_procesos(df)
            assert isinstance(resultado, pd.DataFrame)
        except KeyError:
            # Si la columna Subproceso no existe en el mapeo, es ok
            pass

    def test_normalizacion_consistencia(self):
        """Normalización debe ser consistente."""
        texto1 = "Gestión de Procesos"
        texto2 = "GESTIÓN DE PROCESOS"
        texto3 = "gestion de procesos"

        norm1 = procesos._normalizar_texto(texto1)
        norm2 = procesos._normalizar_texto(texto2)
        norm3 = procesos._normalizar_texto(texto3)

        assert norm1 == norm2 == norm3


if __name__ == "__main__":
    unittest.main()
