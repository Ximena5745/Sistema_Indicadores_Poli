#!/usr/bin/env python
"""Debug: Reproducir el error exact 'column label Id is not unique' en merge"""

import pandas as pd

print("="*70)
print("REPRODUCIR: Error en merge cuando hay columnas duplicadas")
print("="*70)

# Escenario 1: merge con sufijos cuando ambos DataFrames tienen "Id"
print("\n1. Merge normal (sin duplicados):")
df1 = pd.DataFrame({'Id': [1, 2, 3], 'cumplimiento_pct': [80, 90, 70]})
df2 = pd.DataFrame({'Id': [1, 2, 3], 'cumplimiento_pct': [75, 85, 65]})
try:
    merged = df1.merge(df2, on='Id', suffixes=('', '_prev'))
    print(f"   ✓ Funcionó. Shape: {merged.shape}")
    print(f"   Columnas: {merged.columns.tolist()}")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

# Escenario 2: DataFrame con múltiples columnas "Id" (duplicadas)
print("\n2. Merge cuando df1 tiene columnas duplicadas:")
df1_dup = pd.DataFrame([[1, 80], [2, 90], [3, 70]], columns=['Id', 'cumplimiento_pct'])
# Agregar otra columna 'Id'
df1_dup.insert(1, 'Id_2', df1_dup['Id'])
df1_dup.columns = ['Id', 'Id', 'cumplimiento_pct']  # Renombrar para crear duplicado
print(f"   df1_dup columns: {df1_dup.columns.tolist()}")
print(f"   df1_dup duplicadas? {df1_dup.columns.duplicated().any()}")
try:
    merged = df1_dup.merge(df2, on='Id', suffixes=('', '_prev'))
    print(f"   ✓ Funcionó. Shape: {merged.shape}")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

# Escenario 3: Acceder a columnas en DataFrame con duplicados
print("\n3. Acceder a df_dup['Id']:")
try:
    result = df1_dup[['Id']]
    print(f"   Shape: {result.shape} (debería ser [3, 2] - dos columnas 'Id')")
    print(f"   Columnas: {result.columns.tolist()}")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

# Escenario 4: Acceder a lista con 'Id' en DataFrame con columnas duplicadas
print("\n4. Acceder a df_dup[['Id', 'cumplimiento_pct']]:")
try:
    result = df1_dup[['Id', 'cumplimiento_pct']]
    print(f"   Shape: {result.shape} (debería ser [3, 3] - dos 'Id' + cumplimiento_pct)")
    print(f"   Columnas: {result.columns.tolist()}")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

print("\n" + "="*70)
