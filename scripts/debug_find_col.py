#!/usr/bin/env python3
"""Debug load_worksheet_flags paso a paso."""

import sys
import unicodedata
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.config import DATA_RAW

def _norm_text(value: str) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")

def _find_col(df: pd.DataFrame, names: list[str]) -> str | None:
    lookup = {_norm_text(c): c for c in df.columns}
    print(f"    Lookup keys (primeros 5): {list(lookup.keys())[:5]}")
    for name in names:
        norm_name = _norm_text(name)
        print(f"    Buscando: '{name}' -> normalizado: '{norm_name}'")
        hit = lookup.get(norm_name)
        if hit:
            print(f"      ENCONTRADO: '{hit}'")
            return hit
        else:
            print(f"      No encontrado")
    return None

print("\n" + "="*80)
print("DEBUG: load_worksheet_flags")
print("="*80)

RAW_XLSX = DATA_RAW / "Indicadores por CMI.xlsx"

print(f"\nArchivo: {RAW_XLSX}")
print(f"Existe: {RAW_XLSX.exists()}")

df = pd.read_excel(RAW_XLSX, sheet_name="Worksheet", engine="openpyxl")
df.columns = [str(c).strip() for c in df.columns]

print(f"\nDataFrame: {len(df)} filas, {len(df.columns)} columnas")
print(f"Todas las columnas:")
for i, col in enumerate(df.columns, 1):
    print(f"  {i:2d}. '{col}'")

# Buscar columnas clave
print("\n--- Buscando columnas clave ---")

print("\n1. Buscando c_plan:")
c_plan = _find_col(df, ["Indicadores Plan estrategico"])
print(f"  Resultado: {c_plan}")

print("\n2. Buscando c_linea:")
c_linea = _find_col(df, ["Linea"])
print(f"  Resultado: {c_linea}")

print("\n3. Buscando c_obj:")
c_obj = _find_col(df, ["Objetivo"])
print(f"  Resultado: {c_obj}")

print("\n4. Verificar columna Indicadores Plan estrategico manualmente:")
target_col = "Indicadores Plan estrategico"
if target_col in df.columns:
    print(f"  ENCONTRADA: '{target_col}'")
    print(f"  Valores únicos: {df[target_col].unique()}")
else:
    print(f"  NO ENCONTRADA")
    # Buscar similar
    similar = [c for c in df.columns if "plan" in c.lower()]
    print(f"  Columnas similares con 'plan': {similar}")

print("\n" + "="*80)
