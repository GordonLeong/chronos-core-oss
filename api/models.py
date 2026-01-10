from typing import Optional
from datetime import datetime, timezone, date
from sqlalchemy import Column, Dialect, Integer, String, DateTime, func, ForeignKey, Enum as SAEnum, UniqueConstraint, Float
from sqlalchemy.types import TypeDecorator, DateTime as SADateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db import Base
from pydantic import BaseModel, ConfigDict
import enum

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