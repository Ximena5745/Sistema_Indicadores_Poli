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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from components.charts import grafico_historico_indicador, tabla_historica_indicador
from streamlit_app.services.data_service import DataService
from streamlit_app.utils.formatting import formatear_meta_ejecucion_df
from services.cmi_filters import filter_df_for_cmi_procesos
from core.proceso_types import TIPOS_PROCESO, get_tipo_color
from streamlit_app.components.dashboard_components import (
    render_executive_kpis,
    render_alertas_criticas,
    render_tabla_analitica,
    render_fichas_indicadores,
    render_analisis_unidad,
    render_historico_tab,
)

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

# ── Estilos y funciones de renderizado de resumen_general.py ──────────────────

NIVELES_COLORS = {
    "sobrecumplimiento": "#6699FF",
    "cumplimiento": "#2E7D32",
    "alerta": "#F9A825",
    "peligro": "#C62828",
    "sin dato": "#6E7781",
}


def _norm_key(value: str) -> str:
    text = str(value or "").strip().upper()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def _ensure_nivel_cumplimiento(df: pd.DataFrame) -> pd.DataFrame:
    if "Nivel de cumplimiento" in df.columns:
        return df
    if "Cumplimiento_pct" not in df.columns and "cumplimiento_pct" in df.columns:
        df = df.copy()
        df["Cumplimiento_pct"] = df["cumplimiento_pct"]
    pct_col = "Cumplimiento_pct" if "Cumplimiento_pct" in df.columns else None
    if pct_col is None:
        df = df.copy()
        df["Nivel de cumplimiento"] = "Sin dato"
        return df
    df = df.copy()
    def _cat(v):
        try:
            v = float(v)
        except Exception:
            return "Sin dato"
        if v >= 105:
            return "Sobrecumplimiento"
        if v >= 100:
            return "Cumplimiento"
        if v >= 80:
            return "Alerta"
        return "Peligro"
    df["Nivel de cumplimiento"] = df[pct_col].apply(_cat)
    return df


def _process_counts_cmi(df: pd.DataFrame, process_col: str) -> pd.DataFrame:
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


def _ensure_tipo_proceso_cmi(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "Tipo de proceso" in df.columns:
        return df
    for col in ["Tipo de proceso_map", "Tipo de proceso_y", "Tipo de proceso_x", "Tipo_proceso", "tipo_proceso"]:
        if col in df.columns:
            df = df.copy()
            df["Tipo de proceso"] = df[col]
            return df
    return df


def _ensure_proceso_cmi(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "Proceso" in df.columns:
        return df
    for col in ["Proceso_map", "Proceso_y", "Proceso_x", "Proceso Padre", "ProcesoPadre", "Proceso_Padre"]:
        if col in df.columns:
            df = df.copy()
            df["Proceso"] = df[col]
            return df
    return df


def _latest_month_for_cierres(df: pd.DataFrame, year: int) -> int | None:
    year_col = "Año" if "Año" in df.columns else ("Anio" if "Anio" in df.columns else None)
    if year_col is None:
        return None
    subset = df[pd.to_numeric(df[year_col], errors="coerce") == year].copy()
    if subset.empty:
        return None

    if "Mes_num" in subset.columns:
        months = pd.to_numeric(subset["Mes_num"], errors="coerce")
    elif "Mes" in subset.columns:
        months = subset["Mes"].apply(_mes_to_num)
    else:
        return None

    months = pd.to_numeric(months, errors="coerce").dropna().astype(int)
    return int(months.max()) if not months.empty else None


def _canonical_tipo_proceso(value: object) -> str | None:
    txt = str(value or "").strip()
    key = _norm_text(txt)
    if not key or key in {"METRICA", "METRICAS"}:
        return None

    tipo_map = {_norm_text(t): t for t in TIPOS_PROCESO}
    return tipo_map.get(key, txt)


def _render_process_card(
    name: str,
    indicadores: int,
    cumplimiento: float,
    delta_vs_base: float | None,
    base_year: int | None,
    color: str,
):
    """Renderiza tarjeta de tipo de proceso con cumplimiento promedio y delta vs año base."""
    up = (delta_vs_base is not None) and (delta_vs_base >= 0)
    delta_color = "#16A34A" if up else "#D32F2F"
    base_label = str(base_year) if base_year is not None else "base"
    delta_text = (
        f"{delta_vs_base:+.1f} pp vs {base_label}" if delta_vs_base is not None and pd.notna(delta_vs_base) else f"Sin dato {base_label}"
    )
    spark = _sparkline_svg("#2A6BB0", up=up)
    st.markdown(
        f"""
        <div style='border-radius:12px;background:#FFFFFF;border:1px solid #DAE4F1;
                    box-shadow:0 3px 8px rgba(0,0,0,0.06);padding:0.75rem;min-height:140px;
                    border-top:4px solid {color};'>
            <p style='font-size:0.84rem;font-weight:700;margin:0;color:{color};'>{name}</p>
            <p style='font-size:0.75rem;color:#546D88;margin:0.2rem 0;'> {indicadores} indicadores</p>
            <p style='font-size:1.5rem;font-weight:800;margin:0.3rem 0;line-height:1.1;color:#1A3A5C;'>
                {cumplimiento:.1f}%
            </p>
            <p style='font-size:0.75rem;color:#546D88;margin:0;'>Cumplimiento promedio</p>
            <p style='font-size:0.74rem;font-weight:700;color:{delta_color};margin:0.15rem 0 0 0;'>{delta_text}</p>
            <div style='display:flex;justify-content:flex-end;margin-top:0.2rem;'>{spark}</div>
        </div>
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


def _build_ia_rows_rpp(rows: list[dict]) -> str:
    """Build IA rows HTML para perspectivas operativas (copiado de resumen_general.py)"""
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


def _render_resumen_procesos_style() -> None:
    """Estilos claros y legibles solo para la pestaña Resumen del CMI por Procesos."""
    st.markdown(
        """
        <style>
        .rpp-summary-card {
            background: #ffffff;
            border: 1px solid #dbe5f2;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(12, 34, 64, 0.06);
            padding: 14px 16px;
            margin: 10px 0 8px 0;
        }
        .rpp-summary-title {
            margin: 0 0 6px 0;
            color: #173a63;
            font-size: 0.94rem;
            font-weight: 700;
        }
        .rpp-summary-text {
            margin: 0;
            color: #3f5875;
            font-size: 0.82rem;
            line-height: 1.5;
        }
        .rpp-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 12px;
            margin-top: 8px;
        }
        .rpp-panel {
            background: #ffffff;
            border: 1px solid #d7e4f2;
            border-radius: 12px;
            padding: 12px;
            box-shadow: 0 2px 8px rgba(17, 46, 81, 0.05);
        }
        .rpp-panel-title {
            margin: 0 0 8px 0;
            font-size: 0.86rem;
            font-weight: 700;
            color: #1a3f6d;
        }
        .rpp-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.8rem;
            color: #23384f;
        }
        .rpp-table th {
            text-align: left;
            background: #f4f8fd;
            color: #35506e;
            font-weight: 700;
            padding: 8px 10px;
            border-bottom: 1px solid #d9e4f2;
        }
        .rpp-table th:last-child,
        .rpp-table td:last-child {
            text-align: right;
        }
        .rpp-table td {
            padding: 8px 10px;
            border-bottom: 1px solid #edf2f8;
            vertical-align: top;
        }
        .rpp-table tr:last-child td {
            border-bottom: none;
        }
        .rpp-empty {
            color: #697b90;
            font-style: italic;
        }
        @media (max-width: 920px) {
            .rpp-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_resumen_overview_cards(
    df: pd.DataFrame,
    selected_process: str,
    selected_subprocess: str,
    global_year: int,
    month_name: str,
) -> None:
    if df.empty:
        st.info("No hay datos disponibles para el resumen general del corte actual.")
        return

    pct_col = "Cumplimiento_pct" if "Cumplimiento_pct" in df.columns else (
        "cumplimiento_pct" if "cumplimiento_pct" in df.columns else None
    )
    cumplimiento = pd.to_numeric(df[pct_col], errors="coerce") if pct_col else pd.Series(dtype="float64")
    avg_cumpl = float(cumplimiento.mean()) if not cumplimiento.dropna().empty else 0.0
    total_process = int(df["Proceso_padre"].dropna().nunique()) if "Proceso_padre" in df.columns else 0
    total_subprocess = int(df["Subproceso_final"].dropna().nunique()) if "Subproceso_final" in df.columns else 0
    total_indicadores = int(df["Indicador"].dropna().shape[0]) if "Indicador" in df.columns else 0
    riesgos = int((cumplimiento < 80).sum()) if not cumplimiento.empty else 0
    alertas = int(((cumplimiento >= 80) & (cumplimiento < 100)).sum()) if not cumplimiento.empty else 0

    st.markdown(
        f"""
        <div style='display:grid;grid-template-columns:repeat(4,minmax(160px,1fr));gap:12px;margin:16px 0;'>
            <div style='background:#ffffff;border:1px solid #d9e4f5;border-radius:14px;padding:16px;box-shadow:0 5px 18px rgba(15,24,44,0.05);'>
                <div style='font-size:0.78rem;font-weight:700;color:#173a63;margin-bottom:8px;'>Indicadores activos</div>
                <div style='font-size:2rem;font-weight:800;color:#1e3a8a;'>{total_indicadores}</div>
                <div style='font-size:0.78rem;color:#4b597d;margin-top:8px;'>Proceso actual: {selected_process}</div>
            </div>
            <div style='background:#ffffff;border:1px solid #d9e4f5;border-radius:14px;padding:16px;box-shadow:0 5px 18px rgba(15,24,44,0.05);'>
                <div style='font-size:0.78rem;font-weight:700;color:#173a63;margin-bottom:8px;'>Procesos / subprocesos</div>
                <div style='font-size:2rem;font-weight:800;color:#1e3a8a;'>{total_process}</div>
                <div style='font-size:0.78rem;color:#4b597d;margin-top:8px;'>Subprocesos: {total_subprocess}</div>
            </div>
            <div style='background:#ffffff;border:1px solid #d9e4f5;border-radius:14px;padding:16px;box-shadow:0 5px 18px rgba(15,24,44,0.05);'>
                <div style='font-size:0.78rem;font-weight:700;color:#173a63;margin-bottom:8px;'>Cumplimiento promedio</div>
                <div style='font-size:2rem;font-weight:800;color:#047857;'>{avg_cumpl:.1f}%</div>
                <div style='font-size:0.78rem;color:#4b597d;margin-top:8px;'>Corte: {month_name} {global_year}</div>
            </div>
            <div style='background:#ffffff;border:1px solid #d9e4f5;border-radius:14px;padding:16px;box-shadow:0 5px 18px rgba(15,24,44,0.05);'>
                <div style='font-size:0.78rem;font-weight:700;color:#173a63;margin-bottom:8px;'>Alertas y riesgos</div>
                <div style='font-size:2rem;font-weight:800;color:#b45309;'>{alertas}</div>
                <div style='font-size:0.78rem;color:#4b597d;margin-top:8px;'>Riesgos: {riesgos}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_propuesta_resumen(
    latest_df: pd.DataFrame,
    proceso_actual: str,
    subproceso_actual: str,
    month_name: str,
    year: int,
) -> None:
    st.markdown("#### Propuesta de acción")
    if latest_df.empty:
        st.info("No hay datos de indicadores en el corte actual para generar una propuesta.")
        return

    propuesta = _build_propuestos(latest_df, proceso_actual)
    if propuesta.empty:
        st.info("No se generó una propuesta con los datos disponibles.")
        return

    row = propuesta.iloc[0].to_dict()
    cards = [
        ("Plan de mejoramiento", row.get("Plan de mejoramiento", "Sin datos"), "#fef3c7", "#92400e"),
        ("PDI 2026-2030", row.get("PDI 2026-2030", "Sin datos"), "#dbeafe", "#1e40af"),
        ("SGA", row.get("SGA", "Sin datos"), "#ede9fe", "#4c1d95"),
        ("Retos", row.get("Retos", "Sin datos"), "#ecfccb", "#365314"),
    ]
    cols = st.columns(4)
    for col, (title, text, background, title_color) in zip(cols, cards):
        col.markdown(
            f"""
            <div style='background:{background};border:1px solid {title_color};border-radius:14px;padding:14px;min-height:130px;'>
                <div style='font-size:0.8rem;font-weight:700;color:{title_color};margin-bottom:10px;'>{title}</div>
                <div style='font-size:0.85rem;color:#1f2937;line-height:1.4;min-height:92px;'>{text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    pct_col = "Cumplimiento_pct" if "Cumplimiento_pct" in latest_df.columns else (
        "cumplimiento_pct" if "cumplimiento_pct" in latest_df.columns else None
    )
    if pct_col:
        riesgos = latest_df[pd.to_numeric(latest_df[pct_col], errors="coerce") < 80].copy()
        if not riesgos.empty:
            top_riesgos = riesgos.sort_values(pct_col).head(3)
            st.markdown("**Top 3 indicadores críticos**")
            for _, r in top_riesgos.iterrows():
                indicador = str(r.get("Indicador", "Sin nombre"))
                proc = str(r.get("Proceso_padre", "Sin proceso"))
                valor = pd.to_numeric(r.get(pct_col), errors="coerce")
                valor_text = f"{valor:.1f}%" if pd.notna(valor) else "Sin dato"
                st.markdown(f"- **{indicador}** ({proc}) — Cumplimiento: {valor_text}")
        else:
            st.success("No hay indicadores críticos para el corte actual.")


def _process_variation_for_rpp(base_df: pd.DataFrame, prev_df: pd.DataFrame, display_col: str) -> tuple[list, list]:
    """Calcula mejores y peores variaciones entre períodos."""
    if base_df.empty or prev_df.empty:
        return [], []

    curr_pct_col = "Cumplimiento_pct" if "Cumplimiento_pct" in base_df.columns else "cumplimiento_pct"
    prev_pct_col = "Cumplimiento_pct" if "Cumplimiento_pct" in prev_df.columns else "cumplimiento_pct"
    if curr_pct_col not in base_df.columns or prev_pct_col not in prev_df.columns:
        return [], []

    curr_proc = (
        base_df.groupby(display_col, dropna=False)
        .agg(indicadores=("Indicador", "count"), actual=(curr_pct_col, "mean"))
        .reset_index()
    )
    prev_proc = (
        prev_df.groupby(display_col, dropna=False)
        .agg(prev=(prev_pct_col, "mean"))
        .reset_index()
    )
    merged = curr_proc.merge(prev_proc, on=display_col, how="left")
    if merged.empty:
        return [], []
    merged["change"] = merged["actual"] - merged["prev"]
    merged = merged.dropna(subset=["change"])

    best = [
        {"name": str(r[display_col]), "change": float(r["change"])}
        for _, r in merged.sort_values("change", ascending=False).head(5).iterrows()
    ]
    worst = [
        {"name": str(r[display_col]), "change": float(r["change"])}
        for _, r in merged.sort_values("change", ascending=True).head(5).iterrows()
    ]
    return best, worst


def _get_prev_month_for_year(tracking_df: pd.DataFrame, year: int) -> int | None:
    """Obtiene el último mes disponible del año anterior."""
    if tracking_df.empty or "Anio" not in tracking_df.columns:
        return None
    subset = tracking_df[tracking_df["Anio"] == year].copy()
    if subset.empty:
        return None

    if "Mes_num" in subset.columns:
        months = pd.to_numeric(subset["Mes_num"], errors="coerce")
    elif "Mes" in subset.columns:
        months = subset["Mes"].apply(_mes_to_num)
    else:
        return None

    months = pd.to_numeric(months, errors="coerce").dropna().astype(int)
    return int(months.max()) if not months.empty else None


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
    """
    Normaliza valores de cumplimiento a porcentaje (0-100 o 0-130).

    Problema #8 FIX: Usa normalizar_valor_a_porcentaje() de core/semantica.
    Elimina hardcoding de heurística "si max_abs <= 2".
    """
    from core.semantica import normalizar_valor_a_porcentaje

    # Caso 1: Cumplimiento_norm (ya normalizado en DECIMAL [0-1.3], convertir a PORCENTAJE)
    if "Cumplimiento_norm" in df.columns:
        vals = pd.to_numeric(df["Cumplimiento_norm"], errors="coerce")
        # Cumplimiento_norm viene en decimal (0-1.3), multiplicar por 100 para porcentaje
        return vals * 100

    # Caso 2: Cumplimiento (puede ser decimal o porcentaje)
    if "Cumplimiento" in df.columns:

        def _norm_cumpl(val):
            """Normaliza un valor individual."""
            return normalizar_valor_a_porcentaje(val)

        return df["Cumplimiento"].apply(_norm_cumpl)

    # Caso 3: Meta/Ejecucion (calcular ratio)
    if {"Meta", "Ejecucion"}.issubset(df.columns):
        meta = pd.to_numeric(df["Meta"].apply(_to_float), errors="coerce")
        ejec = pd.to_numeric(df["Ejecucion"].apply(_to_float), errors="coerce")
        ratio = (ejec / meta.replace({0: pd.NA})) * 100
        return pd.to_numeric(ratio, errors="coerce")

    # Caso 4: No hay datos disponibles
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


def _prepare_tracking(
    df: pd.DataFrame, map_df: pd.DataFrame, month_num: int | None = None
) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()
    if "Proceso" not in out.columns:
        out["Proceso"] = "Sin proceso"

    if not map_df.empty and {"Subproceso", "Proceso"}.issubset(map_df.columns):
        sub_map = (
            map_df[["Subproceso", "Proceso"]].dropna().drop_duplicates(subset=["Subproceso"]).copy()
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

        out = out.drop(
            columns=[
                c
                for c in ["proc_input", "proc_norm", "sub_norm", "Proceso_padre_sub"]
                if c in out.columns
            ]
        )
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
            return (
                _to_float(row.get(col_name)) if col_name is not None and col_name in row else None
            )

        out["Ejecucion"] = out.apply(_row_ejec, axis=1)
        if ejec_col is not None:
            # Fallback para fuentes que no traen columnas Periodo N pero sí Ejecución directa.
            out["Ejecucion"] = out["Ejecucion"].fillna(out[ejec_col].apply(_to_float))
    elif ejec_col is not None:
        out["Ejecucion"] = out[ejec_col].apply(_to_float)
    else:
        out["Ejecucion"] = pd.Series(index=out.index, dtype="float64")

    out["Cumplimiento_pct"] = _cumplimiento_pct(out)
    out = _completar_ejecucion_desde_meta_cumpl(out)
    return out


@st.cache_data(show_spinner=False)
def _load_calidad_data() -> tuple[pd.DataFrame, str | None]:
    excel_path = Path("data") / "raw" / "Monitoreo" / "Monitoreo_Informacion_Procesos 2025.xlsx"
    if not excel_path.exists():
        return pd.DataFrame(), f"No existe el archivo: {excel_path}"

    try:
        # Fuente oficial solicitada por negocio: hoja LISTA DE CHEQUEO (encabezados fila 5).
        df = pd.read_excel(excel_path, sheet_name="LISTA DE CHEQUEO", header=4, engine="openpyxl")
    except Exception as exc:
        return pd.DataFrame(), f"No se pudo leer la hoja LISTA DE CHEQUEO de calidad: {exc}"

    if df.empty:
        return pd.DataFrame(), "La hoja LISTA DE CHEQUEO de calidad está vacía."

    df = df.dropna(how="all")
    df.columns = [str(c).strip() for c in df.columns]

    proc_col = _first_col(df, ["PROCESO", "Proceso"])
    sub_col = _first_col(df, ["SUBPROCESO", "Subproceso"])
    tem_col = _first_col(df, ["Tematica", "Temática"])

    c1_col = _first_col(df, ["I. OPORTUNIDAD", "OPORTUNIDAD"])
    c2_col = _first_col(df, ["II. COMPLETITUD", "COMPLETITUD"])
    c3_col = _first_col(df, ["III. CONSISTENCIA", "CONSISTENCIA"])
    c4_col = _first_col(df, ["IV. PRECISIÓN", "IV. PRECISION", "PRECISIÓN", "PRECISION"])
    c5_col = _first_col(df, ["V. PROTOCOLO", "PROTOCOLO"])

    if proc_col is None:
        return pd.DataFrame(), "No se encontró columna Proceso en LISTA DE CHEQUEO de calidad."
    if any(c is None for c in [c1_col, c2_col, c3_col, c4_col, c5_col]):
        return (
            pd.DataFrame(),
            "No se encontraron las 5 columnas de criterios de calidad en LISTA DE CHEQUEO.",
        )

    out_cols = [
        c
        for c in [proc_col, sub_col, tem_col, c1_col, c2_col, c3_col, c4_col, c5_col]
        if c is not None
    ]
    out = df[out_cols].copy()
    rename_map = {proc_col: "Proceso"}
    if sub_col is not None:
        rename_map[sub_col] = "Subproceso"
    if tem_col is not None:
        rename_map[tem_col] = "Temática"
    rename_map[c1_col] = "I. OPORTUNIDAD"
    rename_map[c2_col] = "II. COMPLETITUD"
    rename_map[c3_col] = "III. CONSISTENCIA"
    rename_map[c4_col] = "IV. PRECISIÓN"
    rename_map[c5_col] = "V. PROTOCOLO"

    out = out.rename(columns=rename_map)

    for col in [
        "I. OPORTUNIDAD",
        "II. COMPLETITUD",
        "III. CONSISTENCIA",
        "IV. PRECISIÓN",
        "V. PROTOCOLO",
    ]:
        out[col] = (
            out[col]
            .astype(str)
            .str.replace("✔", "", regex=False)
            .str.replace("⚠", "", regex=False)
            .str.replace("✘", "", regex=False)
            .str.strip()
            .str.upper()
        )

    def _score_calidad(v: object) -> float | None:
        t = _norm_text(v)
        if not t:
            return None
        if "CUMPLE PARCIAL" in t:
            return 0.5
        if "NO CUMPLE" in t:
            return 0.0
        if "CUMPLE" in t:
            return 1.0
        return None

    crit_cols = [
        "I. OPORTUNIDAD",
        "II. COMPLETITUD",
        "III. CONSISTENCIA",
        "IV. PRECISIÓN",
        "V. PROTOCOLO",
    ]
    score_cols = []
    for c in crit_cols:
        sc = f"{c}__score"
        out[sc] = out[c].apply(_score_calidad)
        score_cols.append(sc)

    out["% Calidad"] = (out[score_cols].mean(axis=1, skipna=True) * 100).round(1)

    def _estado(p: object) -> str:
        n = _to_float(p)
        if n is None:
            return "SIN DATO"
        if n >= 90:
            return "CUMPLE"
        if n >= 70:
            return "CUMPLE PARCIALMENTE"
        return "NO CUMPLE"

    out["Estado calidad"] = out["% Calidad"].apply(_estado)
    out = out.drop(columns=score_cols, errors="ignore")
    out = out.dropna(subset=["Proceso"]).reset_index(drop=True)
    return out, None


def _build_calidad_metrics(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    work = df.copy()
    if "Subproceso" not in work.columns:
        work["Subproceso"] = "Sin subproceso"
    if "% Calidad" not in work.columns:
        work["% Calidad"] = pd.NA
    if "Estado calidad" not in work.columns:
        work["Estado calidad"] = "SIN DATO"

    work["Proceso"] = work["Proceso"].astype(str).str.strip()
    work["Subproceso"] = work["Subproceso"].astype(str).str.strip()
    work["% Calidad"] = pd.to_numeric(work["% Calidad"], errors="coerce")

    proc = (
        work.groupby("Proceso", dropna=False)
        .agg(
            Subprocesos=("Subproceso", "nunique"),
            Registros=("Subproceso", "size"),
            Calidad_promedio=("% Calidad", "mean"),
            Cumple=("Estado calidad", lambda s: (s == "CUMPLE").sum()),
            Cumple_parcialmente=("Estado calidad", lambda s: (s == "CUMPLE PARCIALMENTE").sum()),
            No_cumple=("Estado calidad", lambda s: (s == "NO CUMPLE").sum()),
        )
        .reset_index()
    )
    proc["Calidad_promedio"] = proc["Calidad_promedio"].round(1)
    proc["% Cumple"] = (
        (proc["Cumple"] / proc["Registros"].replace({0: pd.NA}) * 100).round(1).fillna(0)
    )
    proc["% Parcial"] = (
        (proc["Cumple_parcialmente"] / proc["Registros"].replace({0: pd.NA}) * 100)
        .round(1)
        .fillna(0)
    )
    proc["% No cumple"] = (
        (proc["No_cumple"] / proc["Registros"].replace({0: pd.NA}) * 100).round(1).fillna(0)
    )

    sub = (
        work.groupby(["Proceso", "Subproceso"], dropna=False)
        .agg(
            Registros=("Subproceso", "size"),
            Calidad_promedio=("% Calidad", "mean"),
            Cumple=("Estado calidad", lambda s: (s == "CUMPLE").sum()),
            Cumple_parcialmente=("Estado calidad", lambda s: (s == "CUMPLE PARCIALMENTE").sum()),
            No_cumple=("Estado calidad", lambda s: (s == "NO CUMPLE").sum()),
        )
        .reset_index()
    )

    sub["Calidad_promedio"] = sub["Calidad_promedio"].round(1)
    sub["% Cumple"] = (
        (sub["Cumple"] / sub["Registros"].replace({0: pd.NA}) * 100).round(1).fillna(0)
    )
    sub["% Parcial"] = (
        (sub["Cumple_parcialmente"] / sub["Registros"].replace({0: pd.NA}) * 100).round(1).fillna(0)
    )
    sub["% No cumple"] = (
        (sub["No_cumple"] / sub["Registros"].replace({0: pd.NA}) * 100).round(1).fillna(0)
    )

    proc = proc.sort_values(["Calidad_promedio", "Proceso"], ascending=[False, True]).reset_index(
        drop=True
    )
    sub = sub.sort_values(
        ["Proceso", "Calidad_promedio", "Subproceso"], ascending=[True, False, True]
    ).reset_index(drop=True)

    proc = proc.rename(columns={"Calidad_promedio": "% Calidad"})
    sub = sub.rename(columns={"Calidad_promedio": "% Calidad"})
    return proc, sub


def _calif_style_token(value: object) -> tuple[str, str, str]:
    t = _norm_text(value)
    if "NO CUMPLE" in t:
        return "NO CUMPLE", "#ffebee", "#b71c1c"
    if "CUMPLE PARCIAL" in t:
        return "CUMPLE PARCIALMENTE", "#fff8e1", "#e65100"
    if "CUMPLE" in t:
        return "CUMPLE", "#e8f5e9", "#1b5e20"
    return str(value), "#eceff1", "#37474f"


def _render_calidad_kpis_cards(df: pd.DataFrame) -> None:
    if df.empty:
        return

    work = df.copy()
    work["% Calidad"] = pd.to_numeric(work.get("% Calidad"), errors="coerce")
    work["Estado calidad"] = work.get("Estado calidad", "SIN DATO").astype(str)

    total_sub = work["Subproceso"].astype(str).nunique() if "Subproceso" in work.columns else 0
    avg = float(work["% Calidad"].mean()) if not work["% Calidad"].dropna().empty else 0.0

    st.markdown(
        f"""
        <div style='display:grid;grid-template-columns:minmax(260px,420px);gap:10px;margin:8px 0 14px 0;'>
            <div style='background:linear-gradient(135deg,#0d47a1,#1565c0);color:#fff;border-radius:12px;padding:12px;border:1px solid #0b3c8a;'>
                <div style='font-size:0.8rem;opacity:0.9;'>General</div>
                <div style='font-size:1.6rem;font-weight:700;line-height:1.2;'>{avg:.1f}%</div>
                <div style='font-size:0.78rem;opacity:0.9;'>Calidad promedio | {total_sub} subprocesos</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "Subproceso" not in work.columns:
        return

    sub = (
        work.groupby("Subproceso", dropna=False)
        .agg(
            Registros=("Subproceso", "size"),
            Calidad=("% Calidad", "mean"),
            Cumple=("Estado calidad", lambda s: (s == "CUMPLE").sum()),
            Parcial=("Estado calidad", lambda s: (s == "CUMPLE PARCIALMENTE").sum()),
            NoCumple=("Estado calidad", lambda s: (s == "NO CUMPLE").sum()),
        )
        .reset_index()
    )
    sub["Calidad"] = sub["Calidad"].round(1)
    sub = sub.sort_values(["Calidad", "Subproceso"], ascending=[False, True]).reset_index(drop=True)

    palette = [
        ("#e8f5e9", "#1b5e20", "#66bb6a"),
        ("#e3f2fd", "#0d47a1", "#42a5f5"),
        ("#fff8e1", "#e65100", "#ffb74d"),
        ("#f3e5f5", "#4a148c", "#ba68c8"),
        ("#e0f2f1", "#004d40", "#4db6ac"),
        ("#fce4ec", "#880e4f", "#f48fb1"),
    ]

    rows = []
    for idx, (_, r) in enumerate(sub.iterrows()):
        sc = _to_float(r.get("Calidad")) or 0.0
        bg, fg, br = palette[idx % len(palette)]
        cumple = int(r.get("Cumple", 0))
        parcial = int(r.get("Parcial", 0))
        no_cumple = int(r.get("NoCumple", 0))
        rows.append(
            f"<div style='background:{bg};color:{fg};border:1px solid {br};border-radius:12px;padding:10px 12px;'>"
            f"<div style='font-size:0.78rem;opacity:0.85;'>Subproceso</div>"
            f"<div style='font-size:0.95rem;font-weight:700;line-height:1.2;margin-bottom:4px;'>{str(r.get('Subproceso',''))}</div>"
            f"<div style='font-size:1.35rem;font-weight:700;line-height:1.1;'>{sc:.1f}%</div>"
            f"<div style='font-size:0.75rem;margin-top:6px;line-height:1.25;'>"
            f"CUMPLE: <b>{cumple}</b> | CUMPLE PARCIALMENTE: <b>{parcial}</b> | NO CUMPLE: <b>{no_cumple}</b>"
            f"</div>"
            f"<div style='font-size:0.72rem;margin-top:2px;opacity:0.9;'>Registros: {int(r.get('Registros',0))}</div>"
            f"</div>"
        )

    if rows:
        st.markdown(
            "<div style='font-weight:700;margin:2px 0 8px 0;color:#0f172a;'>KPIs por subproceso</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='display:grid;grid-template-columns:repeat(4,minmax(180px,1fr));gap:10px;'>"
            + "".join(rows)
            + "</div>",
            unsafe_allow_html=True,
        )


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
        return (
            pd.DataFrame(),
            "No está instalado pypdf ni PyPDF2. Instala uno de esos paquetes para extraer texto de auditoría.",
        )

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
                        window = sentences[max(0, idx - 1) : min(len(sentences), idx + 2)]
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
        return (
            pd.DataFrame(),
            "No se encontraron menciones directas de procesos en los PDFs de auditoría.",
        )

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

_AUDITORIA_XLSX = (
    Path(__file__).resolve().parents[2] / "data" / "raw" / "Auditoria" / "auditoria_resultado.xlsx"
)

_AUD_LABELS = {
    "fortalezas": ("Fortalezas", "#0d6e55", "✦"),
    "oportunidades_mejora": ("Oportunidades de Mejora", "#7a5c00", "◈"),
    "hallazgos": ("Hallazgos", "#1b4f8a", "◉"),
    "no_conformidades": ("No Conformidades", "#8b1a1a", "▲"),
    "recomendacion_desempeno": ("Recomendación de Desempeño", "#3d2b8e", "◆"),
}


@st.cache_data(show_spinner=False)
def _load_auditoria_excel() -> tuple:
    if not _AUDITORIA_XLSX.exists():
        return (
            pd.DataFrame(),
            f"No existe el archivo: {_AUDITORIA_XLSX.name}. Ejecuta scripts/generar_auditoria_csv.py primero.",
        )
    try:
        df = pd.read_excel(_AUDITORIA_XLSX, sheet_name="Auditoria", engine="openpyxl")
        df = df.fillna("")
        return df, None
    except Exception as e:
        return pd.DataFrame(), f"Error leyendo Excel de auditoría: {e}"


def _render_categoria_card(
    proceso: str,
    label: str,
    items: list,
    pill_bg: str,
    pill_text: str,
    dot_color: str,
    icono: str,
    hdr_color: str,
) -> str:
    """Una tarjeta por categoría: header con color de categoría, nombre de proceso, lista de items."""
    count_badge = f'<span style="background:rgba(255,255,255,0.3);color:#fff;font-size:0.6rem;font-weight:700;padding:1px 7px;border-radius:10px;margin-left:8px;">{len(items)}</span>'
    items_html = "".join(
        f'<div style="display:flex;gap:10px;align-items:flex-start;padding:7px 0;border-bottom:1px solid #f3f4f7;">'
        f'<span style="width:7px;height:7px;min-width:7px;background:{dot_color};border-radius:50%;margin-top:5px;flex-shrink:0;"></span>'
        f'<span style="font-size:0.81rem;color:#2c2c3e;line-height:1.55;word-break:break-word;">{item}</span>'
        f"</div>"
        for item in items
    )
    return (
        f'<div style="background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e4e8f0;'
        f'box-shadow:0 3px 14px rgba(0,0,0,0.08);margin-bottom:18px;">'
        f'<div style="background:{hdr_color};padding:10px 16px;display:flex;align-items:center;justify-content:space-between;">'
        f'<div style="display:flex;align-items:center;gap:7px;">'
        f'<span style="font-size:1rem;line-height:1;">{icono}</span>'
        f'<span style="font-size:0.71rem;font-weight:700;letter-spacing:0.07em;text-transform:uppercase;color:#ffffff;">{label}</span>'
        f"</div>{count_badge}</div>"
        f'<div style="padding:8px 16px 6px 16px;background:{pill_bg};border-bottom:1px solid #eaedf3;">'
        f'<span style="font-size:0.75rem;font-weight:600;color:{pill_text};text-transform:uppercase;letter-spacing:0.04em;">{proceso}</span>'
        f"</div>"
        f'<div style="padding:4px 16px 10px 16px;">{items_html}</div>'
        f"</div>"
    )


def _render_auditoria_tab(proceso_filtro: str) -> None:
    """Renderiza la pestaña Auditoría como fichas ejecutivas por proceso."""
    st.markdown(
        '<p style="font-size:0.82rem;color:#888;margin-bottom:16px;">'
        "Resultados estructurados a partir de informes de auditoría. "
        "Solo se muestran campos con contenido registrado.</p>",
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
        "fortalezas": ("Fortalezas", "#d1f5e0", "#0a5c36", "#1aaa6b", "✅", "#1aaa6b"),
        "oportunidades_mejora": (
            "Oportunidades de Mejora",
            "#fff3cd",
            "#7a5000",
            "#e6a800",
            "🔄",
            "#e6a800",
        ),
        "hallazgos": ("Hallazgos", "#dbeeff", "#003d8f", "#1a6fdb", "🔍", "#1a6fdb"),
        "no_conformidades": ("No Conformidades", "#fde0e0", "#7a0000", "#e63535", "⚠️", "#e63535"),
        "recomendacion_desempeno": (
            "Recomendación Desempeño",
            "#ede0ff",
            "#3d0080",
            "#7c3aed",
            "💡",
            "#7c3aed",
        ),
    }

    def _seccion(tipo: str, titulo: str, color_titulo: str) -> None:
        cols_check = [f"{c}_{tipo}" for c in _CAT_STYLE]
        cols_present = [c for c in cols_check if c in df_filtrado.columns]
        if not cols_present:
            return
        df_tipo = df_filtrado[
            df_filtrado[cols_present].apply(lambda r: r.str.strip().ne("").any(), axis=1)
        ]

        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;margin:20px 0 10px 0;">'
            f'<div style="width:4px;height:28px;border-radius:2px;background:{color_titulo};flex-shrink:0;"></div>'
            f'<span style="font-size:0.95rem;font-weight:700;color:#1a1a2e;">{titulo}</span>'
            f"</div>",
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
                f"letter-spacing:0.04em;padding:8px 0 4px 2px;border-bottom:2px solid {color_titulo};"
                f'margin-bottom:12px;">{proceso}</div>',
                unsafe_allow_html=True,
            )

            # Columnas dinámicas: 1 si hay 1, 2 si hay 2-4, 3 si hay 5+
            n = len(cats_con_datos)
            n_cols = 1 if n == 1 else (2 if n <= 4 else 3)
            columnas = st.columns(n_cols)

            for idx, (estilo, items) in enumerate(cats_con_datos):
                label, pill_bg, pill_text, dot_color, emoji, hdr_color = estilo
                html = _render_categoria_card(
                    proceso, label, items, pill_bg, pill_text, dot_color, emoji, hdr_color
                )
                with columnas[idx % n_cols]:
                    st.markdown(html, unsafe_allow_html=True)

    _seccion("interna", "Auditoría Interna", "#1b3f72")
    st.markdown(
        '<hr style="border:none;border-top:1px solid #e8e8e8;margin:8px 0;">',
        unsafe_allow_html=True,
    )
    _seccion("externa", "Auditoría Externa – Icontec 2025", "#b06000")


def _build_info_table(df_latest: pd.DataFrame) -> pd.DataFrame:
    base_cols = [
        c
        for c in [
            "Indicador",
            "Meta",
            "Ejecucion",
            "Meta_Signo",
            "Meta s",
            "MetaS",
            "Ejecucion_Signo",
            "Ejecución s",
            "Ejecucion s",
            "EjecS",
            "Decimales",
            "Decimales_Meta",
            "Decimales_Ejecucion",
            "DecimalesEje",
            "DecMeta",
            "DecEjec",
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


def _buscar_analisis_periodos(indicador: str, analisis_periodos: dict[str, list[str]]) -> list[str]:
    key = _norm_text(indicador)
    if not key or not analisis_periodos:
        return []
    if key in analisis_periodos:
        return analisis_periodos[key]
    for map_key, vals in analisis_periodos.items():
        if key in map_key or map_key in key:
            return vals
    return []


def _completar_ejecucion_desde_meta_cumpl(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if not {"Meta", "Ejecucion", "Cumplimiento_pct"}.issubset(out.columns):
        return out

    meta = pd.to_numeric(out["Meta"], errors="coerce")
    ejec = pd.to_numeric(out["Ejecucion"], errors="coerce")
    cumpl = pd.to_numeric(out["Cumplimiento_pct"], errors="coerce")
    inferida = meta * (cumpl / 100.0)
    out["Ejecucion"] = ejec.fillna(inferida)
    return out


def _generar_analisis_estandar(yearly_df: pd.DataFrame, textos_periodo: list[str]) -> str:
    if yearly_df.empty:
        return "Sin histórico suficiente para generar análisis cuantitativo."

    work = yearly_df.copy()
    if "Anio" in work.columns:
        work["Anio_num"] = pd.to_numeric(work["Anio"], errors="coerce")
        work = work.sort_values("Anio_num")
    else:
        work["Anio_num"] = pd.NA

    meta_s = pd.to_numeric(work.get("Meta"), errors="coerce")
    ejec_s = pd.to_numeric(work.get("Ejecucion"), errors="coerce")
    cumpl_s = pd.to_numeric(work.get("Cumplimiento_pct"), errors="coerce")

    last_idx = work.index[-1]
    anio = int(work.loc[last_idx, "Anio_num"]) if pd.notna(work.loc[last_idx, "Anio_num"]) else None
    meta = meta_s.loc[last_idx] if last_idx in meta_s.index else pd.NA
    ejec = ejec_s.loc[last_idx] if last_idx in ejec_s.index else pd.NA
    cumpl = cumpl_s.loc[last_idx] if last_idx in cumpl_s.index else pd.NA

    estado = "sin dato"
    if pd.notna(cumpl):
        if float(cumpl) >= 105:
            estado = "sobrecumplimiento"
        elif float(cumpl) >= 100:
            estado = "cumplimiento"
        elif float(cumpl) >= 80:
            estado = "alerta"
        else:
            estado = "peligro"

    lineas: list[str] = []
    if anio is not None:
        lineas.append(
            f"En {anio}, la ejecución fue {_fmt_short_value(ejec)} frente a una meta de {_fmt_short_value(meta)}, "
            f"con cumplimiento de {_fmt_short_value(cumpl)}% ({estado})."
        )

    if len(work) >= 2:
        prev = work.iloc[-2]
        prev_ejec = _to_float(prev.get("Ejecucion"))
        prev_cumpl = _to_float(prev.get("Cumplimiento_pct"))
        curr_ejec = _to_float(ejec)
        curr_cumpl = _to_float(cumpl)

        if curr_ejec is not None and prev_ejec is not None:
            d_e = curr_ejec - prev_ejec
            trend_e = "aumentó" if d_e > 0 else ("disminuyó" if d_e < 0 else "se mantuvo")
            lineas.append(
                f"La ejecución {trend_e} {abs(d_e):.2f} puntos respecto al periodo/año previo comparable."
            )

        if curr_cumpl is not None and prev_cumpl is not None:
            d_c = curr_cumpl - prev_cumpl
            trend_c = "mejoró" if d_c > 0 else ("cayó" if d_c < 0 else "se mantuvo")
            lineas.append(
                f"El cumplimiento {trend_c} {abs(d_c):.2f} puntos frente al periodo/año previo."
            )

    promedio = cumpl_s.dropna().mean() if not cumpl_s.dropna().empty else None
    if promedio is not None and pd.notna(promedio):
        lineas.append(
            f"En el histórico visible, el cumplimiento promedio fue {float(promedio):.1f}%."
        )

    # Complemento cualitativo con últimos análisis registrados por periodos.
    comp = [_resumir_analisis_texto(t, max_chars=180) for t in textos_periodo if str(t).strip()]
    comp = [c for c in comp if c and c != "Sin análisis disponible."]
    if comp:
        lineas.append("Complemento cualitativo de periodos reportados: " + " | ".join(comp[-2:]))

    return "\n\n".join(lineas) if lineas else "Sin análisis disponible."


@st.cache_data(show_spinner=False)
def _load_analisis_indicadores() -> dict[str, str]:
    source = (
        Path(__file__).parents[2]
        / "data"
        / "raw"
        / "Fuentes Consolidadas"
        / "Consolidado_API_Kawak.xlsx"
    )
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


@st.cache_data(show_spinner=False)
def _load_analisis_periodos() -> dict[str, list[str]]:
    source = (
        Path(__file__).parents[2]
        / "data"
        / "raw"
        / "Fuentes Consolidadas"
        / "Consolidado_API_Kawak.xlsx"
    )
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

    out: dict[str, list[str]] = {}
    for _, row in work.dropna(how="all").iterrows():
        indicador = str(row.get(ind_col, "")).strip()
        analisis = str(row.get(ana_col, "")).strip()
        if not indicador or not analisis:
            continue
        key = _norm_text(indicador)
        if not key:
            continue
        out.setdefault(key, []).append(analisis)
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
    work = _completar_ejecucion_desde_meta_cumpl(work)
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
    analisis_periodos = _load_analisis_periodos()
    subprocesos_datos = (
        sorted(filtered["Subproceso_final"].dropna().astype(str).unique().tolist())
        if "Subproceso_final" in filtered.columns
        else []
    )
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
        oficiales = sorted(
            map_work[map_work["_proc_norm"] == proceso_norm]["_sub_val"].dropna().unique().tolist()
        )

        if oficiales:
            datos_map = {_norm_text(s): s for s in subprocesos_datos}
            subprocesos = [
                datos_map[_norm_text(s)] for s in oficiales if _norm_text(s) in datos_map
            ]
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

            st.caption(
                f"Mostrando indicadores {start + 1} a {min(end, indicadores_total)} de {indicadores_total}."
            )

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
                        hist_prev = hist_prev[
                            hist_prev["Mes"].apply(_mes_to_num) == float(month_num)
                        ]
                    if not hist_prev.empty:
                        previo = _to_float(
                            _latest_per_indicator(hist_prev).iloc[-1].get("Cumplimiento_pct")
                        )

                delta_txt, delta_color = _cumpl_delta(cumpl, previo)
                analisis_txt = _resumir_analisis_texto(
                    _buscar_analisis_indicador(indicador, analisis_map)
                )
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

                    if st.button(
                        "Ver detalle",
                        key=f"btn_det_{_norm_text(sub)}_{_norm_text(indicador)}_{idx}",
                        use_container_width=True,
                    ):
                        st.session_state[selected_key] = indicador

            nav1, nav2, nav3 = st.columns([1, 2, 1])
            with nav1:
                if st.button(
                    "< Anterior",
                    key=f"btn_prev_{_norm_text(sub)}",
                    disabled=page == 0,
                    use_container_width=True,
                ):
                    st.session_state[page_key] = page - 1
                    st.rerun()
            with nav2:
                st.markdown(
                    f"<div style='text-align:center;padding-top:6px;'>Página <b>{page + 1}</b> de <b>{total_pages}</b></div>",
                    unsafe_allow_html=True,
                )
            with nav3:
                if st.button(
                    "Siguiente >",
                    key=f"btn_next_{_norm_text(sub)}",
                    disabled=page >= total_pages - 1,
                    use_container_width=True,
                ):
                    st.session_state[page_key] = page + 1
                    st.rerun()

            selected_indicator = st.session_state.get(selected_key)
            if selected_indicator:
                st.markdown(f"#### Detalle del indicador: {selected_indicator}")
                yearly_df = _build_indicator_yearly(
                    selected_indicator, historic_df, subproceso=sub, month_num=month_num
                )
                if yearly_df.empty:
                    st.info("No hay histórico para el indicador seleccionado.")
                else:
                    chart_df = yearly_df.copy()
                    if "Anio" in chart_df.columns:
                        chart_df["Año"] = (
                            pd.to_numeric(chart_df["Anio"], errors="coerce")
                            .astype("Int64")
                            .astype(str)
                        )
                    if "Año" in chart_df.columns:
                        fig = make_subplots(specs=[[{"secondary_y": True}]])
                        if "Meta" in chart_df.columns:
                            fig.add_trace(
                                go.Bar(
                                    name="Meta",
                                    x=chart_df["Año"],
                                    y=pd.to_numeric(chart_df["Meta"], errors="coerce"),
                                ),
                                secondary_y=False,
                            )
                        if "Ejecucion" in chart_df.columns:
                            fig.add_trace(
                                go.Bar(
                                    name="Ejecución",
                                    x=chart_df["Año"],
                                    y=pd.to_numeric(chart_df["Ejecucion"], errors="coerce"),
                                ),
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

                    table = chart_df[
                        [
                            c
                            for c in ["Anio", "Meta", "Ejecucion", "Cumplimiento_pct"]
                            if c in chart_df.columns
                        ]
                    ].copy()
                    table = table.rename(
                        columns={
                            "Anio": "Año",
                            "Ejecucion": "Ejecución",
                            "Cumplimiento_pct": "Cumplimiento (%)",
                        }
                    )
                    if "Ejecución" in table.columns:
                        table["Ejecución"] = pd.to_numeric(table["Ejecución"], errors="coerce")
                    if "Cumplimiento (%)" in table.columns:
                        table["Cumplimiento (%)"] = pd.to_numeric(
                            table["Cumplimiento (%)"], errors="coerce"
                        ).round(1)
                    st.dataframe(table, use_container_width=True, hide_index=True)

                analisis_raw = _buscar_analisis_indicador(selected_indicator, analisis_map)
                analisis_hist = _buscar_analisis_periodos(selected_indicator, analisis_periodos)
                st.markdown("##### Análisis del indicador")
                texto_estandar = _generar_analisis_estandar(yearly_df, analisis_hist)
                if analisis_raw and analisis_raw not in analisis_hist:
                    texto_estandar = (
                        texto_estandar
                        + "\n\n"
                        + "Resumen del último periodo: "
                        + _resumir_analisis_texto(analisis_raw, max_chars=220)
                    )
                st.write(texto_estandar)


def _build_indicadores_table(df_latest: pd.DataFrame) -> pd.DataFrame:
    base_cols = [
        c
        for c in [
            "Subproceso_final",
            "Indicador",
            "Meta",
            "Ejecucion",
            "Meta_Signo",
            "Meta s",
            "MetaS",
            "Ejecucion_Signo",
            "Ejecución s",
            "Ejecucion s",
            "EjecS",
            "Decimales",
            "Decimales_Meta",
            "Decimales_Ejecucion",
            "DecimalesEje",
            "DecMeta",
            "DecEjec",
        ]
        if c in df_latest.columns
    ]
    out = df_latest[base_cols].copy() if base_cols else pd.DataFrame(index=df_latest.index)
    out["Subproceso - Indicador"] = (
        out.get(
            "Subproceso_final", pd.Series(["Sin subproceso"] * len(out), index=out.index)
        ).astype(str)
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
    return out[
        [
            c
            for c in ["Subproceso - Indicador", "Meta", "Ejecución", "Cumplimiento"]
            if c in out.columns
        ]
    ]


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

    riesgo_names = ", ".join(
        top_riesgos.get("Indicador", pd.Series(dtype=str)).astype(str).tolist()
    )
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
        st.warning(
            "No se encontró data de seguimiento en data/output/Resultados Consolidados.xlsx (Consolidado Semestral)."
        )
        return
    if map_df.empty:
        st.warning("No se encontró el mapeo de procesos en data/raw/Subproceso-Proceso-Area.xlsx.")
        return

    years = (
        sorted(
            [
                int(y)
                for y in pd.to_numeric(tracking_df["Anio"], errors="coerce")
                .dropna()
                .unique()
                .tolist()
            ]
        )
        if "Anio" in tracking_df.columns
        else []
    )
    default_month_num = _default_month_num(tracking_df)
    default_month = MESES_OPCIONES[default_month_num - 1]
    full_work_df = _prepare_tracking(tracking_df, map_df, month_num=None)
    # Aplicar filtro global CMI por Procesos: solo indicadores con 'Subprocesos' == 1
    full_work_df = filter_df_for_cmi_procesos(full_work_df, id_column="Id")
    snapshot_df = _prepare_tracking(tracking_df, map_df, month_num=default_month_num)
    procesos_all = sorted(full_work_df["Proceso_padre"].dropna().astype(str).unique().tolist())

    st.markdown("#### Filtros")
    st.caption(
        "Usa los filtros para cambiar el corte de evaluación. El Resumen consolida los indicadores activos de CMI por Procesos y mantiene la semántica oficial de niveles."
    )
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
    selected_month_num = (
        MESES_OPCIONES.index(mes) + 1 if mes in MESES_OPCIONES else default_month_num
    )
    snapshot_df = _prepare_tracking(tracking_df, map_df, month_num=selected_month_num)
    base_filtered = snapshot_df.copy()
    # Asegurar que el corte también respete el filtro CMI por Procesos
    base_filtered = filter_df_for_cmi_procesos(base_filtered, id_column="Id")

    if anio is not None and "Anio" in base_filtered.columns:
        base_filtered = base_filtered[
            pd.to_numeric(base_filtered["Anio"], errors="coerce") == int(anio)
        ]

    if mes and "Mes" in base_filtered.columns:
        mes_num = MESES_OPCIONES.index(mes) + 1
        base_filtered = base_filtered[base_filtered["Mes"].apply(_mes_to_num) == float(mes_num)]

    procesos_filtrados = sorted(
        base_filtered["Proceso_padre"].dropna().astype(str).unique().tolist()
    )
    opciones_proceso = ["Todos"] + (procesos_filtrados if procesos_filtrados else procesos_all)
    default_index = 1 if len(opciones_proceso) > 1 else 0

    proceso_sel = proceso_placeholder.selectbox(
        "Proceso (Filtro Padre)", options=opciones_proceso, index=default_index
    )

    filtered = base_filtered.copy()
    if proceso_sel != "Todos":
        filtered = filtered[filtered["Proceso_padre"].astype(str) == proceso_sel]

    subproceso_sel = "Todos"
    if proceso_sel != "Todos":
        subprocesos_filtrados = sorted(
            filtered["Subproceso_final"].dropna().astype(str).unique().tolist()
        )
        if subprocesos_filtrados:
            sub_options = ["Todos"] + subprocesos_filtrados
            subproceso_sel = st.selectbox("Subproceso", options=sub_options, index=0)
            if subproceso_sel != "Todos":
                filtered = filtered[filtered["Subproceso_final"].astype(str) == subproceso_sel]

    if filtered.empty:
        st.info(
            "No hay datos para la combinación de filtros seleccionada. Se muestran las pestañas en modo informativo."
        )

    latest = _latest_per_indicator(filtered) if not filtered.empty else filtered.copy()
    selected_process_label = proceso_sel if proceso_sel != "Todos" else "Todos los procesos"
    selected_subprocess_label = (
        subproceso_sel if subproceso_sel != "Todos" else "Todos los subprocesos"
    )

    historic_base = full_work_df.copy()
    if anio is not None and "Anio" in historic_base.columns:
        historic_base = historic_base[
            pd.to_numeric(historic_base["Anio"], errors="coerce") == int(anio)
        ]
    if proceso_sel != "Todos":
        historic_base = historic_base[historic_base["Proceso_padre"].astype(str) == proceso_sel]
    if subproceso_sel != "Todos":
        historic_base = historic_base[
            historic_base["Subproceso_final"].astype(str) == subproceso_sel
        ]

    st.caption(
        f"Filtro Padre activo: {selected_process_label} | Subproceso: {selected_subprocess_label} | Corte: {mes} {anio}"
    )

    tabs = st.tabs(
        [
            "📋 Resumen",
            "💡 Propuesta",
            "📈 Análisis Avanzado",
        ]
    )

    with tabs[0]:
        _render_resumen_procesos_style()
        st.markdown("### CMI por Procesos — Vista Global")
        st.caption("Fuente: Consolidado Cierres · Resultados Consolidados.xlsx — Filtrado por año, sin filtros de proceso/subproceso")

        # Selector de año para la vista global (independiente de los filtros superiores)
        _g_year_col, _ = st.columns([2, 5])
        with _g_year_col:
            global_year = st.selectbox(
                "Año", options=years, index=len(years) - 1 if years else 0, key="cmi_global_year"
            )

        # Cargar datos desde el Consolidado Semestral para el año seleccionado
        with st.spinner("Cargando resumen global de CMI por Procesos..."):
            _latest_m = _get_prev_month_for_year(tracking_df, int(global_year)) or 12
            _base_year = int(global_year) - 1

            cmi_global = tracking_df[tracking_df["Anio"] == int(global_year)].copy()
            cmi_global = _prepare_tracking(cmi_global, map_df, month_num=_latest_m)
            cmi_global = filter_df_for_cmi_procesos(cmi_global, id_column="Id")

            cmi_base_2024 = pd.DataFrame()
            if _base_year in years:
                _base_m = _get_prev_month_for_year(tracking_df, int(_base_year))
                if _base_m is not None:
                    cmi_base_2024 = tracking_df[tracking_df["Anio"] == int(_base_year)].copy()
                    cmi_base_2024 = _prepare_tracking(cmi_base_2024, map_df, month_num=int(_base_m))
                    cmi_base_2024 = filter_df_for_cmi_procesos(cmi_base_2024, id_column="Id")

        _latest_month_name = (
            MESES_OPCIONES[int(_latest_m) - 1] if _latest_m and 1 <= int(_latest_m) <= 12 else "Diciembre"
        )
        _base_caption = f"Último mes {_base_year}" if _base_m is not None else f"Sin datos {_base_year}"
        st.caption(
            f"Corte activo en Resumen: {_latest_month_name} {global_year}. Comparación: {global_year} vs {_base_caption}."
        )

        # Filtrar subprocesos válidos del mapeo y de Indicadores por CMI.xlsx
        try:
            _cmi_path = Path(__file__).parents[2] / "data" / "raw" / "Indicadores por CMI.xlsx"
            if _cmi_path.exists():
                _df_cmi = pd.read_excel(_cmi_path, sheet_name=0, engine="openpyxl")
                _df_cmi.columns = [str(c).strip() for c in _df_cmi.columns]
                _subprocesos_cmi = set(
                    _df_cmi.loc[_df_cmi["Subprocesos"] == 1, "Subproceso"].dropna().astype(str).unique()
                )
            else:
                _subprocesos_cmi = set()
        except Exception:
            _subprocesos_cmi = set()

        _subprocesos_validos = set(map_df["Subproceso"].dropna().astype(str).unique()) if not map_df.empty else set()

        def _prepare_resumen_df(df_src: pd.DataFrame) -> pd.DataFrame:
            df_out = df_src.copy()
            if df_out.empty:
                return df_out

            if "Subproceso" in df_out.columns and _subprocesos_cmi:
                valid_subs = _subprocesos_validos & _subprocesos_cmi
                df_out = df_out[df_out["Subproceso"].astype(str).isin(valid_subs)]

            if (
                not df_out.empty
                and not map_df.empty
                and "Subproceso" in df_out.columns
                and "Tipo de proceso" in map_df.columns
            ):
                df_out = df_out.merge(
                    map_df[[c for c in ["Subproceso", "Proceso", "Tipo de proceso"] if c in map_df.columns]].drop_duplicates(),
                    on="Subproceso",
                    how="left",
                )
                df_out = _ensure_tipo_proceso_cmi(df_out)
                df_out = _ensure_proceso_cmi(df_out)

            if "Tipo de proceso" in df_out.columns:
                df_out["Tipo de proceso"] = df_out["Tipo de proceso"].apply(_canonical_tipo_proceso)
                df_out = df_out[df_out["Tipo de proceso"].notna()].copy()

            return df_out

        cmi_global = _prepare_resumen_df(cmi_global)
        cmi_base_2024 = _prepare_resumen_df(cmi_base_2024)

        if cmi_global.empty:
            st.warning("No hay indicadores de CMI por Procesos para el año seleccionado.")
        else:
            # ── Fichas KPI por Tipo de proceso (4 tipos globales) ─────────────
            st.markdown("##### Monitoreo por Tipo de Proceso")

            pct_col = "cumplimiento_pct" if "cumplimiento_pct" in cmi_global.columns else "Cumplimiento_pct"

            type_curr = (
                cmi_global.groupby("Tipo de proceso", dropna=False)
                .agg(indicadores=("Indicador", "count"), actual=(pct_col, "mean"))
                .reset_index()
            )

            # Delta respecto a 2024
            if not cmi_base_2024.empty:
                _pct_prev = "cumplimiento_pct" if "cumplimiento_pct" in cmi_base_2024.columns else "Cumplimiento_pct"
                prev_type = (
                    cmi_base_2024.groupby("Tipo de proceso", dropna=False)
                    .agg(prev=(_pct_prev, "mean"))
                    .reset_index()
                )
                type_curr = type_curr.merge(prev_type, on="Tipo de proceso", how="left")
                type_curr["change"] = type_curr["actual"] - type_curr["prev"]
            else:
                type_curr["prev"] = pd.NA
                type_curr["change"] = pd.NA

            type_curr = type_curr[type_curr["Tipo de proceso"].notna()].copy()
            ordered_tipos = [t for t in TIPOS_PROCESO if t in type_curr["Tipo de proceso"].astype(str).tolist()]
            if ordered_tipos:
                tipo_cols = st.columns(min(4, len(ordered_tipos)))
                for idx, tipo in enumerate(ordered_tipos[:4]):
                    row = type_curr[type_curr["Tipo de proceso"] == tipo].iloc[0]
                    delta = pd.to_numeric(row.get("change"), errors="coerce")
                    tipo_color = get_tipo_color(tipo, light=False)
                    with tipo_cols[idx]:
                        _render_process_card(
                            name=tipo,
                            indicadores=int(row.get("indicadores", 0)),
                            cumplimiento=float(row.get("actual", 0.0) or 0.0),
                            delta_vs_base=None if pd.isna(delta) else float(delta),
                            base_year=_base_year,
                            color=tipo_color,
                        )

            # ── Gráfico principal: cumplimiento promedio por proceso ─────────
            st.markdown("##### Procesos con mayor cumplimiento")
            selected_tipo_chart = st.segmented_control(
                "Tipo de proceso (gráfica)",
                options=["Todos"] + ordered_tipos,
                default="Todos",
                key="cmi_resumen_tipo_chart",
            )
            if selected_tipo_chart is None:
                selected_tipo_chart = "Todos"

            chart_curr = cmi_global.copy()
            chart_base = cmi_base_2024.copy()
            if selected_tipo_chart != "Todos":
                chart_curr = chart_curr[chart_curr["Tipo de proceso"].astype(str) == selected_tipo_chart]
                if not chart_base.empty:
                    chart_base = chart_base[chart_base["Tipo de proceso"].astype(str) == selected_tipo_chart]

            process_col_bar = (
                "Proceso"
                if "Proceso" in chart_curr.columns
                else ("Subproceso_final" if "Subproceso_final" in chart_curr.columns else ("Subproceso" if "Subproceso" in chart_curr.columns else "Proceso"))
            )
            group_cols = [process_col_bar]
            if "Tipo de proceso" in chart_curr.columns:
                group_cols.append("Tipo de proceso")

            proc_curr = (
                chart_curr.groupby(group_cols, dropna=False)
                .agg(actual=(pct_col, "mean"), indicadores=("Indicador", "count"))
                .reset_index()
            )
            proc_count = proc_curr[process_col_bar].nunique()
            st.caption(
                f"Agrupando por: {process_col_bar}. Procesos únicos con datos: {proc_count}."
            )

            if not chart_base.empty:
                _base_pct_col = "cumplimiento_pct" if "cumplimiento_pct" in chart_base.columns else "Cumplimiento_pct"
                proc_base = (
                    chart_base.groupby(group_cols, dropna=False)
                    .agg(base_2024=(_base_pct_col, "mean"))
                    .reset_index()
                )
                proc_comp = proc_curr.merge(proc_base, on=group_cols, how="left")
            else:
                proc_comp = proc_curr.copy()
                proc_comp["base_2024"] = pd.NA

            proc_comp["delta_2024"] = proc_comp["actual"] - pd.to_numeric(proc_comp["base_2024"], errors="coerce")
            proc_comp = proc_comp.sort_values(["Tipo de proceso", "actual"], ascending=[True, False]).head(10)

            if not proc_comp.empty:
                fig_bar = go.Figure()
                fig_bar.add_trace(
                    go.Bar(
                        name=f"Cumplimiento {global_year}",
                        x=proc_comp[process_col_bar],
                        y=proc_comp["actual"],
                        marker_color="#1E4C86",
                        yaxis="y1",
                    )
                )
                if proc_comp["base_2024"].notna().any():
                    fig_bar.add_trace(
                        go.Bar(
                            name=f"Cumplimiento {_base_year}",
                            x=proc_comp[process_col_bar],
                            y=proc_comp["base_2024"],
                            marker_color="#9AB7D5",
                            yaxis="y1",
                        )
                    )
                fig_bar.add_trace(
                    go.Scatter(
                        name="Variación 2025 vs 2024",
                        x=proc_comp[process_col_bar],
                        y=proc_comp["delta_2024"].round(1),
                        mode="lines+markers+text",
                        text=proc_comp["delta_2024"].round(1).astype(str) + "%",
                        textposition="top center",
                        marker=dict(color="#E4572E", size=8),
                        line=dict(color="#E4572E", width=2, dash="dash"),
                        yaxis="y2",
                    )
                )
                fig_bar.update_layout(
                    barmode="group",
                    height=380,
                    margin=dict(t=20, b=120),
                    xaxis_tickangle=-25,
                    xaxis_title="Proceso",
                    yaxis=dict(title="Cumplimiento promedio (%)", side="left", showgrid=False),
                    yaxis2=dict(
                        title="Variación (%)",
                        overlaying="y",
                        side="right",
                        showgrid=False,
                    ),
                    legend_title_text="Comparación histórica",
                )
                st.plotly_chart(fig_bar, use_container_width=True, key="cmi_resumen_bar_chart")

                table_cols = [process_col_bar, "actual", "base_2024", "delta_2024"]
                if "Tipo de proceso" in proc_comp.columns:
                    table_cols.insert(0, "Tipo de proceso")

                proc_table = proc_comp[table_cols].copy()
                proc_table = proc_table.rename(
                    columns={
                        process_col_bar: "Proceso",
                        "actual": f"Cumplimiento {global_year}",
                        "base_2024": f"Cumplimiento {_base_year}",
                        "delta_2024": "Delta"
                    }
                )
                for col in [f"Cumplimiento {global_year}", f"Cumplimiento {_base_year}", "Delta"]:
                    if col in proc_table.columns:
                        proc_table[col] = pd.to_numeric(proc_table[col], errors="coerce").round(1)

                if "Tipo de proceso" in proc_table.columns:
                    proc_table = proc_table.sort_values(["Tipo de proceso", f"Cumplimiento {global_year}"], ascending=[True, False])

                st.markdown("#### Tabla de procesos comparativa")
                st.dataframe(proc_table, use_container_width=True, hide_index=True)
            else:
                st.info("No hay procesos con cumplimiento para el filtro de tipo seleccionado.")

            # ── Variación de procesos respecto a 2024 ────────────────────────
            best_proc_rows, worst_proc_rows = [], []
            _ins_curr = chart_curr.copy()
            _ins_base = chart_base.copy()
            if not _ins_base.empty:
                best_proc_rows, worst_proc_rows = _process_variation_for_rpp(_ins_curr, _ins_base, process_col_bar)

            _proc_counts = _process_counts_cmi(_ins_curr, "Tipo de proceso") if "Tipo de proceso" in _ins_curr.columns else pd.DataFrame()
            _total_p = len(_ins_curr)
            _health_p = 0
            if not _proc_counts.empty:
                _health_p = _proc_counts[["Sobrecumplimiento", "Cumplimiento"]].sum(axis=1).sum()
            _health_pct = round(_health_p / max(_total_p, 1) * 100, 1)
            _op_summary = (
                f"{_health_pct}% de indicadores de proceso en niveles saludables"
                + (f" | Mejora: {best_proc_rows[0]['name']}" if best_proc_rows else "")
                + (f" | Riesgo: {worst_proc_rows[0]['name']}" if worst_proc_rows else "")
            )
            if _base_m is not None and 1 <= int(_base_m) <= 12:
                _base_month_name = MESES_OPCIONES[int(_base_m) - 1]
                _base_detail = f"Base comparativa usada: cierre {_base_year} ({_base_month_name})."
            else:
                _base_detail = f"Base comparativa usada: sin cierre disponible para {_base_year}."
            _best_html = _build_ia_rows_rpp(best_proc_rows)
            _worst_html = _build_ia_rows_rpp(worst_proc_rows)

            st.markdown(
                f"""
                <div class='rpp-summary-card'>
                    <h4 class='rpp-summary-title'>Insights del corte</h4>
                    <p class='rpp-summary-text'>{_op_summary}</p>
                    <p class='rpp-summary-text' style='margin-top:4px;color:#4f6783;'>{_base_detail}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if not _best_html:
                _best_html = "<tr><td colspan='2' class='rpp-empty'>Sin mejoras comparables para este corte.</td></tr>"
            if not _worst_html:
                _worst_html = "<tr><td colspan='2' class='rpp-empty'>Sin riesgos comparables para este corte.</td></tr>"

            st.markdown(
                f"""
                <div class='rpp-grid'>
                    <div class='rpp-panel'>
                        <div class='rpp-panel-title'>Procesos con mayor mejora</div>
                        <table class='rpp-table'>
                            <thead>
                                <tr>
                                    <th>Proceso</th>
                                    <th>Variación</th>
                                </tr>
                            </thead>
                            <tbody>{_best_html}</tbody>
                        </table>
                    </div>
                    <div class='rpp-panel'>
                        <div class='rpp-panel-title'>Procesos en mayor riesgo</div>
                        <table class='rpp-table'>
                            <thead>
                                <tr>
                                    <th>Proceso</th>
                                    <th>Variación</th>
                                </tr>
                            </thead>
                            <tbody>{_worst_html}</tbody>
                        </table>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ── Sección ampliada: KPIs, Alertas, Tabla, Fichas, Unidad ──────────
        if not cmi_global.empty:
            _pct_g = (
                "cumplimiento_pct"
                if "cumplimiento_pct" in cmi_global.columns
                else "Cumplimiento_pct"
            )

            st.divider()
            st.markdown("#### 📊 KPIs Ejecutivos del Corte")
            render_executive_kpis(cmi_global, _pct_g)

            st.divider()
            st.markdown("#### 🚨 Alertas y Hallazgos")
            render_alertas_criticas(cmi_global, _pct_g)

            st.divider()
            st.markdown("#### 📋 Tabla Analítica de Indicadores")
            render_tabla_analitica(cmi_global, _pct_g)

            st.divider()
            st.markdown("#### 🗂️ Fichas de Indicadores")
            render_fichas_indicadores(cmi_global, _pct_g)

            st.divider()
            st.markdown("#### 🏢 Análisis por Unidad Organizacional")
            render_analisis_unidad(cmi_global, _pct_g)

    with tabs[1]:
        st.markdown("### Propuesta de mejora")
        st.caption(
            "Gráficas, tablas e insights que complementan la sección Resumen CMI por Procesos."
        )
        _render_propuesta_resumen(
            latest,
            proceso_sel,
            subproceso_sel,
            _latest_month_name,
            int(global_year),
        )

        if not cmi_global.empty:
            st.markdown("##### Procesos con mayor cumplimiento")
            selected_tipo_chart = st.segmented_control(
                "Tipo de proceso (gráfica)",
                options=["Todos"] + ordered_tipos,
                default="Todos",
                key="cmi_propuesta_tipo_chart",
            )
            if selected_tipo_chart is None:
                selected_tipo_chart = "Todos"

            chart_curr = cmi_global.copy()
            chart_base = cmi_base_2024.copy()
            if selected_tipo_chart != "Todos":
                chart_curr = chart_curr[chart_curr["Tipo de proceso"].astype(str) == selected_tipo_chart]
                if not chart_base.empty:
                    chart_base = chart_base[chart_base["Tipo de proceso"].astype(str) == selected_tipo_chart]

            process_col_bar = (
                "Proceso"
                if "Proceso" in chart_curr.columns
                else ("Subproceso_final" if "Subproceso_final" in chart_curr.columns else ("Subproceso" if "Subproceso" in chart_curr.columns else "Proceso"))
            )
            group_cols = [process_col_bar]
            if "Tipo de proceso" in chart_curr.columns:
                group_cols.append("Tipo de proceso")

            proc_curr = (
                chart_curr.groupby(group_cols, dropna=False)
                .agg(actual=(pct_col, "mean"), indicadores=("Indicador", "count"))
                .reset_index()
            )
            proc_count = proc_curr[process_col_bar].nunique()
            st.caption(
                f"Agrupando por: {process_col_bar}. Procesos únicos con datos: {proc_count}."
            )

            if not chart_base.empty:
                _base_pct_col = "cumplimiento_pct" if "cumplimiento_pct" in chart_base.columns else "Cumplimiento_pct"
                proc_base = (
                    chart_base.groupby(group_cols, dropna=False)
                    .agg(base_2024=(_base_pct_col, "mean"))
                    .reset_index()
                )
                proc_comp = proc_curr.merge(proc_base, on=group_cols, how="left")
            else:
                proc_comp = proc_curr.copy()
                proc_comp["base_2024"] = pd.NA

            proc_comp["delta_2024"] = proc_comp["actual"] - pd.to_numeric(proc_comp["base_2024"], errors="coerce")
            proc_comp = proc_comp.sort_values(["Tipo de proceso", "actual"], ascending=[True, False]).head(10)

            if not proc_comp.empty:
                fig_bar = go.Figure()
                fig_bar.add_trace(
                    go.Bar(
                        name=f"Cumplimiento {global_year}",
                        x=proc_comp[process_col_bar],
                        y=proc_comp["actual"],
                        marker_color="#1E4C86",
                        yaxis="y1",
                    )
                )
                if proc_comp["base_2024"].notna().any():
                    fig_bar.add_trace(
                        go.Bar(
                            name=f"Cumplimiento {_base_year}",
                            x=proc_comp[process_col_bar],
                            y=proc_comp["base_2024"],
                            marker_color="#9AB7D5",
                            yaxis="y1",
                        )
                    )
                fig_bar.add_trace(
                    go.Scatter(
                        name="Variación 2025 vs 2024",
                        x=proc_comp[process_col_bar],
                        y=proc_comp["delta_2024"].round(1),
                        mode="lines+markers+text",
                        text=proc_comp["delta_2024"].round(1).astype(str) + "%",
                        textposition="top center",
                        marker=dict(color="#E4572E", size=8),
                        line=dict(color="#E4572E", width=2, dash="dash"),
                        yaxis="y2",
                    )
                )
                fig_bar.update_layout(
                    barmode="group",
                    height=380,
                    margin=dict(t=20, b=120),
                    xaxis_tickangle=-25,
                    xaxis_title="Proceso",
                    yaxis=dict(title="Cumplimiento promedio (%)", side="left", showgrid=False),
                    yaxis2=dict(
                        title="Variación (%)",
                        overlaying="y",
                        side="right",
                        showgrid=False,
                    ),
                    legend_title_text="Comparación histórica",
                )
                st.plotly_chart(fig_bar, use_container_width=True, key="cmi_propuesta_bar_chart")

                table_cols = [process_col_bar, "actual", "base_2024", "delta_2024"]
                if "Tipo de proceso" in proc_comp.columns:
                    table_cols.insert(0, "Tipo de proceso")

                proc_table = proc_comp[table_cols].copy()
                proc_table = proc_table.rename(
                    columns={
                        process_col_bar: "Proceso",
                        "actual": f"Cumplimiento {global_year}",
                        "base_2024": f"Cumplimiento {_base_year}",
                        "delta_2024": "Delta"
                    }
                )
                for col in [f"Cumplimiento {global_year}", f"Cumplimiento {_base_year}", "Delta"]:
                    if col in proc_table.columns:
                        proc_table[col] = pd.to_numeric(proc_table[col], errors="coerce").round(1)

                if "Tipo de proceso" in proc_table.columns:
                    proc_table = proc_table.sort_values(["Tipo de proceso", f"Cumplimiento {global_year}"], ascending=[True, False])

                st.markdown("#### Tabla de procesos comparativa")
                st.dataframe(proc_table, use_container_width=True, hide_index=True)
            else:
                st.info("No hay procesos con cumplimiento para el filtro de tipo seleccionado.")

            best_proc_rows, worst_proc_rows = [], []
            _ins_curr = chart_curr.copy()
            _ins_base = chart_base.copy()
            if not _ins_base.empty:
                best_proc_rows, worst_proc_rows = _process_variation_for_rpp(_ins_curr, _ins_base, process_col_bar)

            _proc_counts = _process_counts_cmi(_ins_curr, "Tipo de proceso") if "Tipo de proceso" in _ins_curr.columns else pd.DataFrame()
            _total_p = len(_ins_curr)
            _health_p = 0
            if not _proc_counts.empty:
                _health_p = _proc_counts[["Sobrecumplimiento", "Cumplimiento"]].sum(axis=1).sum()
            _health_pct = round(_health_p / max(_total_p, 1) * 100, 1)
            _op_summary = (
                f"{_health_pct}% de indicadores de proceso en niveles saludables"
                + (f" | Mejora: {best_proc_rows[0]['name']}" if best_proc_rows else "")
                + (f" | Riesgo: {worst_proc_rows[0]['name']}" if worst_proc_rows else "")
            )
            if _base_m is not None and 1 <= int(_base_m) <= 12:
                _base_month_name = MESES_OPCIONES[int(_base_m) - 1]
                _base_detail = f"Base comparativa usada: cierre {_base_year} ({_base_month_name})."
            else:
                _base_detail = f"Base comparativa usada: sin cierre disponible para {_base_year}."
            _best_html = _build_ia_rows_rpp(best_proc_rows)
            _worst_html = _build_ia_rows_rpp(worst_proc_rows)

            st.markdown(
                f"""
                <div class='rpp-summary-card'>
                    <h4 class='rpp-summary-title'>Insights del corte</h4>
                    <p class='rpp-summary-text'>{_op_summary}</p>
                    <p class='rpp-summary-text' style='margin-top:4px;color:#4f6783;'>{_base_detail}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if not _best_html:
                _best_html = "<tr><td colspan='2' class='rpp-empty'>Sin mejoras comparables para este corte.</td></tr>"
            if not _worst_html:
                _worst_html = "<tr><td colspan='2' class='rpp-empty'>Sin riesgos comparables para este corte.</td></tr>"

            st.markdown(
                f"""
                <div class='rpp-grid'>
                    <div class='rpp-panel'>
                        <div class='rpp-panel-title'>Procesos con mayor mejora</div>
                        <table class='rpp-table'>
                            <thead>
                                <tr>
                                    <th>Proceso</th>
                                    <th>Variación</th>
                                </tr>
                            </thead>
                            <tbody>{_best_html}</tbody>
                        </table>
                    </div>
                    <div class='rpp-panel'>
                        <div class='rpp-panel-title'>Procesos en mayor riesgo</div>
                        <table class='rpp-table'>
                            <thead>
                                <tr>
                                    <th>Proceso</th>
                                    <th>Variación</th>
                                </tr>
                            </thead>
                            <tbody>{_worst_html}</tbody>
                        </table>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with tabs[2]:
        st.markdown("### 📈 Análisis Avanzado — Histórico de Indicadores")
        st.caption(
            "Evolución temporal de indicadores seleccionados. "
            "Compara períodos y detecta tendencias (↑ creciente, ↓ decreciente, → estable)."
        )
        if not cmi_global.empty:
            _pct_g2 = (
                "cumplimiento_pct"
                if "cumplimiento_pct" in cmi_global.columns
                else "Cumplimiento_pct"
            )
            render_historico_tab(cmi_global, _pct_g2)
        else:
            st.info("No hay datos disponibles para el análisis histórico en este corte.")

def _load_indicadores_propuestos(
    proceso_actual: str = "Todos", subproceso_actual: str = "Todos"
):
    import pandas as pd

    EXCEL_PATH = (
        Path(__file__).parents[2]
        / "data"
        / "raw"
        / "Propuesta Indicadores"
        / "Indicadores Propuestos.xlsx"
    )
    if not EXCEL_PATH.exists():
        return pd.DataFrame(), f"No existe el archivo: {EXCEL_PATH}"
    try:
        # Retos
        retos = pd.read_excel(EXCEL_PATH, sheet_name="Retos")
        retos_filtrados = retos[retos["Aplica Desempeño"].str.upper() == "SI"][
            ["Proceso", "Subproceso", "Indicador Propuesto"]
        ]
        retos_filtrados = retos_filtrados.dropna(subset=["Indicador Propuesto"])
        retos_filtrados["Indicador Propuesto"] = retos_filtrados["Indicador Propuesto"].astype(
            str
        )
        factor_ret = _first_col(retos, ["Factor", "FACTOR"])
        car_ret = _first_col(retos, ["Caracteristica", "Característica", "CARACTERÍSTICA"])
        if factor_ret is not None:
            retos_filtrados["Factor"] = retos.loc[retos_filtrados.index, factor_ret].astype(str)
        else:
            retos_filtrados["Factor"] = ""
        if car_ret is not None:
            retos_filtrados["Característica"] = retos.loc[
                retos_filtrados.index, car_ret
            ].astype(str)
        else:
            retos_filtrados["Característica"] = ""
        retos_filtrados["Fuente"] = "Retos"

        # Proyectos
        proyectos = pd.read_excel(EXCEL_PATH, sheet_name="Proyectos")
        proyectos_filtrados = proyectos[proyectos["Propuesta"].str.upper() == "SI"][
            ["Proceso", "Subproceso", "Nombre del Indicador Propuesto"]
        ]
        proyectos_filtrados = proyectos_filtrados.rename(
            columns={"Nombre del Indicador Propuesto": "Indicador Propuesto"}
        )
        proyectos_filtrados = proyectos_filtrados.dropna(subset=["Indicador Propuesto"])
        proyectos_filtrados["Indicador Propuesto"] = proyectos_filtrados[
            "Indicador Propuesto"
        ].astype(str)
        proyectos_filtrados["Factor"] = ""
        proyectos_filtrados["Característica"] = ""
        proyectos_filtrados["Fuente"] = "Proyectos"

        # Plan de mejoramiento
        plan = pd.read_excel(EXCEL_PATH, sheet_name="Plan de mejoramiento", header=1)
        plan_filtrados = plan[plan["Propuesta Indicador"].str.upper() == "SI"][
            ["Proceso", "Subproceso", "INDICADOR DE RESULTADO O IMPACTO"]
        ]
        plan_filtrados = plan_filtrados.rename(
            columns={"INDICADOR DE RESULTADO O IMPACTO": "Indicador Propuesto"}
        )
        plan_filtrados = plan_filtrados.dropna(subset=["Indicador Propuesto"])
        plan_filtrados["Indicador Propuesto"] = plan_filtrados["Indicador Propuesto"].astype(
            str
        )
        factor_col = _first_col(plan, ["FACTOR", "Factor"])
        car_col = _first_col(plan, ["CARACTERÍSTICA", "Característica", "CARACTERISTICA"])
        plan_filtrados["Factor"] = (
            plan.loc[plan_filtrados.index, factor_col].astype(str)
            if factor_col is not None
            else ""
        )
        plan_filtrados["Característica"] = (
            plan.loc[plan_filtrados.index, car_col].astype(str) if car_col is not None else ""
        )
        plan_filtrados["Fuente"] = "Plan de mejoramiento"

        # Calidad
        calidad = pd.read_excel(EXCEL_PATH, sheet_name="Calidad")
        calidad_filtrados = calidad[["Proceso", "Subroceso", "Propuesta SGC (Indicadores)"]]
        calidad_filtrados = calidad_filtrados.rename(
            columns={
                "Subroceso": "Subproceso",
                "Propuesta SGC (Indicadores)": "Indicador Propuesto",
            }
        )
        calidad_filtrados = calidad_filtrados.dropna(subset=["Indicador Propuesto"])
        calidad_filtrados["Indicador Propuesto"] = calidad_filtrados[
            "Indicador Propuesto"
        ].astype(str)
        calidad_filtrados["Factor"] = ""
        calidad_filtrados["Característica"] = ""
        calidad_filtrados["Fuente"] = "Calidad"

        df_final = pd.concat(
            [retos_filtrados, proyectos_filtrados, plan_filtrados, calidad_filtrados],
            ignore_index=True,
        )
        df_final = df_final.drop_duplicates(
            subset=["Proceso", "Subproceso", "Indicador Propuesto", "Fuente"]
        )

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
    source_style = {
        "Retos": {"bg": "#e8f5e9", "border": "#66bb6a", "title": "#1b5e20"},
        "Proyectos": {"bg": "#e3f2fd", "border": "#42a5f5", "title": "#0d47a1"},
        "Plan de mejoramiento": {"bg": "#fff3e0", "border": "#ffb74d", "title": "#e65100"},
        "Calidad": {"bg": "#f3e5f5", "border": "#ba68c8", "title": "#4a148c"},
    }
    source_order = ["Retos", "Proyectos", "Plan de mejoramiento", "Calidad"]

    procesos = sorted(df["Proceso"].dropna().astype(str).unique().tolist())
    proc_tabs = st.tabs(procesos)

    for tab, proceso in zip(proc_tabs, procesos):
        with tab:
            proc_df = df[df["Proceso"].astype(str) == proceso].copy()
            subps = sorted(proc_df["Subproceso"].dropna().astype(str).unique().tolist())
            if not subps:
                st.info("Sin subprocesos con propuestas para este proceso.")
                continue

            sub_tabs = st.tabs(subps)
            for sub_tab, sp in zip(sub_tabs, subps):
                with sub_tab:
                    sp_df_all = proc_df[proc_df["Subproceso"].astype(str) == sp].copy()
                    col_blocks = st.columns(4)
                    for i, fuente in enumerate(source_order):
                        with col_blocks[i]:
                            style = source_style[fuente]
                            st.markdown(
                                f"<div style='font-weight:700;color:{style['title']};margin-bottom:8px;border-left:4px solid {style['border']};padding-left:8px;'>{fuente}</div>",
                                unsafe_allow_html=True,
                            )
                            src_df = sp_df_all[sp_df_all["Fuente"].astype(str) == fuente].copy()
                            if src_df.empty:
                                st.caption("Sin propuestas")
                                continue

                            for _, r in src_df.iterrows():
                                ind = str(r.get("Indicador Propuesto", "")).strip()
                                fac = str(r.get("Factor", "")).strip()
                                car = str(r.get("Característica", "")).strip()
                                extra = ""
                                if fuente == "Plan de mejoramiento":
                                    tags = []
                                    if fac and fac.lower() != "nan":
                                        tags.append(f"Factor: {fac}")
                                    if car and car.lower() != "nan":
                                        tags.append(f"Característica: {car}")
                                    extra = (
                                        "<div style='font-size:0.74rem;color:#5d4037;margin-top:6px;line-height:1.2;'>"
                                        + " | ".join(tags)
                                        + "</div>"
                                        if tags
                                        else ""
                                    )
                                st.markdown(
                                    f"""
                                    <div style='background:{style['bg']};border:1px solid {style['border']};border-radius:10px;padding:10px 10px;margin-bottom:8px;'>
                                        <div style='font-size:0.88rem;color:#263238;line-height:1.25;font-weight:600;'>{ind}</div>
                                        {extra}
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )


