from sqlalchemy import Column, Integer, String, Text

from services.db import Base


# Game model class.
# This class represents the "games" table in the SQLite database.
class Game(Base):
    # Name of the database table created by SQLAlchemy
    __tablename__ = "games"

    # Local database ID.
    # This is the primary key for each game record.
    id = Column(Integer, primary_key=True, index=True)

    # Stable identity used for cloud synchronization.
    # Unlike the local database ID, this value follows the game when its
    # metadata is imported on another RomDex installation.
    cloud_id = Column(String, unique=True, nullable=True, index=True)

    # IGDB metadata fields.
    # These store game information collected from the IGDB API.
    igdb_id = Column(Integer, unique=True, nullable=True)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    storyline = Column(Text, nullable=True)
    cover_url = Column(String, nullable=True)
    release_year = Column(String, nullable=True)
    platform = Column(String, nullable=True)

    # Local ROM file information.
    # These fields store file details when the user adds a local .nds file.
    file_name = Column(String, nullable=True)
    rom_path = Column(String, unique=True, nullable=True)

    # Library ownership/status.
    # Example values could be "Owned" or "Saved".
    status = Column(String, nullable=True, default="Owned")

    def __repr__(self):
        # Returns a readable text version of the Game object for debugging.
        return f"<Game title={self.title}>"
