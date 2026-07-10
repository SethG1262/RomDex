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
                status="Saved"
            )

            self.session.add(game)
            self.session.commit()
            self.session.refresh(game)

            return game

        except SQLAlchemyError as error:
            self.session.rollback()
            raise error

    def add_local_rom(self, rom_path):
        """
        Adds a local .nds ROM file to the library.
        """
        import os

        try:
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

        except SQLAlchemyError as error:
            self.session.rollback()
            raise error

    def import_cloud_game(self, cloud_game):
        """
        Imports one cloud-safe game record into the local SQLite library.

        The method deliberately leaves file_name and rom_path empty.
        """
        igdb_id = cloud_game.get("igdb_id")
        title = (cloud_game.get("title") or "Unknown Title").strip()
        platform = cloud_game.get("platform") or "Unknown"

        if igdb_id is not None:
            existing_game = self.get_game_by_igdb_id(igdb_id)
        else:
            existing_game = self.get_game_by_title_and_platform(
                title,
                platform
            )

        if existing_game:
            return existing_game, False

        try:
            game = Game(
                igdb_id=igdb_id,
                title=title,
                summary=cloud_game.get("summary"),
                storyline=cloud_game.get("storyline"),
                cover_url=cloud_game.get("cover_url"),
                release_year=cloud_game.get("release_year"),
                platform=platform,
                status=cloud_game.get("status") or "Saved",
                file_name=None,
                rom_path=None
            )

            self.session.add(game)
            self.session.commit()
            self.session.refresh(game)

            return game, True

        except SQLAlchemyError as error:
            self.session.rollback()
            raise error

    def import_cloud_games(self, cloud_games):
        """
        Imports multiple cloud game records and skips local duplicates.
        """
        imported_count = 0
        skipped_count = 0

        for cloud_game in cloud_games:
            _, was_imported = self.import_cloud_game(cloud_game)

            if was_imported:
                imported_count += 1
            else:
                skipped_count += 1

        return {
            "imported_count": imported_count,
            "skipped_count": skipped_count
        }

    def get_game_by_id(self, game_id):
        return (
            self.session
            .query(Game)
            .filter(Game.id == game_id)
            .first()
        )

    def get_game_by_igdb_id(self, igdb_id):
        return (
            self.session
            .query(Game)
            .filter(Game.igdb_id == igdb_id)
            .first()
        )

    def get_game_by_rom_path(self, rom_path):
        return (
            self.session
            .query(Game)
            .filter(Game.rom_path == rom_path)
            .first()
        )

    def get_game_by_title_and_platform(self, title, platform):
        """
        Finds a local game using a case-insensitive title and platform match.
        """
        return (
            self.session
            .query(Game)
            .filter(
                Game.title.ilike(title),
                Game.platform.ilike(platform)
            )
            .first()
        )

    def get_all_games(self):
        return (
            self.session
            .query(Game)
            .order_by(Game.title)
            .all()
        )

    def delete_game(self, game_id):
        try:
            game = self.get_game_by_id(game_id)

            if game:
                self.session.delete(game)
                self.session.commit()

            return game

        except SQLAlchemyError as error:
            self.session.rollback()
            raise error

    def close(self):
        self.session.close()

    def _extract_cover_url(self, game_data):
        cover = game_data.get("cover")

        if not cover:
            return None

        image_id = cover.get("image_id")

        if not image_id:
            return None

        return (
            "https://images.igdb.com/igdb/image/upload/"
            f"t_cover_big_2x/{image_id}.jpg"
        )

    def _extract_release_year(self, game_data):
        release_dates = game_data.get("release_dates")

        if not release_dates:
            return None

        first_date = release_dates[0]
        return first_date.get("human")

    def _extract_platform_name(self, game_data):
        platforms = game_data.get("platforms")

        if not platforms:
            return None

        first_platform = platforms[0]
        return first_platform.get("name")
