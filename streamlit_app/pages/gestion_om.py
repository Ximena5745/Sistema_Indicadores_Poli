from datetime import date

import pandas as pd
import streamlit as st

from components.charts import exportar_excel
from core.config import CACHE_TTL
from core.db_manager import guardar_registro_om, leer_registros_om
from services.data_loader import cargar_dataset


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _cargar_indicadores_riesgo() -> pd.DataFrame:
    df = cargar_dataset()
    if df.empty:
        return df

    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        df = df.sort_values("Fecha").drop_duplicates(subset="Id", keep="last")
    else:
        df = df.drop_duplicates(subset="Id", keep="last")

    if "Categoria" in df.columns:
        df = df[df["Categoria"].isin(["Peligro", "Alerta"])].copy()

    cols = [c for c in ["Id", "Indicador", "Proceso", "Categoria", "Periodicidad", "Anio", "Mes"] if c in df.columns]
    return df[cols].reset_index(drop=True)


def _meses_disponibles() -> list[str]:
    return [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
    ]


def render():
    st.title("Gestión de Oportunidades de Mejora")
    st.caption("Registro y seguimiento de OMs sobre indicadores en alerta y peligro.")

    df_riesgo = _cargar_indicadores_riesgo()
    if df_riesgo.empty:
        st.warning("No hay indicadores en riesgo para registrar OMs.")
        return

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Indicadores en riesgo", len(df_riesgo))
    col_m2.metric("En Peligro", int((df_riesgo.get("Categoria", pd.Series(dtype=str)) == "Peligro").sum()))
    col_m3.metric("En Alerta", int((df_riesgo.get("Categoria", pd.Series(dtype=str)) == "Alerta").sum()))

    opciones = {
        f"{row['Id']} - {row.get('Indicador', '')}": row["Id"]
        for _, row in df_riesgo.iterrows()
    }
    seleccionado = st.selectbox("Indicador", options=list(opciones.keys()))
    id_sel = opciones[seleccionado]
    fila = df_riesgo[df_riesgo["Id"] == id_sel].iloc[0]

    st.markdown(
        f"**Proceso:** {fila.get('Proceso', 'N/D')}  \\n+**Categoría actual:** {fila.get('Categoria', 'N/D')}"
    )

    with st.form("form_registro_om", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            anio = st.number_input("Año", min_value=2020, max_value=2100, value=int(date.today().year), step=1)
        with c2:
            periodo = st.selectbox("Mes", options=_meses_disponibles(), index=max(0, date.today().month - 1))
        with c3:
            tiene_om = st.radio("¿Se abrió OM?", options=["Sí", "No"], horizontal=True)

        numero_om = ""
        comentario = ""
        if tiene_om == "Sí":
            numero_om = st.text_input("Número OM")
        else:
            comentario = st.text_area("Comentario / Justificación", placeholder="Mínimo 20 caracteres")

        guardar = st.form_submit_button("Guardar registro", use_container_width=True)

    if guardar:
        if tiene_om == "Sí" and not str(numero_om).strip():
            st.error("Debes ingresar el número de OM.")
        elif tiene_om == "No" and len(str(comentario).strip()) < 20:
            st.error("El comentario debe tener al menos 20 caracteres.")
        else:
            payload = {
                "id_indicador": str(id_sel),
                "nombre_indicador": str(fila.get("Indicador", "")),
                "proceso": str(fila.get("Proceso", "")),
                "periodo": str(periodo),
                "anio": int(anio),
                "tiene_om": 1 if tiene_om == "Sí" else 0,
                "numero_om": str(numero_om).strip() if tiene_om == "Sí" else "",
                "comentario": str(comentario).strip() if tiene_om == "No" else "",
            }
            if guardar_registro_om(payload):
                st.success("Registro OM guardado correctamente.")
            else:
                st.error("No se pudo guardar el registro OM.")

    st.markdown("### Registros OM")
    anio_filtro = st.number_input("Filtrar registros por año", min_value=2020, max_value=2100, value=int(date.today().year), step=1)
    registros = leer_registros_om(anio=int(anio_filtro))
    if registros:
        df_reg = pd.DataFrame(registros)
        st.dataframe(df_reg, use_container_width=True, height=350)
        st.download_button(
            label="Descargar registros OM (Excel)",
            data=exportar_excel(df_reg, nombre_hoja="Registros_OM"),
            file_name=f"registros_om_{anio_filtro}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    else:
        st.info("No hay registros OM para el año seleccionado.")
