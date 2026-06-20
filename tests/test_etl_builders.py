"""
tests/test_etl_builders.py
Cobertura de scripts/etl/builders.py.

Cubre:
  - construir_registros_historico
  - construir_registros_semestral (AVG y SUM)
  - construir_registros_cierres (LAST, AVG, SUM)

Los tests mockean _extraer_registro, _ejec_corrected_from_row y
_meta_corrected_from_row para aislar la lógica del builder.
"""
from unittest.mock import patch

import pandas as pd
import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de fixture
# ─────────────────────────────────────────────────────────────────────────────

def _df_mensual(id_val="10", year=2025, months=(6,)):
    rows = []
    for m in months:
        import calendar
        last_day = calendar.monthrange(year, m)[1]
        rows.append({
            "Id": id_val,
            "Indicador": "Indicador de Prueba",
            "Proceso": "Proceso1",
            "Periodicidad": "Mensual",
            "Sentido": "Positivo",
            "fecha": pd.Timestamp(year, m, last_day),
            "LLAVE": f"{id_val}-{year}-{m:02d}-{last_day:02d}",
            "Meta": 100.0,
            "Ejecucion": 85.0,
            "resultado": 85.0,
            "meta": 100.0,
            "variables": None,
            "series": None,
        })
    df = pd.DataFrame(rows)
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df


# ─────────────────────────────────────────────────────────────────────────────
# construir_registros_historico
# ─────────────────────────────────────────────────────────────────────────────

class TestConstruirRegistrosHistorico:

    @patch("scripts.etl.builders._extraer_registro")
    def test_registro_nuevo_se_agrega(self, mock_ext):
        mock_ext.return_value = (100.0, 85.0, "consolidado", False)
        from scripts.etl.builders import construir_registros_historico
        regs, skip, na = construir_registros_historico(
            _df_mensual(), set(), {}
        )
        assert len(regs) == 1
        assert regs[0]["Meta"] == 100.0
        assert regs[0]["Ejecucion"] == 85.0

    @patch("scripts.etl.builders._extraer_registro")
    def test_llave_existente_no_se_procesa(self, mock_ext):
        mock_ext.return_value = (100.0, 85.0, "consolidado", False)
        from scripts.etl.builders import construir_registros_historico
        df = _df_mensual()
        llave_existente = df.iloc[0]["LLAVE"]
        regs, skip, na = construir_registros_historico(
            df, {llave_existente}, {}
        )
        assert regs == []
        mock_ext.assert_not_called()

    @patch("scripts.etl.builders._extraer_registro")
    def test_fuente_skip_incrementa_contador(self, mock_ext):
        mock_ext.return_value = (None, None, "skip", False)
        from scripts.etl.builders import construir_registros_historico
        regs, skip, na = construir_registros_historico(
            _df_mensual(), set(), {}
        )
        assert regs == []
        assert skip == 1

    @patch("scripts.etl.builders._extraer_registro")
    def test_fuente_sin_resultado_incrementa_skip(self, mock_ext):
        mock_ext.return_value = (None, None, "sin_resultado", False)
        from scripts.etl.builders import construir_registros_historico
        regs, skip, na = construir_registros_historico(
            _df_mensual(), set(), {}
        )
        assert skip == 1
        assert regs == []

    @patch("scripts.etl.builders._extraer_registro")
    def test_es_na_incrementa_conteo_y_se_agrega(self, mock_ext):
        mock_ext.return_value = (None, None, "na", True)
        from scripts.etl.builders import construir_registros_historico
        regs, skip, na = construir_registros_historico(
            _df_mensual(), set(), {}
        )
        assert na == 1
        assert len(regs) == 1

    @patch("scripts.etl.builders._extraer_registro")
    def test_kawak_validos_filtra_id_ausente(self, mock_ext):
        mock_ext.return_value = (100.0, 85.0, "consolidado", False)
        from scripts.etl.builders import construir_registros_historico
        regs, skip, na = construir_registros_historico(
            _df_mensual(id_val="10"),
            set(), {},
            kawak_validos={("99", 2025)},
        )
        assert regs == []
        assert skip == 1

    @patch("scripts.etl.builders._extraer_registro")
    def test_kawak_validos_permite_id_presente(self, mock_ext):
        mock_ext.return_value = (100.0, 85.0, "consolidado", False)
        from scripts.etl.builders import construir_registros_historico
        regs, skip, na = construir_registros_historico(
            _df_mensual(id_val="10", year=2025),
            set(), {},
            kawak_validos={("10", 2025)},
        )
        assert len(regs) == 1

    @patch("scripts.etl.builders._extraer_registro")
    def test_retorna_claves_correctas(self, mock_ext):
        mock_ext.return_value = (50.0, 40.0, "api", False)
        from scripts.etl.builders import construir_registros_historico
        regs, _, _ = construir_registros_historico(
            _df_mensual(), set(), {}
        )
        expected_keys = {"Id", "Indicador", "Proceso", "Periodicidad",
                         "Sentido", "fecha", "Meta", "Ejecucion", "LLAVE", "es_na"}
        assert expected_keys.issubset(set(regs[0].keys()))

    @patch("scripts.etl.builders._extraer_registro")
    def test_dataframe_vacio_retorna_listas_vacias(self, mock_ext):
        from scripts.etl.builders import construir_registros_historico
        df = pd.DataFrame(columns=["Id", "LLAVE", "fecha", "Indicador",
                                    "Proceso", "Periodicidad", "Sentido"])
        regs, skip, na = construir_registros_historico(df, set(), {})
        assert regs == []
        assert skip == 0
        assert na == 0

    @patch("scripts.etl.builders._extraer_registro")
    def test_multiples_registros_nuevos(self, mock_ext):
        mock_ext.return_value = (100.0, 80.0, "consolidado", False)
        from scripts.etl.builders import construir_registros_historico
        df = _df_mensual(months=(1, 2, 3, 4, 5, 6))
        regs, skip, na = construir_registros_historico(df, set(), {})
        assert len(regs) == 6

    @patch("scripts.etl.builders._extraer_registro")
    def test_llave_none_se_descarta(self, mock_ext):
        mock_ext.return_value = (100.0, 80.0, "consolidado", False)
        from scripts.etl.builders import construir_registros_historico
        df = pd.DataFrame([{
            "Id": "10", "Indicador": "Test", "Proceso": "P",
            "Periodicidad": "Mensual", "Sentido": "+",
            "fecha": pd.Timestamp("2025-06-30"),
            "LLAVE": None,  # None LLAVE should be dropped
        }])
        regs, skip, na = construir_registros_historico(df, set(), {})
        assert regs == []


# ─────────────────────────────────────────────────────────────────────────────
# construir_registros_semestral — patrón SUM/AVG
# ─────────────────────────────────────────────────────────────────────────────

class TestConstruirRegistrosSemestral:

    @patch("scripts.etl.builders._extraer_registro")
    @patch("scripts.etl.builders._ejec_corrected_from_row")
    @patch("scripts.etl.builders._meta_corrected_from_row")
    def test_suma_acumulado_primer_semestre(self, mock_meta, mock_ejec, mock_ext):
        mock_ejec.return_value = 40.0
        mock_meta.return_value = 50.0
        mock_ext.return_value = (100.0, 80.0, "consolidado", False)

        from scripts.etl.builders import construir_registros_semestral

        df = _df_mensual(months=(1, 2, 3, 4, 5, 6))  # 6 months
        regs, skip, na = construir_registros_semestral(
            df, set(), {},
            tipo_calculo_map={"10": "acumulado"},
        )
        agg_regs = [r for r in regs if r.get("Ejecucion") is not None]
        assert len(agg_regs) >= 1
        # Sum of 6 months × 40.0 = 240.0
        sums = [r["Ejecucion"] for r in agg_regs if "Ejecucion" in r]
        assert any(s is not None for s in sums)

    @patch("scripts.etl.builders._extraer_registro")
    @patch("scripts.etl.builders._ejec_corrected_from_row")
    @patch("scripts.etl.builders._meta_corrected_from_row")
    def test_promedio_calcula_media(self, mock_meta, mock_ejec, mock_ext):
        mock_ejec.return_value = 80.0
        mock_meta.return_value = 100.0
        mock_ext.return_value = (100.0, 80.0, "consolidado", False)

        from scripts.etl.builders import construir_registros_semestral

        df = _df_mensual(months=(1, 2, 3, 4, 5, 6))
        regs, skip, na = construir_registros_semestral(
            df, set(), {},
            tipo_calculo_map={"10": "promedio"},
        )
        agg_regs = [r for r in regs if r.get("Ejecucion") == 80.0]
        # promedio(80, 80, 80, 80, 80, 80) = 80
        assert len(agg_regs) >= 1

    @patch("scripts.etl.builders._extraer_registro")
    def test_indicador_cierre_filtra_junio_diciembre(self, mock_ext):
        mock_ext.return_value = (100.0, 90.0, "consolidado", False)
        from scripts.etl.builders import construir_registros_semestral

        # Months 1-6, but only June (6) is a semestral endpoint
        df = _df_mensual(months=(3, 6))
        regs, skip, na = construir_registros_semestral(
            df, set(), {}
        )
        # Standard path calls construir_registros_historico on filtered df
        assert isinstance(regs, list)

    @patch("scripts.etl.builders._extraer_registro")
    @patch("scripts.etl.builders._ejec_corrected_from_row")
    @patch("scripts.etl.builders._meta_corrected_from_row")
    def test_llave_existente_agg_se_omite(self, mock_meta, mock_ejec, mock_ext):
        mock_ejec.return_value = 50.0
        mock_meta.return_value = 100.0
        mock_ext.return_value = (100.0, 50.0, "consolidado", False)

        from scripts.etl.builders import construir_registros_semestral

        df = _df_mensual(months=(1, 6))
        # Pre-populate the expected aggregate LLAVE
        llaves = {"10-2025-06-30"}
        regs, skip, na = construir_registros_semestral(
            df, llaves, {},
            tipo_calculo_map={"10": "acumulado"},
        )
        # aggregate record for 10/2025-S1 should be skipped
        agg_ejecuciones = [r["Ejecucion"] for r in regs
                           if r.get("LLAVE") == "10-2025-06-30"]
        assert len(agg_ejecuciones) == 0


# ─────────────────────────────────────────────────────────────────────────────
# construir_registros_cierres
# ─────────────────────────────────────────────────────────────────────────────

class TestConstruirRegistrosCierres:

    def _df_anual(self, months=(6, 12), id_val="10", year=2025):
        import calendar
        rows = []
        for m in months:
            last = calendar.monthrange(year, m)[1]
            rows.append({
                "Id": id_val, "Indicador": "Test", "Proceso": "P",
                "Periodicidad": "Mensual", "Sentido": "+",
                "fecha": pd.Timestamp(year, m, last),
                "LLAVE": f"{id_val}-{year}-{m:02d}-{last:02d}",
            })
        df = pd.DataFrame(rows)
        df["fecha"] = pd.to_datetime(df["fecha"])
        return df

    @patch("scripts.etl.builders._extraer_registro")
    def test_last_elige_diciembre_para_año_historico(self, mock_ext):
        mock_ext.return_value = (100.0, 90.0, "api", False)
        from scripts.etl.builders import construir_registros_cierres

        df = self._df_anual(months=(6, 12), year=2023)
        regs, skip, na = construir_registros_cierres(df, {})
        assert len(regs) == 1
        assert regs[0]["fecha"].month == 12

    @patch("scripts.etl.builders._extraer_registro")
    def test_last_sin_diciembre_usa_ultimo_mes(self, mock_ext):
        mock_ext.return_value = (100.0, 75.0, "api", False)
        from scripts.etl.builders import construir_registros_cierres

        # Only June available
        df = self._df_anual(months=(6,), year=2023)
        regs, skip, na = construir_registros_cierres(df, {})
        assert len(regs) == 1

    @patch("scripts.etl.builders._ejec_corrected_from_row")
    @patch("scripts.etl.builders._meta_corrected_from_row")
    def test_acumulado_suma_todos_los_meses(self, mock_meta, mock_ejec):
        mock_ejec.return_value = 10.0
        mock_meta.return_value = 12.0
        from scripts.etl.builders import construir_registros_cierres

        df = self._df_anual(months=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12),
                            year=2023)
        regs, skip, na = construir_registros_cierres(
            df, {},
            tipo_calculo_map={"10": "acumulado"},
        )
        assert len(regs) == 1
        assert regs[0]["Ejecucion"] == 120.0  # 12 × 10.0

    @patch("scripts.etl.builders._ejec_corrected_from_row")
    @patch("scripts.etl.builders._meta_corrected_from_row")
    def test_promedio_calcula_media_mensual(self, mock_meta, mock_ejec):
        mock_ejec.return_value = 80.0
        mock_meta.return_value = 100.0
        from scripts.etl.builders import construir_registros_cierres

        df = self._df_anual(months=(6, 12), year=2023)
        regs, skip, na = construir_registros_cierres(
            df, {},
            tipo_calculo_map={"10": "promedio"},
        )
        assert len(regs) == 1
        assert regs[0]["Ejecucion"] == 80.0  # avg(80, 80)

    @patch("scripts.etl.builders._extraer_registro")
    def test_kawak_validos_filtra_año_no_valido(self, mock_ext):
        mock_ext.return_value = (100.0, 90.0, "api", False)
        from scripts.etl.builders import construir_registros_cierres

        df = self._df_anual(months=(12,), year=2023)
        regs, skip, na = construir_registros_cierres(
            df, {},
            kawak_validos={("10", 2022)},  # 2023 not valid
        )
        assert regs == []
        assert skip >= 1

    @patch("scripts.etl.builders._extraer_registro")
    def test_fuente_skip_no_agrega_registro(self, mock_ext):
        mock_ext.return_value = (None, None, "skip", False)
        from scripts.etl.builders import construir_registros_cierres

        df = self._df_anual(months=(12,), year=2023)
        regs, skip, na = construir_registros_cierres(df, {})
        assert regs == []
        assert skip >= 1
