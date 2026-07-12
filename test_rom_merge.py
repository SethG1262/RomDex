import argparse

from repositories.game_repository import GameRepository


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Merge a personal ROM entry into an IGDB metadata entry."
        )
    )

    parser.add_argument(
        "target_game_id",
        type=int,
        help="ID of the IGDB game that should remain."
    )

    parser.add_argument(
        "source_game_id",
        type=int,
        help="ID of the personal ROM entry that will be removed."
    )

    parser.add_argument(
        "--merge",
        action="store_true",
        help="Perform the merge after showing the preview."
    )

    return parser.parse_args()


def main():
    arguments = parse_arguments()
    repository = GameRepository()

    try:
        target = repository.get_game_by_id(
            arguments.target_game_id
        )
        source = repository.get_game_by_id(
            arguments.source_game_id
        )

        if not target:
            print(
                f"No target game exists with ID "
                f"{arguments.target_game_id}."
            )
            return

        if not source:
            print(
                f"No source game exists with ID "
                f"{arguments.source_game_id}."
            )
            return

        print("Merge preview")
        print("-------------")
        print(
            f"Target kept: {target.id} - {target.title}"
        )
        print(
            f"Target IGDB ID: {target.igdb_id or 'None'}"
        )
        print(
            f"Source removed: {source.id} - {source.title}"
        )
        print(
            f"Source ROM: {source.rom_path or 'None'}"
        )

        if not arguments.merge:
            print()
            print(
                "Preview only. Add --merge to perform "
                "the database change."
            )
            return

        result = repository.merge_local_rom_into_game(
            target_game_id=arguments.target_game_id,
            source_game_id=arguments.source_game_id
        )

        merged_game = result["game"]
        removed_source = result["removed_source"]

        print()
        print("Merge successful.")
        print(
            f"Remaining game: {merged_game.id} - "
            f"{merged_game.title}"
        )
        print(f"ROM: {merged_game.rom_path}")
        print(f"Status: {merged_game.status}")
        print(
            f"Removed duplicate: "
            f"{removed_source['id']} - "
            f"{removed_source['title']}"
        )

    except Exception as error:
        print(f"ROM merge failed: {error}")

    finally:
        repository.close()


if __name__ == "__main__":
    main()
