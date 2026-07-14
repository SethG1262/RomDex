from repositories.game_repository import GameRepository
from services.cloud.cloud_library_service import (
    CloudLibraryError,
    CloudLibraryService
)


def main():
    repository = GameRepository()

    try:
        local_games = repository.get_all_games()

        print(f"Local games found: {len(local_games)}")

        cloud_service = CloudLibraryService()

        cloud_library = cloud_service.create_library(
            name="My RomDex Library"
        )

        print("Cloud library created.")
        print(f"Library ID: {cloud_library['library_id']}")
        print(f"Share ID: {cloud_library['share_id']}")

        result = cloud_service.upload_library_games(
            cloud_library["library_id"],
            local_games
        )

        print(
            f"Uploaded games: {result['uploaded_count']}"
        )

        downloaded_games = cloud_service.get_library_games(
            cloud_library["library_id"]
        )

        print(
            f"Downloaded cloud game records: {len(downloaded_games)}"
        )

        if downloaded_games:
            print(
                f"First cloud game: {downloaded_games[0]['title']}"
            )

        print("Cloud library upload test successful.")

    except CloudLibraryError as error:
        print(f"Cloud library upload failed: {error}")

    finally:
        repository.close()


if __name__ == "__main__":
    main()
