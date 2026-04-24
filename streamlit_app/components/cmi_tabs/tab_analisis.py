import streamlit as st
import pandas as pd
import plotly.express as px
from services.strategic_indicators import load_cierres
from streamlit_app.utils.cmi_helpers import linea_color

def get_history_data(df_current):
    """
    Obtiene los últimos 6 periodos para los indicadores actuales.
    """
    cierres = load_cierres()
    if cierres.empty or df_current.empty:
        return pd.DataFrame()
        
    ids = df_current["Id"].unique()
    cierres_filtrados = cierres[cierres["Id"].isin(ids)].copy()
    
    # Crear un campo periodo: Anio-Mes
    cierres_filtrados["Periodo"] = cierres_filtrados["Anio"].astype(str) + "-" + cierres_filtrados["Mes"].astype(str).str.zfill(2)
    
    # Ordenar periodos
    periodos_ordenados = sorted(cierres_filtrados["Periodo"].unique())[-6:]
    cierres_filtrados = cierres_filtrados[cierres_filtrados["Periodo"].isin(periodos_ordenados)]
    
    # Añadir Línea a partir de df_current
    linea_map = df_current.set_index("Id")["Linea"].to_dict()
    cierres_filtrados["Linea"] = cierres_filtrados["Id"].map(linea_map)
    
    return cierres_filtrados, periodos_ordenados

def render_tab_analisis(df):
    st.markdown("### Análisis y Tendencias")
    
    hist_data, periodos = get_history_data(df)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Cumplimiento por Línea (Histórico)")
        if not hist_data.empty and "cumplimiento_pct" in hist_data.columns:
            linea_hist = hist_data.groupby(["Periodo", "Linea"])["cumplimiento_pct"].mean().reset_index()
            fig_line = px.line(
                linea_hist, 
                x="Periodo", 
                y="cumplimiento_pct", 
                color="Linea",
                color_discrete_map={l: linea_color(l) for l in linea_hist["Linea"].unique()},
                markers=True,
                title="Evolución del Cumplimiento Promedio"
            )
            fig_line.update_layout(margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("No hay suficientes datos históricos.")
            
    with col2:
        st.markdown("#### Indicadores en Peligro (Ranking)")
        if "Nivel de cumplimiento" in df.columns:
            peligro_df = df[df["Nivel de cumplimiento"] == "Peligro"].copy()
            if not peligro_df.empty and "cumplimiento_pct" in peligro_df.columns:
                peligro_df = peligro_df.sort_values("cumplimiento_pct", ascending=True).head(10)
                fig_bar = px.bar(
                    peligro_df,
                    x="cumplimiento_pct",
                    y="Indicador",
                    orientation='h',
                    title="Top 10 Indicadores con menor cumplimiento (Peligro)",
                    color_discrete_sequence=["#ef5350"]
                )
                fig_bar.update_layout(margin=dict(l=10, r=10, t=30, b=10), yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.success("¡Excelente! No hay indicadores en nivel de Peligro en este periodo.")
                
    st.markdown("#### Heatmap: Cumplimiento x Periodo")
    if not hist_data.empty and "cumplimiento_pct" in hist_data.columns:
        # Pivot para heatmap (solo tomamos el promedio por linea y periodo para que sea legible, o top 20 indicadores)
        heatmap_data = hist_data.groupby(["Linea", "Periodo"])["cumplimiento_pct"].mean().reset_index()
        heatmap_pivot = heatmap_data.pivot(index="Linea", columns="Periodo", values="cumplimiento_pct")
        
        fig_heat = px.imshow(
            heatmap_pivot,
            text_auto=".1f",
            aspect="auto",
            color_continuous_scale="RdYlGn",
            title="Mapa de Calor: Cumplimiento Promedio por Línea"
        )
        st.plotly_chart(fig_heat, use_container_width=True)
        
    # IA Narrativa
    st.markdown("""
    <div style="background-color: #F5F7FA; padding: 20px; border-radius: 10px; border-left: 5px solid #A6CE38; margin-top: 10px;">
        <h4 style="color: #A6CE38; margin-top: 0;">🧠 Recomendaciones Automáticas</h4>
        <ul style="color: #333; line-height: 1.5;">
            <li><b>Variabilidad:</b> Identifique las líneas con mayor fluctuación en el mapa de calor para estandarizar procesos.</li>
            <li><b>Foco:</b> Concentrar recursos en los indicadores listados en el ranking de Peligro.</li>
            <li><b>Tendencias:</b> Si una línea muestra 3 periodos consecutivos a la baja, se sugiere una auditoría preventiva.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
