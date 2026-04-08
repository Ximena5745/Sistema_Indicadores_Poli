import streamlit as st
class KPIRow:
    def __init__(self, kpis=None):
        self.kpis = kpis or [
            ("Total indicadores", 387, "Kawak + API", "#04122e"),
            ("En peligro", 20, "+19 vs ant. · 5.2%", "#ff3b30"),
            ("En alerta", 24, "+21 vs ant. · 6.2%", "#ffab00"),
            ("Cumplimiento", 85, "+70 vs ant. · 22%", "#00c853"),
            ("Sobrecumplimiento", 115, "+108 vs ant. · 29.7%", "#00b8d4"),
        ]

    def render(self):
        cols = st.columns(len(self.kpis))
        for col, (title, value, sub, color) in zip(cols, self.kpis):
            with col:
                st.markdown(f"**{title}**")
                st.markdown(f"<div class='kpi-value' style='color:{color}'>{value}</div>", unsafe_allow_html=True)
                st.caption(sub)

def render_kpi_row(kpis=None):
    return KPIRow(kpis).render()
