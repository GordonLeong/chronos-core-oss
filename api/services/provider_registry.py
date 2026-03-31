from __future__ import annotations
from typing import Protocol, runtime_checkable, Dict, List, Optional
from datetime import date
from ohlcv import OHLCVRow

_BUILTINS_LOADED = False

from services.contracts import PriceAdapter

_BUILTINS_LOADED = False

_REGISTRY: Dict[str, PriceAdapter] = {}

def register_provider(name: str, provider: PriceAdapter) -> None:
    _REGISTRY[name] = provider

def _ensure_builtins_loaded() -> None:
    global _BUILTINS_LOADED
    if _BUILTINS_LOADED:
        return

    # Import default providers for their side-effects (register_provider calls)
    from services.providers import yahooquery_adapter  # noqa: F401

    _BUILTINS_LOADED = True

def get_provider(name: str) -> PriceAdapter:
    _ensure_builtins_loaded()
    try:
        return _REGISTRY[name]
    
    except KeyError:
        raise ValueError(f"unknown provider: {name!r}. Registered: {list(_REGISTRY)}")
