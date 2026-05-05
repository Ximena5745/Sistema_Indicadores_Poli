from pathlib import Path
path = Path('streamlit_app/pages/resumen_por_proceso.py')
text = path.read_text(encoding='utf-8')
old = '''            proc_curr = (
                chart_curr.groupby(group_cols, dropna=False)
                .agg(actual=(pct_col, "mean"), indicadores=("Indicador", "count"))
                .reset_index()
            )
'''
new = '''            proc_curr = (
                chart_curr.groupby(group_cols, dropna=False)
                .agg(actual=(pct_col, "mean"), indicadores=("Id", lambda s: s.dropna().astype(str).str.strip().nunique()))
                .reset_index()
            )
'''
replaced = text.replace(old, new)
count = text.count(old)
print('found', count, 'occurrences')
if count != text.count(old):
    print('replace count changed unexpectedly')
path.write_text(replaced, encoding='utf-8')
print('done')
