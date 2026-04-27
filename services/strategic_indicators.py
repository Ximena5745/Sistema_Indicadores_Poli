from __future__ import annotations

import unicodedata
from pathlib import Path
import pandas as pd
import streamlit as st

from core.config import (
    CACHE_TTL,
    NIVEL_COLOR,
    UMBRAL_ALERTA,
    UMBRAL_PELIGRO,
    UMBRAL_SOBRECUMPLIMIENTO,
)
from core import calculos as _calculos
from core.semantica import categorizar_cumplimiento

# Caché manual simple (no depende de Streamlit)
_CACHE_MANUAL = {}
_CACHE_TTL_MANUAL = 300  # segundos


def _get_cached(key: str) -> pd.DataFrame | None:
    """Obtener del caché manual si está disponible."""
    if key in _CACHE_MANUAL:
        data, timestamp = _CACHE_MANUAL[key]
        import time

        if time.time() - timestamp < _CACHE_TTL_MANUAL:
            return data
        else:
            del _CACHE_MANUAL[key]
    return None


def _set_cached(key: str, data: pd.DataFrame) -> None:
    """Guardar en caché manual."""
    import time

    _CACHE_MANUAL[key] = (data, time.time())


def _validate_cached_result(df: pd.DataFrame, context: str) -> bool:
    """Valida que caché no retorne DataFrame vacío corrupto."""
    if df.empty:
        # Log para debugging
        import sys

        print(f"WARNING: Caché vacío en {context}, invalidando...", file=sys.stderr)
        return False
    return True


# Aliases decimales para compatibilidad
UMBRAL_ALERTA_DEC = UMBRAL_ALERTA
UMBRAL_PELIGRO_DEC = UMBRAL_PELIGRO
UMBRAL_SOBRECUMPLIMIENTO_DEC = UMBRAL_SOBRECUMPLIMIENTO

ROOT = Path(__file__).resolve().parents[1]
RAW_XLSX = ROOT / "data" / "raw" / "Indicadores por CMI.xlsx"
OUT_XLSX = ROOT / "data" / "output" / "Resultados Consolidados.xlsx"

NO_APLICA = "No aplica"
PENDIENTE = "Pendiente de reporte"
METRICA = "Metrica"
SOBRECUMPLIMIENTO = "Sobrecumplimiento"

NIVEL_COLOR_EXT = {
    **NIVEL_COLOR,
    NO_APLICA: "#78909C",
    PENDIENTE: "#BDBDBD",
}


def _norm_text(value: str) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


def _find_col(df: pd.DataFrame, names: list[str]) -> str | None:
    lookup = {_norm_text(c): c for c in df.columns}
    for name in names:
        hit = lookup.get(_norm_text(name))
        if hit:
            return hit
    return None


def _id_limpio(x) -> str:
    if pd.isna(x):
        return ""
    try:
        f = float(x)
        return str(int(f)) if f == int(f) else str(f)
    except (ValueError, TypeError):
        return str(x).strip()


# ──────────────────────────────────────────────────────────────────────────────
def load_pdi_catalog() -> pd.DataFrame:
    if not RAW_XLSX.exists():
        return pd.DataFrame(columns=["Linea", "Objetivo", "Meta_Estrategica"])
    try:
        df = pd.read_excel(RAW_XLSX, sheet_name="PDI", engine="openpyxl")
    except Exception:
        return pd.DataFrame(columns=["Linea", "Objetivo", "Meta_Estrategica"])

    df.columns = [str(c).strip() for c in df.columns]
    c_linea = _find_col(df, ["LINEA ESTRATEGICA", "LÍNEA ESTRATÉGICA", "Linea estrategica"])
    c_obj = _find_col(df, ["OBJETIVO ESTRATEGICO", "OBJETIVO ESTRATÉGICO", "Objetivo estrategico"])
    c_meta_est = _find_col(
        df,
        [
            "META ESTRATEGICA",
            "META ESTRATÉGICA",
            "Meta estrategica",
            "Meta estratégica",
            "Meta Estratégica",
        ],
    )
    if not c_linea or not c_obj:
        return pd.DataFrame(columns=["Linea", "Objetivo", "Meta_Estrategica"])

    cols = [c_linea, c_obj] + ([c_meta_est] if c_meta_est else [])
    out = df[cols].copy().rename(columns={c_linea: "Linea", c_obj: "Objetivo"})
    if c_meta_est:
        out = out.rename(columns={c_meta_est: "Meta_Estrategica"})
    else:
        out["Meta_Estrategica"] = ""

    out["Linea"] = out["Linea"].astype(str).str.strip()
    out["Objetivo"] = out["Objetivo"].astype(str).str.strip()
    out["Meta_Estrategica"] = out["Meta_Estrategica"].astype(str).str.strip()
    out = out[(out["Linea"] != "") & (out["Objetivo"] != "")]
    return out.drop_duplicates().reset_index(drop=True)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_cna_catalog() -> pd.DataFrame:
    if not RAW_XLSX.exists():
        return pd.DataFrame(columns=["Factor", "Caracteristica"])
    try:
        df = pd.read_excel(RAW_XLSX, sheet_name="CNA", engine="openpyxl")
    except Exception:
        return pd.DataFrame(columns=["Factor", "Caracteristica"])

    df.columns = [str(c).strip() for c in df.columns]
    c_factor = _find_col(df, ["Factor", "FACTOR"])
    c_car = _find_col(
        df, ["Caracteristicas", "Características", "Caracteristica", "CARACTERISTICA"]
    )
    if not c_factor or not c_car:
        return pd.DataFrame(columns=["Factor", "Caracteristica"])

    out = df[[c_factor, c_car]].copy().rename(columns={c_factor: "Factor", c_car: "Caracteristica"})
    out["Factor"] = out["Factor"].astype(str).str.strip()
    out["Caracteristica"] = out["Caracteristica"].astype(str).str.strip()
    out = out[(out["Factor"] != "") & (out["Caracteristica"] != "")]
    return out.drop_duplicates().reset_index(drop=True)


def load_worksheet_flags() -> pd.DataFrame:
    """Cargador de flags con caché manual como fallback."""
    # Intentar caché manual primero
    cached = _get_cached("worksheet_flags")
    if cached is not None and not cached.empty:
        # Evitar reutilizar caché incompleto que rompe mapeo de proyectos por Línea/Objetivo.
        required_min = {"Id", "Indicador"}
        if required_min.issubset(set(cached.columns)) and (
            {"Linea", "Objetivo"}.issubset(set(cached.columns))
            or {"Factor", "Caracteristica"}.issubset(set(cached.columns))
        ):
            return cached

    # Cargar sin dependencia en st.cache_data
    if not RAW_XLSX.exists():
        print("Error: El archivo 'RAW_XLSX' no existe en la ruta esperada.")
        return pd.DataFrame()

    try:
        df = pd.read_excel(RAW_XLSX, sheet_name="Worksheet", engine="openpyxl")
    except Exception as e:
        print(f"Error al cargar la hoja 'Worksheet': {e}")
        return pd.DataFrame()

    df.columns = [str(c).strip() for c in df.columns]

    c_id = _find_col(df, ["Id", "ID"])
    c_ind = _find_col(df, ["Indicador"])
    c_linea = _find_col(
        df,
        [
            "Linea",
            "Línea",
            "LINEA",
            "LÍNEA",
            "Linea estrategica",
            "Línea estratégica",
            "LINEA ESTRATEGICA",
            "LÍNEA ESTRATÉGICA",
        ],
    )
    c_obj = _find_col(
        df,
        [
            "Objetivo",
            "OBJETIVO",
            "Objetivo estrategico",
            "Objetivo estratégico",
            "OBJETIVO ESTRATEGICO",
            "OBJETIVO ESTRATÉGICO",
        ],
    )
    c_factor = _find_col(df, ["FACTOR", "Factor"])
    c_car = _find_col(df, ["CARACTERISTICA", "Caracteristica", "CARACTERÍSTICA"])
    c_plan = _find_col(df, ["Indicadores Plan estrategico"])
    c_cna = _find_col(df, ["CNA"])
    c_proyecto = _find_col(df, ["Proyecto", "PROYECTO"])
    c_subproceso = _find_col(df, ["Subproceso", "SUBPROCESO"])

    needed = [c for c in [c_id, c_ind, c_linea, c_obj, c_factor, c_car, c_plan, c_cna] if c]
    optional_cols = []
    if c_proyecto:
        optional_cols.append(c_proyecto)
    if c_subproceso:
        optional_cols.append(c_subproceso)

    if not needed:
        print("Error: No se encontraron las columnas necesarias en la hoja 'Worksheet'.")
        return pd.DataFrame()

    out = df[needed + optional_cols].copy()
    rename_map = {
        c_id: "Id",
        c_ind: "Indicador",
        c_linea: "Linea",
        c_obj: "Objetivo",
        c_factor: "Factor",
        c_car: "Caracteristica",
        c_plan: "FlagPlanEstrategico",
        c_cna: "FlagCNA",
    }
    if c_proyecto:
        rename_map[c_proyecto] = "Proyecto"
    if c_subproceso:
        rename_map[c_subproceso] = "Subproceso"

    out = out.rename(columns=rename_map)
    _set_cached("worksheet_flags", out)
    return out


def load_cierres() -> pd.DataFrame:
    """Cargador de cierres con caché manual como fallback."""
    # Intentar caché manual primero
    cached = _get_cached("cierres")
    if cached is not None and not cached.empty:
        return cached

    if not OUT_XLSX.exists():
        return pd.DataFrame()

    try:
        xl = pd.ExcelFile(OUT_XLSX, engine="openpyxl")
    except Exception:
        return pd.DataFrame()

    sheet = (
        "Cierre historico"
        if "Cierre historico" in xl.sheet_names
        else ("Consolidado Cierres" if "Consolidado Cierres" in xl.sheet_names else None)
    )
    if not sheet:
        return pd.DataFrame()

    try:
        df = xl.parse(sheet)
    except Exception:
        return pd.DataFrame()

    df.columns = [str(c).strip() for c in df.columns]

    c_id = _find_col(df, ["Id", "ID"])
    c_ind = _find_col(df, ["Indicador"])
    c_fecha = _find_col(df, ["Fecha"])
    c_anio = _find_col(df, ["Año", "Anio"])
    c_mes = _find_col(df, ["Mes"])
    c_periodo = _find_col(df, ["Periodo"])
    c_meta = _find_col(df, ["Meta"])
    c_ejec = _find_col(df, ["Ejecucion", "Ejecución"])
    c_sentido = _find_col(df, ["Sentido"])
    c_tipo = _find_col(df, ["Tipo_Registro", "Tipo Registro"])
    c_meta_s = _find_col(df, ["Meta_Signo", "Meta s", "Meta Signo", "MetaS"])
    c_ejec_s = _find_col(
        df,
        [
            "Ejecucion_Signo",
            "Ejecución s",
            "Ejecucion s",
            "EjecS",
            "Ejecucion Signo",
            "Ejecución Signo",
        ],
    )
    c_dec_meta = _find_col(df, ["Decimales", "Decimales_Meta", "DecMeta"])
    c_dec_ejec = _find_col(df, ["DecimalesEje", "Decimales_Ejecucion", "DecEjec"])

    if not c_id:
        return pd.DataFrame()

    out = pd.DataFrame()
    out["Id"] = df[c_id].apply(_id_limpio)
    out["Indicador"] = df[c_ind].astype(str).str.strip() if c_ind else None
    out["Fecha"] = pd.to_datetime(df[c_fecha], errors="coerce") if c_fecha else pd.NaT
    out["Anio"] = pd.to_numeric(df[c_anio], errors="coerce") if c_anio else pd.NA
    out["Mes"] = pd.to_numeric(df[c_mes], errors="coerce") if c_mes else pd.NA
    out["Periodo"] = df[c_periodo].astype(str).str.strip() if c_periodo else None
    out["Meta"] = pd.to_numeric(df[c_meta], errors="coerce") if c_meta else pd.NA
    out["Ejecucion"] = pd.to_numeric(df[c_ejec], errors="coerce") if c_ejec else pd.NA
    out["Sentido"] = df[c_sentido].astype(str).str.strip() if c_sentido else ""
    out["Tipo_Registro"] = df[c_tipo].astype(str).str.strip() if c_tipo else ""
    out["Meta_Signo"] = df[c_meta_s].astype(str).str.strip() if c_meta_s else ""
    out["Ejecucion_Signo"] = df[c_ejec_s].astype(str).str.strip() if c_ejec_s else ""
    out["Decimales_Meta"] = pd.to_numeric(df[c_dec_meta], errors="coerce") if c_dec_meta else 0
    out["Decimales_Ejecucion"] = pd.to_numeric(df[c_dec_ejec], errors="coerce") if c_dec_ejec else 0
    # Alias esperados por la capa de presentación
    out["Decimales"] = out["Decimales_Meta"]
    out["DecimalesEje"] = out["Decimales_Ejecucion"]

    out = out[out["Id"] != ""].copy()

    # Completar Año/Mes desde Fecha para filas donde no vienen informadas.
    if "Fecha" in out.columns:
        out.loc[out["Anio"].isna(), "Anio"] = out.loc[out["Anio"].isna(), "Fecha"].dt.year
        out.loc[out["Mes"].isna(), "Mes"] = out.loc[out["Mes"].isna(), "Fecha"].dt.month

    # NOTA: Cumplimiento es calculado oficialmente en scripts/etl/cumplimiento.py
    # Los readers leen valores pre-calculados del Excel (cols L, M).
    # NO recalcular aquí. Véase: Problema #4 - Consolidación de cálculos

    # Leer cumplimiento pre-calculado del Excel
    c_cumpl = _find_col(df, ["Cumplimiento", "cumplimiento_dec"])
    c_cumpl_real = _find_col(df, ["CumplReal", "cumplimiento_real"])

    out["cumplimiento_dec"] = pd.to_numeric(df[c_cumpl], errors="coerce") if c_cumpl else pd.NA
    out["cumplimiento_real"] = (
        pd.to_numeric(df[c_cumpl_real], errors="coerce") if c_cumpl_real else pd.NA
    )

    out["cumplimiento_pct"] = pd.to_numeric(out["cumplimiento_dec"], errors="coerce") * 100

    # Detectar si es métrica para establecer "Nivel de cumplimiento"
    es_metrica = out["Tipo_Registro"].str.lower() == METRICA.lower()

    # Problema #5 FIX: Usar categorizar_cumplimiento() directamente (que SÍ considera Plan Anual)
    # en lugar de _nivel_desde_cumplimiento() que era incompleta
    out["Nivel de cumplimiento"] = out.apply(
        lambda row: categorizar_cumplimiento(row["cumplimiento_dec"], id_indicador=row.get("Id")),
        axis=1,
    )
    out.loc[es_metrica, "Nivel de cumplimiento"] = NO_APLICA
    out.loc[out["cumplimiento_pct"].isna() & ~es_metrica, "Nivel de cumplimiento"] = PENDIENTE

    result = out.reset_index(drop=True)

    # Guardar en caché manual
    _set_cached("cierres", result)

    return result


def cierre_por_corte(df_cierres: pd.DataFrame, anio: int, mes: int) -> pd.DataFrame:
    if df_cierres.empty:
        return df_cierres

    df = df_cierres.copy()
    cutoff = int(anio) * 100 + int(mes)
    cutoff_date = pd.Timestamp(int(anio), int(mes), 1) + pd.offsets.MonthEnd(0)

    if "Anio" in df.columns and "Mes" in df.columns:
        ym = pd.to_numeric(df["Anio"], errors="coerce") * 100 + pd.to_numeric(
            df["Mes"], errors="coerce"
        )
        by_period = ym.notna() & (ym <= cutoff)
        if "Fecha" in df.columns:
            by_date = (
                ym.isna()
                & df["Fecha"].notna()
                & (pd.to_datetime(df["Fecha"], errors="coerce") <= cutoff_date)
            )
            df = df[by_period | by_date].copy()
        else:
            df = df[by_period].copy()
    elif "Fecha" in df.columns:
        df = df[pd.to_datetime(df["Fecha"], errors="coerce") <= cutoff_date].copy()

    if df.empty:
        return df

    if "Fecha" in df.columns:
        df = df.sort_values(["Id", "Fecha"]).drop_duplicates(subset=["Id"], keep="last")
    else:
        df = df.drop_duplicates(subset=["Id"], keep="last")
    return df.reset_index(drop=True)


def _preparar_indicadores_con_cierre(
    anio: int,
    mes: int,
    flag_column: str,
    catalog_loader,
    catalog_merge_cols: list,
) -> pd.DataFrame:
    """
    Función GENÉRICA para preparar indicadores estratégicos con cierre (PDI o CNA).

    Problema #6 FIX: Consolidación de preparar_pdi_con_cierre + preparar_cna_con_cierre.

    PARÁMETROS:
      anio: Año a consultar
      mes: Mes a consultar
      flag_column: Nombre columna de flag ("FlagPlanEstrategico", "FlagCNA", etc.)
      catalog_loader: Función que carga el catálogo (load_pdi_catalog, load_cna_catalog)
      catalog_merge_cols: Lista de columnas para merge del catálogo
                         ej: ["Linea", "Objetivo"] para PDI
                         ej: ["Factor", "Caracteristica"] para CNA

    RETORNA:
      DataFrame con indicadores enriquecidos + cierre + catálogo
    """
    base = load_worksheet_flags()
    catalog = catalog_loader()
    cierres = load_cierres()

    if base.empty or cierres.empty:
        return pd.DataFrame()

    def _normalize_flag_series(series: pd.Series) -> pd.Series:
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.isna().any():
            raw = series.astype(str).str.strip().str.lower()
            mapped = raw.map(
                {
                    "1": 1,
                    "1.0": 1,
                    "si": 1,
                    "true": 1,
                    "x": 1,
                    "0": 0,
                    "0.0": 0,
                    "no": 0,
                    "false": 0,
                    "": 0,
                }
            )
            numeric = numeric.fillna(mapped)
        return numeric

    def _normalize_id_value(val) -> str:
        if pd.isna(val):
            return ""
        if isinstance(val, int):
            return str(val)
        if isinstance(val, float):
            return str(int(val)) if val.is_integer() else str(val).strip()
        text = str(val).strip()
        try:
            num = float(text)
            if num.is_integer():
                return str(int(num))
        except Exception:
            return text
        return text

    # Filtrar por flag especifico
    if flag_column not in base.columns:
        return pd.DataFrame()

    flag_vals = _normalize_flag_series(base[flag_column])
    indicators = base[flag_vals == 1].copy()
    if indicators.empty:
        return pd.DataFrame()

    # Excluir proyectos
    if "Proyecto" in indicators.columns:
        proyecto_vals = _normalize_flag_series(indicators["Proyecto"])
        indicators = indicators[proyecto_vals != 1].copy()
    if indicators.empty:
        return pd.DataFrame()

    close = cierre_por_corte(cierres, anio, mes)

    # Cols estándar de cierre
    cols_close = [
        "Id",
        "Indicador",
        "cumplimiento_pct",
        "Nivel de cumplimiento",
        "Anio",
        "Mes",
        "Fecha",
    ]
    for _ec in [
        "Meta",
        "Ejecucion",
        "Sentido",
        "Meta_Signo",
        "Ejecucion_Signo",
        "Decimales",
        "DecimalesEje",
        "Decimales_Meta",
        "Decimales_Ejecucion",
    ]:
        if _ec in close.columns:
            cols_close.append(_ec)

    # Merge con cierre (normalizando Id para evitar desalineacion por tipos)
    indicators = indicators.copy()
    close = close.copy()
    indicators["_Id_norm"] = indicators["Id"].map(_normalize_id_value)
    close["_Id_norm"] = close["Id"].map(_normalize_id_value)

    merged = indicators.merge(
        close[cols_close + ["_Id_norm"]],
        on="_Id_norm",
        how="left",
        suffixes=("", "_cierre"),
    ).drop(columns=["_Id_norm"])

    # Unificar Indicador desde cierre si falta
    if "Indicador_cierre" in merged.columns:
        merged["Indicador"] = merged["Indicador"].fillna(merged["Indicador_cierre"])
        merged = merged.drop(columns=["Indicador_cierre"])

    # Merge con catálogo si existen las columnas
    if not catalog.empty and all(c in merged.columns for c in catalog_merge_cols):
        merged = merged.merge(catalog, on=catalog_merge_cols, how="left")

    # Normalizar cumplimiento_pct
    if not merged.empty:
        merged["cumplimiento_pct"] = pd.to_numeric(merged.get("cumplimiento_pct"), errors="coerce")
        merged["Nivel de cumplimiento"] = merged["Nivel de cumplimiento"].fillna(PENDIENTE)

        # Filtrar filas sin datos de origen
        def _has_source(row):
            for c in ["Meta", "Ejecucion", "Cumplimiento"]:
                if c in merged.columns:
                    v = row.get(c)
                    if pd.notna(v) and str(v).strip() != "":
                        return True
            return False

        merged = merged[merged.apply(_has_source, axis=1)].reset_index(drop=True)

    return merged


def preparar_pdi_con_cierre(anio: int, mes: int) -> pd.DataFrame:
    """
    Preparar indicadores Plan Estratégico (PDI) con cierre.

    Problema #6 FIX: Ahora usa función genérica _preparar_indicadores_con_cierre.
    """
    return _preparar_indicadores_con_cierre(
        anio,
        mes,
        flag_column="FlagPlanEstrategico",
        catalog_loader=load_pdi_catalog,
        catalog_merge_cols=["Linea", "Objetivo"],
    )


def preparar_cna_con_cierre(anio: int, mes: int) -> pd.DataFrame:
    """
    Preparar indicadores CNA con cierre.

    Problema #6 FIX: Ahora usa función genérica _preparar_indicadores_con_cierre.
    """
    return _preparar_indicadores_con_cierre(
        anio,
        mes,
        flag_column="FlagCNA",
        catalog_loader=load_cna_catalog,
        catalog_merge_cols=["Factor", "Caracteristica"],
    )


# ──────────────────────────────────────────────────────────────────────────────
