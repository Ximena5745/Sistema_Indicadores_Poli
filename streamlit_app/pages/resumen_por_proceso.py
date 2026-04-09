import unicodedata

import pandas as pd
import streamlit as st
from streamlit_app.components import KPIRow
from streamlit_app.services.data_service import DataService


def _normalize_text(value):
    if value is None:
        return ""
    text = str(value).strip()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch)).upper()


def _indicator_modal(ind_name="Indicador ejemplo"):
    if st.button(f"Abrir detalle: {ind_name}", key=f"modal_btn_{ind_name}"):
        with st.modal("Detalle indicador"):
            st.header(ind_name)
            tabs = st.tabs(["IRIP", "DAD", "Coherencia", "Eficiencia OM"])
            with tabs[0]:
                st.write("Contenido IRIP (mock)")
            with tabs[1]:
                st.write("Contenido DAD (mock)")
            with tabs[2]:
                st.write("Contenido Coherencia (mock)")
            with tabs[3]:
                st.write("Contenido Eficiencia OM (mock)")


def _render_html_bars(counts, labels, color_map=None, max_value=None):
    html = ["<div class='html-bar-chart'>"]
    color_map = color_map or {}
    if max_value is None:
        max_value = max(counts.values()) if counts else 1
    for label in labels:
        value = int(counts.get(label, 0))
        width = int(max(3, min(100, (value / max_value * 100) if max_value else 5)))
        color = color_map.get(label, "#7d8be3")
        html.append(
            f"<div class='html-bar-item'>"
            f"<div class='bar-axis'>"
            f"<div class='bar-label'>{label}</div>"
            f"<div class='bar-track'><div class='bar-fill' style='width:{width}%;background:{color};'></div></div>"
            f"</div>"
            f"<div class='bar-value'>{value}</div>"
            f"</div>"
        )
    html.append("</div>")
    return "".join(html)


def render():
    st.title("Resumen por procesos")
    st.write("Seleccione un proceso para ver detalle. Esta vista contiene 6 tabs por proceso.")

    ds = DataService()
    df = ds.get_tracking_data()
    map_df = ds.get_process_map()

    if map_df.empty:
        st.warning(
            "No se encontró la fuente de mapeo `Subproceso-Proceso-Area.xlsx` en `data/raw`. "
            "Revisa que el archivo exista y contenga la hoja 'Proceso'."
        )

    elif df.empty:
        st.warning(
            "No se encontró la fuente de datos `Tracking Mensual` en `data/output/Seguimiento_Reporte.xlsx`. "
            "Revisa que el archivo exista y la hoja `Tracking Mensual` esté disponible."
        )

    map_df = map_df.rename(columns={
        c: c.strip() for c in map_df.columns
    })
    if "Unidad" not in map_df.columns or "Proceso" not in map_df.columns or "Subproceso" not in map_df.columns:
        st.error("La hoja 'Proceso' del archivo de mapeo no contiene las columnas esperadas: Unidad, Proceso, Subproceso.")
        return

    map_df = map_df.dropna(subset=["Proceso"]).reset_index(drop=True)
    map_df["Tipo de proceso"] = map_df.get("Tipo de proceso", "").astype(str)

    tipo_opts = ["Todos"] + sorted(map_df["Tipo de proceso"].dropna().unique().tolist())
    unidad_opts = ["Todas"]
    proceso_opts = ["Todos"]
    subproceso_opts = ["Todos"]

    if tipo_opts:
        col_tipo, col_unidad, col_proceso, col_subproceso = st.columns([1, 1, 1, 1])
        with col_tipo:
            tipo_proceso = st.selectbox("Tipo de proceso", tipo_opts, key="resumen_tipo_proceso")
        if tipo_proceso != "Todos":
            unidad_opts += sorted(map_df.loc[map_df["Tipo de proceso"] == tipo_proceso, "Unidad"].dropna().unique().tolist())
        else:
            unidad_opts += sorted(map_df["Unidad"].dropna().unique().tolist())
        with col_unidad:
            unidad = st.selectbox("Unidad", unidad_opts, key="resumen_unidad")

        unidad_filter = map_df
        if unidad != "Todas":
            unidad_filter = unidad_filter[unidad_filter["Unidad"] == unidad]

        proceso_opts += sorted(unidad_filter["Proceso"].dropna().unique().tolist())
        with col_proceso:
            proceso = st.selectbox("Proceso", proceso_opts, key="resumen_proceso")

        subproceso_filter = unidad_filter
        if proceso != "Todos":
            subproceso_filter = subproceso_filter[subproceso_filter["Proceso"] == proceso]
        subproceso_opts += sorted(subproceso_filter["Subproceso"].dropna().unique().tolist())
        with col_subproceso:
            subproceso = st.selectbox("Subproceso", subproceso_opts, key="resumen_subproceso")
    else:
        tipo_proceso = "Todos"
        unidad = "Todas"
        proceso = "Todos"
        subproceso = "Todos"

    if df.empty:
        proc_df = pd.DataFrame()
    else:
        proc_df = df.copy()
        if "Proceso" in map_df.columns:
            proc_df = proc_df.merge(
                map_df[["Unidad", "Proceso", "Subproceso", "Tipo de proceso"]],
                on="Proceso",
                how="left",
            )

        if tipo_proceso != "Todos" and "Tipo de proceso" in proc_df.columns:
            proc_df = proc_df[proc_df["Tipo de proceso"] == tipo_proceso]
        if unidad != "Todas" and "Unidad" in proc_df.columns:
            proc_df = proc_df[proc_df["Unidad"] == unidad]
        if proceso != "Todos":
            proc_df = proc_df[proc_df["Proceso"] == proceso]
        if subproceso != "Todos" and "Subproceso" in proc_df.columns:
            proc_df = proc_df[proc_df["Subproceso"] == subproceso]

    selected_process = (
        proceso
        if proceso != "Todos"
        else subproceso
        if subproceso != "Todos"
        else unidad
        if unidad != "Todas"
        else "Todos los procesos"
    )

    tabs = st.tabs(["📊 Indicadores", "📋 Resumen", "✅ Calidad", "🔍 Auditoría", "💡 Propuestos", "🤖 Análisis IA"])

    with tabs[0]:
        st.markdown(f"### Indicadores — {selected_process}")
        if proc_df.empty:
            st.info("No hay datos disponibles para el proceso seleccionado.")
        else:
            total = len(proc_df)
            reportado = int((proc_df["Estado"] == "Reportado").sum()) if "Estado" in proc_df.columns else 0
            pendiente = int((proc_df["Estado"] == "Pendiente").sum()) if "Estado" in proc_df.columns else 0
            no_aplica = int((proc_df["Estado"] == "No aplica").sum()) if "Estado" in proc_df.columns else 0

            cols = st.columns([1, 1, 1, 1])
            cols[0].metric("Total indicadores", total)
            cols[1].metric("Reportado", reportado)
            cols[2].metric("Pendiente", pendiente, delta=f"{round(pendiente/total*100,1)}%" if total else None)
            cols[3].metric("No aplica", no_aplica)

            st.markdown("#### Indicadores clave")
            breakdown = proc_df["Estado"].value_counts().to_dict() if "Estado" in proc_df.columns else {}
            st.markdown(
                _render_html_bars(
                    breakdown,
                    ["Reportado", "Pendiente", "No aplica"],
                    {
                        "Reportado": "#0f3a6d",
                        "Pendiente": "#ffab00",
                        "No aplica": "#9e9e9e",
                    },
                    max(breakdown.values()) if breakdown else 1,
                ),
                unsafe_allow_html=True,
            )

            st.markdown("#### Distribución por periodicidad")
            periodo_counts = proc_df["Periodicidad"].value_counts().to_dict() if "Periodicidad" in proc_df.columns else {}
            st.markdown(
                _render_html_bars(
                    periodo_counts,
                    sorted(periodo_counts.keys()),
                    {
                        "Anual": "#0f3a6d",
                        "Bimestral": "#00b8d4",
                        "Mensual": "#1d4a86",
                        "Semestral": "#1d9c60",
                        "Trimestral": "#ffab00",
                    },
                    max(periodo_counts.values()) if periodo_counts else 1,
                ),
                unsafe_allow_html=True,
            )

    with tabs[1]:
        st.markdown(f"#### Resumen — {selected_process}")
        st.write("Resumen agregado de indicadores filtrados por proceso. Aquí se prioriza el análisis por estado y periodicidad.")
        if proc_df.empty:
            st.info("No hay datos disponibles para el proceso seleccionado.")
        else:
            periodo_counts = proc_df["Periodicidad"].value_counts().to_dict() if "Periodicidad" in proc_df.columns else {}
            st.write("**Periodicidad dentro del proceso seleccionado**")
            st.markdown(
                _render_html_bars(
                    periodo_counts,
                    sorted(periodo_counts.keys()),
                    {
                        "Anual": "#0f3a6d",
                        "Bimestral": "#00b8d4",
                        "Mensual": "#1d4a86",
                        "Semestral": "#1d9c60",
                        "Trimestral": "#ffab00",
                    },
                    max(periodo_counts.values()) if periodo_counts else 1,
                ),
                unsafe_allow_html=True,
            )

            status_summary = (
                proc_df["Estado"]
                .value_counts(dropna=True)
                .rename_axis("Estado")
                .reset_index(name="Indicadores")
            ) if "Estado" in proc_df.columns else pd.DataFrame()
            if not status_summary.empty:
                st.markdown("**Indicadores por estado**")
                st.table(status_summary)

            breakdown_df = (
                proc_df[["Periodicidad", "Estado"]]
                .dropna(subset=["Periodicidad", "Estado"])
                .groupby(["Periodicidad", "Estado"], as_index=False)
                .size()
                .rename(columns={"size": "Indicadores"})
            )
            if not breakdown_df.empty:
                st.markdown("**Indicadores por periodicidad y estado**")
                st.dataframe(breakdown_df, use_container_width=True)

            top_processes = (
                proc_df["Proceso"]
                .value_counts()
                .rename_axis("Proceso")
                .reset_index(name="Indicadores")
                .head(8)
            )
            if not top_processes.empty:
                st.markdown("**Procesos con más indicadores en la selección**")
                st.table(top_processes)

    with tabs[2]:
        st.markdown(f"### Calidad — {selected_process}")
        st.write("Métrica de calidad basada en el estado de reporte para el proceso seleccionado.")

    with tabs[3]:
        st.markdown(f"### Auditoría — {selected_process}")
        st.write("Los datos están filtrados por proceso y listos para análisis de auditoría.")

    with tabs[4]:
        st.markdown(f"### Propuestos — {selected_process}")
        st.write("Indicadores propuestos y notas relacionadas con el proceso seleccionado.")

    with tabs[5]:
        st.markdown(f"### Análisis IA — {selected_process}")
        st.write("Análisis IA (mock) para el proceso seleccionado.")
