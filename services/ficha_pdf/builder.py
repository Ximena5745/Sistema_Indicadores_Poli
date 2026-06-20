"""
services/ficha_pdf/builder.py
=============================

PDF document builder for indicator technical sheet.

Responsibility: Orchestrate PDF construction from indicator data.
"""

import io
from datetime import date

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

from .charts import chart_to_png
from .utils import MARGIN, BORDE, BLANCO, FONDO, GRIS, PRIMARIO, PAGE_W, PAGE_H, nivel_color, safe, fmt_meta_from_dict, fmt_ejec_from_dict, fmt_valor_signo


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
    nombre = safe(ind_data.get("Indicador"))
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
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
        textColor=GRIS,
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
        textColor=PRIMARIO,
        spaceBefore=6,
        spaceAfter=4,
    )
    st_ai = _s("ai", fontSize=8, leading=13, textColor=colors.HexColor("#334155"))
    st_footer = _s("footer", fontSize=7, leading=10, textColor=GRIS, alignment=TA_CENTER)

    # ── Extraer campos ────────────────────────────────────────────────────────
    id_ind = safe(ind_data.get("Id"))
    linea = safe(ind_data.get("Linea"))
    objetivo = safe(ind_data.get("Objetivo"))
    descripcion = safe(
        ind_data.get("descripcion", ind_data.get("Descripcion", ind_data.get("Descripción del indicador", "")))
    )
    meta_val = fmt_meta_from_dict(ind_data)
    ejec_val = fmt_ejec_from_dict(ind_data)
    cump_raw = ind_data.get("cumplimiento_pct", 0)
    cump = float(cump_raw) if pd.notna(cump_raw) else 0.0
    nivel = safe(ind_data.get("Nivel de cumplimiento"))
    responsable = safe(
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
    periodicidad = safe(ind_data.get("Periodicidad", ind_data.get("Frecuencia", "")))
    nivel_col = nivel_color(nivel)
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
                ("BACKGROUND", (0, 0), (0, 0), PRIMARIO),
                ("BACKGROUND", (1, 0), (1, 0), FONDO),
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
                ("BACKGROUND", (0, 0), (-1, -1), FONDO),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDE),
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
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDE, spaceAfter=6))

    # ── GRÁFICO HISTÓRICO ─────────────────────────────────────────────────────
    if not hist.empty:
        story.append(Paragraph("Evolución Histórica", st_section))
        img_buf = chart_to_png(hist)
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
            HRFlowable(width="100%", thickness=0.5, color=BORDE, spaceAfter=6)
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
                ("BACKGROUND", (0, 0), (0, -1), FONDO),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDE),
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
            h
            .sort_values("Periodo")
            .tail(10)
            .reset_index(drop=True)
        )
        if "Meta" in seg.columns:
            seg["Meta"] = seg.apply(
                lambda r: fmt_valor_signo(
                    r.get("Meta"),
                    r.get("Meta_Signo") or r.get("Meta s") or "%",
                    r.get("Decimales_Meta") or 0,
                ),
                axis=1,
            )
        if "Ejecucion" in seg.columns:
            seg["Ejecucion"] = seg.apply(
                lambda r: fmt_valor_signo(
                    r.get("Ejecucion"),
                    r.get("Ejecucion_s") or r.get("EjecS") or r.get("Ejecucion_Signo") or "%",
                    r.get("Decimales_Ejecucion") or 0,
                ),
                axis=1,
            )
        seg = seg[[c for c in seg_cols if c in seg.columns]].rename(columns={"cumplimiento_pct": "% Cumpl."})
        if "% Cumpl." in seg.columns:
            seg["% Cumpl."] = pd.to_numeric(seg["% Cumpl."], errors="coerce").round(1)

        hdr_row = [Paragraph(f"<b>{c}</b>", st_label) for c in seg.columns]
        seg_table_data = [hdr_row] + [
            [Paragraph(safe(v), st_body) for v in row] for _, row in seg.iterrows()
        ]
        seg_tbl = Table(seg_table_data, colWidths=[None] * len(seg.columns))
        seg_style = [
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARIO),
            ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDE),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]
        seg_tbl.setStyle(TableStyle(seg_style))
        story.append(seg_tbl)
        story.append(Spacer(1, 10))

    # ── CIERRE ────────────────────────────────────────────────────────────────
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
