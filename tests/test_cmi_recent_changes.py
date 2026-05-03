"""Pruebas de regresion para ajustes recientes en CMI estrategico."""

import pandas as pd

from services import ai_analysis
from streamlit_app.components.cmi_tabs.tab_lineas import _with_ui_group_key


def test_with_ui_group_key_prioriza_id():
    df = pd.DataFrame(
        {
            "Id": [204, 204, 305],
            "Indicador": ["Caja", "Caja", "Otro"],
        }
    )

    out = _with_ui_group_key(df)

    assert "_ui_group_key" in out.columns
    assert out["_ui_group_key"].tolist() == ["204", "204", "305"]


def test_with_ui_group_key_fallback_indicador():
    df = pd.DataFrame({"Indicador": [" Caja ", "Caja", "Otro"]})

    out = _with_ui_group_key(df)

    assert out["_ui_group_key"].tolist() == ["caja", "caja", "otro"]


def test_analizar_linea_cmi_tiene_fallback_heuristico(monkeypatch):
    monkeypatch.setattr(ai_analysis, "_get_client", lambda: None)

    payload = (
        '[{"Indicador":"Caja","Objetivo":"Sostenibilidad",'
        '"cumplimiento_pct":82.3,"Nivel de cumplimiento":"Alerta"}]'
    )
    text = ai_analysis.analizar_linea_cmi("Sostenibilidad", "98.7", 10, 2, payload)

    assert isinstance(text, str)
    assert "Directriz" in text
    assert "Sostenibilidad" in text


def test_analizar_ficha_cmi_tiene_fallback_heuristico(monkeypatch):
    monkeypatch.setattr(ai_analysis, "_get_client", lambda: None)

    text = ai_analysis.analizar_ficha_cmi(
        nombre="Caja",
        linea="Sostenibilidad",
        objetivo="Optimizar recursos",
        meta="95",
        ejecucion="152.24",
        nivel="Sobrecumplimiento",
        cumplimiento="130",
    )

    assert isinstance(text, str)
    assert "Diagnóstico" in text
    assert "Recomendación" in text
