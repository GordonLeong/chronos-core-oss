from __future__ import annotations
from typing import Dict

from services.contracts import (
    PriceAdapter,
    OptionChainAdapter,
    VenueAdapter,
    ExecutionAdapter,
    AccountStateAdapter
)

_BUILTINS_LOADED = False

_PRICE_REGISTRY: Dict[str, PriceAdapter] = {}
_OPTION_REGISTRY: Dict[str, OptionChainAdapter] = {}
_VENUE_REGISTRY: Dict[str, VenueAdapter] = {}
_EXECUTION_REGISTRY: Dict[str, ExecutionAdapter] = {}
_ACCOUNT_REGISTRY: Dict[str, AccountStateAdapter] = {}

# --- Registration Methods ---

def register_price_adapter(name: str, adapter: PriceAdapter) -> None:
    _PRICE_REGISTRY[name] = adapter

def register_option_adapter(name: str, adapter: OptionChainAdapter) -> None:
    _OPTION_REGISTRY[name] = adapter

def register_execution_adapter(name: str, adapter: ExecutionAdapter) -> None:
    _EXECUTION_REGISTRY[name] = adapter

def register_venue_adapter(name: str, adapter: VenueAdapter) -> None:
    _VENUE_REGISTRY[name] = adapter

def register_account_adapter(name: str, adapter: AccountStateAdapter) -> None:
    _ACCOUNT_REGISTRY[name] = adapter


def _ensure_builtins_loaded() -> None:
    global _BUILTINS_LOADED
    if _BUILTINS_LOADED:
        return

    # Import default adapters for their side-effects (registration calls)
    from services.adapters import yahooquery_adapter  # noqa: F401
    from services.adapters import yahoo_options_adapter  # noqa: F401
    from services.adapters import local_sim_execution  # noqa: F401

    _BUILTINS_LOADED = True

# --- Retrieval Methods ---

def get_price_adapter(name: str) -> PriceAdapter:
    _ensure_builtins_loaded()
    try:
        return _PRICE_REGISTRY[name]
    except KeyError:
        raise ValueError(f"unknown price adapter: {name!r}. Registered: {list(_PRICE_REGISTRY)}")

def get_option_adapter(name: str) -> OptionChainAdapter:
    _ensure_builtins_loaded()
    try:
        return _OPTION_REGISTRY[name]
    except KeyError:
        raise ValueError(f"unknown option adapter: {name!r}. Registered: {list(_OPTION_REGISTRY)}")

def get_execution_adapter(name: str) -> ExecutionAdapter:
    _ensure_builtins_loaded()
    try:
        return _EXECUTION_REGISTRY[name]
    except KeyError:
        raise ValueError(f"unknown execution adapter: {name!r}. Registered: {list(_EXECUTION_REGISTRY)}")

def get_venue_adapter(name: str) -> VenueAdapter:
    _ensure_builtins_loaded()
    try:
        return _VENUE_REGISTRY[name]
    except KeyError:
        raise ValueError(f"unknown venue adapter: {name!r}. Registered: {list(_VENUE_REGISTRY)}")

def get_account_adapter(name: str) -> AccountStateAdapter:
    _ensure_builtins_loaded()
    try:
        return _ACCOUNT_REGISTRY[name]
    except KeyError:
        raise ValueError(f"unknown account adapter: {name!r}. Registered: {list(_ACCOUNT_REGISTRY)}")
