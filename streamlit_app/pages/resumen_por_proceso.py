from pathlib import Path
import importlib
import re
import unicodedata

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from components.charts import grafico_historico_indicador, tabla_historica_indicador
from streamlit_app.services.data_service import DataService
from streamlit_app.utils.formatting import formatear_meta_ejecucion_df


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

MES_MAP = {m.upper(): i + 1 for i, m in enumerate(MESES_OPCIONES)}

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


def _mes_to_num(value: object) -> float | None:
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        try:
            v = int(value)
            return float(v) if 1 <= v <= 12 else None
        except Exception:
            return None

    txt = str(value).strip()
    if not txt:
        return None

    if txt.isdigit():
        v = int(txt)
        return float(v) if 1 <= v <= 12 else None

    txt_norm = _norm_text(txt)
    return float(MES_MAP.get(txt_norm)) if txt_norm in MES_MAP else None


def _cumplimiento_pct(df: pd.DataFrame) -> pd.Series:
    if "Cumplimiento_norm" in df.columns:
        vals = pd.to_numeric(df["Cumplimiento_norm"], errors="coerce")
        return vals * 100

    if "Cumplimiento" in df.columns:
        vals = pd.to_numeric(df["Cumplimiento"].apply(_to_float), errors="coerce")
        max_abs = vals.abs().max(skipna=True) if not vals.dropna().empty else 0
        return vals * 100 if max_abs <= 2 else vals

    if {"Meta", "Ejecucion"}.issubset(df.columns):
        meta = pd.to_numeric(df["Meta"].apply(_to_float), errors="coerce")
        ejec = pd.to_numeric(df["Ejecucion"].apply(_to_float), errors="coerce")
        ratio = (ejec / meta.replace({0: pd.NA})) * 100
        return pd.to_numeric(ratio, errors="coerce")

    return pd.Series(index=df.index, dtype="float64")


def _first_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols_norm = {_norm_text(c): c for c in df.columns}
    for cand in candidates:
        key = _norm_text(cand)
        if key in cols_norm:
            return cols_norm[key]
    for cand in candidates:
        key = _norm_text(cand)
        for norm_col, real_col in cols_norm.items():
            if key in norm_col:
                return real_col
    return None


def _period_col_for_month(df: pd.DataFrame, month_num: int | None) -> str | None:
    if month_num is None:
        return None
    col = _first_col(df, [f"Periodo {int(month_num)}", f"Periodo{int(month_num)}"])
    if col is not None:
        return col

    period_cols = [c for c in df.columns if _norm_text(c).startswith("PERIODO")]
    for c in period_cols:
        digits = "".join(ch for ch in str(c) if ch.isdigit())
        if digits and int(digits) == int(month_num):
            return c
    return None


def _categoria_por_pct(pct: float | None) -> str:
    if pct is None or pd.isna(pct):
        return "Sin dato"
    if pct >= 105:
        return "Sobrecumplimiento"
    if pct >= 100:
        return "Cumplimiento"
    if pct >= 80:
        return "Alerta"
    return "Peligro"


def _available_months_with_data(df: pd.DataFrame) -> list[int]:
    if df.empty:
        return []
    months = sorted(
        set(
            int(m)
            for m in pd.to_numeric(df.get("Mes"), errors="coerce").dropna().unique()
            if 1 <= int(m) <= 12
        )
    )
    valid = []
    for month in months:
        period_col = _period_col_for_month(df, month)
        if period_col and df[period_col].notna().any():
            valid.append(month)
    return valid


def _default_month_num(df: pd.DataFrame) -> int:
    valid_months = _available_months_with_data(df)
    if valid_months:
        return valid_months[-1]
    return MESES_OPCIONES.index("Diciembre") + 1


def _ensure_historic_tracking(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Cumplimiento_pct"] = _cumplimiento_pct(out)
    out["Cumplimiento_norm"] = pd.to_numeric(out["Cumplimiento_pct"], errors="coerce") / 100
    out["Categoria"] = out["Cumplimiento_pct"].apply(_categoria_por_pct)
    if "Anio" in out.columns and "Mes" in out.columns:
        # Convertir mes string a número (Enero->01, Febrero->02, etc.)
        out["Mes_num"] = out["Mes"].apply(lambda x: _mes_to_num(x) if pd.notna(x) else None)
        out["Fecha"] = pd.to_datetime(
            out["Anio"].astype(str).str.replace("<NA>", "NaN", regex=False)
            + "-"
            + out["Mes_num"].astype(str).str.replace("None", "NaN", regex=False).str.zfill(2)
            + "-01",
            errors="coerce",
        )
    elif "Periodo" in out.columns:
        out["Fecha"] = pd.to_datetime(out["Periodo"].astype(str), errors="coerce")
    else:
        out["Fecha"] = pd.NaT
    return out


def _build_indicator_history(df: pd.DataFrame, indicador: str) -> pd.DataFrame:
    if df.empty or indicador is None:
        return df.copy()
    history = df[df["Indicador"].astype(str) == str(indicador)].copy()
    if history.empty:
        return history
    history = _ensure_historic_tracking(history)
    return history.sort_values("Fecha").reset_index(drop=True)


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

    sort_cols = [c for c in ["Anio", "Año", "Mes", "Fecha", "Periodo"] if c in df.columns]
    out = df.sort_values(sort_cols) if sort_cols else df.copy()

    if "Id" in out.columns:
        out = out.drop_duplicates(subset=["Id"], keep="last")
    elif "Indicador" in out.columns:
        out = out.drop_duplicates(subset=["Indicador"], keep="last")

    return out.reset_index(drop=True)


def _prepare_tracking(df: pd.DataFrame, map_df: pd.DataFrame, month_num: int | None = None) -> pd.DataFrame:
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

    meta_col = _first_col(out, ["Meta", "Meta último periodo", "Meta ultimo periodo"])
    if meta_col is not None:
        out["Meta"] = out[meta_col].apply(_to_float)
    else:
        out["Meta"] = pd.NA

    ejec_col = _first_col(out, ["Ejecución", "Ejecucion"])
    period_col = _period_col_for_month(out, month_num) if month_num is not None else None

    if period_col is not None:
        out["Ejecucion"] = out[period_col].apply(_to_float)
    elif month_num is None and "Mes" in out.columns:
        def _row_ejec(row):
            month = _mes_to_num(row.get("Mes"))
            if month is None:
                return None
            col_name = _period_col_for_month(out, int(month))
            return _to_float(row.get(col_name)) if col_name is not None and col_name in row else None

        out["Ejecucion"] = out.apply(_row_ejec, axis=1)
        if ejec_col is not None:
            # Fallback para fuentes que no traen columnas Periodo N pero sí Ejecución directa.
            out["Ejecucion"] = out["Ejecucion"].fillna(out[ejec_col].apply(_to_float))
    elif ejec_col is not None:
        out["Ejecucion"] = out[ejec_col].apply(_to_float)
    else:
        out["Ejecucion"] = pd.Series(index=out.index, dtype="float64")

    out["Cumplimiento_pct"] = _cumplimiento_pct(out)
    return out


@st.cache_data(show_spinner=False)
def _load_calidad_data() -> tuple[pd.DataFrame, str | None]:
    excel_path = Path("data") / "raw" / "Monitoreo" / "Monitoreo_Informacion_Procesos 2025.xlsx"
    if not excel_path.exists():
        return pd.DataFrame(), f"No existe el archivo: {excel_path}"

    def _try_parse(header_idx: int) -> tuple[pd.DataFrame, str | None, str | None]:
        try:
            local_df = pd.read_excel(excel_path, header=header_idx, engine="openpyxl")
        except Exception:
            return pd.DataFrame(), None, None

        local_df = local_df.dropna(how="all")
        local_df.columns = [str(c).strip() for c in local_df.columns]
        norm_cols = {_norm_text(c): c for c in local_df.columns}
        local_proc_col = next((v for k, v in norm_cols.items() if "PROCESO" in k), None)
        local_tem_col = next((v for k, v in norm_cols.items() if "TEMATICA" in k or "TEMATICA" in k.replace("Á", "A")), None)
        return local_df, local_proc_col, local_tem_col

    # Prioridad esperada: header=4; fallback a otros encabezados frecuentes.
    df, proc_col, tem_col = _try_parse(4)
    if proc_col is None or tem_col is None:
        for h in [3, 2, 1, 0, 5, 6]:
            df_tmp, proc_tmp, tem_tmp = _try_parse(h)
            if proc_tmp is not None and tem_tmp is not None:
                df, proc_col, tem_col = df_tmp, proc_tmp, tem_tmp
                break

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

    PdfReader = None
    for package in ("pypdf", "PyPDF2"):
        try:
            module = importlib.import_module(package)
            PdfReader = getattr(module, "PdfReader", None)
            if PdfReader is not None:
                break
        except Exception:
            continue

    if PdfReader is None:
        return pd.DataFrame(), "No está instalado pypdf ni PyPDF2. Instala uno de esos paquetes para extraer texto de auditoría."

    if not processes:
        return pd.DataFrame(), "No hay procesos disponibles para buscar en los PDFs."

    indicator_keys = [
        "INDICADOR",
        "INDICADORES",
        "CUMPLIMIENTO",
        "DESEMPENO",
        "DESEMPEÑO",
        "MEDICION",
        "MEDICIÓN",
        "METRICA",
        "MÉTRICA",
        "KPI",
        "OBJETIVO",
        "OBJETIVOS",
        "LINEA BASE",
        "LÍNEA BASE",
        "VARIACION",
        "VARIACIÓN",
        "TENDENCIA",
        "BRECHA",
        "META",
        "EJECUCION",
        "EJECUCIÓN",
        "RESULTADO",
        "AVANCE",
        "HALLAZGO",
        "RIESGO",
        "CONTROL",
        "VERIFICACION",
        "VERIFICACIÓN",
        "EVIDENCIA",
        "SEGUIMIENTO",
        "PLAN DE MEJORAMIENTO",
    ]
    indicator_keys_norm = {_norm_text(k) for k in indicator_keys}

    def _split_sentences(text: str) -> list[str]:
        text = re.sub(r"\s+", " ", str(text or "")).strip()
        if not text:
            return []
        parts = re.split(r"(?<=[\.!\?;])\s+", text)
        return [p.strip() for p in parts if p and len(p.strip()) > 20]

    def _contains_indicator_context(text_norm: str) -> bool:
        return any(k in text_norm for k in indicator_keys_norm)

    def _extract_detected_terms(text_norm: str) -> list[str]:
        found = [k for k in indicator_keys_norm if k in text_norm]
        return sorted(found)

    def _redact_summary(proc: str, fragments: list[str]) -> str:
        if not fragments:
            return f"No se identificó evidencia explícita de indicadores para {proc} en los documentos revisados."

        clean = []
        seen = set()
        for frag in fragments:
            f = re.sub(r"\s+", " ", str(frag or "")).strip()
            if not f:
                continue
            key = _norm_text(f)
            if key in seen:
                continue
            seen.add(key)
            clean.append(f)

        if not clean:
            return f"No se identificó evidencia explícita de indicadores para {proc} en los documentos revisados."

        top = clean[:3]
        if len(top) == 1:
            return f"Para el proceso {proc}, la auditoría reporta que {top[0]}"
        if len(top) == 2:
            return f"Para el proceso {proc}, la auditoría evidencia que {top[0]} Además, {top[1]}"
        return f"Para el proceso {proc}, la auditoría evidencia que {top[0]} Además, {top[1]} Finalmente, {top[2]}"

    proc_names = [str(p) for p in processes if str(p).strip()]
    proc_norm_map = {_norm_text(p): p for p in proc_names}
    collected: dict[tuple[str, str], dict] = {}

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

            text = re.sub(r"\s+", " ", str(text or "")).strip()
            text_norm = _norm_text(text)
            if not text_norm or len(text_norm) < 30:
                continue

            sentences = _split_sentences(text)
            if not sentences:
                continue

            for proc_norm, proc_name in proc_norm_map.items():
                if proc_norm not in text_norm:
                    continue

                matched_fragments = []
                for idx, sent in enumerate(sentences):
                    sent_norm = _norm_text(sent)
                    if proc_norm in sent_norm:
                        window = sentences[max(0, idx - 1): min(len(sentences), idx + 2)]
                        for frag in window:
                            frag_norm = _norm_text(frag)
                            if _contains_indicator_context(frag_norm) or proc_norm in frag_norm:
                                matched_fragments.append(frag)

                if not matched_fragments:
                    # fallback breve si aparece el proceso pero no contexto explícito de indicador
                    fallback = [s for s in sentences if proc_norm in _norm_text(s)][:2]
                    matched_fragments = fallback

                if not matched_fragments:
                    continue

                key = (proc_name, pdf_path.name)
                if key not in collected:
                    collected[key] = {
                        "Proceso": proc_name,
                        "Fuente": pdf_path.name,
                        "Paginas": set(),
                        "Fragmentos": [],
                        "Terminos": set(),
                    }

                collected[key]["Paginas"].add(page_num)
                collected[key]["Fragmentos"].extend(matched_fragments)
                for frag in matched_fragments:
                    collected[key]["Terminos"].update(_extract_detected_terms(_norm_text(frag)))

    if not collected:
        return pd.DataFrame(), "No se encontraron menciones directas de procesos en los PDFs de auditoría."

    rows = []
    for (proc_name, source_name), payload in collected.items():
        paginas = sorted(list(payload["Paginas"]))
        fragments = payload["Fragmentos"]
        summary = _redact_summary(proc_name, fragments)
        rows.append(
            {
                "Proceso": proc_name,
                "Fuente": source_name,
                "Coincidencias": len(fragments),
                "Paginas": ", ".join(str(p) for p in paginas),
                "Resumen IA": summary,
            }
        )

    resumen = pd.DataFrame(rows).sort_values(["Proceso", "Fuente"]).reset_index(drop=True)
    return resumen, None


# ---------------------------------------------------------------------------
# Auditoría estructurada desde Excel (auditoria_resultado.xlsx)
# ---------------------------------------------------------------------------

_AUDITORIA_XLSX = Path(__file__).resolve().parents[2] / "data" / "raw" / "Auditoria" / "auditoria_resultado.xlsx"

_AUD_LABELS = {
    "fortalezas":              ("Fortalezas",              "#0d6e55", "✦"),
    "oportunidades_mejora":    ("Oportunidades de Mejora", "#7a5c00", "◈"),
    "hallazgos":               ("Hallazgos",               "#1b4f8a", "◉"),
    "no_conformidades":        ("No Conformidades",        "#8b1a1a", "▲"),
    "recomendacion_desempeno": ("Recomendación de Desempeño", "#3d2b8e", "◆"),
}


@st.cache_data(show_spinner=False)
def _load_auditoria_excel() -> tuple:
    if not _AUDITORIA_XLSX.exists():
        return pd.DataFrame(), f"No existe el archivo: {_AUDITORIA_XLSX.name}. Ejecuta scripts/generar_auditoria_csv.py primero."
    try:
        df = pd.read_excel(_AUDITORIA_XLSX, sheet_name="Auditoria", engine="openpyxl")
        df = df.fillna("")
        return df, None
    except Exception as e:
        return pd.DataFrame(), f"Error leyendo Excel de auditoría: {e}"


def _render_categoria_card(proceso: str, label: str, items: list, pill_bg: str, pill_text: str, dot_color: str, icono: str, hdr_color: str) -> str:
    """Una tarjeta por categoría: header con color de categoría, nombre de proceso, lista de items."""
    count_badge = f'<span style="background:rgba(255,255,255,0.3);color:#fff;font-size:0.6rem;font-weight:700;padding:1px 7px;border-radius:10px;margin-left:8px;">{len(items)}</span>'
    items_html = "".join(
        f'<div style="display:flex;gap:10px;align-items:flex-start;padding:7px 0;border-bottom:1px solid #f3f4f7;">'
        f'<span style="width:7px;height:7px;min-width:7px;background:{dot_color};border-radius:50%;margin-top:5px;flex-shrink:0;"></span>'
        f'<span style="font-size:0.81rem;color:#2c2c3e;line-height:1.55;word-break:break-word;">{item}</span>'
        f'</div>'
        for item in items
    )
    return (
        f'<div style="background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e4e8f0;'
        f'box-shadow:0 3px 14px rgba(0,0,0,0.08);margin-bottom:18px;">'
        f'<div style="background:{hdr_color};padding:10px 16px;display:flex;align-items:center;justify-content:space-between;">'
        f'<div style="display:flex;align-items:center;gap:7px;">'
        f'<span style="font-size:1rem;line-height:1;">{icono}</span>'
        f'<span style="font-size:0.71rem;font-weight:700;letter-spacing:0.07em;text-transform:uppercase;color:#ffffff;">{label}</span>'
        f'</div>{count_badge}</div>'
        f'<div style="padding:8px 16px 6px 16px;background:{pill_bg};border-bottom:1px solid #eaedf3;">'
        f'<span style="font-size:0.75rem;font-weight:600;color:{pill_text};text-transform:uppercase;letter-spacing:0.04em;">{proceso}</span>'
        f'</div>'
        f'<div style="padding:4px 16px 10px 16px;">{items_html}</div>'
        f'</div>'
    )


def _render_auditoria_tab(proceso_filtro: str) -> None:
    """Renderiza la pestaña Auditoría como fichas ejecutivas por proceso."""
    st.markdown(
        '<p style="font-size:0.82rem;color:#888;margin-bottom:16px;">'
        'Resultados estructurados a partir de informes de auditoría. '
        'Solo se muestran campos con contenido registrado.</p>',
        unsafe_allow_html=True,
    )

    df, msg = _load_auditoria_excel()
    if msg:
        st.warning(msg)
        return
    if df.empty:
        st.info("No hay datos de auditoría disponibles.")
        return

    if proceso_filtro and proceso_filtro.upper() != "TODOS":
        mask = df["proceso"].str.upper().str.contains(proceso_filtro.upper(), na=False)
        df_filtrado = df[mask]
    else:
        df_filtrado = df

    if df_filtrado.empty:
        st.info(f"No hay hallazgos de auditoría para el proceso: {proceso_filtro}")
        return

    # campo → (label, pill_bg, pill_text, dot_color, emoji, hdr_color)
    _CAT_STYLE = {
        "fortalezas":              ("Fortalezas",              "#d1f5e0", "#0a5c36", "#1aaa6b", "✅", "#1aaa6b"),
        "oportunidades_mejora":    ("Oportunidades de Mejora", "#fff3cd", "#7a5000", "#e6a800", "🔄", "#e6a800"),
        "hallazgos":               ("Hallazgos",               "#dbeeff", "#003d8f", "#1a6fdb", "🔍", "#1a6fdb"),
        "no_conformidades":        ("No Conformidades",        "#fde0e0", "#7a0000", "#e63535", "⚠️", "#e63535"),
        "recomendacion_desempeno": ("Recomendación Desempeño", "#ede0ff", "#3d0080", "#7c3aed", "💡", "#7c3aed"),
    }

    def _seccion(tipo: str, titulo: str, color_titulo: str) -> None:
        cols_check = [f"{c}_{tipo}" for c in _CAT_STYLE]
        cols_present = [c for c in cols_check if c in df_filtrado.columns]
        if not cols_present:
            return
        df_tipo = df_filtrado[df_filtrado[cols_present].apply(lambda r: r.str.strip().ne("").any(), axis=1)]

        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;margin:20px 0 10px 0;">'
            f'<div style="width:4px;height:28px;border-radius:2px;background:{color_titulo};flex-shrink:0;"></div>'
            f'<span style="font-size:0.95rem;font-weight:700;color:#1a1a2e;">{titulo}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if df_tipo.empty:
            st.info(f"No hay hallazgos de {titulo.lower()} para el proceso seleccionado.")
            return

        for _, row in df_tipo.iterrows():
            proceso = str(row.get("proceso", "")).strip()

            # Recolectar categorías con contenido
            cats_con_datos = []
            for campo, estilo in _CAT_STYLE.items():
                col_name = f"{campo}_{tipo.lower()}"
                valor = str(row.get(col_name, "")).strip()
                if not valor:
                    continue
                items = [v.strip() for v in valor.replace("\n", " | ").split(" | ") if v.strip()]
                if items:
                    cats_con_datos.append((estilo, items))

            if not cats_con_datos:
                continue

            # Mostrar nombre del proceso
            st.markdown(
                f'<div style="font-size:0.8rem;font-weight:700;color:#1a1a2e;text-transform:uppercase;'
                f'letter-spacing:0.04em;padding:8px 0 4px 2px;border-bottom:2px solid {color_titulo};'
                f'margin-bottom:12px;">{proceso}</div>',
                unsafe_allow_html=True,
            )

            # Columnas dinámicas: 1 si hay 1, 2 si hay 2-4, 3 si hay 5+
            n = len(cats_con_datos)
            n_cols = 1 if n == 1 else (2 if n <= 4 else 3)
            columnas = st.columns(n_cols)

            for idx, (estilo, items) in enumerate(cats_con_datos):
                label, pill_bg, pill_text, dot_color, emoji, hdr_color = estilo
                html = _render_categoria_card(proceso, label, items, pill_bg, pill_text, dot_color, emoji, hdr_color)
                with columnas[idx % n_cols]:
                    st.markdown(html, unsafe_allow_html=True)

    _seccion("interna", "Auditoría Interna", "#1b3f72")
    st.markdown('<hr style="border:none;border-top:1px solid #e8e8e8;margin:8px 0;">', unsafe_allow_html=True)
    _seccion("externa", "Auditoría Externa – Icontec 2025", "#b06000")


def _build_info_table(df_latest: pd.DataFrame) -> pd.DataFrame:
    base_cols = [
        c
        for c in [
            "Indicador", "Meta", "Ejecucion", "Meta_Signo", "Meta s", "MetaS", "Ejecucion_Signo", "Ejecución s", "Ejecucion s", "EjecS",
            "Decimales", "Decimales_Meta", "Decimales_Ejecucion", "DecimalesEje", "DecMeta", "DecEjec",
        ]
        if c in df_latest.columns
    ]
    out = df_latest[base_cols].copy() if base_cols else pd.DataFrame(index=df_latest.index)
    if "Indicador" not in out.columns:
        out["Indicador"] = ""
    if "Meta" not in out.columns:
        out["Meta"] = pd.NA
    if "Ejecucion" not in out.columns:
        out["Ejecucion"] = pd.NA
    out = formatear_meta_ejecucion_df(out, meta_col="Meta", ejec_col="Ejecucion")
    out = out.rename(columns={"Ejecucion": "Ejecución"})
    out["Cumplimiento"] = df_latest.get("Cumplimiento_pct", pd.NA).apply(_cumpl_label)
    return out[[c for c in ["Indicador", "Meta", "Ejecución", "Cumplimiento"] if c in out.columns]]


def _fmt_short_value(value: object) -> str:
    num = _to_float(value)
    if num is None:
        return "Sin dato"
    if abs(num) >= 100:
        return f"{num:.0f}"
    return f"{num:.2f}".rstrip("0").rstrip(".")


def _resumir_analisis_texto(texto: object, max_chars: int = 260) -> str:
    if texto is None or (isinstance(texto, float) and pd.isna(texto)):
        return "Sin análisis disponible."
    raw = str(texto).strip()
    if not raw:
        return "Sin análisis disponible."

    # Formato típico API Kawak: fecha | usuario | análisis
    if "|" in raw:
        parts = [p.strip() for p in raw.split("|") if p.strip()]
        if len(parts) >= 3:
            raw = " | ".join(parts[2:]).strip()
        elif len(parts) >= 2:
            raw = parts[-1]

    # Resumen simple y robusto: tomar hasta 2 frases útiles.
    frases = [f.strip() for f in re.split(r"[.!?]\s+", raw) if f.strip()]
    if not frases:
        return raw[:max_chars]
    resumen = ". ".join(frases[:2]).strip()
    if len(resumen) > max_chars:
        resumen = resumen[: max_chars - 3].rstrip() + "..."
    return resumen


def _buscar_analisis_indicador(indicador: str, analisis_map: dict[str, str]) -> str:
    key = _norm_text(indicador)
    if not key or not analisis_map:
        return ""
    if key in analisis_map:
        return analisis_map[key]

    # Fallback aproximado: útil cuando el nombre en una base trae sufijos/prefijos.
    for map_key, val in analisis_map.items():
        if key in map_key or map_key in key:
            return val
    return ""


@st.cache_data(show_spinner=False)
def _load_analisis_indicadores() -> dict[str, str]:
    source = Path(__file__).parents[2] / "data" / "raw" / "Fuentes Consolidadas" / "Consolidado_API_Kawak.xlsx"
    if not source.exists():
        return {}

    try:
        df = pd.read_excel(source, engine="openpyxl")
    except Exception:
        return {}

    ind_col = _first_col(df, ["nombre", "Indicador", "Nombre Indicador", "Indicador Nombre"])
    ana_col = _first_col(df, ["analisis", "análisis"])
    fecha_col = _first_col(df, ["fecha_corte", "fecha", "Fecha corte", "Fecha"])
    if ind_col is None or ana_col is None:
        return {}

    work = df[[c for c in [ind_col, ana_col, fecha_col] if c is not None]].copy()
    if fecha_col is not None:
        work["_fecha_sort"] = pd.to_datetime(work[fecha_col], errors="coerce")
    else:
        work["_fecha_sort"] = pd.NaT
    work = work.sort_values("_fecha_sort")

    out: dict[str, str] = {}
    for _, row in work.dropna(how="all").iterrows():
        indicador = str(row.get(ind_col, "")).strip()
        analisis = str(row.get(ana_col, "")).strip()
        if not indicador:
            continue
        key = _norm_text(indicador)
        if key and analisis:
            out[key] = analisis
    return out


def _latest_year_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "Anio" not in df.columns:
        return df.copy()

    out = df.copy()
    if "Mes" in out.columns:
        out["Mes_num"] = out["Mes"].apply(_mes_to_num)
    else:
        out["Mes_num"] = pd.NA

    sort_cols = [c for c in ["Anio", "Mes_num", "Fecha", "Periodo"] if c in out.columns]
    out = out.sort_values(sort_cols) if sort_cols else out
    return out.groupby("Anio", dropna=True, as_index=False).tail(1).reset_index(drop=True)


def _build_indicator_yearly(
    indicador: str,
    base_df: pd.DataFrame,
    subproceso: str | None = None,
    month_num: int | None = None,
) -> pd.DataFrame:
    if base_df.empty or "Indicador" not in base_df.columns:
        return pd.DataFrame()

    work = base_df[base_df["Indicador"].astype(str) == str(indicador)].copy()
    if subproceso and "Subproceso_final" in work.columns:
        work = work[work["Subproceso_final"].astype(str) == str(subproceso)]
    if month_num is not None and "Mes" in work.columns:
        work = work[work["Mes"].apply(_mes_to_num) == float(month_num)]
    if work.empty:
        return work

    if "Cumplimiento_pct" not in work.columns:
        work["Cumplimiento_pct"] = _cumplimiento_pct(work)
    return _latest_year_rows(work)


def _cumpl_delta(actual: object, previo: object) -> tuple[str, str]:
    a = _to_float(actual)
    p = _to_float(previo)
    if a is None or p is None:
        return "vs año anterior: N/A", "#6E7781"
    delta = a - p
    if delta > 0:
        return f"vs año anterior: +{delta:.1f} pts", "#2E7D32"
    if delta < 0:
        return f"vs año anterior: {delta:.1f} pts", "#C62828"
    return "vs año anterior: 0.0 pts", "#6E7781"


def _render_indicadores_subproceso_cards(
    filtered: pd.DataFrame,
    historic_df: pd.DataFrame,
    anio: int | None,
    month_num: int | None,
    map_df: pd.DataFrame,
    proceso_sel: str,
) -> None:
    if filtered.empty:
        st.info("Sin indicadores para el filtro actual.")
        return

    analisis_map = _load_analisis_indicadores()
    subprocesos_datos = sorted(filtered["Subproceso_final"].dropna().astype(str).unique().tolist()) if "Subproceso_final" in filtered.columns else []
    subprocesos = subprocesos_datos.copy()

    # Tabulación oficial por jerarquía Proceso-Subproceso del maestro.
    if (
        proceso_sel != "Todos"
        and not map_df.empty
        and {"Proceso", "Subproceso"}.issubset(map_df.columns)
    ):
        proceso_norm = _norm_text(proceso_sel)
        map_work = map_df.copy()
        map_work["_proc_norm"] = map_work["Proceso"].astype(str).map(_norm_text)
        map_work["_sub_val"] = map_work["Subproceso"].astype(str).str.strip()
        oficiales = sorted(map_work[map_work["_proc_norm"] == proceso_norm]["_sub_val"].dropna().unique().tolist())

        if oficiales:
            datos_map = {_norm_text(s): s for s in subprocesos_datos}
            subprocesos = [datos_map[_norm_text(s)] for s in oficiales if _norm_text(s) in datos_map]
    if not subprocesos:
        st.info("No hay subprocesos para mostrar en este filtro.")
        return

    sub_tabs = st.tabs([f"{sp}" for sp in subprocesos])
    for tab, sub in zip(sub_tabs, subprocesos):
        with tab:
            sub_df = filtered[filtered["Subproceso_final"].astype(str) == str(sub)].copy()
            sub_df = _latest_per_indicator(sub_df)
            if sub_df.empty:
                st.info("Sin indicadores para este subproceso.")
                continue

            sub_df = sub_df.sort_values("Indicador") if "Indicador" in sub_df.columns else sub_df
            indicadores_total = len(sub_df)
            items_per_page = 15
            total_pages = max(1, (indicadores_total + items_per_page - 1) // items_per_page)

            page_key = f"ind_page_{_norm_text(sub)}"
            selected_key = f"ind_selected_{_norm_text(sub)}"
            if page_key not in st.session_state:
                st.session_state[page_key] = 0

            st.session_state[page_key] = min(max(st.session_state[page_key], 0), total_pages - 1)
            page = st.session_state[page_key]

            start = page * items_per_page
            end = start + items_per_page
            page_df = sub_df.iloc[start:end].copy()

            st.caption(f"Mostrando indicadores {start + 1} a {min(end, indicadores_total)} de {indicadores_total}.")

            cols = st.columns(3)
            for idx, (_, row) in enumerate(page_df.iterrows()):
                indicador = str(row.get("Indicador", "")).strip() or "Indicador sin nombre"
                meta = _fmt_short_value(row.get("Meta"))
                ejec = _fmt_short_value(row.get("Ejecucion"))
                cumpl = _to_float(row.get("Cumplimiento_pct"))
                categoria = _categoria_por_pct(cumpl)

                previo = None
                if anio is not None and "Anio" in historic_df.columns:
                    hist_prev = historic_df[
                        (historic_df["Indicador"].astype(str) == indicador)
                        & (pd.to_numeric(historic_df["Anio"], errors="coerce") == int(anio) - 1)
                    ]
                    if "Subproceso_final" in hist_prev.columns:
                        hist_prev = hist_prev[hist_prev["Subproceso_final"].astype(str) == str(sub)]
                    if month_num is not None and "Mes" in hist_prev.columns:
                        hist_prev = hist_prev[hist_prev["Mes"].apply(_mes_to_num) == float(month_num)]
                    if not hist_prev.empty:
                        previo = _to_float(_latest_per_indicator(hist_prev).iloc[-1].get("Cumplimiento_pct"))

                delta_txt, delta_color = _cumpl_delta(cumpl, previo)
                analisis_txt = _resumir_analisis_texto(_buscar_analisis_indicador(indicador, analisis_map))
                color = NIVELES_COLORS.get(categoria.lower(), "#6E7781")

                with cols[idx % 3]:
                    st.markdown(
                        f"""
                        <div style='background:#f9fbff;border:1px solid #dbe5f1;border-left:6px solid {color};border-radius:10px;padding:12px 12px 10px 12px;margin-bottom:8px;min-height:170px;'>
                            <div style='font-weight:700;color:#1a237e;margin-bottom:6px;line-height:1.25;'>{indicador}</div>
                            <div style='font-size:0.9rem;color:#263238;'>Meta: <b>{meta}</b></div>
                            <div style='font-size:0.9rem;color:#263238;'>Ejecución: <b>{ejec}</b></div>
                            <div style='font-size:0.9rem;color:#263238;'>Cumplimiento: <b>{_cumpl_label(cumpl)}</b></div>
                            <div style='font-size:0.85rem;color:{delta_color};margin-top:4px;'><b>{delta_txt}</b></div>
                            <div style='font-size:0.78rem;color:#455a64;margin-top:6px;line-height:1.25;'>{analisis_txt}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if st.button("Ver detalle", key=f"btn_det_{_norm_text(sub)}_{_norm_text(indicador)}_{idx}", use_container_width=True):
                        st.session_state[selected_key] = indicador

            nav1, nav2, nav3 = st.columns([1, 2, 1])
            with nav1:
                if st.button("< Anterior", key=f"btn_prev_{_norm_text(sub)}", disabled=page == 0, use_container_width=True):
                    st.session_state[page_key] = page - 1
                    st.rerun()
            with nav2:
                st.markdown(f"<div style='text-align:center;padding-top:6px;'>Página <b>{page + 1}</b> de <b>{total_pages}</b></div>", unsafe_allow_html=True)
            with nav3:
                if st.button("Siguiente >", key=f"btn_next_{_norm_text(sub)}", disabled=page >= total_pages - 1, use_container_width=True):
                    st.session_state[page_key] = page + 1
                    st.rerun()

            selected_indicator = st.session_state.get(selected_key)
            if selected_indicator:
                st.markdown(f"#### Detalle del indicador: {selected_indicator}")
                yearly_df = _build_indicator_yearly(selected_indicator, historic_df, subproceso=sub, month_num=month_num)
                if yearly_df.empty:
                    st.info("No hay histórico para el indicador seleccionado.")
                else:
                    chart_df = yearly_df.copy()
                    if "Anio" in chart_df.columns:
                        chart_df["Año"] = pd.to_numeric(chart_df["Anio"], errors="coerce").astype("Int64").astype(str)
                    if "Año" in chart_df.columns:
                        fig = make_subplots(specs=[[{"secondary_y": True}]])
                        if "Meta" in chart_df.columns:
                            fig.add_trace(
                                go.Bar(name="Meta", x=chart_df["Año"], y=pd.to_numeric(chart_df["Meta"], errors="coerce")),
                                secondary_y=False,
                            )
                        if "Ejecucion" in chart_df.columns:
                            fig.add_trace(
                                go.Bar(name="Ejecución", x=chart_df["Año"], y=pd.to_numeric(chart_df["Ejecucion"], errors="coerce")),
                                secondary_y=False,
                            )
                        if "Cumplimiento_pct" in chart_df.columns:
                            fig.add_trace(
                                go.Scatter(
                                    name="Cumplimiento (%)",
                                    x=chart_df["Año"],
                                    y=pd.to_numeric(chart_df["Cumplimiento_pct"], errors="coerce"),
                                    mode="lines+markers",
                                ),
                                secondary_y=True,
                            )
                        fig.update_layout(
                            barmode="group",
                            title="Comparativo anual (Meta/Ejecución + Cumplimiento)",
                            legend_title_text="Métrica",
                        )
                        fig.update_yaxes(title_text="Meta/Ejecución", secondary_y=False)
                        fig.update_yaxes(title_text="Cumplimiento (%)", secondary_y=True)
                        st.plotly_chart(fig, use_container_width=True)

                    table = chart_df[[c for c in ["Anio", "Meta", "Ejecucion", "Cumplimiento_pct"] if c in chart_df.columns]].copy()
                    table = table.rename(columns={"Anio": "Año", "Ejecucion": "Ejecución", "Cumplimiento_pct": "Cumplimiento (%)"})
                    if "Cumplimiento (%)" in table.columns:
                        table["Cumplimiento (%)"] = pd.to_numeric(table["Cumplimiento (%)"], errors="coerce").round(1)
                    st.dataframe(table, use_container_width=True, hide_index=True)

                analisis_raw = _buscar_analisis_indicador(selected_indicator, analisis_map)
                st.markdown("##### Análisis del indicador")
                st.write(_resumir_analisis_texto(analisis_raw, max_chars=420))


def _build_indicadores_table(df_latest: pd.DataFrame) -> pd.DataFrame:
    base_cols = [
        c
        for c in [
            "Subproceso_final", "Indicador", "Meta", "Ejecucion", "Meta_Signo", "Meta s", "MetaS", "Ejecucion_Signo", "Ejecución s", "Ejecucion s", "EjecS",
            "Decimales", "Decimales_Meta", "Decimales_Ejecucion", "DecimalesEje", "DecMeta", "DecEjec",
        ]
        if c in df_latest.columns
    ]
    out = df_latest[base_cols].copy() if base_cols else pd.DataFrame(index=df_latest.index)
    out["Subproceso - Indicador"] = (
        out.get("Subproceso_final", pd.Series(["Sin subproceso"] * len(out), index=out.index)).astype(str)
        + " - "
        + out.get("Indicador", pd.Series([""] * len(out), index=out.index)).astype(str)
    )
    if "Meta" not in out.columns:
        out["Meta"] = pd.NA
    if "Ejecucion" not in out.columns:
        out["Ejecucion"] = pd.NA
    out = formatear_meta_ejecucion_df(out, meta_col="Meta", ejec_col="Ejecucion")
    out = out.rename(columns={"Ejecucion": "Ejecución"})
    out["Cumplimiento"] = df_latest.get("Cumplimiento_pct", pd.NA).apply(_cumpl_label)
    return out[[c for c in ["Subproceso - Indicador", "Meta", "Ejecución", "Cumplimiento"] if c in out.columns]]


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
        st.warning("No se encontró data de seguimiento en data/output/Resultados Consolidados.xlsx (Consolidado Semestral).")
        return
    if map_df.empty:
        st.warning("No se encontró el mapeo de procesos en data/raw/Subproceso-Proceso-Area.xlsx.")
        return

    years = sorted([int(y) for y in pd.to_numeric(tracking_df["Anio"], errors="coerce").dropna().unique().tolist()]) if "Anio" in tracking_df.columns else []
    default_month_num = _default_month_num(tracking_df)
    default_month = MESES_OPCIONES[default_month_num - 1]
    full_work_df = _prepare_tracking(tracking_df, map_df, month_num=None)
    snapshot_df = _prepare_tracking(tracking_df, map_df, month_num=default_month_num)
    procesos_all = sorted(full_work_df["Proceso_padre"].dropna().astype(str).unique().tolist())

    st.markdown("#### Filtros")
    c1, c2, c3 = st.columns(3)
    with c1:
        default_year = 2025 if 2025 in years else (years[-1] if years else None)
        default_year_idx = years.index(default_year) if default_year in years else 0
        anio = st.selectbox("Año", options=years, index=default_year_idx if years else None)
    with c2:
        mes = st.selectbox("Mes", options=MESES_OPCIONES, index=MESES_OPCIONES.index(default_month))
    with c3:
        proceso_placeholder = st.empty()

    # Recalcular datos del corte según mes seleccionado para que Meta/Ejecución/Cumplimiento respondan al filtro
    selected_month_num = MESES_OPCIONES.index(mes) + 1 if mes in MESES_OPCIONES else default_month_num
    snapshot_df = _prepare_tracking(tracking_df, map_df, month_num=selected_month_num)
    base_filtered = snapshot_df.copy()

    if anio is not None and "Anio" in base_filtered.columns:
        base_filtered = base_filtered[pd.to_numeric(base_filtered["Anio"], errors="coerce") == int(anio)]

    if mes and "Mes" in base_filtered.columns:
        mes_num = MESES_OPCIONES.index(mes) + 1
        base_filtered = base_filtered[base_filtered["Mes"].apply(_mes_to_num) == float(mes_num)]

    procesos_filtrados = sorted(base_filtered["Proceso_padre"].dropna().astype(str).unique().tolist())
    opciones_proceso = ["Todos"] + (procesos_filtrados if procesos_filtrados else procesos_all)
    default_index = 1 if len(opciones_proceso) > 1 else 0

    proceso_sel = proceso_placeholder.selectbox("Proceso (Filtro Padre)", options=opciones_proceso, index=default_index)

    filtered = base_filtered.copy()
    if proceso_sel != "Todos":
        filtered = filtered[filtered["Proceso_padre"].astype(str) == proceso_sel]

    subproceso_sel = "Todos"
    if proceso_sel != "Todos":
        subprocesos_filtrados = sorted(filtered["Subproceso_final"].dropna().astype(str).unique().tolist())
        if subprocesos_filtrados:
            sub_options = ["Todos"] + subprocesos_filtrados
            subproceso_sel = st.selectbox("Subproceso", options=sub_options, index=0)
            if subproceso_sel != "Todos":
                filtered = filtered[filtered["Subproceso_final"].astype(str) == subproceso_sel]

    if filtered.empty:
        st.info("No hay datos para la combinación de filtros seleccionada. Se muestran las pestañas en modo informativo.")

    latest = _latest_per_indicator(filtered) if not filtered.empty else filtered.copy()
    selected_process_label = proceso_sel if proceso_sel != "Todos" else "Todos los procesos"
    selected_subprocess_label = subproceso_sel if subproceso_sel != "Todos" else "Todos los subprocesos"

    historic_base = full_work_df.copy()
    if anio is not None and "Anio" in historic_base.columns:
        historic_base = historic_base[pd.to_numeric(historic_base["Anio"], errors="coerce") == int(anio)]
    if proceso_sel != "Todos":
        historic_base = historic_base[historic_base["Proceso_padre"].astype(str) == proceso_sel]
    if subproceso_sel != "Todos":
        historic_base = historic_base[historic_base["Subproceso_final"].astype(str) == subproceso_sel]

    st.caption(f"Filtro Padre activo: {selected_process_label} | Subproceso: {selected_subprocess_label} | Corte: {mes} {anio}")

    tabs = st.tabs([
        "📋 Resumen general",
        "ℹ️ Información por proceso",
        "📊 Indicadores",
        "📈 Evolución",
        "✅ Calidad",
        "🔍 Auditoría",
        "💡 Propuestos",
        "🤖 Análisis IA",
    ])

    with tabs[0]:
        st.markdown("### Resumen general - Gráficas importantes")

        if latest.empty:
            st.warning("No hay datos para construir gráficas con el filtro actual.")
        else:
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
        info_df = _build_info_table(latest)
        if info_df.empty:
            st.info("Sin información para el filtro actual.")
        else:
            st.dataframe(info_df, use_container_width=True, hide_index=True)

    with tabs[2]:
        st.markdown("### Indicadores")
        _render_indicadores_subproceso_cards(latest, full_work_df, anio, selected_month_num, map_df, proceso_sel)

    with tabs[3]:
        st.markdown("### Evolución de indicadores")
        if historic_base.empty:
            st.warning("No hay datos históricos para el filtro activo.")
        else:
            indicador_options = sorted(historic_base["Indicador"].dropna().astype(str).unique().tolist())
            if not indicador_options:
                st.info("No hay indicadores históricos disponibles para el filtro activo.")
            else:
                selected_indicator = st.selectbox("Indicador para evolución", options=indicador_options, index=0)
                if selected_indicator:
                    hist_df = _build_indicator_history(historic_base, selected_indicator)
                    if hist_df.empty:
                        st.info("No hay histórico disponible para el indicador seleccionado.")
                    else:
                        st.plotly_chart(
                            grafico_historico_indicador(hist_df, titulo=f"Evolución de {selected_indicator}"),
                            use_container_width=True,
                        )
                        hist_table = tabla_historica_indicador(hist_df)
                        if hist_table.empty:
                            st.info("No hay registros históricos con cumplimiento calculado.")
                        else:
                            st.markdown("#### Detalle histórico")
                            st.dataframe(hist_table, use_container_width=True, hide_index=True)

    with tabs[4]:
        st.markdown("### Calidad")
        calidad_df, calidad_msg = _load_calidad_data()
        if calidad_msg:
            st.warning(calidad_msg)
        else:
            if proceso_sel != "Todos":
                proc_norm = _norm_text(proceso_sel)
                calidad_df = calidad_df.copy()
                calidad_df["_proc_norm"] = calidad_df["Proceso"].astype(str).map(_norm_text)
                filtro = calidad_df[calidad_df["_proc_norm"] == proc_norm]
                if filtro.empty:
                    filtro = calidad_df[calidad_df["_proc_norm"].apply(lambda x: proc_norm in x or x in proc_norm)]
                calidad_df = filtro.drop(columns=["_proc_norm"], errors="ignore")
            st.dataframe(calidad_df, use_container_width=True, hide_index=True)

    with tabs[5]:
        st.markdown("### Auditoría")
        _render_auditoria_tab(selected_process_label)


    def _load_indicadores_propuestos(proceso_actual: str = "Todos", subproceso_actual: str = "Todos"):
        import pandas as pd
        EXCEL_PATH = (
            Path(__file__).parents[2]
            / "data" / "raw" / "Propuesta Indicadores" / "Indicadores Propuestos.xlsx"
        )
        if not EXCEL_PATH.exists():
            return pd.DataFrame(), f"No existe el archivo: {EXCEL_PATH}"
        try:
            # Retos
            retos = pd.read_excel(EXCEL_PATH, sheet_name="Retos")
            retos_filtrados = retos[retos["Aplica Desempeño"].str.upper() == "SI"][["Proceso", "Subproceso", "Indicador Propuesto"]]
            retos_filtrados = retos_filtrados.dropna(subset=["Indicador Propuesto"])
            retos_filtrados["Indicador Propuesto"] = retos_filtrados["Indicador Propuesto"].astype(str)
            retos_filtrados["Fuente"] = "Retos"

            # Proyectos
            proyectos = pd.read_excel(EXCEL_PATH, sheet_name="Proyectos")
            proyectos_filtrados = proyectos[proyectos["Propuesta"].str.upper() == "SI"][["Proceso", "Subproceso", "Nombre del Indicador Propuesto"]]
            proyectos_filtrados = proyectos_filtrados.rename(columns={"Nombre del Indicador Propuesto": "Indicador Propuesto"})
            proyectos_filtrados = proyectos_filtrados.dropna(subset=["Indicador Propuesto"])
            proyectos_filtrados["Indicador Propuesto"] = proyectos_filtrados["Indicador Propuesto"].astype(str)
            proyectos_filtrados["Fuente"] = "Proyectos"

            # Plan de mejoramiento
            plan = pd.read_excel(EXCEL_PATH, sheet_name="Plan de mejoramiento", header=1)
            plan_filtrados = plan[plan["Propuesta Indicador"].str.upper() == "SI"][ ["Proceso", "Subproceso", "INDICADOR DE RESULTADO O IMPACTO"] ]
            plan_filtrados = plan_filtrados.rename(columns={"INDICADOR DE RESULTADO O IMPACTO": "Indicador Propuesto"})
            plan_filtrados = plan_filtrados.dropna(subset=["Indicador Propuesto"])
            plan_filtrados["Indicador Propuesto"] = plan_filtrados["Indicador Propuesto"].astype(str)
            plan_filtrados["Fuente"] = "Plan de mejoramiento"

            # Calidad
            calidad = pd.read_excel(EXCEL_PATH, sheet_name="Calidad")
            calidad_filtrados = calidad[["Proceso", "Subroceso", "Propuesta SGC (Indicadores)"]]
            calidad_filtrados = calidad_filtrados.rename(columns={"Subroceso": "Subproceso", "Propuesta SGC (Indicadores)": "Indicador Propuesto"})
            calidad_filtrados = calidad_filtrados.dropna(subset=["Indicador Propuesto"])
            calidad_filtrados["Indicador Propuesto"] = calidad_filtrados["Indicador Propuesto"].astype(str)
            calidad_filtrados["Fuente"] = "Calidad"

            df_final = pd.concat([
                retos_filtrados,
                proyectos_filtrados,
                plan_filtrados,
                calidad_filtrados
            ], ignore_index=True)
            df_final = df_final.drop_duplicates(subset=["Proceso", "Subproceso", "Indicador Propuesto", "Fuente"])

            if proceso_actual != "Todos" and "Proceso" in df_final.columns:
                proceso_norm = _norm_text(proceso_actual)
                df_final = df_final[df_final["Proceso"].astype(str).map(_norm_text) == proceso_norm]

            if subproceso_actual != "Todos" and "Subproceso" in df_final.columns:
                sub_norm = _norm_text(subproceso_actual)
                df_final = df_final[df_final["Subproceso"].astype(str).map(_norm_text) == sub_norm]

            return df_final, None
        except Exception as e:
            return pd.DataFrame(), f"Error leyendo indicadores propuestos: {e}"

    def _render_tarjetas_propuestos(df):
        if df.empty:
            st.info("No hay indicadores propuestos para mostrar.")
            return
        procesos = df["Proceso"].dropna().unique()
        for proceso in sorted(procesos):
            sub_df = df[df["Proceso"] == proceso]
            st.markdown(f"<div style='margin-top:24px; margin-bottom:8px; font-size:1.1rem; font-weight:700; color:#1a237e; letter-spacing:0.03em; text-transform:uppercase;'>{proceso}</div>", unsafe_allow_html=True)
            subprocesos = sub_df["Subproceso"].dropna().unique()
            for subproceso in sorted(subprocesos):
                ind_df = sub_df[sub_df["Subproceso"] == subproceso]
                if ind_df.empty:
                    continue
                st.markdown(f"<div style='margin-bottom:6px; font-size:1rem; font-weight:600; color:#3949ab; letter-spacing:0.01em;'>{subproceso}</div>", unsafe_allow_html=True)
                agg = (
                    ind_df.groupby("Indicador Propuesto", dropna=True)["Fuente"]
                    .apply(lambda s: sorted(set(s.dropna().astype(str).tolist())))
                    .reset_index(name="Fuentes")
                )
                if agg.empty:
                    continue
                cols = st.columns(min(3, len(agg)))
                for idx, (_, row) in enumerate(agg.iterrows()):
                    indicador = str(row.get("Indicador Propuesto", "")).strip()
                    fuentes = row.get("Fuentes", [])
                    fuentes_html = "".join([
                        f"<span style='display:inline-block;background:#eef3ff;color:#1a237e;border:1px solid #c9d7ff;border-radius:999px;padding:2px 8px;font-size:0.72rem;margin:0 4px 4px 0;'>{f}</span>"
                        for f in fuentes
                    ])
                    with cols[idx % len(cols)]:
                        st.markdown(f"""
                        <div style='background:linear-gradient(90deg,#e3f2fd 0%,#f3e5f5 100%);border-radius:12px;padding:18px 14px 14px 18px;margin-bottom:14px;box-shadow:0 2px 8px rgba(80,80,120,0.07);border:1px solid #e0e0e0;'>
                            <span style='font-size:1.25rem;color:#1a237e;font-weight:700;line-height:1.3;word-break:break-word;'>{indicador}</span>
                            <div style='margin-top:10px;'>{fuentes_html}</div>
                        </div>
                        """, unsafe_allow_html=True)

    with tabs[6]:
        st.markdown("### Indicadores propuestos por proceso y subproceso")
        st.caption("Esta visualización se actualiza automáticamente con el archivo fuente de indicadores propuestos.")
        df_prop, msg_prop = _load_indicadores_propuestos(proceso_sel, subproceso_sel)
        if msg_prop:
            st.warning(msg_prop)
        else:
            _render_tarjetas_propuestos(df_prop)

    with tabs[7]:
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
