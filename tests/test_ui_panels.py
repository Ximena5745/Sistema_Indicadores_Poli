import streamlit as st
from streamlit_app.components import renderers


class _DummyExpander:
    def __init__(self, *a, **k):
        pass

    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        return False


def test_render_alert_and_narrative(monkeypatch):
    # Patch Streamlit renderers to no-op so tests don't require actual UI
    monkeypatch.setattr(st, "markdown", lambda *a, **k: None)
    monkeypatch.setattr(st, "caption", lambda *a, **k: None)
    monkeypatch.setattr(st, "write", lambda *a, **k: None)
    monkeypatch.setattr(st, "warning", lambda *a, **k: None)
    monkeypatch.setattr(st, "expander", lambda *a, **k: _DummyExpander())

    # Should not raise
    renderers.render_alert_strip("Prueba alerta", level="info")
    renderers.render_alert_strip("Prueba alerta critica", level="danger")
    renderers.render_narrative_panel("Título prueba", "Contenido de prueba", collapsed=False)
    renderers.render_narrative_panel("Título colapsado", "Contenido colapsado", collapsed=True)
