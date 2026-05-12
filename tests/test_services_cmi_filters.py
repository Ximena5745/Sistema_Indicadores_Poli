import pandas as pd

from services.cmi_filters.filters import (
    filter_df_for_cmi_estrategico,
    filter_df_for_cmi_procesos,
    filter_df_for_procesos,
    get_cmi_estrategico_ids,
    get_cmi_procesos_ids,
)
from services.cmi_filters.utils import _normalize_flag_series, _normalize_id_value


def test_normalize_flag_series_mixed_values():
    series = pd.Series([1, "1", "si", "true", "x", 0, "0", "no", "false", "", None])
    normalized = _normalize_flag_series(series)
    assert list(normalized.fillna(0).astype(int)) == [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0]


def test_normalize_id_value_variants():
    assert _normalize_id_value(100) == "100"
    assert _normalize_id_value(100.0) == "100"
    assert _normalize_id_value("100.0") == "100"
    assert _normalize_id_value("  ABC  ") == "ABC"
    assert _normalize_id_value(pd.NA) == ""


def test_get_cmi_estrategico_ids_filters_project(monkeypatch):
    df = pd.DataFrame(
        {
            "Id": ["101", "102", "103"],
            "Indicadores Plan estrategico": [1, 1, 0],
            "Proyecto": [0, 1, 0],
        }
    )
    monkeypatch.setattr("services.cmi_filters.filters.load_cmi_worksheet", lambda: df)

    ids = get_cmi_estrategico_ids()
    assert ids == {"101"}


def test_get_cmi_estrategico_ids_missing_columns(monkeypatch):
    df = pd.DataFrame({"Id": ["1"], "Proyecto": [0]})
    monkeypatch.setattr("services.cmi_filters.filters.load_cmi_worksheet", lambda: df)

    ids = get_cmi_estrategico_ids()
    assert ids == set()


def test_get_cmi_procesos_ids_without_year(monkeypatch):
    df = pd.DataFrame(
        {
            "Id": ["201", "202", "203"],
            "Subprocesos": [1, 0, "si"],
        }
    )
    monkeypatch.setattr("services.cmi_filters.filters.load_cmi_worksheet", lambda: df)

    ids = get_cmi_procesos_ids(year=None)
    assert ids == {"201", "203"}


def test_get_cmi_procesos_ids_with_year_and_cross(monkeypatch):
    df = pd.DataFrame(
        {
            "Id": ["201", "202", "203"],
            "Subprocesos": [1, 1, 1],
        }
    )
    monkeypatch.setattr("services.cmi_filters.filters.load_cmi_worksheet", lambda: df)
    monkeypatch.setattr("services.cmi_filters.filters.load_kawak_active_ids", lambda year: {"202", "999"})

    ids = get_cmi_procesos_ids(year=2026, omit_if_no_cross=True, use_kawak_cross=True)
    assert ids == {"202"}


def test_get_cmi_procesos_ids_no_cross_omit_true(monkeypatch):
    df = pd.DataFrame(
        {
            "Id": ["201", "202"],
            "Subprocesos": [1, 1],
        }
    )
    monkeypatch.setattr("services.cmi_filters.filters.load_cmi_worksheet", lambda: df)
    monkeypatch.setattr("services.cmi_filters.filters.load_kawak_active_ids", lambda year: set())

    ids = get_cmi_procesos_ids(year=2026, omit_if_no_cross=True, use_kawak_cross=True)
    assert ids == set()


def test_filter_df_for_cmi_estrategico(monkeypatch):
    monkeypatch.setattr("services.cmi_filters.filters.get_cmi_estrategico_ids", lambda: {"101", "103"})
    df = pd.DataFrame({"Id": [101, 102, "103"], "Valor": [1, 2, 3]})

    result = filter_df_for_cmi_estrategico(df)
    assert list(result["Id"].astype(str)) == ["101", "103"]
    assert "Id_norm" not in result.columns


def test_filter_df_for_cmi_procesos_returns_empty_when_no_cross(monkeypatch):
    monkeypatch.setattr(
        "services.cmi_filters.filters.get_cmi_procesos_ids",
        lambda year, omit_if_no_cross, use_kawak_cross: set(),
    )
    df = pd.DataFrame({"Id": [201, 202], "Valor": [1, 2]})

    result = filter_df_for_cmi_procesos(df, omit_if_no_cross=True)
    assert result.empty
    assert list(result.columns) == ["Id", "Valor"]


def test_filter_df_for_procesos_applies_subproceso_map(monkeypatch):
    monkeypatch.setattr(
        "services.cmi_filters.filters.get_cmi_procesos_ids",
        lambda year, omit_if_no_cross, use_kawak_cross: {"201", "202", "203"},
    )
    monkeypatch.setattr(
        "services.cmi_filters.filters.get_cmi_procesos_subprocesos",
        lambda map_df: {"Talento Humano", "Financiero"},
    )

    df = pd.DataFrame(
        {
            "Id": [201, 202, 203],
            "Subproceso": ["Talento Humano", "No Mapeado", "Financiero"],
        }
    )
    map_df = pd.DataFrame({"Subproceso": ["Talento Humano", "Financiero"]})

    result = filter_df_for_procesos(df, map_df=map_df)
    assert set(result["Id"].astype(str)) == {"201", "203"}
