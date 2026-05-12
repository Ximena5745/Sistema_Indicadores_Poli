#!/usr/bin/env python
"""Debug: Ver qué retorna preparar_pdi_con_cierre para Proyectos"""

from services.strategic_indicators import preparar_pdi_con_cierre
from services.cmi_filters import load_cmi_worksheet
import pandas as pd

print("="*70)
print("VERIFICAR: preparar_pdi_con_cierre() para Proyectos")
print("="*70)

# Simular lo que ocurre en línea 2678-2693
year_estrategico = 2025
prev_year_e = year_estrategico - 1

print(f"\n1. Cargando preparar_pdi_con_cierre({prev_year_e}, 12):")
prev_df = preparar_pdi_con_cierre(prev_year_e, 12)

if prev_df is not None and not prev_df.empty:
    print(f"   Shape: {prev_df.shape}")
    print(f"   Columnas: {len(prev_df.columns)}")
    print(f"   ¿Duplicadas? {prev_df.columns.duplicated().any()}")
    if prev_df.columns.duplicated().any():
        print(f"   DUPLICADOS: {prev_df.columns[prev_df.columns.duplicated()].tolist()}")
    print(f"   Columnas: {prev_df.columns.tolist()}")
    
    # Filtrar por Proyectos
    ids_proy = set(str(int(x)) if isinstance(x, float) else str(x) for x in load_cmi_worksheet()[load_cmi_worksheet()['Proyecto'] == 1]['Id'].dropna())
    
    print(f"\n2. Después de filtrar por proyectos:")
    if "Id" in prev_df.columns:
        prev_df_filtered = prev_df[prev_df["Id"].astype(str).isin(ids_proy)].copy()
        print(f"   Shape: {prev_df_filtered.shape}")
        print(f"   Columnas: {len(prev_df_filtered.columns)}")
        print(f"   ¿Duplicadas? {prev_df_filtered.columns.duplicated().any()}")
        if prev_df_filtered.columns.duplicated().any():
            print(f"   DUPLICADOS: {prev_df_filtered.columns[prev_df_filtered.duplicated()].tolist()}")
    else:
        print("   No tiene columna 'Id'")
        print(f"   Columnas: {prev_df.columns.tolist()[:10]}")
else:
    print("   DataFrame vacío o None")

print("\n" + "="*70)
