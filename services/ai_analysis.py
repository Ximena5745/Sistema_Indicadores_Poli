"""
services/ai_analysis.py — Análisis de texto con Claude (Anthropic).

Extrae insights y oportunidades de mejora del análisis registrado por el usuario.
Requiere ANTHROPIC_API_KEY en st.secrets o variable de entorno.

DISEÑO: este módulo es PURO — no importa streamlit ni gestiona st.session_state.
La caché entre llamadas debe gestionarse en la capa UI con @st.cache_data.
"""

import os
import json

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


def _to_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _analisis_heuristico_ficha(nombre: str, meta: str, ejecucion: str, nivel: str, cumplimiento: str) -> str:
    cump = _to_float(cumplimiento, 0.0)
    if cump >= 100:
        estado = "El indicador supera la meta y presenta desempeño favorable en el corte actual."
        riesgo = "Riesgo de sobreconfianza: sostener el resultado sin plan de continuidad puede generar retroceso en el siguiente periodo."
        accion = "Estandarizar las prácticas que explican el resultado y documentar un plan de sostenibilidad con hitos trimestrales."
    elif cump >= 95:
        estado = "El indicador está cerca de la meta y requiere ajuste fino para consolidar cumplimiento."
        riesgo = "Riesgo de cierre en alerta por variaciones menores de ejecución o retrasos operativos."
        accion = "Definir acciones de corto plazo con responsables y seguimiento semanal hasta el próximo corte."
    else:
        estado = "El indicador presenta brecha frente a la meta y requiere intervención prioritaria."
        riesgo = "Riesgo de incumplimiento del objetivo estratégico asociado y efectos en el balance global de la línea."
        accion = "Implementar plan de recuperación con metas parciales y control quincenal de avance real vs meta."

    return (
        f"- **Diagnóstico:** {estado}\\n"
        f"- **Riesgo principal:** {riesgo}\\n"
        f"- **Recomendación táctica inmediata:** {accion}"
    )


def _analisis_heuristico_linea(
    linea: str,
    cumplimiento_promedio: str,
    total_ind: int,
    total_riesgo: int,
    tabla_json: str,
) -> str:
    cump = _to_float(cumplimiento_promedio, 0.0)
    riesgo_ratio = (float(total_riesgo) / float(total_ind)) if total_ind else 0.0

    if cump >= 100:
        estado = "La línea presenta desempeño agregado favorable y supera la meta institucional."
    elif cump >= 95:
        estado = "La línea presenta desempeño estable, con brechas acotadas que requieren monitoreo cercano."
    else:
        estado = "La línea presenta desviación relevante frente a la meta y requiere priorización de acciones."

    indic_txt = "No se pudo identificar un indicador crítico con los datos disponibles."
    try:
        rows = json.loads(tabla_json or "[]")
        if isinstance(rows, list) and rows:
            def _score(row):
                nivel = str(row.get("Nivel de cumplimiento", "")).strip().lower()
                cump_row = _to_float(row.get("cumplimiento_pct"), 0.0)
                if "peligro" in nivel:
                    return (0, cump_row)
                if "alerta" in nivel:
                    return (1, cump_row)
                return (2, cump_row)

            crit = sorted(rows, key=_score)[0]
            indic = str(crit.get("Indicador", "Indicador sin nombre")).strip() or "Indicador sin nombre"
            objetivo = str(crit.get("Objetivo", "Objetivo no informado")).strip() or "Objetivo no informado"
            nivel = str(crit.get("Nivel de cumplimiento", "Sin nivel")).strip() or "Sin nivel"
            cump_row = _to_float(crit.get("cumplimiento_pct"), 0.0)
            indic_txt = (
                f"Se prioriza **{indic}** (objetivo: {objetivo}), con nivel **{nivel}** "
                f"y cumplimiento de **{cump_row:.1f}%**."
            )
    except Exception:
        pass

    dir_1 = "Enfocar seguimiento semanal en indicadores en riesgo y asegurar cierre de brechas operativas de corto plazo."
    if riesgo_ratio > 0.25:
        dir_2 = "Activar comité táctico por línea con responsables por objetivo y compromisos de recuperación por periodo."
    else:
        dir_2 = "Consolidar prácticas de los indicadores con mejor desempeño para replicarlas en objetivos rezagados."

    return (
        f"{estado} En la línea **{linea}**, se observan **{total_riesgo}** indicadores en alerta/peligro sobre **{total_ind}**.\\n\\n"
        f"- **Foco urgente:** {indic_txt}\\n"
        f"- **Directriz 1:** {dir_1}\\n"
        f"- **Directriz 2:** {dir_2}"
    )

def analizar_ficha_cmi(nombre: str, linea: str, objetivo: str, meta: str, ejecucion: str, nivel: str, cumplimiento: str) -> str | None:
    """Ejecuta el PT-02 para la Ficha de Indicador del CMI."""
    client = _get_client()
    if client is None:
        return _analisis_heuristico_ficha(nombre, meta, ejecucion, nivel, cumplimiento)
    
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
    if client is None:
        return _analisis_heuristico_linea(linea, cumplimiento_promedio, total_ind, total_riesgo, tabla_json)
    
    prompt = _PROMPT_CMI_LINEA.format(
        linea=linea, cumplimiento_promedio=cumplimiento_promedio, total_ind=total_ind, total_riesgo=total_riesgo, tabla_json=tabla_json
    )
    
    try:
        msg = client.messages.create(model=_MODEL, max_tokens=600, messages=[{"role": "user", "content": prompt}])
        return msg.content[0].text.strip()
    except Exception:
        return None

