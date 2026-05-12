from pathlib import Path

import pandas as pd

from scripts.consolidation.core.audit import AuditEngine, TipoArtefacto, TipoOperacion
from scripts.consolidation.core.rules_engine import (
    NivelAlerta,
    Regla,
    RulesEngine,
    TipoRegla,
)


def test_rules_engine_default_rules_loaded():
    engine = RulesEngine()
    reglas = engine.listar_reglas()

    assert len(reglas) >= 5
    assert any(r.id == "semaforizacion" for r in reglas)


def test_rules_engine_semaforizacion_levels():
    engine = RulesEngine()
    regla = engine.obtener_regla("semaforizacion")
    df = pd.DataFrame({"Id": ["A", "B", "C"], "Cumplimiento": [0.6, 0.9, 1.3]})

    resultados = engine.evaluar_semaforizacion(df, regla)
    niveles = [r.nivel for r in resultados]

    assert niveles == [NivelAlerta.CRITICO, NivelAlerta.NORMAL, NivelAlerta.CRITICO]


def test_rules_engine_variacion_abrupta_detecta_alerta():
    engine = RulesEngine()
    regla = engine.obtener_regla("variacion_abrupta")
    df = pd.DataFrame(
        {
            "Id": ["X", "X"],
            "Fecha": ["2026-01-01", "2026-02-01"],
            "Cumplimiento": [0.5, 0.9],
        }
    )

    resultados = engine.evaluar_variacion_abrupta(df, regla)

    assert len(resultados) == 1
    assert resultados[0].nivel in (NivelAlerta.ATENCION, NivelAlerta.CRITICO)


def test_rules_engine_nulos_excesivos_global():
    engine = RulesEngine()
    regla = engine.obtener_regla("nulos_excesivos")
    df = pd.DataFrame({"Ejecucion": [1, None, None, 4]})

    resultados = engine.evaluar_nulos_excesivos(df, regla)

    assert len(resultados) == 1
    assert resultados[0].registro_id == "GLOBAL"


def test_rules_engine_genera_y_exporta_alertas():
    engine = RulesEngine()
    regla = Regla(
        id="custom_test",
        nombre="Custom",
        tipo=TipoRegla.RANGO_CUMPLIMIENTO,
        descripcion="test",
        configuracion={
            "campo": "Cumplimiento",
            "rangos": {
                "critico_low": 0.7,
                "atencion_low": 0.8,
                "normal_low": 0.8,
                "normal_high": 1.05,
                "atencion_high": 1.2,
                "critico_high": 1.2,
            },
        },
    )
    df = pd.DataFrame({"Id": ["A", "B"], "Cumplimiento": [0.5, 0.9]})
    resultados = engine.evaluar_semaforizacion(df, regla)

    alertas = engine.generar_alertas(resultados)
    exported = engine.exportar_alertas("df")

    assert len(alertas) == 1
    assert not exported.empty
    assert set(exported.columns) >= {"nivel", "indicador_id", "mensaje"}


def test_audit_engine_registrar_operacion_crea_log(tmp_path):
    engine = AuditEngine(tmp_path)
    engine.registrar_operacion(
        operacion=TipoOperacion.EXTRACCION,
        detalle="Carga inicial",
        registros_procesados=10,
        registros_exitosos=10,
        metadata={"pipeline_run": "RUN-TEST"},
    )

    assert len(engine.registros) == 1
    logs = list((tmp_path / "audit").glob("audit_*.log"))
    assert len(logs) == 1
    assert "Carga inicial" in logs[0].read_text(encoding="utf-8")


def test_audit_engine_versionar_artefacto_y_metadata(tmp_path):
    engine = AuditEngine(tmp_path)
    csv = tmp_path / "salida.csv"
    pd.DataFrame({"a": [1, 2, 3]}).to_csv(csv, index=False)

    a1 = engine.versionar_artefacto("consolidado", TipoArtefacto.DATASET, csv, pipeline_run="RUN-1")
    a2 = engine.versionar_artefacto("consolidado", TipoArtefacto.DATASET, csv, pipeline_run="RUN-1")

    assert a1.version == "v1.0.0"
    assert a2.version == "v1.0.1"
    metadata_files = list((tmp_path / "versions").glob("consolidado_v*.json"))
    assert len(metadata_files) == 2


def test_audit_engine_finalizar_run_y_resumen(tmp_path):
    engine = AuditEngine(tmp_path)
    run_id = engine.iniciar_pipeline_run()
    engine.registrar_operacion(
        operacion=TipoOperacion.CONSOLIDACION,
        detalle="Paso principal",
        registros_procesados=50,
        registros_exitosos=48,
        registros_fallidos=2,
        metadata={"pipeline_run": run_id},
    )

    run = engine.finalizar_pipeline_run(run_id, estado="PARTIAL", duracion_ms=1200, errores=["warning"])
    reporte = engine.generar_reporte_auditoria()

    assert run.id == run_id
    assert run.resumen["total_operaciones"] >= 1
    assert "REPORTE DE AUDITORÍA" in reporte
