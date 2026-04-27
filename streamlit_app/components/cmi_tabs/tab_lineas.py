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

def _render_subtab_resumen(df_linea, linea, color):
    col1, col2, col3 = st.columns(3)
    cump = df_linea["cumplimiento_pct"].mean()
    if pd.isna(cump): cump = 0
    n_ind = len(df_linea)
    n_obj = df_linea["Objetivo"].nunique()
    
    # HTML cards for subtab
    st.markdown(f"""
    <div style="display: flex; gap: 15px; margin-bottom: 20px;">
        <div style="flex: 1; background-color: #F8F9FA; border-top: 4px solid {color}; padding: 15px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <p style="margin: 0; font-size: 0.9rem; color: #555;">Cumplimiento Promedio</p>
            <h3 style="margin: 0; color: {color};">{cump:.1f}%</h3>
        </div>
        <div style="flex: 1; background-color: #F8F9FA; border-top: 4px solid #1A3A5C; padding: 15px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <p style="margin: 0; font-size: 0.9rem; color: #555;">Objetivos Estratégicos</p>
            <h3 style="margin: 0; color: #1A3A5C;">{n_obj}</h3>
        </div>
        <div style="flex: 1; background-color: #F8F9FA; border-top: 4px solid #43A047; padding: 15px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <p style="margin: 0; font-size: 0.9rem; color: #555;">Total Indicadores PDI</p>
            <h3 style="margin: 0; color: #43A047;">{n_ind}</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sunburst Chart for this Line
    df_sunburst = df_linea.copy()
    df_sunburst['Objetivo'] = df_sunburst['Objetivo'].fillna("Sin Objetivo")
    df_sunburst['Indicador'] = df_sunburst['Indicador'].fillna("Sin Nombre")
    
    fig_sunburst = px.sunburst(
        df_sunburst,
        path=['Objetivo', 'Indicador'],
        color_discrete_sequence=[color, "#E1E1E1"],
        maxdepth=2,
        title=f"Distribución de Objetivos - {linea}"
    )
    fig_sunburst.update_layout(margin=dict(t=30, l=10, r=10, b=10), height=300)
    st.plotly_chart(fig_sunburst, use_container_width=True, key=f"sunburst_{linea}")

def _render_subtab_objetivos(df_linea, linea, pdi_catalog=None):

    st.markdown(f"**Estructura jerárquica de Objetivos, Metas e Indicadores para {linea}**")
    meta_cat = _meta_catalog_for_objetivos(pdi_catalog)
    objetivos = sorted(df_linea['Objetivo'].dropna().unique().tolist())
    for obj in objetivos:
        with st.expander(f"🎯 {obj}"):
            df_obj = df_linea[df_linea['Objetivo'] == obj].copy()
            metas = []
            if not meta_cat.empty:
                obj_key = _normalize_linea_key(obj)
                metas = meta_cat[meta_cat['_obj_key'] == obj_key]['Meta_Estrategica'].dropna().unique().tolist()
            if metas:
                for meta in metas:
                    with st.expander(f"🏆 Meta Estratégica: {meta}"):
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
    # Enriquecer y formatear columnas
    if "Meta" in df.columns:
        meta_signo = (
            df["Meta_Signo"] if "Meta_Signo" in df.columns else pd.Series([""] * len(df), index=df.index)
        )
        decimales = (
            df["Decimales"] if "Decimales" in df.columns else pd.Series([1] * len(df), index=df.index)
        )
        df["Meta"] = [format_meta_pdi(m, s, d) for m, s, d in zip(df["Meta"], meta_signo, decimales)]
    if "cumplimiento_pct" in df.columns and "Nivel de cumplimiento" in df.columns:
        df["Cumplimiento %"] = df.apply(lambda row: render_sparkbar(row["cumplimiento_pct"], row["Nivel de cumplimiento"]), axis=1)
        df["Estado"] = df["Nivel de cumplimiento"].apply(format_nivel_badge)
        df = df.drop(columns=["cumplimiento_pct", "Nivel de cumplimiento"])
    ordered_cols = [
        "Id", "Indicador", "Meta", "Ejecucion", "Cumplimiento %", "Estado"
    ]
    cols_presentes = [c for c in ordered_cols if c in df.columns]
    extras = [c for c in df.columns if c not in cols_presentes]
    df = df[cols_presentes + extras]
    html = df.to_html(escape=False, index=False, classes='table table-hover', border=0)
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
            <h5 style='margin-top: 0; color: #1A3A5C;'>🧠 Insights y Directrices Estratégicas</h5>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(ai_resp)
    else:
        st.info("El análisis automatizado con IA no está disponible en este momento (Falta configurar ANTHROPIC_API_KEY).")

def render_tab_lineas(df, pdi_catalog=None):
    st.markdown("### Líneas Estratégicas y Objetivos")

        # FICHA UNIFICADA Y COMPACTA
        ficha_html = f'''
        <div class="linea-accordion-row{expanded_class}{target_class}" style="background:{gradient_bg}; border-left:6px solid {color}; min-height:{min_h}px; display:flex;align-items:center;gap:18px;box-sizing:border-box;">
            <div style="display:flex;align-items:center;gap:12px;flex:1;">
                <span class="linea-dot" style="background:{color};"></span>
                <span class="linea-title">{linea}</span>
                <span class="linea-meta">{n_ind} indicadores • {n_obj} objetivos • {n_meta} metas</span>
            </div>
            <div style="flex-shrink:0;">
                <span class="linea-pill" style="background:{color}; color:#fff; border:none; box-shadow:0 2px 6px rgba(0,0,0,0.08); padding:6px 18px; border-radius:999px; font-weight:700; font-size:1.1rem;">{cump_val:.1f}%</span>
            </div>
            <form method="post" style="margin:0;display:inline;">
                <button type="submit" name="toggle_linea" value="{_normalize_linea_key(linea)}" style="background:#fff;border:1.5px solid #e0e6ef;border-radius:12px;padding:8px 18px;font-size:1.2rem;font-weight:700;box-shadow:0 2px 8px rgba(0,0,0,0.04);cursor:pointer;transition:background 0.15s;">{arrow_symbol}</button>
            </form>
        </div>
        '''
        st.markdown(ficha_html, unsafe_allow_html=True)

        # Manejo del botón acordeón (usando session_state para mantener compatibilidad con Streamlit)
        import streamlit as _st
        if _st.session_state.get('toggle_linea') == _normalize_linea_key(linea):
            if is_expanded:
                st.session_state["cmi_linea_open"] = ""
            else:
                st.session_state["cmi_linea_open"] = str(linea)
            st.session_state['toggle_linea'] = None
            st.rerun()

        # Panel expandido
    }
    @keyframes lineaFocusPulse {
        0% { box-shadow: 0 0 0 0 rgba(79,142,247,0.35), 0 7px 16px rgba(26,58,92,0.14); }
        100% { box-shadow: 0 0 0 3px rgba(79,142,247,0.16), 0 7px 16px rgba(26,58,92,0.14); }
    }
    .linea-accordion-left {
        display: flex;
        align-items: center;
        gap: 9px;
    }
    .linea-dot {
        width: 11px;
        height: 11px;
        border-radius: 999px;
        display: inline-block;
    }
    .linea-title {
        font-weight: 700;
        color: #1A3A5C;
        font-size: 20px;
        line-height: 1.1;
        letter-spacing: 0.1px;
    }
    .linea-meta {
        color: #4B5563;
        font-size: 12.5px;
        font-weight: 600;
        margin-left: 8px;
    }
    .linea-pill {
        display: inline-block;
        min-width: 94px;
        text-align: center;
        padding: 6px 12px;
        border-radius: 999px;
        font-weight: 700;
        font-size: 16px;
        border: 1px solid #D7E7D9;
        background: #ECF8EE;
        color: #2E7D32;
    }
    .linea-panel {
        border: 1px solid #DEE8F4;
        border-top: 0;
        background: #FFFFFF;
        border-radius: 0 0 14px 14px;
        padding: 16px 18px 14px;
        margin-top: -10px;
        margin-bottom: 14px;
    }
    .meta-estrategica-chip {
        display: inline-block;
        max-width: 380px;
        padding: 4px 10px;
        border-radius: 999px;
        border: 1px solid #C8D8EB;
        background: #EEF4FD;
        color: #1F3550;
        font-weight: 700;
        font-size: 12px;
        line-height: 1.25;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        vertical-align: middle;
    }
    .meta-header {
        background: #F1F8FF;
        color: #1A3A5C;
        padding: 10px;
        border-bottom: 2px solid #C9E0FB;
        font-weight: 800;
    }
    .table td .meta-estrategica-chip { display: inline-block; }
    /* Subtabs integradas: fondo sutil que conecta con header, tab activo con borde superior visible */
    .linea-panel .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: rgba(240,246,255,0.35);
        border: none;
        border-radius: 12px;
        padding: 8px;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.6);
    }
    .linea-panel .stTabs [data-baseweb="tab"] {
        height: 40px;
        padding: 0 14px;
        border-radius: 9px;
        color: #475569;
        font-weight: 700;
        background: transparent;
        border: none;
        transition: all 0.18s ease;
    }
    .linea-panel .stTabs [aria-selected="true"] {
        color: #1A3A5C !important;
        background: #FFFFFF !important;
        border-top: 3px solid #8FAFD1 !important;
        box-shadow: 0 2px 6px rgba(26,58,92,0.08);
        transform: translateY(-2px);
    }
    @media (max-width: 1200px) {
        .linea-title {
            font-size: 18px;
        }
        .linea-meta {
            font-size: 12px;
        }
        .linea-panel {
            padding: 14px 14px 12px;
        }
        .linea-panel .stTabs [data-baseweb="tab"] {
            height: 36px;
            padding: 0 10px;
            font-size: 13px;
        }
        .meta-estrategica-chip {
            max-width: 260px;
        }
    }
    @media (max-width: 768px) {
        .linea-accordion-row {
            min-height: 58px;
            padding: 8px 10px;
            margin-bottom: 10px;
        }
        .linea-title {
            font-size: 16px;
        }
        .linea-meta {
            display: block;
            margin-left: 0;
            margin-top: 4px;
            font-size: 11.5px;
        }
        .linea-pill {
            min-width: 80px;
            font-size: 14px;
            padding: 5px 10px;
        }
        .linea-panel {
            padding: 12px 10px 10px;
        }
        .linea-panel .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
            padding: 4px;
        }
        .linea-panel .stTabs [data-baseweb="tab"] {
            height: 34px;
            padding: 0 8px;
            font-size: 12px;
        }
        .meta-estrategica-chip {
            max-width: 200px;
            font-size: 11px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    lineas = sorted([l for l in df["Linea"].dropna().unique() if str(l).strip()])

    linea_target = st.session_state.get("cmi_tab_linea_expand", None)
    linea_open = st.session_state.get("cmi_linea_open", None)
    if linea_target and not linea_open:
        linea_open = linea_target
        st.session_state["cmi_linea_open"] = linea_open

    for linea in lineas:
        df_linea = df[df["Linea"] == linea].copy()
        cump_mean = df_linea["cumplimiento_pct"].mean()
        cump_val = float(cump_mean) if pd.notna(cump_mean) else 0.0
        color = linea_color(linea)
        n_ind = len(df_linea)
        n_obj = int(df_linea["Objetivo"].nunique()) if "Objetivo" in df_linea.columns else 0
        n_meta = 0
        if pdi_catalog is not None and not getattr(pdi_catalog, "empty", True):
            if all(c in pdi_catalog.columns for c in ["Linea", "Meta_Estrategica"]):
                metas_linea = pdi_catalog[pdi_catalog["Linea"].astype(str).str.strip() == str(linea).strip()]["Meta_Estrategica"]
                n_meta = int(metas_linea.astype(str).str.strip().replace("", pd.NA).dropna().nunique())

        is_expanded = _normalize_linea_key(linea) == _normalize_linea_key(linea_open)
        is_target = bool(linea_target) and (_normalize_linea_key(linea) == _normalize_linea_key(linea_target))
        arrow_symbol = "▼" if is_expanded else "▶"
        row_bg = _hex_to_rgba(color, 0.14 if is_expanded else 0.11)
        target_class = " target-focus" if is_target else ""
        expanded_class = " expanded" if is_expanded else ""

        # gradiente suave usando color de la línea para mayor presencia
        gradient_bg = f"linear-gradient(90deg, {_hex_to_rgba(color, 0.06)}, {_hex_to_rgba(color, 0.02)})"
        min_h = 72

        st.markdown(
            f'<div class="linea-accordion-row{expanded_class}{target_class}" style="background:{gradient_bg}; border-left:6px solid {color}; min-height:{min_h}px;">',
            unsafe_allow_html=True,
        )
        c_left, c_mid, c_btn = st.columns([8.2, 1.6, 0.8])
        with c_left:
            st.markdown(
                f"""
                <div class="linea-accordion-left">
                    <span class="linea-dot" style="background:{color};"></span>
                    <span class="linea-title">{linea}</span>
                    <span class="linea-meta">{n_ind} indicadores • {n_obj} objetivos • {n_meta} metas</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c_mid:
            pill_bg = color
            pill_style = f'background:{pill_bg}; color: #ffffff; border: none; box-shadow: 0 2px 6px rgba(0,0,0,0.08); padding:6px 12px; border-radius:999px; font-weight:700;'
            st.markdown(f'<span class="linea-pill" style="{pill_style}">{cump_val:.1f}%</span>', unsafe_allow_html=True)
        with c_btn:
            if st.button(arrow_symbol, key=f"toggle_linea_{_normalize_linea_key(linea)}", use_container_width=True):
                if is_expanded:
                    st.session_state["cmi_linea_open"] = ""
                else:
                    st.session_state["cmi_linea_open"] = str(linea)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        if is_expanded:
            st.markdown(f'<div class="linea-panel" style="border-top:3px solid {color};">', unsafe_allow_html=True)
            subtabs = st.tabs(["Resumen", "Objetivos, Metas e Indicadores", "Análisis"])
            with subtabs[0]:
                _render_subtab_resumen(df_linea, linea, color)
            with subtabs[1]:
                _render_subtab_objetivos(df_linea, linea, pdi_catalog=pdi_catalog)
            with subtabs[2]:
                _render_subtab_analisis(df_linea, linea, color)
            st.markdown("</div>", unsafe_allow_html=True)
                
