import sys

f = open(r'C:\Users\ximen\OneDrive\Proyectos_DS\Sistema_Indicadores_Poli\streamlit_app\pages\resumen_general.py', 'r', encoding='utf-8')
content = f.read()
f.close()

# Reemplazar la línea mal indentada
old_line = 'objetivo_df = obj_df[[c for c in ["Linea","Objetivo","cumplimiento_pct"] if c in obj_df.columns].copy()'
new_line = '            objetivo_df = obj_df[[c for c in ["Linea","Objetivo","cumplimiento_pct"] if c in obj_df.columns].copy()'

content = content.replace(old_line, new_line)

f = open(r'C:\Users\ximen\OneDrive\Proyectos_DS\Sistema_Indicadores_Poli\streamlit_app\pages\resumen_general.py', 'w', encoding='utf-8')
f.write(content)
f.close()

print("Archivo corregido")