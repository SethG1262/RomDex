from sqlalchemy import Column, Integer, String, Text

from services.db import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)

    # IGDB metadata
    igdb_id = Column(Integer, unique=True, nullable=True)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    storyline = Column(Text, nullable=True)
    cover_url = Column(String, nullable=True)
    release_year = Column(String, nullable=True)
    platform = Column(String, nullable=True)

    # Local ROM file info
    file_name = Column(String, nullable=True)
    rom_path = Column(String, unique=True, nullable=True)

    # Library ownership/status
    status = Column(String, nullable=True, default="Owned")

    def __repr__(self):
        return f"<Game title={self.title}>"