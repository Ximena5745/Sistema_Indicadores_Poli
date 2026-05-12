#!/usr/bin/env python
"""Debug: Simular el error exact de _compute_trends"""

import pandas as pd
import sys

# Crear un DataFrame con columnas duplicadas (nombre "Id" aparece dos veces)
print("="*70)
print("SIMULAR: Error 'column label Id is not unique'")
print("="*70)

# Crear DataFrame con columnas duplicadas
df = pd.DataFrame({
    'Id': [1, 2, 3],
    'Indicador': ['A', 'B', 'C'],
    'cumplimiento_pct': [80, 90, 70],
    'Linea': ['L1', 'L1', 'L2']
})

# Simular lo que pasaría si se hace un concat sin reset_index correcto
df_concat = pd.concat([df, df[[*df.columns]]], axis=1)
print(f"\n1. DataFrame después de concat sin reset:")
print(f"   Shape: {df_concat.shape}")
print(f"   Columnas: {df_concat.columns.tolist()}")
print(f"   ¿Duplicadas? {df_concat.columns.duplicated().any()}")
if df_concat.columns.duplicated().any():
    print(f"   DUPLICADOS: {df_concat.columns[df_concat.columns.duplicated()].tolist()}")

# Intentar seleccionar columnas (esto debería fallar)
print(f"\n2. Intentar acceder a df_concat[['Id', 'Indicador', 'cumplimiento_pct']]:")
try:
    result = df_concat[['Id', 'Indicador', 'cumplimiento_pct']]
    print(f"   ✓ Funcionó. Shape: {result.shape}")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

# Intentar limpiar duplicados
print(f"\n3. Limpiar con loc[:, ~columns.duplicated()]:")
df_clean = df_concat.loc[:, ~df_concat.columns.duplicated()].copy()
print(f"   Shape después: {df_clean.shape}")
print(f"   Columnas: {df_clean.columns.tolist()}")
print(f"   ¿Duplicadas? {df_clean.columns.duplicated().any()}")

# Ahora intentar acceder
print(f"\n4. Acceder a df_clean[['Id', 'Indicador', 'cumplimiento_pct']]:")
try:
    result = df_clean[['Id', 'Indicador', 'cumplimiento_pct']]
    print(f"   ✓ Funcionó. Shape: {result.shape}")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

print("\n" + "="*70)
