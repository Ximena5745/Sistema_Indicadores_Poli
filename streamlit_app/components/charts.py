import pandas as pd
import plotly.express as px
import streamlit as st
from ..services.data_service import DataService


class Charts:
    def __init__(self, service: DataService = None):
        self.service = service or DataService()

    def draw_performance_chart(self):
        df = self.service.get_timeseries()
        fig = px.bar(df, x="date", y="value", labels={"value": "Desempeño"}, title="Curva de desempeño institucional")
        st.plotly_chart(fig, use_container_width=True)

    def draw_semaforo(self):
        df = self.service.get_semaforo()
        fig = px.pie(df, names="estado", values="valor", color_discrete_map={"Peligro": "#ff3b30", "Alerta": "#ffab00", "Cumplimiento": "#00c853", "Sobrecumplimiento": "#00b8d4"}, title="Semáforo global")
        st.plotly_chart(fig, use_container_width=True)


def deterministic_timeseries():
    return DataService().get_timeseries()


def draw_performance_chart():
    return Charts().draw_performance_chart()


def draw_semaforo():
    return Charts().draw_semaforo()
