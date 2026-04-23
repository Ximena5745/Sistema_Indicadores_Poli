def calcular_cascada(df):
    # Nivel 4: Indicador (hoja)
    nivel4 = df.copy()
    nivel4["Nivel"] = 4
    nivel4["Total_Indicadores"] = 1
    nivel4 = nivel4[
        [
            "Nivel",
            "Linea",
            "Objetivo",
            "Meta_PDI",
            "Indicador",
            "cumplimiento_pct",
            "Total_Indicadores",
        ]
    ]
    nivel4 = nivel4.rename(columns={"cumplimiento_pct": "Cumplimiento"})

    # Nivel 3: Meta_PDI
    nivel3 = (
        df.groupby(["Linea", "Objetivo", "Meta_PDI"], dropna=False)
        .agg(Cumplimiento=("cumplimiento_pct", "mean"), Total_Indicadores=("Indicador", "count"))
        .reset_index()
    )
    nivel3["Nivel"] = 3
    nivel3["Indicador"] = None
    nivel3 = nivel3[
        ["Nivel", "Linea", "Objetivo", "Meta_PDI", "Indicador", "Cumplimiento", "Total_Indicadores"]
    ]

    # Nivel 2: Objetivo
    nivel2 = (
        df.groupby(["Linea", "Objetivo"], dropna=False)
        .agg(Cumplimiento=("cumplimiento_pct", "mean"), Total_Indicadores=("Indicador", "count"))
        .reset_index()
    )
    nivel2["Nivel"] = 2
    nivel2["Meta_PDI"] = None
    nivel2["Indicador"] = None
    nivel2 = nivel2[
        ["Nivel", "Linea", "Objetivo", "Meta_PDI", "Indicador", "Cumplimiento", "Total_Indicadores"]
    ]

    # Nivel 1: Linea
    nivel1 = (
        df.groupby(["Linea"], dropna=False)
        .agg(Cumplimiento=("cumplimiento_pct", "mean"), Total_Indicadores=("Indicador", "count"))
        .reset_index()
    )
    nivel1["Nivel"] = 1
    nivel1["Objetivo"] = None
    nivel1["Meta_PDI"] = None
    nivel1["Indicador"] = None
    nivel1 = nivel1[
        ["Nivel", "Linea", "Objetivo", "Meta_PDI", "Indicador", "Cumplimiento", "Total_Indicadores"]
    ]

    # Unir todos los niveles
    cascada = pd.concat([nivel1, nivel2, nivel3, nivel4], ignore_index=True)
    return cascada


"""
pages/resumen_general_real.py — Resumen General con datos reales de Consolidado Cierres.

Fuente real: data/output/Resultados Consolidados.xlsx · hoja Consolidado Cierres
"""
from pathlib import Path  # noqa: F401 — retenido por compatibilidad con código heredado
import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

try:
    from services.strategic_indicators import preparar_pdi_con_cierre, load_pdi_catalog
    import services.strategic_indicators as si
    from core.config import DATA_OUTPUT
    from core.proceso_types import TIPOS_PROCESO, get_tipo_color
    from core.calculos import simple_categoria_desde_porcentaje
    from core.semantica import categorizar_cumplimiento
    from streamlit_app.services.data_service import DataService
    from services.cmi_filters import filter_df_for_cmi_estrategico, filter_df_for_cmi_procesos
except (ImportError, ModuleNotFoundError):
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from services.strategic_indicators import preparar_pdi_con_cierre, load_pdi_catalog
    import services.strategic_indicators as si
    from core.config import DATA_OUTPUT
    from core.proceso_types import TIPOS_PROCESO, get_tipo_color
    from core.calculos import simple_categoria_desde_porcentaje
    from core.semantica import categorizar_cumplimiento
    from streamlit_app.services.data_service import DataService
    from services.cmi_filters import filter_df_for_cmi_estrategico, filter_df_for_cmi_procesos

import numpy as np
# Limpiar caché corrupto si es necesario (defensa para st stub en tests)
def _get_proyectos_ids():
    """Retorna set de IDs de indicadores marcados como Proyecto==1 en CMI xlsx."""
    from services.cmi_filters import load_cmi_worksheet
    df = load_cmi_worksheet()
    if df.empty or "Proyecto" not in df.columns or "Id" not in df.columns:
        return set()
    return set(str(int(x)) if isinstance(x, float) else str(x).strip() for x in df.loc[df["Proyecto"] == 1, "Id"].dropna())

def _build_linea_summary_from_df(df, nivel_col="Nivel de cumplimiento"):
    """Construye resumen por línea: N_Indicadores, Cumpl_Promedio, conteos por nivel."""
    if df.empty or "Linea" not in df.columns:
        return pd.DataFrame(columns=["Linea","N_Indicadores","Cumpl_Promedio","Sobrecumplimiento","Cumplimiento","Alerta","Peligro"])
    df = df.copy()
    if nivel_col not in df.columns:
        df = _ensure_nivel_cumplimiento(df)
        nivel_col = "Nivel de cumplimiento"
    resumen = (
        df.groupby("Linea", dropna=False)
        .agg(
            N_Indicadores=("Indicador", "count") if "Indicador" in df.columns else (df.columns[0], "size"),
            Cumpl_Promedio=("cumplimiento_pct", "mean"),
            Sobrecumplimiento=(nivel_col, lambda s: (s=="Sobrecumplimiento").sum()),
            Cumplimiento=(nivel_col, lambda s: (s=="Cumplimiento").sum()),
            Alerta=(nivel_col, lambda s: (s=="Alerta").sum()),
            Peligro=(nivel_col, lambda s: (s=="Peligro").sum()),
        )
        .reset_index()
    )
    return resumen

def _load_plan_retos_data(year):
    """Carga Plan de retos.xlsx (hojas 'Linea' y 'Objetivo') para el año dado."""
    import pandas as pd
    retos_path = Path("data/raw/Retos/Plan de retos.xlsx")
    if not retos_path.exists():
        return pd.DataFrame(), pd.DataFrame()
    try:
        linea_df = pd.read_excel(retos_path, sheet_name="Linea", engine="openpyxl")
        obj_df = pd.read_excel(retos_path, sheet_name="Objetivo", engine="openpyxl")
        # Normalizar nombres
        linea_df.columns = [str(c).strip() for c in linea_df.columns]
        obj_df.columns = [str(c).strip() for c in obj_df.columns]
        # Filtrar por año
        linea_df = linea_df[linea_df["Año"] == year].copy() if "Año" in linea_df.columns else linea_df
        obj_df = obj_df[obj_df["Año"] == year].copy() if "Año" in obj_df.columns else obj_df
        # Normalizar nombres para sunburst
        if "Línea Estratégica" in linea_df.columns:
            linea_df = linea_df.rename(columns={"Línea Estratégica": "Linea"})
        if "Línea Estratégica" in obj_df.columns:
            obj_df = obj_df.rename(columns={"Línea Estratégica": "Linea"})
        if "Cumplimiento" in linea_df.columns:
            linea_df = linea_df.rename(columns={"Cumplimiento": "cumplimiento_pct"})
        if "Cumplimiento" in obj_df.columns:
            obj_df = obj_df.rename(columns={"Cumplimiento": "cumplimiento_pct"})
        # Objetivo para sunburst
        if "Objetivo" not in obj_df.columns:
            obj_df["Objetivo"] = None
        return linea_df, obj_df
    except Exception:
        return pd.DataFrame(), pd.DataFrame()

def _build_linea_summary_from_retos(linea_df):
    """Construye resumen por línea para Plan de Retos."""
    if linea_df.empty or "Linea" not in linea_df.columns:
        return pd.DataFrame(columns=["Linea","N_Indicadores","Cumpl_Promedio","Sobrecumplimiento","Cumplimiento","Alerta","Peligro"])
    df = linea_df.copy()
    # Asumimos que cada fila es una línea, con cumplimiento_pct
    def _cat(pct):
        if pd.isna(pct): return "Sin dato"
        pct = float(pct)
        if pct >= 105: return "Sobrecumplimiento"
        if pct >= 100: return "Cumplimiento"
        if pct >= 80: return "Alerta"
        return "Peligro"
    df["Nivel de cumplimiento"] = df["cumplimiento_pct"].apply(_cat)
    resumen = (
        df.groupby("Linea", dropna=False)
        .agg(
            N_Indicadores=("cumplimiento_pct", "size"),
            Cumpl_Promedio=("cumplimiento_pct", "mean"),
            Sobrecumplimiento=("Nivel de cumplimiento", lambda s: (s=="Sobrecumplimiento").sum()),
            Cumplimiento=("Nivel de cumplimiento", lambda s: (s=="Cumplimiento").sum()),
            Alerta=("Nivel de cumplimiento", lambda s: (s=="Alerta").sum()),
            Peligro=("Nivel de cumplimiento", lambda s: (s=="Peligro").sum()),
        )
        .reset_index()
    )
    return resumen

def _merge_consolidado_summaries(s1, s2, s3, o1, o2, o3):
    """Promedia Cumpl_Promedio y suma N_Indicadores por línea; concatena objetivos."""
    # s1,s2,s3: linea_summary de cada fuente; o1,o2,o3: objetivo_df de cada fuente
    all_lineas = pd.concat([s1[["Linea"]], s2[["Linea"]], s3[["Linea"]]]).drop_duplicates()
    out = all_lineas.copy()
    for col in ["N_Indicadores","Cumpl_Promedio","Sobrecumplimiento","Cumplimiento","Alerta","Peligro"]:
        vals = []
        for s in [s1,s2,s3]:
            if col in s.columns:
                vals.append(s.set_index("Linea")[col])
        if vals:
            dfc = pd.concat(vals, axis=1).fillna(0)
            if col=="Cumpl_Promedio":
                out[col] = dfc.mean(axis=1)
            else:
                out[col] = dfc.sum(axis=1)
        else:
            out[col] = 0
    out = out.reset_index(drop=True)
    # Objetivos: concatenar y promediar cumplimiento
    objetivo_df = pd.concat([o1,o2,o3], ignore_index=True)
    if "cumplimiento_pct" in objetivo_df.columns:
        objetivo_df["cumplimiento_pct"] = pd.to_numeric(objetivo_df["cumplimiento_pct"], errors="coerce")
    return out, objetivo_df

def _get_sin_gestion_df():
    """Carga CMI xlsx y retorna DF de indicadores con Plan anual == 3."""
    from services.cmi_filters import load_cmi_worksheet
    df = load_cmi_worksheet()
    if df.empty or "Plan anual" not in df.columns:
        return pd.DataFrame()
    sin_gestion = df[df["Plan anual"] == 3].copy()
    cols = [c for c in ["Id","Indicador","Linea"] if c in sin_gestion.columns]
    return sin_gestion[cols] if cols else sin_gestion
try:
    ss = st.session_state
except Exception:
    ss = None
if ss is not None:
    if "page_cache_cleared" not in ss:
        try:
            si.load_worksheet_flags.clear()
            si.load_cierres.clear()
        except Exception:
            pass
        ss.page_cache_cleared = True

PATH_CONSOLIDADO = DATA_OUTPUT / "Resultados Consolidados.xlsx"

LINEA_COLORS = {
    "Expansión": "#FBAF17",
    "Transformación organizacional": "#42F2F2",
    "Calidad": "#EC0677",
    "Experiencia": "#1FB2DE",
    "Sostenibilidad": "#A6CE38",
    "Educación para toda la vida": "#0F385A",
}

MES_MAP = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip() for c in df.columns]
    # Normaliza la columna de cumplimiento
    if "Cumplimiento" in df.columns and "cumplimiento_pct" not in df.columns:
        df = df.rename(columns={"Cumplimiento": "cumplimiento_pct"})
    # Reemplazar guiones bajos por espacios en columnas de texto clave
    _TEXT_COLS = [
        "Linea",
        "Objetivo",
        "Meta_PDI",
        "Indicador",
        "Clasificacion",
        "Proceso",
        "Subproceso",
        "Area",
        "tipo",
        "Estado",
    ]
    for col in _TEXT_COLS:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace("_", " ", regex=False).str.strip()
            df[col] = df[col].replace("nan", pd.NA)
    return df


def _parse_month(value):
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        try:
            return int(value)
        except Exception:
            return None
    text = str(value).strip()
    if text.isdigit():
        return int(text)
    return MES_MAP.get(text.lower())


def _load_consolidado_cierres() -> pd.DataFrame:
    if not PATH_CONSOLIDADO.exists():
        return pd.DataFrame()
    try:
        df = pd.read_excel(PATH_CONSOLIDADO, sheet_name="Consolidado Cierres", engine="openpyxl")
    except Exception:
        return pd.DataFrame()
    df = _normalize_columns(df)
    # Exportar columnas originales del consolidado para inspección
    try:
        df_cols = pd.DataFrame({"columnas": df.columns})
        df_cols.to_excel("artifacts/consolidado_columnas_originales.xlsx", index=False)
        # Exportar valores únicos por columna útil para mapeo
        cols_interes = [
            c
            for c in df.columns
            if any(
                x in c.lower()
                for x in ["linea", "objetivo", "meta", "indicador", "cumplimiento", "categoria"]
            )
        ]
        with pd.ExcelWriter("artifacts/consolidado_valores_unicos_mapeo.xlsx") as writer:
            for col in cols_interes:
                uniques = pd.DataFrame({col: df[col].unique()})
                uniques.to_excel(writer, sheet_name=col[:30], index=False)
    except Exception as e:
        print(f"No se pudo exportar columnas/valores únicos: {e}")
    # Asegurar carpeta de artifacts y normalizar columna año
    os.makedirs("artifacts", exist_ok=True)
    if "A\x1fo" in df.columns:
        df["A\x1fo"] = pd.to_numeric(df["A\x1fo"], errors="coerce")
    elif "Anio" in df.columns:
        df["A\x1fo"] = pd.to_numeric(df["Anio"], errors="coerce")
    else:
        df["A\x1fo"] = pd.NA

    if "Mes" in df.columns:
        df["Mes_num"] = df["Mes"].apply(_parse_month)
    else:
        df["Mes_num"] = None

    # Si existe "Cumplimiento" y no "cumplimiento_pct", normaliza
    if "Cumplimiento" in df.columns and "cumplimiento_pct" not in df.columns:
        df = df.rename(columns={"Cumplimiento": "cumplimiento_pct"})
    # Asegurar que `cumplimiento_pct` esté en escala porcentual (0-100)
    if "cumplimiento_pct" in df.columns:
        df["cumplimiento_pct"] = pd.to_numeric(df.get("cumplimiento_pct"), errors="coerce")
        # Si los valores parecen estar en escala decimal [0..2], convertir a porcentaje
        try:
            mx = (
                float(df["cumplimiento_pct"].abs().max(skipna=True))
                if not df["cumplimiento_pct"].isna().all()
                else 0
            )
        except Exception:
            mx = 0
        if mx <= 2:
            df["cumplimiento_pct"] = df["cumplimiento_pct"].multiply(100)

    df = _ensure_nivel_cumplimiento(df)
    return df


def _ensure_nivel_cumplimiento(df: pd.DataFrame) -> pd.DataFrame:
    # Prefer recalcular 'Nivel de cumplimiento' desde 'cumplimiento_pct' cuando esté disponible
    # 1) Normalize 'Cumplimiento' -> 'cumplimiento_pct' if necesario
    if "Cumplimiento" in df.columns and "cumplimiento_pct" not in df.columns:
        df = df.rename(columns={"Cumplimiento": "cumplimiento_pct"})

    if "cumplimiento_pct" in df.columns:

        def _map_level_v2(row):
            """
            Usa core.semantica para categorizar.
            Los valores en cumplimiento_pct están en porcentaje (0-100).
            """
            if pd.isna(row["cumplimiento_pct"]):
                return "Pendiente de reporte"
            try:
                pct = float(row["cumplimiento_pct"])
            except Exception:
                return "Pendiente de reporte"

            import math

            if math.isnan(pct):
                return "Pendiente de reporte"

            # MEJORA FASE 2: Usar wrapper centralizado
            from core.semantica import normalizar_y_categorizar

            id_indicador = row.get("Id", None)
            categoria = normalizar_y_categorizar(pct, es_porcentaje=True, id_indicador=id_indicador)
            return categoria

        df = df.copy()
        df["Nivel de cumplimiento"] = df.apply(_map_level_v2, axis=1)
        return df

    # 2) Si no hay 'cumplimiento_pct' pero existe 'Categoria', usarla
    if "Categoria" in df.columns:
        df = df.copy()
        df["Nivel de cumplimiento"] = df["Categoria"]
        return df

    # 3) Si nada de lo anterior, marcar como pendiente
    df = df.copy()
    df["Nivel de cumplimiento"] = "Pendiente de reporte"
    return df


def _available_years(df: pd.DataFrame) -> list[int]:
    if df.empty or "Año" not in df.columns:
        return []
    years = pd.to_numeric(df["Año"], errors="coerce").dropna().astype(int).unique().tolist()
    allowed = [y for y in sorted(years) if y in {2022, 2023, 2024, 2025}]
    return allowed or sorted(years)


def _filter_consolidado_by_year_month(
    df: pd.DataFrame, year: int | None, month: int | None
) -> pd.DataFrame:
    df = df.copy()

    # Simple debug to file
    import os

    debug_file = "debug_filter.log"
    with open(debug_file, "w") as f:
        f.write(f"Input rows: {len(df)}\n")

    # detect year column
    year_col = None
    for c in df.columns:
        if isinstance(c, str) and "A" in c and "o" in c and ("ñ" in c.lower() or c == "Anio"):
            year_col = c
            break
    if year_col is None and "Anio" in df.columns:
        year_col = "Anio"
    if year_col is None and "Año" in df.columns:
        year_col = "Año"

    with open(debug_file, "a") as f:
        f.write(f"year_col: {year_col}\n")

    if year_col is not None and year_col in df.columns:
        df["_year"] = pd.to_numeric(df[year_col], errors="coerce")
    elif "Periodo" in df.columns:
        df["_year"] = (
            df["Periodo"]
            .astype(str)
            .str.split("-")
            .str[0]
            .apply(lambda x: pd.to_numeric(x, errors="coerce"))
        )
    else:
        df["_year"] = pd.NA

    # detect month column
    if "Mes_num" in df.columns:
        df["_month"] = pd.to_numeric(df["Mes_num"], errors="coerce")
    elif "Mes" in df.columns:
        df["_month"] = pd.to_numeric(df["Mes"], errors="coerce")
    else:
        df["_month"] = pd.NA

    with open(debug_file, "a") as f:
        f.write(f"year filter: {year}, month filter: {month}\n")
        f.write(f"_year values: {sorted(df['_year'].dropna().unique())}\n")
        f.write(f"_month values: {sorted(df['_month'].dropna().unique())}\n")

    if year is not None:
        df = df[df["_year"] == int(year)]
    if month:
        df = df[df["_month"] == int(month)]

    with open(debug_file, "a") as f:
        f.write(f"Output rows: {len(df)}\n")

    # drop helper cols
    df = df.drop(columns=[c for c in ["_year", "_month"] if c in df.columns])
    return df


def _latest_month_for_year(df: pd.DataFrame, year: int) -> int | None:
    subset = df[df["Año"] == year].copy()
    if subset.empty or "Mes_num" not in subset.columns:
        return None
    months = pd.to_numeric(subset["Mes_num"], errors="coerce").dropna().astype(int)
    return int(months.max()) if not months.empty else None


def _available_months_for_year(df: pd.DataFrame, year: int) -> list[int]:
    subset = df[df["Año"] == year].copy()
    if subset.empty or "Mes_num" not in subset.columns:
        return []
    months = pd.to_numeric(subset["Mes_num"], errors="coerce").dropna().astype(int).unique()
    return sorted(months.tolist())


def _build_sunburst(pdi_df: pd.DataFrame) -> go.Figure:
    """
    Gráfica Sunburst oficial CMI Estratégico
    ----------------------------------------
    Jerarquía:
      - Centro: Línea Estratégica
      - Anillo exterior: Objetivos Estratégicos
    Filtro aplicado:
      - Solo indicadores CMI Estratégico (Indicadores Plan estrategico == 1 y Proyecto != 1)
    Cálculo:
      - Promedio de cumplimiento (cumplimiento_pct) por objetivo y por línea
    Exclusiones:
      - Omitir métricas y filas sin cumplimiento
    Visualización:
      - Cada segmento: nombre objetivo y % cumplimiento promedio
      - Colores oficiales por línea
      - Tooltip y zoom jerárquico
    """
    # Exportar las columnas del DataFrame de entrada (diagnóstico)
    try:
        with open("artifacts/sunburst_columnas_generadas.txt", "w", encoding="utf-8") as f:
            f.write("\n".join([str(c) for c in pdi_df.columns]))
    except Exception as e:
        print(f"No se pudo exportar columnas: {e}")

    df = pdi_df.copy()
    # Normalizar y limpiar cumplimiento_pct: convertir a numérico y eliminar inf
    try:
        import numpy as np

        df["cumplimiento_pct"] = pd.to_numeric(df.get("cumplimiento_pct"), errors="coerce")
        # avoid chained-assignment issues: assign the replaced series back
        df["cumplimiento_pct"] = df["cumplimiento_pct"].replace([np.inf, -np.inf], pd.NA)
    except Exception:
        pass
    # Eliminar nodos vacíos o en blanco en la jerarquía
    for col in ["Linea", "Objetivo"]:
        df = df[df[col].notnull() & (df[col].astype(str).str.strip() != "")]
    df = df[df["cumplimiento_pct"].notna()]

    # Exportar a Excel la información filtrada para el gráfico (solo Linea y Objetivo)
    try:
        df_export = df[["Linea", "Objetivo"]].drop_duplicates().sort_values(["Linea", "Objetivo"])
        df_export.to_excel("artifacts/sunburst_linea_objetivo.xlsx", index=False)
    except Exception as e:
        print(f"No se pudo exportar Excel de sunburst: {e}")

    # Si no hay datos válidos, crear un nodo dummy con 0%
    if df.empty:
        labels = ["Sin datos"]
        parents = [""]
        values = [1]
        customdata = [[0]]
        colors = ["#6B728E"]
        text = ["Sin datos\n0.0%"]
    else:
        # --- LIMPIEZA ADICIONAL: eliminar indicadores tipo métrica y objetivos vacíos ---
        if "tipo" in df.columns:
            try:
                df = df[~df["tipo"].astype(str).str.lower().str.contains("metr", na=False)]
            except Exception:
                pass
        # Asegurar no tener objetivos vacíos o sólo espacios (defensa adicional)
        df = df[df["Objetivo"].notnull() & (df["Objetivo"].astype(str).str.strip() != "")]

        # Nivel 1: Linea (promedio)
        lines = (
            df.groupby("Linea", dropna=False)
            .agg(cumplimiento_pct=("cumplimiento_pct", "mean"))
            .reset_index()
        )
        # Nivel 2: Objetivo (promedio)
        grouped = (
            df.groupby(["Linea", "Objetivo"], dropna=False)
            .agg(cumplimiento_pct=("cumplimiento_pct", "mean"))
            .reset_index()
        )

        labels = []
        parents = []
        values = []
        customdata = []
        colors = []

        # Use counts for sizing but show cumplimiento_pct as text inside sectors
        line_counts = df.groupby("Linea").size().to_dict()
        obj_counts = df.groupby(["Linea", "Objetivo"]).size().to_dict()

        # helper to match color keys ignoring accents/case
        def _norm_key(s: str) -> str:
            import unicodedata, re

            if s is None:
                return ""
            t = str(s).strip().lower()
            t = unicodedata.normalize("NFD", t)
            t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
            # replace any non-alphanumeric with a single space and collapse spaces
            t = re.sub(r"[^0-9a-z]+", " ", t)
            t = re.sub(r"\s+", " ", t).strip()
            return t

        normalized_color_map = {_norm_key(k): v for k, v in LINEA_COLORS.items()}

        # --- AJUSTE: El centro serán las líneas estratégicas ---
        for _, line in lines.iterrows():
            linea_name = str(line["Linea"])
            labels.append(linea_name)
            parents.append("")
            values.append(0)  # branchvalues='remainder': parent=0 → tamaño definido por hijos
            customdata.append(
                [line["cumplimiento_pct"] if pd.notna(line["cumplimiento_pct"]) else 0]
            )
            colors.append(normalized_color_map.get(_norm_key(linea_name), "#6B728E"))

        for _, row in grouped.iterrows():
            obj_name = row["Objetivo"]
            parent_name = row["Linea"]
            # Omitir objetivos vacíos o nulos (defensa adicional)
            if pd.isna(obj_name) or str(obj_name).strip() == "":
                continue
            if pd.isna(parent_name) or str(parent_name).strip() == "":
                continue
            # Omitir objetivos sin indicadores válidos
            count = obj_counts.get((parent_name, obj_name), 0)
            if not count or int(count) <= 0:
                continue
            labels.append(str(obj_name).strip())
            parents.append(str(parent_name).strip())
            values.append(1)  # valor uniforme → distribución igualitaria sin gaps
            customdata.append(
                [float(row["cumplimiento_pct"]) if pd.notna(row["cumplimiento_pct"]) else 0.0]
            )
            colors.append(normalized_color_map.get(_norm_key(parent_name), "#6B728E"))

        # Wrap long labels to multiple lines so they fit inside sectors
        def wrap_label(s: str, width: int = 18) -> str:
            import re

            text = str(s or "").strip()
            if not text:
                return ""
            # First try logical separators to produce natural splits
            separators = [",", " / ", " - ", " y ", ";"]
            segments = [text]
            for sep in separators:
                if any(sep in seg for seg in segments):
                    new_segs = []
                    for seg in segments:
                        if sep in seg:
                            parts = [p.strip() for p in seg.split(sep) if p.strip()]
                            new_segs.extend(parts)
                        else:
                            new_segs.append(seg)
                    segments = new_segs
            # Now for each segment, apply word-wrap to the given width
            wrapped_lines = []
            for seg in segments:
                words = seg.split()
                cur = []
                for w in words:
                    if sum(len(x) for x in cur) + len(cur) + len(w) <= width:
                        cur.append(w)
                    else:
                        if cur:
                            wrapped_lines.append(" ".join(cur))
                        cur = [w]
                if cur:
                    wrapped_lines.append(" ".join(cur))
            # clean and return joined lines
            cleaned = [re.sub(r"\s+", " ", ln).strip() for ln in wrapped_lines]
            return "\n".join(cleaned)

        # Overrides de salto de línea para labels específicos (ajuste visual manual)
        LABEL_WRAP_OVERRIDES = {
            _norm_key("Educación para toda la vida"): "Educación para\ntoda la vida",
        }

        # Build wrapped text lines; include percentage
        text = []
        for lab, cd, parent in zip(labels, customdata, parents):
            pct = cd[0] if cd and cd[0] is not None else 0
            lab_key = _norm_key(lab)
            if lab_key in LABEL_WRAP_OVERRIDES:
                wrapped = LABEL_WRAP_OVERRIDES[lab_key]
            elif parent == "":
                wrapped = wrap_label(lab, width=12)
            else:
                wrapped = wrap_label(lab, width=26)
            html_label = str(wrapped).replace("\n", "<br>")
            html_label = f"<b>{html_label}</b>"
            # porcentaje en línea nueva — sin <span> (Plotly SVG solo soporta <b>, <i>, <br>)
            text.append(f"{html_label}<br>{pct:.0f}%")

    # Split inner (Linea) and outer (Objetivo) for independent styling
    inner_idxs = [i for i, p in enumerate(parents) if p == ""]
    outer_idxs = [i for i, p in enumerate(parents) if p != ""]

    inner_labels = [labels[i] for i in inner_idxs]
    inner_values = [values[i] for i in inner_idxs]
    inner_colors = [colors[i] for i in inner_idxs]
    inner_custom = [customdata[i] for i in inner_idxs]
    inner_text = [text[i] for i in inner_idxs]

    outer_labels = [labels[i] for i in outer_idxs]
    outer_parents = [parents[i] for i in outer_idxs]
    outer_values = [values[i] for i in outer_idxs]
    outer_colors = [colors[i] for i in outer_idxs]
    outer_custom = [customdata[i] for i in outer_idxs]
    outer_text = [text[i] for i in outer_idxs]

    # Exportar diagnósticos (si las tablas existen en el scope)
    try:
        import os

        if "lines" in locals():
            os.makedirs("artifacts", exist_ok=True)
            lines.to_excel(os.path.join("artifacts", "sunburst_diag_lines.xlsx"), index=False)
        if "grouped" in locals():
            os.makedirs("artifacts", exist_ok=True)
            grouped.to_excel(os.path.join("artifacts", "sunburst_diag_grouped.xlsx"), index=False)
    except Exception as e:
        print("No se pudo exportar sunburst diagnostics:", e)

    # Build a single Sunburst trace (more robust across runtimes)
    fig = go.Figure()
    all_labels = labels
    all_parents = parents
    all_values = values
    all_colors = colors
    all_custom = customdata
    all_text = text

    # branchvalues='remainder': padres con valor 0 → su tamaño es exactamente la suma de hijos.
    # Objetivos con valor 1 → distribución uniforme. No quedan gaps blancos.

    fig.add_trace(
        go.Sunburst(
            labels=all_labels,
            parents=all_parents,
            values=all_values,
            branchvalues="remainder",
            marker=dict(colors=all_colors, line=dict(color="#ffffff", width=1)),
            customdata=all_custom,
            text=all_text,
            textinfo="text",
            texttemplate="%{text}",
            insidetextorientation="horizontal",
            hovertemplate="<b>%{label}</b><br>Promedio cumplimiento: %{customdata[0]:.0f}%<extra></extra>",
            domain=dict(x=[0, 1], y=[0, 1]),
            maxdepth=2,
            sort=False,
        )
    )

    # Improve readability: set explicit templates for the sunburst trace
    try:
        if len(fig.data) >= 1 and getattr(fig.data[0], "type", None) == "sunburst":
            fig.data[0].update(
                textfont=dict(family="Inter, sans-serif", size=11, color="#062A4F"),
                insidetextfont=dict(family="Inter, sans-serif", size=11, color="#062A4F"),
                marker=dict(line=dict(color="#FFFFFF", width=1)),
                branchvalues="remainder",
                separation=0,
                texttemplate="%{text}",
                hovertemplate="<b>%{label}</b><br>Promedio cumplimiento: %{customdata[0]:.1f}%<extra></extra>",
                insidetextorientation="horizontal",
                constraintext="none",
            )
    except Exception:
        pass

    # As a final safety, ensure any remaining sunburst traces get a minimal uniformtext update
    for trace in fig.data:
        try:
            if getattr(trace, "type", None) == "sunburst" and not getattr(
                trace, "uniformtext", None
            ):
                trace.update(uniformtext=dict(minsize=9, mode="hide"))
        except Exception:
            pass
    # Ensure Sunburst is present: if not, try to create via plotly.express.sunburst
    has_sunburst = any(getattr(t, "type", None) == "sunburst" for t in fig.data)
    if not has_sunburst:
        try:
            import plotly.express as px

            # use the prepared df to create a sunburst via express (fallback creation)
            px_df = df.copy()
            px_df = px_df.dropna(subset=["Linea", "Objetivo", "cumplimiento_pct"])
            if not px_df.empty:
                px_fig = px.sunburst(
                    px_df, path=["Linea", "Objetivo"], values=None, color="cumplimiento_pct"
                )
                # convert to go.Figure and try to harmonize
                fig = go.Figure(px_fig)
        except Exception:
            # if express also fails, keep original fig and add diagnostic meta
            fig.layout.meta = {
                "sunburst_forced": False,
                "reason": "could not build sunburst via px",
            }

    # Final layout for sunburst
    fig.update_layout(
        margin=dict(t=10, l=10, r=10, b=10),
        height=780,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    # mark success
    fig.layout.meta = dict(fig.layout.meta or {}, sunburst_forced=True)
    return fig


def _compute_trends(current: pd.DataFrame, previous: pd.DataFrame):
    if current.empty or previous.empty:
        return [], []
    # Incluir Linea si existe para mostrarla en tablas
    extra_cols = [c for c in ["Linea"] if c in current.columns]
    cur = (
        current[["Id", "Indicador", "cumplimiento_pct"] + extra_cols]
        .dropna(subset=["cumplimiento_pct"])
        .copy()
    )
    prev = previous[["Id", "cumplimiento_pct"]].dropna(subset=["cumplimiento_pct"]).copy()
    merged = cur.merge(prev, on="Id", suffixes=("", "_prev"))
    if merged.empty:
        return [], []
    merged["variation"] = merged["cumplimiento_pct"] - merged["cumplimiento_pct_prev"]
    best = merged.sort_values("variation", ascending=False).head(5)
    worst = merged.sort_values("variation").head(5)
    return (
        [
            {
                "name": str(row["Indicador"]),
                "change": float(row["variation"]),
                "linea": str(row["Linea"]) if "Linea" in merged.columns else "",
            }
            for _, row in best.iterrows()
        ],
        [
            {
                "name": str(row["Indicador"]),
                "change": float(row["variation"]),
                "linea": str(row["Linea"]) if "Linea" in merged.columns else "",
            }
            for _, row in worst.iterrows()
        ],
    )


def _find_process_column(df: pd.DataFrame) -> str | None:
    for col in ["Proceso", "Subproceso", "ProcesoPadre", "Proceso Padre"]:
        if col in df.columns:
            return col
    return None


def _process_counts(df: pd.DataFrame, process_col: str) -> pd.DataFrame:
    levels = ["Sobrecumplimiento", "Cumplimiento", "Alerta", "Peligro"]
    df = df.copy()
    if df.empty or process_col not in df.columns:
        return pd.DataFrame(columns=[process_col] + levels)
    if "Nivel de cumplimiento" not in df.columns:
        df = _ensure_nivel_cumplimiento(df)
    df["Nivel de cumplimiento"] = df["Nivel de cumplimiento"].fillna("Pendiente de reporte")
    df = df[df[process_col].notna()].copy()
    if df.empty:
        return pd.DataFrame(columns=[process_col] + levels)
    group_col = "Id" if "Id" in df.columns else process_col
    pivot = (
        df[df["Nivel de cumplimiento"].isin(levels)]
        .groupby([process_col, "Nivel de cumplimiento"])[group_col]
        .nunique()
        .reset_index(name="count")
        .pivot(index=process_col, columns="Nivel de cumplimiento", values="count")
        .fillna(0)
    )
    for lvl in levels:
        if lvl not in pivot.columns:
            pivot[lvl] = 0
    return pivot.reset_index()


def _ensure_tipo_proceso_column(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if "Tipo de proceso" in df.columns:
        return df

    candidates = [
        "Tipo de proceso_map",
        "Tipo de proceso_y",
        "Tipo de proceso_x",
        "Tipo_proceso",
        "tipo_proceso",
    ]
    for col in candidates:
        if col in df.columns:
            df = df.copy()
            df["Tipo de proceso"] = df[col]
            return df
    return df


def _ensure_proceso_column(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if "Proceso" in df.columns:
        return df

    candidates = [
        "Proceso_map",
        "Proceso_y",
        "Proceso_x",
        "Proceso Padre",
        "ProcesoPadre",
        "Proceso_Padre",
    ]
    for col in candidates:
        if col in df.columns:
            df = df.copy()
            df["Proceso"] = df[col]
            return df
    return df


def _filter_by_tipo_proceso(df: pd.DataFrame, tipo_seleccionado: str) -> pd.DataFrame:
    if df.empty or "Tipo de proceso" not in df.columns or tipo_seleccionado == "Todos":
        return df
    target = _norm_key(tipo_seleccionado)
    return df[df["Tipo de proceso"].astype(str).apply(_norm_key) == target].copy()


def _process_improvements(current: pd.DataFrame, previous: pd.DataFrame, process_col: str):
    if (
        current.empty
        or previous.empty
        or process_col not in current.columns
        or process_col not in previous.columns
    ):
        return [], []
    current = current[current["cumplimiento_pct"].notna()]
    previous = previous[previous["cumplimiento_pct"].notna()]
    curr_avg = (
        current.groupby(process_col)["cumplimiento_pct"].mean().reset_index(name="current_avg")
    )
    prev_avg = (
        previous.groupby(process_col)["cumplimiento_pct"].mean().reset_index(name="previous_avg")
    )
    merged = curr_avg.merge(prev_avg, on=process_col, how="inner")
    if merged.empty:
        return [], []
    merged["delta"] = merged["current_avg"] - merged["previous_avg"]
    top = merged.sort_values("delta", ascending=False).head(3)
    alerts = merged[
        (merged["current_avg"] >= 50) & (merged["current_avg"] < 80) & (merged["delta"] < 0)
    ]
    alerts = alerts.sort_values("delta").head(3)
    return (
        [
            {"name": str(row[process_col]), "change": float(row["delta"])}
            for _, row in top.iterrows()
        ],
        [
            {"name": str(row[process_col]), "change": float(row["delta"])}
            for _, row in alerts.iterrows()
        ],
    )


def _format_insights(items: list[dict], positive: bool = True):
    if not items:
        return []
    if positive:
        return [
            f"- **{item['name']}** mejora +{item['change']:.1f}% respecto al año anterior."
            for item in items
        ]
    return [
        f"- **{item['name']}** empeora {item['change']:.1f}% respecto al año anterior."
        for item in items
    ]


def _norm_key(value: str) -> str:
    import unicodedata
    import re

    txt = str(value or "").strip().lower()
    txt = unicodedata.normalize("NFD", txt)
    txt = "".join(ch for ch in txt if unicodedata.category(ch) != "Mn")
    txt = re.sub(r"[^0-9a-z]+", " ", txt)
    return re.sub(r"\s+", " ", txt).strip()


def _inject_dashboard_styles():
    st.markdown(
        """
        <style>
        .rg-header {
            background: linear-gradient(120deg, #0A1F3D 0%, #0D2B52 55%, #133A6B 100%);
            border: none;
            border-radius: 16px;
            padding: 1.4rem 1.6rem;
            box-shadow: 0 8px 28px rgba(8, 34, 75, 0.22);
            margin-bottom: 1rem;
            position: relative;
            overflow: hidden;
        }
        .rg-header::before {
            content: '';
            position: absolute;
            top: -40px; right: -40px;
            width: 180px; height: 180px;
            background: radial-gradient(circle, rgba(255,255,255,0.06) 0%, transparent 70%);
            pointer-events: none;
        }
        .rg-header-eyebrow {
            margin: 0 0 0.2rem 0;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #7EAADC;
        }
        .rg-header-title {
            margin: 0;
            color: #FFFFFF;
            font-size: 1.9rem;
            font-weight: 800;
            line-height: 1.15;
            letter-spacing: -0.01em;
        }
        .rg-header-subtitle {
            margin: 0.4rem 0 0 0;
            color: #A8C4E0;
            font-size: 0.88rem;
            font-weight: 400;
        }
        .rg-filter-label {
            color: #A8C4E0;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.3rem;
        }
        .rg-panel {
            background: linear-gradient(180deg, #F9FBFF 0%, #EEF4FB 100%);
            border: 1px solid #D9E3F1;
            border-radius: 16px;
            padding: 1rem;
            box-shadow: 0 8px 20px rgba(8, 34, 75, 0.08);
            margin-bottom: 1rem;
        }
        .rg-title {
            font-size: 2rem;
            font-weight: 800;
            color: #0E2A4D;
            margin: 0;
        }
        .rg-subtitle {
            color: #406080;
            margin-top: 0.2rem;
            margin-bottom: 0.2rem;
            font-size: 0.88rem;
        }
        .rg-card {
            border-radius: 14px;
            border: 1px solid #D6E2F0;
            background: #FFFFFF;
            padding: 0.7rem;
            box-shadow: 0 4px 10px rgba(0,0,0,0.07);
            min-height: 136px;
        }
        .rg-card-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.6rem;
        }
        .rg-icon {
            font-size: 1.6rem;
            width: 42px;
            height: 42px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(255,255,255,0.7);
            border: 1px solid rgba(0,0,0,0.06);
        }
        .rg-card-title {
            margin: 0;
            font-size: 0.95rem;
            color: #2A425D;
            font-weight: 700;
        }
        .rg-main-value {
            margin: 0;
            font-size: 1.55rem;
            font-weight: 800;
            line-height: 1.1;
        }
        .rg-meta {
            color: #546D88;
            font-size: 0.74rem;
            margin-top: 0.2rem;
        }
        .rg-chip {
            border-radius: 10px;
            background: #FFFFFF;
            border: 1px solid #D6E2F0;
            padding: 0.8rem;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }
        .rg-chip-value {
            font-size: 1.8rem;
            font-weight: 800;
            margin: 0;
            line-height: 1;
        }
        .rg-chip-label {
            margin: 0.2rem 0 0;
            color: #4F6781;
            font-size: 0.78rem;
            font-weight: 600;
        }
        .rg-ia {
            background: linear-gradient(135deg, #050E1F 0%, #0A1B3A 55%, #102A50 100%);
            border: 1px solid #2D4D79;
            border-radius: 14px;
            padding: 0.9rem;
            color: #F2F8FF;
            min-height: 220px;
            box-shadow: inset 0 0 0 1px rgba(110, 174, 255, 0.12);
        }
        .rg-ia h4 {
            margin: 0 0 0.6rem 0;
            font-size: 1rem;
            color: #E8F3FF;
        }
        .rg-bubble {
            border: 1px solid rgba(120, 192, 255, 0.55);
            border-radius: 14px;
            padding: 0.55rem 0.7rem;
            margin-bottom: 0.5rem;
            background: rgba(63, 121, 198, 0.22);
            font-size: 0.8rem;
            color: #F3F9FF;
        }
        .rg-ia-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 0.45rem;
            font-size: 0.78rem;
        }
        .rg-ia-table th, .rg-ia-table td {
            border-bottom: 1px solid rgba(128, 179, 230, 0.3);
            padding: 0.35rem 0.2rem;
            text-align: left;
            color: #F4F9FF;
        }
        .rg-ia-table th {
            color: #D2E7FF;
            font-size: 0.74rem;
            font-weight: 700;
        }
        .rg-ia-inline-title {
            color: #C8E4FF;
            font-size: 0.78rem;
            font-weight: 700;
            margin: 0.25rem 0 0.45rem 0;
        }
        .rg-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.86rem;
        }
        .rg-table th, .rg-table td {
            border-bottom: 1px solid #DEE7F4;
            padding: 0.45rem;
            text-align: left;
        }
        .rg-table th {
            color: #2A425D;
            font-weight: 700;
            font-size: 0.8rem;
            background: #F5F9FF;
        }
        .rg-process-card {
            border-radius: 12px;
            background: #FFFFFF;
            border: 1px solid #DAE4F1;
            box-shadow: 0 3px 8px rgba(0,0,0,0.06);
            padding: 0.75rem;
            min-height: 140px;
        }
        .rg-process-name {
            font-size: 0.84rem;
            font-weight: 700;
            margin: 0;
        }
        .rg-variation {
            font-size: 1.5rem;
            font-weight: 800;
            margin: 0.3rem 0 0;
            line-height: 1.1;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _sparkline_svg(color: str, up: bool = True) -> str:
    if up:
        path = "M2,24 C10,20 16,18 22,15 C28,12 34,18 40,14 C46,10 52,7 58,5"
    else:
        path = "M2,7 C10,10 16,12 22,15 C28,18 34,13 40,17 C46,21 52,24 58,26"
    return (
        "<svg width='62' height='30' viewBox='0 0 62 30' xmlns='http://www.w3.org/2000/svg'>"
        f"<path d='{path}' fill='none' stroke='{color}' stroke-width='2.3' stroke-linecap='round'/></svg>"
    )


def _render_strategy_card(
    title: str, indicators: int, cumplimiento: float, color: str, icon: str, historico=None
):
    """Renderiza una tarjeta de estrategia con mini gráfico de línea."""
    import streamlit as st

    # Generar mini gráfico de línea SVG si hay datos históricos
    sparkline = ""
    if historico is not None and not historico.empty and len(historico) >= 1:
        try:
            # Filtrar solo años hasta 2025
            df_sorted = historico[historico["Año"] <= 2025].sort_values("Año")
            if df_sorted.empty:
                df_sorted = historico.sort_values("Año")
            
            anos = [int(a) for a in df_sorted["Año"].values]
            valores = [float(v) for v in df_sorted["Cumplimiento"].values]
            
            if len(anos) >= 1:
                # Calcular puntos del gráfico
                width = 100
                height = 35
                min_v = min(valores) * 0.9
                max_v = max(valores) * 1.1
                if max_v == min_v:
                    max_v = min_v + 20
                
                # Generar puntos
                points = []
                for i, v in enumerate(valores):
                    if len(anos) == 1:
                        x = width / 2
                    else:
                        x = (i / (len(anos) - 1)) * width
                    y = height - ((v - min_v) / (max_v - min_v)) * height
                    points.append(f"{x:.1f},{y:.1f}")
                
                path_d = "M" + " L".join(points)
                
                # Tooltip
                tooltip = " - ".join([f"{a}:{v:.0f}%" for a, v in zip(anos, valores)])
                
                # Construir SVG manualmente
                svg_parts = []
                svg_parts.append(f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="display:block;margin:5px auto;">')
                svg_parts.append(f'<line x1="0" y1="{height/2}" x2="{width}" y2="{height/2}" stroke="#ddd" stroke-width="1" stroke-dasharray="3"/>')
                svg_parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="2"/>')
                for p in points:
                    xy = p.split(",")
                    svg_parts.append(f'<circle cx="{xy[0]}" cy="{xy[1]}" r="3" fill="{color}"/>')
                svg_parts.append(f'<title>{tooltip}</title>')
                svg_parts.append('</svg>')
                
                sparkline = "".join(svg_parts)
                
        except Exception as e:
            sparkline = f"<!-- Error: {str(e)} -->"

    # Construir HTML de la tarjeta con orden: icono, valor, indicadores, título, gráfico
    card_html = "<div class='rg-card' style='border-left:4px solid " + color + ";background:linear-gradient(140deg,#fff,#" + color[1:] + "1E);padding:12px;margin:5px 0;border-radius:8px;'>"
    card_html += "<div style='display:flex;align-items:center;margin-bottom:8px;'>"
    card_html += "<div style='font-size:28px;margin-right:10px;'>" + icon + "</div>"
    card_html += "<div style='text-align:right;flex:1;'>"
    card_html += "<div style='font-size:22px;font-weight:bold;color:" + color + ";'>" + f"{cumplimiento:.1f}%" + "</div>"
    card_html += "<div style='font-size:11px;color:#666;'>" + str(indicators) + " indicadores</div>"
    card_html += "</div></div>"
    card_html += "<div style='font-size:13px;font-weight:bold;margin-bottom:8px;color:#333;'>" + title + "</div>"
    card_html += sparkline
    card_html += "</div>"
    
    st.markdown(card_html, unsafe_allow_html=True)


def _render_chip(value: int, label: str, color: str):
    st.markdown(
        f"""
        <div class='rg-chip'>
            <p class='rg-chip-value' style='color:{color};'>{value}</p>
            <p class='rg-chip-label'>{label}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_process_card(name: str, indicadores: int, variation: float, color: str):
    up = variation >= 0
    variation_color = "#16A34A" if variation >= 0 else "#D32F2F"
    arrow = "↑" if up else "↓"
    spark = _sparkline_svg("#2A6BB0", up=up)
    st.markdown(
        f"""
        <div class='rg-process-card' style='border-top:4px solid {color};'>
            <p class='rg-process-name' style='color:{color};'>{name}</p>
            <p class='rg-meta'>{indicadores} indicadores</p>
            <p class='rg-variation' style='color:{variation_color};'>{abs(variation):.1f}% {arrow}</p>
            <p class='rg-meta'>Variacion</p>
            <div style='display:flex;justify-content:flex-end;margin-top:0.2rem;'>{spark}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_variation_table(title: str, rows: list[dict], positive: bool):
    if not rows:
        st.info("No hay comparativas disponibles.")
        return

    items_html = ""
    for row in rows:
        change = float(row.get("change", 0.0))
        sign = "+" if change >= 0 else ""
        color = "#16A34A" if (change >= 0) else "#D32F2F"
        icon = "↗" if (positive and change >= 0) else ("↘" if change < 0 else "↗")
        items_html += (
            "<tr>"
            f"<td>{row.get('name', '')}</td>"
            f"<td style='color:{color};font-weight:700;'>{icon} {sign}{change:.1f}%</td>"
            "</tr>"
        )

    st.markdown(
        f"""
        <div class='rg-panel'>
            <h4 style='margin:0 0 0.5rem 0; color:#173A62;'>{title}</h4>
            <table class='rg-table'>
                <thead><tr><th>Indicador</th><th>Variacion</th></tr></thead>
                <tbody>{items_html}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _build_ia_rows(rows: list[dict]) -> str:
    if not rows:
        return "<tr><td colspan='2'>Sin datos comparativos</td></tr>"
    out = ""
    for row in rows[:5]:
        change = float(row.get("change", 0.0) or 0.0)
        sign = "+" if change >= 0 else ""
        color = "#84F0A2" if change >= 0 else "#FF9FA3"
        out += (
            "<tr>"
            f"<td>{row.get('name', '')}</td>"
            f"<td style='color:{color};font-weight:700;'>{sign}{change:.1f}%</td>"
            "</tr>"
        )
    return out


def render():
    _inject_dashboard_styles()

    consolidado = _load_consolidado_cierres()
    if consolidado.empty:
        st.error(
            "No se pudo cargar la hoja 'Consolidado Cierres' desde data/output/Resultados Consolidados.xlsx."
        )
        return

    years = _available_years(consolidado)
    if not years:
        st.error("No se encontraron años válidos en los datos.")
        return

    st.markdown(
        """
        <div class='rg-header'>
            <p class='rg-header-eyebrow'>Politécnica Grancolombiana &nbsp;·&nbsp; Sistema de Indicadores</p>
            <h1 class='rg-header-title'>Plan de Desarrollo Institucional 2022–2026</h1>
            <p class='rg-header-subtitle'>Seguimiento estratégico de indicadores PDI &nbsp;·&nbsp; Cuadro de Mando Integral</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Selector de año y filtro de categoría
    _seg_col, _cat_col, _ = st.columns([2, 2, 3])
    with _seg_col:
        year_estrategico = st.segmented_control(
            "Año",
            options=years,
            default=years[-1],
            key="cmi_estrategico_year",
        )
    with _cat_col:
        categoria = st.segmented_control(
            "Vista",
            options=["Indicadores", "Proyectos", "Plan de Retos", "Consolidado"],
            default="Indicadores",
            key="cmi_categoria",
        )

    st.markdown("<div class='rg-panel'>", unsafe_allow_html=True)

    # --- Carga de datos según categoría ---
    linea_summary = pd.DataFrame()
    objetivo_df = pd.DataFrame()
    pdi_base_df = pd.DataFrame()
    historico_df = None
    if categoria == "Indicadores":
        pdi_estrategico = preparar_pdi_con_cierre(int(year_estrategico), 12)
        if pdi_estrategico is None or pdi_estrategico.empty:
            st.error("No se encontraron datos para los indicadores estratégicos del año seleccionado.")
            return
        pdi_estrategico = filter_df_for_cmi_estrategico(pdi_estrategico, id_column="Id")
        linea_summary = _build_linea_summary_from_df(pdi_estrategico)
        objetivo_df = pdi_estrategico[[c for c in ["Linea","Objetivo","cumplimiento_pct"] if c in pdi_estrategico.columns]].copy()
        pdi_base_df = pdi_estrategico.copy()
        # Historico solo para indicadores
        try:
            from services.strategic_indicators import load_cierres
            from services.cmi_filters import filter_df_for_cmi_estrategico
            cierres = load_cierres()
            if not cierres.empty:
                indicadores_cmi_path = Path(__file__).parents[2] / "data" / "raw" / "Indicadores por CMI.xlsx"
                df_cmi = pd.read_excel(indicadores_cmi_path, sheet_name=0, engine="openpyxl")
                df_cmi.columns = [str(c).strip() for c in df_cmi.columns]
                if "Id" in df_cmi.columns and "Linea" in df_cmi.columns:
                    cierres = cierres.copy()
                    cierres["Id"] = cierres["Id"].astype(str)
                    df_cmi = df_cmi.copy()
                    df_cmi["Id"] = df_cmi["Id"].astype(str)
                    id_linea = df_cmi[["Id", "Linea"]].drop_duplicates(subset=["Id"])
                    cierres_con_linea = cierres.merge(id_linea, on="Id", how="left")
                else:
                    cierres_con_linea = cierres
                cierres_con_linea = filter_df_for_cmi_estrategico(cierres_con_linea, id_column="Id")
                if "cumplimiento_pct" not in cierres_con_linea.columns:
                    cierres_con_linea["cumplimiento_pct"] = cierres_con_linea.apply(
                        lambda r: r["Ejecucion"] / r["Meta"] * 100 if r.get("Meta") and r["Meta"] != 0 else None, axis=1
                    )
                historico_df = cierres_con_linea
        except Exception:
            historico_df = None
    elif categoria == "Proyectos":
        pdi_proyectos = preparar_pdi_con_cierre(int(year_estrategico), 12)
        ids_proy = _get_proyectos_ids()
        if not pdi_proyectos.empty and ids_proy:
            pdi_proyectos = pdi_proyectos[pdi_proyectos["Id"].astype(str).isin(ids_proy)].copy()
        linea_summary = _build_linea_summary_from_df(pdi_proyectos)
        objetivo_df = pdi_proyectos[[c for c in ["Linea","Objetivo","cumplimiento_pct"] if c in pdi_proyectos.columns]].copy()
        pdi_base_df = pdi_proyectos.copy()
        historico_df = None
    elif categoria == "Plan de Retos":
        linea_df, obj_df = _load_plan_retos_data(int(year_estrategico))
        linea_summary = _build_linea_summary_from_retos(linea_df)
        objetivo_df = obj_df[[c for c in ["Linea","Objetivo","cumplimiento_pct"] if c in obj_df.columns]].copy()
        pdi_base_df = pd.DataFrame()  # No hay Ids ni variación
        historico_df = None
    elif categoria == "Consolidado":
        # Indicadores
        pdi_estrategico = preparar_pdi_con_cierre(int(year_estrategico), 12)
        pdi_estrategico = filter_df_for_cmi_estrategico(pdi_estrategico, id_column="Id")
        s1 = _build_linea_summary_from_df(pdi_estrategico)
        o1 = pdi_estrategico[[c for c in ["Linea","Objetivo","cumplimiento_pct"] if c in pdi_estrategico.columns]].copy()
        # Proyectos
        pdi_proyectos = preparar_pdi_con_cierre(int(year_estrategico), 12)
        ids_proy = _get_proyectos_ids()
        if not pdi_proyectos.empty and ids_proy:
            pdi_proyectos = pdi_proyectos[pdi_proyectos["Id"].astype(str).isin(ids_proy)].copy()
        s2 = _build_linea_summary_from_df(pdi_proyectos)
        o2 = pdi_proyectos[[c for c in ["Linea","Objetivo","cumplimiento_pct"] if c in pdi_proyectos.columns]].copy()
        # Plan de Retos
        linea_df, obj_df = _load_plan_retos_data(int(year_estrategico))
        s3 = _build_linea_summary_from_retos(linea_df)
        o3 = obj_df[[c for c in ["Linea","Objetivo","cumplimiento_pct"] if c in obj_df.columns]].copy()
        linea_summary, objetivo_df = _merge_consolidado_summaries(s1, s2, s3, o1, o2, o3)
        pdi_base_df = pd.DataFrame()  # No hay Ids ni variación
        historico_df = None

    # --- CHIPS DE MÉTRICAS ---
    _count_total_chips = int(linea_summary["N_Indicadores"].sum()) if not linea_summary.empty else 0
    _counts_chips = {
        "Sobrecumplimiento": int(linea_summary["Sobrecumplimiento"].sum()) if not linea_summary.empty else 0,
        "Cumplimiento": int(linea_summary["Cumplimiento"].sum()) if not linea_summary.empty else 0,
        "Alerta": int(linea_summary["Alerta"].sum()) if not linea_summary.empty else 0,
        "Peligro": int(linea_summary["Peligro"].sum()) if not linea_summary.empty else 0,
    }
    _chip_cols = st.columns(5)
    _chip_cfg = [
        (_count_total_chips, "Total", "#0B5FFF"),
        (_counts_chips["Sobrecumplimiento"], "Sobrecumplimiento", "#173D66"),
        (_counts_chips["Cumplimiento"], "Cumplimiento", "#16A34A"),
        (_counts_chips["Alerta"], "Alerta", "#F59E0B"),
        (_counts_chips["Peligro"], "Peligro", "#D32F2F"),
    ]
    for _cc, (_cv, _cl, _co) in zip(_chip_cols, _chip_cfg):
        with _cc:
            _render_chip(_cv, _cl, _co)

    # --- Fichas por línea estratégica ---
    strategic_defs = [
        {"key": "expansion", "alt": [], "label": "Expansion", "icon": "🚀", "color": "#FBAF17"},
        {"key": "transformacion organizacional", "alt": ["transformacion organizacional"], "label": "Transformacion organizacional", "icon": "📈", "color": "#42F2F2"},
        {"key": "calidad", "alt": [], "label": "Calidad", "icon": "🏅", "color": "#EC0677"},
        {"key": "experiencia", "alt": [], "label": "Experiencia", "icon": "💡", "color": "#1FB2DE"},
        {"key": "sostenibilidad", "alt": ["sustentabilidad"], "label": "Sostenibilidad", "icon": "🌱", "color": "#A6CE38"},
        {"key": "educacion para toda la vida", "alt": ["educacion para toda la vida"], "label": "Educacion para toda la vida", "icon": "🎓", "color": "#0F385A"},
    ]
    norm_to_row = {}
    for _, row in linea_summary.iterrows():
        norm_to_row[_norm_key(str(row["Linea"]))] = row
    ficha_cols = st.columns(6)
    for idx, card_def in enumerate(strategic_defs):
        row = norm_to_row.get(card_def["key"])
        if row is None:
            alt_keys = [card_def["key"]] + card_def.get("alt", [])
            matched = [k for k in norm_to_row.keys() if any(ak in k for ak in alt_keys)]
            row = norm_to_row.get(matched[0]) if matched else None
        n_ind = int(row["N_Indicadores"]) if row is not None else 0
        cumpl = float(row["Cumpl_Promedio"]) if row is not None else 0.0
        historico = None
        if categoria == "Indicadores" and row is not None and historico_df is not None and not historico_df.empty:
            try:
                linea_nombre = row["Linea"]
                df_hist = historico_df[historico_df["Linea"] == linea_nombre].copy()
                if not df_hist.empty and "Anio" in df_hist.columns and "cumplimiento_pct" in df_hist.columns:
                    historico = (
                        df_hist.groupby("Anio", dropna=False)["cumplimiento_pct"].mean().reset_index()
                    )
                    historico = historico[historico["Anio"].notna()]
                    historico = historico.rename(columns={"Anio": "Año", "cumplimiento_pct": "Cumplimiento"})
                    historico = historico.sort_values("Año")
            except Exception:
                pass
        with ficha_cols[idx % 6]:
            _render_strategy_card(
                title=card_def["label"],
                indicators=n_ind,
                cumplimiento=cumpl,
                color=card_def["color"],
                icon=card_def["icon"],
                historico=historico,
            )

    # --- Sunburst ---
    st.markdown("<div style='margin-top:1.5rem;'><b>Alineación de Objetivos Estratégicos</b></div>", unsafe_allow_html=True)
    sunburst = _build_sunburst(objetivo_df)
    st.plotly_chart(sunburst, use_container_width=True)

    # --- Tablas de variación (solo para Indicadores y Proyectos) ---
    best_improvements_e = []
    worst_declines_e = []
    prev_year_e = year_estrategico - 1
    prev_month_e = _latest_month_for_year(consolidado, prev_year_e)
    if categoria in ["Indicadores", "Proyectos"] and not pdi_base_df.empty and prev_month_e:
        prev_df = preparar_pdi_con_cierre(prev_year_e, prev_month_e)
        if categoria == "Indicadores":
            prev_df = filter_df_for_cmi_estrategico(prev_df, id_column="Id")
        elif categoria == "Proyectos":
            ids_proy = _get_proyectos_ids()
            prev_df = prev_df[prev_df["Id"].astype(str).isin(ids_proy)].copy()
        best_improvements_e, worst_declines_e = _compute_trends(pdi_base_df, prev_df)
    # Para Plan de Retos y Consolidado, no hay variación por Id

    # --- Chips de salud y narrativa ejecutiva ---
    count_total_e = int(linea_summary["N_Indicadores"].sum()) if not linea_summary.empty else 0
    counts_e = {
        "Sobrecumplimiento": int(linea_summary["Sobrecumplimiento"].sum()) if not linea_summary.empty else 0,
        "Cumplimiento": int(linea_summary["Cumplimiento"].sum()) if not linea_summary.empty else 0,
        "Alerta": int(linea_summary["Alerta"].sum()) if not linea_summary.empty else 0,
        "Peligro": int(linea_summary["Peligro"].sum()) if not linea_summary.empty else 0,
    }
    health_rate_e = round(((counts_e["Sobrecumplimiento"] + counts_e["Cumplimiento"]) / max(count_total_e, 1)) * 100, 1)

    # --- Tabla de Indicadores sin gestión ---
    if categoria in ["Indicadores", "Consolidado"]:
        sin_gestion_df = _get_sin_gestion_df()
        if not sin_gestion_df.empty:
            st.markdown("<div style='margin-top:2rem;'><b>Indicadores sin gestión (Plan anual = 3)</b></div>", unsafe_allow_html=True)
            st.dataframe(sin_gestion_df, hide_index=True, use_container_width=True)
    # ── Tablas de variación con Línea coloreada ─────────────────────────────
    _LINEA_COLORS_BADGE = {
        "expansion": ("#FBAF17", "#FFFFFF"),
        "transformacion organizacional": ("#0891b2", "#FFFFFF"),
        "calidad": ("#EC0677", "#FFFFFF"),
        "experiencia": ("#1FB2DE", "#FFFFFF"),
        "sostenibilidad": ("#A6CE38", "#1A2E05"),
        "educacion para toda la vida": ("#0F385A", "#FFFFFF"),
    }

    def _build_trend_rows_with_linea(rows: list[dict], positive: bool) -> str:
        if not rows:
            return "<tr><td colspan='3' style='color:#94A3B8;font-size:0.8rem;padding:0.6rem;'>Sin datos comparativos</td></tr>"
        out = ""
        for row in rows[:5]:
            change = float(row.get("change", 0.0) or 0.0)
            sign = "+" if change >= 0 else ""
            val_color = "#16A34A" if change >= 0 else "#DC2626"
            val_bg = "#F0FDF4" if change >= 0 else "#FFF1F2"
            linea = row.get("linea", "")
            _lc = _norm_key(linea)
            bg_col, txt_col = _LINEA_COLORS_BADGE.get(_lc, ("#64748B", "#FFFFFF"))
            # Abreviar nombre de línea largo
            linea_short = (
                linea.replace("Transformación organizacional", "Transformación")
                     .replace("transformacion organizacional", "Transformación")
                     .replace("Educación para toda la vida", "Edu. toda la vida")
                     .replace("educacion para toda la vida", "Edu. toda la vida")
            )
            badge = (
                f"<span style='"
                f"background:{bg_col};color:{txt_col};"
                f"border-radius:999px;"
                f"padding:3px 10px;"
                f"font-size:0.72rem;font-weight:700;"
                f"white-space:nowrap;"
                f"display:inline-block;"
                f"'>{linea_short}</span>"
                if linea else ""
            )
            out += (
                "<tr style='border-bottom:1px solid #F1F5F9;'>"
                f"<td style='padding:0.45rem 0.5rem;font-size:0.82rem;color:#1E293B;'>{row.get('name', '')}</td>"
                f"<td style='padding:0.45rem 0.4rem;'>{badge}</td>"
                f"<td style='padding:0.4rem 0.5rem;'>"
                f"<span style='background:{val_bg};color:{val_color};border-radius:6px;"
                f"padding:3px 8px;font-weight:700;font-size:0.82rem;white-space:nowrap;'>{sign}{change:.1f}%</span>"
                f"</td>"
                "</tr>"
            )
        return out

    best_rows_html = _build_trend_rows_with_linea(best_improvements_e, positive=True)
    worst_rows_html = _build_trend_rows_with_linea(worst_declines_e, positive=False)

    # Texto del período comparado
    _mes_nombres = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                    "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    if prev_month_e:
        _mes_base = _mes_nombres[prev_month_e - 1] if 1 <= prev_month_e <= 12 else str(prev_month_e)
        _periodo_txt = f"Comparando <strong>{year_estrategico}</strong> (cierre anual) vs <strong>{prev_year_e}</strong> ({_mes_base})"
    else:
        _periodo_txt = f"Solo datos de <strong>{year_estrategico}</strong> — sin período anterior disponible"

    # ── Narrativa ejecutiva dinámica ────────────────────────────────────────────
    if health_rate_e >= 85:
        estado_inst = "sobresaliente"
        estado_color = "#16A34A"
        estado_icon = "✅"
    elif health_rate_e >= 70:
        estado_inst = "satisfactorio"
        estado_color = "#2563EB"
        estado_icon = "📊"
    elif health_rate_e >= 50:
        estado_inst = "moderado con oportunidades de mejora"
        estado_color = "#D97706"
        estado_icon = "⚠️"
    else:
        estado_inst = "crítico y requiere atención prioritaria"
        estado_color = "#DC2626"
        estado_icon = "🚨"

    mejor_linea_txt = ""
    if not pdi_estrategico.empty and "Linea" in pdi_estrategico.columns:
        _top_linea = (
            pdi_estrategico.groupby("Linea")["cumplimiento_pct"]
            .mean()
            .reset_index()
            .sort_values("cumplimiento_pct", ascending=False)
        )
        if not _top_linea.empty:
            _ln = _top_linea.iloc[0]
            mejor_linea_txt = (
                f'La línea <strong>{_ln["Linea"]}</strong> lidera el cumplimiento '
                f'con un promedio de <strong>{_ln["cumplimiento_pct"]:.1f}%</strong>. '
            )

    alerta_txt = ""
    if counts_e["Alerta"] + counts_e["Peligro"] > 0:
        alerta_txt = (
            f'Se identifican <strong>{counts_e["Alerta"]} indicadores en alerta</strong> y '
            f'<strong>{counts_e["Peligro"]} en peligro</strong> que requieren seguimiento inmediato. '
        )
    else:
        alerta_txt = "No se registran indicadores en estado crítico en este corte. "

    mejora_txt = ""
    if best_improvements_e:
        top_m = best_improvements_e[0]
        mejora_txt = (
            f'El indicador <strong>"{top_m["name"]}"</strong> registra la mayor mejora '
            f'con <strong>+{top_m["change"]:.1f}%</strong> respecto al período anterior. '
        )

    riesgo_txt = ""
    if worst_declines_e:
        top_r = worst_declines_e[0]
        riesgo_txt = (
            f'Se recomienda atención sobre <strong>"{top_r["name"]}"</strong>, '
            f'que presenta una variación de <strong>{top_r["change"]:.1f}%</strong>.'
        )

    narrativa = (
        f'La institución presenta un desempeño estratégico <strong style="color:{estado_color};">'
        f'{estado_inst}</strong>: el <strong>{health_rate_e}%</strong> de los indicadores PDI '
        f'se encuentran en niveles saludables '
        f'(<strong>{counts_e["Sobrecumplimiento"]}</strong> en sobrecumplimiento y '
        f'<strong>{counts_e["Cumplimiento"]}</strong> en cumplimiento sobre '
        f'<strong>{count_total_e}</strong> totales). '
        f'{mejor_linea_txt}{alerta_txt}{mejora_txt}{riesgo_txt}'
    )

    # ── Narrativa ejecutiva (antes de gráficas y fichas) ───────────────────────
    st.markdown(
        f"""
        <div style='
            background: linear-gradient(135deg, #FFFFFF 0%, #F0F6FF 100%);
            border: 1.5px solid #BFDBFE;
            border-left: 6px solid {estado_color};
            border-radius: 14px;
            padding: 1.1rem 1.3rem;
            box-shadow: 0 4px 18px rgba(37,99,235,0.10);
            margin-bottom: 1.2rem;
        '>
            <div style='display:flex; align-items:center; gap:0.5rem; margin-bottom:0.55rem;'>
                <span style='font-size:1.25rem;'>{estado_icon}</span>
                <span style='font-size:1rem;font-weight:800;color:#1E3A5F;letter-spacing:0.01em;'>Narrativa Ejecutiva</span>
            </div>
            <p style='margin:0;font-size:0.93rem;line-height:1.65;color:#1E293B;'>{narrativa}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Tablas de mejoras/riesgos (antes de gráficas) ───────────────────────
    ia_c1, ia_c2 = st.columns(2)
    _th = "color:#475569;padding:0.4rem 0.5rem;border-bottom:2px solid #E2E8F0;font-size:0.78rem;font-weight:700;text-align:left;"
    _footer_style = "margin:0.6rem 0 0 0;font-size:0.73rem;color:#94A3B8;border-top:1px solid #F1F5F9;padding-top:0.45rem;"
    with ia_c1:
        st.markdown(
            f"""
            <div style='background:#FFFFFF;border:1px solid #D1FAE5;border-left:5px solid #16A34A;
                        border-radius:12px;padding:0.85rem 1rem;
                        box-shadow:0 2px 10px rgba(22,163,74,0.08);'>
                <div style='font-size:0.85rem;font-weight:700;color:#15803D;margin-bottom:0.6rem;'>↗ Indicadores que mejoraron</div>
                <table style='width:100%;border-collapse:collapse;'>
                    <thead><tr>
                        <th style='{_th}'>Indicador</th>
                        <th style='{_th}'>Línea</th>
                        <th style='{_th}'>Variación</th>
                    </tr></thead>
                    <tbody>{best_rows_html}</tbody>
                </table>
                <p style='{_footer_style}'>🗓️ {_periodo_txt}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with ia_c2:
        st.markdown(
            f"""
            <div style='background:#FFFFFF;border:1px solid #FECACA;border-left:5px solid #DC2626;
                        border-radius:12px;padding:0.85rem 1rem;
                        box-shadow:0 2px 10px rgba(220,38,38,0.08);'>
                <div style='font-size:0.85rem;font-weight:700;color:#B91C1C;margin-bottom:0.6rem;'>↘ Indicadores en riesgo</div>
                <table style='width:100%;border-collapse:collapse;'>
                    <thead><tr>
                        <th style='{_th}'>Indicador</th>
                        <th style='{_th}'>Línea</th>
                        <th style='{_th}'>Variación</th>
                    </tr></thead>
                    <tbody>{worst_rows_html}</tbody>
                </table>
                <p style='{_footer_style}'>🗓️ {_periodo_txt}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    render()
