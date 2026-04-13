import json
import streamlit as st
from pathlib import Path
from streamlit.components.v1 import html
from typing import Any

from streamlit_app.components import ui_components

st.set_page_config(page_title="Dashboard Cumplimiento", layout="wide")

# Render filtros y construir payload dinámico
filters = ui_components.render_filters()
payload = ui_components.build_dashboard_payload(filters)

BASE = Path(__file__).parent
tpl_dir = BASE / "components" / "ui" / "templates"

# Render modular: KPIs, Charts y Tabla como componentes separados
kp_tpl = (tpl_dir / "kpis.html").read_text(encoding='utf-8')
charts_tpl = (tpl_dir / "charts.html").read_text(encoding='utf-8')
table_tpl = (tpl_dir / "table.html").read_text(encoding='utf-8')
insights_tpl = (tpl_dir / "insights.html").read_text(encoding='utf-8')


def _json_default(o: Any):
	"""Serializador por defecto para json.dumps que convierte tipos de numpy/pandas."""
	try:
		import numpy as _np
		import pandas as _pd
	except Exception:
		_np = None
		_pd = None

	# pandas NA / numpy nan
	try:
		if _pd is not None and _pd.isna(o):
			return None
	except Exception:
		pass

	if _np is not None:
		if isinstance(o, _np.integer):
			return int(o)
		if isinstance(o, _np.floating):
			return float(o)
		if isinstance(o, _np.ndarray):
			return o.tolist()

	if _pd is not None:
		if isinstance(o, _pd.Series):
			return o.tolist()
		if isinstance(o, _pd.Timestamp):
			return o.isoformat()
		if isinstance(o, _pd.Timedelta):
			return str(o)

	# Fallback: intentar extraer valor con .item() si existe
	if hasattr(o, 'item'):
		try:
			return o.item()
		except Exception:
			pass

	# Finalmente, representar como string
	try:
		return str(o)
	except Exception:
		return None


# Inyectar payload en cada plantilla (usando serializador seguro)
payload_json = json.dumps(payload, ensure_ascii=False, default=_json_default)
kp_html = kp_tpl.replace('__DATA__', payload_json).replace('{{ kpis }}', '')
charts_html = charts_tpl.replace('__DATA__', payload_json)
table_html = table_tpl.replace('__DATA__', payload_json)
insights_html = insights_tpl.replace('__DATA__', payload_json)

st.markdown("<div style='display:flex;gap:16px'>", unsafe_allow_html=True)
html(kp_html, height=180, scrolling=False)
html(insights_html, height=140, scrolling=False)
html(charts_html, height=360, scrolling=True)
st.markdown("</div>", unsafe_allow_html=True)

html(table_html, height=320, scrolling=True)
