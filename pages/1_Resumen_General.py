"""
pages/1_Resumen_General.py — Reporte de Cumplimiento.

Fuente: data/raw/indicadores_kawak.xlsx (último reporte por indicador).
Solo muestra indicadores con datos en kawak.
Mapeo de jerarquía: Subproceso-Proceso-Area.xlsx
"""
import html as _html
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.charts import exportar_excel
from utils.niveles import (
    NIVEL_COLOR, NIVEL_BG, NIVEL_ORDEN, NIVEL_ICON, nivel_desde_pct,
)

# ── Rutas ─────────────────────────────────────────────────────────────────────
_DATA_RAW   = Path(__file__).parent.parent / "data" / "raw"
_RUTA_KAWAK = _DATA_RAW / "indicadores_kawak.xlsx"
_RUTA_MAPA  = _DATA_RAW / "Subproceso-Proceso-Area.xlsx"

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _to_num(v):
    try:
        return float(str(v).strip())
    except (ValueError, TypeError):
        return None


def _nivel(row) -> str:
    """Nivel de cumplimiento con umbrales fijos: <80 Peligro, 80-100 Alerta, 100-105 Cumplimiento, >105 Sobrecumplimiento."""
    return nivel_desde_pct(row.get("cumplimiento", ""))


def _limpiar(v) -> str:
    if pd.isna(v) if not isinstance(v, str) else False:
        return ""
    return _html.unescape(str(v)).strip()


def _id_limpio(x) -> str:
    if pd.isna(x) if not isinstance(x, str) else False:
        return ""
    try:
        f = float(x)
        return str(int(f)) if f == int(f) else str(f)
    except (ValueError, TypeError):
        return str(x).strip()


def _fmt_num(v) -> str:
    n = _to_num(v)
    if n is None:
        return str(v) if str(v).strip() not in ("", "nan") else "—"
    return f"{n:,.2f}".rstrip("0").rstrip(".")


# ══════════════════════════════════════════════════════════════════════════════
# CARGA DE DATOS
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=600, show_spinner=False)
def _cargar_mapa() -> pd.DataFrame:
    if not _RUTA_MAPA.exists():
        return pd.DataFrame()
    df = pd.read_excel(str(_RUTA_MAPA), engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]
    col_sub    = next((c for c in df.columns if c.lower() == "subproceso"), None)
    col_proc   = next((c for c in df.columns if c.lower() == "proceso"), None)
    col_area   = next((c for c in df.columns
                       if "rea" in c.lower() and "vicerr" not in c.lower()), None)
    col_vicerr = next((c for c in df.columns if "icerrector" in c.lower()), None)
    if not col_sub or not col_proc:
        return pd.DataFrame()
    rename = {col_sub: "Subproceso", col_proc: "Proceso"}
    if col_area:   rename[col_area]   = "Area"
    if col_vicerr: rename[col_vicerr] = "Vicerrectoria"
    df = df.rename(columns=rename)
    cols_k = [c for c in ["Subproceso", "Proceso", "Area", "Vicerrectoria"] if c in df.columns]
    return (df[cols_k]
            .dropna(subset=["Subproceso"])
            .drop_duplicates(subset=["Subproceso"])
            .reset_index(drop=True))


@st.cache_data(ttl=300, show_spinner="Cargando indicadores_kawak.xlsx...")
def _cargar_kawak() -> pd.DataFrame:
    if not _RUTA_KAWAK.exists():
        return pd.DataFrame()

    df = pd.read_excel(str(_RUTA_KAWAK), engine="openpyxl",
                       keep_default_na=False, na_values=[""])
    df.columns = [str(c).strip() for c in df.columns]

    # Renombrar columnas al estándar interno
    _rename = {
        "ID": "Id", "nombre": "Indicador", "clasificacion": "Clasificacion",
        "sentido": "Sentido", "proceso": "Subproceso", "frecuencia": "Periodicidad",
        "resultado": "Resultado", "meta": "Meta",
        "fecha": "fecha", "fecha_corte": "fecha_corte",
    }
    df = df.rename(columns={k: v for k, v in _rename.items() if k in df.columns})

    # Limpiar Id y texto
    if "Id" in df.columns:
        df["Id"] = df["Id"].apply(_id_limpio)
    for col in ["Indicador", "Clasificacion", "Sentido", "Subproceso"]:
        if col in df.columns:
            df[col] = df[col].apply(_limpiar)

    # Normalizar fecha y conservar solo el último reporte por indicador
    if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.sort_values("fecha", ascending=True)
    df = df.groupby("Id", as_index=False).last()

    # Calcular Nivel de cumplimiento
    df["Nivel de cumplimiento"] = df.apply(_nivel, axis=1)

    # Columna formateada para mostrar
    df["Cumplimiento"] = df["cumplimiento"].apply(_fmt_num)
    df["Resultado"]    = df["Resultado"].apply(
        lambda v: _fmt_num(v) if _to_num(v) is not None else str(v)
    )
    df["Fecha reporte"] = df["fecha"].dt.strftime("%d/%m/%Y").fillna("—")

    # Merge con jerarquía de procesos
    mapa = _cargar_mapa()
    if not mapa.empty and "Subproceso" in df.columns:
        df = df.merge(mapa, on="Subproceso", how="left")

    return df


# ══════════════════════════════════════════════════════════════════════════════
# FILTROS
# ══════════════════════════════════════════════════════════════════════════════

def _aplicar_filtros(df, txt_id, txt_nom, sel_proc, sel_sub, sel_nivel):
    mask = pd.Series(True, index=df.index)
    if txt_id.strip():
        mask &= df["Id"].astype(str).str.contains(txt_id.strip(), case=False, na=False)
    if txt_nom.strip() and "Indicador" in df.columns:
        mask &= df["Indicador"].astype(str).str.contains(txt_nom.strip(), case=False, na=False)
    if sel_proc and "Proceso" in df.columns:
        mask &= df["Proceso"] == sel_proc
    if sel_sub and "Subproceso" in df.columns:
        mask &= df["Subproceso"] == sel_sub
    if sel_nivel:
        mask &= df["Nivel de cumplimiento"] == sel_nivel
    return df[mask].reset_index(drop=True)


def _filtros_ui(df, prefix):
    with st.expander("🔍 Filtros", expanded=True):
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            txt_id = st.text_input("ID", key=f"{prefix}_id", placeholder="Buscar ID...")
        with r1c2:
            txt_nom = st.text_input("Nombre del indicador", key=f"{prefix}_nom",
                                    placeholder="Buscar nombre...")
        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1:
            opts_p = [""] + sorted(df["Proceso"].dropna().unique().tolist()) \
                     if "Proceso" in df.columns else [""]
            sel_proc = st.selectbox("Proceso", opts_p, key=f"{prefix}_proc",
                                    format_func=lambda x: "— Todos —" if x == "" else x)
        with r2c2:
            if sel_proc and "Proceso" in df.columns and "Subproceso" in df.columns:
                sub_opts = [""] + sorted(
                    df.loc[df["Proceso"] == sel_proc, "Subproceso"].dropna().unique().tolist()
                )
            else:
                sub_opts = [""] + (sorted(df["Subproceso"].dropna().unique().tolist())
                                   if "Subproceso" in df.columns else [])
            sel_sub = st.selectbox("Subproceso", sub_opts, key=f"{prefix}_sub",
                                   format_func=lambda x: "— Todos —" if x == "" else x)
        with r2c3:
            niv_opts = [""] + [n for n in NIVEL_ORDEN
                               if n in df["Nivel de cumplimiento"].unique()]
            sel_niv = st.selectbox("Nivel de cumplimiento", niv_opts, key=f"{prefix}_niv",
                                   format_func=lambda x: "— Todos —" if x == "" else x)
    return txt_id, txt_nom, sel_proc, sel_sub, sel_niv


# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICOS
# ══════════════════════════════════════════════════════════════════════════════

def _fig_donut(df):
    counts = df["Nivel de cumplimiento"].value_counts()
    labels = [n for n in NIVEL_ORDEN if n in counts.index]
    values = [int(counts[n]) for n in labels]
    colors = [NIVEL_COLOR[n] for n in labels]
    total  = sum(values)
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.55,
        marker=dict(colors=colors, line=dict(color="white", width=2)),
        textinfo="label+value",
        textfont=dict(size=12),
        hovertemplate="<b>%{label}</b><br>%{value} indicadores (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        height=320, showlegend=True,
        legend=dict(orientation="v", x=1.02, y=0.5),
        margin=dict(t=10, b=10, l=10, r=120),
        paper_bgcolor="white",
        annotations=[dict(text=f"<b>{total}</b><br>total",
                          x=0.5, y=0.5, font_size=16, showarrow=False)],
    )
    return fig


def _fig_barras_nivel(df, col_cat):
    """Barras horizontales apiladas por Nivel de cumplimiento."""
    if col_cat not in df.columns:
        return go.Figure()
    tmp = df.copy()
    tmp[col_cat] = tmp[col_cat].astype(str).str.strip()
    tmp = tmp[tmp[col_cat].notna() & (tmp[col_cat] != "nan")]

    stats = (tmp.groupby([col_cat, "Nivel de cumplimiento"])
             .size().unstack(fill_value=0).reset_index())

    niveles = [n for n in NIVEL_ORDEN if n in stats.columns]
    stats["_t"] = stats[niveles].sum(axis=1)
    stats = stats.sort_values("_t", ascending=False).drop(columns="_t")
    cats = list(stats[col_cat].astype(str))

    max_len  = max((len(c) for c in cats), default=10)
    margin_l = min(max(max_len * 6, 120), 360)
    h        = max(300, len(stats) * 44 + 70)

    fig = go.Figure()
    for nivel in niveles:
        vals = stats[nivel].tolist()
        fig.add_trace(go.Bar(
            y=cats, x=vals, orientation="h", name=nivel,
            marker_color=NIVEL_COLOR[nivel],
            text=[v if v > 0 else "" for v in vals],
            textposition="inside", insidetextanchor="middle",
            textfont=dict(size=10, color="white"),
        ))

    fig.update_layout(
        barmode="stack", height=h,
        xaxis_title="Indicadores", yaxis_title="",
        yaxis=dict(categoryorder="array", categoryarray=cats,
                   autorange="reversed", tickfont=dict(size=10)),
        uniformtext_minsize=9, uniformtext_mode="hide",
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h", y=-0.12),
        margin=dict(t=10, b=55, l=margin_l, r=30),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# ESTILO TABLA
# ══════════════════════════════════════════════════════════════════════════════

def _estilo_nivel(row):
    bg = NIVEL_BG.get(str(row.get("Nivel de cumplimiento", "")), "")
    return [f"background-color: {bg}" if c == "Nivel de cumplimiento" else ""
            for c in row.index]


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("# 🏠 Reporte de Cumplimiento")
st.caption("Último reporte por indicador · Fuente: **indicadores_kawak.xlsx**")
st.markdown("---")

# Cargar datos
df_raw = _cargar_kawak()

if df_raw.empty:
    st.error("No se encontró **indicadores_kawak.xlsx** en `data/raw/`.")
    st.stop()

total = len(df_raw)
cnts  = df_raw["Nivel de cumplimiento"].value_counts()

# ── KPIs ──────────────────────────────────────────────────────────────────────
kc = st.columns(5)
with kc[0]:
    st.metric("Total indicadores", total)
for i, (niv, d_color) in enumerate([
        ("Peligro",           "inverse"),
        ("Alerta",            "off"),
        ("Cumplimiento",      "normal"),
        ("Sobrecumplimiento", "normal"),
], 1):
    n   = int(cnts.get(niv, 0))
    pct = round(n / total * 100, 1) if total else 0
    with kc[i]:
        st.metric(f"{NIVEL_ICON[niv]} {niv}", n,
                  delta=f"{pct}%", delta_color=d_color)

st.markdown("---")

# ── Filtros UI ────────────────────────────────────────────────────────────────
f_id, f_nom, f_proc, f_sub, f_niv = _filtros_ui(df_raw, "rc")

# Filtros de gráficos (session_state)
_key_donut  = "rc_sel_donut"
_key_vicerr = "rc_sel_vicerr"
_key_proc   = "rc_sel_proceso"

# Aplicar todos los filtros
df_ui = _aplicar_filtros(df_raw, f_id, f_nom, f_proc, f_sub, f_niv)

sel_donut  = st.session_state.get(_key_donut)
sel_vicerr = st.session_state.get(_key_vicerr)
sel_proc_g = st.session_state.get(_key_proc)

df_fil = df_ui.copy()
if sel_donut  and "Nivel de cumplimiento" in df_fil.columns:
    df_fil = df_fil[df_fil["Nivel de cumplimiento"] == sel_donut]
if sel_vicerr and "Vicerrectoria" in df_fil.columns:
    df_fil = df_fil[df_fil["Vicerrectoria"] == sel_vicerr]
if sel_proc_g and "Proceso" in df_fil.columns:
    df_fil = df_fil[df_fil["Proceso"] == sel_proc_g]

# Etiqueta de filtros activos de gráfico
filtros_activos = [v for v in (sel_donut, sel_vicerr, sel_proc_g) if v]
if filtros_activos:
    fa1, fa2 = st.columns([6, 1])
    with fa1:
        st.info("📊 Filtro gráfico activo: " + " · ".join(f"**{v}**" for v in filtros_activos))
    with fa2:
        if st.button("✖ Limpiar", key="rc_clear_all"):
            for k in (_key_donut, _key_vicerr, _key_proc):
                st.session_state[k] = None
            st.rerun()

st.caption(f"Mostrando **{len(df_fil)}** de **{total}** indicadores")
st.markdown("---")

# ── Gráficos: Donut + Vicerrectoría ──────────────────────────────────────────
gc1, gc2 = st.columns([1, 2])

with gc1:
    st.markdown("#### Por Nivel de Cumplimiento")
    st.caption("💡 Clic en un segmento para filtrar.")
    fig_donut = _fig_donut(df_ui)
    ev_donut  = st.plotly_chart(fig_donut, use_container_width=True,
                                on_select="rerun", key="rc_donut_chart")
    if ev_donut.selection and ev_donut.selection.get("points"):
        clicked_niv = ev_donut.selection["points"][0].get("label")
        if clicked_niv != st.session_state.get(_key_donut):
            st.session_state[_key_donut] = clicked_niv
            st.rerun()

with gc2:
    st.markdown("#### Por Vicerrectoría")
    st.caption("💡 Clic en una barra para filtrar.")
    if "Vicerrectoria" in df_ui.columns:
        fig_v = _fig_barras_nivel(df_ui, "Vicerrectoria")
        ev_v  = st.plotly_chart(fig_v, use_container_width=True,
                                on_select="rerun", key="rc_vicerr_chart")
        if ev_v.selection and ev_v.selection.get("points"):
            clicked_v = ev_v.selection["points"][0].get("y")
            if clicked_v != st.session_state.get(_key_vicerr):
                st.session_state[_key_vicerr] = clicked_v
                st.rerun()
    else:
        st.info("No hay columna Vicerrectoría disponible (revisa el mapeo de procesos).")

st.markdown("---")

# ── Gráfico Por Proceso ───────────────────────────────────────────────────────
st.markdown("#### Por Proceso")
st.caption("💡 Clic en una barra para filtrar la tabla.")
if "Proceso" in df_ui.columns:
    fig_p = _fig_barras_nivel(df_ui, "Proceso")
    ev_p  = st.plotly_chart(fig_p, use_container_width=True,
                            on_select="rerun", key="rc_proceso_chart")
    if ev_p.selection and ev_p.selection.get("points"):
        clicked_p = ev_p.selection["points"][0].get("y")
        if clicked_p != st.session_state.get(_key_proc):
            st.session_state[_key_proc] = clicked_p
            st.rerun()

st.markdown("---")

# ── Tabla de detalle ──────────────────────────────────────────────────────────
if sel_proc_g:
    st.markdown(f"#### Detalle — *{sel_proc_g}*")
elif sel_vicerr:
    st.markdown(f"#### Detalle — *{sel_vicerr}*")
else:
    st.markdown("#### Detalle de Indicadores")

COLS_TABLA = [
    "Id", "Indicador", "Nivel de cumplimiento", "Cumplimiento",
    "Resultado", "Meta", "Fecha reporte",
    "Vicerrectoria", "Area", "Proceso", "Subproceso",
    "Clasificacion", "Sentido", "Periodicidad",
]
cols_show = [c for c in COLS_TABLA if c in df_fil.columns]
df_tabla  = df_fil[cols_show].copy()

col_cfg = {
    "Indicador":              st.column_config.TextColumn("Indicador", width="large"),
    "Nivel de cumplimiento":  st.column_config.TextColumn("Nivel de cumplimiento", width="medium"),
    "Cumplimiento":           st.column_config.TextColumn("Cumplimiento", width="small"),
    "Resultado":              st.column_config.TextColumn("Resultado",    width="small"),
    "Meta":                   st.column_config.TextColumn("Meta",         width="small"),
}

st.dataframe(
    df_tabla.style.apply(_estilo_nivel, axis=1),
    use_container_width=True, hide_index=True,
    column_config=col_cfg,
)

st.download_button(
    "📥 Exportar Excel",
    data=exportar_excel(df_tabla, "Cumplimiento"),
    file_name="reporte_cumplimiento.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="exp_cumplimiento",
)
