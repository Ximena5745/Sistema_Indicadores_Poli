import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from ..services.data_service import DataService


class Charts:
    def __init__(self, service: DataService = None):
        self.service = service or DataService()

    def draw_performance_chart(self):
        df = self.service.get_timeseries()
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df["value"],
                name="Realizado",
                marker_color="#325f99",
                hovertemplate="%{x|%b %Y}<br>Desempeño: %{y}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["value"],
                name="Tendencia",
                mode="lines+markers",
                line=dict(color="#00b8d4", width=4),
                marker=dict(size=8),
                hovertemplate="%{x|%b %Y}<br>Tendencia: %{y}<extra></extra>",
            )
        )
        fig.update_layout(
            title="Curva de desempeño institucional",
            template="plotly_white",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=40, b=20),
            xaxis=dict(showgrid=False, tickformat="%b %Y"),
            yaxis=dict(showgrid=True, gridcolor="#eef2f7"),
        )
        st.plotly_chart(fig, use_container_width=True)

    def draw_semaforo(self):
        df = self.service.get_semaforo()
        fig = px.bar(
            df,
            x="valor",
            y="estado",
            orientation="h",
            color="estado",
            color_discrete_map={
                "Peligro": "#ff3b30",
                "Alerta": "#ffab00",
                "Cumplimiento": "#00c853",
                "Sobrecumplimiento": "#00b8d4",
            },
            labels={"valor": "Indicadores", "estado": "Estado"},
        )
        fig.update_layout(
            title="Semáforo global",
            template="plotly_white",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=40, b=20),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False),
            showlegend=False,
        )
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)


def deterministic_timeseries():
    return DataService().get_timeseries()


def draw_performance_chart():
    return Charts().draw_performance_chart()


def draw_semaforo():
    return Charts().draw_semaforo()
