"""Tests para scripts/cna_extraction/catalog.py, con workbooks openpyxl
pequeños construidos en el propio test (sin depender del xlsx real)."""
from __future__ import annotations

import openpyxl
import pytest

from scripts.cna_extraction.catalog import SHEET_INDICE, load_catalog

HEADER = [
    "Factor",
    "SUBCAPÍTULO/CARACTERÍSTICA",
    "Orden",
    "Tabla No",
    "Gráfico",
    "Nombre",
    "Fuente",
    "Responsable Información",
    "Enlace",
    "Observaciones",
]


@pytest.fixture
def catalog_path(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = SHEET_INDICE
    ws.append(HEADER)
    ws.append(["FACTOR 1. Identidad institucional", "Característica 3. Formación integral", 1, 23, None, "Resultados de formación integral", "DAC", "Hector", "Carlos", None])
    ws.append(["FACTOR 3. Desarrollo, gestión y sostenibilidad institucional", "Característica 8. Procesos de Comunicación", 2, None, "Ilustración 20", "Frecuencia de uso de medios", "Mercadeo", "Nestor", "Laura", None])
    ws.append([None, None, None, None, None, None, None, None, None, None])  # fila vacía, debe ignorarse
    path = tmp_path / "anexo.xlsx"
    wb.save(path)
    return path


def test_load_catalog_returns_one_record_per_row(catalog_path):
    records = load_catalog(catalog_path)
    assert len(records) == 2


def test_tabla_record_unifies_numero_and_tipo(catalog_path):
    records = load_catalog(catalog_path)
    tabla_rec = next(r for r in records if r.tipo == "tabla")
    assert tabla_rec.numero == 23
    assert tabla_rec.tabla_no == 23
    assert tabla_rec.factor_num == 1
    assert tabla_rec.factor_nombre == "Identidad institucional"


def test_grafico_record_with_string_number_extracts_numero(catalog_path):
    records = load_catalog(catalog_path)
    graf_rec = next(r for r in records if r.tipo == "grafico")
    assert graf_rec.numero == 20
    assert graf_rec.grafico_no == "Ilustración 20"
    assert graf_rec.factor_num == 3
