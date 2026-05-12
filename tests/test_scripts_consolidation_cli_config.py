import json
from json import JSONDecodeError
from pathlib import Path
import sys

import scripts.consolidation.cli as cli_module
import scripts.consolidation.core.config_loader as cfg_module


def test_create_parser_defaults_and_flags():
    parser = cli_module.create_parser()
    args = parser.parse_args([])

    assert args.batch_size == 1000
    assert args.verbose == 0
    assert args.quiet is False
    assert args.no_parallel is False


def test_setup_logging_from_args_levels(monkeypatch):
    captured = {"level": None}

    def fake_setup_logging(level, log_file, console):
        captured["level"] = level

    monkeypatch.setattr(cli_module, "setup_logging", fake_setup_logging)
    parser = cli_module.create_parser()

    args = parser.parse_args(["-q"])
    level = cli_module.setup_logging_from_args(args)
    assert level == cli_module.logging.ERROR

    args = parser.parse_args(["-vvv"])
    level = cli_module.setup_logging_from_args(args)
    assert level == cli_module.logging.DEBUG


def test_run_cli_validate_only(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["consolidation", "--validate-only"])
    monkeypatch.setattr(cli_module, "setup_logging_from_args", lambda args: cli_module.logging.INFO)

    code = cli_module.run_cli()
    assert code == 0


def test_run_cli_success_and_report(monkeypatch, tmp_path):
    report = tmp_path / "report.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "consolidation",
            "--report-output",
            str(report),
            "--report-format",
            "json",
            "--filter-ids",
            "1,2",
        ],
    )
    monkeypatch.setattr(cli_module, "setup_logging_from_args", lambda args: cli_module.logging.INFO)

    class _OkOrchestrator:
        def __init__(self, config, workers, batch_size):
            self.config = config
            self.workers = workers
            self.batch_size = batch_size

        def run(self, dry_run, filter_year, filter_ids):
            assert filter_ids == ["1", "2"]
            return {"success": True, "metrics": {"records": 10}}

    monkeypatch.setattr(cli_module, "ConsolidationOrchestrator", _OkOrchestrator)

    code = cli_module.run_cli()
    assert code == 0
    assert report.exists()
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["success"] is True


def test_run_cli_failure(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["consolidation"])
    monkeypatch.setattr(cli_module, "setup_logging_from_args", lambda args: cli_module.logging.INFO)

    class _FailOrchestrator:
        def __init__(self, config, workers, batch_size):
            pass

        def run(self, dry_run, filter_year, filter_ids):
            return {"success": False, "error": "boom"}

    monkeypatch.setattr(cli_module, "ConsolidationOrchestrator", _FailOrchestrator)

    code = cli_module.run_cli()
    assert code == 1


def test_config_loader_load_json_and_merge(tmp_path):
    config_file = tmp_path / "conf.json"
    config_file.write_text(json.dumps({"processing": {"batch_size": 777}, "logging": {"level": "DEBUG"}}), encoding="utf-8")

    loaded = cfg_module.ConfigLoader.load(config_file)
    merged = cfg_module.merge_configs(cfg_module.get_default_config(), loaded)

    assert loaded["processing"]["batch_size"] == 777
    assert merged["processing"]["batch_size"] == 777
    assert merged["logging"]["level"] == "DEBUG"


def test_config_loader_validate_and_save_json(tmp_path):
    input_file = tmp_path / "input.xlsx"
    api_file = tmp_path / "api.xlsx"
    kawak_file = tmp_path / "kawak.xlsx"
    for p in (input_file, api_file, kawak_file):
        p.write_text("x", encoding="utf-8")

    config = {
        "input": {
            "input_file": str(input_file),
            "api_consolidated": str(api_file),
            "kawak_catalog": str(kawak_file),
        },
        "processing": {
            "año_cierre": 2026,
            "batch_size": 1200,
            "use_cache": True,
            "validate_output": True,
        },
        "extractions": {
            "101": {"patron": "LAST"},
            "102": {"patron": "VARIABLES", "simbolo_ejec": "EJ"},
        },
    }

    validated = cfg_module.ConfigLoader.validate(config)
    assert validated["input"].input_file == str(input_file)
    assert validated["processing"].batch_size == 1200
    assert validated["extractions"]["102"].patron == "VARIABLES"

    out_json = tmp_path / "saved.json"
    cfg_module.save_config(config, out_json, format="json")
    assert out_json.exists()


def test_config_loader_errors(tmp_path):
    missing = tmp_path / "missing.json"
    try:
        cfg_module.ConfigLoader.load(missing)
        assert False, "Debió lanzar FileNotFoundError"
    except FileNotFoundError:
        assert True

    bad = tmp_path / "bad.txt"
    bad.write_text("x", encoding="utf-8")
    try:
        cfg_module.ConfigLoader.load(bad)
        assert False, "Debió lanzar ValueError"
    except ValueError:
        assert True


def test_config_loader_load_yaml_empty_returns_dict(tmp_path):
    yml = tmp_path / "empty.yaml"
    yml.write_text("", encoding="utf-8")

    loaded = cfg_module.ConfigLoader.load(yml)
    assert loaded == {}


def test_config_loader_load_yaml_without_pyyaml_raises(monkeypatch, tmp_path):
    yml = tmp_path / "conf.yaml"
    yml.write_text("a: 1", encoding="utf-8")

    monkeypatch.setattr(cfg_module, "HAS_YAML", False)

    try:
        cfg_module.ConfigLoader.load(yml)
        assert False, "Debió lanzar ImportError"
    except ImportError:
        assert True


def test_save_config_yaml_without_pyyaml_raises(monkeypatch, tmp_path):
    out = tmp_path / "saved.yaml"
    monkeypatch.setattr(cfg_module, "HAS_YAML", False)

    try:
        cfg_module.save_config({"a": 1}, out, format="yaml")
        assert False, "Debió lanzar ImportError"
    except ImportError:
        assert True


def test_merge_configs_deep_and_base_immutable():
    base = {
        "processing": {"batch_size": 1000, "validate_output": True},
        "logging": {"level": "INFO", "file": "a.log"},
    }
    override = {
        "processing": {"batch_size": 2000},
        "logging": {"level": "DEBUG"},
    }

    merged = cfg_module.merge_configs(base, override)

    assert merged["processing"]["batch_size"] == 2000
    assert merged["processing"]["validate_output"] is True
    assert merged["logging"]["level"] == "DEBUG"
    assert base["processing"]["batch_size"] == 1000
    assert base["logging"]["level"] == "INFO"


def test_save_config_json_preserves_unicode(tmp_path):
    out = tmp_path / "unicode.json"
    cfg_module.save_config({"texto": "Planeación Estratégica"}, out, format="json")

    content = out.read_text(encoding="utf-8")
    assert "Planeación Estratégica" in content


def test_run_cli_no_parallel_sets_workers_one(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["consolidation", "--no-parallel", "--filter-ids", "1, 2 ,,3"])
    monkeypatch.setattr(cli_module, "setup_logging_from_args", lambda args: cli_module.logging.INFO)

    captured = {"workers": None, "filter_ids": None}

    class _OkOrchestrator:
        def __init__(self, config, workers, batch_size):
            captured["workers"] = workers

        def run(self, dry_run, filter_year, filter_ids):
            captured["filter_ids"] = filter_ids
            return {"success": True, "metrics": {}}

    monkeypatch.setattr(cli_module, "ConsolidationOrchestrator", _OkOrchestrator)

    code = cli_module.run_cli()
    assert code == 0
    assert captured["workers"] == 1
    assert captured["filter_ids"] == ["1", " 2 ", "", "3"]


def test_run_cli_handles_orchestrator_exception(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["consolidation"])
    monkeypatch.setattr(cli_module, "setup_logging_from_args", lambda args: cli_module.logging.INFO)

    class _ExplodesOrchestrator:
        def __init__(self, config, workers, batch_size):
            pass

        def run(self, dry_run, filter_year, filter_ids):
            raise RuntimeError("fatal")

    monkeypatch.setattr(cli_module, "ConsolidationOrchestrator", _ExplodesOrchestrator)

    code = cli_module.run_cli()
    assert code == 1


def test_generate_report_yaml(monkeypatch, tmp_path):
    out = tmp_path / "report.yaml"

    class _YamlStub:
        @staticmethod
        def dump(metrics, stream, allow_unicode=True):
            stream.write("success: true\n")

    monkeypatch.setitem(sys.modules, "yaml", _YamlStub)

    cli_module.generate_report({"success": True, "metrics": {"ok": 1}}, "yaml", str(out))
    assert out.exists()
    assert "success" in out.read_text(encoding="utf-8")


def test_generate_report_json_has_metrics(tmp_path):
    out = tmp_path / "report.json"
    cli_module.generate_report({"success": True, "metrics": {"rows": 123}}, "json", str(out))

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["success"] is True
    assert data["metrics"]["rows"] == 123


def test_generate_report_html_not_implemented_raises(tmp_path):
    out = tmp_path / "report.html"

    try:
        cli_module.generate_report({"success": True, "metrics": {}}, "html", str(out))
        assert False, "Debió lanzar ValueError"
    except ValueError as e:
        assert "no implementado" in str(e)


def test_run_cli_report_html_returns_error_code(monkeypatch, tmp_path):
    report = tmp_path / "report.html"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "consolidation",
            "--report-output",
            str(report),
            "--report-format",
            "html",
        ],
    )
    monkeypatch.setattr(cli_module, "setup_logging_from_args", lambda args: cli_module.logging.INFO)

    class _OkOrchestrator:
        def __init__(self, config, workers, batch_size):
            pass

        def run(self, dry_run, filter_year, filter_ids):
            return {"success": True, "metrics": {"records": 1}}

    monkeypatch.setattr(cli_module, "ConsolidationOrchestrator", _OkOrchestrator)

    code = cli_module.run_cli()
    assert code == 1


def test_generate_report_json_permission_error(monkeypatch, tmp_path):
    out = tmp_path / "blocked.json"

    import builtins

    orig_open = builtins.open

    def _fake_open(path, *args, **kwargs):
        if str(path) == str(out):
            raise PermissionError("denied")
        return orig_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", _fake_open)

    try:
        cli_module.generate_report({"success": True, "metrics": {}}, "json", str(out))
        assert False, "Debió lanzar PermissionError"
    except PermissionError:
        assert True


def test_run_cli_report_output_permission_error_returns_1(monkeypatch, tmp_path):
    report = tmp_path / "report.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "consolidation",
            "--report-output",
            str(report),
            "--report-format",
            "json",
        ],
    )
    monkeypatch.setattr(cli_module, "setup_logging_from_args", lambda args: cli_module.logging.INFO)

    class _OkOrchestrator:
        def __init__(self, config, workers, batch_size):
            pass

        def run(self, dry_run, filter_year, filter_ids):
            return {"success": True, "metrics": {"records": 1}}

    monkeypatch.setattr(cli_module, "ConsolidationOrchestrator", _OkOrchestrator)
    monkeypatch.setattr(cli_module, "generate_report", lambda *args, **kwargs: (_ for _ in ()).throw(PermissionError("denied")))

    code = cli_module.run_cli()
    assert code == 1


def test_config_loader_load_malformed_json_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"processing": ', encoding="utf-8")

    try:
        cfg_module.ConfigLoader.load(bad)
        assert False, "Debió lanzar JSONDecodeError"
    except JSONDecodeError:
        assert True


def test_config_loader_validate_invalid_section_types():
    try:
        cfg_module.ConfigLoader.validate({"input": "no-dict"})
        assert False, "Debió lanzar ValueError para input"
    except ValueError as e:
        assert "input" in str(e)

    try:
        cfg_module.ConfigLoader.validate({"processing": []})
        assert False, "Debió lanzar ValueError para processing"
    except ValueError as e:
        assert "processing" in str(e)

    try:
        cfg_module.ConfigLoader.validate({"extractions": []})
        assert False, "Debió lanzar ValueError para extractions"
    except ValueError as e:
        assert "extractions" in str(e)


def test_get_default_config_returns_deep_copy():
    c1 = cfg_module.get_default_config()
    c2 = cfg_module.get_default_config()

    c1["processing"]["batch_size"] = 9999
    assert c2["processing"]["batch_size"] == 1000
