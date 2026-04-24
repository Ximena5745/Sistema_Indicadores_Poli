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

def calcular_alertas(df):
    """
    Calcula las alertas para los indicadores (Severidad: Crítica, Alta, Media, Baja).
    Reglas sugeridas:
    - Crítica: Cumplimiento < 70% o Peligro
    - Alta: Caídas > 15pp o tendencia descendente fuerte
    - Media: Sin reporte
    - Baja: Alerta (70-85%)
    """
    alertas = []
    
    for _, row in df.iterrows():
        nivel = row.get("Nivel de cumplimiento", "")
        cump = row.get("cumplimiento_pct", 0)
        if pd.isna(cump):
            cump = 0
            
        nombre = row.get("Indicador", "Sin Nombre")
        linea = row.get("Linea", "Sin Línea")
        ejecucion = row.get("Ejecucion", "")
        meta = row.get("Meta", "")
        
        # Lógica de severidad
        if nivel == "Peligro" or cump < 70:
            severidad = "Crítica"
            tipo = "Bajo Desempeño"
            accion = "Revisar plan de acción urgente"
        elif nivel == "Alerta":
            severidad = "Media"
            tipo = "Desviación"
            accion = "Monitorear tendencia"
        elif pd.isna(row.get("cumplimiento_pct")) or nivel == "Pendiente de reporte":
            severidad = "Media"
            tipo = "Sin Dato"
            accion = "Solicitar reporte"
        else:
            continue # No hay alerta
            
        # Calcular brecha
        try:
            m = float(meta) if pd.notna(meta) else 0
            e = float(ejecucion) if pd.notna(ejecucion) else 0
            brecha = f"{e - m:+.1f}"
        except (ValueError, TypeError):
            brecha = "N/A"
            
        alertas.append({
            "Indicador": nombre,
            "Linea": linea,
            "Severidad": severidad,
            "Tipo": tipo,
            "Valor Actual": ejecucion,
            "Meta": meta,
            "Brecha": brecha,
            "Acción": accion,
            "Id": row.get("Id", "")
        })
        
    return pd.DataFrame(alertas)

def linea_color(linea: str) -> str:
    txt = str(linea or "").strip().lower()
    txt = unicodedata.normalize("NFD", txt)
    txt = "".join(ch for ch in txt if unicodedata.category(ch) != "Mn")
    if "expansi" in txt:
        return "#FBAF17"
    if "transform" in txt:
        return "#42F2F2"
    if "calidad" in txt:
        return "#EC0677"
    if "experien" in txt:
        return "#1FB2DE"
    if "sostenib" in txt:
        return "#A6CE38"
    if "educaci" in txt or "toda la vida" in txt:
        return "#0F385A"
    return "#1f4e79"
