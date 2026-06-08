import os
import requests
from dotenv import load_dotenv


ROOT = os.path.dirname(os.path.dirname(__file__))
ENV_PATH = os.path.join(ROOT, ".env")

load_dotenv(ENV_PATH)


class IGDBService:
    NINTENDO_DS_ID = 20
    NINTENDO_3DS_ID = 37
    NINTENDO_DSI_ID = 159

    DS_FAMILY_PLATFORM_IDS = [
        NINTENDO_DS_ID,
        NINTENDO_3DS_ID,
        NINTENDO_DSI_ID
    ]

    def __init__(self):
        self.client_id = os.getenv("IGDB_CLIENT_ID")
        self.client_secret = os.getenv("IGDB_CLIENT_SECRET")
        self.access_token = None

    def credentials_are_ready(self):
        return bool(self.client_id and self.client_secret)

    def get_access_token(self):
        if not self.credentials_are_ready():
            raise ValueError(
                "Missing IGDB_CLIENT_ID or IGDB_CLIENT_SECRET in your .env file."
            )

        url = "https://id.twitch.tv/oauth2/token"

        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }

        response = requests.post(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        self.access_token = data["access_token"]

        return self.access_token

    def _headers(self):
        if not self.access_token:
            self.get_access_token()

        return {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }

    def search_platforms(self, search_term):
        url = "https://api.igdb.com/v4/platforms"

        query = f'''
            search "{search_term}";
            fields id,name,abbreviation,slug;
            limit 10;
        '''

        response = requests.post(
            url,
            headers=self._headers(),
            data=query,
            timeout=10
        )

        response.raise_for_status()
        return response.json()

    def search_ds_family_games_page(self, search_term, limit=50, offset=0):
        """
        Searches IGDB by title, then filters results to Nintendo DS / DSi / 3DS.
        This is paged using limit and offset.
        """

        games = self._search_games_page(search_term, limit, offset)
        return self._filter_ds_family_games(games)

    def _search_games_page(self, search_term, limit, offset):
        url = "https://api.igdb.com/v4/games"

        safe_search_term = search_term.replace('"', '\\"')

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

        response = requests.post(
            url,
            headers=self._headers(),
            data=query,
            timeout=10
        )

        response.raise_for_status()
        return response.json()

    def get_ds_family_games_page(self, limit=50, offset=0):
        """
        Browses Nintendo DS / DSi / 3DS games using IGDB pagination.
        """

        url = "https://api.igdb.com/v4/games"

        platform_filter = ", ".join(
            str(platform_id) for platform_id in self.DS_FAMILY_PLATFORM_IDS
        )

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

        response = requests.post(
            url,
            headers=self._headers(),
            data=query,
            timeout=10
        )

        response.raise_for_status()
        return response.json()

    def search_ds_games_page(self, search_term, limit=50, offset=0):
        games = self.search_ds_family_games_page(search_term, limit, offset)
        return self._filter_games_by_platform_id(games, self.NINTENDO_DS_ID)

    def search_dsi_games_page(self, search_term, limit=50, offset=0):
        games = self.search_ds_family_games_page(search_term, limit, offset)
        return self._filter_games_by_platform_id(games, self.NINTENDO_DSI_ID)

    def search_3ds_games_page(self, search_term, limit=50, offset=0):
        games = self.search_ds_family_games_page(search_term, limit, offset)
        return self._filter_games_by_platform_id(games, self.NINTENDO_3DS_ID)

    def _filter_ds_family_games(self, games):
        filtered_games = []

        for game in games:
            platforms = game.get("platforms", [])

            for platform in platforms:
                platform_id = platform.get("id")

                if platform_id in self.DS_FAMILY_PLATFORM_IDS:
                    filtered_games.append(game)
                    break

        return filtered_games

    def _filter_games_by_platform_id(self, games, target_platform_id):
        filtered_games = []

        for game in games:
            platforms = game.get("platforms", [])

            for platform in platforms:
                platform_id = platform.get("id")

                if platform_id == target_platform_id:
                    filtered_games.append(game)
                    break

        return filtered_games