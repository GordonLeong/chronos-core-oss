from __future__ import annotations
from typing import Protocol, runtime_checkable, Dict, List, Optional
from datetime import date
from ohlcv import OHLCVRow

_BUILTINS_LOADED = False

@runtime_checkable
class PriceProvider(Protocol):
    """
    Adapter interface for OHLCV providers
    
    """
    name: str
    def fetch_ohlcv(self, ticker: str, interval: str) -> int:
        """
        Return number of rows fetched or 0 if none. Raise on fatal errors.
        """
        ...
    def fetch_ohlcv_rows(
            self, 
            ticker: str,
            interval: str,
    ) -> list[OHLCVRow]:
        """
        Return normalized OHLCV rows for (ticker, interval).

        Each tuple is:
        (date, open, high, low, close, volume_or_None)
        """
        ...
        

_REGISTRY: Dict[str, PriceProvider] = {}

def register_provider(provider: PriceProvider) -> None:
    _REGISTRY[provider.name] = provider

def _ensure_builtins_loaded() -> None:
    global _BUILTINS_LOADED
    if _BUILTINS_LOADED:
        return

    # Import default providers for their side-effects (register_provider calls)
    from services.providers import yahooquery_adapter  # noqa: F401

    _BUILTINS_LOADED = True

def get_provider(name: str) -> PriceProvider:
    _ensure_builtins_loaded()
    try:
        return _REGISTRY[name]
    
    except KeyError:
        raise ValueError(f"unknown provider: {name!r}. Registered: {list(_REGISTRY)}")
