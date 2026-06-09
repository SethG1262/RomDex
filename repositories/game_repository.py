import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# Gets the root folder of the project.
# This makes the database path work even if this file is inside the /services folder.
ROOT = os.path.dirname(os.path.dirname(__file__))

# Creates the path to the data folder where the SQLite database will be stored.
DB_DIR = os.path.join(ROOT, "data")

# Creates the full path to the romdex database file.
DB_PATH = os.path.join(DB_DIR, "romdex.db")

# Makes sure the data folder exists before trying to create/use the database file.
os.makedirs(DB_DIR, exist_ok=True)

# SQLite database connection string used by SQLAlchemy.
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Creates the SQLAlchemy engine, which manages the connection to the database.
# check_same_thread=False allows the SQLite connection to be used with Tkinter's app flow.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Creates a database session factory.
# Each session is used to communicate with the database.
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

# Base class used by SQLAlchemy models.
# Model classes inherit from this so SQLAlchemy can map them to database tables.
Base = declarative_base()


def init_db():
    # Creates all database tables that are defined by models inheriting from Base.
    # If the tables already exist, SQLAlchemy will leave them alone.
    Base.metadata.create_all(bind=engine)


def get_db():
    # Creates a new database session.
    db = SessionLocal()

    try:
        # Gives the session to whatever part of the program needs database access.
        yield db

    finally:
        # Always closes the session after it is done being used.
        db.close()