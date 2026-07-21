"""Desktop client for RomDex's authenticated Firebase IGDB proxy."""

import requests
from dotenv import load_dotenv

from services.cloud.firebase_auth_service import (
    FirebaseAuthError,
    FirebaseAuthService,
)
from services.cloud.firebase_public_config import get_igdb_proxy_url


class IGDBServiceError(Exception):
    """Raised when the RomDex IGDB proxy cannot complete a request."""


class IGDBService:
    """Fetches IGDB data without placing IGDB credentials in the app."""

    NINTENDO_DS_ID = 20
    NINTENDO_3DS_ID = 37
    NINTENDO_DSI_ID = 159

    DS_FAMILY_PLATFORM_IDS = [
        NINTENDO_DS_ID,
        NINTENDO_3DS_ID,
        NINTENDO_DSI_ID,
    ]

    def __init__(
        self,
        auth_service=None,
        proxy_url=None,
        http_session=None,
    ):
        load_dotenv()

        self.proxy_url = (
            proxy_url.rstrip("/")
            if proxy_url
            else get_igdb_proxy_url()
        )
        self.http_session = http_session or requests.Session()

        try:
            self.auth_service = (
                auth_service
                if auth_service is not None
                else FirebaseAuthService()
            )
        except FirebaseAuthError as error:
            raise IGDBServiceError(str(error)) from error

    def credentials_are_ready(self):
        """Returns whether the public proxy endpoint is configured."""
        return bool(self.proxy_url)

    def search_platforms(self, search_term):
        data = self._request_proxy(
            "search_platforms",
            search_term=search_term,
        )
        return self._read_result_list(data, "platforms")

    def search_ds_family_games_page(self, search_term, limit=50, offset=0):
        data = self._request_proxy(
            "search_games",
            search_term=search_term,
            limit=limit,
            offset=offset,
        )
        return self._read_result_list(data, "games")

    def _search_games_page(self, search_term, limit, offset):
        return self.search_ds_family_games_page(
            search_term,
            limit=limit,
            offset=offset,
        )

    def get_ds_family_games_page(self, limit=50, offset=0):
        data = self._request_proxy(
            "browse_games",
            limit=limit,
            offset=offset,
        )
        return self._read_result_list(data, "games")

    def search_ds_games_page(self, search_term, limit=50, offset=0):
        games = self.search_ds_family_games_page(search_term, limit, offset)
        return self._filter_games_by_platform_id(games, self.NINTENDO_DS_ID)

    def search_dsi_games_page(self, search_term, limit=50, offset=0):
        games = self.search_ds_family_games_page(search_term, limit, offset)
        return self._filter_games_by_platform_id(games, self.NINTENDO_DSI_ID)

    def search_3ds_games_page(self, search_term, limit=50, offset=0):
        games = self.search_ds_family_games_page(search_term, limit, offset)
        return self._filter_games_by_platform_id(games, self.NINTENDO_3DS_ID)

    def _request_proxy(self, action, **payload):
        request_payload = {"action": action, **payload}

        try:
            headers = self.auth_service.get_auth_headers()
            response = self.http_session.post(
                self.proxy_url,
                headers=headers,
                json=request_payload,
                timeout=20,
            )

            if response.status_code == 401:
                self.auth_service.refresh_id_token()
                response = self.http_session.post(
                    self.proxy_url,
                    headers=self.auth_service.get_auth_headers(),
                    json=request_payload,
                    timeout=20,
                )
        except FirebaseAuthError as error:
            raise IGDBServiceError(str(error)) from error
        except requests.RequestException as error:
            raise IGDBServiceError(
                "RomDex could not connect to its IGDB service."
            ) from error

        try:
            data = response.json()
        except ValueError as error:
            raise IGDBServiceError(
                "The RomDex IGDB service returned invalid data."
            ) from error

        if not response.ok:
            message = self._read_error_message(data)
            raise IGDBServiceError(message)

        if not isinstance(data, dict):
            raise IGDBServiceError(
                "The RomDex IGDB service returned an unexpected response."
            )

        return data

    @staticmethod
    def _read_result_list(data, key):
        results = data.get(key)
        if not isinstance(results, list):
            raise IGDBServiceError(
                "The RomDex IGDB service returned an unexpected response."
            )
        return results

    @staticmethod
    def _read_error_message(data):
        if isinstance(data, dict):
            error = data.get("error")
            if isinstance(error, dict):
                message = error.get("message")
                if isinstance(message, str) and message.strip():
                    return message.strip()

        return "The RomDex IGDB request could not be completed."

    def _filter_ds_family_games(self, games):
        return [
            game
            for game in games
            if any(
                platform.get("id") in self.DS_FAMILY_PLATFORM_IDS
                for platform in game.get("platforms", [])
            )
        ]

    @staticmethod
    def _filter_games_by_platform_id(games, target_platform_id):
        return [
            game
            for game in games
            if any(
                platform.get("id") == target_platform_id
                for platform in game.get("platforms", [])
            )
        ]
