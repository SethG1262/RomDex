class LibraryExportService:
    """
    Converts local SQLAlchemy Game objects into cloud-safe dictionaries.

    Local ROM paths and file names are deliberately excluded because
    those paths are device-specific and should not be shared.
    """

    def export_game(self, game):
        """
        Converts one local Game object into a Firestore-safe dictionary.
        """
        return {
            "cloud_id": getattr(game, "cloud_id", None),
            "local_source_id": game.id,
            "igdb_id": game.igdb_id,
            "title": game.title or "Unknown Title",
            "summary": game.summary,
            "storyline": game.storyline,
            "cover_url": game.cover_url,
            "release_year": game.release_year,
            "platform": game.platform or "Unknown",
            "status": game.status or "Saved",
            "has_local_rom": bool(game.rom_path)
        }

    def export_games(self, games):
        """
        Converts a collection of Game objects into cloud-safe dictionaries.
        """
        return [
            self.export_game(game)
            for game in games
        ]

    def get_cloud_game_id(self, exported_game):
        """
        Generates a stable Firestore document ID for one exported game.

        IGDB games use their IGDB ID. Local-only games use a persistent
        cloud ID that follows the record across RomDex installations.
        """
        igdb_id = exported_game.get("igdb_id")

        if igdb_id is not None:
            return f"igdb_{igdb_id}"

        cloud_id = (exported_game.get("cloud_id") or "").strip()

        if cloud_id:
            if "/" in cloud_id:
                raise ValueError(
                    "A cloud game ID cannot contain a forward slash."
                )

            return cloud_id

        local_source_id = exported_game.get("local_source_id")

        if local_source_id is None:
            raise ValueError(
                "The exported game is missing both IGDB and local IDs."
            )

        # Compatibility fallback for old or test records. Current database
        # migrations populate cloud_id before synchronization begins.
        return f"local_{local_source_id}"
