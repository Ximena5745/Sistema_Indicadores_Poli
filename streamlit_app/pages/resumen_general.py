import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

from streamlit_app.services.data_service import DataService


def _sample_summary():
    return [
        ("Indicadores activos", 387, "Kawak + API", "info"),
        ("En peligro", 20, "+19 vs ant. · 5.2%", "danger"),
        ("En alerta", 24, "+21 vs ant. · 6.2%", "warning"),
        ("Cumplimiento", 85, "+70 vs ant. · 22%", "success"),
        ("Sobrecumplimiento", 115, "+108 vs ant. · 29.7%", "info"),
    ]


def _sample_table():
    return pd.DataFrame(
        [
            {"Indicador": "Cumplimiento financiero", "Proceso": "Finanzas", "Estado": "Cumplimiento", "Valor": "92%"},
            {"Indicador": "Tasa de retención", "Proceso": "Academia", "Estado": "Alerta", "Valor": "78%"},
            {"Indicador": "Calidad de datos", "Proceso": "TI", "Estado": "Pendiente", "Valor": "N/A"},
            {"Indicador": "Satisfacción docente", "Proceso": "Talento Humano", "Estado": "En peligro", "Valor": "61%"},
        ]
    )


def render():
    st.title("Resumen General")
    st.markdown("Una visión integral de cumplimiento, progreso y alertas de los indicadores institucionales.")

    st.markdown("---")
    cols = st.columns(5)
    for col, (title, value, subtitle, tone) in zip(cols, _sample_summary()):
        with col:
            st.markdown(
                f"<div class='kpi-card'><div class='label'>{title}</div><div class='value {tone}'>{value}</div><div class='sub'>{subtitle}</div></div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown("### Tendencia de cumplimiento por mes")
    df = DataService().get_timeseries()
    fig = px.area(df, x="date", y="value", title="Tendencia de cumplimiento", markers=True)
    fig.update_layout(template="plotly_white", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("### Indicadores destacados")
    st.dataframe(_sample_table())
