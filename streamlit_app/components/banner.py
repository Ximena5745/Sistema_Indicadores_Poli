import streamlit as st

class Banner:
    def __init__(self, text=None):
        self.text = text or "**IA detectó:** 9 indicadores con riesgo alto (IRIP >70%) · 3 anomalías (z-score>3) · 7 metas fuera de rango"

    def render(self):
        container = st.container()
        with container:
            st.markdown(
                f"<div class='banner-card'><div class='banner-text'><strong>IA detectó:</strong> 9 indicadores con riesgo alto (IRIP >70%) · 3 anomalías (z-score&gt;3) · 7 metas fuera de rango</div><div><button class='banner-button'>Ver detalle IA ↗</button></div></div>",
                unsafe_allow_html=True,
            )
            # fallback CTA for Streamlit interactivity
            if st.button("Ver detalle IA ↗", key='banner_cta'):
                st.session_state.show_ia = True

def render_banner():
    return Banner().render()
