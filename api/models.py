from typing import Optional
from datetime import datetime, timezone, date
from sqlalchemy import Column, Dialect, Integer, String, DateTime, func, ForeignKey, Enum as SAEnum, UniqueConstraint, Float
from sqlalchemy.types import TypeDecorator, DateTime as SADateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db import Base
from pydantic import BaseModel, ConfigDict, field_validator
import enum, json

class Universe(Base):
    __tablename__ = "universes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable = False, index=True)
    description = Column(String(1024), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    members: Mapped[list["UniverseMember"]] = relationship(
        back_populates="universe", cascade="all, delete-orphan"
    )


class Stock(Base):
    __tablename__ ="stocks"
    id: Mapped[int] = mapped_column(Integer,primary_key= True, index = True)
    ticker: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    #backrefs
    memberships: Mapped[list["UniverseMember"]]= relationship(
        back_populates="stock", cascade ="all, delete-orphan"
    )

class UniverseMember(Base):
    __tablename__ = "universe_members"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    universe_id: Mapped[int] = mapped_column(
        ForeignKey("universes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True
    )

    __table_args__ = (UniqueConstraint("universe_id", "stock_id", name="uq_universe_stock"),)

    #relationships
    universe: Mapped["Universe"] = relationship(back_populates="members")
    stock: Mapped["Stock"]= relationship(back_populates="memberships")




#-- Pydantic v2 ----
class UniverseCreate(BaseModel):
    name: str
    description: Optional[str] = None

class UniverseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None


class UniverseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class UniverseScanRequest(BaseModel):
    template_id: int
    provider: str = "yahooquery"
    interval: str = "1d"

class UniverseScanResponse(BaseModel):
    universe_id: int
    template_id: int
    tickers_processed: int
    ohlcv_rows_written: int
    candidates_created: int
    error_count: int


class UtcDateTime(TypeDecorator):
    """
    stores datetimes as naive UTC in DB: returns tz-aware UTC datetimes in python.
    Works across SQLite(tz lost) and Postgres (tz preserved).
    """

    impl = SADateTime
    cache_ok=True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        # convert any tz-aware to UTC then drop tzinfo before storing

        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value
    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        #attach UTC tzinfo on load

        return value.replace(tzinfo=timezone.utc)


class CacheStatus(str, enum.Enum):
    fresh = "fresh"
    stale = "stale"
    fetching = "fetching"
    error = "error"
    unknown = "unknown"




class StockPriceCache(Base):
    __tablename__ = "stock_price_cache"

    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"),primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), primary_key=True) #e.g. yahooquery
    interval: Mapped[str] = mapped_column(String(8), primary_key=True) #e.g. 1d, 1h

    last_fetched_at: Mapped[Optional[datetime]] = mapped_column(UtcDateTime(), nullable=True)
    status: Mapped[CacheStatus] = mapped_column(
        SAEnum(CacheStatus, name = "cache_status"),
        nullable = False,
        default = CacheStatus.unknown
    )
    detail: Mapped[Optional[str]] = mapped_column(String(512), nullable=True) #last error or note

    #optional backref
    stock: Mapped["Stock"] = relationship(back_populates="price_cache", lazy="joined")


Stock.price_cache = relationship(
    "StockPriceCache",
    back_populates="stock",
    cascade="all, delete-orphan",
    lazy = "selectin"
)

Stock.signals = relationship(
"StockSignal",
back_populates="stock",
cascade="all, delete-orphan",
lazy="selectin",
)
    


class StockOHLCV(Base):
    __tablename__ = "stock_ohlcv"
    stock_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("stocks.id", ondelete="CASCADE"),
        primary_key=True,
    )
    as_of: Mapped[date] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), primary_key=True)
    interval: Mapped[str] = mapped_column(String(8), primary_key=True)

    open: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[Optional[float]] = mapped_column(Float, nullable=True)



class StockSignal(Base):
    __tablename__ ="stock_signals"
    stock_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("stocks.id", ondelete="CASCADE"),
        primary_key=True,
    )
    as_of: Mapped[date] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), primary_key=True)
    interval: Mapped[str] = mapped_column(String(8), primary_key=True)

    rsi: Mapped[Optional[float]]=mapped_column(Float, nullable=True)
    macd: Mapped[Optional[float]]=mapped_column(Float, nullable=True)
    macd_signal: Mapped[Optional[float]]=mapped_column(Float, nullable=True)
    ema_20: Mapped[Optional[float]]=mapped_column(Float, nullable=True)
    ema_50: Mapped[Optional[float]]=mapped_column(Float, nullable=True)
    bb_upper: Mapped[Optional[float]]=mapped_column(Float, nullable=True)
    bb_lower: Mapped[Optional[float]]=mapped_column(Float, nullable=True)
    

    stock: Mapped["Stock"] = relationship(back_populates="signals", lazy="joined")

class TemplateKind(str, enum.Enum):
    risk = "risk"
    trade = "trade"
    strategy = "strategy"

class StrategyTemplate(Base):
    __tablename__ = "strategy_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    kind: Mapped[TemplateKind] = mapped_column(
        SAEnum(TemplateKind, name="template_kind"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    config_json: Mapped[str] = mapped_column(String(8192), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("kind", "name","version", name="uq_template_kind_name_version"),
    )

class TemplateCreate(BaseModel):
    kind: TemplateKind
    name: str
    version: int =1
    description: Optional[str] = None
    config_json: str

    @field_validator("config_json")
    @classmethod
    def validate_config_json(cls,v: str) -> str:
        try: 
            parsed = json.loads(v)
        except json.JSONDecodeError as exc:
            raise ValueError("config_json must be a valid JSON string") from exc
        if not isinstance(parsed, dict):
            raise ValueError("config_json must decode to a JSON object")

        rules = parsed.get("entry_rules", [])
        if not isinstance(rules, list):
            raise ValueError("entry_rules must be a list")
        allowed_ops = {"lt","lte","gt","gte","eq"}
        for i, rule in enumerate(rules):
            if not isinstance(rule, dict):
                raise ValueError(f"entry_rules[{i}] must be an object")
            field = rule.get("field")
            op = rule.get("op")
            value = rule.get("value")
            if not isinstance(field, str) or not field:
                raise ValueError(f"entry_rules[{i}].field must be a non-empty string")
            if op not in allowed_ops:
                raise ValueError(f"entry_rules[{i}].op must be one of {sorted(allowed_ops)}")
            if not isinstance(value, (int, float)):
                raise ValueError(f"entry_rules[{i}].value must be numeric")
            
        
        score_field = parsed.get("score_field")
        if score_field is not None and (not isinstance(score_field, str) or not score_field):
            raise ValueError("score_field must be a non-empty string when provided")
        return v
    
    
        


class TemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: TemplateKind
    name: str
    version: int
    description: Optional[str] = None
    config_json: str
    created_at: Optional[datetime] = None

class TemplateUpdate(BaseModel):
    name: str | None = None
    version: int | None = None
    description: Optional[str] = None
    config_json: str | None = None
    @field_validator("config_json")
    @classmethod
    def validate_config_json(cls,v: str | None) -> str | None:
        if v is None:
            return None
        try: 
            parsed = json.loads(v)
        except json.JSONDecodeError as exc:
            raise ValueError("config_json must be a valid JSON string") from exc
        if not isinstance(parsed, dict):
            raise ValueError("config_json must decode to a JSON object")
        return v


class CandidateStatus(str, enum.Enum):
    proposed = "proposed"
    selected = "selected"
    rejected = "rejected"

class CandidateCreate(BaseModel):
    universe_id: int
    template_id: int
    ticker: str
    score: float
    status: CandidateStatus = CandidateStatus.proposed
    reason_code: Optional[str] = None
    payload_json: str

class CandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    universe_id: int
    template_id: int
    ticker: str
    as_of: datetime
    score: float
    status: CandidateStatus
    reason_code: Optional[str] = None
    payload_json: str


class TradeCandidate(Base):
    """
    CandidateStatus defines controlled lifecycle states for one generated candidate.
    TradeCandidate is the persistence record for candidate pipeline output.
    universe_id ties candidate to selection scope.
    template_id ties candidate to the rule/template that produced it.
    ticker records underlying symbol for quick filtering.
    as_of stores generation timestamp.
    score stores deterministic ranking value.
    status tracks proposed/selected/rejected state transitions.
    reason_code captures explainable rejection or selection label.
    payload_json stores full candidate context snapshot for later audit/journal.
    """
    __tablename__ = "trade_candidates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    universe_id: Mapped[int] = mapped_column(ForeignKey("universes.id", ondelete="CASCADE"), nullable=False, index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("strategy_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    ticker: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
   
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[CandidateStatus] = mapped_column(SAEnum(CandidateStatus, name="candidate_status"), nullable=False, default=CandidateStatus.proposed)

    reason_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    payload_json: Mapped[str] = mapped_column(String(8192), nullable=False)

class GenerateCandidateRequest(BaseModel):
    universe_id: int
    template_id: int
    provider: str = "yahooquery"
    interval: str = "1d"


class GenerateCandidateResponse(BaseModel):
    universe_id: int
    template_id: int
    created_count: int