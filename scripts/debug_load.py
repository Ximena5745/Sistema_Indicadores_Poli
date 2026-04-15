#!/usr/bin/env python3
"""Test con debug detallado."""

import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RAW_XLSX = ROOT / "data" / "raw" / "Indicadores por CMI.xlsx"
OUT_XLSX = ROOT / "data" / "output" / "Resultados Consolidados.xlsx"

print(f"RAW exists: {RAW_XLSX.exists()}")
print(f"OUT exists: {OUT_XLSX.exists()}\n")

# Prueba directa: leer sin importar si.functions
print("=== Reading directly ===\n")

print("1. Read Worksheet directly:")
try:
    df = pd.read_excel(RAW_XLSX, sheet_name="Worksheet", engine="openpyxl")
    print(f"   ✓ {len(df)} rows")
    print(f"   Columns: {list(df.columns)[:5]}")
except Exception as e:
    print(f"   ✗ {e}")

print("\n2. Read Consolidado Cierres directly:")
try:
    df = pd.read_excel(OUT_XLSX, sheet_name="Consolidado Cierres", engine="openpyxl")
    print(f"   ✓ {len(df)} rows")
    print(f"   Columns: {list(df.columns)[:5]}")
except Exception as e:
    print(f"   ✗ {e}")

print("\n3. Read PDI sheet directly:")
try:
    df = pd.read_excel(RAW_XLSX, sheet_name="PDI", engine="openpyxl")
    print(f"   ✓ {len(df)} rows")
    print(f"   Columns: {list(df.columns)[:5]}")
except Exception as e:
    print(f"   ✗ {e}")

print("\n=== Now testing si functions ===\n")

from services import strategic_indicators as si

# Add debug to load_worksheet_flags
print("4. si.load_worksheet_flags():")
print(f"   File check: {RAW_XLSX.exists()}")
try:
    df = pd.read_excel(RAW_XLSX, sheet_name="Worksheet", engine="openpyxl")
    print(f"   Direct read: {len(df)} rows")
except Exception as e:
    print(f"   Direct read ERROR: {e}")

result = si.load_worksheet_flags()
print(f"   si.load_worksheet_flags: {len(result)} rows")
if not result.empty:
    print(f"   First cols: {list(result.columns)[:3]}")

print("\n5. si.load_cierres():")
result = si.load_cierres()  
print(f"   si.load_cierres: {len(result)} rows")
if not result.empty:
    print(f"   First cols: {list(result.columns)[:3]}")
