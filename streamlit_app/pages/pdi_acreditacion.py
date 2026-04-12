def render():
import pandas as pd
import plotly.express as px
import streamlit as st

from core.config import NIVEL_COLOR, NIVEL_BG, UMBRAL_PELIGRO, UMBRAL_ALERTA
from services.data_loader import cargar_dataset, cargar_acciones_mejora
from streamlit_app.components.filters import render_filters

def _brecha(row):
    try:
        return float(row.get("Meta", 0)) - float(row.get("Ejecucion", 0))
    except Exception:
        return None

def _clasificar_estado(cumpl):
    if pd.isna(cumpl):
        return "Sin dato"
    if cumpl < UMBRAL_PELIGRO * 100:
        return "Peligro"
    if cumpl < UMBRAL_ALERTA * 100:
        return "Alerta"
    if cumpl < 105:
        return "Cumplimiento"
    return "Sobrecumplimiento"

def render():
    st.title("Gestión y Acreditación (Nivel 2)")
    st.caption("Panel de cumplimiento, brechas y matriz de acreditación.")

    # --- Filtros ---
    with st.expander("🔎 Filtros", expanded=False):
        if st.button("Limpiar filtros", key="pdi_clear_filters"):
            for _k in ("pdi_estado", "pdi_macro", "pdi_horizonte"):
                if _k in st.session_state:
                    del st.session_state[_k]
            st.rerun()

        sel = render_filters(
            pd.DataFrame(),
            {
                "estado": {"label": "Estado", "options": ["Peligro", "Alerta", "Cumplimiento", "Sobrecumplimiento", "Sin dato"]},
                "macro": {"label": "Macrolinea", "options": ["Docencia", "Investigación", "Extensión", "Gobierno"]},
                "horizonte": {"label": "Horizonte", "options": ["2026-1", "2026-2", "2027-1"], "include_all": False, "default": "2026-1"},
            },
            key_prefix="pdi",
            columns_per_row=3,
        )

    activos = []
    if sel.get("estado", "Todos") != "Todos":
        activos.append(f"Estado: {sel['estado']}")
    if sel.get("macro", "Todos") != "Todos":
        activos.append(f"Macrolinea: {sel['macro']}")
    if sel.get("horizonte"):
        activos.append(f"Horizonte: {sel['horizonte']}")
    if activos:
        st.caption("Filtros activos: " + " · ".join(activos))

    # --- Cargar datos reales ---
    df = cargar_dataset()
    if df.empty:
        st.warning("No hay datos disponibles para la matriz de acreditación.")
        return

    # --- Filtrado y normalización ---
    df = df[df["Clasificacion"].str.contains("acredit", case=False, na=False)]
    df = df.copy()
    df["cumplimiento_pct"] = pd.to_numeric(df["cumplimiento_pct"], errors="coerce")
    df["brecha"] = df.apply(_brecha, axis=1)
    df["Estado"] = df["cumplimiento_pct"].apply(_clasificar_estado)

    if sel.get("estado") and sel["estado"] != "Todos":
        df = df[df["Estado"] == sel["estado"]]
    if sel.get("macro") and sel["macro"] != "Todos":
        df = df[df["Linea"] == sel["macro"]]
    if sel.get("horizonte"):
        df = df[df["Periodo"] == sel["horizonte"]]

    # --- KPIs Scorecard ---
    k1, k2, k3 = st.columns(3)
    k1.metric("Cumplimiento promedio (%)", f"{df['cumplimiento_pct'].mean():.1f}%" if not df.empty else "-")
    k2.metric("Brecha promedio (pp)", f"{df['brecha'].mean():.1f}" if not df.empty else "-")
    # Tasa cierre OM: OM cerradas / OM totales (por Id)
    df_acc = cargar_acciones_mejora()
    if not df_acc.empty:
        om_ids = set(df["Id"])
        om_cerradas = df_acc[(df_acc["ESTADO"] == "CERRADA") & (df_acc["ID_INDICADOR"].isin(om_ids))]
        om_total = df_acc[df_acc["ID_INDICADOR"].isin(om_ids)]
        tasa_cierre = 100 * len(om_cerradas) / len(om_total) if len(om_total) else 0
        k3.metric("Tasa cierre OM (%)", f"{tasa_cierre:.1f}%")
    else:
        k3.metric("Tasa cierre OM (%)", "-")

    st.markdown("---")

    # --- Comparativa de brechas por proceso ---
    st.markdown("#### Brecha promedio por proceso")
    if "Proceso" in df.columns:
        df_proc = df.groupby("Proceso", dropna=False).agg(
            brecha=("brecha", "mean"),
            cumplimiento=("cumplimiento_pct", "mean"),
            n=("Id", "count")
        ).reset_index().sort_values("brecha", ascending=False)
        fig = px.bar(
            df_proc,
            x="Proceso", y="brecha",
            color="cumplimiento",
            color_continuous_scale=[NIVEL_COLOR["Peligro"], NIVEL_COLOR["Alerta"], NIVEL_COLOR["Cumplimiento"]],
            labels={"brecha": "Brecha promedio (pp)", "cumplimiento": "% Cumplimiento"},
            title="Brecha promedio por proceso",
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=340)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos de proceso para comparar brechas.")

    st.markdown("---")

    # --- Matriz de acreditación ---
    st.markdown("#### Matriz de acreditación")
    cols = [c for c in ["Id", "Indicador", "Linea", "Objetivo", "cumplimiento_pct", "Meta", "Ejecucion", "Estado"] if c in df.columns]
    tabla = df[cols].copy()
    tabla = tabla.rename(columns={
        "cumplimiento_pct": "% Cumplimiento",
        "Meta": "Meta",
        "Ejecucion": "Ejecución",
        "Linea": "Macrolinea",
    })
    st.dataframe(tabla, use_container_width=True, hide_index=True, height=420)
