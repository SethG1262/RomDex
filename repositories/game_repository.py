from sqlalchemy.exc import SQLAlchemyError

from services.db import SessionLocal
from models.game import Game


# Repository class responsible for database operations related to Game objects.
# This keeps database logic separate from the UI and service layers.
class GameRepository:
    def __init__(self):
        # Creates a database session that this repository will use.
        self.session = SessionLocal()

    def add_game(self, game_data):
        """
        Saves a game from IGDB to the local SQLite database.
        """

        try:
            # Gets the IGDB ID from the API game data.
            # This is used to prevent saving duplicate IGDB games.
            igdb_id = game_data.get("id")

            if igdb_id is None:
                raise ValueError("Game data is missing IGDB ID.")

            # Checks if the game already exists in the database.
            existing_game = self.get_game_by_igdb_id(igdb_id)

            # If the game already exists, return it instead of creating a duplicate.
            if existing_game:
                return existing_game

            # Creates a new Game model object using data from IGDB.
            game = Game(
                igdb_id=igdb_id,
                title=game_data.get("name", "Unknown Title"),
                summary=game_data.get("summary"),
                storyline=game_data.get("storyline"),
                cover_url=self._extract_cover_url(game_data),
                release_year=self._extract_release_year(game_data),
                platform=self._extract_platform_name(game_data),
                status="Saved"
            )

            # Adds the new game to the database session.
            self.session.add(game)

            # Saves the changes permanently to the database.
            self.session.commit()

            # Refreshes the object so it includes generated database values like id.
            self.session.refresh(game)

            return game

        except SQLAlchemyError as error:
            # Rolls back the transaction if a database error happens.
            self.session.rollback()
            raise error

    def add_local_rom(self, rom_path):
        """
        Adds a local .nds ROM file to the library.
        """

        import os

        try:
            # Checks if this ROM path already exists in the database.
            existing_game = self.get_game_by_rom_path(rom_path)

            # Prevents duplicate ROM file entries.
            if existing_game:
                return existing_game

            # Gets the file name from the full file path.
            file_name = os.path.basename(rom_path)

            # Uses the file name without extension as the game title.
            title = os.path.splitext(file_name)[0]

            # Creates a Game object for a local ROM file.
            game = Game(
                title=title,
                platform="Nintendo DS",
                file_name=file_name,
                rom_path=rom_path,
                status="Owned"
            )

            # Adds and saves the local ROM entry.
            self.session.add(game)
            self.session.commit()
            self.session.refresh(game)

            return game

        except SQLAlchemyError as error:
            # Undo database changes if the insert fails.
            self.session.rollback()
            raise error

    def get_game_by_id(self, game_id):
        """
        Finds one game by local database ID.
        """

        # Queries the Game table for the first game matching the local database id.
        return (
            self.session
            .query(Game)
            .filter(Game.id == game_id)
            .first()
        )

    def get_game_by_igdb_id(self, igdb_id):
        """
        Finds one game by its IGDB ID.
        """

        # Queries the Game table for the first game matching the IGDB id.
        return (
            self.session
            .query(Game)
            .filter(Game.igdb_id == igdb_id)
            .first()
        )

    def get_game_by_rom_path(self, rom_path):
        """
        Finds one game by its local ROM file path.
        """

        # Queries the Game table for the first game with the same ROM file path.
        return (
            self.session
            .query(Game)
            .filter(Game.rom_path == rom_path)
            .first()
        )

    def get_all_games(self):
        """
        Returns all saved games from the local database.
        """

        # Returns all games ordered alphabetically by title.
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

        try:
            # Finds the game before trying to delete it.
            game = self.get_game_by_id(game_id)

            # Only delete if the game exists.
            if game:
                self.session.delete(game)
                self.session.commit()

            return game

        except SQLAlchemyError as error:
            # Roll back if the delete operation fails.
            self.session.rollback()
            raise error

    def close(self):
        """
        Closes the database session.
        """

        # Closes the session when the repository is no longer needed.
        self.session.close()

    def _extract_cover_url(self, game_data):
        # Gets cover information from the IGDB game data.
        cover = game_data.get("cover")

        if not cover:
            return None

        # Gets IGDB's image id for the cover art.
        image_id = cover.get("image_id")

        if not image_id:
            return None

        # Builds a full IGDB cover image URL from the image id.
        return f"https://images.igdb.com/igdb/image/upload/t_cover_big_2x/{image_id}.jpg"

    def _extract_release_year(self, game_data):
        # Gets release date data from the IGDB game data.
        release_dates = game_data.get("release_dates")

        if not release_dates:
            return None

        # Uses the first release date listed by IGDB.
        first_date = release_dates[0]
        human_date = first_date.get("human")

        if not human_date:
            return None

        return human_date

    def _extract_platform_name(self, game_data):
        # Gets platform data from the IGDB game data.
        platforms = game_data.get("platforms")

        if not platforms:
            return None

        # Uses the first platform listed by IGDB.
        first_platform = platforms[0]

        return first_platform.get("name")