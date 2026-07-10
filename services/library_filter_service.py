class LibraryFilterService:
    """
    Handles searching, filtering, and sorting for library games.

    This service receives Game objects from the repository and does not
    directly access the database or Tkinter interface.
    """

    def get_game_type(self, game):
        """
        Returns the display type for a saved game.
        """
        has_local_rom = bool(game.rom_path)
        has_igdb_metadata = bool(game.igdb_id)

        if has_local_rom and has_igdb_metadata:
            return "Local + IGDB"

        if has_local_rom:
            return "Local ROM"

        if has_igdb_metadata:
            return "IGDB"

        return "Manual"

    def filter_games(
        self,
        games,
        search_text="",
        platform="All Platforms",
        game_type="All Types",
        status="All Statuses",
        sort_option="Title A-Z"
    ):
        """
        Filters games by title, platform, type, and status, then sorts
        the matching results.
        """
        normalized_search = search_text.strip().lower()
        filtered_games = []

        for game in games:
            display_platform = game.platform or "Unknown"
            display_status = game.status or "Saved"
            display_type = self.get_game_type(game)
            display_title = game.title or ""

            title_matches = (
                not normalized_search
                or normalized_search in display_title.lower()
            )

            platform_matches = (
                platform == "All Platforms"
                or display_platform == platform
            )

            type_matches = (
                game_type == "All Types"
                or display_type == game_type
            )

            status_matches = (
                status == "All Statuses"
                or display_status == status
            )

            if (
                title_matches
                and platform_matches
                and type_matches
                and status_matches
            ):
                filtered_games.append(game)

        if sort_option == "Title A-Z":
            filtered_games.sort(
                key=lambda game: (game.title or "").lower()
            )

        elif sort_option == "Title Z-A":
            filtered_games.sort(
                key=lambda game: (game.title or "").lower(),
                reverse=True
            )

        elif sort_option == "Newest Added":
            filtered_games.sort(
                key=lambda game: game.id or 0,
                reverse=True
            )

        elif sort_option == "Oldest Added":
            filtered_games.sort(
                key=lambda game: game.id or 0
            )

        return filtered_games

    def get_platform_options(self, games):
        """
        Returns unique platform names for the platform dropdown.
        """
        platforms = {
            game.platform or "Unknown"
            for game in games
        }

        return ["All Platforms"] + sorted(
            platforms,
            key=str.lower
        )

    def get_status_options(self, games):
        """
        Returns unique status names for the status dropdown.
        """
        statuses = {
            game.status or "Saved"
            for game in games
        }

        return ["All Statuses"] + sorted(
            statuses,
            key=str.lower
        )
