from services.cloud.cloud_library_service import (
    CloudLibraryError,
    CloudLibraryService
)


def main():
    try:
        cloud_service = CloudLibraryService()

        created_library = cloud_service.create_library(
            name="My RomDex Library"
        )

        print("Cloud library created successfully.")
        print(f"Library ID: {created_library['library_id']}")
        print(f"Owner UID: {created_library['owner_uid']}")
        print(f"Share ID: {created_library['share_id']}")

        downloaded_library = cloud_service.get_library(
            created_library["library_id"]
        )

        print("\nFirestore read-back successful.")
        print(f"Name: {downloaded_library['name']}")
        print(f"Game count: {downloaded_library['game_count']}")
        print(
            "Library ID matches: "
            f"{downloaded_library['library_id'] == created_library['library_id']}"
        )

    except CloudLibraryError as error:
        print(f"Cloud library test failed: {error}")


if __name__ == "__main__":
    main()
