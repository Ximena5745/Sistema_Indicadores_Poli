#!/usr/bin/env python
from services.strategic_indicators import load_cierres
from services.cmi_filters import load_cmi_worksheet

cierres = load_cierres()
cmi = load_cmi_worksheet()

print("="*60)
print("ANÁLISIS DE IDs EN CIERRES vs PROYECTOS DEL CMI")
print("="*60)

cierres_ids = sorted(cierres['Id'].unique())
proy_cmi = cmi[cmi['Proyecto'] == 1]
proy_cmi_ids = set(str(int(x)) if isinstance(x, float) else str(x) for x in proy_cmi['Id'].dropna())

print(f"\nTotal registros en cierres: {len(cierres)}")
print(f"IDs únicos en cierres: {len(cierres_ids)}")
print(f"Primeros 30 IDs en cierres: {cierres_ids[:30]}")

print(f"\nProyectos en CMI: {len(proy_cmi)}")
print(f"IDs de proyectos en CMI: {sorted(proy_cmi_ids)}")

# Buscar intersección
interseccion = set(cierres_ids) & proy_cmi_ids
print(f"\nIDs que coinciden entre cierres y proyectos CMI: {len(interseccion)}")
if interseccion:
    print(f"IDs coincidentes: {sorted(interseccion)}")

# Ver columnas de cierres
print(f"\nColumnas en cierres: {cierres.columns.tolist()}")
print(f"\nPrimer registro de cierres:")
print(cierres.iloc[0] if len(cierres) > 0 else "No hay datos")
