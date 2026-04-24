with open(r'C:\Users\ximen\OneDrive\Proyectos_DS\Sistema_Indicadores_Poli\streamlit_app\pages\resumen_general.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if i == 1481:
        new_lines.append('            cols = [c for c in ["Linea", "Objetivo", "cumplimiento_pct"] if c in obj_df.columns]\n')
        new_lines.append('            objetivo_df = obj_df[cols].copy()\n')
    else:
        new_lines.append(line)

with open(r'C:\Users\ximen\OneDrive\Proyectos_DS\Sistema_Indicadores_Poli\streamlit_app\pages\resumen_general.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Archivo corregido')