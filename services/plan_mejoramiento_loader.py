"""
services/plan_mejoramiento_loader.py — Carga y análisis de dirección CNA

Fuente: data/raw/Plan de mejoramiento/Resultados_Consolidados_CNA_actualizado.xlsx
Hojas usadas: "Metricas" (hecho, largo por Periodo) y "Factor- Caracteristica"
(mapeo canónico Factor→Característica).

Responsabilidad única: cargar el Excel, limpiar/derivar columnas, y calcular
la DIRECCIÓN (aumento/disminución/estable) de Ejecución por Periodo — sin
Meta/Cumplimiento (prácticamente vacíos en la fuente) y sin información de
ficha técnica/formulación del indicador.

Estas son métricas crudas (conteos, totales, montos), no indicadores con una
meta que defina qué dirección es "buena". Por eso la clasificación es
deliberadamente NEUTRA: describe si el valor subió, bajó o se mantuvo, nunca
si eso es favorable o desfavorable (el campo Sentido no se usa para juzgar).

Funciones públicas:
  - load_metricas_raw()
  - load_factor_caracteristica_map()
  - get_factor_options()
  - get_caracteristicas_for_factor()
  - build_indicador_series()
  - compute_trend_table()
  - aggregate_trend_by()
  - compute_evolucion_agregada()
  - compute_evolucion_por_segmento()
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import streamlit as st

from core.config import CACHE_TTL, DATA_RAW

PM_XLSX = DATA_RAW / "Plan de mejoramiento" / "Resultados_Consolidados_CNA_actualizado.xlsx"
SHEET_METRICAS = "Metricas"
SHEET_FACTOR_CARACTERISTICA = "Factor- Caracteristica"

_FACTOR_NUM_RE = re.compile(r"Factor\s+(\d+)", flags=re.IGNORECASE)

METRICAS_COLS = [
    "Id",
    "Indicador",
    "Subindicador",
    "Factor",
    "Caracteristica",
    "Proceso",
    "Periodicidad",
    "Sentido",
    "Fecha",
    "Año",
    "Mes",
    "Periodo",
    "Ejecución",
    "Ejecución s",
    "Llave",
    "DecimalesEje",
    "Proyecto",
]


def _parse_ejecucion(value, unidad: str) -> float | None:
    """Convierte el valor crudo de Ejecución a float, respetando su unidad.

    `unidad` (columna "Ejecución s") ∈ {"ENT", "$", "DEC", "%"} indica cómo
    interpretar/limpiar el valor, pero el resultado siempre es el número tal
    cual reportado (sin dividir % entre 100): el formateo de presentación se
    hace por separado según la unidad.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("$", "").replace("%", "").replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def _split_periodo(periodo: str) -> tuple[int, int]:
    """'2019-1' -> (2019, 1). Valores inválidos ordenan al final."""
    try:
        anio_str, sem_str = str(periodo).split("-")
        return int(anio_str), int(sem_str)
    except (ValueError, AttributeError):
        return 9999, 9


def _factor_num(factor_label: str) -> int | None:
    match = _FACTOR_NUM_RE.search(str(factor_label or ""))
    return int(match.group(1)) if match else None


def _factor_nombre(factor_label: str) -> str:
    text = str(factor_label or "")
    return text.split(".", 1)[1].strip() if "." in text else text.strip()


@st.cache_data(ttl=CACHE_TTL, show_spinner="Cargando Plan de Mejoramiento...")
def load_metricas_raw() -> pd.DataFrame:
    """Carga la hoja Metricas, limpia y deriva columnas de análisis."""
    if not PM_XLSX.exists():
        return pd.DataFrame(columns=METRICAS_COLS)

    df = pd.read_excel(PM_XLSX, sheet_name=SHEET_METRICAS, engine="openpyxl")

    keep = [c for c in METRICAS_COLS if c in df.columns]
    df = df[keep].copy()

    for col in ("Factor", "Caracteristica", "Indicador", "Subindicador", "Periodo", "Sentido", "Proceso", "Periodicidad"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    df["Factor_num"] = df["Factor"].map(_factor_num)
    df["Factor_nombre"] = df["Factor"].map(_factor_nombre)

    periodo_split = df["Periodo"].map(_split_periodo)
    df["Periodo_anio"] = periodo_split.map(lambda t: t[0])
    df["Periodo_sem"] = periodo_split.map(lambda t: t[1])

    df["Ejecucion_num"] = [
        _parse_ejecucion(val, unidad)
        for val, unidad in zip(df.get("Ejecución"), df.get("Ejecución s", pd.Series(dtype=str)))
    ]

    return df.sort_values(["Periodo_anio", "Periodo_sem"]).reset_index(drop=True)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_factor_caracteristica_map() -> pd.DataFrame:
    """Mapeo canónico Factor→Característica (fuente del filtro dependiente)."""
    if not PM_XLSX.exists():
        return pd.DataFrame(columns=["Factor", "Caracteristica"])

    df = pd.read_excel(PM_XLSX, sheet_name=SHEET_FACTOR_CARACTERISTICA, engine="openpyxl")
    df = df.rename(columns={"Características": "Caracteristica", "Característica": "Caracteristica"})
    df = df[["Factor", "Caracteristica"]].copy()
    df["Factor"] = df["Factor"].astype(str).str.strip()
    df["Caracteristica"] = df["Caracteristica"].astype(str).str.strip()
    df["Factor_num"] = df["Factor"].map(_factor_num)
    df["Factor_nombre"] = df["Factor"].map(_factor_nombre)
    return df.drop_duplicates().sort_values(["Factor_num", "Caracteristica"]).reset_index(drop=True)


def get_factor_options() -> list[dict]:
    """Los 12 factores, ordenados por número — fuente única de orden en toda la página."""
    catalog = load_factor_caracteristica_map()
    if catalog.empty:
        return []
    factores = catalog[["Factor_num", "Factor_nombre", "Factor"]].drop_duplicates()
    factores = factores.sort_values("Factor_num")
    return [
        {"num": int(row.Factor_num), "nombre": row.Factor_nombre, "label": row.Factor}
        for row in factores.itertuples()
        if pd.notna(row.Factor_num)
    ]


def get_caracteristicas_for_factor(factor_label: str) -> list[str]:
    """Características canónicas de un Factor (filtro dependiente)."""
    catalog = load_factor_caracteristica_map()
    if catalog.empty:
        return []
    return (
        catalog.loc[catalog["Factor"] == factor_label, "Caracteristica"]
        .drop_duplicates()
        .tolist()
    )


def classify_trend(serie: pd.DataFrame) -> str:
    """Clasifica la DIRECCIÓN comparando los dos últimos periodos con dato.

    Deliberadamente neutro: no evalúa si subir o bajar es "bueno" — son
    métricas crudas (conteos, totales), no indicadores con una meta que
    definiría una dirección deseable.

    `serie`: DataFrame ordenado cronológicamente con columna `Ejecucion_num`.
    Retorna: "aumento" | "disminucion" | "estable" | "sin_datos".
    """
    valores = serie["Ejecucion_num"].dropna()
    if len(valores) < 2:
        return "sin_datos"

    delta = valores.iloc[-1] - valores.iloc[-2]
    if delta == 0:
        return "estable"
    return "aumento" if delta > 0 else "disminucion"


def build_indicador_series(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    """Serie larga (una fila por entidad+Periodo) lista para graficar evolución.

    `group_cols`: ["Indicador"] o ["Indicador", "Subindicador"].
    """
    if df.empty:
        return df

    cols = group_cols + [
        "Periodo", "Periodo_anio", "Periodo_sem",
        "Factor", "Factor_num", "Factor_nombre", "Caracteristica",
        "Ejecucion_num", "Ejecución s", "Sentido",
    ]
    cols = [c for c in cols if c in df.columns]
    serie = df[cols].copy()

    dedup_cols = group_cols + ["Periodo"]
    serie = serie.drop_duplicates(subset=dedup_cols, keep="last")
    return serie.sort_values(group_cols + ["Periodo_anio", "Periodo_sem"]).reset_index(drop=True)


def compute_trend_table(df: pd.DataFrame, level: str) -> pd.DataFrame:
    """Una fila por Indicador (o Subindicador) con su dirección y variación.

    `level`: "indicador" | "subindicador".
    """
    if df.empty:
        return pd.DataFrame()

    group_cols = ["Indicador"] if level == "indicador" else ["Indicador", "Subindicador"]
    serie = build_indicador_series(df, group_cols)
    if serie.empty:
        return pd.DataFrame()

    rows = []
    for keys, grupo in serie.groupby(group_cols, dropna=False):
        keys = keys if isinstance(keys, tuple) else (keys,)
        direccion = classify_trend(grupo)

        valores = grupo["Ejecucion_num"].dropna()
        ultimo_valor = valores.iloc[-1] if not valores.empty else None
        delta_abs = None
        delta_pct = None
        if len(valores) >= 2:
            delta_abs = float(valores.iloc[-1] - valores.iloc[-2])
            previo = valores.iloc[-2]
            delta_pct = float(delta_abs / previo * 100) if previo not in (0, None) else None

        row = dict(zip(group_cols, keys))
        row.update(
            {
                "Factor": grupo["Factor"].dropna().iloc[0] if not grupo["Factor"].dropna().empty else None,
                "Factor_num": grupo["Factor_num"].dropna().iloc[0] if not grupo["Factor_num"].dropna().empty else None,
                "Caracteristica": grupo["Caracteristica"].dropna().iloc[0] if not grupo["Caracteristica"].dropna().empty else None,
                "Sentido": grupo["Sentido"].dropna().iloc[0] if not grupo["Sentido"].dropna().empty else "",
                "Tendencia": direccion,
                "ultimo_periodo": grupo["Periodo"].dropna().iloc[-1] if not grupo["Periodo"].dropna().empty else None,
                "ultimo_valor": ultimo_valor,
                "unidad": grupo["Ejecución s"].dropna().iloc[-1] if not grupo["Ejecución s"].dropna().empty else None,
                "delta_abs": delta_abs,
                "delta_pct": delta_pct,
                "n_periodos": int(len(valores)),
            }
        )
        rows.append(row)

    return pd.DataFrame(rows)


def aggregate_trend_by(df_trend: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Cuenta aumento/disminución/estable/sin_datos por Factor o Característica.

    Puramente descriptivo — NO es un ranking de desempeño: los Factores/
    Características agrupan métricas de naturaleza distinta y no son
    comparables entre sí. El orden de presentación lo decide quien llama
    (normalmente el orden canónico 1→12), no este DataFrame.
    """
    if df_trend.empty or group_col not in df_trend.columns:
        return pd.DataFrame()

    counts = (
        df_trend.groupby(group_col)["Tendencia"]
        .value_counts()
        .unstack(fill_value=0)
        .reindex(columns=["aumento", "disminucion", "estable", "sin_datos"], fill_value=0)
    )
    counts.columns = ["n_aumento", "n_disminucion", "n_estable", "n_sin_datos"]
    counts["n_total"] = counts.sum(axis=1)
    con_dato = counts["n_total"] - counts["n_sin_datos"]

    counts["pct_aumento"] = (counts["n_aumento"] / con_dato.replace(0, pd.NA) * 100).fillna(0.0)
    counts["pct_disminucion"] = (counts["n_disminucion"] / con_dato.replace(0, pd.NA) * 100).fillna(0.0)

    return counts.reset_index()


def compute_evolucion_agregada(df: pd.DataFrame, group_cols: list[str] | None = None) -> pd.DataFrame:
    """% de indicadores en aumento por Periodo (serie agregada de dirección).

    Para cada entidad (Indicador, o Indicador+Subindicador si `group_cols` lo
    incluye) y cada par de periodos consecutivos con dato, clasifica el paso
    como aumento/disminución/estable; agrega el % en aumento por periodo de
    llegada. Es la base de los gráficos de "evolución" — describe dirección,
    no desempeño.
    """
    group_cols = group_cols or ["Indicador"]
    if df.empty:
        return pd.DataFrame(columns=["Periodo", "Periodo_anio", "Periodo_sem", "pct_aumento"])

    serie = build_indicador_series(df, group_cols)
    if serie.empty:
        return pd.DataFrame(columns=["Periodo", "Periodo_anio", "Periodo_sem", "pct_aumento"])

    records = []
    for _, grupo in serie.groupby(group_cols, dropna=False):
        grupo = grupo.sort_values(["Periodo_anio", "Periodo_sem"]).reset_index(drop=True)
        for i in range(1, len(grupo)):
            if pd.isna(grupo.loc[i - 1, "Ejecucion_num"]) or pd.isna(grupo.loc[i, "Ejecucion_num"]):
                continue
            direccion = classify_trend(grupo.iloc[i - 1 : i + 1])
            records.append(
                {
                    "Periodo": grupo.loc[i, "Periodo"],
                    "Periodo_anio": grupo.loc[i, "Periodo_anio"],
                    "Periodo_sem": grupo.loc[i, "Periodo_sem"],
                    "Tendencia": direccion,
                }
            )

    if not records:
        return pd.DataFrame(columns=["Periodo", "Periodo_anio", "Periodo_sem", "pct_aumento"])

    df_rec = pd.DataFrame(records)
    agg = (
        df_rec.groupby(["Periodo", "Periodo_anio", "Periodo_sem"])["Tendencia"]
        .apply(lambda s: float((s == "aumento").mean() * 100))
        .reset_index(name="pct_aumento")
    )
    return agg.sort_values(["Periodo_anio", "Periodo_sem"]).reset_index(drop=True)


def compute_evolucion_por_segmento(df: pd.DataFrame, segment_col: str = "Factor") -> pd.DataFrame:
    """% en aumento por Periodo, desglosado por Factor o Característica.

    Insumo del heatmap Factor×Periodo: una fila por (segmento, periodo) con
    su % de indicadores en aumento — permite ver EN QUÉ periodo cada factor
    subió o bajó, no solo el promedio global.
    """
    if df.empty or segment_col not in df.columns:
        return pd.DataFrame(columns=[segment_col, "Periodo", "Periodo_anio", "Periodo_sem", "pct_aumento"])

    piezas = []
    for valor in df[segment_col].dropna().unique():
        sub = df[df[segment_col] == valor]
        evo = compute_evolucion_agregada(sub)
        if evo.empty:
            continue
        evo = evo.copy()
        evo[segment_col] = valor
        piezas.append(evo)

    if not piezas:
        return pd.DataFrame(columns=[segment_col, "Periodo", "Periodo_anio", "Periodo_sem", "pct_aumento"])

    return pd.concat(piezas, ignore_index=True)
