"""Tests para scripts/cna_extraction/structure_detector.py.

Un test por cada patrón de estructura documentado en el plan (fixtures
sintéticas armadas a mano, sin depender del xlsx real).
"""
from __future__ import annotations

from scripts.cna_extraction.structure_detector import detect_structure, normalize_missing


class TestNormalizeMissing:
    def test_dash_and_blank_become_none(self):
        assert normalize_missing("-") is None
        assert normalize_missing("") is None
        assert normalize_missing("   ") is None

    def test_special_space_chars_become_none(self):
        assert normalize_missing("\xa0") is None
        assert normalize_missing(" ") is None

    def test_real_values_pass_through(self):
        assert normalize_missing(42) == 42
        assert normalize_missing("Instagram") == "Instagram"


class TestHorizontalFlat:
    def test_single_category_column(self):
        raw_rows = [
            ["Tabla NO", 1],
            ["Nombre", "Indicador simple"],
            [],
            ["Categoria", 2019, 2020, 2021],
            ["A", 10, 20, 30],
            ["B", 5, 6, 7],
        ]
        structure = detect_structure(raw_rows, 1)
        assert structure.kind == "horizontal_periods_flat"
        assert [pc.period for pc in structure.period_columns] == ["2019", "2020", "2021"]
        assert structure.category_columns == [0]
        values_a = [r["value"] for r in structure.rows if r["category_path"] == ["A"]]
        assert values_a == [10, 20, 30]


class TestHorizontal2LevelRows:
    def test_forward_fill_and_subtotal_row_preserved(self):
        raw_rows = [
            ["Tabla NO", 2],
            ["Nombre", "Indicador jerárquico"],
            [],
            [None, "Nivel", "2019-1", "2019-2"],
            ["Grupo A", "X", 1, 2],
            [None, "Y", 3, 4],
            ["Total Grupo A", None, 4, 6],
            ["Grupo B", "Z", 5, 6],
        ]
        structure = detect_structure(raw_rows, 2)
        assert structure.kind == "horizontal_periods_2level_rows"
        assert structure.category_columns == [0, 1]
        # La fila "Total Grupo A" no se descarta: queda marcada como total_explicito.
        total_rows = [r for r in structure.rows if r["row_kind"] == "total_explicito"]
        assert total_rows, "la fila Total debe conservarse, no descartarse"
        assert all("Total Grupo A" in r["category_path"] for r in total_rows)
        assert structure.has_explicit_total is True
        # La fila "Grupo A" > "Y" (forward-fill de la categoría dispersa) sigue como detalle.
        detalle_y = [r for r in structure.rows if r["category_path"] == ["Grupo A", "Y"]]
        assert detalle_y and all(r["row_kind"] == "detalle" for r in detalle_y)


class TestHorizontal2LevelHeader:
    def test_group_row_forward_filled_over_period_row(self):
        raw_rows = [
            ["Tabla NO", 3],
            ["Nombre", "Frecuencia de uso"],
            [],
            ["Medio", "Instagram", None, "Facebook", None],
            ["Año", 2022, 2023, 2022, 2023],
            ["Lo uso siempre", 10, 20, 30, 40],
        ]
        structure = detect_structure(raw_rows, 3)
        assert structure.kind == "horizontal_periods_2level_header"
        groups = [pc.group_label for pc in structure.period_columns]
        assert groups == ["Instagram", "Instagram", "Facebook", "Facebook"]
        row = next(r for r in structure.rows if r["category_path"] == ["Lo uso siempre"])
        assert row["value"] in (10, 20, 30, 40)


class TestTrailingTotalColumnExcluded:
    def test_total_column_not_treated_as_period(self):
        raw_rows = [
            ["Tabla NO", 4],
            ["Nombre", "x"],
            [],
            ["Cat", 2019, 2020, "Total"],
            ["A", 1, 2, 3],
        ]
        structure = detect_structure(raw_rows, 4)
        periods = [pc.period for pc in structure.period_columns]
        assert periods == ["2019", "2020"]
        assert 3 in structure.excluded_columns


class TestBlankSeparatorColumn:
    def test_blank_column_between_periods_is_excluded(self):
        raw_rows = [
            ["Tabla NO", 5],
            ["Nombre", "x"],
            [],
            ["Cat", 2019, None, 2020],
            ["A", 1, None, 2],
        ]
        structure = detect_structure(raw_rows, 5)
        periods = [pc.period for pc in structure.period_columns]
        assert periods == ["2019", "2020"]
        assert 2 in structure.excluded_columns


class TestSnapshotNoPeriod:
    def test_categorical_table_without_periods(self):
        raw_rows = [
            ["Tabla NO", 7],
            ["Nombre", "conteo"],
            [],
            ["Proceso", "Estrategicos", "Gestion", "Total"],
            ["Auditoria", None, 2, 2],
            ["Total", 1, 13, 14],
        ]
        structure = detect_structure(raw_rows, 7)
        assert structure.kind == "snapshot_no_period"
        assert not structure.period_columns
        total_row = [r for r in structure.rows if r["category_path"][0] == "Total"]
        assert total_row and all(r["row_kind"] == "total_explicito" for r in total_row)


class TestEventLogAtypical:
    def test_activity_log_not_forced_into_period_model(self):
        raw_rows = [
            ["Tabla NO", 8],
            ["Nombre", "eventos"],
            [],
            ["Año", "Actividad", "Población impactada", "Lugar"],
            [2020, "Evento A", "100 personas", "Poli"],
        ]
        structure = detect_structure(raw_rows, 8)
        assert structure.kind == "event_log_atypical"
        assert structure.rows == []


class TestVerticalPeriods:
    def test_periods_in_leftmost_column(self):
        raw_rows = [
            ["Tabla NO", 9],
            ["Nombre", "vertical"],
            [],
            ["Periodo", "CategoriaA", "CategoriaB"],
            ["2019-1", 10, 20],
            ["2019-2", 11, 21],
        ]
        structure = detect_structure(raw_rows, 9)
        assert structure.kind == "vertical_periods"
        periods = sorted({r["period"] for r in structure.rows})
        assert periods == ["2019-1", "2019-2"]
        value = next(
            r["value"]
            for r in structure.rows
            if r["period"] == "2019-1" and r["category_path"] == ["CategoriaA"]
        )
        assert value == 10


class TestUnresolved:
    def test_no_data_rows_after_header_block(self):
        raw_rows = [
            ["Tabla NO", 99],
            ["Nombre", "vacía"],
        ]
        structure = detect_structure(raw_rows, 99)
        assert structure.kind == "unresolved"
        assert structure.issues
