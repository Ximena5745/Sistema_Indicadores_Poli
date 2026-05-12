from pathlib import Path

import pandas as pd

import services.loaders.pipeline as pipeline


def test_fase1_leer_consolidado_semestral_normaliza_ids(monkeypatch):
    monkeypatch.setattr(
        pipeline.pd,
        "read_excel",
        lambda *args, **kwargs: pd.DataFrame({"Id": [101.0, " 202 "], "Valor": [1, 2]}),
    )
    monkeypatch.setattr(pipeline, "renombrar_columnas", lambda df, _: df)
    monkeypatch.setattr(pipeline, "obtener_rename_map", lambda: {})
    monkeypatch.setattr(pipeline, "id_a_str", lambda x: str(int(float(str(x).strip()))) if str(x).strip() else "")

    result = pipeline.fase1_leer_consolidado_semestral(Path("dummy.xlsx"))

    assert list(result["Id"]) == ["101", "202"]


def test_fase2_enriquecer_clasificacion_noop_si_ya_existe():
    df = pd.DataFrame({"Id": ["1"], "Clasificacion": ["X"]})

    result = pipeline.fase2_enriquecer_clasificacion(df, Path("dummy.xlsx"))

    assert result.equals(df)


def test_fase2_enriquecer_clasificacion_hace_merge(monkeypatch):
    df = pd.DataFrame({"Id": ["1", "2"]})
    cat = pd.DataFrame({"Id": ["1", "2"], "Clasificacion": ["A", "B"]})

    monkeypatch.setattr(pipeline.pd, "read_excel", lambda *args, **kwargs: cat)
    monkeypatch.setattr(pipeline, "id_a_str", lambda x: str(x))

    result = pipeline.fase2_enriquecer_clasificacion(df, Path("dummy.xlsx"))

    assert "Clasificacion" in result.columns
    assert set(result["Clasificacion"].dropna()) == {"A", "B"}


def test_fase4_reconstruir_columnas_formula_desde_fecha():
    df = pd.DataFrame(
        {
            "Fecha": ["2026-01-15", "2026-07-01"],
            "Año": [None, None],
            "Mes": ["", ""],
            "Periodo": ["", ""],
        }
    )

    result = pipeline.fase4_reconstruir_columnas_formula(df)

    assert list(result["Año"].astype(int)) == [2026, 2026]
    assert list(result["Mes"]) == ["Enero", "Julio"]
    assert list(result["Periodo"]) == ["2026-1", "2026-2"]


def test_fase5_aplicar_calculos_cumplimiento_metrica_y_no_aplica(monkeypatch):
    df = pd.DataFrame(
        {
            "Id": ["1", "2", "3"],
            "Cumplimiento": [0.9, 0.8, 1.1],
            "TipoRegistro": ["metrica", "normal", "no aplica"],
            "Meta": [10, 0, 20],
        }
    )

    monkeypatch.setattr(pipeline, "normalizar_cumplimiento", lambda v: float(v))
    monkeypatch.setattr(
        pipeline,
        "categorizar_cumplimiento",
        lambda cumplimiento, id_indicador=None: "Sin dato" if pd.isna(cumplimiento) else "Cumplimiento",
    )

    result = pipeline.fase5_aplicar_calculos_cumplimiento(df)

    assert pd.isna(result.loc[0, "Cumplimiento_norm"])
    assert pd.isna(result.loc[1, "Cumplimiento_norm"])
    assert pd.isna(result.loc[2, "Cumplimiento_norm"])
    assert set(result["Categoria"]) == {"Sin dato"}


def test_fase5_aplicar_calculos_cumplimiento_asigna_anio_desde_fecha(monkeypatch):
    df = pd.DataFrame(
        {
            "Id": ["1"],
            "Cumplimiento": [1.0],
            "Meta": [100],
            "Fecha": ["2025-12-31"],
            "Anio": [None],
        }
    )

    monkeypatch.setattr(pipeline, "normalizar_cumplimiento", lambda v: float(v))
    monkeypatch.setattr(pipeline, "categorizar_cumplimiento", lambda cumplimiento, id_indicador=None: "Cumplimiento")

    result = pipeline.fase5_aplicar_calculos_cumplimiento(df)

    assert int(result.loc[0, "Anio"]) == 2025
    assert result.loc[0, "Categoria"] == "Cumplimiento"


def test_ejecutar_pipeline_completo_orquesta_fases(monkeypatch):
    calls = []
    base = pd.DataFrame({"Id": ["1"]})

    monkeypatch.setattr(
        pipeline,
        "fase1_leer_consolidado_semestral",
        lambda path: calls.append("f1s") or base.copy(),
    )
    monkeypatch.setattr(
        pipeline,
        "fase1_leer_consolidado_historico",
        lambda path: calls.append("f1h") or base.copy(),
    )
    monkeypatch.setattr(
        pipeline,
        "fase2_enriquecer_clasificacion",
        lambda df, path: calls.append("f2") or df,
    )
    monkeypatch.setattr(
        pipeline,
        "fase3_enriquecer_cmi_y_procesos",
        lambda df: calls.append("f3") or df,
    )
    monkeypatch.setattr(
        pipeline,
        "fase4_reconstruir_columnas_formula",
        lambda df: calls.append("f4") or df,
    )
    monkeypatch.setattr(
        pipeline,
        "fase5_aplicar_calculos_cumplimiento",
        lambda df: calls.append("f5") or df,
    )

    pipeline.ejecutar_pipeline_completo(Path("dummy.xlsx"), es_historico=False)
    assert calls == ["f1s", "f2", "f3", "f4", "f5"]

    calls.clear()
    pipeline.ejecutar_pipeline_completo(Path("dummy.xlsx"), es_historico=True)
    assert calls == ["f1h", "f2", "f3", "f4", "f5"]
