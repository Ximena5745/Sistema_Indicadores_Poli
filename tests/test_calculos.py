"""
tests/test_calculos.py — Pruebas unitarias para core/calculos.py.

Ejecutar:
    pytest tests/ -v

No requiere Streamlit ni archivos de datos.
"""

import math
import pandas as pd
import pytest

from core.calculos import (
    normalizar_cumplimiento,
    categorizar_cumplimiento,
    calcular_tendencia,
    calcular_meses_en_peligro,
    obtener_ultimo_registro,
    calcular_kpis,
    estado_tiempo_acciones,
)

# ── normalizar_cumplimiento ────────────────────────────────────────────────────
# ACTUALIZADO (21 abr 2026): Opción A Mejorada
# - Removida heurística "si > 2"
# - Ahora valida rango [0.0, 1.3]
# - Retorna NaN si fuera de rango

import numpy as np


class TestNormalizarCumplimiento:
    """Tests para normalizar_cumplimiento() con validación de rango"""

    def test_valor_valido_minimo(self):
        """Caso: valor mínimo válido (0.0)"""
        assert normalizar_cumplimiento(0.0) == pytest.approx(0.0)

    def test_valor_valido_maximo(self):
        """Caso: valor máximo válido (1.3 = 130%)"""
        assert normalizar_cumplimiento(1.3) == pytest.approx(1.3)

    def test_valor_intermedio(self):
        """Caso: valor en rango medio [0, 1.3]"""
        assert normalizar_cumplimiento(0.5) == pytest.approx(0.5)
        assert normalizar_cumplimiento(1.0) == pytest.approx(1.0)
        assert normalizar_cumplimiento(1.15) == pytest.approx(1.15)

    def test_nan_entrada(self):
        """Caso: entrada NaN"""
        assert math.isnan(normalizar_cumplimiento(np.nan))
        assert math.isnan(normalizar_cumplimiento(float("nan")))

    def test_string_valido(self):
        """Caso: string que puede convertirse a float (formato latinoamericano)"""
        # Formato latinoamericano: , para decimales
        assert normalizar_cumplimiento("0,5") == pytest.approx(0.5)
        assert normalizar_cumplimiento("1,0") == pytest.approx(1.0)
        assert normalizar_cumplimiento("0,95") == pytest.approx(0.95)
        assert normalizar_cumplimiento("1,3") == pytest.approx(1.3)

    def test_string_con_simbolo_porcentaje(self):
        """Caso: string con símbolo % (formato latinoamericano)"""
        # "0,95%" = 0.95 (dentro de rango) ✓
        assert normalizar_cumplimiento("0,95%") == pytest.approx(0.95)
        # "95%" = 95.0 (fuera de rango [0, 1.3]) → NaN
        assert math.isnan(normalizar_cumplimiento("95%"))
        # "130%" = 130.0 (fuera de rango) → NaN
        assert math.isnan(normalizar_cumplimiento("130%"))

    def test_string_invalido(self):
        """Caso: string que NO puede convertirse"""
        assert math.isnan(normalizar_cumplimiento("abc"))
        assert math.isnan(normalizar_cumplimiento("no_es_numero"))
        assert math.isnan(normalizar_cumplimiento(""))

    def test_valor_fuera_rango_superior(self):
        """Caso: valor > 1.3 (fuera de rango superior)"""
        assert math.isnan(normalizar_cumplimiento(1.31))
        assert math.isnan(normalizar_cumplimiento(2.0))
        assert math.isnan(normalizar_cumplimiento(100.0))
        assert math.isnan(normalizar_cumplimiento(1765.5))  # Valor encontrado en Cumplimiento Real

    def test_valor_fuera_rango_inferior(self):
        """Caso: valor < 0.0 (fuera de rango inferior)"""
        assert math.isnan(normalizar_cumplimiento(-0.1))
        assert math.isnan(normalizar_cumplimiento(-1.0))

    def test_string_con_miles_formato_latinoamericano(self):
        """Caso: strings con separador de miles (.) en formato latinoamericano"""
        # "1.000,0" parsea como 1000.0 (fuera de rango) → NaN
        assert math.isnan(normalizar_cumplimiento("1.000,0"))
        # "1.234,56" parsea como 1234.56 (fuera de rango) → NaN
        assert math.isnan(normalizar_cumplimiento("1.234,56"))

    def test_tipo_invalido(self):
        """Caso: tipo que no puede convertirse a float"""
        assert math.isnan(normalizar_cumplimiento({"valor": 0.5}))
        assert math.isnan(normalizar_cumplimiento([1, 2, 3]))

    def test_zero(self):
        """Caso específico: cero"""
        assert normalizar_cumplimiento(0) == pytest.approx(0.0)

    # NOTA: Tests de heurística "si > 2" REMOVIDOS (era la versión anterior)
    # La heurística ha sido eliminada completamente
    # Ahora cualquier valor > 1.3 retorna NaN


# ── categorizar_cumplimiento ───────────────────────────────────────────────────


class TestCategorizarCumplimiento:
    def test_peligro(self):
        assert categorizar_cumplimiento(0.50) == "Peligro"

    def test_limite_peligro(self):
        assert categorizar_cumplimiento(0.799) == "Peligro"

    def test_alerta_limite_inferior(self):
        assert categorizar_cumplimiento(0.80) == "Alerta"

    def test_alerta(self):
        assert categorizar_cumplimiento(0.90) == "Alerta"

    def test_cumplimiento_exacto(self):
        assert categorizar_cumplimiento(1.00) == "Cumplimiento"

    def test_cumplimiento(self):
        assert categorizar_cumplimiento(1.03) == "Cumplimiento"

    def test_limite_sobrecumplimiento(self):
        # 105% exacto → Sobrecumplimiento (umbral es < 1.05, no <=)
        assert categorizar_cumplimiento(1.05) == "Sobrecumplimiento"

    def test_justo_debajo_105(self):
        assert categorizar_cumplimiento(1.0499) == "Cumplimiento"

    def test_sobrecumplimiento(self):
        assert categorizar_cumplimiento(1.10) == "Sobrecumplimiento"

    def test_nan_sin_dato(self):
        assert categorizar_cumplimiento(float("nan")) == "Sin dato"

    def test_sentido_negativo_no_cambia_umbral(self):
        # El Sentido Negativo se aplica al calcular el cumplimiento, no aquí
        assert categorizar_cumplimiento(1.10, sentido="Negativo") == "Sobrecumplimiento"

    # ── Plan Anual: cumple desde 95%, tope 100% ──────────────────────────────
    def test_plan_anual_alerta(self):
        # 90% → Alerta para PA (entre 80% y 95%)
        assert categorizar_cumplimiento(0.90, id_indicador="45") == "Alerta"

    def test_plan_anual_cumplimiento_desde_95(self):
        assert categorizar_cumplimiento(0.95, id_indicador="45") == "Cumplimiento"

    def test_plan_anual_cumplimiento_99(self):
        assert categorizar_cumplimiento(0.99, id_indicador="45") == "Cumplimiento"

    def test_plan_anual_sobrecumplimiento_100(self):
        # 100% exacto → Sobrecumplimiento en PA (tope es < 1.0)
        assert categorizar_cumplimiento(1.00, id_indicador="45") == "Sobrecumplimiento"

    def test_indicador_normal_no_es_pa(self):
        # Id no PA: 95% sigue siendo Alerta
        assert categorizar_cumplimiento(0.95, id_indicador="999") == "Alerta"


# ── calcular_tendencia ─────────────────────────────────────────────────────────


class TestCalcularTendencia:
    def _df(self, vals):
        return pd.DataFrame(
            {
                "Fecha": pd.date_range("2024-01-01", periods=len(vals), freq="MS"),
                "Cumplimiento_norm": vals,
            }
        )

    def test_sin_datos_suficientes(self):
        assert calcular_tendencia(self._df([0.9])) == "→"

    def test_mejora(self):
        assert calcular_tendencia(self._df([0.80, 0.95])) == "↑"

    def test_empeora(self):
        assert calcular_tendencia(self._df([0.95, 0.80])) == "↓"

    def test_estable(self):
        assert calcular_tendencia(self._df([0.95, 0.954])) == "→"


# ── calcular_meses_en_peligro ──────────────────────────────────────────────────


class TestCalcularMesesEnPeligro:
    def _df(self, cats):
        return pd.DataFrame(
            {
                "Fecha": pd.date_range("2024-01-01", periods=len(cats), freq="MS"),
                "Categoria": cats,
            }
        )

    def test_sin_peligro(self):
        assert calcular_meses_en_peligro(self._df(["Cumplimiento", "Alerta"])) == 0

    def test_uno_en_peligro(self):
        assert calcular_meses_en_peligro(self._df(["Cumplimiento", "Peligro"])) == 1

    def test_consecutivos(self):
        assert calcular_meses_en_peligro(self._df(["Alerta", "Peligro", "Peligro"])) == 2

    def test_no_consecutivos(self):
        # Rompió la racha en el penúltimo
        assert calcular_meses_en_peligro(self._df(["Peligro", "Cumplimiento", "Peligro"])) == 1


# ── obtener_ultimo_registro ────────────────────────────────────────────────────


class TestObtenerUltimoRegistro:
    def test_vacio(self):
        df = pd.DataFrame()
        assert obtener_ultimo_registro(df).empty

    def test_deduplica_por_id(self):
        df = pd.DataFrame(
            {
                "Id": ["1", "1", "2"],
                "Fecha": pd.to_datetime(["2024-01-01", "2024-06-01", "2024-01-01"]),
                "Cumplimiento_norm": [0.8, 0.9, 1.0],
            }
        )
        result = obtener_ultimo_registro(df)
        assert len(result) == 2
        # Para Id=1 debe quedar el más reciente (0.9)
        assert result[result["Id"] == "1"]["Cumplimiento_norm"].iloc[0] == pytest.approx(0.9)

    def test_usa_revisar_si_existe(self):
        df = pd.DataFrame(
            {
                "Id": ["1", "1"],
                "Fecha": pd.to_datetime(["2024-01-01", "2024-06-01"]),
                "Cumplimiento_norm": [0.8, 0.9],
                "Revisar": [1, 0],
            }
        )
        result = obtener_ultimo_registro(df)
        assert len(result) == 1
        assert result["Cumplimiento_norm"].iloc[0] == pytest.approx(0.8)


# ── calcular_kpis ──────────────────────────────────────────────────────────────


class TestCalcularKpis:
    def test_proporciones(self):
        df = pd.DataFrame(
            {
                "Cumplimiento_norm": [0.5, 0.85, 1.02, 1.10, float("nan")],
                "Categoria": ["Peligro", "Alerta", "Cumplimiento", "Sobrecumplimiento", "Sin dato"],
            }
        )
        total, conteos = calcular_kpis(df)
        assert total == 4  # NaN excluido
        assert conteos["Peligro"]["n"] == 1
        assert conteos["Sobrecumplimiento"]["pct"] == pytest.approx(25.0)


# ── estado_tiempo_acciones ─────────────────────────────────────────────────────


class TestEstadoTiempoAcciones:
    def _df(self, dias, estado):
        return pd.DataFrame({"DIAS_VENCIDA": [dias], "ESTADO": [estado]})

    def test_cerrada(self):
        assert (
            estado_tiempo_acciones(self._df(-10, "Cerrada"))["Estado_Tiempo"].iloc[0] == "Cerrada"
        )

    def test_vencida(self):
        assert estado_tiempo_acciones(self._df(5, "Abierta"))["Estado_Tiempo"].iloc[0] == "Vencida"

    def test_por_vencer(self):
        assert (
            estado_tiempo_acciones(self._df(-15, "Abierta"))["Estado_Tiempo"].iloc[0]
            == "Por vencer"
        )

    def test_a_tiempo(self):
        assert (
            estado_tiempo_acciones(self._df(-60, "Abierta"))["Estado_Tiempo"].iloc[0] == "A tiempo"
        )
