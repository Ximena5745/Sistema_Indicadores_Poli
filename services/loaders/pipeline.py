"""
services/loaders/pipeline.py — ETL PIPELINE (5 FASES)

Módulo de transformación de datos con 5 fases claramente separadas:

FASE 1: Lectura (IO)
  - Leer Excel, renombrar columnas, normalizar IDs

FASE 2: Enriquecimiento Primario
  - JOIN con Catálogo Indicadores

FASE 3: Enriquecimiento Secundario
  - JOIN con CMI + mapeo de procesos maestros

FASE 4: Reconstrucción de Fórmulas
  - Calcular Año, Mes, Período desde Fecha

FASE 5: Cálculos y Categorización
  - Normalizar y categorizar cumplimiento

IMPORTAR:
  from services.loaders.pipeline import (
      fase1_leer_consolidado_semestral,
      fase5_aplicar_calculos_cumplimiento,
      ejecutar_pipeline_completo,
  )
"""

import pandas as pd
from pathlib import Path

from core.calculos import normalizar_cumplimiento
from core.domain import categorizar_cumplimiento, recalcular_cumplimiento_faltante
from core.config import DATA_RAW
from services.procesos import obtener_proceso_padre
from services.loaders.utils import renombrar_columnas, id_a_str, obtener_rename_map

# Import data validation skill
try:
    import sys
    skill_path = Path(__file__).resolve().parent.parent.parent / ".github" / "skills" / "data-validation"
    if skill_path.exists():
        sys.path.insert(0, str(skill_path))
    from data_validation import enrich_with_process_hierarchy
except ImportError:
    def enrich_with_process_hierarchy(df, path):
        return df


# ═════════════════════════════════════════════════════════════════════════════
# FASE 1: LECTURA (IO)
# Responsabilidad única: Leer Excel + renombrar columnas + normalizar IDs
# ═════════════════════════════════════════════════════════════════════════════


def fase1_leer_consolidado_semestral(path: Path) -> pd.DataFrame:
    """
    FASE 1 - Lectura: Leer hoja principal y normalizar.

    Entrada: Ruta a Resultados Consolidados.xlsx
    Salida: DataFrame crudo con columnas normalizadas e IDs como string
    Efectos: Solo IO, sin transformaciones de negocio
    """
    df = pd.read_excel(path, sheet_name="Consolidado Semestral", engine="openpyxl")
    df = renombrar_columnas(df, obtener_rename_map())
    if "Id" in df.columns:
        df["Id"] = df["Id"].apply(id_a_str)
    return df


def fase1_leer_consolidado_historico(path: Path) -> pd.DataFrame:
    """
    FASE 1 - Lectura (histórico): Leer hoja histórico y normalizar.

    Entrada: Ruta a Resultados Consolidados.xlsx
    Salida: DataFrame histórico con columnas normalizadas
    Nota: Usada solo por cargar_dataset_historico() para Gestión OM
    """
    df = pd.read_excel(path, sheet_name="Consolidado Historico", engine="openpyxl")
    df = renombrar_columnas(df, obtener_rename_map())
    if "Id" in df.columns:
        df["Id"] = df["Id"].apply(id_a_str)
    return df


# ═════════════════════════════════════════════════════════════════════════════
# FASE 2: ENRIQUECIMIENTO PRIMARIO
# Responsabilidad única: JOIN con Catálogo Indicadores
# ═════════════════════════════════════════════════════════════════════════════


def fase2_enriquecer_clasificacion(df: pd.DataFrame, path: Path) -> pd.DataFrame:
    """
    FASE 2 - Enriquecimiento Primario: JOIN con Catálogo Indicadores.

    Entrada: DataFrame de FASE 1
    Salida: DataFrame con columna Clasificación enriquecida
    Efectos: Agrega metadatos desde Catálogo (si falta)
    """
    if "Clasificacion" in df.columns:
        return df
    try:
        df_cat = pd.read_excel(path, sheet_name="Catalogo Indicadores", engine="openpyxl")
        df_cat["Id"] = df_cat["Id"].apply(id_a_str)
        cols_cat = ["Id"] + [c for c in ["Clasificacion"] if c in df_cat.columns]
        if len(cols_cat) > 1:
            df = df.merge(df_cat[cols_cat].drop_duplicates("Id"), on="Id", how="left")
    except Exception:
        pass
    return df


# ═════════════════════════════════════════════════════════════════════════════
# FASE 3: ENRIQUECIMIENTO SECUNDARIO
# Responsabilidad única: JOIN con CMI + mapeo Procesos maestros
# ═════════════════════════════════════════════════════════════════════════════


def fase3_enriquecer_cmi_y_procesos(df: pd.DataFrame) -> pd.DataFrame:
    """
    FASE 3 - Enriquecimiento Secundario: JOIN CMI y mapeo de procesos.

    Entrada: DataFrame de FASE 2
    Salida: DataFrame con Subproceso, Línea, Objetivo, Proceso Padre
    Efectos: Agrega jerarquía de procesos (CMI + mapeo YAML)
    """
    # CMI — NO se toma Sentido (puede estar desactualizado respecto a Kawak)
    # Desde la fusión 2026-07-14, vive en 'Catalogo Indicadores' del directorio
    # maestro dedicado (antes 'Indicadores por CMI.xlsx', archivado en
    # data/raw/_archivados/).
    try:
        df_cmi = pd.read_excel(
            DATA_RAW / "Catalogo de Indicadores.xlsx",
            sheet_name="Catalogo Indicadores",
            engine="openpyxl",
        )
        df_cmi = renombrar_columnas(df_cmi, obtener_rename_map())
        df_cmi = df_cmi.rename(columns={
            "Linea_Estrategica": "Linea", "Objetivo_Estrategico": "Objetivo",
        })
        df_cmi["Id"] = df_cmi["Id"].apply(id_a_str)
        cols_cmi = ["Id"] + [c for c in ["Subproceso", "Linea", "Objetivo"] if c in df_cmi.columns]
        if len(cols_cmi) > 1:
            df = df.merge(df_cmi[cols_cmi].drop_duplicates("Id"), on="Id", how="left")
    except Exception:
        pass

    # Jerarquía de procesos oficial (Data Validation Skill)
    df = enrich_with_process_hierarchy(df, DATA_RAW / "Subproceso-Proceso-Area.xlsx")

    # Proceso padre desde YAML
    if "Proceso" in df.columns:
        df["ProcesoPadre"] = df["Proceso"].apply(obtener_proceso_padre)

    return df


# ═════════════════════════════════════════════════════════════════════════════
# FASE 4: RECONSTRUCCIÓN DE FÓRMULAS
# Responsabilidad única: Calcular Año, Mes, Período desde Fecha
# ═════════════════════════════════════════════════════════════════════════════


def fase4_reconstruir_columnas_formula(df: pd.DataFrame) -> pd.DataFrame:
    """
    FASE 4 - Reconstrucción de Fórmulas: Calcular Año, Mes, Período desde Fecha.

    Entrada: DataFrame de FASE 3
    Salida: DataFrame con columnas temporales completas
    Efectos: Rellena campos faltantes desde Fecha (fuente confiable)
    """
    if "Fecha" not in df.columns:
        return df

    _fecha = pd.to_datetime(df["Fecha"], errors="coerce")
    _MESES_ES = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
    }

    if "Año" in df.columns:
        df["Año"] = df["Año"].fillna(_fecha.dt.year)

    if "Mes" in df.columns:
        df["Mes"] = df["Mes"].where(
            df["Mes"].notna() & (df["Mes"] != ""),
            _fecha.dt.month.map(_MESES_ES),
        )

    _periodo_calc = (
        _fecha.dt.year.astype("Int64").astype(str)
        + "-"
        + _fecha.dt.month.apply(lambda m: "1" if m <= 6 else "2")
    )

    if "Periodo" in df.columns:
        df["Periodo"] = df["Periodo"].where(
            df["Periodo"].notna() & (df["Periodo"] != ""), _periodo_calc
        )
    else:
        df["Periodo"] = _periodo_calc

    return df


# ═════════════════════════════════════════════════════════════════════════════
# FASE 5: CÁLCULOS Y CATEGORIZACIÓN
# Responsabilidad única: Normalizar y categorizar cumplimiento
# ═════════════════════════════════════════════════════════════════════════════


def fase5_aplicar_calculos_cumplimiento(df: pd.DataFrame) -> pd.DataFrame:
    """
    FASE 5 - Cálculos y Categorización: Normalizar y categorizar cumplimiento.

    Entrada: DataFrame de FASE 4
    Salida: DataFrame con columnas Cumplimiento_norm y Categoria finales
    Efectos:
      - Normaliza escala (% vs decimal)
      - Categoriza según umbrales (Peligro/Alerta/Cumplimiento/Sobrecumplimiento)
      - Detecta registros especiales (métricas, sin reporte)

    NOTA: Cumplimiento es pre-calculado en scripts/etl/cumplimiento.py
    Esta función solo NORMALIZA Y CATEGORIZA valores existentes.
    """

    _col_tipo_reg = next((c for c in ["TipoRegistro", "Tipo_Registro"] if c in df.columns), None)
    _col_ejec_signo = next((c for c in ["EjecS", "Ejecucion_Signo"] if c in df.columns), None)

    # Detectar métricas
    if _col_tipo_reg:
        _mask_metrica = df[_col_tipo_reg].astype(str).str.strip().str.lower() == "metrica"
    elif "Indicador" in df.columns:
        _mask_metrica = (
            df["Indicador"].astype(str).str.lower().str.contains(r"\bmetrica\b", na=False)
        )
    else:
        _mask_metrica = pd.Series(False, index=df.index)

    # Detectar sin meta / No Aplica
    _mask_sin_meta = (
        (
            pd.to_numeric(df["Meta"], errors="coerce").isna()
            | (pd.to_numeric(df["Meta"], errors="coerce") == 0)
        )
        if "Meta" in df.columns
        else pd.Series(False, index=df.index)
    )

    if _col_tipo_reg:
        _mask_no_aplica = df[_col_tipo_reg].astype(str).str.strip().str.lower().eq("no aplica")
    elif _col_ejec_signo:
        _mask_no_aplica = df[_col_ejec_signo].astype(str).str.strip().str.lower().eq("no aplica")
    else:
        _mask_no_aplica = pd.Series(False, index=df.index)

    _mask_sin_reporte = (~_mask_metrica) & (_mask_sin_meta | _mask_no_aplica)

    # Normalizar
    df["Cumplimiento_norm"] = (
        df["Cumplimiento"].apply(normalizar_cumplimiento)
        if "Cumplimiento" in df.columns
        else float("nan")
    )
    df.loc[_mask_metrica | _mask_sin_reporte, "Cumplimiento_norm"] = float("nan")

    # Recalcular cumplimiento faltante cuando Meta y Ejecución están disponibles
    _tiene_ejec = "Ejecucion" in df.columns or "Ejecución" in df.columns
    _col_ejec = "Ejecucion" if "Ejecucion" in df.columns else ("Ejecución" if "Ejecución" in df.columns else None)
    _col_sentido = "Sentido" if "Sentido" in df.columns else None
    if _tiene_ejec and "Meta" in df.columns:
        _calcular_mask = df["Cumplimiento_norm"].isna() & df["Meta"].notna() & df[_col_ejec].notna()
        if _calcular_mask.any():
            def _calcular_fila(row):
                sentido = row[_col_sentido] if _col_sentido and _col_sentido in row.index else "Positivo"
                return recalcular_cumplimiento_faltante(
                    row["Meta"], row[_col_ejec], sentido=sentido, id_indicador=row.get("Id")
                )
            df.loc[_calcular_mask, "Cumplimiento_norm"] = df.loc[_calcular_mask].apply(_calcular_fila, axis=1)

    # Categorizar
    df["Categoria"] = df.apply(
        lambda r: categorizar_cumplimiento(
            r["Cumplimiento_norm"],
            id_indicador=r.get("Id"),
        ),
        axis=1,
    )

    # Fechas y tipos finales
    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    if "Anio" in df.columns:
        df["Anio"] = pd.to_numeric(df["Anio"], errors="coerce")
        if "Fecha" in df.columns and df["Anio"].isna().any():
            df["Anio"] = df["Anio"].fillna(df["Fecha"].dt.year)
        df["Anio"] = df["Anio"].astype("Int64")

    return df


# ═════════════════════════════════════════════════════════════════════════════
# PIPELINE COMPLETO
# ═════════════════════════════════════════════════════════════════════════════


def ejecutar_pipeline_completo(path: Path, es_historico: bool = False) -> pd.DataFrame:
    """
    Ejecuta el pipeline ETL completo (5 fases).

    Parámetros
    ----------
    path : Path
        Ruta a Resultados Consolidados.xlsx
    es_historico : bool
        Si True, usa hoja Consolidado Historico (FASE 1)
        Si False, usa hoja Consolidado Semestral (default)

    Retorna
    -------
    pd.DataFrame
        Dataset completamente procesado listo para consumo
    """
    # FASE 1: Lectura
    df = (
        fase1_leer_consolidado_historico(path) if es_historico
        else fase1_leer_consolidado_semestral(path)
    )

    # FASE 2: Enriquecimiento Primario
    df = fase2_enriquecer_clasificacion(df, path)

    # FASE 3: Enriquecimiento Secundario
    df = fase3_enriquecer_cmi_y_procesos(df)

    # FASE 4: Reconstrucción de Fórmulas
    df = fase4_reconstruir_columnas_formula(df)

    # FASE 5: Cálculos y Categorización
    df = fase5_aplicar_calculos_cumplimiento(df)

    return df
