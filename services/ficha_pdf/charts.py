"""
services/ficha_pdf/charts.py
============================

Chart generation for PDF (kaleido-based PNG rendering).

Responsibility: Generate and render chart PNG from historical data.
"""

import io
from typing import Optional

import pandas as pd

from .utils import PRIMARIO


def chart_to_png(hist: pd.DataFrame) -> Optional[io.BytesIO]:
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

        # ── Ejecución (barras) ──────────────────────────────────────────────
        if "Ejecucion" in h.columns:
            ev = pd.to_numeric(h["Ejecucion"], errors="coerce")
            if ev.notna().sum() >= 1:
                fig.add_trace(go.Bar(
                    x=h["Periodo"], y=ev, name="Ejecución",
                    marker_color="#1A3A5C", opacity=0.85, yaxis="y1",
                ))

        # ── Meta (línea discontinua) ────────────────────────────────────────
        if "Meta" in h.columns:
            mv = pd.to_numeric(h["Meta"], errors="coerce")
            if mv.notna().sum() >= 1:
                fig.add_trace(go.Scatter(
                    x=h["Periodo"], y=mv, mode="lines+markers", name="Meta",
                    line=dict(color="#F59E0B", width=2, dash="dash"),
                    marker=dict(size=5, symbol="diamond"),
                    yaxis="y1",
                ))

        # ── % Cumplimiento (eje secundario) ─────────────────────────────────
        if "cumplimiento_pct" in h.columns:
            cv = pd.to_numeric(h["cumplimiento_pct"], errors="coerce")
            if cv.notna().sum() >= 1:
                fig.add_trace(go.Scatter(
                    x=h["Periodo"], y=cv, mode="lines+markers",
                    name="% Cumplimiento",
                    line=dict(color="#0EA5E9", width=2),
                    marker=dict(size=6),
                    yaxis="y2",
                ))
                # Anotación de variación en el último punto
                valid_idx = cv.dropna().index
                if len(valid_idx) >= 2:
                    last_i = valid_idx[-1]
                    prev_i = valid_idx[-2]
                    delta = float(cv[last_i]) - float(cv[prev_i])
                    delta_text = f"+{delta:.1f}pp" if delta >= 0 else f"{delta:.1f}pp"
                    arrow_color = "#16A034" if delta >= 0 else "#DC2626"
                    fig.add_annotation(
                        x=h.loc[last_i, "Periodo"],
                        y=float(cv[last_i]),
                        text=f"<b>{delta_text}</b>",
                        showarrow=True, arrowhead=2,
                        arrowcolor=arrow_color, arrowsize=1.2,
                        font=dict(size=9, color=arrow_color),
                        bgcolor="white", bordercolor=arrow_color,
                        borderwidth=1, borderpad=2,
                        yref="y2", ay=-28,
                    )

        # Fallback: solo cumplimiento
        if len(fig.data) == 0 and "cumplimiento_pct" in h.columns:
            cv = pd.to_numeric(h["cumplimiento_pct"], errors="coerce")
            if cv.notna().sum() >= 1:
                fig.add_trace(go.Scatter(
                    x=h["Periodo"], y=cv, mode="lines+markers",
                    name="Cumplimiento %",
                    line=dict(color="#1A3A5C", width=2),
                ))

        if len(fig.data) == 0:
            return None

        fig.update_layout(
            margin=dict(t=25, b=20, l=45, r=55),
            height=220,
            barmode="overlay",
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(size=9, family="Arial"),
            legend=dict(orientation="h", y=1.12, font=dict(size=8)),
            xaxis=dict(showgrid=False),
            yaxis=dict(title="Valor", showgrid=True, gridcolor="#F1F5F9", side="left"),
            yaxis2=dict(
                title="% Cumpl.", overlaying="y", side="right",
                showgrid=False, ticksuffix="%",
            ),
        )

        buf = io.BytesIO()
        fig.write_image(buf, format="png", width=720, height=220, scale=2)
        buf.seek(0)
        return buf
    except Exception:
        return None
