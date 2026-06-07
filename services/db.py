import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

ROOT = os.path.dirname(os.path.dirname(__file__))
DB_DIR = os.path.join(ROOT, "data")
DB_PATH = os.path.join(DB_DIR, "romdex.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
