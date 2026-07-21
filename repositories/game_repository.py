from pathlib import Path
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError

from services.db import SessionLocal
from models.game import Game


class GameRepository:
    """
    Handles SQLite operations for RomDex Game objects.
    """

    SUPPORTED_ROM_EXTENSIONS = {
        "Nintendo DS": {".nds"},
        "Nintendo DSi": {".nds"},
        "Nintendo 3DS": {".3ds", ".cci", ".cxi"}
    }

    IMPORT_MODE_ADDITIVE = "additive"
    IMPORT_MODE_OVERWRITE = "overwrite"
    IMPORT_MODES = {
        IMPORT_MODE_ADDITIVE,
        IMPORT_MODE_OVERWRITE
    }

    def __init__(self):
        self.session = SessionLocal()

    def add_game(self, game_data):
        """
        Saves one IGDB result to the local library.
        """
        try:
            igdb_id = game_data.get("id")

            if igdb_id is None:
                raise ValueError("Game data is missing IGDB ID.")

            existing_game = self.get_game_by_igdb_id(igdb_id)

            if existing_game:
                return existing_game

            game = Game(
                cloud_id=f"igdb_{igdb_id}",
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

        except SQLAlchemyError:
            self.session.rollback()
            raise

    def add_local_rom(self, rom_path):
        """
        Adds a local Nintendo DS ROM as a new library entry.
        """
        path = self._validate_rom_path(
            rom_path=rom_path,
            platform="Nintendo DS"
        )

        existing_game = self.get_game_by_rom_path(str(path))

        if existing_game:
            return existing_game

        try:
            game = Game(
                cloud_id=f"local_{uuid4().hex}",
                title=path.stem,
                platform="Nintendo DS",
                file_name=path.name,
                rom_path=str(path),
                status="Owned"
            )

            self.session.add(game)
            self.session.commit()
            self.session.refresh(game)

            return game

        except SQLAlchemyError:
            self.session.rollback()
            raise

    def attach_rom_to_game(self, game_id, rom_path):
        """
        Attaches or replaces the ROM file on an existing game.
        """
        game = self.get_game_by_id(game_id)

        if not game:
            raise ValueError(
                f"No game exists with database ID {game_id}."
            )

        path = self._validate_rom_path(
            rom_path=rom_path,
            platform=game.platform
        )

        existing_game = self.get_game_by_rom_path(str(path))

        if existing_game and existing_game.id != game.id:
            raise ValueError(
                "That ROM file is already attached to another library game."
            )

        try:
            game.file_name = path.name
            game.rom_path = str(path)

            if not game.status or game.status == "Saved":
                game.status = "Owned"

            self.session.commit()
            self.session.refresh(game)

            return game

        except SQLAlchemyError:
            self.session.rollback()
            raise

    def replace_rom_on_game(self, game_id, rom_path):
        """
        Replaces a game's current ROM attachment.
        """
        return self.attach_rom_to_game(
            game_id=game_id,
            rom_path=rom_path
        )

    def detach_rom_from_game(self, game_id):
        """
        Removes a ROM attachment while keeping the library entry.
        """
        game = self.get_game_by_id(game_id)

        if not game:
            raise ValueError(
                f"No game exists with database ID {game_id}."
            )

        previous_attachment = {
            "file_name": game.file_name,
            "rom_path": game.rom_path
        }

        try:
            game.file_name = None
            game.rom_path = None

            if game.igdb_id and game.status == "Owned":
                game.status = "Saved"

            self.session.commit()
            self.session.refresh(game)

            return {
                "game": game,
                "previous_attachment": previous_attachment
            }

        except SQLAlchemyError:
            self.session.rollback()
            raise

    def get_rom_merge_candidates(self, target_game_id=None):
        """
        Returns local-only games that have a ROM and can be merged into
        an IGDB library entry.
        """
        query = (
            self.session
            .query(Game)
            .filter(
                Game.igdb_id.is_(None),
                Game.rom_path.isnot(None)
            )
        )

        if target_game_id is not None:
            query = query.filter(Game.id != target_game_id)

        return query.order_by(Game.title).all()

    def merge_local_rom_into_game(
        self,
        target_game_id,
        source_game_id
    ):
        """
        Merges a local-only ROM entry into an IGDB metadata entry.

        The target keeps its IGDB metadata. The source contributes only
        file_name and rom_path, then the source row is deleted.
        """
        if target_game_id == source_game_id:
            raise ValueError(
                "The target and source must be different games."
            )

        target_game = self.get_game_by_id(target_game_id)
        source_game = self.get_game_by_id(source_game_id)

        if not target_game:
            raise ValueError(
                f"No target game exists with ID {target_game_id}."
            )

        if not source_game:
            raise ValueError(
                f"No source game exists with ID {source_game_id}."
            )

        if target_game.igdb_id is None:
            raise ValueError(
                "The target must be an IGDB metadata entry."
            )

        if target_game.rom_path:
            raise ValueError(
                "The target already has a ROM attached. "
                "Detach it before merging another entry."
            )

        if source_game.igdb_id is not None:
            raise ValueError(
                "The source must be a personal/local ROM entry."
            )

        if not source_game.rom_path:
            raise ValueError(
                "The source game does not have a ROM attached."
            )

        validated_path = self._validate_rom_path(
            rom_path=source_game.rom_path,
            platform=target_game.platform
        )

        source_snapshot = {
            "id": source_game.id,
            "title": source_game.title,
            "file_name": source_game.file_name,
            "rom_path": source_game.rom_path
        }

        try:
            # Release the source row's unique rom_path before assigning
            # that same path to the IGDB target.
            source_game.file_name = None
            source_game.rom_path = None
            self.session.flush()

            target_game.file_name = validated_path.name
            target_game.rom_path = str(validated_path)
            target_game.status = "Owned"

            self.session.delete(source_game)
            self.session.commit()
            self.session.refresh(target_game)

            return {
                "game": target_game,
                "removed_source": source_snapshot
            }

        except SQLAlchemyError:
            self.session.rollback()
            raise

    def import_cloud_game(
        self,
        cloud_game,
        mode=IMPORT_MODE_ADDITIVE
    ):
        """
        Imports or updates one cloud-safe game record.

        Additive mode leaves matching local metadata unchanged. Overwrite
        mode refreshes matching metadata while preserving local ROM paths.
        """
        if mode not in self.IMPORT_MODES:
            raise ValueError(f"Unknown cloud import mode: {mode}")

        igdb_id = cloud_game.get("igdb_id")
        title = (cloud_game.get("title") or "Unknown Title").strip()
        platform = cloud_game.get("platform") or "Unknown"
        cloud_id = self._get_imported_cloud_id(
            cloud_game=cloud_game,
            igdb_id=igdb_id
        )

        existing_game = None

        if cloud_id:
            existing_game = self.get_game_by_cloud_id(cloud_id)

        if existing_game is None and igdb_id is not None:
            existing_game = self.get_game_by_igdb_id(igdb_id)

        if existing_game is None and igdb_id is None:
            existing_game = self.get_game_by_title_and_platform(
                title,
                platform
            )

        if existing_game:
            try:
                if cloud_id and existing_game.cloud_id != cloud_id:
                    existing_game.cloud_id = cloud_id

                if mode == self.IMPORT_MODE_OVERWRITE:
                    self._apply_cloud_metadata(
                        game=existing_game,
                        cloud_game=cloud_game,
                        title=title,
                        platform=platform
                    )
                    action = "updated"
                else:
                    action = "skipped"

                self.session.commit()
                self.session.refresh(existing_game)
                return existing_game, action

            except SQLAlchemyError:
                self.session.rollback()
                raise

        try:
            game = Game(
                cloud_id=cloud_id or f"local_{uuid4().hex}",
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

            return game, "imported"

        except SQLAlchemyError:
            self.session.rollback()
            raise

    def import_cloud_games(
        self,
        cloud_games,
        mode=IMPORT_MODE_ADDITIVE
    ):
        """
        Imports cloud records without creating duplicate local games.

        Duplicate records inside the incoming cloud library are processed
        once. Overwrite mode updates matching rows in place, so attached ROM
        paths and local file names remain device-specific and untouched.
        """
        if mode not in self.IMPORT_MODES:
            raise ValueError(f"Unknown cloud import mode: {mode}")

        imported_count = 0
        updated_count = 0
        skipped_count = 0
        seen_identities = set()

        for cloud_game in cloud_games:
            identity = self._get_cloud_import_identity(cloud_game)

            if identity in seen_identities:
                skipped_count += 1
                continue

            seen_identities.add(identity)

            _, action = self.import_cloud_game(
                cloud_game,
                mode=mode
            )

            if action == "imported":
                imported_count += 1
            elif action == "updated":
                updated_count += 1
            else:
                skipped_count += 1

        return {
            "imported_count": imported_count,
            "updated_count": updated_count,
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

    def get_game_by_cloud_id(self, cloud_id):
        return (
            self.session
            .query(Game)
            .filter(Game.cloud_id == cloud_id)
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

        except SQLAlchemyError:
            self.session.rollback()
            raise

    def close(self):
        self.session.close()

    @staticmethod
    def _get_imported_cloud_id(cloud_game, igdb_id=None):
        if igdb_id is not None:
            return f"igdb_{igdb_id}"

        cloud_id = (
            cloud_game.get("cloud_id")
            or cloud_game.get("_cloud_game_id")
            or ""
        )

        return str(cloud_id).strip() or None

    def _get_cloud_import_identity(self, cloud_game):
        igdb_id = cloud_game.get("igdb_id")
        cloud_id = self._get_imported_cloud_id(
            cloud_game=cloud_game,
            igdb_id=igdb_id
        )

        if cloud_id:
            return ("cloud", cloud_id.casefold())

        title = (cloud_game.get("title") or "Unknown Title").strip()
        platform = (cloud_game.get("platform") or "Unknown").strip()
        return ("metadata", title.casefold(), platform.casefold())

    @staticmethod
    def _apply_cloud_metadata(game, cloud_game, title, platform):
        game.title = title
        game.summary = cloud_game.get("summary")
        game.storyline = cloud_game.get("storyline")
        game.cover_url = cloud_game.get("cover_url")
        game.release_year = cloud_game.get("release_year")
        game.platform = platform

        # A local ROM attachment always keeps the stronger Owned status.
        if game.rom_path:
            game.status = "Owned"
        else:
            game.status = cloud_game.get("status") or "Saved"

    def _validate_rom_path(self, rom_path, platform):
        """
        Confirms that a ROM exists and matches the target platform.
        """
        if not rom_path:
            raise ValueError("A ROM file path is required.")

        path = Path(rom_path).expanduser().resolve()

        if not path.exists():
            raise ValueError(
                "The selected ROM file does not exist."
            )

        if not path.is_file():
            raise ValueError(
                "The selected ROM path must point to a file."
            )

        allowed_extensions = self._get_allowed_extensions(platform)

        if path.suffix.lower() not in allowed_extensions:
            extensions_text = ", ".join(
                sorted(allowed_extensions)
            )

            raise ValueError(
                f'The platform "{platform or "Unknown"}" accepts: '
                f"{extensions_text}"
            )

        return path

    def _get_allowed_extensions(self, platform):
        normalized_platform = (platform or "").strip()

        if normalized_platform in self.SUPPORTED_ROM_EXTENSIONS:
            return self.SUPPORTED_ROM_EXTENSIONS[normalized_platform]

        return set().union(
            *self.SUPPORTED_ROM_EXTENSIONS.values()
        )

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

        return release_dates[0].get("human")

    def _extract_platform_name(self, game_data):
        platforms = game_data.get("platforms")

        if not platforms:
            return None

        return platforms[0].get("name")
