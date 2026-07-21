import requests

from services.cloud.firebase_auth_service import FirebaseAuthService
from services.cloud.library_key_service import LibraryKeyService


class LibraryShareError(Exception):
    """Raised when a shared cloud library cannot be found or imported."""


class LibraryShareService:
    """Downloads read-only metadata through the Share Key function."""

    SHARE_FUNCTION_URL = (
        "https://us-central1-romdex-d6b1b.cloudfunctions.net/"
        "read_shared_library"
    )

    def __init__(
        self,
        auth_service=None,
        key_service=None,
        cloud_library_service=None,
        share_function_url=None
    ):
        self.auth_service = (
            auth_service
            if auth_service is not None
            else (
                cloud_library_service.auth_service
                if cloud_library_service is not None
                else FirebaseAuthService()
            )
        )
        self.key_service = (
            key_service
            if key_service is not None
            else LibraryKeyService()
        )
        self.share_function_url = (
            share_function_url or self.SHARE_FUNCTION_URL
        )

    def find_library_by_share_key(self, share_key):
        """Returns sanitized library information for a valid Share Key."""
        return self.download_shared_library(share_key)["library"]

    def download_shared_library(self, share_key):
        """Returns sanitized library information and cloud game metadata."""
        normalized_key = str(share_key or "").strip()

        if not self.key_service.is_valid_share_key(normalized_key):
            raise LibraryShareError("The RomDex Share Key format is invalid.")

        try:
            response = requests.post(
                self.share_function_url,
                headers=self.auth_service.get_auth_headers(),
                json={"share_key": normalized_key},
                timeout=30
            )
        except requests.RequestException as error:
            raise LibraryShareError(
                f"Could not download the shared library: {error}"
            ) from error

        if not response.ok:
            self._raise_function_error(response)

        try:
            shared_data = response.json()
        except ValueError as error:
            raise LibraryShareError(
                "The RomDex sharing service returned invalid data."
            ) from error

        library = shared_data.get("library")
        games = shared_data.get("games")
        if not isinstance(library, dict) or not isinstance(games, list):
            raise LibraryShareError(
                "The RomDex sharing service returned an incomplete library."
            )

        if not library.get("library_id") or not library.get("name"):
            raise LibraryShareError(
                "The shared library is missing required information."
            )

        return {
            "library": library,
            "games": games
        }

    def import_shared_library(
        self,
        share_key,
        game_repository,
        mode="merge"
    ):
        """
        Downloads a read-only shared library into SQLite.

        Merge adds games the user does not already have. Overwrite makes the
        current local metadata library match the shared snapshot. The local
        cloud identity and Share Key remain unchanged. ROM files are never
        downloaded or deleted.
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
            "skipped_count": import_result["skipped_count"],
            "removed_count": import_result.get("removed_count", 0),
            "preserved_rom_file_count": import_result.get(
                "preserved_rom_file_count",
                import_result.get("unlinked_rom_count", 0)
            ),
            "unlinked_rom_count": import_result.get(
                "unlinked_rom_count",
                0
            )
        }

    @staticmethod
    def _raise_function_error(response):
        try:
            data = response.json()
        except ValueError:
            raise LibraryShareError(
                f"The RomDex sharing service returned HTTP "
                f"{response.status_code}."
            )

        message = (
            data.get("error", {}).get("message")
            or "The RomDex sharing service rejected the request."
        )
        raise LibraryShareError(message)
