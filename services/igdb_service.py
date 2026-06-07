import os
import requests
from dotenv import load_dotenv


ROOT = os.path.dirname(os.path.dirname(__file__))
ENV_PATH = os.path.join(ROOT, ".env")

load_dotenv(ENV_PATH)


class IGDBService:
    NINTENDO_3DS_ID = 37

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
        """
        Use this to verify platform IDs like Nintendo DSi.
        """
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

    def search_handheld_games(self, search_term, platform_ids):
        """
        Searches IGDB for games on selected platforms.
        Example platform_ids: [37, DSI_ID]
        """
        url = "https://api.igdb.com/v4/games"

        platform_filter = ", ".join(str(platform_id) for platform_id in platform_ids)

        query = f'''
            search "{search_term}";
            fields id,name,summary,storyline,first_release_date,
                   genres.name,platforms.name,cover.url;
            where platforms = ({platform_filter});
            limit 12;
        '''

        response = requests.post(
            url,
            headers=self._headers(),
            data=query,
            timeout=10
        )

        response.raise_for_status()
        return response.json()

    def search_3ds_games(self, search_term):
        return self.search_handheld_games(
            search_term,
            [self.NINTENDO_3DS_ID]
        )

    def search_3ds_and_dsi_games(self, search_term):
        """
        Replace DSI_ID_HERE after verifying it with search_platforms("Nintendo DSi").
        """
        DSI_ID_HERE = None

        if DSI_ID_HERE is None:
            raise ValueError(
                "Nintendo DSi platform ID is not set yet. "
                "Run search_platforms('Nintendo DSi') first, then update DSI_ID_HERE."
            )

        return self.search_handheld_games(
            search_term,
            [self.NINTENDO_3DS_ID, DSI_ID_HERE]
        )