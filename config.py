"""
config.py — Re-export de core/config.py para compatibilidad con imports legacy.

Usar preferentemente: `from core.config import ...`
"""
from __future__ import annotations

import importlib
from types import ModuleType


_core_config = importlib.import_module("core.config")

# Reexporta simbolos publicos del modulo canonico.
# Se excluyen nombres privados y modulos internos.
__all__ = [
    name
    for name, value in vars(_core_config).items()
    if not name.startswith("_") and not isinstance(value, ModuleType)
]

for _name in __all__:
    globals()[_name] = getattr(_core_config, _name)
