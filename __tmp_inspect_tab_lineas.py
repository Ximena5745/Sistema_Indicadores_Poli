import sys
sys.path.insert(0, r'c:/Users/lxisilva/OneDrive - Politécnico Grancolombiano/Documentos/Proyectos/Sistema_Indicadores_Poli')
import inspect
from streamlit_app.components.cmi_tabs import tab_lineas as t
print('module file:', t.__file__)
print('function source start:')
print('\n'.join(inspect.getsource(t._render_subtab_resumen).splitlines()[:20]))
