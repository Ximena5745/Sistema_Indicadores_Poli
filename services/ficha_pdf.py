"""
services/ficha_pdf.py — Generador PDF de Ficha Técnica de Indicador.

Usa reportlab (ya en requirements.txt).
Si kaleido está disponible, incrusta el gráfico histórico como imagen PNG;
si no, genera un PDF de texto + tablas sin gráfico (fallback silencioso).
"""

import io
from datetime import date
from typing import Optional

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Paleta institucional ──────────────────────────────────────────────────────
_PRIMARIO = colors.HexColor("#1A3A5C")
_GRIS = colors.HexColor("#64748B")
_FONDO = colors.HexColor("#F8FAFC")
_BORDE = colors.HexColor("#E2E8F0")
_BLANCO = colors.white

_NIVEL_COLORS = {
    "Peligro": colors.HexColor("#D32F2F"),
    "Alerta": colors.HexColor("#FBAF17"),
    "Cumplimiento": colors.HexColor("#43A047"),
    "Sobrecumplimiento": colors.HexColor("#6699FF"),
}

_MARGIN = 1.8 * cm
_PAGE_W, _PAGE_H = A4


# ── Helpers ──────────────────────────────────────────────────────────────────

def _nivel_color(nivel: str):
    return _NIVEL_COLORS.get(nivel, _GRIS)


def _safe(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    s = str(v).strip()
    return s if s and s not in ("nan", "None") else "—"


def _chart_to_png(hist: pd.DataFrame) -> Optional[io.BytesIO]:
    """Renderiza el histórico a PNG en memoria usando kaleido."""
    try:
        import plotly.graph_objects as go

        h = hist.copy()
        if "Periodo" not in h.columns:
            h["Periodo"] = (
                h["Anio"].astype(str) + "-" + h["Mes"].astype(str).str.zfill(2)
            )
        h = h.sort_values("Periodo").tail(12)

        fig = go.Figure()
        if "Ejecucion" in h.columns:
            ev = pd.to_numeric(h["Ejecucion"], errors="coerce")
            if ev.notna().sum() > 1:
                fig.add_trace(
                    go.Scatter(
                        x=h["Periodo"],
                        y=ev,
                        mode="lines+markers",
                        name="Ejecutado",
                        line=dict(color="#1A3A5C", width=2),
                        marker=dict(size=6),
                    )
                )
        if "Meta" in h.columns:
            mv = pd.to_numeric(h["Meta"], errors="coerce")
            if mv.notna().sum() > 1:
                fig.add_trace(
                    go.Scatter(
                        x=h["Periodo"],
                        y=mv,
                        mode="lines",
                        name="Meta",
                        line=dict(color="#94A3B8", width=1.5, dash="dash"),
                    )
                )
        if len(fig.data) == 0 and "cumplimiento_pct" in h.columns:
            fig.add_trace(
                go.Scatter(
                    x=h["Periodo"],
                    y=pd.to_numeric(h["cumplimiento_pct"], errors="coerce"),
                    mode="lines+markers",
                    name="Cumplimiento %",
                    line=dict(color="#1A3A5C", width=2),
                )
            )

        if len(fig.data) == 0:
            return None

        fig.update_layout(
            margin=dict(t=20, b=20, l=40, r=10),
            height=200,
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(size=9, family="Arial"),
            legend=dict(orientation="h", y=1.12),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
        )

        buf = io.BytesIO()
        fig.write_image(buf, format="png", width=700, height=200, scale=2)
        buf.seek(0)
        return buf
    except Exception:
        return None


# ── Constructor principal ─────────────────────────────────────────────────────

def build_ficha_pdf(
    ind_data: pd.Series,
    hist: pd.DataFrame,
    ai_text: str = "",
    tendencia_label: str = "",
    tendencia_icon: str = "",
) -> bytes:
    """
    Construye el PDF de la ficha técnica de un indicador.
    Retorna bytes listos para st.download_button.
    """
    buf = io.BytesIO()
    nombre = _safe(ind_data.get("Indicador"))
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=_MARGIN,
        bottomMargin=_MARGIN,
        leftMargin=_MARGIN,
        rightMargin=_MARGIN,
        title=f"Ficha – {nombre}",
    )

    styles = getSampleStyleSheet()

    def _s(name, **kw):
        return ParagraphStyle(name, parent=styles["Normal"], **kw)

    st_body = _s("body", fontSize=8.5, leading=12, textColor=colors.HexColor("#0F172A"))
    st_label = _s(
        "label",
        fontSize=7,
        leading=10,
        textColor=_GRIS,
        fontName="Helvetica-Bold",
        spaceAfter=1,
    )
    st_title = _s(
        "title",
        fontSize=17,
        leading=21,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=3,
    )
    st_desc = _s("desc", fontSize=8.5, leading=13, textColor=colors.HexColor("#475569"))
    st_section = _s(
        "section",
        fontSize=9,
        leading=13,
        fontName="Helvetica-Bold",
        textColor=_PRIMARIO,
        spaceBefore=6,
        spaceAfter=4,
    )
    st_ai = _s("ai", fontSize=8, leading=13, textColor=colors.HexColor("#334155"))
    st_footer = _s("footer", fontSize=7, leading=10, textColor=_GRIS, alignment=TA_CENTER)

    # ── Extraer campos ────────────────────────────────────────────────────────
    id_ind = _safe(ind_data.get("Id"))
    linea = _safe(ind_data.get("Linea"))
    objetivo = _safe(ind_data.get("Objetivo"))
    descripcion = _safe(
        ind_data.get("descripcion", ind_data.get("Descripcion", ind_data.get("Descripción del indicador", "")))
    )
    meta_val = _safe(ind_data.get("Meta"))
    ejec_val = _safe(ind_data.get("Ejecucion"))
    cump_raw = ind_data.get("cumplimiento_pct", 0)
    cump = float(cump_raw) if pd.notna(cump_raw) else 0.0
    nivel = _safe(ind_data.get("Nivel de cumplimiento"))
    responsable = _safe(
        ind_data.get("responsable", ind_data.get("Responsable del calculo", ind_data.get("Responsable", "")))
    )
    fuente = "Kawak"
    _fml_raw = ind_data.get("Formula", "")
    formula = (
        str(_fml_raw).strip()
        if _fml_raw is not None and not (isinstance(_fml_raw, float) and pd.isna(_fml_raw))
        else ""
    )
    if formula in ("nan", "None"):
        formula = ""
    periodicidad = _safe(ind_data.get("Periodicidad", ind_data.get("Frecuencia", "")))
    nivel_col = _nivel_color(nivel)
    hoy = date.today().strftime("%d/%m/%Y")

    story = []

    # ── ENCABEZADO ────────────────────────────────────────────────────────────
    hdr = Table(
        [
            [
                Paragraph(
                    f"<font color='white' size='7'><b>{linea.upper()}</b></font>",
                    styles["Normal"],
                ),
                Paragraph(
                    f"<font color='#64748B' size='7'>Código: {id_ind}   |   {hoy}</font>",
                    styles["Normal"],
                ),
            ]
        ],
        colWidths=[8 * cm, None],
    )
    hdr.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), _PRIMARIO),
                ("BACKGROUND", (1, 0), (1, 0), _FONDO),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(hdr)
    story.append(Spacer(1, 6))
    story.append(Paragraph(nombre, st_title))

    if descripcion != "—":
        story.append(Paragraph(descripcion, st_desc))
        story.append(Spacer(1, 5))

    # ── KPIs en línea ─────────────────────────────────────────────────────────
    kpi_rows = [
        [
            Paragraph(f"<b>Estado</b><br/>{nivel}", st_body),
            Paragraph(
                f"<b>Tendencia</b><br/>{tendencia_icon} {tendencia_label}", st_body
            ),
            Paragraph(f"<b>Meta</b><br/>{meta_val}", st_body),
            Paragraph(f"<b>Ejecución</b><br/>{ejec_val}", st_body),
            Paragraph(f"<b>Cumplimiento</b><br/>{cump:.1f}%", st_body),
        ]
    ]
    kpi_tbl = Table(kpi_rows, colWidths=[None] * 5)
    kpi_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), _FONDO),
                ("GRID", (0, 0), (-1, -1), 0.5, _BORDE),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TEXTCOLOR", (0, 0), (0, 0), nivel_col),
            ]
        )
    )
    story.append(kpi_tbl)
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_BORDE, spaceAfter=6))

    # ── GRÁFICO HISTÓRICO ─────────────────────────────────────────────────────
    if not hist.empty:
        story.append(Paragraph("Evolución Histórica", st_section))
        img_buf = _chart_to_png(hist)
        if img_buf:
            story.append(RLImage(img_buf, width=16 * cm, height=4.8 * cm))
        else:
            story.append(
                Paragraph(
                    "<i>(Gráfico no disponible — kaleido no instalado)</i>", st_desc
                )
            )
        story.append(Spacer(1, 8))
        story.append(
            HRFlowable(width="100%", thickness=0.5, color=_BORDE, spaceAfter=6)
        )

    # ── FICHA DE IDENTIDAD ────────────────────────────────────────────────────
    story.append(Paragraph("Ficha de Identidad", st_section))
    id_rows = [
        [Paragraph("RESPONSABLE", st_label), Paragraph(responsable, st_body)],
        [Paragraph("FUENTE DE DATOS", st_label), Paragraph(fuente, st_body)],
        [
            Paragraph("FÓRMULA", st_label),
            Paragraph(
                f"<font face='Courier' size='8'>{formula}</font>", st_body
            ),
        ],
        [Paragraph("PERIODICIDAD", st_label), Paragraph(periodicidad, st_body)],
    ]
    id_tbl = Table(id_rows, colWidths=[4 * cm, None])
    id_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), _FONDO),
                ("GRID", (0, 0), (-1, -1), 0.5, _BORDE),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(id_tbl)
    story.append(Spacer(1, 10))

    # ── SEGUIMIENTO POR PERIODO ───────────────────────────────────────────────
    if not hist.empty:
        story.append(Paragraph("Seguimiento por Periodo", st_section))
        h = hist.copy()
        if "Periodo" not in h.columns:
            h["Periodo"] = (
                h["Anio"].astype(str) + "-" + h["Mes"].astype(str).str.zfill(2)
            )
        seg_cols = [
            c
            for c in ["Periodo", "Meta", "Ejecucion", "cumplimiento_pct"]
            if c in h.columns
        ]
        seg = (
            h[seg_cols]
            .rename(columns={"cumplimiento_pct": "% Cumpl."})
            .sort_values("Periodo")
            .tail(10)
            .reset_index(drop=True)
        )
        if "% Cumpl." in seg.columns:
            seg["% Cumpl."] = pd.to_numeric(seg["% Cumpl."], errors="coerce").round(1)

        hdr_row = [Paragraph(f"<b>{c}</b>", st_label) for c in seg.columns]
        seg_table_data = [hdr_row] + [
            [Paragraph(_safe(v), st_body) for v in row] for _, row in seg.iterrows()
        ]
        seg_tbl = Table(seg_table_data, colWidths=[None] * len(seg.columns))
        seg_style = [
            ("BACKGROUND", (0, 0), (-1, 0), _PRIMARIO),
            ("TEXTCOLOR", (0, 0), (-1, 0), _BLANCO),
            ("GRID", (0, 0), (-1, -1), 0.5, _BORDE),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ]
        for i in range(1, len(seg_table_data)):
            if i % 2 == 0:
                seg_style.append(("BACKGROUND", (0, i), (-1, i), _FONDO))
        seg_tbl.setStyle(TableStyle(seg_style))
        story.append(seg_tbl)
        story.append(Spacer(1, 10))

    # ── ANÁLISIS ESTRATÉGICO IA ───────────────────────────────────────────────
    if ai_text:
        story.append(
            HRFlowable(width="100%", thickness=0.5, color=_BORDE, spaceAfter=6)
        )
        story.append(Paragraph("Análisis Estratégico (IA)", st_section))
        # Limpiar markdown básico
        clean = (
            ai_text.replace("**", "")
            .replace("###", "")
            .replace("##", "")
            .replace("#", "")
            .replace("*", "•")
        )
        story.append(Paragraph(clean, st_ai))
        story.append(Spacer(1, 8))

    # ── PIE DE PÁGINA ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 12))
    story.append(
        Paragraph(
            f"Politécnico Grancolombiano · Sistema de Indicadores · {hoy}",
            st_footer,
        )
    )

    doc.build(story)
    buf.seek(0)
    return buf.read()
