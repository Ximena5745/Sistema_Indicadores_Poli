"""
services/ficha_pdf/ — Technical sheet PDF generator

Refactorización PHASE 2 (395L → 3 modules):
  - utils.py: Color palette and formatting utilities (40L)
  - charts.py: Historical chart PNG rendering (100L)
  - builder.py: PDF document construction (245L)

Responsibility unique per module:
  - utils: Define constants and basic formatting helpers
  - charts: Generate Plotly-based charts as PNG images
  - builder: Orchestrate PDF document construction

Features:
  - Full-featured technical sheet PDF with charts, KPIs, identity card
  - Kaleido-based chart rendering (with graceful degradation)
  - Responsive table layout with custom styling
  - Historical data tracking and trend visualization
  - Professional institutional color palette

Usage:
    from services.ficha_pdf import build_ficha_pdf

    pdf_bytes = build_ficha_pdf(
        ind_data=indicator_row,
        hist=historical_df,
        tendencia_label="Estable",
        tendencia_icon="→"
    )
    
    # Download with Streamlit
    st.download_button("Descargar PDF", pdf_bytes, file_name="ficha.pdf")
"""

from .builder import build_ficha_pdf

__all__ = ["build_ficha_pdf"]
