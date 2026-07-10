import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv


class FirebaseAuthError(Exception):
    """Raised when Firebase Authentication cannot complete a request."""


class FirebaseAuthService:
    """
    Handles anonymous Firebase Authentication for RomDex.

    The service uses Firebase's REST API, so it is suitable for the
    desktop application and does not require npm or firebase-admin.
    """

    SIGN_IN_URL = (
        "https://identitytoolkit.googleapis.com/v1/"
        "accounts:signUp?key={api_key}"
    )
    REFRESH_URL = (
        "https://securetoken.googleapis.com/v1/"
        "token?key={api_key}"
    )

    def __init__(self, session_file=None):
        load_dotenv()

        self.api_key = os.getenv("FIREBASE_API_KEY", "").strip()

        if not self.api_key:
            raise FirebaseAuthError(
                "FIREBASE_API_KEY is missing. Add it to the project's .env file."
            )

        if session_file is None:
            project_root = Path(__file__).resolve().parents[2]
            session_file = project_root / "data" / "firebase_auth_session.json"

        self.session_file = Path(session_file)
        self.session = self._load_session()

    @property
    def uid(self):
        """Returns the current anonymous Firebase UID, if available."""
        return self.session.get("uid")

    @property
    def id_token(self):
        """Returns the current Firebase ID token, if available."""
        return self.session.get("id_token")

    @property
    def refresh_token(self):
        """Returns the current Firebase refresh token, if available."""
        return self.session.get("refresh_token")

    def sign_in_anonymously(self):
        """
        Creates a new anonymous Firebase user and stores its session.

        If this installation already has a saved session, use
        get_valid_id_token() instead to preserve the same UID.
        """
        url = self.SIGN_IN_URL.format(api_key=self.api_key)

        try:
            response = requests.post(
                url,
                json={"returnSecureToken": True},
                timeout=15
            )
        except requests.RequestException as error:
            raise FirebaseAuthError(
                f"Could not connect to Firebase Authentication: {error}"
            ) from error

        data = self._read_response(response)

        self.session = {
            "uid": data["localId"],
            "id_token": data["idToken"],
            "refresh_token": data["refreshToken"],
            "expires_at": time.time() + int(data.get("expiresIn", 3600))
        }

        self._save_session()
        return self.session.copy()

    def refresh_id_token(self):
        """
        Refreshes an expired Firebase ID token while keeping the same UID.
        """
        if not self.refresh_token:
            return self.sign_in_anonymously()

        url = self.REFRESH_URL.format(api_key=self.api_key)

        try:
            response = requests.post(
                url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token
                },
                timeout=15
            )
        except requests.RequestException as error:
            raise FirebaseAuthError(
                f"Could not refresh the Firebase session: {error}"
            ) from error

        data = self._read_response(response)

        self.session = {
            "uid": data.get("user_id", self.uid),
            "id_token": data["id_token"],
            "refresh_token": data["refresh_token"],
            "expires_at": time.time() + int(data.get("expires_in", 3600))
        }

        self._save_session()
        return self.session.copy()

    def get_valid_id_token(self):
        """
        Returns a usable Firebase ID token.

        The existing anonymous session is reused. A new user is created
        only when this installation has no saved session.
        """
        if not self.session:
            self.sign_in_anonymously()

        # Refresh five minutes before expiration.
        expires_at = float(self.session.get("expires_at", 0))

        if time.time() >= expires_at - 300:
            self.refresh_id_token()

        return self.id_token

    def get_auth_headers(self):
        """
        Returns HTTP headers for authenticated Firebase REST requests.
        """
        return {
            "Authorization": f"Bearer {self.get_valid_id_token()}",
            "Content-Type": "application/json"
        }

    def clear_local_session(self):
        """
        Removes the locally stored session.

        Calling sign_in_anonymously() afterward creates a new Firebase UID.
        """
        self.session = {}

        try:
            self.session_file.unlink(missing_ok=True)
        except OSError as error:
            raise FirebaseAuthError(
                f"Could not remove the local Firebase session: {error}"
            ) from error

    def _load_session(self):
        if not self.session_file.exists():
            return {}

        try:
            with self.session_file.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, dict):
                return {}

            return data

        except (OSError, json.JSONDecodeError):
            return {}

    def _save_session(self):
        try:
            self.session_file.parent.mkdir(parents=True, exist_ok=True)

            with self.session_file.open("w", encoding="utf-8") as file:
                json.dump(self.session, file, indent=2)

        except OSError as error:
            raise FirebaseAuthError(
                f"Could not save the Firebase session: {error}"
            ) from error

    @staticmethod
    def _read_response(response):
        try:
            data = response.json()
        except ValueError as error:
            raise FirebaseAuthError(
                "Firebase returned a response that was not valid JSON."
            ) from error

        if response.ok:
            return data

        firebase_error = data.get("error", {})
        message = firebase_error.get("message", "UNKNOWN_FIREBASE_ERROR")

        friendly_messages = {
            "OPERATION_NOT_ALLOWED": (
                "Anonymous Authentication is disabled. Enable it in "
                "Firebase Authentication > Sign-in method."
            ),
            "API_KEY_INVALID": (
                "The Firebase API key is invalid. Check FIREBASE_API_KEY "
                "in the .env file."
            ),
            "PROJECT_NOT_FOUND": (
                "Firebase could not find the configured project."
            ),
            "TOO_MANY_ATTEMPTS_TRY_LATER": (
                "Firebase temporarily blocked new sign-ins because too "
                "many attempts were made. Try again later."
            )
        }

        raise FirebaseAuthError(
            friendly_messages.get(message, f"Firebase error: {message}")
        )
