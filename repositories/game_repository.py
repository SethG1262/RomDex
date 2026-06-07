from sqlalchemy.exc import SQLAlchemyError

from services.db import SessionLocal
from models.game import Game


class GameRepository:
    def __init__(self):
        self.session = SessionLocal()

    def add_game(self, game_data):
        """
        Saves a game to the local SQLite database.
        game_data should be a dictionary from IGDB.
        """

        try:
            igdb_id = game_data.get("id")

            if igdb_id is None:
                raise ValueError("Game data is missing IGDB ID.")

            existing_game = self.get_game_by_igdb_id(igdb_id)

            if existing_game:
                return existing_game

            game = Game(
                igdb_id=igdb_id,
                title=game_data.get("name", "Unknown Title"),
                summary=game_data.get("summary"),
                storyline=game_data.get("storyline"),
                cover_url=self._extract_cover_url(game_data),
                release_year=self._extract_release_year(game_data),
                platform=self._extract_platform_name(game_data),
            )

            self.session.add(game)
            self.session.commit()
            self.session.refresh(game)

            return game

        except SQLAlchemyError as error:
            self.session.rollback()
            raise error

    def get_game_by_igdb_id(self, igdb_id):
        """
        Finds one game by its IGDB ID.
        """

        return (
            self.session
            .query(Game)
            .filter(Game.igdb_id == igdb_id)
            .first()
        )

    def get_all_games(self):
        """
        Returns all saved games from the local database.
        """

        return (
            self.session
            .query(Game)
            .order_by(Game.title)
            .all()
        )

    def delete_game(self, game_id):
        """
        Deletes a saved game by local database ID.
        """

        game = (
            self.session
            .query(Game)
            .filter(Game.id == game_id)
            .first()
        )

        if game:
            self.session.delete(game)
            self.session.commit()

        return game

    def close(self):
        """
        Closes the database session.
        """

        self.session.close()

    def _extract_cover_url(self, game_data):
        cover = game_data.get("cover")

        if not cover:
            return None

        image_id = cover.get("image_id")

        if not image_id:
            return None

        return f"https://images.igdb.com/igdb/image/upload/t_cover_big/{image_id}.jpg"

    def _extract_release_year(self, game_data):
        release_dates = game_data.get("release_dates")

        if not release_dates:
            return None

        first_date = release_dates[0]
        human_date = first_date.get("human")

        if not human_date:
            return None

        return human_date

    def _extract_platform_name(self, game_data):
        platforms = game_data.get("platforms")

        if not platforms:
            return None

        first_platform = platforms[0]

        return first_platform.get("name")

    def add_local_rom(self, rom_path):
        """
        Adds a local .nds ROM file to the library.
        """

        import os

        existing_game = self.get_game_by_rom_path(rom_path)

        if existing_game:
            return existing_game

        file_name = os.path.basename(rom_path)
        title = os.path.splitext(file_name)[0]

        game = Game(
            title=title,
            platform="Nintendo DS",
            file_name=file_name,
            rom_path=rom_path,
            status="Owned"
        )

        self.session.add(game)
        self.session.commit()
        self.session.refresh(game)

        return game
    def get_game_by_rom_path(self, rom_path):
        return (
            self.session
            .query(Game)
            .filter(Game.rom_path == rom_path)
            .first()
        )
    