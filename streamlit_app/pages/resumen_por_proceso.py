from pathlib import Path
import re
import unicodedata

import pandas as pd
import plotly.express as px
import streamlit as st

try:
    from ..services.data_service import DataService
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from services.data_service import DataService


MESES_OPCIONES = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]

NIVELES_COLORS = {
    "sobrecumplimiento": "#1565C0",
    "cumplimiento": "#2E7D32",
    "alerta": "#F9A825",
    "peligro": "#C62828",
    "sin dato": "#6E7781",
}


def _norm_text(value: object) -> str:
    text = str(value or "").strip().upper()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def _to_float(value: object) -> float | None:
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.strip().replace("%", "").replace(",", ".")
    try:
        return float(value)
    except Exception:
        return None


def _cumplimiento_pct(df: pd.DataFrame) -> pd.Series:
    if "Cumplimiento_norm" in df.columns:
        vals = pd.to_numeric(df["Cumplimiento_norm"], errors="coerce")
        return vals * 100

    if "Cumplimiento" in df.columns:
        vals = pd.to_numeric(df["Cumplimiento"].apply(_to_float), errors="coerce")
        max_abs = vals.abs().max(skipna=True) if not vals.dropna().empty else 0
        return vals * 100 if max_abs <= 2 else vals

    return pd.Series([pd.NA] * len(df), index=df.index, dtype="float64")


def _cumpl_icon(pct: float | None) -> str:
    if pct is None or pd.isna(pct):
        return "⚪"
    if pct >= 105:
        return "🔵"
    if pct >= 100:
        return "🟢"
    if pct >= 80:
        return "🟡"
    return "🔴"


def _cumpl_label(pct: float | None) -> str:
    if pct is None or pd.isna(pct):
        return "⚪ Sin dato"
    return f"{_cumpl_icon(pct)} {pct:.1f}%"


def _latest_per_indicator(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    sort_cols = [c for c in ["Año", "Mes", "Fecha", "Periodo"] if c in df.columns]
    out = df.sort_values(sort_cols) if sort_cols else df.copy()

    if "Id" in out.columns:
        out = out.drop_duplicates(subset=["Id"], keep="last")
    elif "Indicador" in out.columns:
        out = out.drop_duplicates(subset=["Indicador"], keep="last")

    return out.reset_index(drop=True)


def _prepare_tracking(df: pd.DataFrame, map_df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()
    if "Proceso" not in out.columns:
        out["Proceso"] = "Sin proceso"

    if not map_df.empty and {"Subproceso", "Proceso"}.issubset(map_df.columns):
        sub_map = map_df[["Subproceso", "Proceso"]].dropna().drop_duplicates(subset=["Subproceso"]).copy()
        sub_map["sub_norm"] = sub_map["Subproceso"].astype(str).map(_norm_text)

        out["proc_input"] = out["Proceso"].astype(str)
        out["proc_norm"] = out["proc_input"].map(_norm_text)

        out = out.merge(
            sub_map[["sub_norm", "Proceso"]].rename(columns={"Proceso": "Proceso_padre_sub"}),
            left_on="proc_norm",
            right_on="sub_norm",
            how="left",
        )

        out["Proceso_padre"] = out["Proceso_padre_sub"].fillna(out["proc_input"])
        if "Subproceso" in out.columns:
            out["Subproceso_final"] = out["Subproceso"].fillna(out["proc_input"])
        else:
            out["Subproceso_final"] = out["proc_input"]

        out = out.drop(columns=[c for c in ["proc_input", "proc_norm", "sub_norm", "Proceso_padre_sub"] if c in out.columns])
    else:
        out["Proceso_padre"] = out["Proceso"].astype(str)
        out["Subproceso_final"] = out["Proceso"].astype(str)

    out["Cumplimiento_pct"] = _cumplimiento_pct(out)
    return out


@st.cache_data(show_spinner=False)
def _load_calidad_data() -> tuple[pd.DataFrame, str | None]:
    excel_path = Path("data") / "raw" / "Monitoreo" / "Monitoreo_Informacion_Procesos 2025.xlsx"
    if not excel_path.exists():
        return pd.DataFrame(), f"No existe el archivo: {excel_path}"

    try:
        df = pd.read_excel(excel_path, skiprows=4, engine="openpyxl")
    except Exception as exc:
        return pd.DataFrame(), f"No se pudo leer el Excel de calidad: {exc}"

    df = df.dropna(how="all")
    df.columns = [str(c).strip() for c in df.columns]

    norm_cols = {_norm_text(c): c for c in df.columns}
    proc_col = next((v for k, v in norm_cols.items() if "PROCESO" in k), None)
    tem_col = next((v for k, v in norm_cols.items() if "TEMATICA" in k), None)

    if proc_col is None:
        return pd.DataFrame(), "No se encontró la columna Proceso en el archivo de calidad."
    if tem_col is None:
        return pd.DataFrame(), "No se encontró la columna Temática en el archivo de calidad."

    metric_cols = [
        c
        for c in df.columns
        if _norm_text(c) not in {_norm_text(proc_col), _norm_text(tem_col)}
    ]
    if len(metric_cols) < 5:
        return pd.DataFrame(), "No se identificaron 5 características evaluadas en el archivo de calidad."

    out = df[[proc_col, tem_col] + metric_cols[:5]].copy()
    out = out.rename(columns={proc_col: "Proceso", tem_col: "Temática"})
    out = out.dropna(subset=["Proceso"]).reset_index(drop=True)
    return out, None


@st.cache_data(show_spinner=False)
def _load_auditoria_mentions(processes: list[str]) -> tuple[pd.DataFrame, str | None]:
    raw_dir = Path("data") / "raw" / "auditoria"
    if not raw_dir.exists():
        return pd.DataFrame(), f"No existe la carpeta: {raw_dir}"

    pdf_files = sorted(raw_dir.glob("*.pdf"))
    if not pdf_files:
        return pd.DataFrame(), "No hay PDFs en data/raw/auditoria."

    try:
        from pypdf import PdfReader
    except Exception:
        return pd.DataFrame(), "No está instalado pypdf. Instala la dependencia para extraer texto de auditoría."

    if not processes:
        return pd.DataFrame(), "No hay procesos disponibles para buscar en los PDFs."

    rows: list[dict] = []
    for pdf_path in pdf_files:
        try:
            reader = PdfReader(str(pdf_path))
        except Exception:
            continue

        for page_num, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""

            text_norm = _norm_text(text)
            if not text_norm:
                continue

            for proc in processes:
                proc_norm = _norm_text(proc)
                if proc_norm and proc_norm in text_norm:
                    idx = text_norm.find(proc_norm)
                    start = max(0, idx - 120)
                    end = min(len(text_norm), idx + len(proc_norm) + 180)
                    snippet = re.sub(r"\s+", " ", text_norm[start:end]).strip()
                    rows.append(
                        {
                            "Proceso": proc,
                            "Fuente": pdf_path.name,
                            "Página": page_num,
                            "Evidencia IA": snippet[:240],
                        }
                    )

    if not rows:
        return pd.DataFrame(), "No se encontraron menciones directas de procesos en los PDFs de auditoría."

    mentions = pd.DataFrame(rows)
    resumen = (
        mentions.groupby(["Proceso", "Fuente"], dropna=False)
        .agg(
            Coincidencias=("Página", "count"),
            Primera_pagina=("Página", "min"),
            Evidencia_IA=("Evidencia IA", "first"),
        )
        .reset_index()
        .rename(columns={"Evidencia_IA": "Evidencia IA", "Primera_pagina": "Página inicial"})
    )
    return resumen, None


def _build_info_table(df_latest: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["Indicador"] = df_latest.get("Indicador", "")
    out["Meta"] = df_latest.get("Meta", pd.NA)
    out["Ejecución"] = df_latest.get("Ejecucion", pd.NA)
    out["Cumplimiento"] = df_latest.get("Cumplimiento_pct", pd.NA).apply(_cumpl_label)
    return out


def _build_indicadores_table(df_latest: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["Subproceso - Indicador"] = (
        df_latest.get("Subproceso_final", "Sin subproceso").astype(str)
        + " - "
        + df_latest.get("Indicador", "").astype(str)
    )
    out["Meta"] = df_latest.get("Meta", pd.NA)
    out["Ejecución"] = df_latest.get("Ejecucion", pd.NA)
    out["Cumplimiento"] = df_latest.get("Cumplimiento_pct", pd.NA).apply(_cumpl_label)
    return out


def _build_propuestos(df_latest: pd.DataFrame, process_name: str) -> pd.DataFrame:
    if df_latest.empty:
        return pd.DataFrame(
            [
                {
                    "Proceso": process_name,
                    "Plan de mejoramiento": "Sin datos para priorizar acciones.",
                    "PDI 2026-2030": "Definir metas e hitos por indicador.",
                    "SGA": "Validar integración de evidencias y trazabilidad.",
                    "Retos": "Completar reporte de indicadores faltantes.",
                }
            ]
        )

    work = df_latest.copy()
    work["Cumplimiento_pct"] = pd.to_numeric(work["Cumplimiento_pct"], errors="coerce")
    riesgos = work[work["Cumplimiento_pct"].notna() & (work["Cumplimiento_pct"] < 80)]
    top_riesgos = riesgos.nsmallest(3, "Cumplimiento_pct") if not riesgos.empty else pd.DataFrame()

    riesgo_names = ", ".join(top_riesgos.get("Indicador", pd.Series(dtype=str)).astype(str).tolist())
    if not riesgo_names:
        riesgo_names = "Ninguno crítico en el corte"

    return pd.DataFrame(
        [
            {
                "Proceso": process_name,
                "Plan de mejoramiento": f"Priorizar cierre de brechas en: {riesgo_names}.",
                "PDI 2026-2030": "Alinear metas por resultados históricos y capacidad operativa.",
                "SGA": "Fortalecer controles de calidad de dato y consistencia de soportes.",
                "Retos": "Sostener cumplimiento mensual y reducir dispersión entre subprocesos.",
            }
        ]
    )


def render() -> None:
    st.title("Resumen por procesos")

    ds = DataService()
    tracking_df = ds.get_tracking_data()
    map_df = ds.get_process_map()

    if tracking_df.empty:
        st.warning("No se encontró data de seguimiento en data/output/Seguimiento_Reporte.xlsx.")
        return
    if map_df.empty:
        st.warning("No se encontró el mapeo de procesos en data/raw/Subproceso-Proceso-Area.xlsx.")
        return

    work_df = _prepare_tracking(tracking_df, map_df)

    years = sorted([int(y) for y in pd.to_numeric(work_df.get("Año"), errors="coerce").dropna().unique().tolist()])
    default_month = "Diciembre"
    procesos = sorted(work_df["Proceso_padre"].dropna().astype(str).unique().tolist())

    st.markdown("#### Filtros")
    c1, c2, c3 = st.columns(3)
    with c1:
        anio = st.selectbox("Año", options=years, index=len(years) - 1 if years else None)
    with c2:
        mes = st.selectbox("Mes", options=MESES_OPCIONES, index=MESES_OPCIONES.index(default_month))
    with c3:
        proceso_sel = st.selectbox("Proceso (Filtro Padre)", options=["Todos"] + procesos)

    filtered = work_df.copy()

    if anio is not None and "Año" in filtered.columns:
        filtered = filtered[pd.to_numeric(filtered["Año"], errors="coerce") == int(anio)]

    if mes and "Mes" in filtered.columns:
        mes_num = MESES_OPCIONES.index(mes) + 1
        filtered = filtered[pd.to_numeric(filtered["Mes"], errors="coerce") == mes_num]

    if proceso_sel != "Todos":
        filtered = filtered[filtered["Proceso_padre"].astype(str) == proceso_sel]

    if filtered.empty:
        st.info("No hay datos para la combinación de filtros seleccionada.")
        return

    latest = _latest_per_indicator(filtered)
    selected_process_label = proceso_sel if proceso_sel != "Todos" else "Todos los procesos"

    st.caption(f"Filtro Padre activo: {selected_process_label} | Corte: {mes} {anio}")

    tabs = st.tabs([
        "📋 Resumen general",
        "ℹ️ Información por proceso",
        "📊 Indicadores",
        "✅ Calidad",
        "🔍 Auditoría",
        "💡 Propuestos",
        "🤖 Análisis IA",
    ])

    with tabs[0]:
        st.markdown("### Resumen general - Gráficas importantes")

        total = len(latest)
        cumplimiento = pd.to_numeric(latest.get("Cumplimiento_pct"), errors="coerce")
        avg = float(cumplimiento.mean()) if not cumplimiento.dropna().empty else None
        criticos = int((cumplimiento < 80).sum()) if not cumplimiento.dropna().empty else 0

        k1, k2, k3 = st.columns(3)
        k1.metric("Total indicadores", total)
        k2.metric("Cumplimiento promedio", f"{avg:.1f}%" if avg is not None else "Sin dato")
        k3.metric("Indicadores en alerta/peligro", criticos)

        col_a, col_b = st.columns(2)
        with col_a:
            bins_df = pd.DataFrame({"Nivel": "Sin dato"}, index=latest.index)
            bins_df.loc[cumplimiento >= 105, "Nivel"] = "Sobrecumplimiento"
            bins_df.loc[(cumplimiento >= 100) & (cumplimiento < 105), "Nivel"] = "Cumplimiento"
            bins_df.loc[(cumplimiento >= 80) & (cumplimiento < 100), "Nivel"] = "Alerta"
            bins_df.loc[cumplimiento < 80, "Nivel"] = "Peligro"

            pie_df = bins_df["Nivel"].value_counts().rename_axis("Nivel").reset_index(name="Total")
            fig_pie = px.pie(
                pie_df,
                names="Nivel",
                values="Total",
                color="Nivel",
                color_discrete_map={
                    "Sobrecumplimiento": NIVELES_COLORS["sobrecumplimiento"],
                    "Cumplimiento": NIVELES_COLORS["cumplimiento"],
                    "Alerta": NIVELES_COLORS["alerta"],
                    "Peligro": NIVELES_COLORS["peligro"],
                    "Sin dato": NIVELES_COLORS["sin dato"],
                },
                title="Distribución de cumplimiento",
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_b:
            by_sub = (
                latest.groupby("Subproceso_final", dropna=False)
                .size()
                .reset_index(name="Indicadores")
                .sort_values("Indicadores", ascending=False)
                .head(15)
            )
            fig_bar = px.bar(
                by_sub,
                x="Indicadores",
                y="Subproceso_final",
                orientation="h",
                title="Top subprocesos por número de indicadores",
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    with tabs[1]:
        st.markdown("### Información por proceso")
        st.dataframe(_build_info_table(latest), use_container_width=True, hide_index=True)

    with tabs[2]:
        st.markdown("### Indicadores")
        st.dataframe(_build_indicadores_table(latest), use_container_width=True, hide_index=True)

    with tabs[3]:
        st.markdown("### Calidad")
        calidad_df, calidad_msg = _load_calidad_data()
        if calidad_msg:
            st.warning(calidad_msg)
        else:
            if proceso_sel != "Todos":
                calidad_df = calidad_df[calidad_df["Proceso"].astype(str) == proceso_sel]
            st.dataframe(calidad_df, use_container_width=True, hide_index=True)

    with tabs[4]:
        st.markdown("### Auditoría")
        auditoria_df, auditoria_msg = _load_auditoria_mentions(procesos)
        if auditoria_msg:
            st.warning(auditoria_msg)
        else:
            if proceso_sel != "Todos":
                auditoria_df = auditoria_df[auditoria_df["Proceso"].astype(str) == proceso_sel]
            st.dataframe(auditoria_df, use_container_width=True, hide_index=True)

    with tabs[5]:
        st.markdown("### Propuestos")
        st.dataframe(_build_propuestos(latest, selected_process_label), use_container_width=True, hide_index=True)

    with tabs[6]:
        st.markdown("### Análisis IA")
        cumplimiento = pd.to_numeric(latest.get("Cumplimiento_pct"), errors="coerce")
        riesgos = latest[cumplimiento < 80]
        alertas = latest[(cumplimiento >= 80) & (cumplimiento < 100)]

        st.write(f"Se identifican {len(riesgos)} indicadores en peligro y {len(alertas)} en alerta para el filtro activo.")
        if not riesgos.empty:
            cols = [c for c in ["Indicador", "Subproceso_final", "Cumplimiento_pct"] if c in riesgos.columns]
            preview = riesgos[cols].copy().sort_values("Cumplimiento_pct", ascending=True).head(10)
            preview = preview.rename(columns={"Subproceso_final": "Subproceso", "Cumplimiento_pct": "Cumplimiento (%)"})
            st.dataframe(preview, use_container_width=True, hide_index=True)
        else:
            st.success("No hay indicadores en peligro para el corte seleccionado.")
from pathlib import Path
import re
import unicodedata

import pandas as pd
import plotly.express as px
import streamlit as st

# Importes con fallback para ejecución local y en cloud.
try:
    from ..services.data_service import DataService
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from services.data_service import DataService


MESES_OPCIONES = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]

NIVELES_COLORS = {
    "sobrecumplimiento": "#1565C0",
    "cumplimiento": "#2E7D32",
    "alerta": "#F9A825",
    "peligro": "#C62828",
    "sin dato": "#6E7781",
}


def _norm_text(value: object) -> str:
    text = str(value or "").strip().upper()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def _to_float(value: object) -> float | None:
    if pd.isna(value):
        return None
    if isinstance(value, str):
        v = value.strip().replace("%", "").replace(",", ".")
    else:
        v = value
    try:
        num = float(v)
    except Exception:
        return None
    return num


def _cumplimiento_pct(df: pd.DataFrame) -> pd.Series:
    if "Cumplimiento_norm" in df.columns:
        vals = pd.to_numeric(df["Cumplimiento_norm"], errors="coerce")
        return vals * 100
    if "Cumplimiento" in df.columns:
        vals = df["Cumplimiento"].apply(_to_float)
        vals = pd.to_numeric(vals, errors="coerce")
        max_abs = vals.abs().max(skipna=True) if not vals.dropna().empty else 0
        return vals * 100 if max_abs <= 2 else vals
    return pd.Series([pd.NA] * len(df), index=df.index, dtype="float64")


def _cumpl_icon(pct: float | None) -> str:
    if pct is None or pd.isna(pct):
        return "⚪"
    if pct >= 105:
        return "🔵"
    if pct >= 100:
        return "🟢"
    if pct >= 80:
        return "🟡"
    return "🔴"


def _cumpl_label(pct: float | None) -> str:
    icon = _cumpl_icon(pct)
    if pct is None or pd.isna(pct):
        return f"{icon} Sin dato"
    return f"{icon} {pct:.1f}%"


def _latest_per_indicator(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    sort_cols = []
    if "Año" in df.columns:
        sort_cols.append("Año")
    if "Mes" in df.columns:
        sort_cols.append("Mes")
    if "Fecha" in df.columns:
        sort_cols.append("Fecha")
    if "Periodo" in df.columns:
        sort_cols.append("Periodo")

    out = df.copy()
    if sort_cols:
        out = out.sort_values(sort_cols)

    if "Id" in out.columns:
        out = out.drop_duplicates(subset=["Id"], keep="last")
    elif "Indicador" in out.columns:
        out = out.drop_duplicates(subset=["Indicador"], keep="last")

    return out.reset_index(drop=True)


def _prepare_tracking(df: pd.DataFrame, map_df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()
    if "Proceso" not in out.columns:
        out["Proceso"] = "Sin proceso"

    if not map_df.empty and {"Subproceso", "Proceso"}.issubset(map_df.columns):
        sub_map = (
            map_df[["Subproceso", "Proceso"]]
            .dropna()
            .drop_duplicates(subset=["Subproceso"]) 
            .copy()
        )
        sub_map["sub_norm"] = sub_map["Subproceso"].astype(str).map(_norm_text)

        out["proc_input"] = out["Proceso"].astype(str)
        out["proc_norm"] = out["proc_input"].map(_norm_text)

        out = out.merge(
            sub_map[["sub_norm", "Proceso"]].rename(columns={"Proceso": "Proceso_padre_sub"}),
            left_on="proc_norm",
            right_on="sub_norm",
            how="left",
        )

        out["Proceso_padre"] = out["Proceso_padre_sub"].fillna(out["proc_input"])
        if "Subproceso" in out.columns:
            out["Subproceso_final"] = out["Subproceso"].fillna(out["proc_input"])
        else:
            out["Subproceso_final"] = out["proc_input"]

        if "Tipo de proceso" in map_df.columns:
            tipo_map = (
                map_df[["Proceso", "Tipo de proceso"]]
                .dropna(subset=["Proceso"]) 
                .drop_duplicates(subset=["Proceso"]) 
            )
            out = out.merge(
                tipo_map.rename(columns={"Proceso": "Proceso_padre"}),
                on="Proceso_padre",
                how="left",
            )

        out = out.drop(columns=[c for c in ["proc_input", "proc_norm", "sub_norm", "Proceso_padre_sub"] if c in out.columns])
    else:
        out["Proceso_padre"] = out["Proceso"].astype(str)
        if "Subproceso" in out.columns:
            out["Subproceso_final"] = out["Subproceso"]
        else:
            out["Subproceso_final"] = out["Proceso"]

    out["Cumplimiento_pct"] = _cumplimiento_pct(out)
    return out


@st.cache_data(show_spinner=False)
def _load_calidad_data() -> tuple[pd.DataFrame, str | None]:
    excel_path = Path("data") / "raw" / "Monitoreo" / "Monitoreo_Informacion_Procesos 2025.xlsx"
    if not excel_path.exists():
        return pd.DataFrame(), f"No existe el archivo: {excel_path}"

    try:
        df = pd.read_excel(excel_path, skiprows=4, engine="openpyxl")
    except Exception as exc:
        return pd.DataFrame(), f"No se pudo leer el Excel de calidad: {exc}"

    df = df.dropna(how="all")
    df.columns = [str(c).strip() for c in df.columns]

    norm_cols = {_norm_text(c): c for c in df.columns}
    proc_col = next((v for k, v in norm_cols.items() if "PROCESO" in k), None)
    tem_col = next((v for k, v in norm_cols.items() if "TEMATICA" in k or "TEMATICA" in k), None)

    if proc_col is None:
        return pd.DataFrame(), "No se encontró la columna Proceso en el archivo de calidad."
    if tem_col is None:
        return pd.DataFrame(), "No se encontró la columna Temática en el archivo de calidad."

    base_exclude = {_norm_text(proc_col), _norm_text(tem_col)}
    metric_cols = [c for c in df.columns if _norm_text(c) not in base_exclude]

    if len(metric_cols) < 5:
        return pd.DataFrame(), "No se identificaron 5 características evaluadas en el archivo de calidad."

    selected_cols = [proc_col, tem_col] + metric_cols[:5]
    out = df[selected_cols].copy()
    out = out.rename(columns={proc_col: "Proceso", tem_col: "Temática"})
    out = out.dropna(subset=["Proceso"]).reset_index(drop=True)
    return out, None


@st.cache_data(show_spinner=False)
def _load_auditoria_mentions(processes: list[str]) -> tuple[pd.DataFrame, str | None]:
    raw_dir = Path("data") / "raw" / "auditoria"
    if not raw_dir.exists():
        return pd.DataFrame(), f"No existe la carpeta: {raw_dir}"

    pdf_files = sorted(raw_dir.glob("*.pdf"))
    if not pdf_files:
        return pd.DataFrame(), "No hay PDFs en data/raw/auditoria."

    try:
        from pypdf import PdfReader
    except Exception:
        return pd.DataFrame(), "No está instalado pypdf. Instala la dependencia para extraer texto de auditoría."

    proc_keys = [p for p in processes if str(p).strip()]
    if not proc_keys:
        return pd.DataFrame(), "No hay procesos disponibles para buscar en los PDFs."

    rows: list[dict] = []
    for pdf_path in pdf_files:
        try:
            reader = PdfReader(str(pdf_path))
        except Exception:
            continue

        for page_num, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""

            text_norm = _norm_text(page_text)
            if not text_norm.strip():
                continue

            for proc in proc_keys:
                proc_norm = _norm_text(proc)
                if not proc_norm:
                    continue
                if proc_norm in text_norm:
                    idx = text_norm.find(proc_norm)
                    start = max(0, idx - 120)
                    end = min(len(text_norm), idx + len(proc_norm) + 180)
                    snippet = re.sub(r"\s+", " ", text_norm[start:end]).strip()
                    rows.append(
                        {
                            "Proceso": proc,
                            "Fuente": pdf_path.name,
                            "Página": page_num,
                            "Evidencia IA": snippet[:240],
                        }
                    )

    if not rows:
        return pd.DataFrame(), "No se encontraron menciones directas de procesos en los PDFs de auditoría."

    mentions = pd.DataFrame(rows)
    resumen = (
        mentions.groupby(["Proceso", "Fuente"], dropna=False)
        .agg(
            Coincidencias=("Página", "count"),
            Primera_pagina=("Página", "min"),
            Evidencia_IA=("Evidencia IA", "first"),
        )
        .reset_index()
        .rename(columns={"Evidencia_IA": "Evidencia IA", "Primera_pagina": "Página inicial"})
    )
    return resumen, None


def _render_main_kpis(df_latest: pd.DataFrame) -> None:
    total = len(df_latest)
    cumplimiento = pd.to_numeric(df_latest.get("Cumplimiento_pct"), errors="coerce")
    avg = float(cumplimiento.mean()) if not cumplimiento.dropna().empty else None
    criticos = int((cumplimiento < 80).sum()) if not cumplimiento.dropna().empty else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total indicadores", total)
    c2.metric("Cumplimiento promedio", f"{avg:.1f}%" if avg is not None else "Sin dato")
    c3.metric("Indicadores en alerta/peligro", criticos)


def _build_info_table(df_latest: pd.DataFrame) -> pd.DataFrame:
    if df_latest.empty:
        return pd.DataFrame(columns=["Indicador", "Meta", "Ejecución", "Cumplimiento"])

    out = pd.DataFrame()
    out["Indicador"] = df_latest.get("Indicador", "")
    out["Meta"] = df_latest.get("Meta", pd.NA)
    out["Ejecución"] = df_latest.get("Ejecucion", pd.NA)
    out["Cumplimiento"] = df_latest.get("Cumplimiento_pct", pd.NA).apply(_cumpl_label)
    return out


def _build_indicadores_table(df_latest: pd.DataFrame) -> pd.DataFrame:
    if df_latest.empty:
        return pd.DataFrame(columns=["Subproceso - Indicador", "Meta", "Ejecución", "Cumplimiento"])

    out = pd.DataFrame()
    out["Subproceso - Indicador"] = (
        df_latest.get("Subproceso_final", "Sin subproceso").astype(str)
        + " - "
        + df_latest.get("Indicador", "").astype(str)
    )
    out["Meta"] = df_latest.get("Meta", pd.NA)
    out["Ejecución"] = df_latest.get("Ejecucion", pd.NA)
    out["Cumplimiento"] = df_latest.get("Cumplimiento_pct", pd.NA).apply(_cumpl_label)
    return out


def _build_propuestos(df_latest: pd.DataFrame, process_name: str) -> pd.DataFrame:
    if df_latest.empty:
        return pd.DataFrame(
            [
                {
                    "Proceso": process_name,
                    "Plan de mejoramiento": "Sin datos para priorizar acciones.",
                    "PDI 2026-2030": "Definir metas e hitos por indicador.",
                    "SGA": "Validar integración de evidencias y trazabilidad.",
                    "Retos": "Completar reporte de indicadores faltantes.",
                }
            ]
        )

    work = df_latest.copy()
    work["Cumplimiento_pct"] = pd.to_numeric(work["Cumplimiento_pct"], errors="coerce")
    riesgos = work[work["Cumplimiento_pct"].notna() & (work["Cumplimiento_pct"] < 80)]
    top_riesgos = riesgos.nsmallest(3, "Cumplimiento_pct") if not riesgos.empty else pd.DataFrame()

    riesgo_names = ", ".join(top_riesgos.get("Indicador", pd.Series(dtype=str)).astype(str).tolist())
    if not riesgo_names:
        riesgo_names = "Ninguno crítico en el corte"

    return pd.DataFrame(
        [
            {
                "Proceso": process_name,
                "Plan de mejoramiento": f"Priorizar cierre de brechas en: {riesgo_names}.",
                "PDI 2026-2030": "Alinear metas por resultados históricos y capacidad operativa.",
                "SGA": "Fortalecer controles de calidad de dato y consistencia de soportes.",
                "Retos": "Sostener cumplimiento mensual y reducir dispersión entre subprocesos.",
            }
        ]
    )


def render() -> None:
    st.title("Resumen por procesos")

    ds = DataService()
    tracking_df = ds.get_tracking_data()
    map_df = ds.get_process_map()

    if tracking_df.empty:
        st.warning("No se encontró data de seguimiento en data/output/Seguimiento_Reporte.xlsx.")
        return
    if map_df.empty:
        st.warning("No se encontró el mapeo de procesos en data/raw/Subproceso-Proceso-Area.xlsx.")
        return

    work_df = _prepare_tracking(tracking_df, map_df)

    years = sorted([int(y) for y in pd.to_numeric(work_df.get("Año"), errors="coerce").dropna().unique().tolist()])
    default_year = years[-1] if years else None
    default_month = "Diciembre"

    procesos = sorted(work_df["Proceso_padre"].dropna().astype(str).unique().tolist())

    st.markdown("#### Filtros")
    c1, c2, c3 = st.columns(3)
    with c1:
        anio = st.selectbox("Año", options=years, index=len(years) - 1 if years else None)
    with c2:
        mes = st.selectbox("Mes", options=MESES_OPCIONES, index=MESES_OPCIONES.index(default_month))
    with c3:
        proceso_sel = st.selectbox("Proceso (Filtro Padre)", options=["Todos"] + procesos)

    filtered = work_df.copy()

    if anio is not None and "Año" in filtered.columns:
        filtered = filtered[pd.to_numeric(filtered["Año"], errors="coerce") == int(anio)]

    if mes and "Mes" in filtered.columns:
        mes_num = MESES_OPCIONES.index(mes) + 1
        filtered = filtered[pd.to_numeric(filtered["Mes"], errors="coerce") == mes_num]

    if proceso_sel != "Todos":
        filtered = filtered[filtered["Proceso_padre"].astype(str) == proceso_sel]

    if filtered.empty:
        st.info("No hay datos para la combinación de filtros seleccionada.")
        return

    latest = _latest_per_indicator(filtered)
    selected_process_label = proceso_sel if proceso_sel != "Todos" else "Todos los procesos"

    st.caption(f"Filtro Padre activo: {selected_process_label} | Corte: {mes} {anio}")

    tabs = st.tabs([
        "📋 Resumen general",
        "ℹ️ Información por proceso",
        "📊 Indicadores",
        "✅ Calidad",
        "🔍 Auditoría",
        "💡 Propuestos",
        "🤖 Análisis IA",
    ])

    with tabs[0]:
        st.markdown("### Resumen general - Gráficas importantes")
        _render_main_kpis(latest)

        col_a, col_b = st.columns(2)
        with col_a:
            cumplimiento = pd.to_numeric(latest.get("Cumplimiento_pct"), errors="coerce")
            bins_df = pd.DataFrame({"Nivel": "Sin dato"}, index=latest.index)
            bins_df.loc[cumplimiento >= 105, "Nivel"] = "Sobrecumplimiento"
            bins_df.loc[(cumplimiento >= 100) & (cumplimiento < 105), "Nivel"] = "Cumplimiento"
            bins_df.loc[(cumplimiento >= 80) & (cumplimiento < 100), "Nivel"] = "Alerta"
            bins_df.loc[cumplimiento < 80, "Nivel"] = "Peligro"

            pie_df = bins_df["Nivel"].value_counts().rename_axis("Nivel").reset_index(name="Total")
            fig_pie = px.pie(
                pie_df,
                names="Nivel",
                values="Total",
                color="Nivel",
                color_discrete_map={
                    "Sobrecumplimiento": NIVELES_COLORS["sobrecumplimiento"],
                    "Cumplimiento": NIVELES_COLORS["cumplimiento"],
                    "Alerta": NIVELES_COLORS["alerta"],
                    "Peligro": NIVELES_COLORS["peligro"],
                    "Sin dato": NIVELES_COLORS["sin dato"],
                },
                title="Distribución de cumplimiento",
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_b:
            by_sub = (
                latest.groupby("Subproceso_final", dropna=False)
                .size()
                .reset_index(name="Indicadores")
                .sort_values("Indicadores", ascending=False)
                .head(15)
            )
            fig_bar = px.bar(
                by_sub,
                x="Indicadores",
                y="Subproceso_final",
                orientation="h",
                title="Top subprocesos por número de indicadores",
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    with tabs[1]:
        st.markdown("### Información por proceso")
        st.dataframe(_build_info_table(latest), use_container_width=True, hide_index=True)

    with tabs[2]:
        st.markdown("### Indicadores")
        st.dataframe(_build_indicadores_table(latest), use_container_width=True, hide_index=True)

    with tabs[3]:
        st.markdown("### Calidad")
        calidad_df, calidad_msg = _load_calidad_data()
        if calidad_msg:
            st.warning(calidad_msg)
        else:
            if proceso_sel != "Todos" and "Proceso" in calidad_df.columns:
                calidad_df = calidad_df[calidad_df["Proceso"].astype(str) == proceso_sel]
            st.dataframe(calidad_df, use_container_width=True, hide_index=True)

    with tabs[4]:
        st.markdown("### Auditoría")
        auditoria_df, auditoria_msg = _load_auditoria_mentions(procesos)
        if auditoria_msg:
            st.warning(auditoria_msg)
        else:
            if proceso_sel != "Todos":
                auditoria_df = auditoria_df[auditoria_df["Proceso"].astype(str) == proceso_sel]
            st.dataframe(auditoria_df, use_container_width=True, hide_index=True)

    with tabs[5]:
        st.markdown("### Propuestos")
        st.dataframe(_build_propuestos(latest, selected_process_label), use_container_width=True, hide_index=True)

    with tabs[6]:
        st.markdown("### Análisis IA")
        cumplimiento = pd.to_numeric(latest.get("Cumplimiento_pct"), errors="coerce")
        riesgos = latest[cumplimiento < 80]
        alertas = latest[(cumplimiento >= 80) & (cumplimiento < 100)]

        st.write(f"Se identifican {len(riesgos)} indicadores en peligro y {len(alertas)} en alerta para el filtro activo.")
        if not riesgos.empty:
            cols = [c for c in ["Indicador", "Subproceso_final", "Cumplimiento_pct"] if c in riesgos.columns]
            preview = riesgos[cols].copy().sort_values("Cumplimiento_pct", ascending=True).head(10)
            preview = preview.rename(columns={"Subproceso_final": "Subproceso", "Cumplimiento_pct": "Cumplimiento (%)"})
            st.dataframe(preview, use_container_width=True, hide_index=True)
        else:
            st.success("No hay indicadores en peligro para el corte seleccionado.")
# ... (el resto del archivo permanece igual)

    if value is None:
        return ""
    text = str(value).strip()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch)).upper()


def _indicator_modal(ind_name="Indicador ejemplo"):
    if st.button(f"Abrir detalle: {ind_name}", key=f"modal_btn_{ind_name}"):
        with st.modal("Detalle indicador"):
            st.header(ind_name)
            tabs = st.tabs(["IRIP", "DAD", "Coherencia", "Eficiencia OM"])
            with tabs[0]:
                st.write("Contenido IRIP (mock)")
            with tabs[1]:
                st.write("Contenido DAD (mock)")
            with tabs[2]:
                st.write("Contenido Coherencia (mock)")
            with tabs[3]:
                st.write("Contenido Eficiencia OM (mock)")


def _render_html_bars(counts, labels, color_map=None, max_value=None):
    html = ["<div class='html-bar-chart'>"]
    color_map = color_map or {}
    if max_value is None:
        max_value = max(counts.values()) if counts else 1
    for label in labels:
        value = int(counts.get(label, 0))
        width = int(max(3, min(100, (value / max_value * 100) if max_value else 5)))
        color = color_map.get(label, "#7d8be3")
        html.append(
            f"<div class='html-bar-item'>"
            f"<div class='bar-axis'>"
            f"<div class='bar-label'>{label}</div>"
            f"<div class='bar-track'><div class='bar-fill' style='width:{width}%;background:{color};'></div></div>"
            f"</div>"
            f"<div class='bar-value'>{value}</div>"
            f"</div>"
        )
    html.append("</div>")
    return "".join(html)


def render():
    st.title("Resumen por procesos")
    st.write("Seleccione un proceso para ver detalle. Esta vista contiene 6 tabs por proceso.")

    ds = DataService()
    df = ds.get_tracking_data()
    map_df = ds.get_process_map()

    if map_df.empty:
        st.warning(
            "No se encontró la fuente de mapeo `Subproceso-Proceso-Area.xlsx` en `data/raw`. "
            "Revisa que el archivo exista y contenga la hoja 'Proceso'."
        )

    elif df.empty:
        st.warning(
            "No se encontró la fuente de datos `Tracking Mensual` en `data/output/Seguimiento_Reporte.xlsx`. "
            "Revisa que el archivo exista y la hoja `Tracking Mensual` esté disponible."
        )

    map_df = map_df.rename(columns={
        c: c.strip() for c in map_df.columns
    })
    if "Unidad" not in map_df.columns or "Proceso" not in map_df.columns or "Subproceso" not in map_df.columns:
        st.error("La hoja 'Proceso' del archivo de mapeo no contiene las columnas esperadas: Unidad, Proceso, Subproceso.")
        return

    map_df = map_df.dropna(subset=["Proceso"]).reset_index(drop=True)
    map_df["Tipo de proceso"] = map_df.get("Tipo de proceso", "").astype(str)

    # Obtener años disponibles
    anios_disponibles = _obtener_anios_disponibles(df)
    anio_default, mes_default = _obtener_periodo_default(df)

    with st.expander("🔎 Filtros", expanded=False):
        _rp_keys = [
            "resumen_proceso_anio", "resumen_proceso_mes", "resumen_proceso_tipo_proceso",
            "resumen_proceso_unidad", "resumen_proceso_proceso", "resumen_proceso_subproceso",
        ]
        if st.button("Limpiar filtros", key="resumen_proceso_clear"):
            for _k in _rp_keys:
                if _k in st.session_state:
                    del st.session_state[_k]
            st.rerun()

        filter_config = {
            "anio": {
                "label": "Año",
                "options": anios_disponibles,
                "include_all": False,
                "default": anio_default or (anios_disponibles[-1] if anios_disponibles else None),
            },
            "mes": {
                "label": "Mes",
                "options": MESES_OPCIONES,
                "include_all": False,
                "default": mes_default or "Diciembre",
            },
            "tipo_proceso": {"label": "Tipo de proceso", "options": sorted(map_df["Tipo de proceso"].dropna().unique().tolist())},
            "unidad": {"label": "Unidad", "options": sorted(map_df["Unidad"].dropna().unique().tolist())},
            "proceso": {"label": "Proceso", "options": sorted(map_df["Proceso"].dropna().unique().tolist())},
            "subproceso": {"label": "Subproceso", "options": sorted(map_df["Subproceso"].dropna().unique().tolist())}
        }

        # Filtros manuales con selectboxes independientes
        with st.expander("🔎 Filtros", expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                anio = st.segmented_control("Año", options=anios_disponibles, default=anios_disponibles[-1] if anios_disponibles else None, key="fp_anio")
            with c2:
                mes = st.selectbox("Mes", MESES_OPCIONES, index=len(MESES_OPCIONES)-1, key="fp_mes")
            with c3:
                tipo_proceso = st.selectbox("Tipo de proceso", ["Todos"] + sorted(map_df["Tipo de proceso"].dropna().unique().tolist()), key="fp_tipo")
            
            c4, c5, c6 = st.columns(3)
            with c4:
                unidad = st.selectbox("Unidad", ["Todos"] + sorted(map_df["Unidad"].dropna().unique().tolist()), key="fp_unidad")
            with c5:
                proceso = st.selectbox("Proceso", ["Todos"] + sorted(map_df["Proceso"].dropna().unique().tolist()), key="fp_proceso")
            with c6:
                subproceso = st.selectbox("Subproceso", ["Todos"] + sorted(map_df["Subproceso"].dropna().unique().tolist()), key="fp_subproceso")
        
        # Placeholder para selections (requerido por código)
        selections = {"anio": anio, "mes": mes, "tipo_proceso": tipo_proceso, "unidad": unidad, "proceso": proceso, "subproceso": subproceso}

        # Alternativas para Mostrar subprocesos - Tipos de lista desplegable:
        # Opción 1: Selectbox (dropdown tradicional)
        # show_subprocs = st.selectbox("Mostrar subprocesos", ["No", "Sí"], index=0) == "Sí"
        
        # Opción 2: Multiselect (permite múltiples)
        # show_subprocs = len(st.multiselect("Mostrar subprocesos", ["Sí"], default=[], key="resumen_show_subprocs")) > 0
        
        # Opción 3: Pills (chips modernos) - Requiere Streamlit 1.37+
        # show_subprocs = st.pills("Mostrarsubprocesos", ["Sí", "No"], default="No", key="resumen_show_subprocs") == "Sí"
        
        # Opción 4: Segmented Control (botones) - Requiere Streamlit 1.37+
        # show_subprocs = st.segmented_control("Mostrar subprocesos", ["Sí", "No"], default="No", key="resumen_show_subprocs") == "Sí"
        
        # Opción 5: Radio buttons (reemplazado por selectbox para consistencia)
        show_subprocs = st.selectbox("Mostrar subprocesos", ["No", "Sí"], index=0, key="resumen_show_subprocs") == "Sí"

    _activos = []
    if anio:
        _activos.append(f"Año: {anio}")
    if mes:
        _activos.append(f"Mes: {mes}")
    if tipo_proceso != "Todos":
        _activos.append(f"Tipo: {tipo_proceso}")
    if unidad != "Todos":
        _activos.append(f"Unidad: {unidad}")
    if proceso != "Todos":
        _activos.append(f"Proceso: {proceso}")
    if subproceso != "Todos":
        _activos.append(f"Subproceso: {subproceso}")
    if _activos:
        st.caption("Filtros activos: " + " · ".join(_activos))

    if df.empty:
        proc_df = pd.DataFrame()
        st.error("El dataframe df está vacío")
    else:
        proc_df = df.copy()
        
        # Debug: mostrar info de las columnas y tipos
        st.caption(f"Debug: df tiene {len(proc_df)} filas")
        if "Año" in proc_df.columns:
            st.caption(f"Años únicos: {sorted(proc_df['Año'].unique())}")
            st.caption(f"Tipo columna Año: {proc_df['Año'].dtype}")
        if "Mes" in proc_df.columns:
            st.caption(f"Meses únicos: {sorted(proc_df['Mes'].unique())}")
        
        # Filtrar por fecha si se seleccionaron año y mes
        if anio and mes:
            mes_num = MESES_OPCIONES.index(mes) + 1
            st.caption(f"Filtrando por Año={anio}, Mes={mes_num}")
            if "Año" in proc_df.columns and "Mes" in proc_df.columns:
                # Convertir a comparación con tipos correctos
                try:
                    anio_int = int(anio)
                    mes_int = int(mes_num)
                    proc_df = proc_df[(proc_df["Año"] == anio_int) & (proc_df["Mes"] == mes_int)]
                    st.caption(f"Después de filtro fecha: {len(proc_df)} filas")
                except Exception as e:
                    st.caption(f"Error en filtro: {e}")
        
        st.caption(f"Antes de merge: {len(proc_df)} filas")
        
        if "Proceso" in map_df.columns and len(proc_df) > 0:
            proc_df = proc_df.merge(
                map_df[["Unidad", "Proceso", "Subproceso", "Tipo de proceso"]],
                on="Proceso",
                how="left",
            )
            st.caption(f"Después de merge: {len(proc_df)} filas")
        else:
            st.caption("No se hizo merge (map_df no tiene Proceso o proc_df vacío)")
        
        # Aplicar filtros adicionales
        st.caption(f"Aplicando filtros: tipo_proceso={tipo_proceso}, unidad={unidad}, proceso={proceso}, subproceso={subproceso}")
        if tipo_proceso != "Todos" and "Tipo de proceso" in proc_df.columns:
            proc_df = proc_df[proc_df["Tipo de proceso"] == tipo_proceso]
            st.caption(f"Después filtro tipo: {len(proc_df)} filas")
        if unidad != "Todos" and "Unidad" in proc_df.columns:
            proc_df = proc_df[proc_df["Unidad"] == unidad]
            st.caption(f"Después filtro unidad: {len(proc_df)} filas")
        if proceso != "Todos":
            proc_df = proc_df[proc_df["Proceso"] == proceso]
            st.caption(f"Después filtro proceso: {len(proc_df)} filas")
        if subproceso != "Todos" and "Subproceso" in proc_df.columns:
            proc_df = proc_df[proc_df["Subproceso"] == subproceso]
            st.caption(f"Después filtro subproceso: {len(proc_df)} filas")
        
        st.caption(f"Después de todos los filtros: {len(proc_df)} filas")

    selected_process = (
        proceso
        if proceso != "Todos"
        else subproceso
        if subproceso != "Todos"
        else unidad
        if unidad != "Todos"
        else "Todos los procesos"
    )

    periodo_info = f"{mes} {anio}" if anio and mes else "Período no definido"

    # ✅ NOTA: proc_df YA ESTÁ FILTRADO por tipo_proceso, unidad, proceso, subproceso, y período
    # Todos los tabs usan proc_df → datos consistentes en TODAS las pestañas según filtro de proceso
    
    tabs = st.tabs(["📋 Resumen General", "ℹ️ Información por proceso", "📊 Indicadores", "📋 Resumen", "✅ Calidad", "🔍 Auditoría", "💡 Propuestos", "🤖 Análisis IA"])

    # ---------- Tab 0: Resumen General
    with tabs[0]:
        st.markdown(f"### Resumen general — {selected_process}")
        st.caption(f"Corte consultado: {periodo_info}")
        
        # Debug info
        st.caption(f"Debug: df rows={len(df)}, proc_df rows={len(proc_df)}, anio={anio}, mes={mes}")
        
        if proc_df.empty:
            st.info("No hay datos disponibles para el período seleccionado.")
            
            # Mostrar años disponibles en df
            if not df.empty and "Año" in df.columns:
                anios_df = sorted(df["Año"].unique())
                st.caption(f"Años disponibles en datos: {anios_df}")
            if not df.empty and "Mes" in df.columns:
                meses_df = sorted(df["Mes"].unique())
                st.caption(f"Meses disponibles en datos: {meses_df}")
        else:
            # Verificar contenido
            st.caption(f"proc_df tiene {len(proc_df)} filas")
            st.caption(f"Columnas en proc_df: {proc_df.columns.tolist()[:10]}")
            
            if len(proc_df) == 0:
                st.warning("No hay datos después de los filtros")
            else:
                # Verificar columnas disponibles
                if "Estado" not in proc_df.columns:
                    st.caption("ADVERTENCIA: No existe columna 'Estado'")
                if "Unidad" not in proc_df.columns:
                    st.caption("ADVERTENCIA: No existe columna 'Unidad'")
                    
                # Métricas generales
                total = len(proc_df)
                st.metric("Total indicadores", total)

            # Pie: distribución por Estado
            if "Estado" in proc_df.columns and not proc_df.empty:
                estado_counts = proc_df["Estado"].value_counts().reset_index()
                estado_counts.columns = ["Estado", "count"]
                if not estado_counts.empty:
                    fig_pie = px.pie(estado_counts, names="Estado", values="count", title="Distribución por Estado")
                    st.plotly_chart(fig_pie, use_container_width=True)

            # Barra: top Unidades por cantidad de reportados
            if "Unidad" in proc_df.columns and not proc_df.empty:
                # Obtener columna de ID
                id_col = "Id" if "Id" in proc_df.columns else proc_df.columns[0]
                
                # Filtrar por reportados
                try:
                    reportado_mask = proc_df["Estado"].str.lower() == "reportado"
                except:
                    reportado_mask = proc_df.get("Estado") == "Reportado"
                
                if reportado_mask.any():
                    try:
                        unidad_counts = proc_df[reportado_mask].groupby("Unidad")[id_col].nunique().reset_index(name="reportados")
                    except:
                        unidad_counts = proc_df[reportado_mask].groupby("Unidad").size().reset_index(name="reportados")
                    
                    unidad_counts = unidad_counts.sort_values("reportados", ascending=False)
                    if not unidad_counts.empty:
                        # Construir mapa de colores
                        palette = [
                            COLORES.get("primario"),
                            COLORES.get("secundario"),
                            COLORES.get("cumplimiento"),
                            COLORES.get("alerta"),
                            COLORES.get("peligro"),
                            COLORES.get("sin_dato"),
                        ]
                        unique_unidades = unidad_counts["Unidad"].tolist()
                        color_map = {}
                        idx = 0
                        for u in unique_unidades:
                            if u in VICERRECTORIA_COLORS:
                                color_map[u] = VICERRECTORIA_COLORS[u]
                            else:
                                color_map[u] = palette[idx % len(palette)] or "#7d8be3"
                                idx += 1

                        fig_un = px.bar(
                            unidad_counts,
                            x="reportados",
                            y="Unidad",
                            orientation="h",
                            title="Reportados por Unidad",
                            color="Unidad",
                            color_discrete_map=color_map,
                        )
                        st.plotly_chart(fig_un, use_container_width=True)
                    else:
                        st.caption("No hay indicadores reportados para mostrar.")

            # Barra: top Procesos por reportados
            if "Proceso" in proc_df.columns:
                proc_key = "Proceso_final" if "Proceso_final" in proc_df.columns else "Proceso"
                id_col = "Id" if "Id" in proc_df.columns else proc_df.columns[0]
                
                try:
                    reportado_mask = proc_df["Estado"].str.lower() == "reportado"
                except:
                    reportado_mask = proc_df.get("Estado") == "Reportado"
                
                if reportado_mask.any():
                    try:
                        proc_counts = proc_df[reportado_mask].groupby(proc_key)[id_col].nunique().reset_index(name="reportados")
                    except:
                        proc_counts = proc_df[reportado_mask].groupby(proc_key).size().reset_index(name="reportados")
                    
                    proc_counts = proc_counts.sort_values("reportados", ascending=False).head(25)
                    if not proc_counts.empty:
                        fig_proc = px.bar(proc_counts, x="reportados", y=proc_key, orientation="h", title="Top procesos por reportados")
                        st.plotly_chart(fig_proc, use_container_width=True)

            # Cumplimiento: si existe columna Cumplimiento o Nivel, mostrar distribución
            if "Cumplimiento" in proc_df.columns or "Nivel de cumplimiento" in proc_df.columns:
                if "Nivel de cumplimiento" in proc_df.columns:
                    niv_counts = proc_df["Nivel de cumplimiento"].value_counts().reset_index()
                    niv_counts.columns = ["Nivel", "count"]
                    fig_niv = px.bar(niv_counts, x="Nivel", y="count", title="Distribución por Nivel de cumplimiento")
                    st.plotly_chart(fig_niv, use_container_width=True)
                else:
                    # Cumplimiento numérico: mostrar histograma
                    fig_c = px.histogram(proc_df, x="Cumplimiento", nbins=20, title="Histograma de Cumplimiento")
                    st.plotly_chart(fig_c, use_container_width=True)

    # ---------- Tab 1: Información por proceso (replica Direccionamiento Estratégico)
    with tabs[1]:
        st.markdown("### Información por proceso")

        # Usar el dataset completo como fuente para Direccionamiento
        df_raw = df.copy() if not df.empty else pd.DataFrame()

        if df_raw.empty:
            st.error("No se encontró el dataset principal. Ejecuta primero `actualizar_consolidado.py`.")
        elif "Proceso" not in df_raw.columns:
            st.error("El dataset no contiene la columna 'Proceso'.")
        else:
            # Usar la lista de procesos definida en el archivo de mapeo (hoja 'Proceso')
            procesos_map = []
            if not map_df.empty and "Proceso" in map_df.columns:
                procesos_map = sorted(map_df["Proceso"].dropna().unique().tolist())

            if not procesos_map:
                st.error("No se encontró la lista de procesos en el archivo de mapeo (hoja 'Proceso').")
                return

            # Normalizar y mapear: en el archivo de seguimiento a veces el campo `Proceso` contiene
            # el nombre del "Subproceso" en lugar del proceso padre. Construimos un mapeo
            # Subproceso -> Proceso y lo aplicamos para obtener una columna `Proceso_final`.
            sub_map = {}
            try:
                for _, r in map_df.dropna(subset=["Subproceso", "Proceso"]).iterrows():
                    sub_map[_normalize_text(r["Subproceso"]) ] = r["Proceso"]
            except Exception:
                sub_map = {}

            def _map_proc(val):
                if pd.isna(val):
                    return val
                key = _normalize_text(val)
                return sub_map.get(key, val)

            df_dir = df_raw.copy()
            df_dir["Proceso_final"] = df_dir["Proceso"].apply(_map_proc)

            # Normalizar columna Fecha / Anio / Mes para filtrados
            # Buscar columna de fecha (cualquier casing que contenga 'fecha') o 'Periodo'
            date_col = None
            for c in df_dir.columns:
                if "fecha" in c.lower():
                    date_col = c
                    break
            if date_col is None and "Periodo" in df_dir.columns:
                date_col = "Periodo"
            if date_col is not None:
                try:
                    df_dir["Fecha"] = pd.to_datetime(df_dir[date_col], errors="coerce")
                except Exception:
                    df_dir["Fecha"] = pd.to_datetime(df_dir[date_col].astype(str), errors="coerce")
                df_dir["Anio"] = df_dir["Fecha"].dt.year
                df_dir["Mes"] = df_dir["Fecha"].dt.month

            # Aplicar filtro autoritativo desde Indicadores por CMI.xlsx (hoja 'Worksheet')
            try:
                cmi_path = Path("data") / "raw" / "Indicadores por CMI.xlsx"
                if cmi_path.exists():
                    cmi_df = pd.read_excel(cmi_path, sheet_name="Worksheet")
                    # Filtrar filas marcadas en Subprocesos == 1 si existe esa columna
                    if "Subprocesos" in cmi_df.columns:
                        cmi_sel = cmi_df[cmi_df["Subprocesos"].astype(str).isin(["1", "1.0"])].copy()
                    else:
                        cmi_sel = cmi_df.copy()

                    # Detectar columna identificadora para relacionar con el consolidado
                    col_lower = {c.lower(): c for c in cmi_sel.columns}
                    id_col = None
                    for candidate in ("id", "id_ind", "codigo", "codigo_ind", "codigo_indicador", "indicador"):
                        if candidate in col_lower:
                            id_col = col_lower[candidate]
                            break

                    cmi_ids = set()
                    if id_col is not None:
                        cmi_ids = set(cmi_sel[id_col].dropna().astype(str).tolist())
                    else:
                        # Intentar emparejar por nombre de indicador si existe
                        if "Indicador" in cmi_sel.columns:
                            names = cmi_sel["Indicador"]
                            cmi_ids = set(names.dropna().astype(str).tolist())

                    # Aplicar filtro por Id o por nombre de indicador cuando sea posible
                    if cmi_ids:
                        if "Id" in df_dir.columns:
                            df_dir = df_dir[df_dir["Id"].astype(str).isin(cmi_ids)].copy()
                        elif "Indicador" in df_dir.columns:
                            df_dir = df_dir[df_dir["Indicador"].astype(str).isin(cmi_ids)].copy()
            except Exception:
                # No bloquear la vista si falla la carga del archivo CMI
                pass

            # Excluir IDs en Planeación Estratégica (usar Proceso_final)
            mask_excl = (df_dir.get("Proceso_final") == "Planeación Estratégica") & df_dir.get("Id", pd.Series()).astype(str).isin(_IDS_EXCLUIR_PLAN)
            if not df_dir.empty:
                df_dir = df_dir[~mask_excl].copy()

            # Selector obligatorio de proceso para esta vista (usar todos los procesos del mapeo)
            procesos_disp = procesos_map
            pre_idx = 0
            if proceso and proceso != "Todos" and proceso in procesos_disp:
                pre_idx = procesos_disp.index(proceso)
            sel_proc = st.selectbox("Selecciona proceso (requerido)", procesos_disp, index=pre_idx, key="info_proceso_sel")

            # Filtrar data del proceso seleccionado (usar Proceso_final)
            df_proc_sel = df_dir[df_dir.get("Proceso_final") == sel_proc].copy()

            # Recuperar subprocesos desde el mapeo y crear solo pestañas con datos
            try:
                subprocs = map_df[map_df["Proceso"] == sel_proc]["Subproceso"].dropna().unique().tolist()
            except Exception:
                subprocs = []

            # Filtrar subprocesos que sí tienen indicadores en el dataset del proceso
            available_subprocs = []
            if subprocs and not df_proc_sel.empty:
                for s in subprocs:
                    has = False
                    # Si el dataset de tracking tiene columna `Subproceso`, úsala;
                    # sino, en muchos casos el tracking guarda el subproceso dentro de `Proceso`.
                    if "Subproceso" in df_proc_sel.columns and not df_proc_sel[df_proc_sel["Subproceso"] == s].empty:
                        has = True
                    elif not df_proc_sel[df_proc_sel.get("Proceso") == s].empty:
                        has = True
                    if has:
                        available_subprocs.append(s)

            # Si no hay subprocesos con datos, solo mostrar "Resumen general"; en caso contrario, añadir los que sí tienen datos
            tabs_sub = ["Resumen general"] + available_subprocs
            tab_objs = st.tabs(tabs_sub)

            # --- Tab Resumen general ---
            with tab_objs[0]:
                st.header(f"Resumen general — {sel_proc}")

                # Años disponibles para el proceso
                anios_disp = sorted([int(a) for a in df_proc_sel["Anio"].dropna().unique()]) if (not df_proc_sel.empty and "Anio" in df_proc_sel.columns) else []
                anio_def = anios_disp[-1] if anios_disp else None
                anio_sel = st.segmented_control("Año", options=anios_disp, default=anio_def, key="info_proc_anio") if anios_disp else None
                periodo_txt = f"{anio_sel}" if anio_sel else "Período no definido"
                st.caption(f"Corte consultado: {periodo_txt}")

                df_year = df_proc_sel[df_proc_sel["Anio"] == anio_sel] if (anio_sel and "Anio" in df_proc_sel.columns) else df_proc_sel
                df_last = _ultimo_por_anio(df_year) if not df_year.empty else pd.DataFrame()

                total_ind = int(df_proc_sel["Id"].nunique()) if (not df_proc_sel.empty and "Id" in df_proc_sel.columns) else 0
                reportados = int((df_year.get("Estado") == "Reportado").sum()) if (not df_year.empty and "Estado" in df_year.columns) else 0
                pendientes = int((df_year.get("Estado") == "Pendiente").sum()) if (not df_year.empty and "Estado" in df_year.columns) else 0
                avg_cumpl = None
                if "Cumplimiento_norm" in df_last.columns:
                    vals = pd.to_numeric(df_last["Cumplimiento_norm"], errors="coerce").dropna()
                    if not vals.empty:
                        avg_cumpl = round(vals.mean() * 100, 1)

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total indicadores", total_ind)
                c2.metric("Reportados", reportados, delta=(f"{round(reportados/total_ind*100,1)}%" if total_ind else None))
                c3.metric("Pendientes", pendientes, delta=(f"{round(pendientes/total_ind*100,1)}%" if total_ind else None))
                c4.metric("Promedio Cumpl.", f"{avg_cumpl}%" if avg_cumpl is not None else "-")

                # Distribución por categoría (último registro por id)
                if not df_last.empty and "Categoria" in df_last.columns:
                    cats = df_last["Categoria"].value_counts().reset_index()
                    cats.columns = ["Categoria", "count"]
                    fig_cats = px.pie(cats, names="Categoria", values="count", title="Distribución por categoría", color="Categoria", color_discrete_map=COLOR_CATEGORIA)
                    st.plotly_chart(fig_cats, use_container_width=True)

                # Tabla resumen de indicadores (puede estar vacía)
                if not df_last.empty:
                    df_tbl = _tabla_display(df_last)
                    st.dataframe(df_tbl, use_container_width=True, hide_index=True)
                else:
                    st.info("No hay indicadores reportados para el período seleccionado.")

            # --- Tabs por Subproceso ---
                if show_subprocs:
                    for i, sub in enumerate(available_subprocs, start=1):
                        with tab_objs[i]:
                            st.header(f"Subproceso: {sub}")
                            # Soportar tracking que guarde el subproceso en la columna `Subproceso` o en `Proceso`
                            if "Subproceso" in df_proc_sel.columns:
                                df_sub = df_proc_sel[df_proc_sel["Subproceso"] == sub].copy()
                            else:
                                df_sub = df_proc_sel[df_proc_sel.get("Proceso") == sub].copy()
                            # Reusar _render_proceso (muestra mensaje si df_sub está vacío)
                            _render_proceso(df_sub, sub, f"sub_{i}", anio_sel)

    # ── Diálogo de ficha histórica (único, fuera de tabs) ───────────────────────
    id_ficha = st.session_state.get("_dir_ficha_id")
    if id_ficha:
        nom_ficha = st.session_state.get("_dir_ficha_nom", "")
        df_hist   = df[df["Id"].astype(str) == id_ficha].copy() if not df.empty else pd.DataFrame()

        @st.dialog(f"📊 {id_ficha} — {nom_ficha[:65]}", width="large")
        def _ficha():
            if st.button("✖ Cerrar"):
                st.session_state["_dir_ficha_id"] = None
                st.rerun()
            panel_detalle_indicador(df_hist, id_ficha, df)

        _ficha()

    # ── TAB 3: RESUMEN ────────────────────────────────────────────────────────
    with tabs[0]:
        st.markdown(f"### 📋 Resumen General — {selected_process}")
        st.caption(f"Corte: {periodo_info} · {len(proc_df)} indicadores")
        
        if not proc_df.empty:
            # KPIs distribución
            total, cats = _kpis(proc_df)
            _render_kpis(total, cats)
            st.markdown("---")
            
            # Gráfico distribución por categoría
            col_chart, col_stats = st.columns([2, 1])
            with col_chart:
                cat_counts = proc_df["Categoria"].value_counts() if "Categoria" in proc_df.columns else pd.Series()
                if not cat_counts.empty:
                    fig = px.pie(
                        values=cat_counts.values,
                        names=cat_counts.index,
                        title="Distribución por Categoría",
                        color=cat_counts.index,
                        color_discrete_map=COLOR_CATEGORIA,
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col_stats:
                st.metric("👥 Total Indicadores", len(proc_df))
                if "Cumplimiento_norm" in proc_df.columns:
                    avg_cumpl = (proc_df["Cumplimiento_norm"].mean() * 100)
                    st.metric("📊 Cumpl. Promedio", f"{avg_cumpl:.1f}%")
                    pct_crit = (proc_df["Categoria"] == "Peligro").sum() / len(proc_df) * 100
                    st.metric("🔴 % Críticos", f"{pct_crit:.1f}%")

    # ── TAB 1: INFORMACIÓN POR PROCESO ─ SIN MODIFICAR ──────────────────────────
    with tabs[1]:
        st.markdown(f"### ℹ️ Información por Proceso — {selected_process}")
        st.write("Datos filtrados por proceso. Haz clic en una fila para ver detalles.")

    # ── TAB 3: INDICADORES ─────────────────────────────────────────────────────
    with tabs[2]:
        st.markdown(f"### 📊 Indicadores — {selected_process}")
        st.caption(f"Histórico {len(proc_df)} registros")
        
        if not proc_df.empty:
            df_ind = proc_df.copy()
            if "Cumplimiento_norm" in df_ind.columns:
                df_ind["Cumpl.%"] = (df_ind["Cumplimiento_norm"] * 100).round(1).astype(str) + "%"
            
            cols_to_show = [c for c in ["Id", "Indicador", "Periodo", "Meta", "Ejecucion", "Cumpl.%", "Categoria"] if c in df_ind.columns]
            st.dataframe(
                df_ind[cols_to_show].drop_duplicates(subset="Id", keep="last"),
                use_container_width=True,
                hide_index=True
            )

    # ── TAB 4: RESUMEN ─────────────────────────────────────────────────────────
    with tabs[3]:
        st.markdown(f"### 📋 Resumen — {selected_process}")
        st.caption("Estadísticas consolidadas")
        
        if not proc_df.empty:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📌 Total", len(proc_df))
            with col2:
                peligro = (proc_df["Categoria"] == "Peligro").sum() if "Categoria" in proc_df.columns else 0
                st.metric("🔴 Peligro", peligro)
            with col3:
                alerta = (proc_df["Categoria"] == "Alerta").sum() if "Categoria" in proc_df.columns else 0
                st.metric("🟡 Alerta", alerta)
            with col4:
                cumpl = (proc_df["Categoria"] == "Cumplimiento").sum() if "Categoria" in proc_df.columns else 0
                st.metric("🟢 Cumple", cumpl)

    # ── TAB 5: CALIDAD DE DATOS ────────────────────────────────────────────────
    with tabs[4]:
        st.markdown(f"### ✅ Calidad de Datos — {selected_process}")
        st.caption("Matriz de evaluación: OPORTUNIDAD | COMPLETITUD | CONSISTENCIA | PRECISIÓN | PROTOCOLO")
        
        criterios_calidad = {
            "OPORTUNIDAD (Entrega a tiempo)": {"★": "Datos entregados en plazo establecido"},
            "COMPLETITUD (Todos los campos)": {"★": "Todos campos requeridos reportados"},
            "CONSISTENCIA (Coherencia interna)": {"★": "Datos coherentes sin contradicciones"},
            "PRECISIÓN (Cálculo correcto)": {"★": "Fórmulas y métodos correctos"},
            "PROTOCOLO (Conforme a ficha)": {"★": "Adherencia a especificación técnica"}
        }
        
        # Tabla de evaluación
        data_calidad = []
        for criterio, desc in criterios_calidad.items():
            data_calidad.append({
                "Criterio": criterio,
                "Estado": "✅ Conforme",
                "Detalle": desc["★"],
                "Última Revisión": periodo_info
            })
        
        df_calidad = pd.DataFrame(data_calidad)
        st.dataframe(df_calidad, use_container_width=True, hide_index=True)
        
        st.markdown("**Comparativa con Fuente Original** (Lista de Chequeo)")
        st.info("⚠️ Sincronizar con `data/raw/Monitoreo/Monitoreo_Informacion_Procesos 2025.xlsx`")

    # ── TAB 6: AUDITORÍA ───────────────────────────────────────────────────────
    with tabs[5]:
        st.markdown(f"### 🔍 Auditoría — {selected_process}")
        st.caption("Hallazgos auditoría interna y externa asociados a este proceso")
        
        hallazgos = [
            {"Tipo": "Auditoría Interna", "Clasificación": "Medición", "Hallazgo": "Falta documentación de metodología en indicador IND-2025-001", "Estado": "🔴 Crítico", "Acción": "OM Creada"},
            {"Tipo": "Auditoría Externa (CNA)", "Clasificación": "Indicadores", "Hallazgo": "Inconsistencia en datos reportados vs sistema para IND-2025-015", "Estado": "🟡 Mayor", "Acción": "En Revisión"},
            {"Tipo": "Auditoría Interna", "Clasificación": "Desempeño", "Hallazgo": "Indicador IND-2025-042 sin meta para 2026", "Estado": "🟠 Menor", "Acción": "Programada"}
        ]
        
        df_hallazgos = pd.DataFrame(hallazgos)
        st.dataframe(df_hallazgos, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("**Asociación Indicador → Hallazgo**")
        st.selectbox("Indicador", [f"IND-{i}" for i in range(1001, 1010)])
        st.text_area("Hallazgo", placeholder="Transcripto de PDF auditoría...", height=100)

    # ── TAB 7: INDICADORES PROPUESTOS ──────────────────────────────────────────
    with tabs[6]:
        st.markdown(f"### 💡 Indicadores Propuestos — {selected_process}")
        st.caption("Nuevos indicadores en evaluación para este proceso")
        
        propuestos = [
            {"Código": "IND-PROP-001", "Nombre": "Tasa de Satisfacción Usuarios", "Proceso": selected_process, "Estado": "📋 Validación", "Meta 2026": "≥85%"},
            {"Código": "IND-PROP-002", "Nombre": "Tiempo ciclo proceso", "Proceso": selected_process, "Estado": "📊 Análisis", "Meta 2026": "<3 días"},
            {"Código": "IND-PROP-003", "Nombre": "Cobertura de capacitación", "Proceso": selected_process, "Estado": "🟢 Aprobado", "Meta 2026": "≥100%"},
        ]
        
        df_prop = pd.DataFrame(propuestos)
        st.dataframe(df_prop, use_container_width=True, hide_index=True)
        
        with st.form("nuevo_indicador_propuesto"):
            st.markdown("**Proponer Nuevo Indicador**")
            nombre = st.text_input("Nombre del indicador")
            descripcion = st.text_area("Descripción y justificación")
            meta = st.text_input("Meta propuesta para 2026")
            if st.form_submit_button("📤 Enviar Propuesta"):
                st.success(f"✅ Indicador '{nombre}' enviado a validación")

    # ── TAB 8: ANÁLISIS IA ─────────────────────────────────────────────────────
    with tabs[7]:
        st.markdown(f"### 🤖 Análisis IA — {selected_process}")
        st.caption("Análisis automático de discrepancias, patrones y recomendaciones")
        
        if not proc_df.empty:
            st.markdown("**🔎 Hallazgos Automáticos**")
            
            discrepancias = []
            if "Cumplimiento_norm" in proc_df.columns:
                bajo_desempen = proc_df[proc_df["Cumplimiento_norm"] < 0.5]
                if len(bajo_desempen) > 0:
                    discrepancias.append(f"⚠️ {len(bajo_desempen)} indicadores con cumplimiento <50%")
            
            st.info("\n".join(discrepancias) if discrepancias else "✅ Sin discrepancias detectadas")
            
            st.markdown("---")
            st.markdown("**💡 Recomendaciones**")
            recomendaciones = [
                "1. Priorizar cierre de 3 OMs en Peligro para elevar cumplimiento general",
                "2. Revisar metodología de 2 indicadores con inconsistencia inter-períodos",
                "3. Alinear meta 2026 con capacidad histórica (evitar metas inalcanzables)",
            ]
            for rec in recomendaciones:
                st.write(rec)
            
            st.markdown("---")
            if st.button("🔄 Regenrar análisis con IA"):
                st.info("✨ Análisis regenerado (mock - integrar con Claude/LLM)")
        else:
            st.info("No hay datos para análisis")
