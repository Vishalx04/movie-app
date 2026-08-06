from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/movie_db"

engine = create_engine(DATABASE_URL)

sessionLocal = sessionmaker(autocommit = False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()