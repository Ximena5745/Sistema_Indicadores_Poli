from pathlib import Path
import sys
import types

import pandas as pd

import scripts.consolidation as consolidation_pkg

sys.modules.setdefault("consolidation", consolidation_pkg)

import scripts.consolidation.main as main_module
import scripts.consolidation.pipeline.orchestrator as orch_module


class _DummyLoader:
    def __init__(self, sources):
        self._sources = sources

    def load_api_consolidated(self):
        return self._sources["api_consolidated"]

    def load_kawak_2025(self):
        return self._sources["kawak_2025"]

    def load_historical_consolidated(self):
        return self._sources["historical"]

    def load_kawak_valid_ids(self):
        return self._sources["kawak_valid_ids"]

    def load_lmi_metric_ids(self):
        return self._sources["lmi_metric_ids"]


def test_validate_prerequisites_ok(monkeypatch, tmp_path):
    api = tmp_path / "api.xlsx"
    inp = tmp_path / "in.xlsx"
    out = tmp_path / "out.xlsx"
    api.write_text("x", encoding="utf-8")
    inp.write_text("x", encoding="utf-8")

    monkeypatch.setattr(
        orch_module,
        "get_project_paths",
        lambda: {
            "CONSOLIDADO_API_KW": api,
            "INPUT_FILE": inp,
            "OUTPUT_FILE": out,
        },
    )
    monkeypatch.setattr(orch_module, "DataLoader", lambda: _DummyLoader({
        "api_consolidated": pd.DataFrame(),
        "kawak_2025": pd.DataFrame(),
        "historical": {},
        "kawak_valid_ids": None,
        "lmi_metric_ids": set(),
    }))

    orch = orch_module.ConsolidationOrchestrator()
    orch._validate_prerequisites()


def test_validate_prerequisites_error(monkeypatch, tmp_path):
    api = tmp_path / "api_missing.xlsx"
    inp = tmp_path / "in_missing.xlsx"
    out = tmp_path / "out.xlsx"

    monkeypatch.setattr(
        orch_module,
        "get_project_paths",
        lambda: {
            "CONSOLIDADO_API_KW": api,
            "INPUT_FILE": inp,
            "OUTPUT_FILE": out,
        },
    )
    monkeypatch.setattr(orch_module, "DataLoader", lambda: _DummyLoader({
        "api_consolidated": pd.DataFrame(),
        "kawak_2025": pd.DataFrame(),
        "historical": {},
        "kawak_valid_ids": None,
        "lmi_metric_ids": set(),
    }))

    orch = orch_module.ConsolidationOrchestrator()
    try:
        orch._validate_prerequisites()
        assert False, "Se esperaba ValidationError"
    except orch_module.ValidationError:
        assert True


def test_process_data_counts_na_skip_processed(monkeypatch, tmp_path):
    api = tmp_path / "api.xlsx"
    inp = tmp_path / "in.xlsx"
    out = tmp_path / "out.xlsx"
    api.write_text("x", encoding="utf-8")
    inp.write_text("x", encoding="utf-8")

    monkeypatch.setattr(
        orch_module,
        "get_project_paths",
        lambda: {
            "CONSOLIDADO_API_KW": api,
            "INPUT_FILE": inp,
            "OUTPUT_FILE": out,
        },
    )
    monkeypatch.setattr(orch_module, "DataLoader", lambda: _DummyLoader({
        "api_consolidated": pd.DataFrame(),
        "kawak_2025": pd.DataFrame(),
        "historical": {},
        "kawak_valid_ids": None,
        "lmi_metric_ids": set(),
    }))

    class _R:
        def __init__(self, fuente):
            self.meta = 10
            self.ejec = 8
            self.fuente = fuente
            self.es_na = False

    class _E:
        def __init__(self, fuente):
            self._fuente = fuente

        def extract(self, row):
            return _R(self._fuente)

    def fake_create_from_config(config):
        return _E("skip" if config.get("patron") == "SKIP" else "api_directo")

    def fake_es_registro_na(row):
        return str(row.get("Id")) == "NA"

    monkeypatch.setattr(orch_module.ExtractorFactory, "create_from_config", staticmethod(fake_create_from_config))
    monkeypatch.setattr(orch_module.ConsolidationOrchestrator, "_load_extraction_configs", lambda self: {"SK": {"patron": "SKIP"}})
    monkeypatch.setattr("scripts.consolidation.core.utils.es_registro_na", fake_es_registro_na)

    orch = orch_module.ConsolidationOrchestrator()
    df_api = pd.DataFrame(
        {
            "Id": ["NA", "SK", "OK"],
            "fecha": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"]),
            "LLAVE": ["a", "b", "c"],
            "Periodicidad": ["Mensual", "Mensual", "Mensual"],
        }
    )

    processed = orch._process_data({"api_consolidated": df_api})

    assert processed["na_count"] == 1
    assert processed["skip_count"] == 1
    assert len(processed["historico"]) == 1
    assert orch.metrics["records_processed"] == 1


def test_run_success_and_failure(monkeypatch, tmp_path):
    api = tmp_path / "api.xlsx"
    inp = tmp_path / "in.xlsx"
    out = tmp_path / "out.xlsx"
    api.write_text("x", encoding="utf-8")
    inp.write_text("x", encoding="utf-8")

    monkeypatch.setattr(
        orch_module,
        "get_project_paths",
        lambda: {
            "CONSOLIDADO_API_KW": api,
            "INPUT_FILE": inp,
            "OUTPUT_FILE": out,
        },
    )
    monkeypatch.setattr(orch_module, "DataLoader", lambda: _DummyLoader({
        "api_consolidated": pd.DataFrame(),
        "kawak_2025": pd.DataFrame(),
        "historical": {},
        "kawak_valid_ids": None,
        "lmi_metric_ids": set(),
    }))

    orch = orch_module.ConsolidationOrchestrator()
    monkeypatch.setattr(orch, "_validate_prerequisites", lambda: None)
    monkeypatch.setattr(orch, "_load_sources", lambda: {"api_consolidated": pd.DataFrame()})
    monkeypatch.setattr(orch, "_process_data", lambda s: {"historico": []})
    monkeypatch.setattr(orch, "_generate_output", lambda p: None)

    ok = orch.run()
    assert ok["success"] is True
    assert ok["output_file"] == out

    orch2 = orch_module.ConsolidationOrchestrator()
    monkeypatch.setattr(orch2, "_validate_prerequisites", lambda: (_ for _ in ()).throw(ValueError("boom")))
    fail = orch2.run()
    assert fail["success"] is False
    assert "boom" in fail["error"]


def test_load_extraction_configs_ok_and_fallback(monkeypatch, tmp_path):
    api = tmp_path / "api.xlsx"
    inp = tmp_path / "in.xlsx"
    out = tmp_path / "out.xlsx"
    api.write_text("x", encoding="utf-8")
    inp.write_text("x", encoding="utf-8")

    monkeypatch.setattr(
        orch_module,
        "get_project_paths",
        lambda: {
            "CONSOLIDADO_API_KW": api,
            "INPUT_FILE": inp,
            "OUTPUT_FILE": out,
        },
    )
    monkeypatch.setattr(orch_module, "DataLoader", lambda: _DummyLoader({
        "api_consolidated": pd.DataFrame(),
        "kawak_2025": pd.DataFrame(),
        "historical": {},
        "kawak_valid_ids": None,
        "lmi_metric_ids": set(),
    }))

    orch = orch_module.ConsolidationOrchestrator()

    fake_mod = types.SimpleNamespace(cargar_config_patrones=lambda: {"1": {"patron": "LAST"}})
    monkeypatch.setitem(sys.modules, "actualizar_consolidado", fake_mod)
    cfg = orch._load_extraction_configs()
    assert cfg["1"]["patron"] == "LAST"

    monkeypatch.delitem(sys.modules, "actualizar_consolidado", raising=False)

    import builtins

    orig_import = builtins.__import__

    def _fake_import(name, *args, **kwargs):
        if name == "actualizar_consolidado":
            raise ImportError("missing")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    cfg2 = orch._load_extraction_configs()
    assert cfg2 == {}


def test_run_failure_when_generate_output_fails(monkeypatch, tmp_path):
    api = tmp_path / "api.xlsx"
    inp = tmp_path / "in.xlsx"
    out = tmp_path / "out.xlsx"
    api.write_text("x", encoding="utf-8")
    inp.write_text("x", encoding="utf-8")

    monkeypatch.setattr(
        orch_module,
        "get_project_paths",
        lambda: {
            "CONSOLIDADO_API_KW": api,
            "INPUT_FILE": inp,
            "OUTPUT_FILE": out,
        },
    )
    monkeypatch.setattr(orch_module, "DataLoader", lambda: _DummyLoader({
        "api_consolidated": pd.DataFrame(),
        "kawak_2025": pd.DataFrame(),
        "historical": {},
        "kawak_valid_ids": None,
        "lmi_metric_ids": set(),
    }))

    orch = orch_module.ConsolidationOrchestrator()
    monkeypatch.setattr(orch, "_validate_prerequisites", lambda: None)
    monkeypatch.setattr(orch, "_load_sources", lambda: {"api_consolidated": pd.DataFrame()})
    monkeypatch.setattr(orch, "_process_data", lambda s: {"historico": []})
    monkeypatch.setattr(orch, "_generate_output", lambda p: (_ for _ in ()).throw(RuntimeError("disk full")))

    out_run = orch.run()

    assert out_run["success"] is False
    assert "disk full" in out_run["error"]


def test_process_data_accepts_missing_periodicidad(monkeypatch, tmp_path):
    api = tmp_path / "api.xlsx"
    inp = tmp_path / "in.xlsx"
    out = tmp_path / "out.xlsx"
    api.write_text("x", encoding="utf-8")
    inp.write_text("x", encoding="utf-8")

    monkeypatch.setattr(
        orch_module,
        "get_project_paths",
        lambda: {
            "CONSOLIDADO_API_KW": api,
            "INPUT_FILE": inp,
            "OUTPUT_FILE": out,
        },
    )
    monkeypatch.setattr(orch_module, "DataLoader", lambda: _DummyLoader({
        "api_consolidated": pd.DataFrame(),
        "kawak_2025": pd.DataFrame(),
        "historical": {},
        "kawak_valid_ids": None,
        "lmi_metric_ids": set(),
    }))

    class _R:
        def __init__(self):
            self.meta = 1
            self.ejec = 1
            self.fuente = "api_directo"
            self.es_na = False

    class _E:
        def extract(self, row):
            return _R()

    monkeypatch.setattr(orch_module.ExtractorFactory, "create_from_config", staticmethod(lambda cfg: _E()))
    monkeypatch.setattr(orch_module.ConsolidationOrchestrator, "_load_extraction_configs", lambda self: {})
    monkeypatch.setattr("scripts.consolidation.core.utils.es_registro_na", lambda row: False)

    orch = orch_module.ConsolidationOrchestrator()
    df_api = pd.DataFrame(
        {
            "Id": ["OK"],
            "fecha": pd.to_datetime(["2026-01-03"]),
            "LLAVE": ["ok-1"],
        }
    )

    processed = orch._process_data({"api_consolidated": df_api})

    assert len(processed["historico"]) == 1
    assert orch.metrics["records_processed"] == 1


def test_run_failure_with_incomplete_api_columns(monkeypatch, tmp_path):
    api = tmp_path / "api.xlsx"
    inp = tmp_path / "in.xlsx"
    out = tmp_path / "out.xlsx"
    api.write_text("x", encoding="utf-8")
    inp.write_text("x", encoding="utf-8")

    monkeypatch.setattr(
        orch_module,
        "get_project_paths",
        lambda: {
            "CONSOLIDADO_API_KW": api,
            "INPUT_FILE": inp,
            "OUTPUT_FILE": out,
        },
    )
    monkeypatch.setattr(orch_module, "DataLoader", lambda: _DummyLoader({
        "api_consolidated": pd.DataFrame(),
        "kawak_2025": pd.DataFrame(),
        "historical": {},
        "kawak_valid_ids": None,
        "lmi_metric_ids": set(),
    }))

    orch = orch_module.ConsolidationOrchestrator()
    monkeypatch.setattr(orch, "_validate_prerequisites", lambda: None)
    monkeypatch.setattr(orch, "_load_sources", lambda: {
        "api_consolidated": pd.DataFrame({"fecha": pd.to_datetime(["2026-01-01"]), "LLAVE": ["x"]})
    })
    monkeypatch.setattr(orch_module.ConsolidationOrchestrator, "_load_extraction_configs", lambda self: {})
    monkeypatch.setattr("scripts.consolidation.core.utils.es_registro_na", lambda row: False)

    class _R:
        def __init__(self):
            self.meta = 1
            self.ejec = 1
            self.fuente = "api_directo"
            self.es_na = False

    class _E:
        def extract(self, row):
            return _R()

    monkeypatch.setattr(orch_module.ExtractorFactory, "create_from_config", staticmethod(lambda cfg: _E()))

    result = orch.run()

    assert result["success"] is False
    assert "Id" in result["error"]


def test_load_sources_calls_loader_methods(monkeypatch, tmp_path):
    api = tmp_path / "api.xlsx"
    inp = tmp_path / "in.xlsx"
    out = tmp_path / "out.xlsx"
    api.write_text("x", encoding="utf-8")
    inp.write_text("x", encoding="utf-8")

    monkeypatch.setattr(
        orch_module,
        "get_project_paths",
        lambda: {
            "CONSOLIDADO_API_KW": api,
            "INPUT_FILE": inp,
            "OUTPUT_FILE": out,
        },
    )

    sources = {
        "api_consolidated": pd.DataFrame({"Id": ["1"], "fecha": pd.to_datetime(["2026-01-01"]), "LLAVE": ["1-a"]}),
        "kawak_2025": pd.DataFrame(),
        "historical": {"historico": pd.DataFrame()},
        "kawak_valid_ids": {("1", 2026)},
        "lmi_metric_ids": {"1"},
    }
    monkeypatch.setattr(orch_module, "DataLoader", lambda: _DummyLoader(sources))

    orch = orch_module.ConsolidationOrchestrator()
    loaded = orch._load_sources()

    assert set(loaded.keys()) == {
        "api_consolidated",
        "kawak_2025",
        "historical",
        "kawak_valid_ids",
        "lmi_metric_ids",
    }
    assert "1" in loaded["lmi_metric_ids"]


def test_generate_output_copies_input_file(monkeypatch, tmp_path):
    api = tmp_path / "api.xlsx"
    inp = tmp_path / "in.xlsx"
    out = tmp_path / "out.xlsx"
    api.write_text("x", encoding="utf-8")
    inp.write_text("contenido-base", encoding="utf-8")

    monkeypatch.setattr(
        orch_module,
        "get_project_paths",
        lambda: {
            "CONSOLIDADO_API_KW": api,
            "INPUT_FILE": inp,
            "OUTPUT_FILE": out,
        },
    )
    monkeypatch.setattr(orch_module, "DataLoader", lambda: _DummyLoader({
        "api_consolidated": pd.DataFrame(),
        "kawak_2025": pd.DataFrame(),
        "historical": {},
        "kawak_valid_ids": None,
        "lmi_metric_ids": set(),
    }))

    orch = orch_module.ConsolidationOrchestrator()
    orch._generate_output({"historico": []})

    assert out.exists()
    assert out.read_text(encoding="utf-8") == "contenido-base"


def test_run_failure_with_invalid_api_source_type(monkeypatch, tmp_path):
    api = tmp_path / "api.xlsx"
    inp = tmp_path / "in.xlsx"
    out = tmp_path / "out.xlsx"
    api.write_text("x", encoding="utf-8")
    inp.write_text("x", encoding="utf-8")

    monkeypatch.setattr(
        orch_module,
        "get_project_paths",
        lambda: {
            "CONSOLIDADO_API_KW": api,
            "INPUT_FILE": inp,
            "OUTPUT_FILE": out,
        },
    )
    monkeypatch.setattr(orch_module, "DataLoader", lambda: _DummyLoader({
        "api_consolidated": pd.DataFrame(),
        "kawak_2025": pd.DataFrame(),
        "historical": {},
        "kawak_valid_ids": None,
        "lmi_metric_ids": set(),
    }))

    orch = orch_module.ConsolidationOrchestrator()
    monkeypatch.setattr(orch, "_validate_prerequisites", lambda: None)
    monkeypatch.setattr(orch, "_load_sources", lambda: {"api_consolidated": [1, 2, 3]})

    result = orch.run()

    assert result["success"] is False
    assert "DataFrame" in result["error"]


def test_process_data_empty_dataframe_returns_zero_metrics(monkeypatch, tmp_path):
    api = tmp_path / "api.xlsx"
    inp = tmp_path / "in.xlsx"
    out = tmp_path / "out.xlsx"
    api.write_text("x", encoding="utf-8")
    inp.write_text("x", encoding="utf-8")

    monkeypatch.setattr(
        orch_module,
        "get_project_paths",
        lambda: {
            "CONSOLIDADO_API_KW": api,
            "INPUT_FILE": inp,
            "OUTPUT_FILE": out,
        },
    )
    monkeypatch.setattr(orch_module, "DataLoader", lambda: _DummyLoader({
        "api_consolidated": pd.DataFrame(),
        "kawak_2025": pd.DataFrame(),
        "historical": {},
        "kawak_valid_ids": None,
        "lmi_metric_ids": set(),
    }))

    orch = orch_module.ConsolidationOrchestrator()
    processed = orch._process_data({"api_consolidated": pd.DataFrame()})

    assert processed["historico"] == []
    assert orch.metrics["records_processed"] == 0
    assert orch.metrics["records_na"] == 0
    assert orch.metrics["records_skipped"] == 0


def test_run_success_with_empty_api_dataframe(monkeypatch, tmp_path):
    api = tmp_path / "api.xlsx"
    inp = tmp_path / "in.xlsx"
    out = tmp_path / "out.xlsx"
    api.write_text("x", encoding="utf-8")
    inp.write_text("base", encoding="utf-8")

    monkeypatch.setattr(
        orch_module,
        "get_project_paths",
        lambda: {
            "CONSOLIDADO_API_KW": api,
            "INPUT_FILE": inp,
            "OUTPUT_FILE": out,
        },
    )
    monkeypatch.setattr(orch_module, "DataLoader", lambda: _DummyLoader({
        "api_consolidated": pd.DataFrame(),
        "kawak_2025": pd.DataFrame(),
        "historical": {},
        "kawak_valid_ids": None,
        "lmi_metric_ids": set(),
    }))

    orch = orch_module.ConsolidationOrchestrator()
    monkeypatch.setattr(orch, "_validate_prerequisites", lambda: None)
    monkeypatch.setattr(orch, "_load_sources", lambda: {"api_consolidated": pd.DataFrame()})

    result = orch.run()

    assert result["success"] is True
    assert result["metrics"]["records_processed"] == 0


def test_main_returns_0_on_success(monkeypatch):
    calls = {"setup": 0}

    class _OkOrchestrator:
        def run(self):
            return {"success": True}

    monkeypatch.setattr(main_module, "setup_logging", lambda **kwargs: calls.__setitem__("setup", calls["setup"] + 1))
    monkeypatch.setattr(main_module, "ConsolidationOrchestrator", _OkOrchestrator)

    code = main_module.main()
    assert code == 0
    assert calls["setup"] == 1


def test_main_returns_1_on_failure(monkeypatch):
    class _FailOrchestrator:
        def run(self):
            return {"success": False, "error": "x"}

    monkeypatch.setattr(main_module, "setup_logging", lambda **kwargs: None)
    monkeypatch.setattr(main_module, "ConsolidationOrchestrator", _FailOrchestrator)

    code = main_module.main()
    assert code == 1
