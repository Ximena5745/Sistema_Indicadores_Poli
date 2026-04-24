import re

with open(r'C:\Users\ximen\OneDrive\Proyectos_DS\Sistema_Indicadores_Poli\streamlit_app\pages\resumen_general.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Patrón para encontrar las líneas problemáticas
# Reemplazar: obj_df[[c for c in ["X","Y","Z"] if c in obj_df.columns].copy()
# Con: cols = [c for c in ["X","Y","Z"] if c in obj_df.columns]\n objetivo_df = obj_df[cols].copy()

# Lista de patrones a buscar y reemplazar
patterns = [
    (r'(\w+)\[c for c in \["([^"]+)"\] if c in \1\.columns\]\.copy\(\)', r'cols = [c for c in ["\2"] if c in \1.columns]\n            \1 = \1[cols].copy()'),
]

# Primero, identificar todas las líneas problemáticas
lines = content.split('\n')
problematic_lines = []
for i, line in enumerate(lines):
    if 'if c in' in line and '.columns].copy()' in line and '[' in line:
        problematic_lines.append((i, line.strip()))

print(f"Encontradas {len(problematic_lines)} líneas problemáticas:")
for i, line in problematic_lines:
    print(f"  Línea {i+1}: {line[:80]}...")

# Reemplazar cada línea problemática
for i, old_line in problematic_lines:
    # Extraer el nombre del DataFrame
    match = re.match(r'(\w+)\s*=\s*(\w+)\[\[c for c in \["([^\]]+)"\]', old_line)
    if match:
        df_name = match.group(1)
        source_df = match.group(2)
        cols_str = match.group(3).replace('","', '", "')
        
        new_line1 = f'            cols = [c for c in ["{cols_str}"] if c in {source_df}.columns]'
        new_line2 = f'            {df_name} = {source_df}[cols].copy()'
        
        lines[i] = new_line1 + '\n' + new_line2
        print(f"Reemplazando línea {i+1}")

with open(r'C:\Users\ximen\OneDrive\Proyectos_DS\Sistema_Indicadores_Poli\streamlit_app\pages\resumen_general.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print('Archivo corregido')