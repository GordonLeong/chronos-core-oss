from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, func
from db import Base
from pydantic import BaseModel

class Universe(Base):
    __tablename__ = "universes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), unique = True,nullable = False, index=True)
    description = Column(String(1024), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class UniverseCreate(BaseModel):
    name: str
    description: Optional[str] = None

class UniverseRead(UniverseCreate):
    id: int
    created_at: Optional[str]

    class Config:
        orm_mode = True