from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db import Base
from pydantic import BaseModel, ConfigDict

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