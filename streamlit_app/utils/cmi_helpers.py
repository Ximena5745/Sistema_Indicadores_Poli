import pandas as pd
import streamlit as st
import unicodedata

def aplicar_filtros_globales(df, pdi_catalog, linea_sel, objetivo_sel, nombre_q):
    """
    Aplica los filtros de línea, objetivo y nombre al DataFrame de indicadores.
    """
    df_filtrado = df.copy()
    
    if linea_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Linea"] == linea_sel]
    
    if objetivo_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Objetivo"] == objetivo_sel]
        
    if nombre_q and nombre_q.strip():
        df_filtrado = df_filtrado[df_filtrado["Indicador"].astype(str).str.contains(nombre_q.strip(), case=False, na=False)]
        
    return df_filtrado

def calcular_kpis(df):
    """
    Calcula los KPIs principales del CMI Estratégico.
    """
    total = len(df)
    con_dato = int(df["cumplimiento_pct"].notna().sum())
    promedio = float(df["cumplimiento_pct"].mean()) if con_dato else 0.0
    
    if total > 0 and "Nivel de cumplimiento" in df.columns:
        top_nivel = df["Nivel de cumplimiento"].value_counts().idxmax()
    else:
        top_nivel = "Sin dato"
        
    n_lineas_vis = int(df["Linea"].nunique()) if "Linea" in df.columns else 0
    n_obj_vis = int(df["Objetivo"].nunique()) if "Objetivo" in df.columns else 0
    
    # Conteo por estados
    conteo_estados = {}
    if "Nivel de cumplimiento" in df.columns:
        conteo_estados = df["Nivel de cumplimiento"].value_counts().to_dict()
        
    return {
        "total": total,
        "con_dato": con_dato,
        "promedio": promedio,
        "top_nivel": top_nivel,
        "n_lineas_vis": n_lineas_vis,
        "n_obj_vis": n_obj_vis,
        "conteo_estados": conteo_estados
    }



def linea_color(linea: str) -> str:
    """Retorna el color oficial para una línea estratégica.
    
    Utiliza la fuente central de colores del sistema de diseño:
    - docs/core/04_Dashboard.md
    - streamlit_app/styles/design_system.py
    
    Mapeo de líneas estratégicas:
    - Expansión -> #FBAF17
    - Transformación organizacional -> #42F2F2
    - Calidad -> #EC0677
    - Experiencia -> #1FB2DE
    - Sostenibilidad -> #A6CE38
    - Educación para toda la vida -> #0F385A
    """
    try:
        from streamlit_app.styles.design_system import LINE_COLOR
        txt = str(linea or "").strip()
        
        # Normalizar: quitar acentos y convertir a minúsculas
        import unicodedata
        txt_normalized = txt.lower()
        txt_normalized = unicodedata.normalize("NFD", txt_normalized)
        txt_normalized = "".join(ch for ch in txt_normalized if unicodedata.category(ch) != "Mn")
        
        # Busqueda exacta primero
        for key, color in LINE_COLOR.items():
            key_clean = key.upper()
            txt_clean = txt_normalized.replace(" ", "_")
            if key_clean == txt_clean.upper():
                return color
        
        # Busqueda parcial después
        for key, color in LINE_COLOR.items():
            key_clean = key.lower().replace("í", "i").replace("á", "a").replace("é", "e").replace("ó", "o").replace("ú", "u")
            if key_clean in txt_normalized.replace(" ", "_"):
                return color
        
        return "#1A3A5C"  # Default: azul institucional
    except ImportError:
        # Fallback: colores hardcoded del proyecto
        txt = str(linea or "").strip().lower()
        import unicodedata
        txt = unicodedata.normalize("NFD", txt)
        txt = "".join(ch for ch in txt if unicodedata.category(ch) != "Mn")
        
        # Busqueda por palabras clave
        if "expansi" in txt:
            return "#FBAF17"
        if "transform" in txt:
            return "#42F2F2"
        if "calidad" in txt:
            return "#EC0677"
        if "experien" in txt:
            return "#1FB2DE"
        if "sostenib" in txt or "sustentab" in txt:
            return "#A6CE38"
        if "educaci" in txt or "toda la vida" in txt:
            return "#0F385A"
        return "#1A3A5C"
