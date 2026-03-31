from typing import Protocol, Optional
from datetime import date, datetime
from pydantic import BaseModel

# --- Shared Typings ---

OHLCVRow = tuple[date, float, float, float, float, Optional[float]]
# as_of, open, high, low, close, volume

class OptionStrike(BaseModel):
    strike: float
    call_bid: Optional[float]
    call_ask: Optional[float]
    call_mid: Optional[float]
    call_iv: Optional[float]
    put_bid: Optional[float]
    put_ask: Optional[float]
    put_mid: Optional[float]
    put_iv: Optional[float]

class OptionChainSnapshot(BaseModel):
    underlying_ticker: str
    as_of: datetime
    # Map of DTE -> expiry date -> list of strikes
    # Just list of strikes for a specific target expiry or across expiries?
    # Simple list of expiries for now, with their strikes
    expiries: dict[str, list[OptionStrike]] # yyyy-mm-dd -> strikes

class ExecutionIntent(BaseModel):
    ticker: str
    action: str  # "buy", "sell", "sell_short", "buy_to_cover" etc.
    quantity: int
    order_type: str # "market", "limit"
    limit_price: Optional[float] = None
    # Add legs for options later if needed

class ExecutionFill(BaseModel):
    intent: ExecutionIntent
    filled_at: datetime
    filled_qty: int
    avg_price: float
    status: str # "filled", "rejected", "partial"

class AccountState(BaseModel):
    cash: float
    buying_power: float
    positions: dict[str, int] # ticker -> qty

class VenueProfile(BaseModel):
    name: str
    allows_shorting: bool
    allows_options: bool
    options_level: int
    margin_multiplier: float

# --- Adapter Protocols ---

class PriceAdapter(Protocol):
    def fetch_ohlcv_rows(self, ticker: str, interval: str) -> list[OHLCVRow]:
        ...

class OptionChainAdapter(Protocol):
    def fetch_chain_snapshot(self, ticker: str) -> OptionChainSnapshot:
        ...

class VenueAdapter(Protocol):
    def get_venue_profile(self) -> VenueProfile:
        ...

class ExecutionAdapter(Protocol):
    async def submit_intent(self, intent: ExecutionIntent) -> ExecutionFill:
        ...

class AccountStateAdapter(Protocol):
    def get_account_state(self) -> AccountState:
        ...
