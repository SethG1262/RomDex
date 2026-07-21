"""Firebase HTTPS proxy for the IGDB endpoints used by RomDex."""

import json
import logging
import threading
import time
from typing import Any

import requests
from firebase_admin import auth, get_app, initialize_app
from firebase_functions import https_fn
from firebase_functions.params import SecretParam


try:
    get_app()
except ValueError:
    initialize_app()

IGDB_CLIENT_ID = SecretParam("IGDB_CLIENT_ID")
IGDB_CLIENT_SECRET = SecretParam("IGDB_CLIENT_SECRET")

TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
IGDB_API_ROOT = "https://api.igdb.com/v4"
DS_FAMILY_PLATFORM_IDS = (20, 37, 159)

GAME_FIELDS = (
    "id,name,summary,storyline,"
    "release_dates.human,"
    "genres.name,"
    "platforms.id,"
    "platforms.name,"
    "cover.image_id"
)

MAX_PAGE_SIZE = 50
MAX_OFFSET = 10_000
MAX_SEARCH_LENGTH = 120
TOKEN_REFRESH_MARGIN_SECONDS = 300
MIN_IGDB_REQUEST_INTERVAL_SECONDS = 0.26

_access_token: str | None = None
_access_token_expires_at = 0.0
_token_lock = threading.Lock()
_igdb_request_lock = threading.Lock()
_last_igdb_request_at = 0.0


class ProxyError(Exception):
    """A safe error that can be returned to the RomDex client."""

    def __init__(self, message: str, status: int):
        super().__init__(message)
        self.message = message
        self.status = status


def _json_response(payload: dict[str, Any], status: int = 200):
    return https_fn.Response(
        json.dumps(payload),
        status=status,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )


def _verify_firebase_user(request: https_fn.Request) -> str:
    authorization = request.headers.get("Authorization", "")
    scheme, separator, token = authorization.partition(" ")

    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise ProxyError("A Firebase sign-in token is required.", 401)

    try:
        decoded_token = auth.verify_id_token(token.strip())
    except Exception as error:
        logging.warning(
            "Rejected an invalid Firebase ID token (%s).",
            type(error).__name__,
        )
        raise ProxyError(
            "The Firebase sign-in token is invalid or expired.",
            401,
        ) from error

    uid = decoded_token.get("uid")
    if not uid:
        raise ProxyError("The Firebase sign-in token has no user ID.", 401)

    return str(uid)


def _read_request_payload(request: https_fn.Request) -> dict[str, Any]:
    if request.method != "POST":
        raise ProxyError("Only POST requests are supported.", 405)

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ProxyError("The request body must be a JSON object.", 400)

    return payload


def _read_page(payload: dict[str, Any]) -> tuple[int, int]:
    limit = payload.get("limit", MAX_PAGE_SIZE)
    offset = payload.get("offset", 0)

    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ProxyError("limit must be an integer.", 400)
    if isinstance(offset, bool) or not isinstance(offset, int):
        raise ProxyError("offset must be an integer.", 400)
    if not 1 <= limit <= MAX_PAGE_SIZE:
        raise ProxyError(
            f"limit must be between 1 and {MAX_PAGE_SIZE}.",
            400,
        )
    if not 0 <= offset <= MAX_OFFSET:
        raise ProxyError(
            f"offset must be between 0 and {MAX_OFFSET}.",
            400,
        )

    return limit, offset


def _read_search_term(payload: dict[str, Any]) -> str:
    search_term = payload.get("search_term")

    if not isinstance(search_term, str):
        raise ProxyError("search_term must be a string.", 400)

    search_term = " ".join(search_term.split()).strip()

    if not search_term:
        raise ProxyError("search_term cannot be empty.", 400)
    if len(search_term) > MAX_SEARCH_LENGTH:
        raise ProxyError(
            f"search_term cannot exceed {MAX_SEARCH_LENGTH} characters.",
            400,
        )

    return search_term


def _escape_igdb_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _get_access_token(force_refresh: bool = False) -> str:
    global _access_token, _access_token_expires_at

    now = time.time()
    if (
        not force_refresh
        and _access_token
        and now < _access_token_expires_at - TOKEN_REFRESH_MARGIN_SECONDS
    ):
        return _access_token

    with _token_lock:
        now = time.time()
        if (
            not force_refresh
            and _access_token
            and now < _access_token_expires_at - TOKEN_REFRESH_MARGIN_SECONDS
        ):
            return _access_token

        try:
            response = requests.post(
                TWITCH_TOKEN_URL,
                params={
                    "client_id": IGDB_CLIENT_ID.value,
                    "client_secret": IGDB_CLIENT_SECRET.value,
                    "grant_type": "client_credentials",
                },
                timeout=10,
            )
        except requests.RequestException as error:
            raise ProxyError(
                "RomDex could not reach the IGDB authentication service.",
                502,
            ) from error

        if not response.ok:
            logging.error(
                "Twitch token request failed with HTTP %s.",
                response.status_code,
            )
            raise ProxyError(
                "The RomDex IGDB service is not configured correctly.",
                502,
            )

        try:
            data = response.json()
            token = data["access_token"]
            expires_in = int(data.get("expires_in", 3600))
        except (KeyError, TypeError, ValueError) as error:
            raise ProxyError(
                "The IGDB authentication service returned invalid data.",
                502,
            ) from error

        _access_token = str(token)
        _access_token_expires_at = time.time() + max(expires_in, 1)
        return _access_token


def _invalidate_access_token():
    global _access_token, _access_token_expires_at

    with _token_lock:
        _access_token = None
        _access_token_expires_at = 0.0


def _send_igdb_request(endpoint: str, query: str, retry_auth: bool = True):
    global _last_igdb_request_at

    token = _get_access_token()
    headers = {
        "Client-ID": IGDB_CLIENT_ID.value,
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    try:
        # One deployed instance plus this lock keeps RomDex below IGDB's
        # four-request-per-second application limit.
        with _igdb_request_lock:
            wait_seconds = (
                MIN_IGDB_REQUEST_INTERVAL_SECONDS
                - (time.monotonic() - _last_igdb_request_at)
            )
            if wait_seconds > 0:
                time.sleep(wait_seconds)

            response = requests.post(
                f"{IGDB_API_ROOT}/{endpoint}",
                headers=headers,
                data=query,
                timeout=15,
            )
            _last_igdb_request_at = time.monotonic()
    except requests.RequestException as error:
        raise ProxyError("RomDex could not reach IGDB.", 502) from error

    if response.status_code == 401 and retry_auth:
        _invalidate_access_token()
        _get_access_token(force_refresh=True)
        return _send_igdb_request(endpoint, query, retry_auth=False)

    if response.status_code == 429:
        raise ProxyError("IGDB is busy. Please try again shortly.", 503)

    if not response.ok:
        logging.error(
            "IGDB %s request failed with HTTP %s.",
            endpoint,
            response.status_code,
        )
        raise ProxyError("IGDB could not complete the request.", 502)

    try:
        data = response.json()
    except ValueError as error:
        raise ProxyError("IGDB returned invalid data.", 502) from error

    if not isinstance(data, list):
        raise ProxyError("IGDB returned an unexpected response.", 502)

    return data


def _search_games(payload: dict[str, Any]):
    search_term = _escape_igdb_string(_read_search_term(payload))
    limit, offset = _read_page(payload)
    platforms = ", ".join(map(str, DS_FAMILY_PLATFORM_IDS))

    query = (
        f'search "{search_term}";\n'
        f"fields {GAME_FIELDS};\n"
        f"where platforms = ({platforms});\n"
        f"limit {limit};\n"
        f"offset {offset};"
    )
    return {"games": _send_igdb_request("games", query)}


def _browse_games(payload: dict[str, Any]):
    limit, offset = _read_page(payload)
    platforms = ", ".join(map(str, DS_FAMILY_PLATFORM_IDS))

    query = (
        f"fields {GAME_FIELDS};\n"
        f"where platforms = ({platforms});\n"
        "sort name asc;\n"
        f"limit {limit};\n"
        f"offset {offset};"
    )
    return {"games": _send_igdb_request("games", query)}


def _search_platforms(payload: dict[str, Any]):
    search_term = _escape_igdb_string(_read_search_term(payload))
    query = (
        f'search "{search_term}";\n'
        "fields id,name,abbreviation,slug;\n"
        "limit 10;"
    )
    return {"platforms": _send_igdb_request("platforms", query)}


ACTIONS = {
    "search_games": _search_games,
    "browse_games": _browse_games,
    "search_platforms": _search_platforms,
}


@https_fn.on_request(
    region="us-central1",
    secrets=[IGDB_CLIENT_ID, IGDB_CLIENT_SECRET],
    max_instances=1,
    concurrency=20,
    timeout_sec=30,
)
def igdb_proxy(request: https_fn.Request) -> https_fn.Response:
    """Runs one validated IGDB operation for an authenticated RomDex user."""

    try:
        _verify_firebase_user(request)
        payload = _read_request_payload(request)
        action = payload.get("action")

        if not isinstance(action, str):
            raise ProxyError("action must be a string.", 400)

        handler = ACTIONS.get(action)
        if handler is None:
            raise ProxyError("The requested IGDB action is not supported.", 400)

        return _json_response(handler(payload))
    except ProxyError as error:
        return _json_response(
            {"error": {"message": error.message}},
            status=error.status,
        )
    except Exception:
        logging.exception("Unexpected IGDB proxy failure.")
        return _json_response(
            {"error": {"message": "The RomDex IGDB service failed."}},
            status=500,
        )
