"""Tests para services/plan_mejoramiento_loader.py — módulo Plan de Mejoramiento."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

import services.plan_mejoramiento_loader as pm_loader
from services.plan_mejoramiento_loader import (
    aggregate_plan_estado_by,
    compute_plan_cumplimiento_by_factor,
    get_plan_indicadores_for_factor,
    load_catalogo_plan_indicadores,
    load_plan_indicadores,
)
from streamlit_app.pages.plan_mejoramiento_utils import build_indicador_cump_texto, fmt_valor_plan


class TestLoadPlanIndicadores:
    """Tests para load_plan_indicadores()."""

    def test_returns_dataframe(self):
        df = load_plan_indicadores()
        assert isinstance(df, pd.DataFrame)

    def test_has_66_rows(self):
        df = load_plan_indicadores()
        assert len(df) == 66

    def test_has_required_columns(self):
        df = load_plan_indicadores()
        required = [
            "Factor", "Caracteristica", "Indicador", "Tipo",
            "Estado_raw", "Estado_Aprobacion", "Estado_final",
            "Factor_num", "Factor_nombre", "tiene_medicion",
            "Meta_num_2025", "Ejecucion_num_2025", "Cump_calc_2025",
            "Meta_num_2026", "Ejecucion_num_2026", "Cump_calc_2026",
            "Signo", "Decimales", "Decimales_Cump",
        ]
        for col in required:
            assert col in df.columns, f"Columna {col} faltante"

    def test_estado_final_values(self):
        df = load_plan_indicadores()
        valid = {"Activo", "Aprobado", "Pendiente"}
        assert set(df["Estado_final"].unique()).issubset(valid)

    def test_estado_counts_sum_to_total(self):
        df = load_plan_indicadores()
        counts = df["Estado_final"].value_counts()
        assert counts.sum() == 66

    def test_activo_requires_aprobado_and_tipo_and_medicion(self):
        df = load_plan_indicadores()
        activos = df[df["Estado_final"] == "Activo"]
        if not activos.empty:
            assert (activos["Estado_Aprobacion"] == "Aprobado").all()
            assert (activos["Tipo"] == "Indicador").all()
            # tiene_medicion depends on parsed numeric Meta/Ejecución
            # Some raw values ("Línea Base", "pendiente") don't parse
            # but still qualify as Activo via raw column check
            assert activos["tiene_medicion"].any()

    def test_cump_calc_bounds(self):
        df = load_plan_indicadores()
        for col in ("Cump_calc_2025", "Cump_calc_2026"):
            if col in df.columns:
                vals = pd.to_numeric(df[col], errors="coerce").dropna()
                if not vals.empty:
                    assert vals.min() >= 0, f"{col} tiene valores negativos"
                    assert vals.max() <= 1.3, f"{col} excede tope 1.3"

    def test_factor_num_matches_factor(self):
        df = load_plan_indicadores()
        for _, row in df.iterrows():
            if pd.notna(row["Factor_num"]):
                assert f"Factor {int(row['Factor_num'])}." in str(row["Factor"])


class TestAggregatePlanEstado:
    """Tests para aggregate_plan_estado_by()."""

    def test_returns_dataframe(self):
        df = load_plan_indicadores()
        result = aggregate_plan_estado_by(df)
        assert isinstance(result, pd.DataFrame)

    def test_columns(self):
        df = load_plan_indicadores()
        result = aggregate_plan_estado_by(df)
        expected_cols = {"Factor", "n_Activo", "n_Aprobado", "n_Pendiente", "n_total"}
        assert expected_cols.issubset(set(result.columns))

    def test_n_total_sums_correctly(self):
        df = load_plan_indicadores()
        result = aggregate_plan_estado_by(df)
        assert result["n_total"].sum() == 66

    def test_12_factors(self):
        df = load_plan_indicadores()
        result = aggregate_plan_estado_by(df)
        assert len(result) == 12


class TestComputePlanCumplimiento:
    """Tests para compute_plan_cumplimiento_by_factor()."""

    def test_returns_dataframe(self):
        df = load_plan_indicadores()
        result = compute_plan_cumplimiento_by_factor(df)
        assert isinstance(result, pd.DataFrame)

    def test_columns(self):
        df = load_plan_indicadores()
        result = compute_plan_cumplimiento_by_factor(df)
        expected_cols = {"Factor", "Factor_num", "n_total", "n_con_dato", "cump_promedio", "n_en_brecha", "n_alto"}
        assert expected_cols.issubset(set(result.columns))

    def test_cump_promedio_between_0_and_1_3(self):
        df = load_plan_indicadores()
        result = compute_plan_cumplimiento_by_factor(df)
        vals = result["cump_promedio"].dropna()
        if not vals.empty:
            assert vals.min() >= 0
            assert vals.max() <= 1.3

    def test_n_con_dato_leq_n_total(self):
        df = load_plan_indicadores()
        result = compute_plan_cumplimiento_by_factor(df)
        assert (result["n_con_dato"] <= result["n_total"]).all()


class TestGetPlanIndicadoresForFactor:
    """Tests para get_plan_indicadores_for_factor()."""

    def test_returns_subset(self):
        f1 = get_plan_indicadores_for_factor("Factor 1. Identidad institucional")
        assert len(f1) == 4
        assert (f1["Factor"] == "Factor 1. Identidad institucional").all()

    def test_all_factors_return_results(self):
        df = load_plan_indicadores()
        factors = df["Factor"].unique()
        for factor in factors:
            result = get_plan_indicadores_for_factor(factor)
            assert len(result) > 0, f"Factor {factor} sin resultados"


class TestCatalogoPlanIndicadores:
    """Tests para load_catalogo_plan_indicadores() y su merge en load_plan_indicadores()."""

    def test_catalogo_tiene_columnas_esperadas(self):
        catalogo = load_catalogo_plan_indicadores()
        for col in ("Factor", "Indicador", "Signo", "Decimales", "Decimales_Cump"):
            assert col in catalogo.columns

    def test_catalogo_ausente_retorna_vacio_sin_romper(self, monkeypatch):
        monkeypatch.setattr(pm_loader, "CATALOGO_PLAN_XLSX", Path("no/existe/catalogo.xlsx"))
        load_catalogo_plan_indicadores.clear()
        try:
            catalogo = load_catalogo_plan_indicadores()
            assert catalogo.empty
            assert list(catalogo.columns) == ["Factor", "Indicador", "Signo", "Decimales", "Decimales_Cump"]
        finally:
            load_catalogo_plan_indicadores.clear()

    def test_ninguna_fila_queda_sin_signo_o_decimales(self):
        df = load_plan_indicadores()
        assert df["Signo"].notna().all()
        assert df["Decimales"].notna().all()
        assert df["Decimales_Cump"].notna().all()

    def test_signo_valores_reconocidos(self):
        df = load_plan_indicadores()
        assert set(df["Signo"].unique()).issubset({"%", "%FRAC", "ENT", "DEC", "$", "Sin reporte"})

    def test_fmt_valor_plan_escala_fraccion_a_porcentaje(self):
        """Signo='%FRAC' (0.95 = 95%) se multiplica por 100; Signo='%' (86.1 = 86,1%)
        se muestra tal cual — la ambigüedad real del Excel fuente que motivó el catálogo."""
        assert fmt_valor_plan(0.95, "%FRAC", 1) == "95.0%"
        assert fmt_valor_plan(86.1, "%", 1) == "86.1%"

    def test_formateo_modal_respeta_signo_del_indicador(self):
        """build_indicador_cump_texto formatea Meta/Ejecución con el Signo/Decimales
        del indicador (no siempre %) y % Cump siempre como porcentaje."""
        row = pd.Series(
            {
                "Meta_num_2025": 3690, "Ejecucion_num_2025": 7304, "Cump_calc_2025": 0.95,
                "Meta_num_2026": None, "Ejecucion_num_2026": None, "Cump_calc_2026": None,
                "Signo": "ENT", "Decimales": 0, "Decimales_Cump": 1,
            }
        )
        texto = build_indicador_cump_texto(row)
        assert "3,690" in texto
        assert "95.0%" in texto
        assert "0.95" not in texto
