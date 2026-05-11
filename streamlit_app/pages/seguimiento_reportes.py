"""
Tracking and reporting monitoring for strategic indicators.

Refactored PHASE 2 WEEK 4: Extracted config and utility functions.
"""

from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from components.charts import exportar_excel
from streamlit_app.components.filter_panel import render_filter_panel
from core.config import CACHE_TTL
from streamlit_app.utils.formatting import id_limpio

# Import refactored utilities
from .seguimiento_config import MESES_OPCIONES, COLOR_ESTADO
from .seguimiento_utils import detectar_vencidos

# Module-level variables for backward compatibility with tests
RUTA_SEGUIMIENTO = Path(__file__).resolve().parents[2] / "data" / "output" / "Seguimiento_Reporte.xlsx"
VENTANA_MESES = {
    "mensual": 1,
    "bimestral": 2,
    "trimestral": 3,
    "semestral": 6,
    "anual": 12,
}


@st.cache_data(ttl=CACHE_TTL, show_spinner="Cargando Tracking Mensual...")
def _cargar_tracking() -> pd.DataFrame:
    """
    Load tracking data from Excel file.
    This function is kept here (instead of moved to utils) to support test monkeypatching.
    """
    if not RUTA_SEGUIMIENTO.exists():
        return pd.DataFrame()
    try:
        df = pd.read_excel(str(RUTA_SEGUIMIENTO), sheet_name="Tracking Mensual", engine="openpyxl")
    except Exception:
        return pd.DataFrame()

    df.columns = [str(c).strip() for c in df.columns]
    if "Id" in df.columns:
        df["Id"] = df["Id"].apply(id_limpio)
    if "Año" in df.columns:
        df["Año"] = pd.to_numeric(df["Año"], errors="coerce").astype("Int64")
    if "Mes" in df.columns:
        df["Mes"] = pd.to_numeric(df["Mes"], errors="coerce").astype("Int64")
    return df


def render():
    """Main render function for seguimiento de reportes page."""
    st.title("Seguimiento de Reportes")
    st.caption("Vista operativa de reportes mensuales por estado, proceso y periodicidad.")

    df = _cargar_tracking()
    if df.empty:
        st.error("No se encontró la hoja Tracking Mensual en data/output/Seguimiento_Reporte.xlsx.")
        return

    anios = sorted(
        pd.to_numeric(df.get("Año", pd.Series(dtype=float)), errors="coerce")
        .dropna().astype(int).unique().tolist()
    )
    meses_nums = sorted(
        pd.to_numeric(df.get("Mes", pd.Series(dtype=float)), errors="coerce")
        .dropna().astype(int).unique().tolist()
    )
    mes_names = [MESES_OPCIONES[m - 1] for m in meses_nums if 1 <= m <= 12]
    procesos = (
        sorted(df["Proceso"].dropna().astype(str).unique().tolist())
        if "Proceso" in df.columns else []
    )
    estados = (
        sorted(df["Estado"].dropna().astype(str).unique().tolist())
        if "Estado" in df.columns else []
    )

    default_year = 2025 if 2025 in anios else (anios[-1] if anios else "Todos")
    default_mes = "Diciembre" if "Diciembre" in mes_names else (mes_names[-1] if mes_names else "Todos")

    _filter_defs = [
        {
            "key": "anio", "label": "Año", "type": "segmented_control",
            "options": anios, "default": default_year, "include_all": True,
        },
        {
            "key": "mes", "label": "Mes", "type": "selectbox",
            "options": mes_names, "default": default_mes, "include_all": True,
        },
        {
            "key": "proceso", "label": "Proceso", "type": "selectbox",
            "options": procesos, "include_all": True,
        },
        {
            "key": "estado", "label": "Estado", "type": "selectbox",
            "options": estados, "include_all": True,
        },
    ]
    sels = render_filter_panel(_filter_defs, title="Filtros de reporte", key_prefix="sr", n_cols=4)
    anio_sel = sels["anio"]
    mes_sel = sels["mes"]
    proceso_sel = sels["proceso"]
    estado_sel = sels["estado"]

    df_view = df.copy()
    if anio_sel not in (None, "Todos") and "Año" in df_view.columns:
        df_view = df_view[df_view["Año"] == anio_sel]
    if mes_sel not in (None, "Todos") and "Mes" in df_view.columns:
        try:
            mes_num = MESES_OPCIONES.index(mes_sel) + 1
            df_view = df_view[df_view["Mes"] == mes_num]
        except Exception:
            pass
    if proceso_sel not in (None, "Todos") and "Proceso" in df_view.columns:
        df_view = df_view[df_view["Proceso"] == proceso_sel]
    if estado_sel not in (None, "Todos") and "Estado" in df_view.columns:
        df_view = df_view[df_view["Estado"] == estado_sel]

    # Display metrics
    total = len(df_view)
    reportado = int((df_view.get("Estado", pd.Series(dtype=str)) == "Reportado").sum())
    pendiente = int((df_view.get("Estado", pd.Series(dtype=str)) == "Pendiente").sum())
    no_aplica = int((df_view.get("Estado", pd.Series(dtype=str)) == "No aplica").sum())

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Registros", total)
    k2.metric("Reportados", reportado)
    k3.metric("Pendientes", pendiente)
    k4.metric("No aplica", no_aplica)

    # Alert section
    vencidos, por_vencer = detectar_vencidos(df)
    if not vencidos.empty or not por_vencer.empty:
        st.markdown("### ⚠️ Alertas de frecuencia de reporte")
        ac1, ac2 = st.columns(2)
        with ac1:
            if not vencidos.empty:
                st.error(f"**{len(vencidos)} indicadores vencidos** (sin reporte en su ventana)")
                _v_cols = [
                    c
                    for c in ["Id", "Indicador", "Proceso", "Periodicidad", "diff_meses"]
                    if c in vencidos.columns
                ]
                st.dataframe(
                    vencidos[_v_cols].rename(columns={"diff_meses": "Meses sin reporte"}).head(20),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.success("Sin indicadores vencidos detectados.")
        with ac2:
            if not por_vencer.empty:
                st.warning(f"**{len(por_vencer)} próximos a vencer** (dentro del 80 % de ventana)")
                _pv_cols = [
                    c
                    for c in ["Id", "Indicador", "Proceso", "Periodicidad", "diff_meses"]
                    if c in por_vencer.columns
                ]
                st.dataframe(
                    por_vencer[_pv_cols]
                    .rename(columns={"diff_meses": "Meses sin reporte"})
                    .head(20),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.success("Sin indicadores próximos a vencer.")

    # Chart: estado por proceso
    if "Proceso" in df_view.columns and "Estado" in df_view.columns:
        st.markdown("### Estado de reportes por proceso")
        df_proc = (
            df_view.groupby(["Proceso", "Estado"], dropna=False).size().reset_index(name="Cantidad")
        )
        fig_proc = px.bar(
            df_proc,
            x="Proceso",
            y="Cantidad",
            color="Estado",
            barmode="stack",
            title="Indicadores por proceso y estado de reporte",
            color_discrete_map=COLOR_ESTADO,
        )
        fig_proc.update_layout(
            xaxis_tickangle=-35,
            margin=dict(l=10, r=10, t=50, b=120),
            legend_title="Estado",
        )
        try:
            from components.renderers import render_echarts

            def _option_proc_estado(df_proc, color_map):
                procs = df_proc["Proceso"].astype(str).unique().tolist()
                estados = df_proc["Estado"].astype(str).unique().tolist()
                procs = sorted(procs)
                series = []
                for est in estados:
                    vals = []
                    for p in procs:
                        s = df_proc[(df_proc["Proceso"] == p) & (df_proc["Estado"] == est)]
                        vals.append(int(s["Cantidad"].sum()) if not s.empty else 0)
                    series.append(
                        {
                            "name": est,
                            "type": "bar",
                            "stack": "total",
                            "data": vals,
                            "itemStyle": {"color": color_map.get(est, "#888")},
                        }
                    )
                option = {
                    "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                    "legend": {"bottom": 0},
                    "xAxis": {"type": "category", "data": procs, "axisLabel": {"rotate": -35}},
                    "yAxis": {"type": "value"},
                    "series": series,
                    "grid": {"left": "10%", "right": "5%", "bottom": "20%"},
                }
                return {"option": option, "height": max(320, len(procs) * 28 + 80)}

            opt = _option_proc_estado(df_proc, COLOR_ESTADO)
            if opt and opt.get("option"):
                render_echarts(opt["option"], height=opt.get("height", 420))
            else:
                st.plotly_chart(fig_proc, use_container_width=True, key="sr_proc_estado")
        except Exception:
            st.plotly_chart(fig_proc, use_container_width=True, key="sr_proc_estado")

    st.markdown("### Detalle")
    st.dataframe(df_view, use_container_width=True, height=500)

    st.download_button(
        label="Descargar vista filtrada (Excel)",
        data=exportar_excel(df_view, nombre_hoja="Seguimiento"),
        file_name="seguimiento_reportes_filtrado.xlsx",
    )
