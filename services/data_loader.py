"""
services/data_loader.py — Carga de datos desde xlsx con caché st.cache_data.

REFACTORIZACIÓN PHASE 2:
  - Utilidades: services/loaders/utils.py
  - Pipeline ETL (5 fases): services/loaders/pipeline.py
  - Archivo original (541L) → 380L+ (después extracciones)
  - data_loader.py = Wrapper de caché Streamlit + Loaders públicas

Fuente principal general: data/output/Resultados Consolidados.xlsx (hoja Consolidado Semestral).
Excepción: Gestión OM consume Consolidado Historico desde cargar_dataset_historico().

Regla de capas:
  - Lógica pura          → core/calculos.py
  - Configuración        → core/config.py
  - Carga con caché Streamlit → aquí (services/)
  - Mapeos de procesos   → services/procesos.py (desde config/mapeos_procesos.yaml)
"""

import streamlit as st
import pandas as pd
from pathlib import Path

from core.config import DATA_RAW, DATA_OUTPUT
from core.calculos import estado_tiempo_acciones

# Import utilidades y pipeline refactorizados
from services.loaders.utils import renombrar_columnas, id_a_str, obtener_rename_map, ascii_lower
from services.loaders.pipeline import ejecutar_pipeline_completo


# Re-export para backward compatibility
_RENAME = obtener_rename_map()

# Backward compatibility: mantener funciones privadas antiguas como aliases
_ascii_lower = ascii_lower
_renombrar = renombrar_columnas
_id_a_str = id_a_str


def _cargar_mapa_proceso_padre() -> dict:
    """DEPRECADO (11-abr-2026): usar services.procesos.obtener_proceso_padre() en su lugar."""
    from services.procesos import cargar_mapeos_procesos
    return cargar_mapeos_procesos()


# ═════════════════════════════════════════════════════════════════════════════
# ETL PIPELINE: 5 FASES CLARAMENTE SEPARADAS
# ═════════════════════════════════════════════════════════════════════════════
#


# ═════════════════════════════════════════════════════════════════════════════
# WRAPPERS DE CACHÉ STREAMLIT
# ═════════════════════════════════════════════════════════════════════════════


@st.cache_data(ttl=300, show_spinner="Cargando datos principales...")
def cargar_dataset() -> pd.DataFrame:
    """
    Carga el dataset principal desde Resultados Consolidados.xlsx (fuente oficial).
    
    Pipeline ETL completo (5 fases): services/loaders/pipeline.py
    """
    path = DATA_OUTPUT / "Resultados Consolidados.xlsx"
    if not path.exists():
        st.error(f"Archivo no encontrado: {path}")
        return pd.DataFrame()

    try:
        return ejecutar_pipeline_completo(path, es_historico=False)
    except Exception as e:
        st.error(f"Error cargando dataset: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner="Cargando datos históricos para Gestión OM...")
def cargar_dataset_historico() -> pd.DataFrame:
    """
    Carga la hoja Consolidado Historico para casos específicos de Gestión OM.
    Usa el mismo pipeline pero con FASE 1 histórica.
    """
    path = DATA_OUTPUT / "Resultados Consolidados.xlsx"
    if not path.exists():
        return pd.DataFrame()

    try:
        return ejecutar_pipeline_completo(path, es_historico=True)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner="Cargando acciones de mejora...")
def cargar_acciones_mejora() -> pd.DataFrame:
    path = DATA_RAW / "acciones_mejora.xlsx"
    if not path.exists():
        st.error(f"Archivo no encontrado: {path}")
        return pd.DataFrame()

    df = pd.read_excel(path, sheet_name="Acciones", engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]

    for col in ["FECHA_IDENTIFICACION", "FECHA_ESTIMADA_CIERRE", "FECHA_CIERRE", "FECHA_CREACION"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    for col in ["DIAS_VENCIDA", "MESES_SIN_AVANCE", "AVANCE"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = estado_tiempo_acciones(df)
    return df


@st.cache_data(ttl=300, show_spinner="Cargando ficha técnica...")
def cargar_ficha_tecnica() -> pd.DataFrame:
    path = DATA_RAW / "Ficha_Tecnica.xlsx"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_excel(path, sheet_name="Hoja1", engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]
    if "Id Ind" in df.columns:
        df["Id"] = df["Id Ind"].apply(id_a_str)
    return df


def _leer_excel(path: Path, header: int = 0) -> pd.DataFrame:
    """Lee .xlsx (openpyxl) o .xls (xlrd) con preferencia por .xlsx."""
    xlsx = path.with_suffix(".xlsx")
    if path.suffix.lower() == ".xls" and xlsx.exists():
        path = xlsx
    ext = path.suffix.lower()
    if ext == ".xlsx":
        return pd.read_excel(str(path), header=header, engine="openpyxl")
    return pd.read_excel(str(path), header=header, engine="xlrd")


@st.cache_data(ttl=300, show_spinner="Cargando Oportunidades de Mejora...")
def cargar_om() -> pd.DataFrame:
    """Carga OM.xlsx (preferido) o OM.xls. Encabezados en fila 8 (header=7)."""
    xlsx = DATA_RAW / "OM.xlsx"
    xls = DATA_RAW / "OM.xls"

    if xlsx.exists():
        path, header = xlsx, 7
    elif xls.exists():
        path, header = xls, 7
    else:
        return pd.DataFrame()

    try:
        engine = "openpyxl" if path.suffix.lower() == ".xlsx" else "xlrd"
        df = pd.read_excel(str(path), header=header, engine=engine)
    except Exception as e:
        st.error(f"Error leyendo {path.name}: {e}")
        return pd.DataFrame()

    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all").reset_index(drop=True)

    if "Id" in df.columns:
        df = df[df["Id"].notna() & (df["Id"].astype(str).str.strip() != "")].reset_index(drop=True)
        df["Id"] = df["Id"].apply(id_a_str)

    for col in [
        "Fecha de identificación",
        "Fecha de creación",
        "Fecha estimada de cierre",
        "Fecha real de cierre",
    ]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    col_av = next((c for c in df.columns if "avance" in c.lower()), None)
    if col_av:
        df[col_av] = pd.to_numeric(df[col_av], errors="coerce")
        mask = df[col_av].notna()
        if mask.any() and df.loc[mask, col_av].max() <= 1.5:
            df[col_av] = df[col_av] * 100

    return df


@st.cache_data(ttl=300, show_spinner="Cargando Plan de Acción...")
def cargar_plan_accion() -> pd.DataFrame:
    """Consolida todos los archivos de data/raw/Plan de accion/. Prioriza .xlsx sobre .xls."""
    folder = DATA_RAW / "Plan de accion"
    if not folder.exists():
        return pd.DataFrame()

    xlsx_stems = {p.stem for p in folder.glob("*.xlsx")}
    archivos = []
    for p in sorted(folder.iterdir()):
        ext = p.suffix.lower()
        if ext == ".xlsx":
            archivos.append(p)
        elif ext == ".xls" and p.stem not in xlsx_stems:
            archivos.append(p)

    frames = []
    for p in archivos:
        try:
            engine = "openpyxl" if p.suffix.lower() == ".xlsx" else "xlrd"
            df = pd.read_excel(str(p), engine=engine)
            df.columns = [str(c).strip() for c in df.columns]
            df = df.dropna(how="all").reset_index(drop=True)
            frames.append(df)
        except Exception as e:
            print(f"[data_loader] No se pudo leer {p.name}: {e}")

    if not frames:
        return pd.DataFrame()

    df_all = pd.concat(frames, ignore_index=True)

    for col in df_all.columns:
        if any(kw in col.lower() for kw in ["fecha", "ejecuci", "seguimiento", "evaluaci"]):
            try:
                df_all[col] = pd.to_datetime(df_all[col], errors="coerce")
            except Exception:
                pass

    col_av = next((c for c in df_all.columns if "avance" in c.lower()), None)
    if col_av:
        df_all[col_av] = pd.to_numeric(df_all[col_av], errors="coerce")
        mask = df_all[col_av].notna()
        if mask.any() and df_all.loc[mask, col_av].max() <= 1.5:
            df_all[col_av] = df_all[col_av] * 100

    for col in df_all.columns:
        if "id oportunidad" in col.lower():
            df_all[col] = df_all[col].apply(id_a_str)

    return df_all


@st.cache_data(ttl=300, show_spinner=False)
def cargar_analisis_usuarios() -> pd.DataFrame:
    """
    Carga la hoja 'Desglose Analisis' de Resultados Consolidados.xlsx.
    Retorna columnas: Id (str), fecha, analisis_fecha, analisis_autor, analisis_texto.
    """
    path = DATA_OUTPUT / "Resultados Consolidados.xlsx"
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_excel(path, sheet_name="Desglose Analisis", engine="openpyxl")
        df.columns = [str(c).strip() for c in df.columns]
        if "Id" in df.columns:
            df["Id"] = df["Id"].apply(id_a_str)
        for col in ("analisis_fecha", "fecha"):
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()


def df_indicadores_unicos(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna un registro único por Id (el más reciente por Fecha)."""
    if df.empty or "Id" not in df.columns:
        return df
    if "Revisar" in df.columns:
        revisar = pd.to_numeric(df["Revisar"], errors="coerce").fillna(0)
        return df[revisar == 1].drop_duplicates(subset="Id", keep="first").reset_index(drop=True)
    col_fecha = "Fecha" if "Fecha" in df.columns else None
    if col_fecha:
        return (
            df.sort_values(col_fecha)
            .drop_duplicates(subset="Id", keep="last")
            .reset_index(drop=True)
        )
    return df.drop_duplicates(subset="Id", keep="last").reset_index(drop=True)


def construir_opciones_indicadores(df: pd.DataFrame) -> dict:
    """Retorna dict {label: id_str} con etiquetas 'Id — Nombre' únicas."""
    if df.empty or "Id" not in df.columns:
        return {}
    unicos = df_indicadores_unicos(df)
    sub = unicos[["Id", "Indicador"]].dropna(subset=["Id"])
    sub = sub[sub["Id"] != ""]
    opciones = {}
    for _, row in sub.iterrows():
        label = f"{row['Id']} — {row.get('Indicador', '')}"
        opciones[label] = row["Id"]
    return dict(sorted(opciones.items()))


# ── Metadatos Kawak para Ficha Técnica ────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def cargar_metadatos_kawak() -> pd.DataFrame:
    """
    Carga metadatos de indicadores desde tres fuentes Kawak para la ficha técnica.

    Fuentes:
      - Consolidado_API_Kawak.xlsx  → descripcion, responsable (registro más reciente por Id)
      - Ficha_Tecnica_Indicadores.xlsx → Formula (vacío si no hay datos)
      - Indicadores Kawak.xlsx        → Periodicidad (año más reciente por Id)

    Retorna un DataFrame con columnas: Id, descripcion, responsable, Formula, Periodicidad
    (una fila por Id, con la información más actualizada disponible).
    """
    FUENTES = DATA_RAW / "Fuentes Consolidadas"
    result: pd.DataFrame = pd.DataFrame()

    # ── 1. Consolidado_API_Kawak.xlsx → descripcion, responsable ──────────────
    api_path = FUENTES / "Consolidado_API_Kawak.xlsx"
    if api_path.exists():
        try:
            df_api = pd.read_excel(api_path, engine="openpyxl")
            df_api.columns = [str(c).strip() for c in df_api.columns]
            df_api = df_api.rename(columns={"ID": "Id"})
            df_api["Id"] = df_api["Id"].apply(_id_a_str)
            if "fecha" in df_api.columns:
                df_api["fecha"] = pd.to_datetime(df_api["fecha"], errors="coerce")
                df_api = df_api.sort_values("fecha", ascending=False)
            cols_api = ["Id"] + [c for c in ["descripcion", "responsable"] if c in df_api.columns]
            result = df_api[cols_api].drop_duplicates(subset=["Id"], keep="first").reset_index(drop=True)
        except Exception:
            pass

    # ── 2. 'Ficha Tecnica Detalle' (directorio maestro dedicado) → Formula ───
    # Desde la fusión 2026-07-14 (antes 'Ficha_Tecnica_Indicadores.xlsx',
    # archivado en data/raw/_archivados/).
    ficha_path = DATA_RAW / "Catalogo de Indicadores.xlsx"
    if ficha_path.exists():
        try:
            df_ficha = pd.read_excel(ficha_path, sheet_name="Ficha Tecnica Detalle", engine="openpyxl")
            df_ficha.columns = [str(c).strip() for c in df_ficha.columns]
            id_col = next(
                (c for c in ["Id", "ID Kawak", "Id Ind"] if c in df_ficha.columns), None
            )
            if id_col and "Formula" in df_ficha.columns:
                df_ficha = (
                    df_ficha[[id_col, "Formula"]]
                    .rename(columns={id_col: "Id"})
                    .copy()
                )
                df_ficha["Id"] = df_ficha["Id"].apply(_id_a_str)
                df_ficha = df_ficha.drop_duplicates(subset=["Id"], keep="first")
                if result.empty:
                    result = df_ficha
                else:
                    result = result.merge(df_ficha, on="Id", how="left")
        except Exception:
            pass

    # ── 3. Indicadores Kawak.xlsx → Periodicidad (año más reciente) ───────────
    kawak_path = FUENTES / "Indicadores Kawak.xlsx"
    if kawak_path.exists():
        try:
            df_kw = pd.read_excel(kawak_path, engine="openpyxl")
            df_kw.columns = [str(c).strip() for c in df_kw.columns]
            df_kw["Id"] = df_kw["Id"].apply(_id_a_str)
            if "Año" in df_kw.columns:
                df_kw = df_kw.sort_values("Año", ascending=False)
            cols_kw = ["Id"] + [c for c in ["Periodicidad"] if c in df_kw.columns]
            df_kw = df_kw[cols_kw].drop_duplicates(subset=["Id"], keep="first")
            if result.empty:
                result = df_kw
            else:
                result = result.merge(df_kw, on="Id", how="left")
        except Exception:
            pass

    return result
