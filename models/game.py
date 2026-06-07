from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from services.db import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    platform = Column(String, nullable=True)
    genre = Column(String, nullable=True)
    status = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
