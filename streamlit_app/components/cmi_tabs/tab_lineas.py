import hashlib
import html
import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata
from streamlit_app.utils.cmi_helpers import linea_color
from streamlit_app.components.cmi_tabs.modal_ficha import render_modal_ficha
from services.strategic_indicators import load_cierres
from streamlit_app.utils.cmi_styles import format_meta_pdi


def _normalize_linea_key(linea):
    txt = str(linea or "").strip().lower().replace("_", " ")
    txt = unicodedata.normalize("NFD", txt)
    return "".join(ch for ch in txt if unicodedata.category(ch) != "Mn")


def _key_for_linea(linea):
    normalized = _normalize_linea_key(linea)
    hashed = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:10]
    return f"{normalized}_{hashed}" if normalized else hashed


def _hex_to_rgba(hex_color, alpha=0.12):
    txt = str(hex_color or "").strip().lstrip("#")
    if len(txt) != 6:
        return f"rgba(26,58,92,{alpha})"
    try:
        r = int(txt[0:2], 16)
        g = int(txt[2:4], 16)
        b = int(txt[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    except Exception:
        return f"rgba(26,58,92,{alpha})"


def _contrast_text_color(hex_color):
    txt = str(hex_color or "").strip().lstrip("#")
    if len(txt) != 6:
        return "#FFFFFF"
    try:
        r = int(txt[0:2], 16)
        g = int(txt[2:4], 16)
        b = int(txt[4:6], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return "#111111" if brightness > 150 else "#FFFFFF"
    except Exception:
        return "#FFFFFF"


def _meta_catalog_for_objetivos(pdi_catalog):
    if pdi_catalog is None or getattr(pdi_catalog, "empty", True):
        return pd.DataFrame(columns=["_obj_key", "Meta_Estrategica"])

    cols = set(pdi_catalog.columns)
    if "Objetivo" not in cols or "Meta_Estrategica" not in cols:
        return pd.DataFrame(columns=["_obj_key", "Meta_Estrategica"])

    cat = pdi_catalog[["Objetivo", "Meta_Estrategica"]].copy()
    cat["_obj_key"] = cat["Objetivo"].apply(_normalize_linea_key)
    cat["Meta_Estrategica"] = cat["Meta_Estrategica"].astype(str).str.strip()
    cat = cat[(cat["_obj_key"] != "") & (cat["Meta_Estrategica"] != "")]
    cat = cat.drop_duplicates(subset=["_obj_key"], keep="first")
    return cat[["_obj_key", "Meta_Estrategica"]]


def _toggle_linea_state(state_key):
    st.session_state[state_key] = not st.session_state.get(state_key, False)


def _render_subtab_resumen(df_linea, linea, color):
    cump = df_linea["cumplimiento_pct"].mean() if "cumplimiento_pct" in df_linea.columns else 0
    if pd.isna(cump):
        cump = 0
    n_ind = len(df_linea)
    n_obj = df_linea["Objetivo"].nunique() if "Objetivo" in df_linea.columns else 0

    niveles = df_linea["Nivel de cumplimiento"].astype(str).str.strip() if "Nivel de cumplimiento" in df_linea.columns else pd.Series([""] * len(df_linea), index=df_linea.index)
    n_sobrecumplimiento = int((niveles == "Sobrecumplimiento").sum())
    n_cumplimiento = int((niveles == "Cumplimiento").sum())
    n_alerta = int((niveles == "Alerta").sum())
    n_riesgo = int((niveles == "Peligro").sum())

    metrics = [
        ("Cumplimiento Promedio", f"{cump:.1f}%", color),
        ("En Sobrecumplimiento", str(n_sobrecumplimiento), "#0F766E"),
        ("En Cumplimiento", str(n_cumplimiento), "#15803D"),
        ("En Alerta", str(n_alerta), "#F97316"),
        ("En Riesgo", str(n_riesgo), "#DC2626"),
        ("Total indicadores", str(n_ind), "#2563EB"),
    ]

    cols = st.columns(6)
    for idx, (title, value, border_color) in enumerate(metrics):
        with cols[idx]:
            st.markdown(
                f"""
                <div style='padding:18px; border-radius:16px; border:1px solid #E5E7EB; background:#FFFFFF; box-shadow:0 8px 20px rgba(15,23,42,0.06); margin-bottom:12px;'>
                    <div style='font-size:0.9rem; color:#475569; margin-bottom:10px;'>{title}</div>
                    <div style='font-size:2rem; font-weight:800; color:#111827; margin-bottom:0;'>{value}</div>
                    <div style='height:4px; width:40px; background:{border_color}; border-radius:999px; margin-top:14px;'></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if "Indicador" in df_linea.columns and "cumplimiento_pct" in df_linea.columns:
        df_ind = df_linea[["Indicador", "cumplimiento_pct", "Nivel de cumplimiento"]].dropna(subset=["Indicador"]).copy()
        if not df_ind.empty:
            df_ind["cumplimiento_pct"] = pd.to_numeric(df_ind["cumplimiento_pct"], errors="coerce")
            df_ind = df_ind.sort_values("cumplimiento_pct", ascending=False).head(6)

            st.markdown(
                "<div style='margin-top:18px; padding:18px; border-radius:18px; background:#F8FAFF; border:1px solid #E2E8F0;'>"
                "<div style='font-size:0.95rem; font-weight:700; color:#0F172A; margin-bottom:12px;'>Indicadores principales</div>"
                "</div>",
                unsafe_allow_html=True,
            )

            from streamlit_app.utils.cmi_styles import render_sparkbar
            for _, row in df_ind.iterrows():
                label = str(row["Indicador"])
                nivel = row.get("Nivel de cumplimiento", "")
                bar_html = render_sparkbar(row["cumplimiento_pct"], nivel, label=label)
                st.markdown(bar_html, unsafe_allow_html=True)

def _render_subtab_objetivos(df_linea, linea, pdi_catalog=None):

    st.markdown(f"**Estructura jerárquica de Objetivos, Metas e Indicadores para {linea}**")
    meta_cat = _meta_catalog_for_objetivos(pdi_catalog)
    objetivos = sorted(df_linea['Objetivo'].dropna().unique().tolist())
    for obj in objetivos:
        with st.expander(f"Objetivo estratégico: {obj}"):
            df_obj = df_linea[df_linea['Objetivo'] == obj].copy()
            metas = []
            if not meta_cat.empty:
                obj_key = _normalize_linea_key(obj)
                metas = meta_cat[meta_cat['_obj_key'] == obj_key]['Meta_Estrategica'].dropna().unique().tolist()
            if metas:
                for meta in metas:
                    with st.expander(f"Meta Estratégica: {meta}"):
                        df_meta = df_obj.copy()
                        # Filtrar por meta estratégica si hay columna en df_obj
                        if 'Meta_Estrategica' in df_meta.columns:
                            df_meta = df_meta[df_meta['Meta_Estrategica'] == meta]
                        # Mostrar tabla de indicadores
                        _render_tabla_indicadores(df_meta)
            else:
                # Si no hay metas estratégicas, mostrar todos los indicadores del objetivo
                _render_tabla_indicadores(df_obj)

def _render_tabla_indicadores(df):
    from streamlit_app.utils.cmi_styles import render_sparkbar, format_nivel_badge, format_meta_pdi
    if df.empty:
        st.info("No hay indicadores para mostrar.")
        return
    
    # Preparar solo las columnas solicitadas: Indicador, Proceso, Meta, Ejecución, Cumplimiento %, Estado
    df_work = df.copy()
    
    # Formatear Meta con signo si existe
    if "Meta" in df_work.columns:
        meta_signo = (
            df_work["Meta_Signo"] if "Meta_Signo" in df_work.columns else pd.Series([""] * len(df_work), index=df_work.index)
        )
        decimales = (
            df_work["Decimales"] if "Decimales" in df_work.columns else pd.Series([1] * len(df_work), index=df_work.index)
        )
        df_work["Meta"] = [format_meta_pdi(m, s, d) for m, s, d in zip(df_work["Meta"], meta_signo, decimales)]
    
    # Formatear Ejecución con signo si existe
    if "Ejecucion" in df_work.columns:
        ejec_signo = (
            df_work["Ejecucion_Signo"] if "Ejecucion_Signo" in df_work.columns else pd.Series([""] * len(df_work), index=df_work.index)
        )
        decimales_ejec = (
            df_work["Decimales_Ejecucion"] if "Decimales_Ejecucion" in df_work.columns else pd.Series([1] * len(df_work), index=df_work.index)
        )
        df_work["Ejecucion"] = [format_meta_pdi(e, s, d) for e, s, d in zip(df_work["Ejecucion"], ejec_signo, decimales_ejec)]
    
    # Crear columna Cumplimiento % y Estado
    if "cumplimiento_pct" in df_work.columns and "Nivel de cumplimiento" in df_work.columns:
        df_work["Cumplimiento %"] = df_work.apply(
            lambda row: render_sparkbar(row["cumplimiento_pct"], row["Nivel de cumplimiento"]), 
            axis=1
        )
        df_work["Estado"] = df_work["Nivel de cumplimiento"].apply(format_nivel_badge)
    
    # Seleccionar solo columnas solicitadas
    cols_solicitadas = [
        "Indicador", 
        "Proceso",  # Si existe
        "Meta", 
        "Ejecucion", 
        "Cumplimiento %", 
        "Estado"
    ]
    
    # Filtrar columnas que existen en el dataframe
    cols_presentes = [c for c in cols_solicitadas if c in df_work.columns]
    
    # Si no existe "Proceso", intentar usar "Subproceso" o similar
    if "Proceso" not in cols_presentes and "Subproceso" in df_work.columns:
        cols_presentes = ["Indicador", "Subproceso"] + [c for c in cols_presentes if c != "Indicador"]
    
    df_tabla = df_work[cols_presentes].copy()
    
    # Renderizar como tabla HTML simple
    html = df_tabla.to_html(escape=False, index=False, classes='table table-hover', border=0)
    html = html.replace('<th>', '<th style="text-align: left; background-color: #f8f9fa; padding: 10px; border-bottom: 2px solid #dee2e6;">')
    html = html.replace('<td>', '<td style="padding: 10px; border-bottom: 1px solid #e9ecef; vertical-align: middle;">')
    st.markdown(html, unsafe_allow_html=True)

@st.cache_data(ttl=3600, show_spinner=False)
def _get_ai_linea(linea, cump, n_ind, n_riesgo, df_json):
    from services.ai_analysis import analizar_linea_cmi
    return analizar_linea_cmi(linea, str(cump), n_ind, n_riesgo, df_json)

def _render_subtab_analisis(df_linea, linea, color):
    cierres = load_cierres()
    if not cierres.empty:
        ids = df_linea["Id"].unique()
        hist = cierres[cierres["Id"].isin(ids)].copy()
        
        if not hist.empty:
            hist["Periodo"] = hist["Anio"].astype(str) + "-" + hist["Mes"].astype(str).str.zfill(2)
            hist_agrupado = hist.groupby("Periodo")["cumplimiento_pct"].mean().reset_index()
            
            fig_hist = px.line(
                hist_agrupado, 
                x="Periodo", 
                y="cumplimiento_pct", 
                markers=True,
                title=f"Tendencia de Cumplimiento Histórico",
                color_discrete_sequence=[color]
            )
            fig_hist.update_layout(margin=dict(t=30, b=10, l=10, r=10), height=300)
            st.plotly_chart(fig_hist, use_container_width=True, key=f"hist_{linea}")
        else:
            st.info("No hay histórico para esta línea.")
    
    # Análisis IA Real
    st.markdown("#### Análisis Estratégico Automático")
    
    n_ind = len(df_linea)
    n_riesgo = len(df_linea[df_linea["Nivel de cumplimiento"].isin(["Peligro", "Alerta"])])
    cump_val = df_linea["cumplimiento_pct"].mean()
    if pd.isna(cump_val): cump_val = 0
    
    cols_ai = ["Indicador", "Objetivo", "Meta", "Ejecucion", "cumplimiento_pct", "Nivel de cumplimiento"]
    df_ai = df_linea[[c for c in cols_ai if c in df_linea.columns]].copy()
    tabla_json = df_ai.to_json(orient="records", force_ascii=False)
    
    with st.spinner("Generando análisis táctico automático..."):
        ai_resp = _get_ai_linea(linea, round(cump_val, 1), n_ind, n_riesgo, tabla_json)
        
    if ai_resp:
        st.markdown(f"""
        <div style='padding: 15px; background-color: #F8F9FA; border-left: 5px solid {color}; border-radius: 5px; margin-bottom: 20px;'>
            <h5 style='margin-top: 0; color: #1A3A5C;'><i class='fa-solid fa-brain' style='margin-right:8px;'></i>Insights y Directrices Estratégicas</h5>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(ai_resp)
    else:
        st.info("El análisis automatizado con IA no está disponible en este momento (Falta configurar ANTHROPIC_API_KEY).")

def render_tab_lineas(df, pdi_catalog=None):
    st.markdown("### Líneas Estratégicas y Objetivos")

    if "Linea_Estrategica" not in df.columns and "Linea" not in df.columns:
        st.error("No se encuentra la columna 'Linea_Estrategica' ni 'Linea' en los datos.")
        return

    linea_col = "Linea_Estrategica" if "Linea_Estrategica" in df.columns else "Linea"
    lineas = sorted([str(l).strip() for l in df[linea_col].dropna().unique() if str(l).strip()])

    if not lineas:
        st.info("No hay líneas estratégicas para mostrar.")
        return

    expanded_target_raw = st.session_state.get("cmi_tab_linea_expand", "")
    expanded_target = _normalize_linea_key(expanded_target_raw)
    expanded_applied_key = f"cmi_tab_linea_expand_applied_{expanded_target}"

    st.markdown("<div class='cmi-estrategico-lineas-root'>", unsafe_allow_html=True)
    st.markdown("<div class='cmi-estrategico-lineas-section'>", unsafe_allow_html=True)
    for linea in lineas:
        df_linea = df[df[linea_col] == linea].copy()
        color = linea_color(linea)
        n_ind = len(df_linea)
        n_obj = int(df_linea["Objetivo"].nunique()) if "Objetivo" in df_linea.columns else 0
        n_meta = 0
        if pdi_catalog is not None and not getattr(pdi_catalog, "empty", True):
            if "Meta_Estrategica" in pdi_catalog.columns and linea_col in pdi_catalog.columns:
                metas_linea = pdi_catalog[pdi_catalog[linea_col].astype(str).str.strip() == str(linea).strip()]["Meta_Estrategica"]
                n_meta = int(metas_linea.astype(str).str.strip().replace("", pd.NA).dropna().nunique())
        elif "Meta_Estrategica" in df_linea.columns:
            n_meta = int(df_linea["Meta_Estrategica"].astype(str).str.strip().replace("", pd.NA).dropna().nunique())

        cump_val = float(df_linea["cumplimiento_pct"].mean()) if "cumplimiento_pct" in df_linea.columns else 0.0
        if pd.isna(cump_val):
            cump_val = 0.0

        line_key_norm = _normalize_linea_key(linea)
        line_key = _key_for_linea(linea)
        state_key = f"cmi_linea_open_{line_key}"
        if state_key not in st.session_state:
            st.session_state[state_key] = False
        if expanded_target and line_key_norm == expanded_target and not st.session_state.get(expanded_applied_key, False):
            st.session_state[state_key] = True
            st.session_state[expanded_applied_key] = True
        is_expanded = st.session_state[state_key]
        display_linea = html.escape(str(linea).replace("_", " ") or "Línea")
        gradient_light = _hex_to_rgba(color, 0.98)
        gradient_mid = _hex_to_rgba(color, 0.76)
        gradient_soft = _hex_to_rgba(color, 0.40)
        open_class = " cmi-line-card-open" if is_expanded else ""
        header_html = (
            f"<div class='cmi-line-card{open_class}' style='background: linear-gradient(90deg, {gradient_light} 0%, {gradient_mid} 50%, {gradient_soft} 100%);'>"
            f"<div style='display:flex; justify-content:space-between; align-items:center; gap:18px;'>"
            f"<div style='display:flex; align-items:center; gap:16px; min-width:0;'>"
            f"<span style='width:12px; height:56px; border-radius:999px; background:{color}; display:inline-block;'></span>"
            f"<div style='min-width:0;'>"
            f"<div style='font-size:1.12rem; font-weight:800; color:#FFFFFF; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;'>{display_linea}</div>"
            f"<div class='cmi-line-card-meta'>{n_ind} indicadores · {n_obj} objetivos · {n_meta} metas</div>"
            f"</div>"
            f"</div>"
            f"<div style='display:flex; align-items:center; gap:12px;'>"
            f"<div class='cmi-line-pill'>{cump_val:.1f}%</div>"
            f"</div>"
            f"</div>"
            f"</div>"
        )

        cols = st.columns([0.88, 0.12])
        with cols[0]:
            st.markdown(header_html, unsafe_allow_html=True)
        with cols[1]:
            toggle_label = "Cerrar" if st.session_state[state_key] else "Ver"
            st.button(
                toggle_label,
                key=f"toggle_linea_{line_key}",
                on_click=_toggle_linea_state,
                args=(state_key,),
            )

        if is_expanded:
            st.markdown('<div style="border:1px solid #D9E5F2; border-radius:18px; padding:20px; margin-bottom:22px; background:#FFFFFF;">', unsafe_allow_html=True)
            subtabs = st.tabs(["Resumen", "Objetivos, Metas e Indicadores", "Análisis"])
            with subtabs[0]:
                _render_subtab_resumen(df_linea, linea, color)
            with subtabs[1]:
                _render_subtab_objetivos(df_linea, linea, pdi_catalog=pdi_catalog)
            with subtabs[2]:
                _render_subtab_analisis(df_linea, linea, color)
            st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

