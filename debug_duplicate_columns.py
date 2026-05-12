#!/usr/bin/env python
"""Debug: Verificar columnas duplicadas en DataFrames de Proyectos"""

from services.strategic_indicators import load_proyectos_consolidados, load_worksheet_flags
from services.cmi_filters import load_cmi_worksheet
import pandas as pd

print("="*70)
print("DEBUG: COLUMNAS DUPLICADAS EN PROYECTOS")
print("="*70)

# 1. Cargar proyectos
proyectos = load_proyectos_consolidados()
print(f"\n1. load_proyectos_consolidados():")
print(f"   Filas: {len(proyectos)}")
print(f"   Columnas totales: {len(proyectos.columns)}")
print(f"   ¿Columnas duplicadas? {proyectos.columns.duplicated().any()}")
if proyectos.columns.duplicated().any():
    print(f"   Duplicados: {proyectos.columns[proyectos.columns.duplicated()].tolist()}")

# 2. Filtrar por IDs de proyectos
cmi = load_cmi_worksheet()
proy_cmi = cmi[cmi['Proyecto'] == 1]
ids_proy = set(str(int(x)) if isinstance(x, float) else str(x) for x in proy_cmi['Id'].dropna())

proyectos["Id"] = proyectos["Id"].astype(str)
pdi_proy = proyectos[proyectos["Id"].isin(ids_proy)].copy()

print(f"\n2. Después de filtrar por IDs de proyectos:")
print(f"   Filas: {len(pdi_proy)}")
print(f"   Columnas totales: {len(pdi_proy.columns)}")
print(f"   ¿Columnas duplicadas? {pdi_proy.columns.duplicated().any()}")
if pdi_proy.columns.duplicated().any():
    print(f"   Duplicados: {pdi_proy.columns[pdi_proy.columns.duplicated()].tolist()}")

# 3. Merge con Línea/Objetivo si falta
if not pdi_proy.empty and ("Linea" not in pdi_proy.columns or pdi_proy["Linea"].isna().all()):
    base = load_worksheet_flags()
    if not base.empty:
        print(f"\n3. Antes del merge con load_worksheet_flags():")
        print(f"   pdi_proy columnas: {len(pdi_proy.columns)}")
        print(f"   base columnas: {len(base.columns)}")
        print(f"   base columns: {base.columns.tolist()[:10]}")
        
        base_norm = base.copy()
        base_norm["Id"] = base_norm["Id"].astype(str)
        merge_cols = [c for c in ["Linea", "Objetivo"] if c in base_norm.columns]
        print(f"   merge_cols: {merge_cols}")
        
        if merge_cols:
            base_to_merge = base_norm[["Id"] + merge_cols].drop_duplicates(subset=["Id"])
            print(f"   base_to_merge shape: {base_to_merge.shape}")
            print(f"   base_to_merge columns: {base_to_merge.columns.tolist()}")
            
            pdi_proy = pdi_proy.merge(base_to_merge, on="Id", how="left", suffixes=("", "_cmi"))
            
            print(f"\n4. DESPUÉS del merge:")
            print(f"   Filas: {len(pdi_proy)}")
            print(f"   Columnas totales: {len(pdi_proy.columns)}")
            print(f"   ¿Columnas duplicadas? {pdi_proy.columns.duplicated().any()}")
            if pdi_proy.columns.duplicated().any():
                print(f"   DUPLICADOS ENCONTRADOS: {pdi_proy.columns[pdi_proy.columns.duplicated()].tolist()}")
            print(f"   Columnas: {pdi_proy.columns.tolist()}")

# 5. Después de resolver sufijos
for col in pdi_proy.columns:
    if col.endswith("_cmi"):
        base_col = col[:-4]
        if base_col in pdi_proy.columns:
            pdi_proy[base_col] = pdi_proy[base_col].fillna(pdi_proy[col])
        pdi_proy = pdi_proy.drop(col, axis=1)

print(f"\n5. DESPUÉS de resolver sufijos:")
print(f"   Filas: {len(pdi_proy)}")
print(f"   Columnas totales: {len(pdi_proy.columns)}")
print(f"   ¿Columnas duplicadas? {pdi_proy.columns.duplicated().any()}")
if pdi_proy.columns.duplicated().any():
    print(f"   DUPLICADOS: {pdi_proy.columns[pdi_proy.columns.duplicated()].tolist()}")

# 6. Después de deduplicar
pdi_proy = pdi_proy.sort_values("Id", na_position="last").drop_duplicates(subset=["Id"], keep="last")

print(f"\n6. DESPUÉS de deduplicar por Id:")
print(f"   Filas: {len(pdi_proy)}")
print(f"   Columnas totales: {len(pdi_proy.columns)}")
print(f"   ¿Columnas duplicadas? {pdi_proy.columns.duplicated().any()}")
if pdi_proy.columns.duplicated().any():
    print(f"   DUPLICADOS: {pdi_proy.columns[pdi_proy.columns.duplicated()].tolist()}")

print("\n" + "="*70)
