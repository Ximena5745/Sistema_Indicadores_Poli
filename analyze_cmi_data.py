import pandas as pd
import json
import os

def analyze():
    files = {
        'Dataset_Unificado': 'data/raw/Dataset_Unificado.xlsx',
        'Ficha_Tecnica': 'data/raw/Ficha_Tecnica.xlsx',
        'Indicadores_CMI': 'data/raw/Indicadores por CMI.xlsx'
    }
    
    info = {}
    for name, path in files.items():
        if os.path.exists(path):
            df = pd.read_excel(path, nrows=5)
            info[name] = {
                'columns': list(df.columns),
                'sample': df.head(1).to_dict('records')
            }
        else:
            info[name] = 'File not found'
            
    print(json.dumps(info, indent=2, default=str))

if __name__ == '__main__':
    analyze()
