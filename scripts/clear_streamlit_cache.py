#!/usr/bin/env python3
"""Limpiar caché de Streamlit."""

import shutil
from pathlib import Path

print("\n" + "="*80)
print("LIMPIANDO CACHÉ DE STREAMLIT")
print("="*80)

# Las ubicaciones comunes del caché de Streamlit en Windows
cache_locations = [
    Path.home() / ".streamlit" / "cache",
    Path.home() / ".streamlit",
    Path(__file__).resolve().parent.parent / ".streamlit",
]

for cache_dir in cache_locations:
    if cache_dir.exists():
        print(f"\nEncontrado caché: {cache_dir}")
        try:
            if cache_dir.is_dir():
                shutil.rmtree(cache_dir)
                print(f"  ELIMINADO: {cache_dir}")
            else:
                cache_dir.unlink()
                print(f"  ELIMINADO: {cache_dir}")
        except Exception as e:
            print(f"  ERROR al eliminar: {e}")
    else:
        print(f"\nNo existe: {cache_dir}")

# También limpiar el workspace storage de VS Code
vscode_cache = Path.home() / "AppData" / "Roaming" / "Code" / "workspaceStorage"
if vscode_cache.exists():
    print(f"\n\nVS Code workspace cache: {vscode_cache}")
    # No lo eliminamos porque contiene otras cosas, solo informamos
    print("  (No se elimina automáticamente)")

print("\n" + "="*80)
print("RECOMENDACIÓN:")
print("  1. Ejecuta este script")
print("  2. Reinicia Streamlit: streamlit run streamlit_app/app.py")
print("="*80 + "\n")
