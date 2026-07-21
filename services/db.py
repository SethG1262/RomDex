import os
from sqlalchemy import create_engine, inspect, text
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
    _migrate_games_cloud_id()


def _migrate_games_cloud_id():
    """
    Adds stable cloud IDs to databases created by older RomDex versions.

    Existing IGDB entries retain their IGDB identity. Existing local-only
    entries retain the legacy ``local_<database id>`` identity so upgrading
    does not create duplicate Firestore documents on the next sync.
    """
    inspector = inspect(engine)

    if "games" not in inspector.get_table_names():
        return

    column_names = {
        column["name"]
        for column in inspector.get_columns("games")
    }

    with engine.begin() as connection:
        if "cloud_id" not in column_names:
            connection.execute(
                text("ALTER TABLE games ADD COLUMN cloud_id VARCHAR")
            )

        connection.execute(
            text(
                """
                UPDATE games
                SET cloud_id = CASE
                    WHEN igdb_id IS NOT NULL
                        THEN 'igdb_' || CAST(igdb_id AS TEXT)
                    ELSE 'local_' || CAST(id AS TEXT)
                END
                WHERE cloud_id IS NULL OR TRIM(cloud_id) = ''
                """
            )
        )

        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "ix_games_cloud_id ON games (cloud_id)"
            )
        )


def get_db():
    # Creates a new database session.
    db = SessionLocal()

    try:
        # Gives the session to whatever part of the program needs database access.
        yield db

    finally:
        # Always closes the session after it is done being used.
        db.close()
