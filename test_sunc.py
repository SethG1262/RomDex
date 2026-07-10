from repositories.game_repository import GameRepository
from services.cloud.cloud_library_service import (
    CloudLibraryError,
    CloudLibraryService
)


def main():
    repository = GameRepository()

    try:
        games = repository.get_all_games()
        cloud_service = CloudLibraryService()

        result = cloud_service.sync_library(
            games=games,
            library_name="My RomDex Library"
        )

        print("Cloud sync successful.")
        print(f"Library ID: {result['library_id']}")
        print(f"Share ID: {result['share_id']}")
        print(f"Uploaded games: {result['uploaded_count']}")
        print(
            "Created new library: "
            f"{result['created_new_library']}"
        )

        print(
            "\nRun this test again. On the second run, "
            "'Created new library' should be False and "
            "the Library ID should remain the same."
        )

    except CloudLibraryError as error:
        print(f"Cloud sync failed: {error}")

    finally:
        repository.close()


if __name__ == "__main__":
    main()
