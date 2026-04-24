import pandas as pd
import sys
sys.path.insert(0, r'C:\Users\ximen\OneDrive\Proyectos_DS\Sistema_Indicadores_Poli')

from services.strategic_indicators import load_cierres, load_worksheet_flags
from streamlit_app.pages.resumen_general import _get_proyectos_ids

print("=== LINEAS EN WORKSHEET FLAGS PARA PROYECTOS ===\n")

# Cargar worksheet flags
base = load_worksheet_flags()
proy_base = base[base["Proyecto"] == 1][["Id", "Linea"]].drop_duplicates()

print(f"Proyectos marcados en CMI: {len(proy_base)}")
print("\nLíneas分布:")
print(proy_base.groupby("Linea").size())

print("\n\nDetalles:")
print(proy_base.to_string())