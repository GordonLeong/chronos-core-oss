from __future__ import annotations
from typing import Protocol, runtime_checkable, Dict


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

_REGISTRY: Dict[str, PriceProvider] = {}

def register_provider(provider: PriceProvider) -> None:
    _REGISTRY[provider.name] = provider

def get_provider(name: str) -> PriceProvider:
    try:
        return _REGISTRY[name]
    
    except KeyError:
        raise ValueError(f"unknown provider: {name!r}. Registered: {list(_REGISTRY)}")
