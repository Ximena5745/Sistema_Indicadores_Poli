"""Compatibilidad legacy para `streamlit_app.services.strategic_indicators`.

Ubicacion canonica: `services.strategic_indicators`
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _load_canonical_module():
    """Carga el modulo canonico y preserva fallback de path legacy."""
    try:
        return importlib.import_module("services.strategic_indicators")
    except ImportError:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        return importlib.import_module("services.strategic_indicators")


_canonical = _load_canonical_module()
__all__ = list(getattr(_canonical, "__all__", []))

for _name in __all__:
    globals()[_name] = getattr(_canonical, _name)
