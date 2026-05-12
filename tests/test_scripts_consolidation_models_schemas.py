from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from scripts.consolidation.models.schemas import (
    ConsolidationMetrics,
    ExtractionConfig,
    InputConfig,
    OutputSummary,
    ProcessedRecord,
    ProcessingConfig,
    SourceRow,
)


def test_input_config_valido_con_archivos_existentes(tmp_path):
    input_file = tmp_path / "input.xlsx"
    api_file = tmp_path / "api.xlsx"
    kawak_file = tmp_path / "kawak.xlsx"
    for p in [input_file, api_file, kawak_file]:
        p.write_text("x", encoding="utf-8")

    cfg = InputConfig(
        input_file=str(input_file),
        api_consolidated=str(api_file),
        kawak_catalog=str(kawak_file),
    )

    assert cfg.input_file == str(input_file)


def test_input_config_invalido_si_no_existe_archivo(tmp_path):
    input_file = tmp_path / "input.xlsx"
    input_file.write_text("x", encoding="utf-8")

    with pytest.raises(ValidationError):
        InputConfig(
            input_file=str(input_file),
            api_consolidated=str(tmp_path / "missing_api.xlsx"),
            kawak_catalog=str(tmp_path / "missing_kawak.xlsx"),
        )


def test_extraction_config_patron_valido_e_invalido():
    ok = ExtractionConfig(id="101", patron="LAST", extra_custom="x")
    assert ok.id == "101"
    assert ok.model_extra.get("extra_custom") == "x"

    with pytest.raises(ValidationError):
        ExtractionConfig(id="101", patron="INVALID")


def test_processing_config_limites_validos_e_invalidos():
    cfg = ProcessingConfig(año_cierre=2026, batch_size=500, max_workers=4)
    assert cfg.año_cierre == 2026

    with pytest.raises(ValidationError):
        ProcessingConfig(año_cierre=2035)

    with pytest.raises(ValidationError):
        ProcessingConfig(batch_size=50)


def test_source_row_validaciones_basicas():
    row = SourceRow(
        Id="X1",
        Periodicidad="Mensual",
        Sentido="Positivo",
        fecha=datetime(2026, 5, 12),
        resultado=10.0,
    )
    assert row.Id == "X1"

    with pytest.raises(ValidationError):
        SourceRow(
            Id="X2",
            fecha=datetime(2026, 5, 12),
            Sentido="Mixto",
        )


def test_processed_record_fuente_y_cumplimiento():
    rec = ProcessedRecord(
        Id="ID1",
        Fecha=datetime(2026, 5, 12),
        Meta=10,
        Ejecucion=9,
        Cumplimiento=0.9,
        LLAVE="ID1-2026-05-12",
        fuente="api_directo",
    )
    assert rec.Cumplimiento == 0.9

    with pytest.raises(ValidationError):
        ProcessedRecord(
            Id="ID2",
            Fecha=datetime(2026, 5, 12),
            LLAVE="ID2-2026-05-12",
            Cumplimiento=1.5,
            fuente="api_directo",
        )

    with pytest.raises(ValidationError):
        ProcessedRecord(
            Id="ID3",
            Fecha=datetime(2026, 5, 12),
            LLAVE="ID3-2026-05-12",
            Cumplimiento=1.0,
            fuente="otra_fuente",
        )


def test_consolidation_metrics_calculate_duration():
    start = datetime(2026, 5, 12, 10, 0, 0)
    end = start + timedelta(seconds=12.5)

    m = ConsolidationMetrics(start_time=start, end_time=end)
    m.calculate_duration()

    assert m.duration_seconds == 12.5


def test_output_summary_defaults_y_datos():
    s = OutputSummary(output_file="data/output/Resultados Consolidados.xlsx")
    assert s.sheets_created == []
    assert s.records_by_sheet == {}

    s2 = OutputSummary(
        output_file="out.xlsx",
        sheets_created=["Historico", "Cierres"],
        records_by_sheet={"Historico": 10, "Cierres": 2},
        file_size_bytes=1234,
        checksum="abc",
    )
    assert s2.records_by_sheet["Historico"] == 10
