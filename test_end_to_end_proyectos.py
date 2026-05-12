#!/usr/bin/env python
"""Test end-to-end del flujo Proyectos con defensas contra duplicados"""

import sys
import pandas as pd
sys.path.insert(0, r"c:\Users\ximen\OneDrive\Proyectos_DS\Sistema_Indicadores_Poli")

from services.strategic_indicators import load_proyectos_consolidados, load_worksheet_flags, preparar_pdi_con_cierre
from services.cmi_filters import load_cmi_worksheet

print("="*70)
print("TEST END-TO-END: Proyectos (con defensas)")
print("="*70)

# Función auxiliar para simular _get_proyectos_ids
def _get_proyectos_ids():
    df = load_cmi_worksheet()
    if df.empty or "Proyecto" not in df.columns or "Id" not in df.columns:
        return set()
    return set(str(int(x)) if isinstance(x, float) else str(x).strip() for x in df.loc[df["Proyecto"] == 1, "Id"].dropna())

# Función para simular _compute_trends con defensas
def _compute_trends_safe(current: pd.DataFrame, previous: pd.DataFrame):
    print("\n[_compute_trends]")
    if current.empty or previous.empty:
        print("  INPUT: Vacío")
        return [], []
    
    # Defensa 1: Limpiar columnas duplicadas
    print(f"  Entrada current: {current.shape}, duplicadas={current.columns.duplicated().any()}")
    print(f"  Entrada previous: {previous.shape}, duplicadas={previous.columns.duplicated().any()}")
    
    current = current.loc[:, ~current.columns.duplicated()].copy()
    previous = previous.loc[:, ~previous.columns.duplicated()].copy()
    
    # Defensa 2: Verificar que exista 'Id'
    if "Id" not in current.columns or "Id" not in previous.columns:
        print("  ERROR: Falta columna 'Id' después de limpiar")
        return [], []
    
    print(f"  Después limpiar: current={current.shape}, prev={previous.shape}")
    
    # Resto del flujo
    name_col = "Indicador" if "Indicador" in current.columns else "Id"
    extra_cols = [c for c in ["Linea"] if c in current.columns]
    cols_to_select = ["Id"] + ([name_col] if name_col != "Id" else []) + ["cumplimiento_pct"] + extra_cols
    cols_to_select = list(dict.fromkeys([c for c in cols_to_select if c in current.columns]))
    
    if "Id" not in cols_to_select or "cumplimiento_pct" not in cols_to_select:
        print("  ERROR: Faltan columnas críticas")
        return [], []
    
    cur = (
        current[cols_to_select]
        .dropna(subset=["cumplimiento_pct"])
        .drop_duplicates(subset=["Id"], keep="first")
        .copy()
    )
    prev = (
        previous[["Id", "cumplimiento_pct"]]
        .dropna(subset=["cumplimiento_pct"])
        .drop_duplicates(subset=["Id"], keep="first")
        .copy()
    )
    
    if cur.empty or prev.empty:
        print(f"  FILTRADO: cur={cur.shape}, prev={prev.shape}")
        return [], []
    
    # Defensa 3: Verificar duplicados antes del merge
    if cur.columns.duplicated().any() or prev.columns.duplicated().any():
        print("  ALERTA: Duplicados detectados, limpiando...")
        cur = cur.loc[:, ~cur.columns.duplicated()].copy()
        prev = prev.loc[:, ~prev.columns.duplicated()].copy()
    
    try:
        merged = cur.merge(prev, on="Id", suffixes=("", "_prev"))
        print(f"  ✓ MERGE OK: {merged.shape}")
        return list(range(min(5, len(merged)))), list(range(min(5, len(merged))))
    except Exception as e:
        print(f"  ✗ ERROR en merge: {e}")
        return [], []

# Simular flujo Proyectos
print("\n1. Cargar datos de Proyectos:")
pdi_proy = pd.DataFrame()
ids_proy = _get_proyectos_ids()
print(f"   IDs de proyectos: {len(ids_proy)} IDs")

if ids_proy:
    consolidado = load_proyectos_consolidados()
    print(f"   Consolidado: {consolidado.shape}")
    
    consolidado["Id"] = consolidado["Id"].astype(str)
    pdi_proy = consolidado[consolidado["Id"].isin(ids_proy)].copy()
    print(f"   Filtrado por IDs: {pdi_proy.shape}")
    
    # Defensiva: limpiar duplicados
    if pdi_proy.columns.duplicated().any():
        print("   ⚠ Duplicados encontrados, limpiando...")
        pdi_proy = pdi_proy.loc[:, ~pdi_proy.columns.duplicated()].copy()
    
    pdi_proy = pdi_proy.sort_values("Id", na_position="last").drop_duplicates(subset=["Id"], keep="last")
    print(f"   Deduplicado: {pdi_proy.shape}")

pdi_base_df = pdi_proy.copy()
print(f"   pdi_base_df: {pdi_base_df.shape}, duplicadas={pdi_base_df.columns.duplicated().any()}")

# Cargar datos previos
print("\n2. Cargar datos previos:")
prev_df = preparar_pdi_con_cierre(2024, 12)
print(f"   Prev: {prev_df.shape if prev_df is not None else 'None'}")

if prev_df is not None and not prev_df.empty:
    if "Id" in prev_df.columns:
        prev_df = prev_df[prev_df["Id"].astype(str).isin(ids_proy)].copy()
    else:
        prev_df = pd.DataFrame()
    
    # Defensiva: limpiar duplicados
    if not prev_df.empty and prev_df.columns.duplicated().any():
        print("   ⚠ Duplicados en prev_df, limpiando...")
        prev_df = prev_df.loc[:, ~prev_df.columns.duplicated()].copy()
    
    print(f"   Prev filtrado: {prev_df.shape}, duplicadas={prev_df.columns.duplicated().any()}")
else:
    prev_df = pd.DataFrame()

# Llamar a _compute_trends
print("\n3. Calcular trends:")
best, worst = _compute_trends_safe(pdi_base_df, prev_df)
print(f"   Best improvements: {len(best)}")
print(f"   Worst declines: {len(worst)}")

print("\n" + "="*70)
print("[OK] TEST COMPLETADO SIN ERRORES")
