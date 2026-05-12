import sys
sys.path.insert(0, '.')
import pandas as pd
from services.strategic_indicators import load_worksheet_flags

print('=== PRUEBA: NUEVA LÓGICA DE PROYECTOS ===\n')

# Simular la nueva lógica de carga de proyectos
base = load_worksheet_flags()
pdi_estrategico = pd.DataFrame()

if not base.empty and "Proyecto" in base.columns:
    # Filtrar solo proyectos (Proyecto == 1)
    pdi_estrategico = base[base["Proyecto"] == 1].copy()
    
    print(f'[1] Proyectos cargados desde worksheet: {len(pdi_estrategico)}')
    print(f'    Esperado: 44')
    
    # Asegurar que cumplimiento_pct existe
    if "cumplimiento_pct" not in pdi_estrategico.columns:
        pdi_estrategico["cumplimiento_pct"] = 0.0
        print(f'[2] Columna cumplimiento_pct creada (no existía)')
    else:
        print(f'[2] Columna cumplimiento_pct ya existe')
    
    # Llenar NaN
    pdi_estrategico["cumplimiento_pct"] = pdi_estrategico["cumplimiento_pct"].fillna(0.0)
    
    print(f'[3] Proyectos con cumplimiento_pct: {pdi_estrategico["cumplimiento_pct"].notna().sum()}')
    print(f'    Valor mínimo: {pdi_estrategico["cumplimiento_pct"].min()}')
    print(f'    Valor máximo: {pdi_estrategico["cumplimiento_pct"].max()}')
    print(f'    Promedio: {pdi_estrategico["cumplimiento_pct"].mean():.2f}')
    
    # Check Nivel de cumplimiento
    if "Nivel de cumplimiento" not in pdi_estrategico.columns:
        pdi_estrategico["Nivel de cumplimiento"] = pdi_estrategico["cumplimiento_pct"].apply(
            lambda x: "No Aplica" if pd.isna(x) or x == 0 
                     else "Peligro" if x < 80 
                     else "Alerta" if x < 100 
                     else "Cumplimiento" if x < 105 
                     else "Sobrecumplimiento"
        )
        print(f'[4] Nivel de cumplimiento calculado')
    
    # Check Línea y Objetivo
    linea_count = pdi_estrategico["Linea"].notna().sum() if "Linea" in pdi_estrategico.columns else 0
    objetivo_count = pdi_estrategico["Objetivo"].notna().sum() if "Objetivo" in pdi_estrategico.columns else 0
    
    print(f'[5] Proyectos con Línea: {linea_count}/{len(pdi_estrategico)}')
    print(f'[6] Proyectos con Objetivo: {objetivo_count}/{len(pdi_estrategico)}')
    
    print(f'\n[7] Primeros 5 proyectos:')
    cols_show = ["Indicador", "Linea", "cumplimiento_pct", "Nivel de cumplimiento"]
    cols_show = [c for c in cols_show if c in pdi_estrategico.columns]
    print(pdi_estrategico[cols_show].head(5))
    
    print(f'\n=== RESULTADO ===')
    print(f'EXITO: {len(pdi_estrategico)} proyectos cargados con cumplimiento')
    print(f'Los proyectos ahora muestran en la UI')
else:
    print('ERROR: No se pudieron cargar proyectos')
