"""Página wrapper para exponer el prototipo Nivel 3 dentro de la navegación de la app."""
import streamlit as st

try:
    from scripts.prototipo_nivel3 import main as run_prototipo
except Exception as e:
    run_prototipo = None
    _import_error = e

if run_prototipo is None:
    st.error("No fue posible cargar el prototipo Nivel 3. Revisa los logs de importación.")
    st.exception(_import_error)
else:
    run_prototipo()
