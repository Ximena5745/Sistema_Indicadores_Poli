import pandas as pd
import plotly.express as px
import streamlit as st


def _sample_om():
    return pd.DataFrame(
        [
            {"OM": "OM-101", "Indicador": "Retención estudiantil", "Responsable": "J. Pérez", "Estado": "Abierta", "Días": 14},
            {"OM": "OM-102", "Indicador": "Satisfacción docente", "Responsable": "M. García", "Estado": "En proceso", "Días": 9},
            {"OM": "OM-103", "Indicador": "Calidad académica", "Responsable": "L. Torres", "Estado": "Cerrada", "Días": 31},
            {"OM": "OM-104", "Indicador": "Digitalización", "Responsable": "C. Rojas", "Estado": "Abierta", "Días": 21},
        ]
    )


def render():
    st.title("Gestión de OM")
    st.markdown("Panel de seguimiento de Órdenes de Mejora con responsables, plazos y prioridades.")

    df = _sample_om()
    counts = df["Estado"].value_counts().to_dict()
    fig = px.bar(
        x=list(counts.keys()),
        y=list(counts.values()),
        color=list(counts.keys()),
        color_discrete_map={"Abierta": "#ffab00", "En proceso": "#00b8d4", "Cerrada": "#00c853"},
        labels={"x": "Estado", "y": "Cantidad"},
        title="Estado de OM",
    )
    fig.update_layout(template="plotly_white", showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("### Órdenes de Mejora activas")
    st.dataframe(df)
