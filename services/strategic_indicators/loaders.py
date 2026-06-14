"""
services/strategic_indicators/loaders.py — Cargadores de datos

Responsabilidad única: Carga de catálogos y datos desde Excel con caché

Funciones públicas:
  - load_pdi_catalog(): Carga jerarquía PDI (Línea, Objetivo, Meta Estratégica)
  - load_cna_catalog(): Carga jerarquía CNA (Factor, Característica)
  - load_worksheet_flags(): Carga worksheet con flags (Plan Estratégico, CNA, etc)
  - load_cierres(): Carga datos de cierres con cumplimiento y categorización
"""

from pathlib import Path
import pandas as pd
import streamlit as st

from core.config import CACHE_TTL
from core.domain import categorizar_cumplimiento, recalcular_cumplimiento_faltante
from .utils import (
    _get_cached,
    _set_cached,
    _find_col,
    _id_limpio,
    NO_APLICA,
    PENDIENTE,
    METRICA,
)


# Rutas de datos
ROOT = Path(__file__).resolve().parents[2]
RAW_XLSX = ROOT / "data" / "raw" / "Indicadores por CMI.xlsx"
OUT_XLSX = ROOT / "data" / "output" / "Resultados Consolidados.xlsx"


def _resolve_out_xlsx_path() -> Path:
    """Permite override de OUT_XLSX desde la API pública para tests de compatibilidad."""
    try:
        import services.strategic_indicators as public_api

        candidate = getattr(public_api, "OUT_XLSX", OUT_XLSX)
        return Path(candidate)
    except Exception:
        return OUT_XLSX


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_pdi_catalog(include_ids: bool = False) -> pd.DataFrame:
    """
    Carga catálogo PDI (Plan de Desarrollo Institucional) con jerarquía.
    
    Parámetros:
      include_ids: Si True, incluye columna Id
      
    Retorna:
      DataFrame con columnas: Linea, Objetivo, Meta_Estrategica (y Id si requested)
    """
    if not RAW_XLSX.exists():
        base_cols = ["Linea", "Objetivo", "Meta_Estrategica"]
        return pd.DataFrame(columns=(base_cols + ["Id"] if include_ids else base_cols))
    
    try:
        df = pd.read_excel(RAW_XLSX, sheet_name="Worksheet", engine="openpyxl")
    except Exception:
        base_cols = ["Linea", "Objetivo", "Meta_Estrategica"]
        return pd.DataFrame(columns=(base_cols + ["Id"] if include_ids else base_cols))

    df.columns = [str(c).strip() for c in df.columns]
    
    # Buscar columnas con variantes de nombre
    c_linea = _find_col(
        df,
        [
            "Linea",
            "Línea",
            "LINEA",
            "LÍNEA",
            "LINEA ESTRATEGICA",
            "LÍNEA ESTRATÉGICA",
            "Linea estrategica",
        ],
    )
    c_obj = _find_col(
        df,
        [
            "Objetivo",
            "OBJETIVO",
            "OBJETIVO ESTRATEGICO",
            "OBJETIVO ESTRATÉGICO",
            "Objetivo estrategico",
        ],
    )
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
        base_cols = ["Linea", "Objetivo", "Meta_Estrategica"]
        return pd.DataFrame(columns=(base_cols + ["Id"] if include_ids else base_cols))

    c_id = _find_col(df, ["Id", "ID"])

    cols = [c_linea, c_obj] + ([c_meta_est] if c_meta_est else []) + ([c_id] if c_id else [])
    out = df[cols].copy().rename(columns={c_linea: "Linea", c_obj: "Objetivo"})
    
    if c_meta_est:
        out = out.rename(columns={c_meta_est: "Meta_Estrategica"})
    else:
        out["Meta_Estrategica"] = ""

    out["Linea"] = out["Linea"].astype(str).str.strip()
    out["Objetivo"] = out["Objetivo"].astype(str).str.strip()
    out["Meta_Estrategica"] = out["Meta_Estrategica"].astype(str).str.strip()
    
    if c_id:
        out = out.rename(columns={c_id: "Id"})
        out["Id"] = out["Id"].apply(_id_limpio)
    else:
        out["Id"] = ""
    
    out = out[(out["Linea"] != "") & (out["Objetivo"] != "")]
    out["Meta_Estrategica"] = out["Meta_Estrategica"].replace("nan", "")
    
    if not include_ids:
        out = out.drop(columns=["Id"])
        # Deduplicar a 1 fila por (Linea, Objetivo) para evitar
        # duplicación en merges many-to-many (N indicadores × M catálogos).
        out = (
            out.groupby(["Linea", "Objetivo"], as_index=False)
            .agg({"Meta_Estrategica": "first"})
        )

    return out.reset_index(drop=True)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_cna_catalog() -> pd.DataFrame:
    """
    Carga catálogo CNA (Consejo Nacional de Acreditación) con jerarquía Factor/Característica.
    
    Retorna: DataFrame con columnas: Factor, Caracteristica
    """
    if not RAW_XLSX.exists():
        return pd.DataFrame(columns=["Factor", "Caracteristica"])

    try:
        df = pd.read_excel(RAW_XLSX, sheet_name="Worksheet", engine="openpyxl")
    except Exception:
        return pd.DataFrame(columns=["Factor", "Caracteristica"])

    df.columns = [str(c).strip() for c in df.columns]

    c_factor = _find_col(df, ["FACTOR", "Factor"])
    c_car = _find_col(df, ["CARACTERISTICA", "Caracteristica", "CARACTERÍSTICA"])

    if not c_factor or not c_car:
        return pd.DataFrame(columns=["Factor", "Caracteristica"])

    out = df[[c_factor, c_car]].copy().rename(
        columns={c_factor: "Factor", c_car: "Caracteristica"}
    )

    out["Factor"] = out["Factor"].astype(str).str.strip()
    out["Caracteristica"] = out["Caracteristica"].astype(str).str.strip()
    out = out[(out["Factor"] != "") & (out["Caracteristica"] != "")]
    out["Caracteristica"] = out["Caracteristica"].replace("nan", "")

    return out.reset_index(drop=True)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_worksheet_flags() -> pd.DataFrame:
    """
    Carga worksheet con flags para clasificación de indicadores.
    
    Columnas incluidas: Id, Indicador, Linea, Objetivo, Factor, Caracteristica,
                       FlagPlanEstrategico, FlagCNA, Proyecto (opcional), Subproceso (opcional)
                       
    Retorna: DataFrame normalizado con flags
    """
    # Intentar caché manual primero
    cached = _get_cached("worksheet_flags")
    if cached is not None and not cached.empty:
        if (
            {"Linea", "Objetivo"}.issubset(set(cached.columns))
            or {"Factor", "Caracteristica"}.issubset(set(cached.columns))
        ):
            return cached

    # Cargar sin dependencia en st.cache_data
    if not RAW_XLSX.exists():
        return pd.DataFrame()

    try:
        df = pd.read_excel(RAW_XLSX, sheet_name="Worksheet", engine="openpyxl")
    except Exception:
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


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_cierres() -> pd.DataFrame:
    """
    Carga datos de cierres con cumplimiento pre-calculado y categorización.
    
    Fuente: Excel "Cierre historico" o "Consolidado Cierres"
    
    Columnas: Id, Indicador, Fecha, Anio, Mes, Periodo, Meta, Ejecucion, Sentido,
              Tipo_Registro, Meta_Signo, Ejecucion_Signo, Decimales_Meta, Decimales_Ejecucion,
              cumplimiento_dec, cumplimiento_real, cumplimiento_pct, Nivel de cumplimiento
              
    Retorna: DataFrame con cierres normalizados y categorizados
    """
    # Intentar caché manual primero
    cached = _get_cached("cierres")
    if cached is not None and not cached.empty:
        return cached

    out_xlsx = _resolve_out_xlsx_path()
    if not out_xlsx.exists():
        return pd.DataFrame()

    try:
        xl = pd.ExcelFile(out_xlsx, engine="openpyxl")
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

    # Buscar columnas
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
    out["Decimales_Ejecucion"] = (
        pd.to_numeric(df[c_dec_ejec], errors="coerce") if c_dec_ejec else 0
    )
    
    # Alias esperados por la capa de presentación
    out["Decimales"] = out["Decimales_Meta"]
    out["DecimalesEje"] = out["Decimales_Ejecucion"]

    out = out[out["Id"] != ""].copy()

    # Completar Año/Mes desde Fecha cuando no estén informados.
    if "Fecha" in out.columns:
        out.loc[out["Anio"].isna(), "Anio"] = out.loc[out["Anio"].isna(), "Fecha"].dt.year
        out.loc[out["Mes"].isna(), "Mes"] = out.loc[out["Mes"].isna(), "Fecha"].dt.month

    # Leer cumplimiento pre-calculado del Excel.
    c_cumpl = _find_col(df, ["Cumplimiento", "cumplimiento_dec"])
    c_cumpl_real = _find_col(df, ["CumplReal", "Cumplimiento Real", "cumplimiento_real"])

    out["cumplimiento_dec"] = pd.to_numeric(df[c_cumpl], errors="coerce") if c_cumpl else pd.NA
    out["cumplimiento_real"] = (
        pd.to_numeric(df[c_cumpl_real], errors="coerce") if c_cumpl_real else pd.NA
    )

    # Si el Excel no trae cumplimiento, reconstruirlo desde Meta/Ejecucion.
    calcular_mask = out["cumplimiento_dec"].isna() & out["Meta"].notna() & out["Ejecucion"].notna()
    if calcular_mask.any():
        out.loc[calcular_mask, "cumplimiento_dec"] = out.loc[calcular_mask].apply(
            lambda row: recalcular_cumplimiento_faltante(
                row["Meta"],
                row["Ejecucion"],
                row.get("Sentido", "Positivo"),
                row.get("Id"),
            ),
            axis=1,
        )

    out["cumplimiento_pct"] = pd.to_numeric(out["cumplimiento_dec"], errors="coerce") * 100

    # Clasificación de nivel centralizada y consistente con Plan Anual.
    es_metrica = out["Tipo_Registro"].str.lower() == METRICA.lower()
    out["Nivel de cumplimiento"] = out.apply(
        lambda row: categorizar_cumplimiento(row["cumplimiento_dec"], id_indicador=row.get("Id")),
        axis=1,
    )
    out.loc[es_metrica, "Nivel de cumplimiento"] = NO_APLICA
    out.loc[out["cumplimiento_pct"].isna() & ~es_metrica, "Nivel de cumplimiento"] = PENDIENTE

    result = out.reset_index(drop=True)
    _set_cached("cierres", result)
    return result


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_proyectos_consolidados() -> pd.DataFrame:
    """
    Cargador específico para Proyectos desde 'Consolidado Cierres'.
    
    Fuente: data/raw/Resultados_Consolidados_Fuente.xlsx → Hoja 'Consolidado Cierres'
    Se usa el archivo fuente (raw) porque el archivo procesado (output) excluye 
    los IDs de proyectos durante la consolidación del ETL.
    
    Retorna:
        DataFrame con todos los registros de Consolidado Cierres,
        listo para filtrar por proyectos en la capa de presentación.
    """
    raw_source = ROOT / "data" / "raw" / "Resultados_Consolidados_Fuente.xlsx"
    out_xlsx = _resolve_out_xlsx_path()
    
    # Intentar primero el archivo fuente (raw) que contiene proyectos
    source_file = raw_source if raw_source.exists() else out_xlsx
    if not source_file.exists():
        return pd.DataFrame()
    
    try:
        xl = pd.ExcelFile(source_file, engine="openpyxl")
    except Exception:
        return pd.DataFrame()
    
    # Usar "Consolidado Cierres"
    if "Consolidado Cierres" not in xl.sheet_names:
        return pd.DataFrame()
    
    try:
        df = xl.parse("Consolidado Cierres")
    except Exception:
        return pd.DataFrame()
    
    df.columns = [str(c).strip() for c in df.columns]
    
    # Mapear columnas de Consolidado Cierres
    c_id = _find_col(df, ["Id", "ID"])
    c_ind = _find_col(df, ["Indicador"])
    c_linea = _find_col(df, ["Linea", "Línea", "LINEA", "LÍNEA"])
    c_obj = _find_col(df, ["Objetivo", "OBJETIVO"])
    c_fecha = _find_col(df, ["Fecha"])
    c_anio = _find_col(df, ["Año", "Anio", "AÑO"])
    c_mes = _find_col(df, ["Mes"])
    c_periodo = _find_col(df, ["Periodo"])
    c_meta = _find_col(df, ["Meta"])
    c_ejec = _find_col(df, ["Ejecucion", "Ejecución"])
    c_cumpl = _find_col(df, ["Cumplimiento", "cumplimiento_dec"])
    c_cumpl_real = _find_col(df, ["Cumplimiento Real", "CumplReal", "cumplimiento_real"])
    c_sentido = _find_col(df, ["Sentido"])
    c_tipo = _find_col(df, ["Tipo_Registro", "Tipo Registro"])
    c_meta_s = _find_col(df, ["Meta_Signo", "Meta Signo", "Meta s"])
    c_ejec_s = _find_col(df, ["Ejecucion_Signo", "Ejecución_Signo", "Ejecucion s"])
    c_dec_meta = _find_col(df, ["Decimales_Meta", "Decimales", "DecMeta"])
    c_dec_ejec = _find_col(df, ["Decimales_Ejecucion", "DecimalesEje", "DecEjec"])
    
    if not c_id:
        return pd.DataFrame()
    
    # Construir DataFrame de salida
    out = pd.DataFrame()
    out["Id"] = df[c_id].apply(_id_limpio)
    out["Indicador"] = df[c_ind].astype(str).str.strip() if c_ind else None
    out["Linea"] = df[c_linea].astype(str).str.strip() if c_linea else ""
    out["Objetivo"] = df[c_obj].astype(str).str.strip() if c_obj else ""
    out["Fecha"] = pd.to_datetime(df[c_fecha], errors="coerce") if c_fecha else pd.NaT
    out["Anio"] = pd.to_numeric(df[c_anio], errors="coerce") if c_anio else pd.NA
    out["Mes"] = pd.to_numeric(df[c_mes], errors="coerce") if c_mes else pd.NA
    out["Periodo"] = df[c_periodo].astype(str).str.strip() if c_periodo else None
    out["Meta"] = pd.to_numeric(df[c_meta], errors="coerce") if c_meta else pd.NA
    out["Ejecucion"] = pd.to_numeric(df[c_ejec], errors="coerce") if c_ejec else pd.NA
    out["Sentido"] = df[c_sentido].astype(str).str.strip() if c_sentido else "Positivo"
    out["Tipo_Registro"] = df[c_tipo].astype(str).str.strip() if c_tipo else ""
    out["Meta_Signo"] = df[c_meta_s].astype(str).str.strip() if c_meta_s else ""
    out["Ejecucion_Signo"] = df[c_ejec_s].astype(str).str.strip() if c_ejec_s else ""
    out["Decimales_Meta"] = pd.to_numeric(df[c_dec_meta], errors="coerce") if c_dec_meta else 0
    out["Decimales_Ejecucion"] = pd.to_numeric(df[c_dec_ejec], errors="coerce") if c_dec_ejec else 0
    out["Decimales"] = out["Decimales_Meta"]
    out["DecimalesEje"] = out["Decimales_Ejecucion"]
    
    # Cumplimiento
    out["cumplimiento_dec"] = pd.to_numeric(df[c_cumpl], errors="coerce") if c_cumpl else pd.NA
    out["cumplimiento_real"] = pd.to_numeric(df[c_cumpl_real], errors="coerce") if c_cumpl_real else pd.NA
    
    # Recalcular si falta
    calcular_mask = (
        out["cumplimiento_dec"].isna()
        & out["Meta"].notna()
        & out["Ejecucion"].notna()
    )
    if calcular_mask.any():
        out.loc[calcular_mask, "cumplimiento_dec"] = out.loc[calcular_mask].apply(
            lambda row: recalcular_cumplimiento_faltante(
                row["Meta"],
                row["Ejecucion"],
                row.get("Sentido", "Positivo"),
                row.get("Id"),
            ),
            axis=1,
        )
    
    out["cumplimiento_pct"] = pd.to_numeric(out["cumplimiento_dec"], errors="coerce") * 100
    
    # Nivel de cumplimiento
    es_metrica = out["Tipo_Registro"].str.lower() == METRICA.lower()
    out["Nivel de cumplimiento"] = out.apply(
        lambda row: categorizar_cumplimiento(row["cumplimiento_dec"], id_indicador=row.get("Id")),
        axis=1,
    )
    out.loc[es_metrica, "Nivel de cumplimiento"] = NO_APLICA
    out.loc[out["cumplimiento_pct"].isna() & ~es_metrica, "Nivel de cumplimiento"] = PENDIENTE
    
    out = out[out["Id"] != ""].copy()
    return out.reset_index(drop=True)
