from pathlib import Path

import pandas as pd

from streamlit_app.pages import gestion_om, seguimiento_reportes
from streamlit_app.utils import formatting


def _clear_cache(func):
    if hasattr(func, "clear"):
        func.clear()


def test_formatting_basico():
    assert formatting.is_null(None) is True
    assert formatting.is_null(" ") is True
    assert formatting.is_null("nan") is True
    assert formatting.is_null("abc") is False

    assert formatting.to_num("12.5") == 12.5
    assert formatting.to_num("nope") is None

    assert formatting.limpiar("&amp; dato ") == "& dato"
    assert formatting.id_limpio(10.0) == "10"
    assert formatting.id_limpio(" A-1 ") == "A-1"


def test_formatting_valores():
    assert formatting.fmt_num(1234.0) == "1,234"
    assert formatting.fmt_num(None) == "—"

    assert formatting.fmt_valor(95, "%", 1) == "95.0%"
    assert formatting.fmt_valor(1234.5, "$", 2) == "$1.234,50"
    assert formatting.fmt_valor(1000, "ENT", 0) == "1,000"
    assert formatting.fmt_valor(10.2, "kg", 1) == "10.2 kg"


def test_formato_global_ejecucion_his_signo():
    row_pct = {"Ejecución s": "%", "Ejecución": 95.126, "DecimalesEje": 1, "Decimales": 1}
    assert formatting.ejecucion_his_signo(row_pct) == "95.1%"

    row_estado = {"Ejecución s": "Sin reporte", "Ejecución": 0}
    assert formatting.ejecucion_his_signo(row_estado) == "Pendiente"

    row_ent = {"Ejecución s": "ENT", "Ejecución": 1234.2}
    assert formatting.ejecucion_his_signo(row_ent) == "1,234"


def test_formato_global_meta_y_df():
    row_meta = {"Meta s": "$", "Meta": 1234.5, "Decimales": 2, "DecimalesEje": 2}
    assert formatting.meta_his_signo(row_meta) == "$1,234.50"

    df = pd.DataFrame(
        [
            {
                "Meta": 1000,
                "Ejecucion": 950,
                "Meta_Signo": "%",
                "Ejecucion_Signo": "%",
                "DecimalesEje": 0,
            },
            {
                "Meta": 0,
                "Ejecucion": 0,
                "Meta_Signo": "Sin reporte",
                "Ejecucion_Signo": "Sin reporte",
            },
        ]
    )
    out = formatting.formatear_meta_ejecucion_df(df, meta_col="Meta", ejec_col="Ejecucion")
    assert out.loc[0, "Meta"] == "1,000%"
    assert out.loc[0, "Ejecucion"] == "950%"
    assert out.loc[1, "Meta"] == "Pendiente"
    assert out.loc[1, "Ejecucion"] == "Pendiente"


def test_cargar_indicadores_riesgo_filtra_y_ultima_fecha(monkeypatch):
    _clear_cache(gestion_om._cargar_indicadores_riesgo)

    fake_df = pd.DataFrame(
        [
            {
                "Id": "1",
                "Indicador": "A",
                "Proceso": "P1",
                "Categoria": "Peligro",
                "Fecha": "2026-01-01",
            },
            {
                "Id": "1",
                "Indicador": "A",
                "Proceso": "P1",
                "Categoria": "Alerta",
                "Fecha": "2026-02-01",
            },
            {
                "Id": "2",
                "Indicador": "B",
                "Proceso": "P2",
                "Categoria": "Cumplimiento",
                "Fecha": "2026-02-01",
            },
            {
                "Id": "3",
                "Indicador": "C",
                "Proceso": "P3",
                "Categoria": "Peligro",
                "Fecha": "2026-03-01",
            },
        ]
    )

    monkeypatch.setattr(gestion_om, "cargar_dataset", lambda: fake_df)

    result = gestion_om._cargar_indicadores_riesgo()

    assert set(result["Id"].tolist()) == {"1", "3"}
    fila_1 = result[result["Id"] == "1"].iloc[0]
    assert fila_1["Categoria"] == "Alerta"


def test_cargar_tracking_desde_excel(tmp_path, monkeypatch):
    _clear_cache(seguimiento_reportes._cargar_tracking)

    salida = tmp_path / "Seguimiento_Reporte.xlsx"
    df = pd.DataFrame(
        {
            "Id": [1.0, 2.0],
            "Año": [2026, 2026],
            "Mes": [3, 4],
            "Proceso": ["P1", "P2"],
            "Estado": ["Reportado", "Pendiente"],
        }
    )
    with pd.ExcelWriter(salida, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Tracking Mensual", index=False)

    monkeypatch.setattr(seguimiento_reportes, "RUTA_SEGUIMIENTO", Path(salida))

    result = seguimiento_reportes._cargar_tracking()
    assert len(result) == 2
    assert result["Id"].tolist() == ["1", "2"]
    assert str(result["Año"].dtype) == "Int64"
    assert str(result["Mes"].dtype) == "Int64"


def test_cargar_tracking_si_no_existe(monkeypatch):
    _clear_cache(seguimiento_reportes._cargar_tracking)
    monkeypatch.setattr(seguimiento_reportes, "RUTA_SEGUIMIENTO", Path("no_existe.xlsx"))
    result = seguimiento_reportes._cargar_tracking()
    assert result.empty
