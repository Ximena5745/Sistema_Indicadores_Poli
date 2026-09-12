"""
services/plan_mejoramiento_loader.py — Carga y análisis de dirección CNA

Dos fuentes INDEPENDIENTES (sin join a nivel indicador):

1) **Métricas CNA** (Resultados_Consolidados_CNA_actualizado.xlsx → hoja "Metricas"):
   Ejecución por Periodo, clasificación NEUTRA aumento/disminución/estable.
   Sin Meta/Cumplimiento (prácticamente vacíos en la fuente).

2) **Indicadores Plan de Mejoramiento** (Indicadores Plan de Mejoramiento.xlsx):
   Meta, Ejecución 2025-2026, % Cumplimiento, Estado, Aprobación.

Llave entre fuentes: SOLO a nivel Factor/Característica (no indicador).
Cruce a nivel indicador: 0 coincidencias exactas (ver docs/metodologia_plan_cna.md).

Funciones públicas Métricas:
  - load_metricas_raw()
  - load_factor_caracteristica_map()
  - get_factor_options()
  - get_caracteristicas_for_factor()
  - build_indicador_series()
  - compute_trend_table()
  - aggregate_trend_by()
  - compute_evolucion_agregada()
  - compute_evolucion_por_segmento()

Funciones públicas Plan:
  - load_plan_indicadores()
  - classify_plan_estado()
  - compute_plan_cumplimiento_by_factor()
  - get_plan_indicadores_for_factor()
  - aggregate_plan_estado_by()
"""

from __future__ import annotations

import re
import unicodedata

import pandas as pd
import streamlit as st

from core.config import CACHE_TTL, DATA_RAW  # noqa: F401

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
    "Meta",
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
    df["Meta_num"] = pd.to_numeric(df.get("Meta"), errors="coerce")

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


# ─────────────────────────────────────────────────────────────────────────────
# PLAN DE MEJORAMIENTO — Indicadores con Meta/Ejecución/%Cump
# ─────────────────────────────────────────────────────────────────────────────

PLAN_XLSX = DATA_RAW / "Plan de mejoramiento" / "Indicadores Plan de Mejoramiento.xlsx"
SHEET_PLAN = "Indicadores Plan de Mejor"


def _norm_text(text: object) -> str:
    """Normaliza texto: minúsculas, sin acentos, espacios colapsados."""
    if pd.isna(text):
        return ""
    s = str(text).strip().lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return " ".join(s.split())


def _parse_meta_ejecucion(value: object) -> float | None:
    """Parsea valores de Meta/Ejecución, descartando texto no numérico."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text or text.lower() in {"n/a", "na", "pendiente", "linea base", "línea base"}:
        return None
    text = text.replace("$", "").replace("%", "").replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def _classify_plan_estado(row: pd.Series) -> str:
    """Clasifica estado combinando 'Estado' y 'Estado de aprobación'.

    Regla (decisión del usuario):
      - Activo:  Estado_aprobación=Aprobado AND (Indicador_o_Metrica=Indicador
                AND tiene Meta o Ejecución numérica en 2025/2026)
      - Aprobado: Estado_aprobación=Aprobado pero sin medición aún
      - Pendiente: Estado_aprobación=Pendiente OR Estado∈{Pendiente,Crear}
                OR Indicador_o_Metrica=Pendiente
    """
    aprob = str(row.get("Estado_Aprobacion", "")).strip()
    tipo = str(row.get("Tipo", "")).strip()

    tiene_medicion = any(
        pd.notna(row.get(c))
        for c in ["Meta_2025", "Ejecucion_2025", "Meta_2026", "Ejecucion_2026"]
    )

    if aprob == "Aprobado" and tipo == "Indicador" and tiene_medicion:
        return "Activo"
    if aprob == "Aprobado":
        return "Aprobado"
    return "Pendiente"


@st.cache_data(ttl=CACHE_TTL, show_spinner="Cargando Indicadores del Plan...")
def load_plan_indicadores() -> pd.DataFrame:
    """Carga el Excel de Indicadores del Plan de Mejoramiento.

    Wide→long: Meta|Ejecución|%Cump × 2025,2026 (+2027-2030 futuros).
    Deriva: Factor_num, Factor_nombre, Estado_final, tiene_medicion,
    Meta_num, Ejecucion_num, Cumplimiento_pct.
    """
    if not PLAN_XLSX.exists():
        return pd.DataFrame()

    df = pd.read_excel(PLAN_XLSX, sheet_name=SHEET_PLAN, header=1, engine="openpyxl")

    # Renombrar columnas con saltos de línea
    df.columns = [str(c).replace("\n", " ").strip() for c in df.columns]

    rename_map = {
        "FACTOR": "Factor",
        "CARACTERÍSTICA": "Caracteristica",
        "ACCIÓN DE MEJORA": "Accion_Mejora",
        "INDICADOR DE RESULTADO O IMPACTO": "Indicador",
        "ID Kawak": "Id_Kawak",
        "Indicador o Metrica": "Tipo",
        "Observación Desempeño": "Observacion",
        "Estado": "Estado_raw",
        "Estado de aprobación": "Estado_Aprobacion",
        "Fórmula": "Formula",
        "Fuente": "Fuente",
        "Responsable de la gestión": "Responsable",
        "PERIODICIDAD DE MEDICIÓN": "Periodicidad",
        "Meta 2025": "Meta_2025",
        "Ejecución 2025": "Ejecucion_2025",
        "% Cump 2025": "Cump_2025",
        "Meta 2026": "Meta_2026",
        "Ejecución 2026": "Ejecucion_2026",
        "% Cump 2026": "Cump_2026",
    }
    # Aplicar solo columnas que existen
    existing = {k: v for k, v in rename_map.items() if k in df.columns}
    df = df.rename(columns=existing)

    # Limpiar strings
    for col in ("Factor", "Caracteristica", "Indicador", "Tipo", "Estado_raw", "Estado_Aprobacion", "Periodicidad"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Derivar Factor_num / Factor_nombre
    if "Factor" in df.columns:
        df["Factor_num"] = df["Factor"].map(_factor_num)
        df["Factor_nombre"] = df["Factor"].map(_factor_nombre)

    # Parsear numéricos Meta/Ejecución/Cumplimiento
    for year in ("2025", "2026"):
        for prefix in ("Meta", "Ejecucion", "Cump"):
            col = f"{prefix}_{year}"
            if col in df.columns:
                if prefix == "Cump":
                    df[f"{prefix}_num_{year}"] = df[col].apply(
                        lambda v: float(v) if isinstance(v, (int, float)) and pd.notna(v) else None
                    )
                else:
                    df[f"{prefix}_num_{year}"] = df[col].apply(_parse_meta_ejecucion)

    # Metas futuras 2027-2030 (solo metas, sin ejecución)
    for year in ("2027", "2028", "2029", "2030"):
        col = str(year)
        if col in df.columns:
            df[f"Meta_num_{year}"] = df[col].apply(_parse_meta_ejecucion)

    # Estado combinado
    if "Estado_raw" in df.columns and "Estado_Aprobacion" in df.columns:
        df["Estado_final"] = df.apply(_classify_plan_estado, axis=1)
    elif "Estado_raw" in df.columns:
        df["Estado_final"] = df["Estado_raw"]
    else:
        df["Estado_final"] = "Sin estado"

    # Flag tiene_medicion
    meta_ejec_cols = [f"Meta_num_{y}" for y in ("2025", "2026")] + [
        f"Ejecucion_num_{y}" for y in ("2025", "2026")
    ]
    existentes = [c for c in meta_ejec_cols if c in df.columns]
    if existentes:
        df["tiene_medicion"] = df[existentes].notna().any(axis=1)
    else:
        df["tiene_medicion"] = False

    # Cumplimiento: solo donde Meta y Ejecución son numéricos
    for year in ("2025", "2026"):
        meta_col = f"Meta_num_{year}"
        ejec_col = f"Ejecucion_num_{year}"
        cump_col = f"Cump_calc_{year}"
        if meta_col in df.columns and ejec_col in df.columns:
            df[cump_col] = None
            mask = df[meta_col].notna() & df[ejec_col].notna() & (df[meta_col] != 0)
            df.loc[mask, cump_col] = (df.loc[mask, ejec_col] / df.loc[mask, meta_col]).clip(upper=1.3)
        else:
            df[cump_col] = None

    return df.sort_values(["Factor_num", "Indicador"]).reset_index(drop=True)


def get_plan_indicadores_for_factor(factor_label: str) -> pd.DataFrame:
    """Retorna los indicadores del Plan filtrados por Factor."""
    df = load_plan_indicadores()
    if df.empty or "Factor" not in df.columns:
        return pd.DataFrame()
    return df[df["Factor"] == factor_label].copy()


def compute_plan_cumplimiento_by_factor(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula cumplimiento promedio por Factor (solo filas con dato).

    Retorna: DataFrame con Factor, Factor_num, n_total, n_con_dato,
    cump_promedio, n_en_brecha (<60%), n_alto (>=90%).
    """
    if df.empty:
        return pd.DataFrame()

    rows = []
    for factor, grupo in df.groupby("Factor", dropna=False):
        nums = [f"Cump_calc_{y}" for y in ("2025", "2026")]
        existentes = [c for c in nums if c in grupo.columns]
        if not existentes:
            continue

        vals = pd.to_numeric(grupo[existentes].stack(), errors="coerce").dropna()
        n_total = len(grupo)
        n_con_dato = len(vals)
        cump_prom = float(vals.mean()) if n_con_dato > 0 else None
        n_en_brecha = int((vals < 0.60).sum()) if n_con_dato > 0 else 0
        n_alto = int((vals >= 0.90).sum()) if n_con_dato > 0 else 0

        fnum = grupo["Factor_num"].dropna().iloc[0] if not grupo["Factor_num"].dropna().empty else None
        rows.append({
            "Factor": factor,
            "Factor_num": fnum,
            "n_total": n_total,
            "n_con_dato": n_con_dato,
            "cump_promedio": cump_prom,
            "n_en_brecha": n_en_brecha,
            "n_alto": n_alto,
        })

    return pd.DataFrame(rows)


def aggregate_plan_estado_by(df: pd.DataFrame, group_col: str = "Factor") -> pd.DataFrame:
    """Cuenta indicadores por Estado_final, desglosado por Factor o general.

    Retorna: DataFrame con group_col, n_Activo, n_Aprobado, n_Pendiente, n_total.
    """
    if df.empty or "Estado_final" not in df.columns:
        return pd.DataFrame()

    counts = (
        df.groupby(group_col)["Estado_final"]
        .value_counts()
        .unstack(fill_value=0)
        .reindex(columns=["Activo", "Aprobado", "Pendiente"], fill_value=0)
    )
    counts.columns = ["n_Activo", "n_Aprobado", "n_Pendiente"]
    counts["n_total"] = counts.sum(axis=1)
    return counts.reset_index()


# ─────────────────────────────────────────────────────────────────────────────
# MÉTRICAS — serie anual completa (vista plana "Métricas" de la pestaña)
# ─────────────────────────────────────────────────────────────────────────────

# Opciones fijas del filtro de tendencia (NO se derivan de los datos): el
# valor "Sin suficiente historia" existe como resultado posible de la
# clasificación pero deliberadamente no es una opción de filtro seleccionable.
TENDENCIA_METRICAS_FILTRO_OPTIONS = ["Toda tendencia", "Creciente", "Decreciente", "Estable"]


def _classify_tendencia_historico(variacion_promedio_pct: float | None, n_anios_con_dato: int) -> str:
    """Clasifica la tendencia de una serie ANUAL completa (no solo el último paso).

    Regla explícita (el mockup de referencia no expone su algoritmo real, solo
    el resultado ya calculado):
      - "Sin suficiente historia" si hay menos de 2 años con dato.
      - "Creciente" si el promedio de variación interanual > +3%.
      - "Decreciente" si < -3%.
      - "Estable" en otro caso.
    """
    if n_anios_con_dato < 2 or variacion_promedio_pct is None or pd.isna(variacion_promedio_pct):
        return "Sin suficiente historia"
    if variacion_promedio_pct > 3:
        return "Creciente"
    if variacion_promedio_pct < -3:
        return "Decreciente"
    return "Estable"


@st.cache_data(ttl=CACHE_TTL, show_spinner="Cargando histórico de Métricas...")
def build_metricas_historico() -> pd.DataFrame:
    """Una fila por (Factor, Característica, Indicador, Subindicador): serie ANUAL
    completa + último valor + variaciones + tendencia. Insumo único de la vista
    plana "Métricas" (reemplaza el drilldown Factor→Característica→Indicador).

    Reshape anual: agrupa `Metricas` por año y toma el ÚLTIMO registro del año
    (regla ya documentada en docs/metodologia_plan_cna.md §6: "Múltiples
    registros por periodo -> keep='last'"), para no mezclar el eje semestral
    crudo de origen con el eje anual de esta vista.
    """
    df = load_metricas_raw()
    if df.empty:
        return pd.DataFrame()

    group_cols = ["Factor", "Factor_num", "Caracteristica", "Indicador", "Subindicador"]
    anual = (
        df.sort_values(["Periodo_anio", "Periodo_sem"])
        .drop_duplicates(subset=group_cols + ["Periodo_anio"], keep="last")
    )

    rows = []
    for keys, grupo in anual.groupby(group_cols, dropna=False):
        grupo = grupo.sort_values("Periodo_anio")

        serie = [
            {"anio": int(anio), "ejecucion": ejec, "meta": meta}
            for anio, ejec, meta in zip(grupo["Periodo_anio"], grupo["Ejecucion_num"], grupo["Meta_num"])
            if pd.notna(anio)
        ]

        con_dato = grupo.dropna(subset=["Ejecucion_num"])
        n_anios_con_dato = len(con_dato)
        ultimo_anio = int(con_dato["Periodo_anio"].iloc[-1]) if n_anios_con_dato else None
        ultimo_valor = con_dato["Ejecucion_num"].iloc[-1] if n_anios_con_dato else None

        variacion_ultima_pct = None
        if n_anios_con_dato >= 2:
            previo = con_dato["Ejecucion_num"].iloc[-2]
            if pd.notna(previo) and previo != 0:
                variacion_ultima_pct = float((con_dato["Ejecucion_num"].iloc[-1] - previo) / previo * 100)

        variaciones = []
        valores_lista = con_dato["Ejecucion_num"].tolist()
        for i in range(1, len(valores_lista)):
            previo, actual = valores_lista[i - 1], valores_lista[i]
            if previo not in (0, None) and pd.notna(previo) and pd.notna(actual):
                variaciones.append((actual - previo) / previo * 100)
        variacion_promedio_pct = float(pd.Series(variaciones).mean()) if variaciones else None

        row = dict(zip(group_cols, keys))
        row.update(
            {
                "Proceso": grupo["Proceso"].dropna().iloc[-1] if not grupo["Proceso"].dropna().empty else None,
                "Sentido": grupo["Sentido"].dropna().iloc[-1] if not grupo["Sentido"].dropna().empty else None,
                "Periodicidad": grupo["Periodicidad"].dropna().iloc[-1] if not grupo["Periodicidad"].dropna().empty else None,
                "serie": serie,
                "ultimo_anio": ultimo_anio,
                "ultimo_valor": ultimo_valor,
                "variacion_ultima_pct": variacion_ultima_pct,
                "variacion_promedio_pct": variacion_promedio_pct,
                "n_anios_con_dato": n_anios_con_dato,
                "tendencia": _classify_tendencia_historico(variacion_promedio_pct, n_anios_con_dato),
            }
        )
        rows.append(row)

    return pd.DataFrame(rows).sort_values("Factor_num").reset_index(drop=True)
