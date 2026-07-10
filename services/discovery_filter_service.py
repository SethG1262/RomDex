class DiscoveryFilterService:
    """
    Handles filtering, sorting, and metadata extraction for IGDB
    discovery results.

    The service receives dictionaries returned by IGDB and does not
    directly access Tkinter or the database.
    """

    def filter_games(
        self,
        games,
        title="",
        platform="All Platforms",
        release_year="All Years",
        genre="All Genres",
        cover_option="All Games",
        sort_option="Title A-Z"
    ):
        """
        Filters discovery results using the selected criteria and then
        returns the sorted matching games.
        """
        normalized_title = title.strip().lower()
        filtered_games = []

        for game in games:
            game_title = game.get("name", "")
            platform_names = self.get_platform_names(game)
            genre_names = self.get_genre_names(game)
            year = self.get_release_year(game)
            has_cover = self.has_cover(game)

            title_matches = (
                not normalized_title
                or normalized_title in game_title.lower()
            )

            platform_matches = (
                platform == "All Platforms"
                or platform in platform_names
            )

            year_matches = (
                release_year == "All Years"
                or str(year) == release_year
            )

            genre_matches = (
                genre == "All Genres"
                or genre in genre_names
            )

            cover_matches = (
                cover_option == "All Games"
                or (
                    cover_option == "Has Cover"
                    and has_cover
                )
                or (
                    cover_option == "No Cover"
                    and not has_cover
                )
            )

            if (
                title_matches
                and platform_matches
                and year_matches
                and genre_matches
                and cover_matches
            ):
                filtered_games.append(game)

        return self.sort_games(filtered_games, sort_option)

    def sort_games(self, games, sort_option):
        """
        Sorts IGDB discovery results using the selected option.
        """
        sorted_games = list(games)

        if sort_option == "Title A-Z":
            sorted_games.sort(
                key=lambda game: game.get("name", "").lower()
            )

        elif sort_option == "Title Z-A":
            sorted_games.sort(
                key=lambda game: game.get("name", "").lower(),
                reverse=True
            )

        elif sort_option == "Release Year Newest":
            sorted_games.sort(
                key=self.get_release_year,
                reverse=True
            )

        elif sort_option == "Release Year Oldest":
            sorted_games.sort(
                key=lambda game: (
                    self.get_release_year(game)
                    if self.get_release_year(game) > 0
                    else 9999
                )
            )

        return sorted_games

    def get_platform_options(self, games):
        """
        Returns unique platform names for the platform dropdown.
        """
        platforms = set()

        for game in games:
            platforms.update(self.get_platform_names(game))

        return ["All Platforms"] + sorted(
            platforms,
            key=str.lower
        )

    def get_year_options(self, games):
        """
        Returns unique release years for the year dropdown.
        """
        years = {
            str(self.get_release_year(game))
            for game in games
            if self.get_release_year(game) > 0
        }

        return ["All Years"] + sorted(
            years,
            reverse=True
        )

    def get_genre_options(self, games):
        """
        Returns unique genre names for the genre dropdown.
        """
        genres = set()

        for game in games:
            genres.update(self.get_genre_names(game))

        return ["All Genres"] + sorted(
            genres,
            key=str.lower
        )

    def get_platform_names(self, game):
        """
        Returns platform names from an IGDB result dictionary.
        """
        platforms = game.get("platforms") or []
        names = []

        for platform in platforms:
            if isinstance(platform, dict):
                name = platform.get("name")
            else:
                name = str(platform)

            if name:
                names.append(name)

        return names

    def get_platform_text(self, game):
        """
        Returns platform names formatted for display.
        """
        platform_names = self.get_platform_names(game)

        if not platform_names:
            return "Unknown"

        return ", ".join(platform_names)

    def get_genre_names(self, game):
        """
        Returns genre names from an IGDB result dictionary.
        """
        genres = game.get("genres") or []
        names = []

        for genre in genres:
            if isinstance(genre, dict):
                name = genre.get("name")
            else:
                name = str(genre)

            if name:
                names.append(name)

        return names

    def get_genre_text(self, game):
        """
        Returns genre names formatted for display.
        """
        genre_names = self.get_genre_names(game)

        if not genre_names:
            return "Unknown"

        return ", ".join(genre_names)

    def get_release_year(self, game):
        """
        Returns the first available release year as an integer.
        """
        release_dates = game.get("release_dates") or []

        for release_date in release_dates:
            if not isinstance(release_date, dict):
                continue

            year = release_date.get("y")

            if year:
                try:
                    return int(year)
                except (TypeError, ValueError):
                    pass

            human = release_date.get("human", "")

            if human:
                for part in str(human).replace(",", " ").split():
                    if part.isdigit() and len(part) == 4:
                        return int(part)

        first_release_date = game.get("first_release_date")

        if first_release_date:
            try:
                from datetime import datetime
                return datetime.fromtimestamp(first_release_date).year
            except (TypeError, ValueError, OSError):
                pass

        return 0

    def get_release_date_text(self, game):
        """
        Returns a human-readable release date.
        """
        release_dates = game.get("release_dates") or []

        if not release_dates:
            return "Unknown"

        first_release = release_dates[0]

        if isinstance(first_release, dict):
            return first_release.get("human", "Unknown")

        return str(first_release)

    def has_cover(self, game):
        """
        Returns True when the IGDB result contains cover information.
        """
        return bool(
            game.get("cover")
            or game.get("cover_url")
        )
