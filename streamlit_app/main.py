import streamlit as st
from streamlit_option_menu import option_menu

st.set_page_config(page_title="Sistema de Indicadores", layout="wide")

def main():
    # Configuración del sidebar
    with st.sidebar:
        st.title("Sistema de Indicadores")
        st.markdown("Politécnico Grancolombiano · v2.0 Estratégico")
        st.markdown("---")

        # Menú principal actualizado con solo 3 opciones
        menu = option_menu(
            menu_title="Navegación",
            options=["Inicio estratégico", "Resumen por procesos", "Seguimiento operativo"],
            icons=["house", "bar-chart", "clipboard-check"],
            menu_icon="cast",
            default_index=0,
        )

    # Lógica de navegación actualizada
    if menu == "Inicio estratégico":
        st.title("Inicio estratégico")
        st.write("Esta sección proporciona un resumen estratégico del sistema.")

    elif menu == "Resumen por procesos":
        st.title("Resumen por procesos")
        st.write("Esta sección proporciona un resumen por procesos.")

    elif menu == "Seguimiento operativo":
        st.title("Seguimiento operativo")
        tab1, tab2, tab3 = st.tabs([
            "Seguimiento reportes",
            "Gestión de OM",
            "Registro OM",
        ])

        # Seguimiento reportes
        with tab1:
            st.subheader("Seguimiento de reportes")
            st.write("Esta sección permite visualizar el estado de los reportes generados.")
            st.write("""
                - Reportes pendientes
                - Reportes en proceso
                - Reportes completados
            """)
            # Ejemplo de tabla
            data = {
                "Reporte": ["Reporte 1", "Reporte 2", "Reporte 3"],
                "Estado": ["Pendiente", "En proceso", "Completado"],
                "Fecha": ["2026-04-01", "2026-04-02", "2026-04-03"]
            }
            st.table(data)

        # Gestión de OM
        with tab2:
            st.subheader("Gestión de OM")
            st.write("Esta sección permite gestionar las órdenes de mejora (OM).")
            st.write("""
                - Crear nuevas OM
                - Actualizar estado de OM existentes
                - Consultar historial de OM
            """)
            # Ejemplo de formulario
            with st.form("form_gestion_om"):
                om_name = st.text_input("Nombre de la OM")
                om_status = st.selectbox("Estado", ["Pendiente", "En proceso", "Completado"])
                submitted = st.form_submit_button("Guardar")
                if submitted:
                    st.success(f"OM '{om_name}' guardada con estado '{om_status}'.")

        # Registro OM
        with tab3:
            st.subheader("Registro de OM")
            st.write("Esta sección permite registrar nuevas órdenes de mejora.")
            st.write("""
                - Ingresar detalles de la OM
                - Asignar responsables
                - Establecer fechas de seguimiento
            """)
            # Ejemplo de entrada de datos
            om_details = st.text_area("Detalles de la OM")
            om_responsible = st.text_input("Responsable")
            om_date = st.date_input("Fecha de seguimiento")
            if st.button("Registrar OM"):
                st.success("OM registrada exitosamente.")

if __name__ == "__main__":
    main()
