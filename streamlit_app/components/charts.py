import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import sys
from pathlib import Path

# Agregar raíz del proyecto al path para importaciones
_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

try:
    from ..services.data_service import DataService
    from ..styles.design_system import COLORS, get_vivid_palette
    from core.config import COLOR_CATEGORIA
    from utils.formatting import formatear_meta_ejecucion_df
except ImportError:
    try:
        from streamlit_app.services.data_service import DataService
        from streamlit_app.styles.design_system import COLORS, get_vivid_palette
        from core.config import COLOR_CATEGORIA
        from utils.formatting import formatear_meta_ejecucion_df
    except ImportError:
        from services.data_service import DataService
        from styles.design_system import COLORS, get_vivid_palette
        from core.config import COLOR_CATEGORIA
        from utils.formatting import formatear_meta_ejecucion_df

# Alias para compatibilidad interna — fuente única en core/config.py
COLOR_CAT = COLOR_CATEGORIA


class Charts:
    def __init__(self, service: DataService = None):
        self.service = service or DataService()

    def draw_performance_chart(self):
        df = self.service.get_timeseries()
        if df.empty:
            st.info("No hay datos de desempeño disponibles.")
            return

        fig = go.Figure()
        primary = COLORS.get("primary")
        vivid = get_vivid_palette()[0]

        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df["value"],
                name="Realizado",
                marker_color=primary,
                marker_line_color=primary,
                marker_line_width=1,
                hovertemplate="%{x|%b %Y}<br>Desempeño: %{y}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["value"],
                name="Tendencia",
                mode="lines+markers",
                line=dict(color=vivid, width=4),
                marker=dict(size=8),
                hovertemplate="%{x|%b %Y}<br>Tendencia: %{y}<extra></extra>",
            )
        )
        fig.update_layout(
            title="Curva de desempeño institucional",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=40, b=20),
            xaxis=dict(showgrid=False, tickformat="%b %Y", zeroline=False),
            yaxis=dict(showgrid=True, gridcolor="#e6edf5", zeroline=False),
        )
        st.plotly_chart(fig, use_container_width=True)

    def draw_semaforo(self):
        df = self.service.get_semaforo()
        max_val = df["valor"].max() if not df.empty else 1
        color_map = {
            "Peligro": COLORS.get("danger"),
            "Alerta": COLORS.get("warning"),
            "Cumplimiento": COLORS.get("success"),
            "Sobrecumplimiento": COLORS.get("sobrecumplimiento"),
        }
        html_rows = [
            "<div class='html-bar-chart'>",
            "<div style='font-weight:700;margin-bottom:14px;color:#0f2137;'>Semáforo global</div>",
        ]
        for _, row in df.iterrows():
            estado = str(row["estado"])
            valor = int(row["valor"])
            width = min(max(valor / max_val * 100, 2), 100)
            color = color_map.get(estado, "#7d8be3")
            html_rows.append(
                f"<div class='html-bar-item'>"
                f"<div class='bar-axis'>"
                f"<div class='bar-label'>{estado}</div>"
                f"<div class='bar-track'><div class='bar-fill' style='width:{width}%;background:{color};'></div></div>"
                f"</div>"
                f"<div class='bar-value'>{valor}</div>"
                f"</div>"
            )
        html_rows.append("</div>")
        st.markdown("".join(html_rows), unsafe_allow_html=True)


def deterministic_timeseries():
    return DataService().get_timeseries()


def draw_performance_chart():
    return Charts().draw_performance_chart()


def draw_semaforo():
    return Charts().draw_semaforo()


def _ensure_fecha_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Asegura que el DataFrame tenga una columna `Fecha` de tipo datetime.
    """
    if df is None or df.empty:
        return df

    df = df.copy()
    date_col = None
    for c in df.columns:
        if c.lower() == "fecha" or "fecha" in c.lower():
            date_col = c
            break
    if date_col is None and "Periodo" in df.columns:
        date_col = "Periodo"

    if date_col is not None:
        df["Fecha"] = pd.to_datetime(df[date_col], errors="coerce")
    else:
        df["Fecha"] = pd.NaT
    return df


_MESES_ES = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
             7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}


def _mes_es(fecha) -> str:
    """Convierte fecha a 'Mes YYYY' en español."""
    try:
        dt = pd.to_datetime(fecha, errors="coerce")
        if pd.isna(dt):
            return str(fecha)
        return f"{_MESES_ES[dt.month]} {dt.year}"
    except Exception:
        return str(fecha)


def grafico_historico_indicador(df_ind: pd.DataFrame, titulo: str = "") -> go.Figure:
    """
    Gráfico de línea con zonas de color para el histórico de un indicador.
    df_ind debe tener: Cumplimiento_norm, Categoria, Periodo, Fecha.
    """
    if df_ind.empty:
        fig = go.Figure()
        fig.update_layout(title="Sin datos disponibles")
        return fig

    df_ind = _ensure_fecha_column(df_ind)
    df_ind = df_ind.sort_values("Fecha").copy()
    cum_pct = (df_ind.get("Cumplimiento_norm", pd.Series(dtype=float)) * 100).round(1)
    y_max = max(130, float(cum_pct.max()) + 15) if not cum_pct.empty else 130

    colores_pts = df_ind.get("Categoria", pd.Series()).map(COLOR_CAT).fillna("#9E9E9E")

    fig = go.Figure()

    # Zonas de fondo
    fig.add_hrect(
        y0=0, y1=80, fillcolor="#FFCDD2", opacity=0.45, line_width=0,
        annotation_text="Peligro 0–80%", annotation_position="top left",
        annotation_font_size=10,
    )
    fig.add_hrect(
        y0=80, y1=100, fillcolor="#FFF9C4", opacity=0.45, line_width=0,
        annotation_text="Alerta 80–100%", annotation_position="top left",
        annotation_font_size=10,
    )
    fig.add_hrect(
        y0=100, y1=105, fillcolor="#E8F5E9", opacity=0.50, line_width=0,
        annotation_text="Cumplimiento 100–105%", annotation_position="top left",
        annotation_font_size=10,
    )
    fig.add_hrect(
        y0=105, y1=y_max, fillcolor="#D0E4FF", opacity=0.45, line_width=0,
        annotation_text="Sobrecumplimiento > 105%", annotation_position="top left",
        annotation_font_size=10,
    )

    # Línea de datos
    x_vals = df_ind["Fecha"] if "Fecha" in df_ind.columns else df_ind.get("Periodo")
    mes_labels = (
        df_ind["Fecha"].apply(_mes_es) if "Fecha" in df_ind.columns
        else df_ind.get("Periodo", pd.Series([""] * len(df_ind)))
    )
    custom = list(zip(mes_labels, df_ind.get("Categoria", pd.Series()))) if "Categoria" in df_ind.columns else None

    fig.add_trace(go.Scatter(
        x=x_vals,
        y=cum_pct,
        mode="lines+markers+text",
        line=dict(color="#455A64", width=2),
        marker=dict(
            size=12,
            color=colores_pts,
            line=dict(width=2, color="white"),
        ),
        text=cum_pct.astype(str) + "%",
        textposition="top center",
        textfont=dict(size=9),
        hovertemplate=(
            "<b>Mes:</b> %{customdata[0]}<br>"
            "<b>Cumplimiento:</b> %{y:.1f}%<br>"
            "<b>Estado:</b> %{customdata[1]}<extra></extra>"
        ) if custom is not None else "%{y:.1f}%<extra></extra>",
        customdata=custom,
        showlegend=False,
    ))

    # Líneas de referencia
    fig.add_hline(y=100, line_dash="dash", line_color="#2E7D32", line_width=1.5)
    fig.add_hline(y=80,  line_dash="dot",  line_color="#C62828", line_width=1.5)

    # Leyenda de colores
    for cat, color in COLOR_CAT.items():
        if cat == "Sin dato":
            continue
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(size=10, color=color),
            name=cat, showlegend=True,
        ))

    fig.update_layout(
        title=titulo,
        yaxis=dict(title="Cumplimiento (%)", ticksuffix="%", range=[0, y_max]),
        xaxis_title="",
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", y=-0.2),
        margin=dict(t=50, b=60),
    )
    return fig


def tabla_historica_indicador(df_ind: pd.DataFrame) -> pd.DataFrame:
    """Prepara DataFrame histórico con columnas formateadas para mostrar."""
    df_work = df_ind.copy()

    # Excluir filas sin cumplimiento real (Categoria "Sin dato")
    if "Categoria" in df_work.columns:
        df_work = df_work[df_work["Categoria"] != "Sin dato"]
    if df_work.empty:
        return df_work

    # Generar columna Mes en español desde Fecha
    if "Fecha" in df_work.columns:
        df_work["Mes"] = df_work["Fecha"].apply(_mes_es)
    elif "Periodo" in df_work.columns:
        df_work["Mes"] = df_work["Periodo"].astype(str)

    # Renombrar Anio -> Año
    if "Anio" in df_work.columns:
        df_work.rename(columns={"Anio": "Año"}, inplace=True)

    # Detectar signo para Meta y Ejecución
    _signo_meta = df_work["Meta_Signo"].iloc[0] if "Meta_Signo" in df_work.columns else ""
    _signo_ejec = df_work["Ejecucion_Signo"].iloc[0] if "Ejecucion_Signo" in df_work.columns else ""
    if pd.isna(_signo_meta): _signo_meta = ""
    if pd.isna(_signo_ejec): _signo_ejec = ""

    cols = ["Mes", "Año", "Meta", "Ejecucion", "Cumplimiento_norm", "Categoria"]
    cols_disp = [c for c in cols if c in df_work.columns]
    df_t = df_work[cols_disp].copy()
    if "Año" in df_t.columns:
        df_t = df_t.sort_values("Año")

    if "Meta" in df_t.columns:
        df_t["Meta_Signo"] = _signo_meta
    if "Ejecucion" in df_t.columns:
        df_t["Ejecucion_Signo"] = _signo_ejec
    df_t = formatear_meta_ejecucion_df(df_t, meta_col="Meta", ejec_col="Ejecucion")

    if "Cumplimiento_norm" in df_t.columns:
        def _fmt_cumpl(v):
            try:
                return f"{round(float(v) * 100, 1)}%" if pd.notna(v) else ""
            except (TypeError, ValueError):
                return ""
        df_t["Cumplimiento_norm"] = df_t["Cumplimiento_norm"].apply(_fmt_cumpl)
        df_t.rename(columns={"Cumplimiento_norm": "Cumplimiento%"}, inplace=True)
    return df_t
