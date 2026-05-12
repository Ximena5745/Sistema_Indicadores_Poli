import sys
import types

import pandas as pd

from scripts.consolidation.core.metrics import (
    MetricsCollector,
    PerformanceMonitor,
    ProcessingMetrics,
    ProgressReporter,
)
import scripts.consolidation.core.metrics as metrics_module
import scripts.consolidation.core.parallel_processor as pp_module
from scripts.consolidation.core.parallel_processor import BatchProcessor, ParallelProcessor


def test_parallel_processor_small_dataframe_executes_directly():
    proc = ParallelProcessor(max_workers=2)
    proc.chunk_size = 100
    df = pd.DataFrame({"a": [1, 2, 3]})

    result = proc.process_dataframe(df, lambda x: x.assign(a=x["a"] * 2))

    assert list(result["a"]) == [2, 4, 6]


def test_parallel_processor_large_dataframe_uses_executor(monkeypatch):
    proc = ParallelProcessor(max_workers=2)
    proc.chunk_size = 2
    df = pd.DataFrame({"a": [1, 2, 3, 4, 5]})

    class _DummyExecutor:
        def __init__(self, max_workers=None):
            self.max_workers = max_workers

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def map(self, func, chunks):
            return [func(c) for c in chunks]

    monkeypatch.setattr(pp_module, "ProcessPoolExecutor", _DummyExecutor)

    out = proc.process_dataframe(df, lambda c: c.assign(a=c["a"] + 10))
    assert sorted(out["a"].tolist()) == [11, 12, 13, 14, 15]


def test_parallel_apply_with_fake_joblib(monkeypatch):
    proc = ParallelProcessor(max_workers=2)
    df = pd.DataFrame({"a": [1, 2, 3]})

    class _Parallel:
        def __init__(self, n_jobs):
            self.n_jobs = n_jobs

        def __call__(self, tasks):
            return [task() for task in tasks]

    def _delayed(fn):
        return lambda *args, **kwargs: (lambda: fn(*args, **kwargs))

    fake_joblib = types.SimpleNamespace(Parallel=_Parallel, delayed=_delayed)
    monkeypatch.setitem(sys.modules, "joblib", fake_joblib)

    s = proc.parallel_apply(df, lambda r: r["a"] * 3, axis=1)
    assert s.tolist() == [3, 6, 9]


def test_parallel_file_read_filters_errors(monkeypatch):
    proc = ParallelProcessor(max_workers=2)

    def fake_read_excel(path):
        if path.endswith("ok.xlsx"):
            return pd.DataFrame({"x": [1]})
        raise ValueError("boom")

    monkeypatch.setattr(pp_module.pd, "read_excel", fake_read_excel)

    out = proc.parallel_file_read(["ok.xlsx", "bad.xlsx"])
    assert "ok.xlsx" in out and "bad.xlsx" not in out


def test_batch_processor_with_progress_and_errors(monkeypatch):
    class _Tqdm:
        def __init__(self, items, **kwargs):
            self._items = items

        def __iter__(self):
            return iter(self._items)

    fake_tqdm_module = types.SimpleNamespace(tqdm=lambda items, **kwargs: _Tqdm(items, **kwargs))
    monkeypatch.setitem(sys.modules, "tqdm", fake_tqdm_module)

    bp = BatchProcessor(batch_size=2, show_progress=True)

    def process_item(x):
        if x == 2:
            raise ValueError("x")
        return x * 2

    out = bp.process_with_progress([1, 2, 3], process_item)
    assert out == [2, None, 6]


def test_batch_processor_process_batches_continues_on_error():
    bp = BatchProcessor(batch_size=2, show_progress=False)
    df = pd.DataFrame({"a": [1, 2, 3, 4]})

    def f(batch):
        if 3 in batch["a"].values:
            raise ValueError("fail")
        return batch.assign(a=batch["a"] * 10)

    out = bp.process_batches(df, f)
    assert out["a"].tolist() == [10, 20]


def test_processing_metrics_finalize_and_dict():
    m = ProcessingMetrics(total_records=10)
    m.record_processed(source="api", extractor="LAST")
    m.na_records = 2
    m.record_error("id-1", "boom")
    m.finalize()

    d = m.to_dict()
    assert d["counts"]["processed"] == 1
    assert d["counts"]["errors"] == 1
    assert d["by_source"]["api"] == 1


def test_metrics_collector_report_and_summary(tmp_path):
    c = MetricsCollector()
    c.start_phase("fase_a")
    cur = c.get_current()
    cur.total_records = 5
    cur.record_processed(source="api", extractor="x")
    c.end_phase("fase_a")

    report_path = tmp_path / "report.json"
    rep = c.generate_report(report_path)

    assert "fase_a" in rep["phases"]
    assert report_path.exists()


def test_progress_reporter_update_and_finish(monkeypatch):
    logs = []
    monkeypatch.setattr(metrics_module.logger, "info", lambda msg: logs.append(msg))

    p = ProgressReporter(total=3, description="Test")
    p.update_interval = 0
    p.update()
    p.update(2)
    p.finish()

    assert any("Test" in x for x in logs)


def test_performance_monitor_checkpoint(monkeypatch):
    class _VM:
        percent = 12.5

    class _MemInfo:
        rss = 10 * 1024 * 1024

    class _Proc:
        def memory_info(self):
            return _MemInfo()

    fake_psutil = types.SimpleNamespace(
        cpu_percent=lambda: 20.0,
        virtual_memory=lambda: _VM(),
        Process=lambda: _Proc(),
    )
    monkeypatch.setitem(sys.modules, "psutil", fake_psutil)

    m = PerformanceMonitor()
    m.checkpoint("start")
    r = m.report()

    assert len(r["checkpoints"]) == 1
    assert r["peak_memory_mb"] > 0


def test_processing_metrics_truncates_errors_and_success_rate_zero_total():
    m = ProcessingMetrics(total_records=0)
    for i in range(12):
        m.record_error(f"id-{i}", "err")

    d = m.to_dict()
    assert d["performance"]["success_rate"] == 100.0
    assert len(d["errors"]) == 10


def test_metrics_collector_multi_phase_summary_and_report_without_path():
    c = MetricsCollector()

    c.start_phase("fase_1")
    m1 = c.get_current()
    m1.total_records = 10
    m1.processed_records = 8
    m1.error_records = 2
    c.end_phase("fase_1")

    c.start_phase("fase_2")
    m2 = c.get_current()
    m2.total_records = 5
    m2.processed_records = 5
    c.end_phase("fase_2")

    rep = c.generate_report()
    summary = rep["summary"]

    assert set(rep["phases"].keys()) == {"fase_1", "fase_2"}
    assert summary["total_records"] == 15
    assert summary["total_processed"] == 13
    assert summary["total_errors"] == 2


def test_progress_reporter_finish_handles_near_zero_elapsed(monkeypatch):
    times = iter([100.0, 100.0])
    monkeypatch.setattr(metrics_module.time, "time", lambda: next(times))
    monkeypatch.setattr(metrics_module.logger, "info", lambda msg: None)

    p = ProgressReporter(total=1, description="Fast")
    p.current = 1
    p.finish()
