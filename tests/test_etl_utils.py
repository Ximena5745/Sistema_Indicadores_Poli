"""
tests/test_etl_utils.py
Cobertura de módulos ETL utilitarios puros:
  - scripts/etl/normalizacion.py
  - scripts/etl/periodos.py
  - scripts/etl/no_aplica.py
  - scripts/etl/signos.py (básico)
"""
import math
import numpy as np
import pandas as pd
import pytest

# ─────────────────────────────────────────────────────────────────────────────
# normalizacion.py
# ─────────────────────────────────────────────────────────────────────────────
from scripts.etl.normalizacion import (
    _id_str,
    id_str,
    make_llave,
    nan2none,
    _es_vacio,
    es_vacio,
    limpiar_html,
    limpiar_clasificacion,
    parse_json_safe,
    _fmt_val_raw,
    COL_ALIASES,
    MESES_ES,
)


class TestIdStr:
    def test_entero_normal(self):
        assert _id_str(123) == "123"

    def test_float_con_cero(self):
        assert _id_str(123.0) == "123"

    def test_float_sin_cero(self):
        assert _id_str(1.5) == "1.5"

    def test_string_con_punto_cero(self):
        assert _id_str("99.0") == "99"

    def test_string_normal(self):
        assert _id_str("abc") == "abc"

    def test_alias_publico(self):
        assert id_str is _id_str


class TestMakeLlave:
    def test_llave_bien_formada(self):
        llave = make_llave("68", "2024-06-30")
        assert llave == "68-2024-06-30"

    def test_llave_con_id_float(self):
        llave = make_llave(68.0, "2024-06-30")
        assert llave == "68-2024-06-30"

    def test_llave_mes_con_cero(self):
        llave = make_llave("5", "2024-01-31")
        assert llave == "5-2024-01-31"

    def test_fecha_invalida_retorna_none(self):
        assert make_llave("68", "no-es-fecha") is None

    def test_id_none_usa_string_none(self):
        # _id_str(None) retorna "None"; make_llave no falla, genera "None-..."
        llave = make_llave(None, "2024-06-30")
        assert llave == "None-2024-06-30"


class TestNan2None:
    def test_none_sigue_siendo_none(self):
        assert nan2none(None) is None

    def test_nan_se_convierte(self):
        assert nan2none(float("nan")) is None

    def test_valor_normal_se_conserva(self):
        assert nan2none(42) == 42

    def test_string_se_conserva(self):
        assert nan2none("hola") == "hola"


class TestEsVacio:
    def test_none(self):
        assert _es_vacio(None) is True

    def test_nan(self):
        assert _es_vacio(float("nan")) is True

    def test_string_vacio(self):
        assert _es_vacio("") is True

    def test_string_nan(self):
        assert _es_vacio("nan") is True

    def test_string_none(self):
        assert _es_vacio("None") is True

    def test_lista_vacia_str(self):
        assert _es_vacio("[]") is True

    def test_valor_real(self):
        assert _es_vacio("hola") is False

    def test_cero(self):
        assert _es_vacio(0) is False

    def test_alias_publico(self):
        assert es_vacio is _es_vacio


class TestLimpiarHtml:
    def test_entidades_vocales(self):
        assert limpiar_html("Gesti&oacute;n") == "Gestión"
        assert limpiar_html("N&iacute;vel") == "Nível"
        assert limpiar_html("P&eacute;rdida") == "Pérdida"

    def test_ampersand(self):
        assert limpiar_html("A &amp; B") == "A & B"

    def test_no_string_sin_cambio(self):
        assert limpiar_html(42) == 42
        assert limpiar_html(None) is None

    def test_sin_entidades(self):
        assert limpiar_html("Hola") == "Hola"


class TestLimpiarClasificacion:
    def test_estrategico(self):
        result = limpiar_clasificacion("Estrat&eacute;gico")
        assert result == "Estratégico"

    def test_no_string_sin_cambio(self):
        assert limpiar_clasificacion(5) == 5


class TestParseJsonSafe:
    def test_lista_python(self):
        result = parse_json_safe("[1, 2, 3]")
        assert result == [1, 2, 3]

    def test_dict_python(self):
        result = parse_json_safe("{'a': 1}")
        assert result == {"a": 1}

    def test_none_retorna_none(self):
        assert parse_json_safe(None) is None

    def test_vacio_retorna_none(self):
        assert parse_json_safe("") is None

    def test_nan_retorna_none(self):
        assert parse_json_safe(float("nan")) is None

    def test_invalido_retorna_none(self):
        assert parse_json_safe("esto no es json {{{") is None


class TestFmtValRaw:
    def test_none_retorna_vacio(self):
        assert _fmt_val_raw(None) == ""

    def test_nan_retorna_vacio(self):
        assert _fmt_val_raw(float("nan")) == ""

    def test_cero_retorna_vacio(self):
        assert _fmt_val_raw("0") == ""

    def test_valor_real(self):
        assert _fmt_val_raw("%") == "%"

    def test_numero_real(self):
        assert _fmt_val_raw("ENT") == "ENT"


class TestColAliases:
    def test_año_mapea_a_anio(self):
        assert COL_ALIASES["Año"] == "Anio"

    def test_ejecucion_con_tilde(self):
        assert COL_ALIASES["Ejecución"] == "Ejecucion"

    def test_tipo_registro(self):
        assert COL_ALIASES["Tipo_Registro"] == "TipoRegistro"


class TestMesesEs:
    def test_todos_los_meses(self):
        assert len(MESES_ES) == 12
        assert MESES_ES[1] == "Enero"
        assert MESES_ES[12] == "Diciembre"


# ─────────────────────────────────────────────────────────────────────────────
# periodos.py
# ─────────────────────────────────────────────────────────────────────────────
from scripts.etl.periodos import (
    ultimo_dia_mes,
    fechas_por_periodicidad,
    _fecha_es_periodo_valido,
)


class TestUltimoDiaMes:
    def test_enero(self):
        assert ultimo_dia_mes(2025, 1) == 31

    def test_febrero_no_bisiesto(self):
        assert ultimo_dia_mes(2025, 2) == 28

    def test_febrero_bisiesto(self):
        assert ultimo_dia_mes(2024, 2) == 29

    def test_abril(self):
        assert ultimo_dia_mes(2025, 4) == 30

    def test_diciembre(self):
        assert ultimo_dia_mes(2025, 12) == 31


class TestFechasPorPeriodicidad:
    def test_mensual_tiene_12_fechas(self):
        fechas = fechas_por_periodicidad("Mensual", 2025)
        assert len(fechas) == 12

    def test_trimestral_tiene_4(self):
        fechas = fechas_por_periodicidad("Trimestral", 2025)
        assert len(fechas) == 4

    def test_semestral_tiene_2(self):
        fechas = fechas_por_periodicidad("Semestral", 2025)
        assert len(fechas) == 2

    def test_anual_tiene_1(self):
        fechas = fechas_por_periodicidad("Anual", 2025)
        assert len(fechas) == 1
        assert fechas[0].month == 12 and fechas[0].day == 31

    def test_periodicidad_desconocida_retorna_diciembre(self):
        fechas = fechas_por_periodicidad("Desconocida", 2025)
        assert len(fechas) == 1
        assert fechas[0].month == 12

    def test_fechas_son_ultimo_dia(self):
        for fecha in fechas_por_periodicidad("Mensual", 2025):
            assert fecha.day == ultimo_dia_mes(fecha.year, fecha.month)


class TestFechaEsPeriodoValido:
    def test_semestral_junio_ultimo_dia(self):
        fecha = pd.Timestamp(2025, 6, 30)
        assert _fecha_es_periodo_valido(fecha, "Semestral") is True

    def test_semestral_junio_no_ultimo_dia(self):
        fecha = pd.Timestamp(2025, 6, 15)
        assert _fecha_es_periodo_valido(fecha, "Semestral") is False

    def test_semestral_mes_invalido(self):
        fecha = pd.Timestamp(2025, 3, 31)
        assert _fecha_es_periodo_valido(fecha, "Semestral") is False

    def test_mensual_cualquier_mes_ultimo_dia(self):
        fecha = pd.Timestamp(2025, 3, 31)
        assert _fecha_es_periodo_valido(fecha, "Mensual") is True

    def test_periodicidad_desconocida_siempre_true(self):
        fecha = pd.Timestamp(2025, 5, 15)
        assert _fecha_es_periodo_valido(fecha, "Desconocida") is True


# ─────────────────────────────────────────────────────────────────────────────
# no_aplica.py
# ─────────────────────────────────────────────────────────────────────────────
from scripts.etl.no_aplica import is_na_record, _tiene_datos_utiles, SIGNO_NA


class TestSigNoNA:
    def test_constante(self):
        assert SIGNO_NA == "No Aplica"


class TestTieneDatosUtiles:
    def test_variables_con_valor(self):
        row = {"variables": "[{'nombre': 'x', 'valor': 10}]"}
        assert _tiene_datos_utiles(row) is True

    def test_variables_sin_valor(self):
        row = {"variables": "[{'nombre': 'x', 'valor': None}]"}
        assert _tiene_datos_utiles(row) is False

    def test_series_con_resultado(self):
        row = {"series": "[{'resultado': 5.0, 'meta': 10}]"}
        assert _tiene_datos_utiles(row) is True

    def test_sin_variables_ni_series(self):
        row = {"variables": None, "series": None}
        assert _tiene_datos_utiles(row) is False

    def test_variables_vacias(self):
        row = {"variables": "[]", "series": "[]"}
        assert _tiene_datos_utiles(row) is False


class TestIsNaRecord:
    def test_analisis_no_aplica(self):
        row = {"analisis": "No aplica para este periodo"}
        assert is_na_record(row) is True

    def test_analisis_vacio_sin_resultado(self):
        row = {"analisis": "", "resultado": None, "variables": None, "series": None}
        assert is_na_record(row) is True

    def test_tiene_resultado_numerico(self):
        row = {"analisis": "", "resultado": "85.0"}
        assert is_na_record(row) is False

    def test_tiene_variables_con_datos(self):
        row = {
            "analisis": "",
            "resultado": None,
            "variables": "[{'nombre': 'x', 'valor': 10}]",
            "series": None,
        }
        assert is_na_record(row) is False


# ─────────────────────────────────────────────────────────────────────────────
# signos.py (básico)
# ─────────────────────────────────────────────────────────────────────────────
from scripts.etl.signos import obtener_signos


class TestObtenerSignos:
    def _df(self, records):
        return pd.DataFrame(records) if records else pd.DataFrame()

    def test_signo_basico(self):
        df = pd.DataFrame([{
            "Id": "10", "Fecha": "2025-06-30",
            "Meta_Signo": "%", "Ejecucion_Signo": "%",
            "Decimales_Meta": 2, "Decimales_Ejecucion": 2,
        }])
        vacio = pd.DataFrame(columns=["Id", "Fecha"])
        signos = obtener_signos(df, vacio, vacio)
        assert "10" in signos
        assert signos["10"]["ejec_signo"] == "%"

    def test_no_aplica_no_sobreescribe_real(self):
        df1 = pd.DataFrame([{
            "Id": "10", "Fecha": "2025-01-31",
            "Ejecucion_Signo": "%",
        }])
        df2 = pd.DataFrame([{
            "Id": "10", "Fecha": "2025-06-30",
            "Ejecucion_Signo": "No Aplica",
        }])
        vacio = pd.DataFrame(columns=["Id", "Fecha"])
        signos = obtener_signos(df1, df2, vacio)
        assert signos["10"]["ejec_signo"] == "%"

    def test_no_aplica_registra_si_no_hay_signo_real(self):
        df = pd.DataFrame([{
            "Id": "20", "Fecha": "2025-06-30",
            "Ejecucion_Signo": "No Aplica",
        }])
        vacio = pd.DataFrame(columns=["Id", "Fecha"])
        signos = obtener_signos(df, vacio, vacio)
        assert signos["20"]["ejec_signo"] == "No Aplica"

    def test_dataframes_vacios(self):
        vacio = pd.DataFrame(columns=["Id", "Fecha"])
        signos = obtener_signos(vacio, vacio, vacio)
        assert signos == {}
