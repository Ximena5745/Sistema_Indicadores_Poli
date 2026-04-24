from streamlit_app.pages.resumen_general import _build_sunburst, filter_df_for_cmi_estrategico
from services.strategic_indicators import preparar_pdi_con_cierre
import pandas as pd

pdi = preparar_pdi_con_cierre(2025, 12)
pdi_filtered = filter_df_for_cmi_estrategico(pdi, id_column='Id')
objetivo_df = pdi_filtered[['Linea', 'Objetivo', 'cumplimiento_pct']].copy()
fig = _build_sunburst(objetivo_df)

trace = fig.data[0]

print("=" * 80)
print("SUNBURST - Labels, Values, y Customdata")
print("=" * 80)
print(f"{'Idx':<4} {'Label':<50} {'Parent':<30} {'Value':<8} {'Customdata'}")
print("-" * 150)

for idx, (label, parent, value, custom) in enumerate(zip(trace.labels, trace.parents, trace.values, trace.customdata)):
    val_str = str(value) if value else "0"
    custom_str = str(custom[0]) if custom else "None"
    label_short = label[:48] if label else "(vacío)"
    parent_short = parent[:28] if parent else "(root)"
    print(f"{idx:<4} {label_short:<50} {parent_short:<30} {val_str:<8} {custom_str}")

print("\n" + "=" * 80)
print("ANÁLISIS DE SOSTENIBILIDAD")
print("=" * 80)
for idx, (label, parent, value, custom) in enumerate(zip(trace.labels, trace.parents, trace.values, trace.customdata)):
    if 'sostenibilidad' in label.lower() or 'sostenibilidad' in parent.lower():
        print(f"Índice {idx}:")
        print(f"  Label: {label}")
        print(f"  Parent: {parent}")
        print(f"  Value: {value}")
        print(f"  Customdata: {custom}")
        print()
