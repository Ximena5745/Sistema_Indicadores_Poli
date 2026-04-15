#!/usr/bin/env python3
"""Test para verificar el cálculo de ROOT."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
print(f"Script ROOT: {ROOT}")

# Importar y ver el ROOT del módulo
from services import strategic_indicators as si
import inspect

source = inspect.getsourcefile(si)
print(f"si source: {source}")

# Revisa el ROOT definido en el módulo
print(f"si.ROOT: {si.ROOT}")
print(f"si.RAW_XLSX: {si.RAW_XLSX}")
print(f"si.RAW_XLSX exists: {si.RAW_XLSX.exists()}")
