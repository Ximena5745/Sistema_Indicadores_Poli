from pathlib import Path

import pandas as pd

from scripts.consolidation.extractors.factory import ExtractorFactory
from scripts.consolidation.extractors.strategies import (
    APIDirectExtractor,
    HeuristicExtractor,
    NARecordExtractor,
    SeriesSumExtractor,
    VariableSymbolExtractor,
)
from scripts.consolidation.loaders.data_loader import DataLoader
import scripts.consolidation.loaders.data_loader as dl_module


def _mk_loader_paths(tmp_path: Path) -> dict:
    base = tmp_path / "data" / "raw"
    out = tmp_path / "data" / "output"
    (base / "Fuentes Consolidadas").mkdir(parents=True, exist_ok=True)
    (base / "Kawak").mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)

    paths = {
        "ROOT": tmp_path,
        "BASE_PATH": base,
        "INPUT_FILE": base / "Resultados_Consolidados_Fuente.xlsx",
        "OUTPUT_DIR": out,
        "OUTPUT_FILE": out / "Resultados Consolidados.xlsx",
        "KAWAK_CAT_FILE": base / "Fuentes Consolidadas" / "Indicadores Kawak.xlsx",
        "CONSOLIDADO_API_KW": base / "Fuentes Consolidadas" / "Consolidado_API_Kawak.xlsx",
    }
    for p in [
        paths["INPUT_FILE"],
        paths["KAWAK_CAT_FILE"],
        paths["CONSOLIDADO_API_KW"],
        base / "lmi_reporte.xlsx",
    ]:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x", encoding="utf-8")
    return paths


def test_factory_patterns_and_fallback():
    assert isinstance(ExtractorFactory.create_extractor("LAST"), APIDirectExtractor)
    assert isinstance(ExtractorFactory.create_extractor("VARIABLES"), VariableSymbolExtractor)
    assert isinstance(ExtractorFactory.create_extractor("SUM_SER"), SeriesSumExtractor)
    assert isinstance(ExtractorFactory.create_extractor("DESCONOCIDO"), HeuristicExtractor)


def test_api_direct_extractor_and_na_extractor():
    api = APIDirectExtractor()
    na = NARecordExtractor()

    r1 = api.extract({"resultado": 55.0, "meta": 100.0})
    r2 = na.extract({"analisis": "No aplica para este periodo", "resultado": None})

    assert r1.ejec == 55.0 and r1.fuente == "api_directo"
    assert r2.es_na is True and r2.fuente == "na_record"


def test_variable_symbol_extractor_prefiere_simbolo_configurado():
    ext = VariableSymbolExtractor({"simbolo_ejec": "EJ", "simbolo_meta": "ME"})
    row = {
        "variables": "[{'simbolo':'ME','nombre':'meta','valor':100},{'simbolo':'EJ','nombre':'real','valor':80}]",
        "meta": 120,
    }

    result = ext.extract(row)

    assert result.meta == 100.0
    assert result.ejec == 80.0
    assert result.fuente == "variables_simbolo"


def test_series_sum_extractor_suma_meta_y_resultado():
    ext = SeriesSumExtractor()
    row = {
        "series": "[{'meta': 10, 'resultado': 4}, {'meta': 5, 'resultado': 3}]"
    }

    result = ext.extract(row)

    assert result.meta == 15.0
    assert result.ejec == 7.0
    assert result.fuente == "series_sum"


def test_heuristic_extractor_caso_grande_busca_variables():
    ext = HeuristicExtractor()
    row = {
        "meta": 80,
        "resultado": None,
        "variables": "[{'nombre':'ejecutado','valor':5000},{'nombre':'meta','valor':6000}]",
        "series": "[]",
    }

    result = ext.extract(row, hist_meta_escala=5001)

    assert result.fuente == "variables"
    assert result.ejec == 5000


def test_data_loader_api_consolidated_and_cache(monkeypatch, tmp_path):
    paths = _mk_loader_paths(tmp_path)
    monkeypatch.setattr(dl_module, "get_project_paths", lambda: paths)

    calls = {"n": 0}

    def fake_read_excel(path, *args, **kwargs):
        calls["n"] += 1
        return pd.DataFrame(
            {
                "fecha": ["2026-01-31", "2026-02-28"],
                "ID": [101.0, 102.0],
                "nombre": ["A", "B"],
                "proceso": ["P1", "P2"],
                "frecuencia": ["Mensual", "Mensual"],
                "sentido": ["Positivo", "Positivo"],
                "clasificacion": ["Estrat&eacute;gico", "Operativo"],
            }
        )

    monkeypatch.setattr(dl_module.pd, "read_excel", fake_read_excel)

    loader = DataLoader()
    df1 = loader.load_api_consolidated(use_cache=True)
    df2 = loader.load_api_consolidated(use_cache=True)

    assert calls["n"] == 1
    assert "LLAVE" in df1.columns
    assert "Id" in df1.columns
    assert df2.equals(df1)


def test_data_loader_historical_consolidated_handles_sheet_error(monkeypatch, tmp_path):
    paths = _mk_loader_paths(tmp_path)
    monkeypatch.setattr(dl_module, "get_project_paths", lambda: paths)

    def fake_read_excel(path, *args, **kwargs):
        sheet = kwargs.get("sheet_name")
        if sheet == "Consolidado Cierres":
            raise ValueError("sheet corrupta")
        return pd.DataFrame({"Fecha": ["2026-01-31"], "Id": ["1"]})

    monkeypatch.setattr(dl_module.pd, "read_excel", fake_read_excel)

    loader = DataLoader()
    result = loader.load_historical_consolidated()

    assert set(result.keys()) == {"historico", "semestral", "cierres"}
    assert result["historico"].shape[0] == 1
    assert result["cierres"].empty


def test_data_loader_kawak_valid_ids_and_lmi_metrics(monkeypatch, tmp_path):
    paths = _mk_loader_paths(tmp_path)
    monkeypatch.setattr(dl_module, "get_project_paths", lambda: paths)

    lmi_path = paths["BASE_PATH"] / "lmi_reporte.xlsx"

    def fake_read_excel(path, *args, **kwargs):
        file_name = Path(path).name.lower()
        if file_name == "indicadores kawak.xlsx":
            return pd.DataFrame({"Id": [101.0, "202"], "Año": [2026, 2025]})
        if file_name == "lmi_reporte.xlsx":
            return pd.DataFrame(
                {
                    "Id": ["1", "2", "3"],
                    "Tipo": ["Metrica", "Indicador", "Indicador"],
                    "Indicador": ["X", "MetRica consumo", "Y"],
                }
            )
        raise AssertionError(f"read_excel no esperado para ruta: {path}")

    monkeypatch.setattr(dl_module.pd, "read_excel", fake_read_excel)

    loader = DataLoader()
    loader.paths = paths
    validos = loader.load_kawak_valid_ids()
    metric_ids = loader.load_lmi_metric_ids()

    assert ("101", 2026) in validos
    assert ("202", 2025) in validos
    assert metric_ids == {"1", "2"}


def test_data_loader_api_consolidated_missing_file_raises(monkeypatch, tmp_path):
    paths = _mk_loader_paths(tmp_path)
    paths["CONSOLIDADO_API_KW"].unlink()
    monkeypatch.setattr(dl_module, "get_project_paths", lambda: paths)

    loader = DataLoader()

    try:
        loader.load_api_consolidated()
        assert False, "Se esperaba FileNotFoundError"
    except FileNotFoundError:
        assert True


def test_data_loader_kawak_valid_ids_without_required_columns(monkeypatch, tmp_path):
    paths = _mk_loader_paths(tmp_path)
    monkeypatch.setattr(dl_module, "get_project_paths", lambda: paths)

    def fake_read_excel(path, *args, **kwargs):
        return pd.DataFrame({"Codigo": [1], "Periodo": [2026]})

    monkeypatch.setattr(dl_module.pd, "read_excel", fake_read_excel)

    loader = DataLoader()
    validos = loader.load_kawak_valid_ids()

    assert validos is None


def test_data_loader_lmi_metric_ids_read_error_returns_empty(monkeypatch, tmp_path):
    paths = _mk_loader_paths(tmp_path)
    monkeypatch.setattr(dl_module, "get_project_paths", lambda: paths)

    def fake_read_excel(path, *args, **kwargs):
        raise RuntimeError("fallo lectura")

    monkeypatch.setattr(dl_module.pd, "read_excel", fake_read_excel)

    loader = DataLoader()
    metric_ids = loader.load_lmi_metric_ids()

    assert metric_ids == set()


def test_data_loader_historical_missing_file_raises(monkeypatch, tmp_path):
    paths = _mk_loader_paths(tmp_path)
    paths["INPUT_FILE"].unlink()
    monkeypatch.setattr(dl_module, "get_project_paths", lambda: paths)

    loader = DataLoader()

    try:
        loader.load_historical_consolidated()
        assert False, "Se esperaba FileNotFoundError"
    except FileNotFoundError:
        assert True


def test_data_loader_clear_cache(monkeypatch, tmp_path):
    paths = _mk_loader_paths(tmp_path)
    monkeypatch.setattr(dl_module, "get_project_paths", lambda: paths)

    def fake_read_excel(path, *args, **kwargs):
        return pd.DataFrame(
            {
                "fecha": ["2026-01-31"],
                "ID": [101.0],
                "nombre": ["A"],
                "proceso": ["P1"],
                "frecuencia": ["Mensual"],
                "sentido": ["Positivo"],
            }
        )

    monkeypatch.setattr(dl_module.pd, "read_excel", fake_read_excel)

    loader = DataLoader()
    loader.load_api_consolidated(use_cache=True)
    assert "api_consolidated" in loader._cache

    loader.clear_cache()
    assert loader._cache == {}


def test_data_loader_api_consolidated_drops_invalid_dates(monkeypatch, tmp_path):
    paths = _mk_loader_paths(tmp_path)
    monkeypatch.setattr(dl_module, "get_project_paths", lambda: paths)

    def fake_read_excel(path, *args, **kwargs):
        return pd.DataFrame(
            {
                "fecha": ["2026-01-31", "fecha-invalida", None],
                "ID": [101.0, 102.0, 103.0],
                "nombre": ["A", "B", "C"],
                "proceso": ["P1", "P2", "P3"],
                "frecuencia": ["Mensual", "Mensual", "Mensual"],
                "sentido": ["Positivo", "Positivo", "Positivo"],
            }
        )

    monkeypatch.setattr(dl_module.pd, "read_excel", fake_read_excel)

    loader = DataLoader()
    df = loader.load_api_consolidated(use_cache=False)

    assert len(df) == 1
    assert df["Id"].iloc[0] == "101"


def test_data_loader_api_consolidated_missing_required_columns_raises(monkeypatch, tmp_path):
    paths = _mk_loader_paths(tmp_path)
    monkeypatch.setattr(dl_module, "get_project_paths", lambda: paths)

    def fake_read_excel(path, *args, **kwargs):
        return pd.DataFrame(
            {
                "fecha": ["2026-01-31"],
                "nombre": ["A"],
                "proceso": ["P1"],
            }
        )

    monkeypatch.setattr(dl_module.pd, "read_excel", fake_read_excel)

    loader = DataLoader()

    try:
        loader.load_api_consolidated(use_cache=False)
        assert False, "Se esperaba ValueError por columnas faltantes"
    except ValueError as e:
        assert "Columnas requeridas" in str(e)


def test_data_loader_api_consolidated_accepts_id_column(monkeypatch, tmp_path):
    paths = _mk_loader_paths(tmp_path)
    monkeypatch.setattr(dl_module, "get_project_paths", lambda: paths)

    def fake_read_excel(path, *args, **kwargs):
        return pd.DataFrame(
            {
                "fecha": ["2026-03-31"],
                "Id": ["A-1"],
                "nombre": ["Indicador A"],
                "proceso": ["P"],
                "frecuencia": ["Mensual"],
                "sentido": ["Positivo"],
            }
        )

    monkeypatch.setattr(dl_module.pd, "read_excel", fake_read_excel)

    loader = DataLoader()
    df = loader.load_api_consolidated(use_cache=False)

    assert len(df) == 1
    assert df["Id"].iloc[0] == "A-1"
    assert df["LLAVE"].iloc[0].startswith("A-1-2026-03-31")


def test_data_loader_api_consolidated_normalizes_mixed_ids(monkeypatch, tmp_path):
    paths = _mk_loader_paths(tmp_path)
    monkeypatch.setattr(dl_module, "get_project_paths", lambda: paths)

    def fake_read_excel(path, *args, **kwargs):
        return pd.DataFrame(
            {
                "fecha": ["2026-01-31", "2026-02-28", "2026-03-31", "2026-04-30", "2026-05-31"],
                "ID": [101.0, "A-02", "003.0", None, ""],
                "nombre": ["A", "B", "C", "D", "E"],
                "proceso": ["P1", "P2", "P3", "P4", "P5"],
                "frecuencia": ["Mensual", "Mensual", "Mensual", "Mensual", "Mensual"],
                "sentido": ["Positivo", "Positivo", "Positivo", "Positivo", "Positivo"],
            }
        )

    monkeypatch.setattr(dl_module.pd, "read_excel", fake_read_excel)

    loader = DataLoader()
    df = loader.load_api_consolidated(use_cache=False)

    assert df["Id"].tolist() == ["101", "A-02", "003"]
    assert all(k.count("-") >= 3 for k in df["LLAVE"].tolist())


def test_data_loader_kawak_2025_missing_required_columns_raises(monkeypatch, tmp_path):
    paths = _mk_loader_paths(tmp_path)
    kawak_2025 = paths["BASE_PATH"] / "Kawak" / "2025.xlsx"
    kawak_2025.write_text("x", encoding="utf-8")
    monkeypatch.setattr(dl_module, "get_project_paths", lambda: paths)

    def fake_read_excel(path, *args, **kwargs):
        return pd.DataFrame({"ID": [1]})

    monkeypatch.setattr(dl_module.pd, "read_excel", fake_read_excel)

    loader = DataLoader()

    try:
        loader.load_kawak_2025()
        assert False, "Se esperaba ValueError por columnas faltantes"
    except ValueError as e:
        assert "Columnas requeridas" in str(e)


def test_data_loader_kawak_2025_normalizes_and_drops_invalid_rows(monkeypatch, tmp_path):
    paths = _mk_loader_paths(tmp_path)
    kawak_2025 = paths["BASE_PATH"] / "Kawak" / "2025.xlsx"
    kawak_2025.write_text("x", encoding="utf-8")
    monkeypatch.setattr(dl_module, "get_project_paths", lambda: paths)

    def fake_read_excel(path, *args, **kwargs):
        return pd.DataFrame(
            {
                "fecha": ["2026-01-31", "bad-date", "2026-03-31"],
                "ID": [100.0, 200.0, ""],
            }
        )

    monkeypatch.setattr(dl_module.pd, "read_excel", fake_read_excel)

    loader = DataLoader()
    df = loader.load_kawak_2025()

    assert len(df) == 1
    assert df["Id"].iloc[0] == "100"
    assert df["LLAVE"].iloc[0].startswith("100-2026-01-31")


def test_data_loader_kawak_2025_missing_file_returns_empty(monkeypatch, tmp_path):
    paths = _mk_loader_paths(tmp_path)
    kawak_2025 = paths["BASE_PATH"] / "Kawak" / "2025.xlsx"
    if kawak_2025.exists():
        kawak_2025.unlink()
    monkeypatch.setattr(dl_module, "get_project_paths", lambda: paths)

    loader = DataLoader()
    df = loader.load_kawak_2025()

    assert isinstance(df, pd.DataFrame)
    assert df.empty
