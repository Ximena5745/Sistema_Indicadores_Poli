"""
services/ai_analysis.py — Análisis de texto con Claude (Anthropic).

Extrae insights y oportunidades de mejora del análisis registrado por el usuario.
Requiere ANTHROPIC_API_KEY en st.secrets o variable de entorno.

DISEÑO: este módulo es PURO — no importa streamlit ni gestiona st.session_state.
La caché entre llamadas debe gestionarse en la capa UI con @st.cache_data.
"""

import os

_MODEL = "claude-haiku-4-5-20251001"

_PROMPT_TEMPLATE = """Eres un analista institucional experto en mejora continua y gestión por indicadores.

A continuación se presenta el análisis registrado por el responsable del indicador:

Indicador: {nombre}
Proceso: {proceso}
Categoría actual: {categoria}
Cumplimiento actual: {cumplimiento}

Análisis del responsable:
\"\"\"{analisis}\"\"\"

Tu tarea:
1. Identifica los principales insights del análisis (máximo 3 puntos concisos).
2. Si el análisis menciona causas, brechas o situaciones que lo justifiquen, propón oportunidades de mejora concretas y accionables (máximo 3).
3. Si el análisis es muy breve o no contiene información suficiente para extraer oportunidades, indícalo brevemente.

Responde en español, en formato de listas cortas y directas. No repitas el análisis original."""


def _get_client():
    """Retorna cliente Anthropic o None si la key no está configurada."""
    try:
        import anthropic

        # Intentar desde st.secrets solo si streamlit está disponible
        key = ""
        try:
            import streamlit as st

            key = st.secrets.get("ANTHROPIC_API_KEY", "")
        except Exception:
            pass
        if not key:
            key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            return None
        return anthropic.Anthropic(api_key=key)
    except Exception:
        return None


def analizar_texto_indicador(
    id_ind: str,
    nombre: str,
    proceso: str,
    categoria: str,
    cumplimiento: str,
    texto_analisis: str,
) -> str | None:
    """
    Llama a Claude para extraer insights y oportunidades de mejora.

    PURO: no gestiona estado ni caché. El caller debe usar @st.cache_data
    si desea evitar llamadas repetidas dentro de una sesión:

        @st.cache_data(ttl=3600, show_spinner=False)
        def _analisis_cacheado(id_ind, texto, ...):
            return analizar_texto_indicador(id_ind, texto, ...)

    Retorna el texto generado, o None si no hay API key o falla la llamada.
    """
    client = _get_client()
    if client is None:
        return None

    prompt = _PROMPT_TEMPLATE.format(
        nombre=nombre,
        proceso=proceso,
        categoria=categoria,
        cumplimiento=cumplimiento,
        analisis=texto_analisis,
    )

    try:
        message = client.messages.create(
            model=_MODEL,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()
    except Exception:
        return None

# --- CMI STRATEGIC PROMPTS ---

_PROMPT_CMI_FICHA = """Actúa como analista estratégico experto en el Cuadro de Mando Integral (CMI) de la Politécnica Grancolombiana.

Evalúa el siguiente indicador estratégico:
- Indicador: {nombre}
- Línea Estratégica: {linea}
- Objetivo Estratégico: {objetivo}
- Meta Anual: {meta}
- Ejecución Actual: {ejecucion}
- Nivel de Cumplimiento: {nivel} ({cumplimiento}%)

Con base en estos datos, genera:
1. Un diagnóstico muy breve y directo sobre el estado actual frente a la meta.
2. Un factor de riesgo principal si no se alcanza la meta.
3. Una recomendación táctica inmediata para el responsable.

Responde en formato Markdown, sin rodeos, estructurado en 3 viñetas claras."""

_PROMPT_CMI_LINEA = """Actúa como director de estrategia experto en el Cuadro de Mando Integral (CMI).

Analiza el desempeño de esta línea estratégica:
- Línea: {linea}
- Promedio de Cumplimiento: {cumplimiento_promedio}%
- Total Indicadores: {total_ind}
- Indicadores en Peligro/Alerta: {total_riesgo}

Datos de la tabla de indicadores:
{tabla_json}

Genera:
1. Un análisis sintético del desempeño de la línea (1 párrafo).
2. Cuál es el objetivo/indicador que requiere mayor atención urgente.
3. Dos directrices estratégicas clave para revertir desviaciones o potenciar aciertos.

Responde en formato Markdown, con un tono ejecutivo y propositivo."""

def analizar_ficha_cmi(nombre: str, linea: str, objetivo: str, meta: str, ejecucion: str, nivel: str, cumplimiento: str) -> str | None:
    """Ejecuta el PT-02 para la Ficha de Indicador del CMI."""
    client = _get_client()
    if client is None: return None
    
    prompt = _PROMPT_CMI_FICHA.format(
        nombre=nombre, linea=linea, objetivo=objetivo, meta=meta, ejecucion=ejecucion, nivel=nivel, cumplimiento=cumplimiento
    )
    
    try:
        msg = client.messages.create(model=_MODEL, max_tokens=400, messages=[{"role": "user", "content": prompt}])
        return msg.content[0].text.strip()
    except Exception:
        return None

def analizar_linea_cmi(linea: str, cumplimiento_promedio: str, total_ind: int, total_riesgo: int, tabla_json: str) -> str | None:
    """Ejecuta el PT-03 para el Análisis por Línea Estratégica del CMI."""
    client = _get_client()
    if client is None: return None
    
    prompt = _PROMPT_CMI_LINEA.format(
        linea=linea, cumplimiento_promedio=cumplimiento_promedio, total_ind=total_ind, total_riesgo=total_riesgo, tabla_json=tabla_json
    )
    
    try:
        msg = client.messages.create(model=_MODEL, max_tokens=600, messages=[{"role": "user", "content": prompt}])
        return msg.content[0].text.strip()
    except Exception:
        return None

