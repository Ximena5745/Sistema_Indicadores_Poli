"""CSS and styling functions for resumen_general page."""

import streamlit as st


def _inject_dashboard_styles() -> None:
    """Inject custom CSS for dashboard styling."""
    css = """
    <style>
    /* Header styling */
    .rg-header {
        background: linear-gradient(135deg, #0F385A 0%, #1A5F7A 100%);
        color: #FFFFFF;
        padding: 1.6rem;
        border-radius: 14px;
        margin-bottom: 1.6rem;
        box-shadow: 0 4px 20px rgba(15, 56, 90, 0.15);
    }
    
    .rg-header h1 {
        margin: 0;
        font-size: 1.9rem;
        font-weight: 700;
    }
    
    .rg-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 0.95rem;
    }
    
    /* Panel container */
    .rg-panel {
        background: #F8FAFC;
        padding: 1.6rem;
        border-radius: 14px;
        border: 1px solid #E2E8F0;
        margin-bottom: 1.6rem;
    }
    
    /* Metric card */
    .rg-card {
        border-left: 4px solid #0B5FFF;
        border-radius: 8px;
        padding: 1rem;
        background: #FFFFFF;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        margin-bottom: 0.8rem;
    }
    
    /* Chip (small metric) */
    .rg-chip {
        display: inline-block;
        padding: 0.7rem 1.2rem;
        border-radius: 8px;
        background-color: #0B5FFF;
        color: #FFFFFF;
        font-weight: 600;
        font-size: 0.85rem;
        margin-right: 0.6rem;
        margin-bottom: 0.6rem;
        box-shadow: 0 2px 4px rgba(11, 95, 255, 0.2);
    }
    
    /* IA Narrative */
    .rg-ia {
        background: #FFF7ED;
        border-left: 4px solid #F97316;
        padding: 1.2rem;
        border-radius: 8px;
        margin-bottom: 1.2rem;
    }
    
    .rg-ia h4 {
        margin: 0 0 0.6rem 0;
        color: #EA580C;
        font-size: 0.95rem;
        font-weight: 600;
    }
    
    .rg-ia p {
        margin: 0.4rem 0;
        font-size: 0.9rem;
        line-height: 1.5;
        color: #334155;
    }
    
    /* Variation table */
    .rg-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
    }
    
    .rg-table th {
        background-color: #E2E8F0;
        padding: 0.8rem;
        text-align: left;
        font-weight: 600;
        border-bottom: 2px solid #CBD5E1;
    }
    
    .rg-table td {
        padding: 0.7rem 0.8rem;
        border-bottom: 1px solid #E2E8F0;
    }
    
    .rg-table tr:hover {
        background-color: #F8FAFC;
    }
    
    /* Process card */
    .rg-process-card {
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        background: #FFFFFF;
        transition: all 0.2s ease;
    }
    
    .rg-process-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border-color: #CBD5E1;
    }
    
    .rg-process-card-title {
        font-weight: 600;
        font-size: 1rem;
        margin-bottom: 0.5rem;
    }
    
    /* Badge styling */
    .rg-badge {
        display: inline-block;
        padding: 0.3rem 0.6rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 0 0.2rem;
    }
    
    /* Compliance bar */
    .rg-compliance-bar {
        display: flex;
        height: 20px;
        border-radius: 4px;
        overflow: hidden;
        margin: 0.5rem 0;
        background-color: #E2E8F0;
    }
    
    .rg-compliance-segment {
        height: 100%;
        transition: opacity 0.2s ease;
    }
    
    .rg-compliance-segment:hover {
        opacity: 0.8;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
