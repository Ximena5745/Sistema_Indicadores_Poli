import streamlit as st
import pandas as pd
import io

from streamlit_app.utils.cmi_helpers import linea_color


def render_tab_listado(df):
    st.markdown("### Listado Completo de Indicadores")
    if df.empty:
        st.info("No hay datos para mostrar.")
        return

    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        search = st.text_input("Búsqueda Rápida", key="tab_list_search")
    with col2:
        estados_disp = ["Todos"] + df["Nivel de cumplimiento"].dropna().unique().tolist() if "Nivel de cumplimiento" in df.columns else ["Todos"]
        sel_estado = st.selectbox("Estado", estados_disp, key="tab_list_estado")
    with col3:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Indicadores", index=False)

        st.download_button(
            label="📥 Exportar a Excel",
            data=buffer.getvalue(),
            file_name="indicadores_cmi.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    df_filtrado = df.copy()
    if search:
        df_filtrado = df_filtrado[df_filtrado["Indicador"].astype(str).str.contains(search, case=False, na=False)]
    if sel_estado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Nivel de cumplimiento"] == sel_estado]

    if "cumplimiento_pct" in df_filtrado.columns:
        df_filtrado["cumplimiento_pct"] = pd.to_numeric(df_filtrado["cumplimiento_pct"], errors="coerce")
        df_filtrado = df_filtrado.sort_values("cumplimiento_pct", ascending=False)

    cols_mostrar = ["Id", "Indicador", "Linea", "Objetivo", "Meta", "Ejecucion", "cumplimiento_pct", "Nivel de cumplimiento"]
    df_vista = df_filtrado[[c for c in cols_mostrar if c in df_filtrado.columns]].copy()
    df_vista["Meta"] = df_vista["Meta"].fillna("-")
    df_vista["Ejecucion"] = df_vista["Ejecucion"].fillna("-")
    df_vista["cumplimiento_pct"] = df_vista["cumplimiento_pct"].round(1)

    if df_vista.empty:
        st.warning("No hay indicadores que coincidan con los filtros seleccionados.")
        return

    st.markdown(
        "<div class='cmi-listado-intro'>Selecciona <strong>Ver ficha</strong> en cualquier fila para abrir la ficha técnica del indicador.</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='cmi-listado-table'>
          <div class='cmi-listado-row cmi-listado-header'>
            <div class='cmi-listado-cell cmi-listado-cell-sm'>ID</div>
            <div class='cmi-listado-cell cmi-listado-cell-xl'>Indicador</div>
            <div class='cmi-listado-cell'>Línea</div>
            <div class='cmi-listado-cell cmi-listado-cell-lg'>Objetivo</div>
            <div class='cmi-listado-cell cmi-listado-cell-sm'>Meta</div>
            <div class='cmi-listado-cell cmi-listado-cell-sm'>Ejecución</div>
            <div class='cmi-listado-cell cmi-listado-cell-sm'>Cumplimiento</div>
            <div class='cmi-listado-cell cmi-listado-cell-md'>Nivel</div>
            <div class='cmi-listado-cell cmi-listado-cell-action'>Acción</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    from streamlit_app.components.cmi_tabs.modal_ficha import render_modal_ficha

    for idx, row in df_vista.reset_index(drop=True).iterrows():
        indicador = str(row.get("Indicador", "") or "-")
        linea = str(row.get("Linea", "") or "-")
        objetivo = str(row.get("Objetivo", "") or "-")
        meta = str(row.get("Meta", "-") or "-")
        ejec = str(row.get("Ejecucion", "-") or "-")
        cumplimiento = row.get("cumplimiento_pct")
        cumplimiento_str = f"{cumplimiento:.1f}%" if pd.notna(cumplimiento) else "-"
        nivel = str(row.get("Nivel de cumplimiento", "-") or "-")

        badge_colors = {
            "Peligro": ("#B71C1C", "#FEE2E2"),
            "Alerta": ("#B45309", "#FEF3C7"),
            "Cumplimiento": ("#166534", "#DCFCE7"),
            "Sobrecumplimiento": ("#1D4ED8", "#DBEAFE"),
            "Pendiente de reporte": ("#475569", "#F1F5F9"),
        }
        text_color, bg_color = badge_colors.get(nivel, ("#334155", "#F8FAFC"))
        nivel_badge = (
            f"<span class='cmi-badge' style='background:{bg_color};color:{text_color};'>"
            f"{nivel}</span>"
        )

        linea_dot = linea_color(linea)
        linea_html = (
            f"<div class='cmi-linea-pill' style='border-color:{linea_dot};'>"
            f"<span class='cmi-linea-dot' style='background:{linea_dot};'></span>{linea}</div>"
        )

        row_container = st.container()
        with row_container:
            cols = st.columns([0.7, 4.5, 2.2, 3.5, 1.1, 1.1, 1.5, 2.0, 1.6])
            cols[0].markdown(f"<div class='cmi-listado-cell'>{row.get('Id', '')}</div>", unsafe_allow_html=True)
            cols[1].markdown(f"<div class='cmi-listado-cell cmi-listado-indicador'>{indicador}</div>", unsafe_allow_html=True)
            cols[2].markdown(linea_html, unsafe_allow_html=True)
            cols[3].markdown(f"<div class='cmi-listado-cell cmi-listado-objetivo'>{objetivo}</div>", unsafe_allow_html=True)
            cols[4].markdown(f"<div class='cmi-listado-cell'>{meta}</div>", unsafe_allow_html=True)
            cols[5].markdown(f"<div class='cmi-listado-cell'>{ejec}</div>", unsafe_allow_html=True)
            cols[6].markdown(f"<div class='cmi-listado-cell'>{cumplimiento_str}</div>", unsafe_allow_html=True)
            cols[7].markdown(f"<div class='cmi-listado-cell'>{nivel_badge}</div>", unsafe_allow_html=True)
            button_key = f"ver_ficha_{idx}_{row.get('Id','')}_{abs(hash(indicador))}"
            if cols[8].button("Ver ficha", key=button_key, use_container_width=True):
                render_modal_ficha(row)

    st.markdown("<div style='margin-top:16px;color:#475569;font-size:0.9rem'>Desplázate para ver todos los indicadores.</div>", unsafe_allow_html=True)
