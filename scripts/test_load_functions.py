#!/usr/bin/env python3
"""Test las funciones de carga directamente."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services import strategic_indicators as si

print("=== Testing load functions ===\n")

print("1. load_worksheet_flags():")
try:
    result = si.load_worksheet_flags()
    print(f"   Result: {len(result)} rows")
    if not result.empty:
        print(f"   Columns: {list(result.columns)}")
        print(f"   First row ID: {result['Id'].iloc[0]}")
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n2. load_cierres():")
try:
    result = si.load_cierres()
    print(f"   Result: {len(result)} rows")
    if not result.empty:
        print(f"   Columns: {list(result.columns)}")
        print(f"   First row ID: {result['Id'].iloc[0]}")
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n3. load_pdi_catalog():")
try:
    result = si.load_pdi_catalog()
    print(f"   Result: {len(result)} rows")
    if not result.empty:
        print(f"   Columns: {list(result.columns)}")
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n4. preparar_pdi_con_cierre(2025, 12):")
try:
    result = si.preparar_pdi_con_cierre(2025, 12)
    print(f"   Result: {len(result)} rows")
    if not result.empty:
        print(f"   Columns: {list(result.columns)[:5]}")
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\nDone!")
