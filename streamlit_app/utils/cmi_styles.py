import streamlit as st
import pandas as pd

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
        .badge-peligro {
            background-color: #D32F2F; color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;
        }
        .badge-alerta {
            background-color: #FBAF17; color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;
        }
        .badge-cump {
            background-color: #43A047; color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;
        }
        .badge-sobre {
            background-color: #1A3A5C; color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)

def render_sparkbar(val, nivel):
    """
    Retorna HTML de una mini barra de progreso basado en el porcentaje de cumplimiento.
    """
    try:
        val_float = float(val)
    except:
        return str(val)
        
    width = min(100, val_float)
    
    # Determinar color basado en el nivel si es string, si no, heurística básica
    if "Peligro" in str(nivel): color = "#D32F2F"
    elif "Alerta" in str(nivel): color = "#FBAF17"
    elif "Sobrecumplimiento" in str(nivel): color = "#1A3A5C"
    elif "Cumplimiento" in str(nivel): color = "#43A047"
    else: color = "#9E9E9E"

    html = f"""
    <div style="width: 100%; display: flex; align-items: center; justify-content: space-between;">
        <span style="min-width: 45px; font-weight: bold;">{val_float:.1f}%</span>
        <div style="flex-grow: 1; margin-left: 10px; background-color: #E0E0E0; height: 8px; border-radius: 4px; overflow: hidden;">
            <div style="width: {width}%; background-color: {color}; height: 100%;"></div>
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
        return f'<span class="badge-peligro">🔴 Peligro</span>'
    elif "Alerta" in n_str:
        return f'<span class="badge-alerta">🟡 Alerta</span>'
    elif "Sobrecumplimiento" in n_str:
        return f'<span class="badge-sobre">🔵 Sobrecumpl.</span>'
    elif "Cumplimiento" in n_str:
        return f'<span class="badge-cump">🟢 Cumple</span>'
    else:
        return f'<span style="background-color: #E0E0E0; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;">⚪ {n_str}</span>'
