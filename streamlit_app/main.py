import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.card import card
from streamlit_extras.badge import badge
from streamlit_extras.grid import grid

st.set_page_config(page_title="Sistema de Indicadores", layout="wide")

CSS = """
<style>
[data-testid="stSidebar"] { background-color: #1A3A5C; }
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] label { color: #B3D9FF !important; font-weight: 500; }
.stApp { background-color: #F4F6F9; }
h1 { color: #1A3A5C; }
h2, h3 { color: #1565C0; }
.card { border-radius: 10px; padding: 20px; margin: 10px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

def main():
    with st.sidebar:
        st.markdown("---")
        if st.button("Actualizar datos", use_container_width=True):
            st.cache_data.clear()
            st.success("Datos actualizados.")
        st.markdown("---")

        # Sidebar navigation
        section = st.radio("Navegación", ["Resumen estratégico", "Resumen por procesos", "Seguimiento operativo"], index=0)

    # Topbar
    st.markdown("<div style='display: flex; justify-content: space-between; align-items: center;'>"
                "<h1>Inicio estratégico</h1>"
                "<div>"
                "<span>Dic 2025 · 387 indicadores · Generado 07/04/2026</span>"
                "<button style='margin-left: 10px;'>Actualizar datos</button>"
                "</div>"
                "</div>", unsafe_allow_html=True)

    # Main content based on selected section
    if section == "Resumen estratégico":
        tab = st.tabs(["CMI Estratégico", "PDI / Acreditación", "Plan de Mejoramiento"])
        with tab[0]:
            card("CMI Estratégico", "Indicadores clave de desempeño", "#04122e")
            switch_page("pages/cmi_estrategico.py")
        with tab[1]:
            card("PDI / Acreditación", "Progreso de acreditación institucional", "#1a2744")
            switch_page("pages/pdi_acreditacion.py")
        with tab[2]:
            card("Plan de Mejoramiento", "Acciones estratégicas", "#325f99")
            switch_page("pages/plan_mejoramiento.py")

    elif section == "Resumen por procesos":
        tab = st.tabs(["Mapa de procesos"])
        with tab[0]:
            grid([["Mapa de procesos", "Análisis detallado"]])
            switch_page("pages/resumen_por_proceso.py")

    elif section == "Seguimiento operativo":
        tab = st.tabs(["Seguimiento reportes", "Gestión de OM", "Registro OM"])
        with tab[0]:
            badge("Seguimiento reportes", "#ff7043")
            switch_page("pages/5_Seguimiento_de_reportes.py")
        with tab[1]:
            badge("Gestión de OM", "#00b8d4")
            switch_page("pages/2_Gestion_OM.py")
        with tab[2]:
            badge("Registro OM", "#00c853")
            switch_page("pages/4_Registro_OM.py")

if __name__ == "__main__":
    main()
