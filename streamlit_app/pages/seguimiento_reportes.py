import pandas as pd
import plotly.express as px
import streamlit as st


def _sample_tracking():
    return pd.DataFrame(
        [
            {"ID": "REP-001", "Reporte": "Reportes mensuales", "Estado": "Reportado", "Proceso": "Finanzas"},
            {"ID": "REP-002", "Reporte": "Seguimiento PDI", "Estado": "Pendiente", "Proceso": "Académico"},
            {"ID": "REP-003", "Reporte": "Consolidado QA", "Estado": "No aplica", "Proceso": "Operaciones"},
            {"ID": "REP-004", "Reporte": "Informe semestre", "Estado": "Reportado", "Proceso": "Talento Humano"},
        ]
    )


def render():
    st.title("Seguimiento de reportes")
    st.markdown("Panel ejecutivo de consolidación y avance de reportes de seguimiento.")

    stats = {
        "Reportado": 68,
        "Pendiente": 24,
        "No aplica": 8,
    }
    fig = px.pie(
        names=list(stats.keys()),
        values=list(stats.values()),
        color=list(stats.keys()),
        color_discrete_map={"Reportado": "#1FB2DE", "Pendiente": "#EC0677", "No aplica": "#9E9E9E"},
        title="Estado de reportes",
    )
    fig.update_layout(template="plotly_white", legend_title_text="Estado")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("### Lista de seguimiento")
    st.dataframe(_sample_tracking())
