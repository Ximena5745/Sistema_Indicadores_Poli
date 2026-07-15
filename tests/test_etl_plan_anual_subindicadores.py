"""
tests/test_etl_plan_anual_subindicadores.py
Cobertura de scripts/etl/builders.py::expandir_series_como_subindicadores()
para el grupo Plan Anual (Retos): 373, 390, 414-418, 420, 469-471.

Verifica que Meta/Ejecucion se toman de las variables de "avance"/"esperado"
correctas por indicador padre (_SIMBOLOS_PLAN_ANUAL), NO de
serie["resultado"]/serie["meta"] (que son cumplimiento%/100 hardcodeado).

También cubre el tope de 100% en Cumplimiento y CumplReal para indicadores
de Plan Anual (scripts/etl/cumplimiento.py) y el caso regular sin tope.
"""
import pandas as pd
import pytest

from scripts.etl.builders import expandir_series_como_subindicadores, _SIMBOLOS_PLAN_ANUAL
from scripts.etl.cumplimiento import _calc_cumpl, _calc_cumpl_con_tope_dinamico

# Nombre de una serie real (normalizada) por padre, para pasar el filtro de
# config/series_subindicadores.toml sin depender del texto exacto.
_SERIE_POR_PADRE = {
    "373": "Expansión",
    "390": "ESCUELA DE CIENCIAS BÁSICAS",
    "414": "Vicerrectoría de crecimiento",
    "415": "Gerencia de operaciones",
    "416": "Gerencia de matriculas",
    "417": "Dirección de contabilidad",
    "418": "Dirección aseguramiento de la calidad",
    "420": "SGC",
    "469": "FSCC- DERECHO Y GOBIERNO-DERECHO",
    "470": "DIRECTOR EDITORIAL",
    "471": "DIRECTOR DE BIENESTAR Y RELAC. LABORALES",
}


def _df_padre(id_padre: str, series: list) -> pd.DataFrame:
    return pd.DataFrame([{
        "Id": id_padre,
        "Indicador": f"Indicador padre {id_padre}",
        "Proceso": "Proceso1",
        "Periodicidad": "Semestral",
        "Sentido": "Positivo",
        "fecha": pd.Timestamp(2025, 6, 30),
        "series": series,
    }])


class TestSimbolosPorPadre:
    """Un caso por cada uno de los 11 padres: Meta/Ejecucion deben venir del
    símbolo esperado/avance correcto, no de resultado/meta."""

    @pytest.mark.parametrize("id_padre", sorted(_SIMBOLOS_PLAN_ANUAL.keys()))
    def test_usa_simbolos_avance_esperado(self, id_padre):
        simb_avance, simb_esperado = _SIMBOLOS_PLAN_ANUAL[id_padre]
        nombre_serie = _SERIE_POR_PADRE[id_padre]

        serie = {
            "nombre": nombre_serie,
            # resultado/meta deliberadamente distintos de avance/esperado
            # para probar que el fix NO los usa cuando las variables existen.
            "resultado": 999.0,
            "meta": 100.0,
            "variables": [
                {"simbolo": simb_avance, "valor": 54},
                {"simbolo": simb_esperado, "valor": 58},
            ],
        }
        df = _df_padre(id_padre, [serie])

        regs = expandir_series_como_subindicadores(df, set(), modo="semestral")

        assert len(regs) == 1
        assert regs[0]["Ejecucion"] == 54.0
        assert regs[0]["Meta"] == 58.0


class TestFallbackSinVariables:
    def test_cae_a_resultado_meta_si_no_hay_variables(self):
        serie = {
            "nombre": "SGC",
            "resultado": 93.1,
            "meta": 100.0,
            "variables": [],
        }
        df = _df_padre("420", [serie])

        regs = expandir_series_como_subindicadores(df, set(), modo="semestral")

        assert len(regs) == 1
        assert regs[0]["Ejecucion"] == 93.1
        assert regs[0]["Meta"] == 100.0


class TestTopeCumplimientoPlanAnual:
    def test_cumplimiento_y_cumplreal_topeados_al_100_para_plan_anual(self):
        # avance=110 vs esperado=100 → sobre-ejecución real, debe toparse a 100%
        cumpl_capped, cumpl_real = _calc_cumpl(meta=100, ejec=110, sentido="Positivo", tope=1.0)
        assert cumpl_capped == 1.0
        assert cumpl_real == 1.0

    def test_tope_dinamico_plan_anual_topea_ambos(self):
        cumpl_capped, cumpl_real = _calc_cumpl_con_tope_dinamico(
            meta=100, ejec=130, sentido="Positivo",
            id_indicador="420",
            ids_plan_anual=frozenset({"420"}),
            ids_tope_100=frozenset(),
        )
        assert cumpl_capped == 1.0
        assert cumpl_real == 1.0

    def test_regular_no_topea_cumplreal(self):
        # Indicador regular (no Plan Anual/tope-100): CumplReal sigue sin límite.
        cumpl_capped, cumpl_real = _calc_cumpl(meta=100, ejec=150, sentido="Positivo", tope=1.3)
        assert cumpl_capped == 1.3
        assert cumpl_real == 1.5
