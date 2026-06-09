import os
import requests
from dotenv import load_dotenv


# Gets the root folder of the project.
# This is used so the program can find the .env file even if this file is inside /services.
ROOT = os.path.dirname(os.path.dirname(__file__))

# Builds the full path to the .env file.
ENV_PATH = os.path.join(ROOT, ".env")

# Loads environment variables from the .env file.
# This keeps sensitive API credentials out of the source code.
load_dotenv(ENV_PATH)


# Service class responsible for communicating with the IGDB API.
# This separates API logic from the UI, which makes the code easier to maintain.
class IGDBService:
    # IGDB platform IDs for Nintendo DS family systems.
    # These constants make the code easier to understand instead of using magic numbers.
    NINTENDO_DS_ID = 20
    NINTENDO_3DS_ID = 37
    NINTENDO_DSI_ID = 159

    # Stores all supported Nintendo DS family platform IDs in one list.
    # This allows the service to search/filter DS, DSi, and 3DS games together.
    DS_FAMILY_PLATFORM_IDS = [
        NINTENDO_DS_ID,
        NINTENDO_3DS_ID,
        NINTENDO_DSI_ID
    ]

    def __init__(self):
        # Loads IGDB/Twitch API credentials from environment variables.
        self.client_id = os.getenv("IGDB_CLIENT_ID")
        self.client_secret = os.getenv("IGDB_CLIENT_SECRET")

        # Access token starts as None and is requested only when needed.
        self.access_token = None

    def credentials_are_ready(self):
        # Returns True only if both required API credentials exist.
        return bool(self.client_id and self.client_secret)

    def get_access_token(self):
        # Prevents API requests if the .env file is missing required credentials.
        if not self.credentials_are_ready():
            raise ValueError(
                "Missing IGDB_CLIENT_ID or IGDB_CLIENT_SECRET in your .env file."
            )

        # Twitch OAuth endpoint used to get an IGDB access token.
        url = "https://id.twitch.tv/oauth2/token"

        # Required OAuth parameters for client credentials authentication.
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }

        # Sends a POST request to get an access token.
        response = requests.post(url, params=params, timeout=10)

        # Raises an error if the request failed.
        response.raise_for_status()

        # Converts the response JSON into a Python dictionary.
        data = response.json()

        # Stores the access token so it can be reused by later API calls.
        self.access_token = data["access_token"]

        return self.access_token

    def _headers(self):
        # Gets an access token if one has not already been loaded.
        if not self.access_token:
            self.get_access_token()

        # Headers required by IGDB for authenticated API requests.
        return {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }

    def search_platforms(self, search_term):
        # IGDB endpoint for searching platform information.
        url = "https://api.igdb.com/v4/platforms"

        # IGDB API query language.
        # This searches for platforms matching the user's search term.
        query = f'''
            search "{search_term}";
            fields id,name,abbreviation,slug;
            limit 10;
        '''

        # Sends the platform search request to IGDB.
        response = requests.post(
            url,
            headers=self._headers(),
            data=query,
            timeout=10
        )

        response.raise_for_status()

        # Returns the platform results as a list of dictionaries.
        return response.json()

    def search_ds_family_games_page(self, search_term, limit=50, offset=0):
        """
        Searches IGDB by title, then filters results to Nintendo DS / DSi / 3DS.
        This is paged using limit and offset.
        """

        # First, get games from IGDB using the search term.
        games = self._search_games_page(search_term, limit, offset)

        # Then, only keep games that belong to the DS family platforms.
        return self._filter_ds_family_games(games)

    def _search_games_page(self, search_term, limit, offset):
        # IGDB endpoint for game data.
        url = "https://api.igdb.com/v4/games"

        # Escapes quotation marks so the IGDB query does not break.
        safe_search_term = search_term.replace('"', '\\"')

        # Searches games by title and requests only the fields needed by the app.
        query = f'''
            search "{safe_search_term}";
            fields id,name,summary,storyline,
                   release_dates.human,
                   genres.name,
                   platforms.id,
                   platforms.name,
                   cover.image_id;
            limit {limit};
            offset {offset};
        '''

        # Sends the game search request.
        response = requests.post(
            url,
            headers=self._headers(),
            data=query,
            timeout=10
        )

        response.raise_for_status()

        # Returns the game results as JSON data.
        return response.json()

    def get_ds_family_games_page(self, limit=50, offset=0):
        """
        Browses Nintendo DS / DSi / 3DS games using IGDB pagination.
        """

        # IGDB endpoint for game data.
        url = "https://api.igdb.com/v4/games"

        # Converts the DS family platform IDs into a comma-separated string.
        # Example: "20, 37, 159"
        platform_filter = ", ".join(
            str(platform_id) for platform_id in self.DS_FAMILY_PLATFORM_IDS
        )

        # Requests games where the platform matches Nintendo DS, DSi, or 3DS.
        query = f'''
            fields id,name,summary,storyline,
                   release_dates.human,
                   genres.name,
                   platforms.id,
                   platforms.name,
                   cover.image_id;
            where platforms = ({platform_filter});
            sort name asc;
            limit {limit};
            offset {offset};
        '''

        # Sends the browse request to IGDB.
        response = requests.post(
            url,
            headers=self._headers(),
            data=query,
            timeout=10
        )

        response.raise_for_status()

        # Returns the current page of DS family game results.
        return response.json()

    def search_ds_games_page(self, search_term, limit=50, offset=0):
        # Searches DS family games first, then filters only Nintendo DS games.
        games = self.search_ds_family_games_page(search_term, limit, offset)
        return self._filter_games_by_platform_id(games, self.NINTENDO_DS_ID)

    def search_dsi_games_page(self, search_term, limit=50, offset=0):
        # Searches DS family games first, then filters only Nintendo DSi games.
        games = self.search_ds_family_games_page(search_term, limit, offset)
        return self._filter_games_by_platform_id(games, self.NINTENDO_DSI_ID)

    def search_3ds_games_page(self, search_term, limit=50, offset=0):
        # Searches DS family games first, then filters only Nintendo 3DS games.
        games = self.search_ds_family_games_page(search_term, limit, offset)
        return self._filter_games_by_platform_id(games, self.NINTENDO_3DS_ID)

    def _filter_ds_family_games(self, games):
        # Stores games that match DS, DSi, or 3DS platforms.
        filtered_games = []

        for game in games:
            # Gets the list of platforms for the current game.
            platforms = game.get("platforms", [])

            for platform in platforms:
                platform_id = platform.get("id")

                # If any platform matches the DS family, keep the game.
                if platform_id in self.DS_FAMILY_PLATFORM_IDS:
                    filtered_games.append(game)

                    # Stop checking platforms after a match is found.
                    break

        return filtered_games

    def _filter_games_by_platform_id(self, games, target_platform_id):
        # Stores games that match one specific platform ID.
        filtered_games = []

        for game in games:
            platforms = game.get("platforms", [])

            for platform in platforms:
                platform_id = platform.get("id")

                # Keeps the game only if it matches the requested platform.
                if platform_id == target_platform_id:
                    filtered_games.append(game)

                    # Stop checking once the matching platform is found.
                    break

        return filtered_games