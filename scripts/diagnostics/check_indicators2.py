import pandas as pd

# Cargar Indicadores por CMI
try:
    df_cmi = pd.read_excel('data/raw/Indicadores por CMI.xlsx')
    print('=== Indicadores por CMI ===')
    print(f'Total registros: {len(df_cmi)}')
    print(f'Columnas: {list(df_cmi.columns)}')
    print(f'Primeras 5 filas:')
    print(df_cmi.head())
except Exception as e:
    print(f'Error cargando Indicadores por CMI: {e}')

print('\n' + '='*60)

# Cargar Ficha Técnica
try:
    df_ficha = pd.read_excel('data/raw/Ficha_Tecnica_Indicadores.xlsx')
    print('=== Ficha Técnica Indicadores ===')
    print(f'Total registros: {len(df_ficha)}')
    print(f'Columnas: {list(df_ficha.columns)}')
    print(f'Primeras 5 filas:')
    print(df_ficha.head())
except Exception as e:
    print(f'Error cargando Ficha Técnica: {e}')
