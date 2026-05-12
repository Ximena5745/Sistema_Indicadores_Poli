from pathlib import Path

import pandas as pd

from scripts.consolidation.core import constants
from scripts.consolidation.core.logging_config import setup_logging
from scripts.consolidation.core.utils import (
    calcular_cumplimiento,
    es_registro_na,
    es_vacio,
    extraer_meta_ejec_variables,
    extraer_por_simbolo,
    fecha_es_periodo_valido,
    fechas_por_periodicidad,
    fmt_val_raw,
    id_str,
    limpiar_clasificacion,
    limpiar_html,
    make_llave,
    nan2none,
    parse_json_safe,
    tiene_datos_utiles,
    ultimo_dia_mes,
)


def test_make_llave_ok_y_error():
    llave = make_llave(123.0, "2026-05-12")
    assert llave == "123-2026-05-12"

    invalida = make_llave("X", "fecha-invalida")
    assert invalida is None


def test_ultimo_dia_mes_y_periodicidad():
    assert ultimo_dia_mes(2024, 2) == 29

    fechas = fechas_por_periodicidad("Trimestral", 2026)
    assert [f.month for f in fechas] == [12, 9, 6, 3]


def test_fecha_es_periodo_valido():
    assert fecha_es_periodo_valido(pd.Timestamp("2026-06-30"), "Semestral")
    assert not fecha_es_periodo_valido(pd.Timestamp("2026-05-31"), "Semestral")
    assert not fecha_es_periodo_valido(pd.Timestamp("2026-06-29"), "Semestral")


def test_limpieza_html_clasificacion():
    assert limpiar_clasificacion("Estrat&eacute;gico &amp; prueba") == "Estratégico & prueba"
    assert limpiar_html("Gesti&oacute;n &amp; Planeaci&oacute;n") == "Gestión & Planeación"


def test_parse_json_nan2none_idstr():
    parsed = parse_json_safe("[{'a': 1}]")
    assert isinstance(parsed, list)
    assert parse_json_safe("{invalido") is None

    assert nan2none(float("nan")) is None
    assert nan2none(5) == 5
    assert id_str("77.0") == "77"


def test_es_vacio_fmt_val_raw():
    assert es_vacio(None)
    assert es_vacio("[]")
    assert not es_vacio("dato")

    assert fmt_val_raw(None) == ""
    assert fmt_val_raw("  DEC ") == "DEC"
    assert fmt_val_raw("0") == ""


def test_calcular_cumplimiento_casos():
    capped, real = calcular_cumplimiento(100, 120, "Positivo")
    assert capped == 1.2 and real == 1.2

    capped2, real2 = calcular_cumplimiento(100, 50, "Negativo")
    assert capped2 == 1.3 and real2 == 2.0

    assert calcular_cumplimiento(0, 10, "Positivo") == (None, None)


def test_extraer_meta_ejec_variables_y_simbolo():
    vars_list = [
        {"nombre": "Valor real", "valor": 30},
        {"nombre": "Objetivo esperado", "valor": 50},
    ]
    meta, ejec = extraer_meta_ejec_variables(vars_list)
    assert meta == 50 and ejec == 30

    vars_sim = [
        {"simbolo": "m1", "valor": 10},
        {"simbolo": "M2", "valor": 20},
    ]
    assert extraer_por_simbolo(vars_sim, "m2") == 20.0
    assert extraer_por_simbolo(vars_sim, "ZZ") is None


def test_tiene_datos_utiles_y_registro_na():
    row_util = {
        "variables": "[{'valor': 5}]",
        "series": "[]",
        "resultado": None,
    }
    assert tiene_datos_utiles(row_util)

    row_na = {
        "analisis": "Periodo no aplica por cierre",
        "resultado": None,
        "variables": "[]",
        "series": "[]",
    }
    assert es_registro_na(row_na)

    row_no_na = {
        "analisis": "",
        "resultado": 10,
        "variables": "[]",
        "series": "[]",
    }
    assert not es_registro_na(row_no_na)


def test_constants_paths_y_sets():
    paths = constants.get_project_paths()

    assert isinstance(paths["ROOT"], Path)
    assert "INPUT_FILE" in paths and "OUTPUT_FILE" in paths
    assert constants.EXT_SER_SUM_VAR in constants.EXT_SERIES_TIPOS
    assert constants.EXT_DESGLOSE_SERIES == "Desglose Series"


def test_setup_logging_escribe_archivo(tmp_path):
    log_file = tmp_path / "logs" / "test.log"
    setup_logging(log_file=log_file, console=False)

    import logging

    logging.getLogger("tests.logging").info("mensaje-prueba")

    for h in logging.getLogger().handlers:
        if hasattr(h, "flush"):
            h.flush()

    assert log_file.exists()
    contenido = log_file.read_text(encoding="utf-8")
    assert "mensaje-prueba" in contenido
