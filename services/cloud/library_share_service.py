import requests
from dotenv import load_dotenv

from services.cloud.cloud_library_service import (
    CloudLibraryError,
    CloudLibraryService
)
from services.cloud.firebase_auth_service import FirebaseAuthService
from services.cloud.library_key_service import LibraryKeyService
from services.cloud.firebase_public_config import get_firebase_project_id


class LibraryShareError(Exception):
    """Raised when a shared cloud library cannot be found or imported."""


class LibraryShareService:
    """
    Resolves public RomDex share keys and downloads shared library metadata.

    The service is read-only. It does not modify the original cloud library.
    """

    FIRESTORE_RUN_QUERY_URL = (
        "https://firestore.googleapis.com/v1/"
        "projects/{project_id}/databases/(default)/documents:runQuery"
    )

    def __init__(
        self,
        auth_service=None,
        key_service=None,
        cloud_library_service=None
    ):
        load_dotenv()

        self.project_id = get_firebase_project_id()

        if not self.project_id:
            raise LibraryShareError(
                "The public Firebase project ID is missing from RomDex."
            )

        self.auth_service = (
            auth_service
            if auth_service is not None
            else FirebaseAuthService()
        )

        self.key_service = (
            key_service
            if key_service is not None
            else LibraryKeyService()
        )

        self.cloud_library_service = (
            cloud_library_service
            if cloud_library_service is not None
            else CloudLibraryService(
                auth_service=self.auth_service,
                key_service=self.key_service
            )
        )

        self.run_query_url = self.FIRESTORE_RUN_QUERY_URL.format(
            project_id=self.project_id
        )

    def find_library_by_share_key(self, share_key):
        """
        Finds a cloud library document using its public share key.
        """
        normalized_key = share_key.strip()

        if not self.key_service.is_valid_share_key(normalized_key):
            raise LibraryShareError(
                "The RomDex share key format is invalid."
            )

        query = {
            "structuredQuery": {
                "from": [
                    {
                        "collectionId": "libraries"
                    }
                ],
                "where": {
                    "fieldFilter": {
                        "field": {
                            "fieldPath": "share_id"
                        },
                        "op": "EQUAL",
                        "value": {
                            "stringValue": normalized_key
                        }
                    }
                },
                "limit": 1
            }
        }

        try:
            response = requests.post(
                self.run_query_url,
                headers=self.auth_service.get_auth_headers(),
                json=query,
                timeout=20
            )
        except requests.RequestException as error:
            raise LibraryShareError(
                f"Could not search Firestore: {error}"
            ) from error

        if not response.ok:
            self._raise_query_error(response)

        results = response.json()

        for result in results:
            document = result.get("document")

            if not document:
                continue

            library = self.cloud_library_service._decode_fields(
                document.get("fields", {})
            )

            if library:
                return library

        raise LibraryShareError(
            "No cloud library was found for that share key."
        )

    def download_shared_library(self, share_key):
        """
        Returns the shared library metadata and its cloud game records.
        """
        library = self.find_library_by_share_key(share_key)

        library_id = library.get("library_id")

        if not library_id:
            raise LibraryShareError(
                "The shared library is missing its library ID."
            )

        try:
            games = self.cloud_library_service.get_library_games(
                library_id
            )
        except CloudLibraryError as error:
            raise LibraryShareError(str(error)) from error

        return {
            "library": library,
            "games": games
        }

    def import_shared_library(
        self,
        share_key,
        game_repository,
        mode="additive"
    ):
        """
        Downloads a shared library and merges its games into SQLite.

        Additive mode skips matching games. Overwrite mode refreshes matching
        metadata in place. ROM paths and local filenames are never imported
        or replaced because they belong to the destination computer.
        """
        shared_data = self.download_shared_library(share_key)

        import_result = game_repository.import_cloud_games(
            shared_data["games"],
            mode=mode
        )

        return {
            "library": shared_data["library"],
            "cloud_game_count": len(shared_data["games"]),
            "imported_count": import_result["imported_count"],
            "updated_count": import_result["updated_count"],
            "skipped_count": import_result["skipped_count"]
        }

    @staticmethod
    def _raise_query_error(response):
        try:
            data = response.json()
        except ValueError:
            raise LibraryShareError(
                f"Firestore returned HTTP {response.status_code}."
            )

        error = data.get("error", {})
        status = error.get("status", "UNKNOWN")
        message = error.get("message", "Unknown Firestore error.")

        if status == "PERMISSION_DENIED":
            raise LibraryShareError(
                "Firestore denied shared-library lookup. "
                "Check the published security rules."
            )

        if status == "UNAUTHENTICATED":
            raise LibraryShareError(
                "Firebase authentication was rejected."
            )

        raise LibraryShareError(
            f"Firestore query failed ({status}): {message}"
        )
