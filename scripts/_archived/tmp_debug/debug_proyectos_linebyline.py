#!/usr/bin/env python
"""Debug: Simular línea por línea el código de Proyectos"""

import pandas as pd
import sys

# Configurar path
sys.path.insert(0, r"c:\Users\ximen\OneDrive\Proyectos_DS\Sistema_Indicadores_Poli")

from services.strategic_indicators import load_proyectos_consolidados, load_worksheet_flags
from services.cmi_filters import load_cmi_worksheet

print("="*70)
print("DEBUG LÍNEA POR LÍNEA: Proyectos loading")
print("="*70)

# Línea 2280
print("\n[2280] pdi_proy = pd.DataFrame()")
pdi_proy = pd.DataFrame()

# Línea 2281
print("[2281] ids_proy = _get_proyectos_ids()")
ids_proy = set(str(int(x)) if isinstance(x, float) else str(x) for x in load_cmi_worksheet()[load_cmi_worksheet()['Proyecto'] == 1]['Id'].dropna())
print(f"      ids_proy: {ids_proy}")

# Línea 2283
print("[2283] if ids_proy:")
if ids_proy:
    # Línea 2285
    print("[2285] consolidado = load_proyectos_consolidados()")
    consolidado = load_proyectos_consolidados()
    print(f"      Shape: {consolidado.shape}, Cols: {len(consolidado.columns)}")
    print(f"      Duplicadas? {consolidado.columns.duplicated().any()}")
    
    # Línea 2287
    print("[2287] if not consolidado.empty and 'Id' in consolidado.columns:")
    if not consolidado.empty and "Id" in consolidado.columns:
        # Línea 2289
        print("[2289] consolidado['Id'] = consolidado['Id'].astype(str)")
        consolidado["Id"] = consolidado["Id"].astype(str)
        
        # Línea 2290
        print("[2290] pdi_proy = consolidado[consolidado['Id'].isin(ids_proy)].copy()")
        pdi_proy = consolidado[consolidado["Id"].isin(ids_proy)].copy()
        print(f"      Shape: {pdi_proy.shape}, Cols: {len(pdi_proy.columns)}")
        print(f"      Duplicadas? {pdi_proy.columns.duplicated().any()}")
        
        # Línea 2292
        print("[2292] if not pdi_proy.empty and ('Linea' not in pdi_proy.columns ...")
        if not pdi_proy.empty and ("Linea" not in pdi_proy.columns or pdi_proy["Linea"].isna().all()):
            print("      Entrando a merge de Línea/Objetivo...")
            
            # Línea 2293
            print("[2293] base = load_worksheet_flags()")
            base = load_worksheet_flags()
            
            # Línea 2294
            print("[2294] if not base.empty:")
            if not base.empty:
                # Línea 2295
                print("[2295] base_norm = base.copy()")
                base_norm = base.copy()
                
                # Línea 2296
                print("[2296] base_norm['Id'] = base_norm['Id'].astype(str)")
                base_norm["Id"] = base_norm["Id"].astype(str)
                
                # Línea 2297
                print("[2297] merge_cols = [c for c in ['Linea', 'Objetivo'] if c in base_norm.columns]")
                merge_cols = [c for c in ["Linea", "Objetivo"] if c in base_norm.columns]
                print(f"      merge_cols: {merge_cols}")
                
                # Línea 2298
                print("[2298] if merge_cols:")
                if merge_cols:
                    # Línea 2299
                    print("[2299] base_to_merge = base_norm[['Id'] + merge_cols].drop_duplicates(subset=['Id'])")
                    base_to_merge = base_norm[["Id"] + merge_cols].drop_duplicates(subset=["Id"])
                    print(f"      Shape: {base_to_merge.shape}")
                    print(f"      Columns: {base_to_merge.columns.tolist()}")
                    print(f"      Duplicadas? {base_to_merge.columns.duplicated().any()}")
                    
                    # Línea 2300
                    print("[2300] pdi_proy = pdi_proy.merge(base_to_merge, on='Id', how='left', suffixes=('', '_cmi'))")
                    print(f"      Antes: pdi_proy shape={pdi_proy.shape}, cols={len(pdi_proy.columns)}")
                    print(f"      pdi_proy Duplicadas? {pdi_proy.columns.duplicated().any()}")
                    try:
                        pdi_proy = pdi_proy.merge(base_to_merge, on="Id", how="left", suffixes=("", "_cmi"))
                        print(f"      ✓ Merge exitoso")
                        print(f"      Después: pdi_proy shape={pdi_proy.shape}, cols={len(pdi_proy.columns)}")
                        print(f"      pdi_proy Duplicadas? {pdi_proy.columns.duplicated().any()}")
                        if pdi_proy.columns.duplicated().any():
                            print(f"      DUPLICADOS: {pdi_proy.columns[pdi_proy.columns.duplicated()].tolist()}")
                    except Exception as e:
                        print(f"      ✗ ERROR en merge: {e}")
                        import traceback
                        traceback.print_exc()
                    
                    # Línea 2302-2308 (resolver sufijos)
                    print("[2302-2308] Resolver sufijos...")
                    for col in pdi_proy.columns:
                        if col.endswith("_cmi"):
                            base_col = col[:-4]
                            if base_col in pdi_proy.columns:
                                pdi_proy[base_col] = pdi_proy[base_col].fillna(pdi_proy[col])
                            pdi_proy = pdi_proy.drop(col, axis=1)
                    
                    print(f"      Después resolver: shape={pdi_proy.shape}, Duplicadas? {pdi_proy.columns.duplicated().any()}")
        
        # Línea 2310
        print("[2310] pdi_proy = pdi_proy.sort_values('Id', ...).drop_duplicates(subset=['Id'], keep='last')")
        pdi_proy = pdi_proy.sort_values("Id", na_position="last").drop_duplicates(subset=["Id"], keep="last")
        print(f"      Después: shape={pdi_proy.shape}, Duplicadas? {pdi_proy.columns.duplicated().any()}")

# Línea 2313
print("[2313] pdi_base_df = pdi_proy.copy()")
pdi_base_df = pdi_proy.copy()
print(f"      pdi_base_df shape={pdi_base_df.shape}, Duplicadas? {pdi_base_df.columns.duplicated().any()}")

print("\n" + "="*70)
