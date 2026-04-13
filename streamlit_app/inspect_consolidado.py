import pandas as pd
from pathlib import Path
root = Path(__file__).resolve().parents[1]
path = root.parent / 'data' / 'output' / 'Resultados Consolidados.xlsx'
print('PATH', path)
print('EXISTS', path.exists())
try:
    xls = pd.ExcelFile(path, engine='openpyxl')
    print('SHEETS', xls.sheet_names)
    df = xls.parse('Consolidado Cierres')
    print('SHAPE', df.shape)
    print('COLS', df.columns.tolist())
    print('HEAD', df.head(5).to_dict(orient='records'))
except Exception as e:
    import traceback
    traceback.print_exc()
