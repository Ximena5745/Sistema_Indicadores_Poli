from pathlib import Path

import pandas as pd
import streamlit as st

from components.charts import exportar_excel
from core.config import CACHE_TTL
from streamlit_app.utils.formatting import id_limpio


RUTA_SEGUIMIENTO = Path(__file__).resolve().parents[2] / "data" / "output" / "Seguimiento_Reporte.xlsx"


@st.cache_data(ttl=CACHE_TTL, show_spinner="Cargando Tracking Mensual...")
def _cargar_tracking() -> pd.DataFrame:
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
    st.title("Seguimiento de Reportes")
    st.caption("Vista operativa de reportes mensuales por estado, proceso y periodicidad.")

    df = _cargar_tracking()
    if df.empty:
        st.error("No se encontró la hoja Tracking Mensual en data/output/Seguimiento_Reporte.xlsx.")
        return

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    anios = sorted(pd.to_numeric(df.get("Año", pd.Series(dtype=float)), errors="coerce").dropna().astype(int).unique().tolist())
    with col_f1:
        anio_sel = st.selectbox("Año", options=["Todos"] + anios)

    meses = sorted(pd.to_numeric(df.get("Mes", pd.Series(dtype=float)), errors="coerce").dropna().astype(int).unique().tolist())
    with col_f2:
        mes_sel = st.selectbox("Mes", options=["Todos"] + meses)

    procesos = sorted(df["Proceso"].dropna().astype(str).unique().tolist()) if "Proceso" in df.columns else []
    with col_f3:
        proceso_sel = st.selectbox("Proceso", options=["Todos"] + procesos)

    estados = sorted(df["Estado"].dropna().astype(str).unique().tolist()) if "Estado" in df.columns else []
    with col_f4:
        estado_sel = st.selectbox("Estado", options=["Todos"] + estados)

    df_view = df.copy()
    if anio_sel != "Todos" and "Año" in df_view.columns:
        df_view = df_view[df_view["Año"] == anio_sel]
    if mes_sel != "Todos" and "Mes" in df_view.columns:
        df_view = df_view[df_view["Mes"] == mes_sel]
    if proceso_sel != "Todos" and "Proceso" in df_view.columns:
        df_view = df_view[df_view["Proceso"] == proceso_sel]
    if estado_sel != "Todos" and "Estado" in df_view.columns:
        df_view = df_view[df_view["Estado"] == estado_sel]

    total = len(df_view)
    reportado = int((df_view.get("Estado", pd.Series(dtype=str)) == "Reportado").sum())
    pendiente = int((df_view.get("Estado", pd.Series(dtype=str)) == "Pendiente").sum())
    no_aplica = int((df_view.get("Estado", pd.Series(dtype=str)) == "No aplica").sum())

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Registros", total)
    k2.metric("Reportados", reportado)
    k3.metric("Pendientes", pendiente)
    k4.metric("No aplica", no_aplica)

    st.dataframe(df_view, use_container_width=True, height=500)

    st.download_button(
        label="Descargar vista filtrada (Excel)",
        data=exportar_excel(df_view, nombre_hoja="Seguimiento"),
        file_name="seguimiento_reportes_filtrado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
