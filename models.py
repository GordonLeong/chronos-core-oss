from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, func
from db import Base
from pydantic import BaseModel, ConfigDict

class Universe(Base):
    __tablename__ = "universes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable = False, index=True)
    description = Column(String(1024), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


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