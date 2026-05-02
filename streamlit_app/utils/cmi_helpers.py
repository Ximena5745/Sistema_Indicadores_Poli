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


def linea_icon_svg(linea: str, size: int = 28) -> str:
    """Retorna un SVG inline representativo para cada línea estratégica.

    Iconos basados en Heroicons / Material paths (licencia MIT).
    Colores oficiales del sistema de diseño institucional.
    No utiliza emojis.
    """
    import unicodedata as _ud

    txt = str(linea or "").strip().lower()
    txt = "".join(
        ch for ch in _ud.normalize("NFD", txt) if _ud.category(ch) != "Mn"
    )
    color = linea_color(linea)

    def _svg(path: str, viewbox: str = "0 0 24 24") -> str:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            f'viewBox="{viewbox}" fill="none" stroke="{color}" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
            f'{path}</svg>'
        )

    # Calidad — círculo con marca de verificación (award / check)
    if "calidad" in txt:
        return _svg(
            '<circle cx="12" cy="8" r="6"/>'
            '<path d="M9 12l2 2 4-4"/>'
            '<path d="M8.5 14.5L6 22l6-3 6 3-2.5-7.5"/>'
        )
    # Expansión — flecha hacia arriba en círculo / cohete
    if "expansi" in txt:
        return _svg(
            '<path d="M12 2C8 8 6 14 12 22c6-8 4-14 0-20z"/>'
            '<circle cx="12" cy="12" r="2" fill="' + color + '" stroke="none"/>'
            '<path d="M8 20c-2 0-4-2-4-4s1.5-3 3-3"/>'
            '<path d="M16 20c2 0 4-2 4-4s-1.5-3-3-3"/>'
        )
    # Experiencia — estrella / usuario con corazón
    if "experien" in txt:
        return _svg(
            '<path d="M12 2l2.09 6.26H21l-5.45 3.97L17.18 18 12 14.27 6.82 18l1.63-5.77L3 8.26h6.91z"/>'
        )
    # Sostenibilidad — hoja / reciclaje
    if "sostenib" in txt or "sustentab" in txt:
        return _svg(
            '<path d="M12 2a10 10 0 0 1 0 20A10 10 0 0 1 12 2z"/>'
            '<path d="M8 12c0-3.31 2.69-6 6-6v6H8z" fill="' + color + '22" stroke="' + color + '"/>'
            '<path d="M14 12v6c-3.31 0-6-2.69-6-6"/>'
        )
    # Educación para toda la vida — libro abierto
    if "educaci" in txt or "toda la vida" in txt:
        return _svg(
            '<path d="M2 6s4-2 10-2 10 2 10 2v14s-4-2-10-2S2 20 2 20z"/>'
            '<line x1="12" y1="4" x2="12" y2="18"/>'
        )
    # Transformación organizacional — engranaje / flechas circulares
    if "transform" in txt:
        return _svg(
            '<path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83'
            'M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>'
            '<circle cx="12" cy="12" r="3"/>'
        )
    # Fallback — diamante
    return _svg('<path d="M12 2l10 10-10 10L2 12z"/>')
