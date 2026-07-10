import os
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

from services.cloud.firebase_auth_service import (
    FirebaseAuthError,
    FirebaseAuthService
)
from services.cloud.library_export_service import LibraryExportService
from services.cloud.cloud_config_service import (
    CloudConfigError,
    CloudConfigService
)
from services.cloud.library_key_service import LibraryKeyService


class CloudLibraryError(Exception):
    """Raised when a Firestore cloud-library request fails."""


class CloudLibraryService:
    """
    Creates, retrieves, and uploads RomDex libraries using Firestore REST.

    FirebaseAuthService supplies the anonymous user's ID token. Firestore
    Security Rules remain responsible for access control.
    """

    FIRESTORE_ROOT = (
        "https://firestore.googleapis.com/v1/"
        "projects/{project_id}/databases/(default)/documents"
    )

    def __init__(
        self,
        auth_service=None,
        export_service=None,
        key_service=None,
        config_service=None
    ):
        load_dotenv()

        self.project_id = os.getenv(
            "FIREBASE_PROJECT_ID",
            ""
        ).strip()

        if not self.project_id:
            raise CloudLibraryError(
                "FIREBASE_PROJECT_ID is missing. "
                "Add it to the project's .env file."
            )

        try:
            self.auth_service = (
                auth_service
                if auth_service is not None
                else FirebaseAuthService()
            )
        except FirebaseAuthError as error:
            raise CloudLibraryError(str(error)) from error

        self.export_service = (
            export_service
            if export_service is not None
            else LibraryExportService()
        )

        self.key_service = (
            key_service
            if key_service is not None
            else LibraryKeyService()
        )

        self.config_service = (
            config_service
            if config_service is not None
            else CloudConfigService()
        )

        self.documents_url = self.FIRESTORE_ROOT.format(
            project_id=self.project_id
        )

    def sync_library(
        self,
        games,
        library_name="My RomDex Library"
    ):
        """
        Creates or reuses this installation's cloud library, then uploads
        the current local games.

        On the first sync, a new Firestore library is created and its IDs
        are saved locally. Later syncs reuse the saved library ID so
        duplicate cloud libraries are not created.
        """
        try:
            config = self.config_service.load_config()
        except CloudConfigError as error:
            raise CloudLibraryError(str(error)) from error

        created_new_library = False

        if config:
            library_id = config["library_id"]

            # Confirm the remembered cloud library still exists and belongs
            # to this anonymous Firebase installation.
            library = self.get_library(library_id)

            if library.get("owner_uid") != self.auth_service.uid:
                raise CloudLibraryError(
                    "The saved cloud library is not owned by this "
                    "Firebase installation."
                )

        else:
            library = self.create_library(
                name=library_name
            )
            library_id = library["library_id"]

            try:
                self.config_service.save_config(
                    library_id=library["library_id"],
                    share_id=library["share_id"],
                    private_sync_key=(
                        library["private_sync_key"]
                    ),
                    library_name=library["name"]
                )
            except CloudConfigError as error:
                raise CloudLibraryError(str(error)) from error

            created_new_library = True

        upload_result = self.upload_library_games(
            library_id=library_id,
            games=games
        )

        active_config = self.config_service.load_config()

        return {
            "library_id": library_id,
            "share_id": active_config.get("share_id"),
            "library_name": active_config.get(
                "library_name",
                library_name
            ),
            "uploaded_count": upload_result[
                "uploaded_count"
            ],
            "created_new_library": (
                created_new_library
            )
        }

    def create_library(self, name="My RomDex Library"):
        """
        Creates a new cloud library owned by this anonymous Firebase UID.
        """
        self.auth_service.get_valid_id_token()

        library_id = self.key_service.generate_library_id()
        share_id = self.key_service.generate_share_key()
        private_sync_key = self.key_service.generate_private_sync_key()
        now = self._utc_now()

        library_data = {
            "library_id": library_id,
            "owner_uid": self.auth_service.uid,
            "share_id": share_id,
            "private_sync_key": private_sync_key,
            "name": name.strip() or "My RomDex Library",
            "created_at": now,
            "updated_at": now,
            "game_count": 0
        }

        url = f"{self.documents_url}/libraries"

        try:
            response = requests.post(
                url,
                params={"documentId": library_id},
                headers=self.auth_service.get_auth_headers(),
                json={"fields": self._encode_fields(library_data)},
                timeout=20
            )
        except requests.RequestException as error:
            raise CloudLibraryError(
                f"Could not connect to Cloud Firestore: {error}"
            ) from error

        self._raise_for_firestore_error(response)
        return library_data

    def get_library(self, library_id):
        """
        Retrieves one cloud library document.
        """
        normalized_id = library_id.strip()

        if not self.key_service.is_valid_library_id(normalized_id):
            raise CloudLibraryError("The library ID format is invalid.")

        url = f"{self.documents_url}/libraries/{normalized_id}"

        try:
            response = requests.get(
                url,
                headers=self.auth_service.get_auth_headers(),
                timeout=20
            )
        except requests.RequestException as error:
            raise CloudLibraryError(
                f"Could not connect to Cloud Firestore: {error}"
            ) from error

        self._raise_for_firestore_error(response)
        return self._decode_fields(response.json().get("fields", {}))

    def upload_library_games(self, library_id, games):
        """
        Uploads local Game objects into the library's games subcollection.

        Existing cloud documents with the same stable game IDs are updated.
        ROM files, ROM paths, and local file names are never uploaded.
        """
        library = self.get_library(library_id)

        if library.get("owner_uid") != self.auth_service.uid:
            raise CloudLibraryError(
                "This Firebase installation does not own that cloud library."
            )

        exported_games = self.export_service.export_games(games)
        uploaded_count = 0

        for exported_game in exported_games:
            cloud_game_id = self.export_service.get_cloud_game_id(
                exported_game
            )

            self._upsert_game_document(
                library_id=library_id,
                game_id=cloud_game_id,
                game_data=exported_game
            )
            uploaded_count += 1

        self._update_library_summary(
            library_id=library_id,
            game_count=uploaded_count
        )

        return {
            "library_id": library_id,
            "uploaded_count": uploaded_count
        }

    def get_library_games(self, library_id):
        """
        Downloads the game documents stored under one cloud library.
        """
        if not self.key_service.is_valid_library_id(library_id):
            raise CloudLibraryError("The library ID format is invalid.")

        url = (
            f"{self.documents_url}/libraries/"
            f"{library_id}/games"
        )

        try:
            response = requests.get(
                url,
                headers=self.auth_service.get_auth_headers(),
                timeout=20
            )
        except requests.RequestException as error:
            raise CloudLibraryError(
                f"Could not connect to Cloud Firestore: {error}"
            ) from error

        self._raise_for_firestore_error(response)

        documents = response.json().get("documents", [])

        return [
            self._decode_fields(document.get("fields", {}))
            for document in documents
        ]

    def _upsert_game_document(self, library_id, game_id, game_data):
        url = (
            f"{self.documents_url}/libraries/"
            f"{library_id}/games/{game_id}"
        )

        try:
            response = requests.patch(
                url,
                headers=self.auth_service.get_auth_headers(),
                json={"fields": self._encode_fields(game_data)},
                timeout=20
            )
        except requests.RequestException as error:
            raise CloudLibraryError(
                f"Could not upload game '{game_data.get('title')}': {error}"
            ) from error

        self._raise_for_firestore_error(response)

    def _update_library_summary(self, library_id, game_count):
        now = self._utc_now()
        url = f"{self.documents_url}/libraries/{library_id}"

        params = [
            ("updateMask.fieldPaths", "game_count"),
            ("updateMask.fieldPaths", "updated_at")
        ]

        data = {
            "game_count": game_count,
            "updated_at": now
        }

        try:
            response = requests.patch(
                url,
                params=params,
                headers=self.auth_service.get_auth_headers(),
                json={"fields": self._encode_fields(data)},
                timeout=20
            )
        except requests.RequestException as error:
            raise CloudLibraryError(
                f"Could not update the library summary: {error}"
            ) from error

        self._raise_for_firestore_error(response)

    @staticmethod
    def _utc_now():
        return (
            datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )

    @classmethod
    def _encode_fields(cls, values):
        """
        Converts a flat Python dictionary into Firestore REST values.
        """
        return {
            key: cls._encode_value(value)
            for key, value in values.items()
        }

    @classmethod
    def _encode_value(cls, value):
        if isinstance(value, bool):
            return {"booleanValue": value}

        if isinstance(value, int):
            return {"integerValue": str(value)}

        if isinstance(value, float):
            return {"doubleValue": value}

        if value is None:
            return {"nullValue": None}

        if isinstance(value, list):
            return {
                "arrayValue": {
                    "values": [
                        cls._encode_value(item)
                        for item in value
                    ]
                }
            }

        if isinstance(value, dict):
            return {
                "mapValue": {
                    "fields": cls._encode_fields(value)
                }
            }

        return {"stringValue": str(value)}

    @classmethod
    def _decode_fields(cls, fields):
        return {
            key: cls._decode_value(value)
            for key, value in fields.items()
        }

    @classmethod
    def _decode_value(cls, wrapped_value):
        if "stringValue" in wrapped_value:
            return wrapped_value["stringValue"]

        if "integerValue" in wrapped_value:
            return int(wrapped_value["integerValue"])

        if "doubleValue" in wrapped_value:
            return float(wrapped_value["doubleValue"])

        if "booleanValue" in wrapped_value:
            return wrapped_value["booleanValue"]

        if "nullValue" in wrapped_value:
            return None

        if "arrayValue" in wrapped_value:
            values = wrapped_value["arrayValue"].get("values", [])
            return [
                cls._decode_value(item)
                for item in values
            ]

        if "mapValue" in wrapped_value:
            fields = wrapped_value["mapValue"].get("fields", {})
            return cls._decode_fields(fields)

        return wrapped_value

    @staticmethod
    def _raise_for_firestore_error(response):
        if response.ok:
            return

        try:
            data = response.json()
        except ValueError:
            raise CloudLibraryError(
                f"Firestore returned HTTP {response.status_code}."
            )

        error_data = data.get("error", {})
        status = error_data.get("status", "UNKNOWN")
        message = error_data.get("message", "Unknown Firestore error.")

        friendly_messages = {
            "PERMISSION_DENIED": (
                "Firestore denied the request. Check Authentication and "
                "the published Firestore Security Rules."
            ),
            "NOT_FOUND": (
                "The Firestore project, database, library, or document "
                "could not be found."
            ),
            "ALREADY_EXISTS": (
                "A Firestore document with this ID already exists."
            ),
            "UNAUTHENTICATED": (
                "Firebase authentication expired or was rejected."
            )
        }

        raise CloudLibraryError(
            friendly_messages.get(
                status,
                f"Firestore error ({status}): {message}"
            )
        )
