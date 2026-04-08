"""Página Nivel 3: Tablero Estratégico Operativo — integrada en la navegación principal."""
import streamlit as st

try:
    from scripts.nivel3.ui import main as run_nivel3_ui
except Exception as e:
    run_nivel3_ui = None
    _import_error = e

if run_nivel3_ui is None:
    st.error("No fue posible cargar la vista Tablero Estratégico Operativo. Revisa los logs de importación.")
    st.exception(_import_error)
else:
    run_nivel3_ui()
