"""
tests/test_etl_extraccion.py
Cobertura de scripts/etl/extraccion.py — funciones de extracción de Meta/Ejecución.

Cubre las funciones puras (sin I/O ni dependencias externas):
  - extraer_meta_ejec_variables
  - extraer_meta_ejec_series
  - extraer_por_simbolo
  - _calc_ejec_series
  - _calc_meta_series
  - _agregar_series_por_tipo_calculo
"""
import pytest
import numpy as np

from scripts.etl.extraccion import (
    extraer_meta_ejec_variables,
    extraer_meta_ejec_series,
    extraer_por_simbolo,
    _calc_ejec_series,
    _calc_meta_series,
    _agregar_series_por_tipo_calculo,
    _EXT_SER_SUM_VAR,
    _EXT_SER_AVG_RES,
    _EXT_SER_AVG_VAR,
    _EXT_SER_SUM_RES,
)


# ─────────────────────────────────────────────────────────────────────────────
# extraer_meta_ejec_variables
# ─────────────────────────────────────────────────────────────────────────────

class TestExtraerMetaEjecVariables:
    def test_lista_vacia(self):
        assert extraer_meta_ejec_variables([]) == (None, None)

    def test_extrae_por_keywords(self):
        vars_list = [
            {"nombre": "Valor real", "valor": 85.0},
            {"nombre": "Valor planeado", "valor": 100.0},
        ]
        meta, ejec = extraer_meta_ejec_variables(vars_list)
        assert meta == 100.0
        assert ejec == 85.0

    def test_fallback_posicion_cuando_no_hay_keyword(self):
        vars_list = [
            {"nombre": "Variable A", "valor": 50.0},
            {"nombre": "Variable B", "valor": 80.0},
        ]
        meta, ejec = extraer_meta_ejec_variables(vars_list)
        # fallback: posición 1 = meta, posición 0 = ejec
        assert ejec == 50.0
        assert meta == 80.0

    def test_valor_none_ignorado(self):
        vars_list = [
            {"nombre": "real", "valor": None},
            {"nombre": "planeado", "valor": 100.0},
        ]
        meta, ejec = extraer_meta_ejec_variables(vars_list)
        assert meta == 100.0
        assert ejec is None or ejec == 100.0  # fallback posicional

    def test_valor_nan_ignorado(self):
        vars_list = [
            {"nombre": "ejecutado", "valor": float("nan")},
            {"nombre": "programado", "valor": 90.0},
        ]
        meta, ejec = extraer_meta_ejec_variables(vars_list)
        assert meta == 90.0

    def test_una_sola_variable(self):
        vars_list = [{"nombre": "logrado", "valor": 75.0}]
        meta, ejec = extraer_meta_ejec_variables(vars_list)
        assert ejec == 75.0


# ─────────────────────────────────────────────────────────────────────────────
# extraer_meta_ejec_series
# ─────────────────────────────────────────────────────────────────────────────

class TestExtraerMetaEjecSeries:
    def test_lista_vacia(self):
        assert extraer_meta_ejec_series([]) == (None, None)

    def test_suma_meta_y_resultado(self):
        series = [
            {"meta": 50.0, "resultado": 40.0},
            {"meta": 50.0, "resultado": 45.0},
        ]
        meta, ejec = extraer_meta_ejec_series(series)
        assert meta == 100.0
        assert ejec == 85.0

    def test_sin_meta(self):
        series = [{"resultado": 30.0}, {"resultado": 20.0}]
        meta, ejec = extraer_meta_ejec_series(series)
        assert meta is None
        assert ejec == 50.0

    def test_sin_resultado(self):
        series = [{"meta": 100.0}, {"meta": 100.0}]
        meta, ejec = extraer_meta_ejec_series(series)
        assert meta == 200.0
        assert ejec is None

    def test_nan_ignorado(self):
        series = [
            {"meta": float("nan"), "resultado": 40.0},
            {"meta": 100.0, "resultado": float("nan")},
        ]
        meta, ejec = extraer_meta_ejec_series(series)
        assert meta == 100.0
        assert ejec == 40.0


# ─────────────────────────────────────────────────────────────────────────────
# extraer_por_simbolo
# ─────────────────────────────────────────────────────────────────────────────

class TestExtraerPorSimbolo:
    def test_encuentra_por_simbolo_exacto(self):
        vars_list = [{"simbolo": "A", "valor": 10.0}, {"simbolo": "B", "valor": 20.0}]
        assert extraer_por_simbolo(vars_list, "A") == 10.0

    def test_case_insensitive(self):
        vars_list = [{"simbolo": "ejec", "valor": 55.0}]
        assert extraer_por_simbolo(vars_list, "EJEC") == 55.0

    def test_simbolo_no_encontrado(self):
        vars_list = [{"simbolo": "A", "valor": 10.0}]
        assert extraer_por_simbolo(vars_list, "Z") is None

    def test_lista_vacia(self):
        assert extraer_por_simbolo([], "A") is None

    def test_simbolo_none(self):
        assert extraer_por_simbolo([{"simbolo": "A", "valor": 5.0}], None) is None

    def test_valor_nan_ignorado(self):
        vars_list = [{"simbolo": "X", "valor": float("nan")}]
        assert extraer_por_simbolo(vars_list, "X") is None


# ─────────────────────────────────────────────────────────────────────────────
# _calc_ejec_series
# ─────────────────────────────────────────────────────────────────────────────

class TestCalcEjecSeries:
    def _ser_json(self, series):
        import json
        return str(series).replace("'", '"')

    def test_series_raw_none(self):
        assert _calc_ejec_series(None, _EXT_SER_SUM_VAR) is None

    def test_sum_var(self):
        series = [
            {"variables": [{"valor": 10}, {"valor": 20}]},
            {"variables": [{"valor": 5}]},
        ]
        raw = str(series)
        result = _calc_ejec_series(raw, _EXT_SER_SUM_VAR)
        assert result == 35.0

    def test_avg_res(self):
        series = [{"resultado": 80}, {"resultado": 60}]
        raw = str(series)
        result = _calc_ejec_series(raw, _EXT_SER_AVG_RES)
        assert result == 70.0

    def test_sum_res(self):
        series = [{"resultado": 30}, {"resultado": 70}]
        raw = str(series)
        result = _calc_ejec_series(raw, _EXT_SER_SUM_RES)
        assert result == 100.0

    def test_avg_var(self):
        series = [
            {"variables": [{"valor": 10}, {"valor": 20}]},  # suma=30
            {"variables": [{"valor": 10}]},                  # suma=10
        ]
        raw = str(series)
        result = _calc_ejec_series(raw, _EXT_SER_AVG_VAR)
        assert result == 20.0  # (30+10)/2

    def test_tipo_desconocido(self):
        series = [{"resultado": 50}]
        result = _calc_ejec_series(str(series), "TipoDesconocido")
        assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# _calc_meta_series
# ─────────────────────────────────────────────────────────────────────────────

class TestCalcMetaSeries:
    def test_series_raw_none(self):
        assert _calc_meta_series(None, _EXT_SER_SUM_RES) is None

    def test_sum_metas(self):
        series = [{"meta": 50}, {"meta": 50}]
        result = _calc_meta_series(str(series), _EXT_SER_SUM_RES)
        assert result == 100.0

    def test_avg_metas(self):
        series = [{"meta": 80}, {"meta": 100}]
        result = _calc_meta_series(str(series), _EXT_SER_AVG_RES)
        assert result == 90.0

    def test_flags_binarios_retorna_none(self):
        # Metas de 0 y 1 se consideran flags, no metas reales
        series = [{"meta": 1}, {"meta": 0}]
        result = _calc_meta_series(str(series), _EXT_SER_SUM_RES)
        assert result is None

    def test_sin_meta(self):
        series = [{"resultado": 80}]
        result = _calc_meta_series(str(series), _EXT_SER_SUM_RES)
        assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# _agregar_series_por_tipo_calculo
# ─────────────────────────────────────────────────────────────────────────────

class TestAgregarSeriesPorTipoCalculo:
    def test_tipo_cierre_retorna_none(self):
        series = [{"resultado": 50, "meta": 100}]
        ejec, meta = _agregar_series_por_tipo_calculo(str(series), "cierre")
        assert ejec is None and meta is None

    def test_acumulado_suma(self):
        series = [{"resultado": 30, "meta": 50}, {"resultado": 40, "meta": 50}]
        ejec, meta = _agregar_series_por_tipo_calculo(str(series), "acumulado")
        assert ejec == 70.0
        assert meta == 100.0

    def test_promedio(self):
        series = [{"resultado": 80, "meta": 100}, {"resultado": 60, "meta": 100}]
        ejec, meta = _agregar_series_por_tipo_calculo(str(series), "promedio")
        assert ejec == 70.0
        assert meta == 100.0

    def test_fallback_suma(self):
        series = [{"resultado": 25, "meta": 50}, {"resultado": 25, "meta": 50}]
        ejec, meta = _agregar_series_por_tipo_calculo(str(series), "otro")
        assert ejec == 50.0
        assert meta == 100.0

    def test_series_vacias(self):
        ejec, meta = _agregar_series_por_tipo_calculo(None, "acumulado")
        assert ejec is None and meta is None

    def test_metas_binarias_se_ignoran(self):
        series = [{"resultado": 50, "meta": 1}, {"resultado": 30, "meta": 0}]
        ejec, meta = _agregar_series_por_tipo_calculo(str(series), "acumulado")
        assert ejec == 80.0
        assert meta is None  # metas binarias ignoradas
