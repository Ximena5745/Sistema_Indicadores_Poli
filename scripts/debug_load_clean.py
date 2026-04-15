#!/usr/bin/env python3
"""Test con debug detallado - sin unicode."""

import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RAW_XLSX = ROOT / "data" / "raw" / "Indicadores por CMI.xlsx"
OUT_XLSX = ROOT / "data" / "output" / "Resultados Consolidados.xlsx"

print(f"RAW exists: {RAW_XLSX.exists()}")
print(f"OUT exists: {OUT_XLSX.exists()}\n")

# Prueba directa
print("=== Reading directly ===\n")

print("1. Read Worksheet directly:")
try:
    df = pd.read_excel(RAW_XLSX, sheet_name="Worksheet", engine="openpyxl")
    print(f"   OK: {len(df)} rows")
    print(f"   Columns: {list(df.columns)[:5]}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n2. Read Consolidado Cierres directly:")
try:
    df = pd.read_excel(OUT_XLSX, sheet_name="Consolidado Cierres", engine="openpyxl")
    print(f"   OK: {len(df)} rows")
    print(f"   Columns: {list(df.columns)[:5]}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n=== Now testing si functions ===\n")

from services import strategic_indicators as si

print("3. si.load_worksheet_flags():")
result = si.load_worksheet_flags()
print(f"   Result: {len(result)} rows")
if not result.empty:
    print(f"   First cols: {list(result.columns)[:3]}")

print("\n4. si.load_cierres():")
result = si.load_cierres()  
print(f"   Result: {len(result)} rows")
if not result.empty:
    print(f"   First cols: {list(result.columns)[:3]}")

print("\n5. si.preparar_pdi_con_cierre(2025, 12):")
result = si.preparar_pdi_con_cierre(2025, 12)
print(f"   Result: {len(result)} rows")
if result.empty:
    print("   ERROR: PDI empty!")
else:
    print(f"   First cols: {list(result.columns)[:3]}")
