import streamlit as st
class Banner:
    def __init__(self, text=None):
        self.text = text or "**IA detectó:** 9 indicadores con riesgo alto (IRIP >70%) · 3 anomalías (z-score>3) · 7 metas fuera de rango"

    def render(self):
        container = st.container()
        with container:
            c1, c2 = st.columns([8, 1])
            with c1:
                st.markdown(self.text)
            with c2:
                if st.button("Ver detalle IA ↗"):
                    st.session_state.show_ia = True

def render_banner():
    return Banner().render()
