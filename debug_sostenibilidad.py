import sys
sys.path.insert(0, '.')

from streamlit_app.pages.resumen_general import _build_sunburst, filter_df_for_cmi_estrategico
from services.strategic_indicators import preparar_pdi_con_cierre
import pandas as pd

# Cargar datos
pdi = preparar_pdi_con_cierre(2025, 12)
pdi_filtered = filter_df_for_cmi_estrategico(pdi, id_column="Id")

# Revisar qué objetivos tiene Sostenibilidad DESPUÉS del filtrado
sost = pdi_filtered[pdi_filtered['Linea'] == 'Sostenibilidad']
print("=" * 80)
print("SOSTENIBILIDAD - Después del filtrado CMI")
print("=" * 80)
print(f"Registros: {len(sost)}")
print(f"\nObjetivos únicos:")
print(sost['Objetivo'].unique())
print(f"\nObjetivos agrupados:")
print(sost.groupby('Objetivo')['cumplimiento_pct'].agg(['count', 'mean']))

# Revisar el objetivo_df que se pasaría al sunburst
objetivo_df = pdi_filtered[["Linea", "Objetivo", "cumplimiento_pct"]].copy()
print("\n" + "=" * 80)
print("OBJETIVO_DF - Estructura para el sunburst")
print("=" * 80)
print(objetivo_df.groupby(['Linea', 'Objetivo']).size())

# Revisar específicamente Sostenibilidad en objetivo_df
print("\n" + "=" * 80)
print("SOSTENIBILIDAD en objetivo_df")
print("=" * 80)
sost_obj = objetivo_df[objetivo_df['Linea'] == 'Sostenibilidad']
print(f"Registros: {len(sost_obj)}")
print(f"Objetivos únicos: {sost_obj['Objetivo'].nunique()}")
for obj in sost_obj['Objetivo'].unique():
    print(f"  - {obj[:50]}...")

print("\n" + "=" * 80)
print("Generando sunburst...")
print("=" * 80)
fig = _build_sunburst(objetivo_df)

# Extraer labels, parents y text del trace
trace = fig.data[0]
print(f"\nLabels totales: {len(trace.labels)}")
print(f"Parents totales: {len(trace.parents)}")
print(f"Text totales: {len(trace.text)}")

# Encontrar índices de Sostenibilidad y sus objetivos
print(f"\n" + "=" * 80)
print("SUNBURST - Estructura renderizada")
print("=" * 80)

for idx, (label, parent, text) in enumerate(zip(trace.labels, trace.parents, trace.text)):
    if 'sostenibilidad' in label.lower() or 'sostenibilidad' in parent.lower():
        print(f"Índice {idx}: Label='{label[:40]}', Parent='{parent[:40]}', Text='{text[:40] if text else '(vacío)'}'")

