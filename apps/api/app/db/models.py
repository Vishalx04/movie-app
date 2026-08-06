from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.db.database import Base

class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

