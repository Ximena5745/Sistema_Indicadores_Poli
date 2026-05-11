import sys
sys.path.insert(0, '.')
import pandas as pd
from services.strategic_indicators import load_worksheet_flags, load_cierres

# Simulate the new logic
base = load_worksheet_flags()
print(f'[1] Proyectos en worksheet: {(base["Proyecto"] == 1).sum() if "Proyecto" in base.columns else 0}')

pdi_estrategico = base[base["Proyecto"] == 1].copy() if "Proyecto" in base.columns else pd.DataFrame()
print(f'[2] Proyectos cargados: {len(pdi_estrategico)}')

# Try enriching with cierres
cierres = load_cierres()
cierres_2025 = cierres[cierres["Anio"] == 2025].copy()

if not cierres_2025.empty and "Fecha" in cierres_2025.columns:
    cierres_2025 = cierres_2025.sort_values("Fecha").drop_duplicates(subset=["Indicador"], keep="last")
    print(f'[3] Cierres after dedup: {len(cierres_2025)}')

    if "Indicador" in pdi_estrategico.columns and "Indicador" in cierres_2025.columns:
        print(f'[4] Indicadores en proyectos: {pdi_estrategico["Indicador"].nunique()}')
        print(f'    Ejemplos: {pdi_estrategico["Indicador"].head(3).tolist()}')
        print(f'[5] Indicadores en cierres: {cierres_2025["Indicador"].nunique()}')
        print(f'    Ejemplos: {cierres_2025["Indicador"].head(3).tolist()}')
        
        # Try merge
        merge_cols = ["Indicador", "cumplimiento_pct", "Nivel de cumplimiento"]
        available_cols = [c for c in merge_cols if c in cierres_2025.columns]
        
        pdi_estrategico = pdi_estrategico.merge(
            cierres_2025[available_cols].drop_duplicates(subset=["Indicador"]),
            on="Indicador",
            how="left"
        )
        
        print(f'[6] After merge:')
        print(f'    Rows: {len(pdi_estrategico)}')
        print(f'    Cumplimiento_pct non-null: {pdi_estrategico["cumplimiento_pct"].notna().sum()}')
        print(f'    Sample: \n{pdi_estrategico[["Indicador", "cumplimiento_pct", "Linea"]].head(5)}')
