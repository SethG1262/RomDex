import sys

from repositories.game_repository import GameRepository
from services.cloud.library_share_service import (
    LibraryShareError,
    LibraryShareService
)


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python test_library_sharing.py "
            "RDX-SHARE-your-key"
        )
        return

    share_key = sys.argv[1].strip()
    repository = GameRepository()

    try:
        share_service = LibraryShareService()

        result = share_service.import_shared_library(
            share_key=share_key,
            game_repository=repository
        )

        library = result["library"]

        print("Shared library import successful.")
        print(f"Library name: {library.get('name')}")
        print(
            f"Cloud games found: "
            f"{result['cloud_game_count']}"
        )
        print(
            f"New games imported: "
            f"{result['imported_count']}"
        )
        print(
            f"Duplicates skipped: "
            f"{result['skipped_count']}"
        )

    except LibraryShareError as error:
        print(f"Shared library import failed: {error}")

    finally:
        repository.close()


if __name__ == "__main__":
    main()
