"""
pages/6_Direccionamiento_Estrategico.py — Direccionamiento Estratégico (temporal).

Procesos incluidos:
  · Planeación Estratégica     (excluye IDs: 373, 390, 414–418, 420, 469–471)
  · Desempeño Institucional
  · Gestión de Proyectos

Filtro único: Año (por defecto 2025).
Vista por defecto: KPIs + tabla del año seleccionado (último período por indicador).
Al hacer clic en un indicador: ficha histórica completa (gráfico + tabla).
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.charts import exportar_excel, panel_detalle_indicador
from core.config import COLOR_CATEGORIA, COLOR_CATEGORIA_CLARO, COLORES, ORDEN_CATEGORIAS
from services.data_loader import cargar_dataset

# ── Constantes ─────────────────────────────────────────────────────────────────
_PROCESOS_DIR = {
    "Planeación Estratégica",
    "Desempeño Institucional",
    "Gestión de Proyectos",
}
_IDS_EXCLUIR_PLAN = {
    "373", "390", "414", "415", "416", "417", "418", "420", "469", "470", "471"
}
_COLOR_PROC = {
    "Planeación Estratégica":  "#1A3A5C",
    "Desempeño Institucional": "#1565C0",
    "Gestión de Proyectos":    "#2E7D32",
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def _ultimo_por_anio(df: pd.DataFrame) -> pd.DataFrame:
    """Para el año filtrado: un registro por indicador (el período más reciente)."""
    if df.empty or "Id" not in df.columns:
        return df
    col = "Fecha" if "Fecha" in df.columns else "Periodo"
    return (df.sort_values(col)
              .drop_duplicates(subset="Id", keep="last")
              .reset_index(drop=True))


def _kpis(df: pd.DataFrame):
    total = len(df)
    cats = {
        cat: {"n": int((df["Categoria"] == cat).sum()) if "Categoria" in df.columns else 0}
        for cat in ORDEN_CATEGORIAS
    }
    for cat in cats:
        cats[cat]["pct"] = round(cats[cat]["n"] / total * 100, 1) if total else 0
    return total, cats


def _render_kpis(total: int, cats: dict):
    definiciones = [
        ("Total",             total,                         COLORES["primario"],          None),
        ("🔴 Peligro",        cats["Peligro"]["n"],          COLORES["peligro"],           f'{cats["Peligro"]["pct"]}%'),
        ("🟡 Alerta",         cats["Alerta"]["n"],           COLORES["alerta"],            f'{cats["Alerta"]["pct"]}%'),
        ("🟢 Cumplimiento",   cats["Cumplimiento"]["n"],     COLORES["cumplimiento"],      f'{cats["Cumplimiento"]["pct"]}%'),
        ("🔵 Sobrecumpl.",    cats["Sobrecumplimiento"]["n"],COLORES["sobrecumplimiento"], f'{cats["Sobrecumplimiento"]["pct"]}%'),
    ]
    for col, (label, val, color, delta) in zip(st.columns(5), definiciones):
        with col:
            st.metric(label, val, delta=delta,
                      delta_color="off" if label == "Total" else
                      ("inverse" if "Peligro" in label or "Alerta" in label else "normal"))


def _tabla_display(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in ["Id", "Indicador", "Subproceso", "Periodo",
                        "Meta", "Ejecucion", "Cumplimiento_norm", "Categoria", "Sentido"]
            if c in df.columns]
    df = df[cols].copy()
    if "Cumplimiento_norm" in df.columns:
        df["Cumplimiento_norm"] = (df["Cumplimiento_norm"] * 100).round(1).astype(str) + "%"
    return df.rename(columns={"Cumplimiento_norm": "Cumpl.%", "Ejecucion": "Ejecución"})


def _estilo_cat(row):
    bg = COLOR_CATEGORIA_CLARO.get(row.get("Categoria", ""), "")
    return [f"background-color:{bg}" if bg else "" for _ in row]


def _render_proceso(df_proc: pd.DataFrame, nombre: str, prefix: str, anio: int, df_raw: pd.DataFrame):
    if df_proc.empty:
        st.info(f"Sin indicadores para **{nombre}**.")
        return

    # Filtrar por año seleccionado y tomar último período por indicador
    if "Anio" in df_proc.columns:
        df_anio = df_proc[df_proc["Anio"] == anio]
    else:
        df_anio = df_proc

    df_ult = _ultimo_por_anio(df_anio)

    if df_ult.empty:
        st.warning(f"Sin datos para **{nombre}** en {anio}.")
        return

    # KPIs
    total, cats = _kpis(df_ult)
    _render_kpis(total, cats)

    st.markdown("---")

    # Tabla
    st.caption(
        f"**{total}** indicadores · año **{anio}** · "
        "Haz clic en una fila para ver la ficha histórica completa."
    )
    df_show = _tabla_display(df_ult)

    col_cfg = {
        "Indicador": st.column_config.TextColumn("Indicador", width="large"),
        "Cumpl.%":   st.column_config.TextColumn("Cumpl.%",   width="small"),
    }
    if "Meta"      in df_show.columns: col_cfg["Meta"]      = st.column_config.NumberColumn("Meta",      format="%.2f")
    if "Ejecución" in df_show.columns: col_cfg["Ejecución"] = st.column_config.NumberColumn("Ejecución", format="%.2f")

    event = st.dataframe(
        df_show.style.apply(_estilo_cat, axis=1),
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=f"tbl_{prefix}",
        column_config=col_cfg,
    )

    # Ficha histórica al seleccionar fila
    if event and event.selection and event.selection.get("rows"):
        idx    = event.selection["rows"][0]
        id_sel = str(df_ult.iloc[idx]["Id"])
        nom    = str(df_ult.iloc[idx].get("Indicador", ""))
        df_hist = df_raw[df_raw["Id"] == id_sel].copy() if not df_raw.empty else pd.DataFrame()
        if df_hist.empty:
            df_hist = df_proc[df_proc["Id"] == id_sel].copy()

        @st.dialog(f"📊 {id_sel} — {nom[:65]}", width="large")
        def _ficha():
            panel_detalle_indicador(df_hist, id_sel, df_raw)

        _ficha()

    st.download_button(
        "📥 Exportar",
        data=exportar_excel(df_show, nombre[:31]),
        file_name=f"{prefix}_{anio}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"exp_{prefix}",
    )


# ══════════════════════════════════════════════════════════════════════════════
# CARGA DE DATOS
# ══════════════════════════════════════════════════════════════════════════════

df_raw = cargar_dataset()

if df_raw.empty:
    st.error("No se encontró el dataset principal. Ejecuta primero `actualizar_consolidado.py`.")
    st.stop()

if "Proceso" not in df_raw.columns:
    st.error("El dataset no contiene la columna 'Proceso'.")
    st.stop()

df_dir = df_raw[df_raw["Proceso"].isin(_PROCESOS_DIR)].copy()

if df_dir.empty:
    st.error("No se encontraron indicadores para los procesos de Direccionamiento Estratégico.")
    st.stop()

# Excluir IDs en Planeación Estratégica
mask_excl = (df_dir["Proceso"] == "Planeación Estratégica") & df_dir["Id"].isin(_IDS_EXCLUIR_PLAN)
df_dir = df_dir[~mask_excl].copy()

df_plan   = df_dir[df_dir["Proceso"] == "Planeación Estratégica"].copy()
df_desemp = df_dir[df_dir["Proceso"] == "Desempeño Institucional"].copy()
df_gest   = df_dir[df_dir["Proceso"] == "Gestión de Proyectos"].copy()

# ══════════════════════════════════════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("# 🏛️ Direccionamiento Estratégico")

# Filtro de año (único)
anios_disp = sorted([int(a) for a in df_dir["Anio"].dropna().unique()]) if "Anio" in df_dir.columns else [2025]
anio_def   = 2025 if 2025 in anios_disp else anios_disp[-1]
anio_sel   = st.selectbox("Año", anios_disp, index=anios_disp.index(anio_def), key="dir_anio")

st.markdown("---")

tab_plan, tab_desemp, tab_gest = st.tabs([
    "📋 Planeación Estratégica",
    "📊 Desempeño Institucional",
    "🗂️ Gestión de Proyectos",
])

with tab_plan:
    _render_proceso(df_plan, "Planeación Estratégica", "plan", anio_sel, df_raw)

with tab_desemp:
    _render_proceso(df_desemp, "Desempeño Institucional", "desemp", anio_sel, df_raw)

with tab_gest:
    _render_proceso(df_gest, "Gestión de Proyectos", "gest", anio_sel, df_raw)
