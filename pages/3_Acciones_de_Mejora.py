"""
pages/3_Acciones_de_Mejora.py — Oportunidades de Mejora.

Fuente principal : data/raw/OM.xlsx / OM.xls  (encabezados en fila 8)
Plan de Acción   : data/raw/Plan de accion/*.xlsx / *.xls  (consolidado)

Interacción:
  · Seleccionar una fila en la tabla de OM despliega las acciones
    del Plan de Acción asociadas (vínculo: Id ↔ Id Oportunidad de mejora).
  · Sección inferior muestra procesos con acciones retrasadas.
"""
import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import cargar_om, cargar_plan_accion
from utils.charts import exportar_excel

# ── Carga de datos ─────────────────────────────────────────────────────────────
st.markdown("# 📋 Oportunidades de Mejora")
st.caption("Fuente: **OM.xlsx** · Plan de Acción consolidado")
st.markdown("---")

df_om = cargar_om()
df_pa = cargar_plan_accion()

if df_om.empty:
    st.error(
        "No se encontró **OM.xlsx** en `data/raw/`. "
        "Verifica que el archivo exista y que los encabezados estén en la fila 8."
    )
    st.stop()

# ── Columnas a mostrar ────────────────────────────────────────────────────────
_COLS_OM = [
    "Id", "Fecha de identificación", "Avance (%)", "Estado",
    "Tipo de acción", "Tipo de oportunidad", "Procesos", "Sede",
    "Descripción", "Fuente", "Fecha de creación",
    "Fecha estimada de cierre", "Fecha real de cierre",
    "Días vencida", "Meses sin avance", "Comentario",
]
_COLS_PA = [
    "Id Acción", "Fecha creación", "Clasificación", "Avance (%)",
    "Estado (Plan de Acción)", "Estado (Oportunidad de mejora)", "Aprobado", "Comentario",
    "Id Oportunidad de mejora", "Descripción", "Acción",
    "Proceso responsable", "Responsable de ejecución", "Fecha límite de ejecución",
    "Responsable de seguimiento", "Fecha límite de seguimiento",
    "Responsable de evaluación", "Fuente de Identificación", "Fecha límite de evaluación",
    "Última ejecución", "Último seguimiento",
]

# Columna de vínculo OM ↔ Plan de Acción
_COL_PA_ID = next(
    (c for c in df_pa.columns if "id oportunidad" in c.lower()),
    None,
) if not df_pa.empty else None

# Columnas clave en OM
_COL_AV      = next((c for c in df_om.columns if "avance" in c.lower()), None)
_COL_ESTADO  = next((c for c in df_om.columns if c.lower() == "estado"), None)
_COL_DIAS    = next((c for c in df_om.columns if "días vencida" in c.lower() or "dias vencida" in c.lower()), None)


# ── KPIs ──────────────────────────────────────────────────────────────────────
total         = len(df_om)
cnt_cerradas  = int((df_om[_COL_ESTADO] == "Cerrada").sum())  if _COL_ESTADO else 0
cnt_abiertas  = total - cnt_cerradas
avance_prom   = float(df_om[_COL_AV].mean())                  if _COL_AV     else 0.0
cnt_vencidas  = int((df_om[_COL_DIAS] > 0).sum())             if _COL_DIAS   else 0
cnt_pa        = len(df_pa)

kc = st.columns(6)
kc[0].metric("Total OM",          total)
kc[1].metric("Abiertas",          cnt_abiertas)
kc[2].metric("Cerradas",          cnt_cerradas)
kc[3].metric("Avance promedio",   f"{round(avance_prom, 1)}%")
kc[4].metric("OM vencidas",       cnt_vencidas,  delta=None if cnt_vencidas == 0 else f"⚠ {cnt_vencidas}")
kc[5].metric("Acciones de plan",  cnt_pa)

st.markdown("---")


# ── Filtros ───────────────────────────────────────────────────────────────────
def _opts(col):
    if col not in df_om.columns:
        return [""]
    return [""] + sorted(df_om[col].dropna().astype(str).unique().tolist())


with st.expander("🔍 Filtros", expanded=True):
    fc1, fc2, fc3, fc4, fc5 = st.columns(5)
    f_estado = fc1.selectbox("Estado",           _opts("Estado"),
                             key="om_estado", format_func=lambda x: "— Todos —" if x == "" else x)
    f_tipo_a = fc2.selectbox("Tipo de acción",   _opts("Tipo de acción"),
                             key="om_tipo_a", format_func=lambda x: "— Todos —" if x == "" else x)
    f_tipo_o = fc3.selectbox("Tipo oportunidad", _opts("Tipo de oportunidad"),
                             key="om_tipo_o", format_func=lambda x: "— Todos —" if x == "" else x)
    f_proc   = fc4.selectbox("Proceso",          _opts("Procesos"),
                             key="om_proc",   format_func=lambda x: "— Todos —" if x == "" else x)
    f_sede   = fc5.selectbox("Sede",             _opts("Sede"),
                             key="om_sede",   format_func=lambda x: "— Todos —" if x == "" else x)

df_filt = df_om.copy()
if f_estado and "Estado"              in df_filt.columns: df_filt = df_filt[df_filt["Estado"]              == f_estado]
if f_tipo_a and "Tipo de acción"      in df_filt.columns: df_filt = df_filt[df_filt["Tipo de acción"]      == f_tipo_a]
if f_tipo_o and "Tipo de oportunidad" in df_filt.columns: df_filt = df_filt[df_filt["Tipo de oportunidad"] == f_tipo_o]
if f_proc   and "Procesos"            in df_filt.columns: df_filt = df_filt[df_filt["Procesos"]            == f_proc]
if f_sede   and "Sede"                in df_filt.columns: df_filt = df_filt[df_filt["Sede"]                == f_sede]


# ── Tabla principal de OM (seleccionable) ─────────────────────────────────────
cols_show = [c for c in _COLS_OM if c in df_filt.columns]
df_tabla  = df_filt[cols_show].copy()

# Formatear avance
if _COL_AV and _COL_AV in df_tabla.columns:
    df_tabla[_COL_AV] = df_tabla[_COL_AV].apply(
        lambda v: f"{v:.1f}%" if pd.notna(v) else "—"
    )

# Formatear fechas
for _fc in ["Fecha de identificación", "Fecha de creación",
            "Fecha estimada de cierre", "Fecha real de cierre"]:
    if _fc in df_tabla.columns:
        df_tabla[_fc] = (pd.to_datetime(df_tabla[_fc], errors="coerce")
                          .dt.strftime("%d/%m/%Y").fillna("—"))

st.caption(
    f"Mostrando **{len(df_tabla)}** oportunidades — "
    "selecciona una fila para ver el **Plan de Acción**"
)

ev = st.dataframe(
    df_tabla,
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    column_config={
        "Descripción":         st.column_config.TextColumn("Descripción",      width="large"),
        "Comentario":          st.column_config.TextColumn("Comentario",       width="medium"),
        "Procesos":            st.column_config.TextColumn("Procesos",         width="medium"),
        "Tipo de oportunidad": st.column_config.TextColumn("Tipo oportunidad", width="medium"),
        "Días vencida":        st.column_config.NumberColumn("Días vencida",   format="%d"),
        "Meses sin avance":    st.column_config.NumberColumn("Meses sin avance", format="%d"),
    },
)

st.download_button(
    "📥 Exportar Oportunidades (Excel)",
    data=exportar_excel(df_tabla, "Oportunidades de Mejora"),
    file_name="oportunidades_mejora.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="exp_om",
)


# ── Plan de Acción — detalle al seleccionar fila ──────────────────────────────
if ev.selection and ev.selection.rows:
    row_idx = ev.selection.rows[0]
    row_om  = df_filt.iloc[row_idx]
    om_id   = str(row_om.get("Id", "")).strip()

    st.markdown("---")
    st.markdown(f"### 📌 Plan de Acción — Oportunidad **{om_id}**")

    # Tarjeta resumen de la OM seleccionada
    with st.expander("📄 Detalle de la Oportunidad", expanded=True):
        d1, d2, d3 = st.columns(3)
        d1.write(f"**Tipo de acción:** {row_om.get('Tipo de acción', '—')}")
        d1.write(f"**Tipo de oportunidad:** {row_om.get('Tipo de oportunidad', '—')}")
        d2.write(f"**Proceso:** {row_om.get('Procesos', '—')}")
        d2.write(f"**Sede:** {row_om.get('Sede', '—')}")
        d3.write(f"**Estado:** {row_om.get('Estado', '—')}")
        avance_val = row_om.get(_COL_AV, "—") if _COL_AV else "—"
        d3.write(f"**Avance:** {avance_val}")
        st.write(f"**Descripción:** {row_om.get('Descripción', '—')}")
        st.write(f"**Fuente:** {row_om.get('Fuente', '—')}")
        st.write(f"**Comentario:** {row_om.get('Comentario', '—')}")

    # Acciones del Plan de Acción
    if df_pa.empty or _COL_PA_ID is None:
        st.info(
            "No se encontraron archivos en `data/raw/Plan de accion/`. "
            "Coloca los archivos PA_*.xlsx en esa carpeta."
        )
    else:
        df_plan = df_pa[df_pa[_COL_PA_ID].astype(str) == om_id].copy()

        if df_plan.empty:
            st.info(f"No hay acciones registradas en el Plan de Acción para la OM **{om_id}**.")
        else:
            cols_pa_show = [c for c in _COLS_PA if c in df_plan.columns]
            df_plan_show = df_plan[cols_pa_show].copy()

            # Formatear fechas datetime
            for col in df_plan_show.select_dtypes(include="datetime").columns:
                df_plan_show[col] = df_plan_show[col].dt.strftime("%d/%m/%Y").fillna("—")

            # Formatear avance
            col_av_pa = next((c for c in df_plan_show.columns if "avance" in c.lower()), None)
            if col_av_pa:
                df_plan_show[col_av_pa] = df_plan_show[col_av_pa].apply(
                    lambda v: f"{v:.1f}%" if pd.notna(v) else "—"
                )

            st.caption(f"**{len(df_plan_show)}** acción(es) asociada(s)")
            st.dataframe(
                df_plan_show,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Descripción":                st.column_config.TextColumn("Descripción",       width="large"),
                    "Acción":                     st.column_config.TextColumn("Acción",            width="large"),
                    "Comentario":                 st.column_config.TextColumn("Comentario",        width="medium"),
                    "Proceso responsable":        st.column_config.TextColumn("Proc. resp.",       width="medium"),
                    "Responsable de ejecución":   st.column_config.TextColumn("Resp. ejecución",   width="medium"),
                    "Responsable de seguimiento": st.column_config.TextColumn("Resp. seguimiento", width="medium"),
                    "Responsable de evaluación":  st.column_config.TextColumn("Resp. evaluación",  width="medium"),
                },
            )

            st.download_button(
                "📥 Exportar Plan de Acción (Excel)",
                data=exportar_excel(df_plan_show, f"Plan_OM_{om_id}"),
                file_name=f"plan_accion_om_{om_id}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="exp_pa",
            )


# ── Análisis: Procesos con acciones retrasadas ────────────────────────────────
st.markdown("---")
st.markdown("### ⚠️ Procesos con acciones retrasadas en el Plan de Acción")

if df_pa.empty or _COL_PA_ID is None:
    st.info("Sin datos de Plan de Acción disponibles.")
else:
    _COL_FECHA_LIM = next(
        (c for c in df_pa.columns if "fecha límite de ejecución" in c.lower()
         or "fecha limite de ejecucion" in c.lower()),
        None,
    )
    _COL_ESTADO_PA = next(
        (c for c in df_pa.columns if "estado (plan de acción)" in c.lower()
         or "estado (plan de accion)" in c.lower()),
        None,
    )
    _COL_PROC_RESP = next(
        (c for c in df_pa.columns if "proceso responsable" in c.lower()),
        None,
    )

    if _COL_FECHA_LIM and _COL_ESTADO_PA and _COL_PROC_RESP:
        hoy = pd.Timestamp(datetime.date.today())

        # Retrasada: fecha límite vencida Y estado ≠ Ejecutado
        mask_ret = (
            pd.to_datetime(df_pa[_COL_FECHA_LIM], errors="coerce") < hoy
        ) & (
            df_pa[_COL_ESTADO_PA].astype(str).str.strip() != "Ejecutado"
        )
        df_ret = df_pa[mask_ret].copy()

        if df_ret.empty:
            st.success("✅ No hay acciones del Plan de Acción retrasadas.")
        else:
            # Conteo por proceso responsable
            resumen = (
                df_ret.groupby(_COL_PROC_RESP)
                .size()
                .reset_index(name="Acciones retrasadas")
                .sort_values("Acciones retrasadas", ascending=False)
            )

            col_g, col_t = st.columns([3, 2])

            with col_g:
                fig = go.Figure(go.Bar(
                    x=resumen["Acciones retrasadas"],
                    y=resumen[_COL_PROC_RESP],
                    orientation="h",
                    marker_color="#D32F2F",
                    text=resumen["Acciones retrasadas"],
                    textposition="outside",
                ))
                fig.update_layout(
                    title=f"Acciones retrasadas por proceso ({len(df_ret)} total)",
                    xaxis_title="N° acciones retrasadas",
                    yaxis={"categoryorder": "total ascending"},
                    height=max(300, len(resumen) * 35 + 80),
                    margin=dict(l=10, r=40, t=50, b=30),
                )
                st.plotly_chart(fig, use_container_width=True)

            with col_t:
                st.caption(f"**{len(df_ret)}** acción(es) retrasada(s) en **{len(resumen)}** proceso(s)")
                st.dataframe(resumen, use_container_width=True, hide_index=True)

            # Tabla detalle de acciones retrasadas
            with st.expander("📋 Ver detalle de acciones retrasadas"):
                _cols_ret = [c for c in [
                    _COL_PA_ID, _COL_PROC_RESP,
                    "Descripción", "Acción", _COL_ESTADO_PA, _COL_FECHA_LIM,
                    "Responsable de ejecución",
                ] if c in df_ret.columns]

                df_ret_show = df_ret[_cols_ret].copy()
                if _COL_FECHA_LIM in df_ret_show.columns:
                    df_ret_show[_COL_FECHA_LIM] = (
                        pd.to_datetime(df_ret_show[_COL_FECHA_LIM], errors="coerce")
                        .dt.strftime("%d/%m/%Y").fillna("—")
                    )
                st.dataframe(df_ret_show, use_container_width=True, hide_index=True,
                             column_config={
                                 "Descripción": st.column_config.TextColumn("Descripción", width="large"),
                                 "Acción":      st.column_config.TextColumn("Acción",      width="large"),
                             })
                st.download_button(
                    "📥 Exportar acciones retrasadas (Excel)",
                    data=exportar_excel(df_ret_show, "Acciones_Retrasadas"),
                    file_name="acciones_retrasadas.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="exp_ret",
                )
    else:
        st.warning(
            "No se encontraron las columnas necesarias en el Plan de Acción "
            "(`Proceso responsable`, `Fecha límite de ejecución`, `Estado (Plan de Acción)`)."
        )
