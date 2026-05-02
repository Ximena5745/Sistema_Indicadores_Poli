"""
streamlit_app/components/cmi_tabs/modal_ficha.py
Ficha técnica del indicador — layout propuesto.

Estructura:
  1. Encabezado: badge línea + código + título + descripción + chips estado/tendencia
  2. Donut de cumplimiento (Plotly) + meta/ejecución actual
  3. Evolución histórica (líneas Meta vs Ejecución)
  4. Tres tarjetas: Ficha de Identidad | Seguimiento por Periodo | Análisis IA
  5. Botón Exportar PDF (reportlab)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from core.config import COLOR_CATEGORIA, COLOR_CATEGORIA_CLARO, COLORES
from services.strategic_indicators import load_cierres

try:
    from streamlit_app.utils.cmi_helpers import linea_color as _linea_color
except ImportError:
    def _linea_color(_):
        return COLORES.get("primario", "#1A3A5C")


# ── Helpers de visualización ──────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def _get_ai_ficha(nombre, linea, obj, meta, eje, nivel, cump):
    from services.ai_analysis import analizar_ficha_cmi
    return analizar_ficha_cmi(nombre, linea, obj, str(meta), str(eje), nivel, str(cump))


def _tendencia_desde_hist(hist: pd.DataFrame) -> tuple:
    """Devuelve (label, icono) calculando delta entre último y penúltimo periodo."""
    if hist.empty or "cumplimiento_pct" not in hist.columns:
        return "Sin datos", "→"
    vals = pd.to_numeric(hist["cumplimiento_pct"], errors="coerce").dropna()
    if len(vals) < 2:
        return "Estable", "→"
    delta = float(vals.iloc[-1]) - float(vals.iloc[-2])
    if delta > 2:
        return "Al alza", "↑"
    if delta < -2:
        return "A la baja", "↓"
    return "Estable", "→"


def _donut_fig(cump: float, nivel: str) -> go.Figure:
    color = COLOR_CATEGORIA.get(nivel, COLORES.get("sin_dato", "#BDBDBD"))
    capped = min(cump, 130.0)
    fig = go.Figure(
        go.Pie(
            values=[capped, max(0.0, 130.0 - capped)],
            hole=0.72,
            marker=dict(colors=[color, "#E5E7EB"]),
            textinfo="none",
            hoverinfo="none",
            sort=False,
        )
    )
    fig.add_annotation(
        text=f"<b>{cump:.0f}%</b>",
        x=0.5, y=0.58,
        font=dict(size=26, color=color, family="Inter, sans-serif"),
        showarrow=False,
        xanchor="center",
    )
    fig.add_annotation(
        text="CUMPLIMIENTO",
        x=0.5, y=0.40,
        font=dict(size=8, color="#64748B", family="Inter, sans-serif"),
        showarrow=False,
        xanchor="center",
    )
    fig.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),
        showlegend=False,
        height=190,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _hist_fig(hist: pd.DataFrame) -> go.Figure | None:
    if hist.empty:
        return None
    h = hist.copy()
    if "Periodo" not in h.columns:
        h["Periodo"] = h["Anio"].astype(str) + "-" + h["Mes"].astype(str).str.zfill(2)
    h = h.sort_values("Periodo").tail(12)

    fig = go.Figure()
    # Ejecutado
    if "Ejecucion" in h.columns:
        ev = pd.to_numeric(h["Ejecucion"], errors="coerce")
        if ev.notna().sum() > 1:
            fig.add_trace(go.Scatter(
                x=h["Periodo"], y=ev, mode="lines+markers",
                name="Ejecutado",
                line=dict(color=COLORES.get("primario", "#1A3A5C"), width=2),
                marker=dict(size=7, color=COLORES.get("primario", "#1A3A5C")),
            ))
    # Meta
    if "Meta" in h.columns:
        mv = pd.to_numeric(h["Meta"], errors="coerce")
        if mv.notna().sum() > 1:
            fig.add_trace(go.Scatter(
                x=h["Periodo"], y=mv, mode="lines",
                name="Meta",
                line=dict(color="#CBD5E1", width=1.5, dash="dash"),
            ))
    # Fallback: cumplimiento_pct
    if len(fig.data) == 0 and "cumplimiento_pct" in h.columns:
        fig.add_trace(go.Scatter(
            x=h["Periodo"],
            y=pd.to_numeric(h["cumplimiento_pct"], errors="coerce"),
            mode="lines+markers", name="Cumplimiento %",
            line=dict(color=COLORES.get("primario", "#1A3A5C"), width=2),
        ))
        fig.add_hline(y=100, line_dash="dot", line_color="#43A047",
                      annotation_text="Meta 100%", annotation_position="bottom right")

    if len(fig.data) == 0:
        return None

    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        height=210,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=10)),
        xaxis=dict(showgrid=False, tickfont=dict(size=9)),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickfont=dict(size=9)),
        font=dict(family="Inter, sans-serif"),
    )
    return fig


def _card_field(label: str, value: str, monospace: bool = False) -> None:
    """Renderiza label + valor para la Ficha de Identidad."""
    v = value if value and value not in ("nan", "None", "") else "—"
    font = "font-family:monospace;font-size:0.77rem;white-space:pre-wrap;word-break:break-all" \
        if monospace else "font-size:0.83rem"
    st.markdown(
        f"""<div style="margin-bottom:10px">
            <span style="font-size:0.67rem;text-transform:uppercase;letter-spacing:.07em;
                color:#64748B;font-weight:700">{label}</span>
            <div style="{font};color:#0F172A;margin-top:3px;line-height:1.45">{v}</div>
        </div>""",
        unsafe_allow_html=True,
    )


# ── Modal principal ───────────────────────────────────────────────────────────

@st.dialog("Ficha del Indicador", width="large")
def render_modal_ficha(ind_data: pd.Series):
    """
    Ficha técnica del indicador (layout propuesto).
    Activado desde el botón 'Ver ficha' en tab_listado.
    """
    from services.data_loader import cargar_metadatos_kawak

    # Enriquecer ind_data con metadatos desde fuentes Kawak
    # (Consolidado_API_Kawak → descripcion/responsable; Ficha_Tecnica_Indicadores → Formula;
    #  Indicadores Kawak → Periodicidad). La copia garantiza inmutabilidad del original.
    ind_data = ind_data.copy()
    _meta = cargar_metadatos_kawak()
    _id_raw = str(ind_data.get("Id", ""))
    if not _meta.empty and _id_raw:
        _fila = _meta[_meta["Id"].astype(str) == _id_raw]
        if not _fila.empty:
            _r = _fila.iloc[0]
            if "descripcion" in _r.index and pd.notna(_r["descripcion"]):
                ind_data["descripcion"] = str(_r["descripcion"]).strip()
            if "responsable" in _r.index and pd.notna(_r["responsable"]):
                ind_data["responsable"] = str(_r["responsable"]).strip()
            if "Formula" in _r.index:
                _fml = _r["Formula"]
                ind_data["Formula"] = str(_fml).strip() if pd.notna(_fml) else ""
            if "Periodicidad" in _r.index and pd.notna(_r["Periodicidad"]):
                ind_data["Periodicidad"] = str(_r["Periodicidad"]).strip()
    ind_data["Fuente"] = "Kawak"

    # Extraer campos
    nombre  = str(ind_data.get("Indicador", "Sin nombre"))
    id_ind  = str(ind_data.get("Id", ""))
    linea   = str(ind_data.get("Linea", ""))
    objetivo = str(ind_data.get("Objetivo", ""))
    descripcion = str(
        ind_data.get("descripcion", ind_data.get("Descripcion", ind_data.get("Descripción del indicador", "")))
    ).strip()

    meta_val = ind_data.get("Meta", "—")
    ejec_val = ind_data.get("Ejecucion", "—")
    cump_raw = ind_data.get("cumplimiento_pct", 0)
    cump     = float(cump_raw) if pd.notna(cump_raw) else 0.0
    nivel    = str(ind_data.get("Nivel de cumplimiento", "Sin dato"))

    responsable  = str(ind_data.get("responsable", ind_data.get("Responsable del calculo",
                                    ind_data.get("Responsable", "No definido"))))
    fuente       = "Kawak"
    _fml_raw     = ind_data.get("Formula", "")
    formula      = str(_fml_raw).strip() if _fml_raw is not None and not (isinstance(_fml_raw, float) and pd.isna(_fml_raw)) else ""
    if formula in ("nan", "None"):
        formula = ""
    periodicidad = str(ind_data.get("Periodicidad", ind_data.get("Frecuencia", "No definida")))

    linea_dot   = _linea_color(linea)
    nivel_color = COLOR_CATEGORIA.get(nivel, COLORES.get("sin_dato", "#BDBDBD"))
    nivel_bg    = COLOR_CATEGORIA_CLARO.get(nivel, "#EEEEEE")

    # Histórico del indicador
    cierres = load_cierres()
    hist = pd.DataFrame()
    if not cierres.empty and id_ind:
        hist = cierres[cierres["Id"].astype(str) == id_ind].copy()

    tend_label, tend_icon = _tendencia_desde_hist(hist)

    # ── SECCIÓN 1: ENCABEZADO + DONUT ────────────────────────────────────────
    col_hdr, col_donut = st.columns([1.75, 1])

    with col_hdr:
        # Badge línea + código
        st.markdown(
            f"""<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
                <span style="background:{linea_dot};color:#fff;font-size:0.69rem;font-weight:700;
                    letter-spacing:.07em;text-transform:uppercase;padding:4px 11px;
                    border-radius:999px">{linea}</span>
                <span style="color:#64748B;font-size:0.8rem">Código: {id_ind}</span>
            </div>""",
            unsafe_allow_html=True,
        )
        # Título
        st.markdown(
            f"<h2 style='font-size:1.5rem;font-weight:800;color:#0F172A;"
            f"margin:0 0 6px 0;line-height:1.25'>{nombre}</h2>",
            unsafe_allow_html=True,
        )
        # Descripción
        if descripcion and descripcion not in ("nan", "None", ""):
            st.markdown(
                f"<p style='color:#475569;font-size:0.87rem;line-height:1.55;"
                f"margin:0 0 10px 0'>{descripcion}</p>",
                unsafe_allow_html=True,
            )
        # Chips Estado + Tendencia
        tend_color = (
            "#43A047" if tend_icon == "↑"
            else "#D32F2F" if tend_icon == "↓"
            else "#64748B"
        )
        st.markdown(
            f"""<div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:4px">
                <div>
                    <span style="font-size:0.67rem;color:#64748B;font-weight:700;
                        text-transform:uppercase;letter-spacing:.07em;
                        display:block;margin-bottom:3px">Estado actual</span>
                    <span style="background:{nivel_bg};color:{nivel_color};font-size:0.79rem;
                        font-weight:700;padding:5px 12px;border-radius:999px;
                        border:1.5px solid {nivel_color}">✓ {nivel}</span>
                </div>
                <div>
                    <span style="font-size:0.67rem;color:#64748B;font-weight:700;
                        text-transform:uppercase;letter-spacing:.07em;
                        display:block;margin-bottom:3px">Tendencia</span>
                    <span style="background:{tend_color}18;color:{tend_color};font-size:0.79rem;
                        font-weight:700;padding:5px 12px;border-radius:999px;
                        border:1.5px solid {tend_color}40">
                        {tend_icon} {tend_label}
                    </span>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

    with col_donut:
        st.plotly_chart(
            _donut_fig(cump, nivel),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        meta_fmt = str(meta_val) if pd.notna(meta_val) and str(meta_val) not in ("nan", "None", "") else "—"
        ejec_fmt = str(ejec_val) if pd.notna(ejec_val) and str(ejec_val) not in ("nan", "None", "") else "—"
        st.markdown(
            f"""<div style="text-align:center;margin-top:-8px">
                <p style="font-size:0.78rem;color:#64748B;margin:0">Meta: {meta_fmt}</p>
                <p style="font-size:0.85rem;font-weight:700;color:{nivel_color};
                    margin:3px 0 0 0">{ejec_fmt} Actual</p>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown(
        "<hr style='border:none;border-top:1px solid #E2E8F0;margin:16px 0'>",
        unsafe_allow_html=True,
    )

    # ── SECCIÓN 2: EVOLUCIÓN HISTÓRICA ───────────────────────────────────────
    st.markdown(
        "<p style='font-size:0.85rem;font-weight:700;color:#0F172A;"
        "margin-bottom:6px'>~ Evolución Histórica</p>",
        unsafe_allow_html=True,
    )
    fig_hist = _hist_fig(hist)
    if fig_hist is not None:
        st.plotly_chart(fig_hist, use_container_width=True,
                        config={"displayModeBar": False})
    else:
        st.info("No hay datos históricos disponibles para este indicador.")

    st.markdown(
        "<hr style='border:none;border-top:1px solid #E2E8F0;margin:16px 0'>",
        unsafe_allow_html=True,
    )

    # ── SECCIÓN 3: TRES TARJETAS ──────────────────────────────────────────────
    c1, c2, c3 = st.columns([1, 1.1, 1.2])

    # Ficha de Identidad
    with c1:
        st.markdown(
            "<p style='font-size:0.8rem;font-weight:700;color:#0F172A;"
            "margin-bottom:10px'>Ficha de Identidad</p>",
            unsafe_allow_html=True,
        )
        _card_field("👤 RESPONSABLE", responsable)
        _card_field("🗄 FUENTE DE DATOS", fuente)
        _card_field("ƒ FÓRMULA DE CÁLCULO", formula, monospace=True)
        _card_field("📅 PERIODICIDAD", periodicidad)

    # Seguimiento por Periodo
    with c2:
        st.markdown(
            "<p style='font-size:0.8rem;font-weight:700;color:#0F172A;"
            "margin-bottom:10px'>Seguimiento por Periodo</p>",
            unsafe_allow_html=True,
        )
        if not hist.empty:
            h = hist.copy()
            if "Periodo" not in h.columns:
                h["Periodo"] = (
                    h["Anio"].astype(str) + "-" + h["Mes"].astype(str).str.zfill(2)
                )
            seg_cols = [c for c in ["Periodo", "Meta", "Ejecucion", "cumplimiento_pct"]
                        if c in h.columns]
            seg = (
                h[seg_cols]
                .rename(columns={"cumplimiento_pct": "% Cumpl."})
                .sort_values("Periodo")
                .tail(10)
                .reset_index(drop=True)
            )
            if "% Cumpl." in seg.columns:
                seg["% Cumpl."] = pd.to_numeric(seg["% Cumpl."], errors="coerce").round(1)
            st.dataframe(seg, hide_index=True, use_container_width=True, height=210)
        else:
            st.markdown(
                "<span style='color:#94A3B8;font-size:0.85rem'>"
                "Sin datos de seguimiento.</span>",
                unsafe_allow_html=True,
            )

    # Análisis Estratégico IA
    with c3:
        st.markdown(
            "<p style='font-size:0.8rem;font-weight:700;color:#0F172A;"
            "margin-bottom:10px'>🧠 Análisis Estratégico (IA)</p>",
            unsafe_allow_html=True,
        )
        with st.spinner("Generando análisis..."):
            ai_resp = _get_ai_ficha(
                nombre, linea, objetivo,
                meta_val, ejec_val, nivel, cump,
            )
        if ai_resp:
            st.markdown(
                f"<div style='font-size:0.82rem;color:#334155;line-height:1.65;"
                f"max-height:220px;overflow-y:auto'>{ai_resp}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.info("Análisis IA no disponible (sin API key).")

    st.markdown(
        "<hr style='border:none;border-top:1px solid #E2E8F0;margin:18px 0'>",
        unsafe_allow_html=True,
    )

    # ── EXPORTAR PDF ─────────────────────────────────────────────────────────
    from services.ficha_pdf import build_ficha_pdf

    try:
        pdf_bytes = build_ficha_pdf(
            ind_data=ind_data,
            hist=hist,
            ai_text=ai_resp if ai_resp else "",
            tendencia_label=tend_label,
            tendencia_icon=tend_icon,
        )
        file_name = f"ficha_{id_ind}_{nombre[:28].replace(' ', '_')}.pdf"
        st.download_button(
            label="📄 Exportar PDF",
            data=pdf_bytes,
            file_name=file_name,
            mime="application/pdf",
            use_container_width=False,
        )
    except Exception as exc:
        st.warning(f"No se pudo generar el PDF: {exc}")
