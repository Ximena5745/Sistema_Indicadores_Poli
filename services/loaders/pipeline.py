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
from core.domain import (
    categorizar_cumplimiento,
    cumplimiento_por_bandas_kawak,
    recalcular_cumplimiento_faltante,
)
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


def _cargar_rangos_kawak() -> pd.DataFrame:
    """
    Carga los rangos de semáforo (peligro/alerta/cumplimiento/exceso) parametrizados
    por indicador y período en el export crudo de Kawak.

    Se usan ÚNICAMENTE como respaldo para indicadores con Meta=0, donde el
    cálculo estándar por ratio (Meta/Ejecución) no aplica — ver
    core.domain.cumplimiento_por_bandas_kawak para el porqué.

    Retorna DataFrame con columnas [Id, Fecha, peligro, alerta, cumplimiento,
    exceso] o vacío si el archivo fuente no existe/no se puede leer.
    """
    path = DATA_RAW / "Fuentes Consolidadas" / "Consolidado_API_Kawak.xlsx"
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_excel(path, engine="openpyxl")
    except Exception:
        return pd.DataFrame()

    cols_necesarias = ["ID", "fecha", "peligro", "alerta", "cumplimiento", "exceso"]
    if not all(c in df.columns for c in cols_necesarias):
        return pd.DataFrame()

    df = df[cols_necesarias].copy()
    df["Id"] = df["ID"].apply(id_a_str)
    df["Fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.normalize()
    df = df.dropna(subset=["Id", "Fecha"])
    # Un mismo Id+Fecha puede repetirse en el export crudo; quedarse con el
    # último registro (más reciente en el orden del archivo).
    df = df.drop_duplicates(subset=["Id", "Fecha"], keep="last")
    return df[["Id", "Fecha", "peligro", "alerta", "cumplimiento", "exceso"]]


def _cargar_meta_disponible_kawak() -> pd.DataFrame:
    """
    Indica, por Id+Fecha, si el export crudo de Kawak trae 'meta' parametrizada
    ese período.

    Cuando 'meta' viene vacía en Kawak, el indicador está estableciendo su
    línea base ese período (aún no tiene meta definida): no debe evaluarse
    como incumplimiento aunque el pipeline reconstruya Meta/Ejecución más
    adelante (p.ej. vía desglose de variables).

    Retorna DataFrame [Id, Fecha, meta_kawak_presente] o vacío si el archivo
    fuente no existe/no se puede leer.
    """
    path = DATA_RAW / "Fuentes Consolidadas" / "Consolidado_API_Kawak.xlsx"
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_excel(path, engine="openpyxl")
    except Exception:
        return pd.DataFrame()

    cols_necesarias = ["ID", "fecha", "meta"]
    if not all(c in df.columns for c in cols_necesarias):
        return pd.DataFrame()

    df = df[cols_necesarias].copy()
    df["Id"] = df["ID"].apply(id_a_str)
    df["Fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.normalize()
    df = df.dropna(subset=["Id", "Fecha"])
    df["meta_kawak_presente"] = df["meta"].notna()
    # Un mismo Id+Fecha puede repetirse en el export crudo; basta con que UNA
    # fila traiga meta para considerarla disponible ese período.
    df = df.groupby(["Id", "Fecha"], as_index=False)["meta_kawak_presente"].max()
    return df


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

    # Detectar métricas. Tipo_Registro no siempre está poblado (ej. Consolidado
    # Historico lo trae vacío para filas que sí son métricas), así que el
    # nombre del indicador ("... - (Metrica)") es una señal complementaria,
    # no un fallback exclusivo: se combinan ambas con OR para no dejar pasar
    # métricas cuando la columna existe pero viene en NaN.
    _mask_metrica = pd.Series(False, index=df.index)
    if _col_tipo_reg:
        _mask_metrica |= df[_col_tipo_reg].astype(str).str.strip().str.lower() == "metrica"
    if "Indicador" in df.columns:
        _mask_metrica |= df["Indicador"].astype(str).str.contains(
            r"m[eé]trica", case=False, na=False, regex=True
        )

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
        _calcular_mask = (
            df["Cumplimiento_norm"].isna()
            & df["Meta"].notna()
            & df[_col_ejec].notna()
            & ~_mask_metrica
        )
        if _calcular_mask.any():
            def _calcular_fila(row):
                sentido = row[_col_sentido] if _col_sentido and _col_sentido in row.index else "Positivo"
                return recalcular_cumplimiento_faltante(
                    row["Meta"], row[_col_ejec], sentido=sentido, id_indicador=row.get("Id")
                )
            df.loc[_calcular_mask, "Cumplimiento_norm"] = df.loc[_calcular_mask].apply(_calcular_fila, axis=1)

    # Override SOLO para Meta=0: el ratio Meta/Ejecución da un acantilado
    # binario 0%/100% (ver recalcular_cumplimiento_faltante) que no refleja
    # bien indicadores "menos es mejor" con meta cero. Se reemplaza por un
    # valor proporcional usando los rangos de semáforo parametrizados en Kawak
    # (peligro/alerta/cumplimiento/exceso) cuando están disponibles para ese
    # Id+Fecha. No afecta ningún indicador con Meta≠0.
    _mask_override = pd.Series(False, index=df.index)
    _categoria_override = pd.Series(dtype=object)
    if "Meta" in df.columns and "Id" in df.columns and "Fecha" in df.columns:
        _meta_num = pd.to_numeric(df["Meta"], errors="coerce")
        _mask_meta_cero = _meta_num == 0
        if _mask_meta_cero.any():
            rangos_kawak = _cargar_rangos_kawak()
            if not rangos_kawak.empty:
                # Claves temporales de cruce (no se puede usar directamente
                # "Fecha" como right_on porque df ya tiene su propia columna
                # "Fecha" sin normalizar, y colisionaría con la del merge).
                _idx_original = df.index
                df["_id_key_kawak"] = df["Id"].astype(str)
                df["_fecha_key_kawak"] = pd.to_datetime(df["Fecha"], errors="coerce").dt.normalize()
                rk = rangos_kawak.rename(columns={"Id": "_id_key_kawak", "Fecha": "_fecha_key_kawak"})
                # left-merge sobre clave única (Id+Fecha deduplicado en
                # _cargar_rangos_kawak) no multiplica filas ni reordena, pero
                # pandas igual resetea el índice: se restaura explícitamente
                # para que las máscaras booleanas calculadas antes del merge
                # (_mask_meta_cero, _mask_metrica) sigan alineando por label.
                df = df.merge(rk, on=["_id_key_kawak", "_fecha_key_kawak"], how="left")
                df.index = _idx_original
                df = df.drop(columns=["_id_key_kawak", "_fecha_key_kawak"])

                _bandas_ok = df[["alerta", "cumplimiento", "exceso"]].notna().all(axis=1)
                _mask_override = _mask_meta_cero & _bandas_ok & ~_mask_metrica
                if _mask_override.any():
                    def _fila_bandas_kawak(row):
                        sentido = (
                            row[_col_sentido] if _col_sentido and _col_sentido in row.index else "Positivo"
                        )
                        return cumplimiento_por_bandas_kawak(
                            row[_col_ejec],
                            sentido,
                            alerta=row["alerta"],
                            cumplimiento=row["cumplimiento"],
                            exceso=row["exceso"],
                            peligro=row.get("peligro"),
                        )
                    _resultados = df.loc[_mask_override].apply(_fila_bandas_kawak, axis=1)
                    df.loc[_mask_override, "Cumplimiento_norm"] = _resultados.apply(lambda t: t[0])
                    # La categoría se guarda para aplicarse DESPUÉS de la
                    # categorización general (que de otro modo la pisaría: sus
                    # umbrales universales asumen "Cumplimiento"=100-105%,
                    # mientras que aquí el 100% es el punto "exceso" — ver
                    # docstring de cumplimiento_por_bandas_kawak).
                    _categoria_override = _resultados.apply(lambda t: t[1])
                df = df.drop(columns=["peligro", "alerta", "cumplimiento", "exceso"], errors="ignore")

    # Excepción: indicador estableciendo línea base ese período (Kawak no
    # trae 'meta' parametrizada), aunque el pipeline haya reconstruido
    # Meta/Ejecución por otra vía (p.ej. desglose de variables). No se evalúa
    # como incumplimiento: se marca "Sin dato" y sin ícono de cumplimiento.
    _mask_linea_base = pd.Series(False, index=df.index)
    if "Id" in df.columns and "Fecha" in df.columns:
        meta_kawak = _cargar_meta_disponible_kawak()
        if not meta_kawak.empty:
            _idx_original = df.index
            df["_id_key_kawak"] = df["Id"].astype(str)
            df["_fecha_key_kawak"] = pd.to_datetime(df["Fecha"], errors="coerce").dt.normalize()
            mk = meta_kawak.rename(columns={"Id": "_id_key_kawak", "Fecha": "_fecha_key_kawak"})
            df = df.merge(mk, on=["_id_key_kawak", "_fecha_key_kawak"], how="left")
            df.index = _idx_original
            df = df.drop(columns=["_id_key_kawak", "_fecha_key_kawak"])
            _mask_linea_base = (df["meta_kawak_presente"] == False) & ~_mask_metrica  # noqa: E712
            df = df.drop(columns=["meta_kawak_presente"], errors="ignore")

    # Categorizar
    df["Categoria"] = df.apply(
        lambda r: categorizar_cumplimiento(
            r["Cumplimiento_norm"],
            id_indicador=r.get("Id"),
        ),
        axis=1,
    )
    if _mask_override.any():
        df.loc[_mask_override, "Categoria"] = _categoria_override
    if _mask_linea_base.any():
        df.loc[_mask_linea_base, "Cumplimiento_norm"] = float("nan")
        df.loc[_mask_linea_base, "Categoria"] = "Sin dato"

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
