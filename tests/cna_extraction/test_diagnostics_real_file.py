"""Test de integración contra el Anexo Estadístico real.

Se salta si el archivo no está presente (es un dato crudo no versionado en
todos los clones), siguiendo el mismo criterio que test_plan_mejoramiento_loader.py.
Solo valida invariantes agregados del reporte, no celda por celda: eso sería
frágil y lento. Este test es la validación de cobertura que el usuario pidió
revisar antes de implementar la Fase 2.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from core.config import DATA_RAW
from scripts.cna_extraction.diagnostics import run_diagnostics

SOURCE = DATA_RAW / "Plan de mejoramiento" / "Anexo Estadístico Dcto. Autoevaluacion.xlsx"

pytestmark = pytest.mark.skipif(not SOURCE.exists(), reason="Anexo Estadístico real no presente en este clon.")


@pytest.fixture(scope="module")
def report():
    return run_diagnostics(SOURCE)


def test_total_sheets_matches_known_workbook(report):
    assert report["total_sheets_workbook"] == 170


def test_catalog_records_match_known_count(report):
    assert report["total_catalog_records"] == 167


def test_unreferenced_sheets_within_expected_bound(report):
    # Se esperan solo un puñado de hojas huérfanas conocidas (ej. "Tabla 81").
    assert len(report["unreferenced_sheets"]) <= 5


def test_no_unexpected_unresolved_sheets(report):
    unresolved = [p for p in report["problems"] if p["kind"] == "unresolved"]
    assert len(unresolved) <= 5


def test_period_histogram_covers_recent_years(report):
    periods = report["periods_found_histogram"]
    assert any(p.startswith("2024") or p == "2024" for p in periods)
