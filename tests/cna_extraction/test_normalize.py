"""Tests para scripts/cna_extraction/normalize.py."""
from __future__ import annotations

from datetime import date

from scripts.cna_extraction.models import CatalogRecord
from scripts.cna_extraction.normalize import (
    build_metricas_rows,
    infer_ejecucion,
    make_llave,
    period_to_fecha_anio_mes,
)
from scripts.cna_extraction.structure_detector import detect_structure


def _catalog_record(numero: int, nombre: str = "Indicador X") -> CatalogRecord:
    return CatalogRecord(
        orden=1,
        factor_raw="Factor 1. Identidad institucional",
        factor_num=1,
        factor_nombre="Identidad institucional",
        caracteristica="Característica 3. Formación integral",
        tabla_no=numero,
        grafico_no=None,
        nombre=nombre,
        fuente="",
        responsable="",
        enlace="",
        observaciones="",
        tipo="tabla",
        numero=numero,
        id_hint=f"Tabla {numero}",
    )


class TestPeriodToFechaAnioMes:
    def test_semester_1(self):
        fecha, anio, mes, periodo = period_to_fecha_anio_mes("2024-1")
        assert (fecha, anio, mes, periodo) == (date(2024, 6, 30), 2024, "Junio", "2024-1")

    def test_semester_2(self):
        fecha, anio, mes, periodo = period_to_fecha_anio_mes("2024-2")
        assert (fecha, anio, mes, periodo) == (date(2024, 12, 31), 2024, "Diciembre", "2024-2")

    def test_plain_year_becomes_annual_close(self):
        fecha, anio, mes, periodo = period_to_fecha_anio_mes("2019")
        assert (fecha, anio, mes, periodo) == (date(2019, 12, 31), 2019, "Diciembre", "2019-2")

    def test_none_period(self):
        assert period_to_fecha_anio_mes(None) == (None, None, None, None)


class TestInferEjecucion:
    def test_integer_is_ent(self):
        assert infer_ejecucion(42) == (42.0, "ENT", False)

    def test_proportion_is_percent(self):
        assert infer_ejecucion(0.34) == (0.34, "%", False)

    def test_decimal_is_dec(self):
        assert infer_ejecucion(3.5) == (3.5, "DEC", False)

    def test_dash_placeholder_is_missing_not_qualitative(self):
        # normalize_missing ya debería haber convertido "-" a None antes de llegar aquí.
        assert infer_ejecucion(None) == (None, None, False)

    def test_free_text_is_qualitative(self):
        value, unit, es_cualitativo = infer_ejecucion("120 estudiantes")
        assert es_cualitativo is True
        assert value is None


class TestMakeLlave:
    def test_format(self):
        assert make_llave(23, "Estudiantes", "2019-2") == "23|Estudiantes|2019-2"

    def test_none_subindicador(self):
        assert make_llave(23, None, "2019-2") == "23||2019-2"


class TestBuildMetricasRows:
    def test_flat_table_no_subindicador(self):
        raw_rows = [
            ["Tabla NO", 1],
            ["Nombre", "Indicador simple"],
            [],
            ["Categoria", 2019, 2020],
            ["Total", 10, 20],
        ]
        structure = detect_structure(raw_rows, 1)
        records = build_metricas_rows(structure, _catalog_record(1))
        assert len(records) == 2
        assert all(r["Subindicador"] is None for r in records)
        assert all(r["Id"] == 1 for r in records)
        assert {r["Ejecución"] for r in records} == {10.0, 20.0}

    def test_missing_total_is_computed_by_sum(self):
        raw_rows = [
            ["Tabla NO", 2],
            ["Nombre", "Indicador con subdivisiones sin total"],
            [],
            ["Dimensión", 2019, 2020],
            ["Académica", 3, 4],
            ["Cultural", 5, 6],
        ]
        structure = detect_structure(raw_rows, 2)
        assert structure.has_explicit_total is False
        stats = {"valores_cualitativos_no_convertidos": 0, "totales_calculados_por_suma": 0}
        records = build_metricas_rows(structure, _catalog_record(2), stats)

        totales = [r for r in records if r["Subindicador"] is None]
        assert {r["Periodo"] for r in totales} == {"2019-2", "2020-2"}
        total_2019 = next(r for r in totales if r["Periodo"] == "2019-2")
        assert total_2019["Ejecución"] == 8.0  # 3 + 5
        assert stats["totales_calculados_por_suma"] == 2

    def test_explicit_total_row_used_as_indicador_principal(self):
        raw_rows = [
            ["Tabla NO", 3],
            ["Nombre", "Indicador con total explícito"],
            [],
            ["Dimensión", 2019],
            ["Académica", 3],
            ["Total", 8],
        ]
        structure = detect_structure(raw_rows, 3)
        assert structure.has_explicit_total is True
        records = build_metricas_rows(structure, _catalog_record(3))
        principal = next(r for r in records if r["Subindicador"] is None)
        assert principal["Ejecución"] == 8.0
        # No debe haber un total calculado adicional por suma.
        assert len([r for r in records if r["Subindicador"] is None]) == 1

    def test_qualitative_value_not_converted(self):
        raw_rows = [
            ["Tabla NO", 4],
            ["Nombre", "Actividad y población impactada"],
            [],
            ["Año", "Actividad", "Población impactada", "Lugar"],
            [2020, "Evento A", "100 estudiantes", "Poli"],
        ]
        structure = detect_structure(raw_rows, 4)
        # Esta tabla cae en event_log_atypical -> no produce registros en Metricas.
        stats = {"valores_cualitativos_no_convertidos": 0, "totales_calculados_por_suma": 0}
        records = build_metricas_rows(structure, _catalog_record(4), stats)
        assert records == []

    def test_llave_extended_key_avoids_collision_across_subindicadores(self):
        raw_rows = [
            ["Tabla NO", 5],
            ["Nombre", "x"],
            [],
            ["Dimensión", 2019],
            ["A", 1],
            ["B", 2],
        ]
        structure = detect_structure(raw_rows, 5)
        records = build_metricas_rows(structure, _catalog_record(5))
        llaves = [r["Llave"] for r in records if r["Subindicador"] is not None]
        assert len(llaves) == len(set(llaves))
