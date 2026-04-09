import streamlit as st

class Topbar:
    def __init__(self, title="Inicio estratégico", subtitle="Dic 2025 · 387 indicadores · Generado 07/04/2026"):
        self.title = title
        self.subtitle = subtitle

    def render(self):
        st.markdown(
            "<div class='topbar-card'>"
            "<div class='topbar-left'><div class='title'>{}</div><div class='muted'>{}</div></div>"
            "</div>".format(self.title, self.subtitle),
            unsafe_allow_html=True,
        )
        cols = st.columns([1.6, 1, 1, 0.8])
        with cols[0]:
            st.markdown("<div class='topbar-actions'>Filtros de vista</div>", unsafe_allow_html=True)
        with cols[1]:
            st.markdown("<div class='filter-caption'>Año</div>", unsafe_allow_html=True)
            year = st.selectbox("", [2026, 2025, 2024], index=0, key='topbar_year', label_visibility='collapsed')
        with cols[2]:
            st.markdown("<div class='filter-caption'>Mes</div>", unsafe_allow_html=True)
            month = st.selectbox("", ["Todos", "Ene", "Feb", "Mar", "Abr"], index=0, key='topbar_month', label_visibility='collapsed')
        with cols[3]:
            if st.button("Actualizar datos", key='topbar_refresh'):
                st.experimental_rerun()
        return dict(year=year, month=month)


def render_topbar(default_year=2026):
    return Topbar().render()
