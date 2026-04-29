import streamlit as st
import pandas as pd


def format_meta_pdi(meta_value, meta_signo="", decimales=1):
    """
    Formatea la meta PDI en texto compacto y tolerante a valores faltantes.
    """
    if pd.isna(meta_value):
        return "—"

    try:
        d = int(decimales) if decimales is not None and not pd.isna(decimales) else 1
    except Exception:
        d = 1

    try:
        valor = float(meta_value)
        txt_valor = f"{valor:.{max(0, d)}f}"
        if txt_valor.endswith(".0"):
            txt_valor = txt_valor[:-2]
    except Exception:
        txt_valor = str(meta_value).strip()

    signo = str(meta_signo or "").strip()
    return f"{txt_valor} {signo}".strip()

def inject_cmi_premium_css():
    """
    Inyecta estilos CSS globales para mejorar la interfaz por defecto de Streamlit.
    Aplica fuentes modernas, glassmorphism y estilización de tablas.
    """
    st.markdown("""
    <style>
        /* Tipografía general */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* Ocultar botones de anclaje de encabezados para un look más limpio */
        .css-15zrgzn {display: none}

        /* Estilización de botones para que parezcan tarjetas interactivas */
        .stButton > button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        /* Mejorar tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #f8f9fa;
            padding: 5px 10px;
            border-radius: 10px;
            box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);
        }
        .stTabs [data-baseweb="tab"] {
            padding: 10px 20px;
            border-radius: 8px !important;
            font-weight: 500;
        }
        .stTabs [aria-selected="true"] {
            background-color: white !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            color: #1A3A5C !important;
        }

        /* Mejorar Acordeones (Expanders) */
        .streamlit-expanderHeader {
            font-size: 1.1rem;
            font-weight: 600;
            background-color: white;
            border-radius: 8px;
            border: 1px solid #E0E0E0;
            padding: 15px;
            transition: background-color 0.2s;
        }
        .streamlit-expanderHeader:hover {
            background-color: #F8F9FA;
        }
        
        /* Badges custom */
        .badge-peligro,
        .badge-alerta,
        .badge-cump,
        .badge-sobre,
        .badge-default {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 5px 12px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }
        .badge-peligro { background-color: #D32F2F; color: white; }
        .badge-alerta { background-color: #FBAF17; color: #101827; }
        .badge-cump { background-color: #43A047; color: white; }
        .badge-sobre { background-color: #6699FF; color: white; }
        .badge-default { background-color: #E5E7EB; color: #101827; }

        .cmi-sparkbar-row {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 14px;
            width: 100%;
        }
        .cmi-sparkbar-label {
            flex: 0 0 45%;
            color: #0F172A;
            font-size: 0.95rem;
            font-weight: 600;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            min-width: 120px;
        }
        .cmi-sparkbar-bararea {
            flex: 0 0 55%;
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 200px;
        }
        .cmi-sparkbar-track {
            position: relative;
            flex: 1 1 auto;
            min-width: 0;
            height: 14px;
            background-color: #E5E7EB;
            border-radius: 999px;
            overflow: hidden;
            width: 100%;
        }
        .cmi-sparkbar-fill {
            height: 100%;
            border-radius: 999px;
            box-shadow: 0 2px 6px rgba(15,23,42,0.12);
        }
        .cmi-sparkbar-marker {
            position: absolute;
            top: -4px;
            left: calc(100% - 1px);
            width: 2px;
            height: 22px;
            background: rgba(15,23,42,0.65);
            border-radius: 2px;
        }
        .cmi-sparkbar-value {
            flex: 0 0 15%;
            min-width: 60px;
            text-align: right;
            color: #0F172A;
            font-weight: 700;
            white-space: nowrap;
        }
        .cmi-lineas-root {
            width: 100%;
            padding: 0 16px;
        }
        .cmi-lineas-section {
            margin: 0 0 18px 0;
            padding: 32px 44px 32px 44px;
            border-radius: 24px;
            background-color: rgba(255,255,255,0.02);
            box-shadow: 0 0 0 1px rgba(15,23,42,0.04);
        }
        .cmi-line-card {
            width: 100%;
            border-radius: 20px;
            padding: 22px 24px;
            margin-bottom: 18px;
            box-shadow: 0 18px 36px rgba(15,23,42,0.10);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            border: 1px solid rgba(255,255,255,0.08);
        }
        .cmi-line-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            width: 100%;
        }
        .cmi-line-card-body {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            margin-top: 12px;
        }
        .cmi-line-card-actions button {
            min-width: 100px;
            height: 42px;
            border-radius: 999px;
            font-weight: 700;
        }
        .cmi-line-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 24px 48px rgba(15,23,42,0.14);
        }
        .cmi-line-card-open {
            border-color: rgba(255,255,255,0.18);
        }
        .cmi-line-card-meta {
            color: rgba(255,255,255,0.92);
            font-size: 0.92rem;
            margin-top: 6px;
        }
        .cmi-line-pill {
            padding: 10px 18px;
            border-radius: 999px;
            background: rgba(255,255,255,0.18);
            color: #FFFFFF;
            font-weight: 700;
            min-width: 100px;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

def render_sparkbar(val, nivel, label=None):
    """
    Retorna HTML de una mini barra de progreso basado en el porcentaje de cumplimiento.
    """
    try:
        val_float = float(val)
    except:
        return str(val)
        
    fill_pct = max(0.0, min(100.0, val_float))
    
    if "Peligro" in str(nivel):
        color = "#D32F2F"
    elif "Alerta" in str(nivel):
        color = "#FBAF17"
    elif "Sobrecumplimiento" in str(nivel):
        color = "#6699FF"
    elif "Cumplimiento" in str(nivel):
        color = "#43A047"
    else:
        color = "#9E9E9E"

    label_html = f"<div class='cmi-sparkbar-label'>{label}</div>" if label else ""

    html = f"""
    <div class='cmi-sparkbar-row'>
        {label_html}
        <div class='cmi-sparkbar-bararea'>
            <div class='cmi-sparkbar-track'>
                <div class='cmi-sparkbar-fill' style='width: {fill_pct}%; background-color: {color};'></div>
                <div class='cmi-sparkbar-marker' title='100%'></div>
            </div>
            <div class='cmi-sparkbar-value'>{val_float:.1f}%</div>
        </div>
    </div>
    """
    return html

def format_nivel_badge(nivel):
    """
    Retorna HTML para un badge visual dependiendo del nivel.
    """
    n_str = str(nivel)
    if "Peligro" in n_str:
        return f'<span class="badge-peligro">Peligro</span>'
    elif "Alerta" in n_str:
        return f'<span class="badge-alerta">Alerta</span>'
    elif "Sobrecumplimiento" in n_str:
        return f'<span class="badge-sobre">Sobrecumplimiento</span>'
    elif "Cumplimiento" in n_str:
        return f'<span class="badge-cump">Cumplimiento</span>'
    else:
        return f'<span style="background-color: #E0E0E0; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;">{n_str}</span>'
