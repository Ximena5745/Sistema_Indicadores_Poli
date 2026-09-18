"""Tests para scripts/cna_extraction/writer.py — dedup incremental y
preservación de registros históricos, sobre archivos temporales."""
from __future__ import annotations

import pandas as pd
import pytest

from scripts.cna_extraction.writer import METRICAS_COLUMNS, load_existing_llaves, write_incremental


def _record(id_, subindicador, periodo, ejecucion):
    return {
        "Id": id_,
        "Indicador": "Indicador X",
        "Subindicador": subindicador,
        "Factor": "Factor 1. Identidad institucional",
        "Caracteristica": "Característica 3.",
        "Fecha": None,
        "Año": 2019,
        "Mes": None,
        "Periodo": periodo,
        "Ejecución": ejecucion,
        "Ejecución s": "ENT",
        "Decimales": 0,
        "DecimalesEje": 0,
        "Proyecto": None,
        "Llave": f"{id_}|{subindicador or ''}|{periodo}",
    }


@pytest.fixture
def output_file(tmp_path):
    return tmp_path / "Resultados_Consolidados_CNA.xlsx"


def test_first_run_creates_file_with_all_records(output_file):
    records = [_record(1, None, "2019-2", 10), _record(1, None, "2020-2", 20)]
    result = write_incremental(records, output_file)
    assert output_file.exists()
    assert result["registros_nuevos_insertados"] == 2
    assert result["registros_totales"] == 2


def test_second_run_only_appends_new_periods(output_file):
    write_incremental([_record(1, None, "2019-2", 10)], output_file)
    result = write_incremental(
        [_record(1, None, "2019-2", 10), _record(1, None, "2020-2", 20)], output_file
    )
    assert result["registros_nuevos_insertados"] == 1
    assert result["registros_totales"] == 2


def test_historical_rows_are_not_modified(output_file):
    write_incremental([_record(1, None, "2019-2", 999)], output_file)
    write_incremental([_record(1, None, "2020-2", 20)], output_file)

    df = pd.read_excel(output_file, sheet_name="Metricas")
    row_2019 = df[df["Periodo"] == "2019-2"].iloc[0]
    assert row_2019["Ejecución"] == 999


def test_load_existing_llaves_empty_when_no_file(output_file):
    assert load_existing_llaves(output_file) == set()


def test_llave_distinguishes_subindicadores_same_periodo(output_file):
    records = [
        _record(1, "A", "2019-2", 1),
        _record(1, "B", "2019-2", 2),
    ]
    result = write_incremental(records, output_file)
    assert result["registros_nuevos_insertados"] == 2


def test_columns_match_expected_schema(output_file):
    write_incremental([_record(1, None, "2019-2", 10)], output_file)
    df = pd.read_excel(output_file, sheet_name="Metricas")
    assert list(df.columns) == METRICAS_COLUMNS
