"""
streamlit_app/components/interactive_cards.py
Fichas de indicadores mejoradas con análisis IA para Informe por Procesos.

Proporciona:
- _generate_trend_analysis(): Análisis histórico con IA
- render_indicator_card_enhanced(): Tarjeta HTML mejorada
"""

import re

import pandas as pd
import streamlit as st
from typing import Optional
from streamlit_app.utils.formatting import meta_his_signo, ejecucion_his_signo

# Colores para estados
NIVELES_COLORS = {
    "sobrecumplimiento": "#2563EB",
    "cumplimiento": "#047857",
    "alerta": "#F59E0B",
    "peligro": "#DC2626",
    "sin dato": "#6E7781",
}

COLOR_CATEGORIA = {
    "SobreCumplimiento": "#2563EB",
    "Cumplimiento": "#047857",
    "Alerta": "#F59E0B",
    "Peligro": "#DC2626",
    "Sin dato": "#6E7781",
}


def _to_float(value: object) -> float | None:
    """Convierte valor a float."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", "").replace("%", "").strip())
    except (ValueError, AttributeError):
        return None


def _categoria_por_pct(pct: float | None) -> str:
    """Determina categoría por porcentaje."""
    if pct is None or pd.isna(pct):
        return "sin dato"
    if pct >= 105:
        return "sobrecumplimiento"
    elif pct >= 100:
        return "cumplimiento"
    elif pct >= 80:
        return "alerta"
    else:
        return "peligro"


def _status_color_for_pct(pct: float | None) -> str:
    """Color para el porcentaje."""
    if pct is None or pd.isna(pct):
        return "#6E7781"
    if pct >= 105:
        return "#2563EB"
    if pct >= 100:
        return "#047857"
    if pct >= 80:
        return "#F59E0B"
    return "#DC2626"


def _render_progress_bar_html(ejec: object, meta: object, pct: float | None) -> str:
    """Renderiza barra de progreso HTML."""
    ejec_val = _to_float(ejec)
    meta_val = _to_float(meta)
    if ejec_val is None or meta_val is None or meta_val == 0:
        return "<div style='margin-top:12px;color:#475569;font-size:0.82rem;'>No hay datos completos para mostrar la barra de progreso.</div>"

    ratio = max(0.0, min(1.0, ejec_val / meta_val))
    fill_pct = ratio * 100
    color = _status_color_for_pct(pct)
    label = f"{ejec_val:.1f} / {meta_val:.1f}"
    return (
        f"<div style='margin-top:12px;'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;font-size:0.78rem;font-weight:700;color:#334155;margin-bottom:6px;'>"
        f"<span>Ejecución vs Meta</span><span>{label}</span>"
        f"</div>"
        f"<div style='width:100%;height:10px;border-radius:999px;background:#E5ECF8;overflow:hidden;'>"
        f"<div style='width:{fill_pct:.1f}%;height:100%;background:{color};box-shadow:0 3px 8px rgba(15,23,42,0.12);border-radius:999px;'></div>"
        f"</div>"
        f"</div>"
    )


def _fmt_short_value(value: object) -> str:
    """Formatea valor corto."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    val_str = str(value).strip()
    if val_str.lower() in ("nan", "none", ""):
        return "—"
    try:
        num = float(val_str.replace(",", ""))
        if abs(num) >= 1000:
            return f"{num/1000:.1f}K"
        return f"{num:.1f}"
    except (ValueError, AttributeError):
        return val_str[:12]


def _mes_to_num(mes: object) -> float | pd.NA:
    """Convierte mes a número."""
    if mes is None or (isinstance(mes, float) and pd.isna(mes)):
        return pd.NA
    MES_MAP = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    }
    mes_str = str(mes).lower().strip()
    return MES_MAP.get(mes_str, pd.NA)


@st.cache_data(ttl=300, show_spinner=False)
def _get_ai_analysis(
    nombre: str,
    linea: str,
    objetivo: str,
    meta: object,
    ejec: object,
    nivel: str,
    cump: float,
) -> str:
    """Obtiene análisis IA para el indicador."""
    try:
        from services.ai_analysis import analizar_ficha_cmi
        return analizar_ficha_cmi(
            nombre,
            linea or "",
            objetivo or "",
            str(meta) if meta is not None else "—",
            str(ejec) if ejec is not None else "—",
            nivel,
            str(cump) if cump is not None else "0",
        )
    except Exception as e:
        return f"Análisis IA no disponible: {str(e)[:50]}"


def _generate_trend_analysis(
    historic_df: pd.DataFrame,
    indicator_name: str,
    subproceso: str | None = None,
) -> tuple[str, float | None, float | None]:
    """
    Genera análisis histórico para un indicador.
    
    Returns:
        (analisis_text, promedio_historico, tendencia_value)
    """
    if historic_df.empty or "Indicador" not in historic_df.columns:
        return "Sin histórico disponible para generar análisis.", None, None

    # Filtrar por indicador
    work = historic_df[historic_df["Indicador"].astype(str) == str(indicator_name)].copy()
    
    if subproceso and "Subproceso_final" in work.columns:
        work = work[work["Subproceso_final"].astype(str) == str(subproceso)]

    if work.empty:
        return "Sin histórico disponible para este indicador.", None, None

    # Ordenar por año/mes
    if "Anio" in work.columns:
        work["_sort_anio"] = pd.to_numeric(work["Anio"], errors="coerce")
    
    if "Mes" in work.columns:
        work["_sort_mes"] = work["Mes"].apply(_mes_to_num)
        sort_cols = ["_sort_anio", "_sort_mes"]
    elif "Anio" in work.columns:
        sort_cols = ["_sort_anio"]
    else:
        sort_cols = []
    
    if sort_cols:
        work = work.sort_values(sort_cols)

    # Obtener tantos datos como sea posible (según frecuencia)
    cump_col = "Cumplimiento_pct" if "Cumplimiento_pct" in work.columns else "Cumplimiento"
    
    if cump_col not in work.columns:
        return "Sin datos de cumplimiento disponibles.", None, None

    cumpl_values = pd.to_numeric(work[cump_col], errors="coerce").dropna()
    
    if cumpl_values.empty:
        return "Sin datos de cumplimiento disponibles.", None, None

    # Calcular promedio histórico
    promedio = cumpl_values.mean()
    
    # Calcular tendencia (últimos 3 valores)
    tendencia_val = None
    if len(cumpl_values) >= 3:
        ultimos_3 = cumpl_values.tail(3)
        if ultimos_3.iloc[-1] > ultimos_3.iloc[-2] > ultimos_3.iloc[-3]:
            tendencia_val = 1.0  # ↑ Alza
        elif ultimos_3.iloc[-1] < ultimos_3.iloc[-2] < ultimos_3.iloc[-3]:
            tendencia_val = -1.0  # ↓ Baja
        else:
            tendencia_val = 0.0  # → Estable
    elif len(cumpl_values) >= 2:
        if cumpl_values.iloc[-1] > cumpl_values.iloc[-2]:
            tendencia_val = 1.0
        elif cumpl_values.iloc[-1] < cumpl_values.iloc[-2]:
            tendencia_val = -1.0
        else:
            tendencia_val = 0.0
    else:
        tendencia_val = 0.0

    # Obtener datos actuales para IA
    last_row = work.iloc[-1] if not work.empty else None
    current_meta = last_row.get("Meta") if last_row is not None else None
    current_ejec = last_row.get("Ejecucion") if last_row is not None else None
    current_cump = _to_float(last_row.get(cump_col)) if last_row is not None else None
    current_nivel = _categoria_por_pct(current_cump) if current_cump else "sin dato"

    # Llamar IA
    ai_analysis = _get_ai_analysis(
        nombre=indicator_name,
        linea="",
        objetivo="",
        meta=current_meta,
        ejec=current_ejec,
        nivel=current_nivel,
        cump=current_cump or 0.0,
    )

    # Agregar contexto histórico
    tendencia_icon = "↑" if tendencia_val == 1.0 else ("↓" if tendencia_val == -1.0 else "→")
    tendencia_label = "Al alza" if tendencia_val == 1.0 else ("A la baja" if tendencia_val == -1.0 else "Estable")
    
    contexto = f"\n\nContexto historico: promedio {promedio:.1f}%, tendencia {tendencia_icon} ({tendencia_label})"
    
    analisis_final = ai_analysis + contexto if ai_analysis else f"Sin analisis disponible. {contexto}"
    
    return analisis_final, promedio, tendencia_val


def render_indicator_card_enhanced(
    row: pd.Series,
    analisis_ia: str,
    index: int = 0,
) -> str:
    """
    Renderiza una tarjeta de indicador mejorada.
    
    Args:
        row: Fila con datos del indicador
        analisis_ia: Texto de análisis IA
        index: Índice para key única
    
    Returns:
        HTML string de la tarjeta
    """
    # Extraer campos
    indicador = str(row.get("Indicador", "")).strip() or "Indicador sin nombre"
    row_id = str(row.get("Id", "")).strip() or "—"
    proceso = str(row.get("Proceso_padre", row.get("Proceso", "—"))).strip()
    unidad = str(row.get("Unidad", "—")).strip()
    
    meta = meta_his_signo(row)
    ejec = ejecucion_his_signo(row)
    freq = str(row.get("Frecuencia", row.get("Periodicidad", "—"))).strip()
    clasificacion = str(row.get("Clasificacion", "—")).strip()
    
    # Cumplimiento
    cumpl_raw = row.get("Cumplimiento_pct")
    cumpl = _to_float(cumpl_raw)
    categoria = _categoria_por_pct(cumpl)
    color = NIVELES_COLORS.get(categoria.lower(), "#6E7781")
    cumpl_label = f"{cumpl:.1f}%" if cumpl is not None else "Sin dato"
    
    # Progress bar
    progress_html = _render_progress_bar_html(row.get("Ejecucion"), row.get("Meta"), cumpl)
    
    # Truncar análisis IA
    analisis_display = analisis_ia[:300] + "..." if len(analisis_ia) > 300 else analisis_ia
    analisis_display = analisis_display.replace("\n", "<br>")

    card_html = f"""
    <div class='informe-card'>
        <div class='informe-card-header'>
            <div>
                <div class='informe-card-id'>ID: {row_id}</div>
                <div class='informe-card-title'>{indicador}</div>
                <div class='informe-card-meta'>
                    {proceso} {f"• {unidad}" if unidad and unidad != "—" else ""}
                </div>
            </div>
            <div style='text-align:right;'>
                <div class='informe-card-kpi' style='color:{color};'>{cumpl_label}</div>
                <div class='informe-card-badge' style='background:rgba(0,0,0,0.05);color:{color};margin-top:8px;'>{categoria.upper()}</div>
            </div>
        </div>
        {progress_html}
        <div class='informe-card-fields'>
            <div class='informe-card-field'>
                <span class='informe-card-field-label'>Meta</span>
                <span class='informe-card-field-value'>{meta}</span>
            </div>
            <div class='informe-card-field'>
                <span class='informe-card-field-label'>Frecuencia</span>
                <span class='informe-card-field-value'>{freq}</span>
            </div>
            <div class='informe-card-field'>
                <span class='informe-card-field-label'>Clasificación</span>
                <span class='informe-card-field-value'>{clasificacion}</span>
            </div>
        </div>
        <div class='informe-card-analysis'>
            <div class='informe-card-analysis-label'>🧠 Análisis IA</div>
            <div class='informe-card-analysis-text'>{analisis_display}</div>
        </div>
    </div>
    """
    return card_html


# CSS styles para las tarjetas
INFORME_CARD_CSS = """
<style>
.informe-card {
    background: #ffffff;
    border: 1px solid rgba(37, 99, 235, 0.16);
    border-radius: 18px;
    box-shadow: 0 20px 40px rgba(15, 30, 80, 0.08);
    padding: 18px;
    margin-bottom: 16px;
}
.informe-card-header {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    align-items: flex-start;
    margin-bottom: 12px;
}
.informe-card-id {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    margin-bottom: 4px;
    color: #1D4ED8;
    text-transform: uppercase;
}
.informe-card-title {
    font-size: 1rem;
    font-weight: 800;
    color: #102a43;
    line-height: 1.2;
    margin-bottom: 6px;
}
.informe-card-meta {
    font-size: 0.82rem;
    color: #64748B;
    line-height: 1.4;
}
.informe-card-kpi {
    font-size: 2rem;
    font-weight: 800;
    line-height: 1;
}
.informe-card-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 5px 12px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
}
.informe-card-fields {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #E2E8F0;
}
.informe-card-field {
    display: flex;
    flex-direction: column;
    gap: 2px;
}
.informe-card-field-label {
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748B;
}
.informe-card-field-value {
    font-size: 0.85rem;
    font-weight: 600;
    color: #334155;
}
.informe-card-analysis {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #E2E8F0;
}
.informe-card-analysis-label {
    font-size: 0.75rem;
    font-weight: 700;
    color: #0F172A;
    margin-bottom: 6px;
}
.informe-card-analysis-text {
    font-size: 0.8rem;
    color: #475569;
    line-height: 1.5;
    max-height: 4.2em;
    overflow: hidden;
    text-overflow: ellipsis;
}
</style>
"""


def render_metric_card(title: str, value: str, subtitle: str = "", icon: str = "", color: str = "#1A3A5C") -> str:
    """Renderiza una tarjeta de métrica simple (para KPIs)."""
    icon_html = f"{icon} " if icon else ""
    return f"""
    <div style='background:#fff;border:1px solid {color}22;border-radius:14px;padding:16px;box-shadow:0 4px 12px rgba(15,23,42,0.06);'>
        <div style='font-size:0.75rem;color:#64748B;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;'>
            {icon_html}{title}
        </div>
        <div style='font-size:1.6rem;font-weight:800;color:{color};line-height:1.1;'>{value}</div>
        <div style='font-size:0.78rem;color:#475569;margin-top:4px;'>{subtitle}</div>
    </div>
    """