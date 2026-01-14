from __future__ import annotations
from typing import Protocol, Dict, runtime_checkable

from ohlcv import OHLCVRow
from services.signals import SignalRow


_BUILTINS_LOADED = False
_REGISTRY: Dict[str, "TAProvider"] = {}


@runtime_checkable
class TAProvider(Protocol):
    name: str

    def compute_signals(self, rows: list[OHLCVRow]) -> list[SignalRow]:
        """
        Return signal rows computed from OHLCV input.
        """
        ...


def register_ta_provider(provider: TAProvider) -> None:
    _REGISTRY[provider.name] = provider


def _ensure_builtins_loaded() -> None:
    global _BUILTINS_LOADED
    if _BUILTINS_LOADED:
        return

    # Import default providers for side effects (register_ta_provider)
    from services.providers import pandas_ta_provider  # noqa: F401

    _BUILTINS_LOADED = True


def get_ta_provider(name: str) -> TAProvider:
    _ensure_builtins_loaded()
    try:
        return _REGISTRY[name]
    except KeyError:
        raise ValueError(f"unknown TA provider: {name!r}. Registered: {list(_REGISTRY)}")
