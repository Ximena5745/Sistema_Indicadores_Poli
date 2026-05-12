#!/usr/bin/env python
"""Debug: Verificar exactamente qué le llega a _compute_trends"""

from services.strategic_indicators import load_proyectos_consolidados, load_worksheet_flags, preparar_pdi_con_cierre
from services.cmi_filters import load_cmi_worksheet
import pandas as pd

print("="*70)
print("SIMULAR: _load_base_data_by_type + _compute_trends para Proyectos")
print("="*70)

# Simular lo que hace _load_base_data_by_type para categoría Proyectos
from services.strategic_indicators import load_proyectos_consolidados

pdi_proy = pd.DataFrame()
ids_proy_func = lambda: set(str(int(x)) if isinstance(x, float) else str(x) for x in load_cmi_worksheet()[load_cmi_worksheet()['Proyecto'] == 1]['Id'].dropna())
ids_proy = ids_proy_func()

if ids_proy:
    consolidado = load_proyectos_consolidados()
    
    if not consolidado.empty and "Id" in consolidado.columns:
        consolidado["Id"] = consolidado["Id"].astype(str)
        pdi_proy = consolidado[consolidado["Id"].isin(ids_proy)].copy()
        
        if not pdi_proy.empty and ("Linea" not in pdi_proy.columns or pdi_proy["Linea"].isna().all()):
            base = load_worksheet_flags()
            if not base.empty:
                base_norm = base.copy()
                base_norm["Id"] = base_norm["Id"].astype(str)
                merge_cols = [c for c in ["Linea", "Objetivo"] if c in base_norm.columns]
                if merge_cols:
                    base_to_merge = base_norm[["Id"] + merge_cols].drop_duplicates(subset=["Id"])
                    pdi_proy = pdi_proy.merge(base_to_merge, on="Id", how="left", suffixes=("", "_cmi"))
                    
                    for col in pdi_proy.columns:
                        if col.endswith("_cmi"):
                            base_col = col[:-4]
                            if base_col in pdi_proy.columns:
                                pdi_proy[base_col] = pdi_proy[base_col].fillna(pdi_proy[col])
                            pdi_proy = pdi_proy.drop(col, axis=1)
        
        pdi_proy = pdi_proy.sort_values("Id", na_position="last").drop_duplicates(subset=["Id"], keep="last")

print(f"\n1. pdi_proy (pdi_base_df) después de _load_base_data_by_type:")
print(f"   Filas: {len(pdi_proy)}")
print(f"   Columnas: {len(pdi_proy.columns)}")
print(f"   ¿Duplicadas? {pdi_proy.columns.duplicated().any()}")
if pdi_proy.columns.duplicated().any():
    print(f"   Duplicados: {pdi_proy.columns[pdi_proy.columns.duplicated()].tolist()}")

# Simular _compute_trends
print(f"\n2. Simulando _compute_trends():")

current = pdi_proy.copy()
print(f"   Input current shape: {current.shape}")
print(f"   Input current duplicated? {current.columns.duplicated().any()}")

# Línea 1256-1257 de _compute_trends
current = current.loc[:, ~current.columns.duplicated()].copy()
previous = pd.DataFrame()  # Simulamos sin datos previos

print(f"   Después de limpiar duplicados en current: {current.shape}")
print(f"   Columnas duplicadas ahora? {current.columns.duplicated().any()}")

# Línea 1259-1267
name_col = None
if "Indicador" in current.columns:
    name_col = "Indicador"
elif "Nombre" in current.columns:
    name_col = "Nombre"
else:
    name_col = "Id"

extra_cols = [c for c in ["Linea"] if c in current.columns]
cols_to_select = ["Id"] + ([name_col] if name_col != "Id" else []) + ["cumplimiento_pct"] + extra_cols
cols_to_select = list(dict.fromkeys([c for c in cols_to_select if c in current.columns]))

print(f"\n3. cols_to_select: {cols_to_select}")

try:
    cur = (
        current[cols_to_select]
        .dropna(subset=["cumplimiento_pct"])
        .drop_duplicates(subset=["Id"], keep="first")
        .copy()
    )
    print(f"   cur shape después de seleccionar: {cur.shape}")
    print(f"   cur columnas duplicadas? {cur.columns.duplicated().any()}")
    if cur.columns.duplicated().any():
        print(f"   DUPLICADOS EN cur: {cur.columns[cur.columns.duplicated()].tolist()}")
except Exception as e:
    print(f"   ERROR al crear cur: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
