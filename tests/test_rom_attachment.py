import sys

from repositories.game_repository import GameRepository


def main():
    if len(sys.argv) < 3:
        print(
            'Usage: python test_rom_attachment.py '
            'GAME_ID "C:\\Path\\To\\Game.nds"'
        )
        return

    try:
        game_id = int(sys.argv[1])
    except ValueError:
        print("GAME_ID must be a number.")
        return

    rom_path = sys.argv[2]
    repository = GameRepository()

    try:
        original_game = repository.get_game_by_id(game_id)

        if not original_game:
            print(f"No game exists with ID {game_id}.")
            return

        original_rom_path = original_game.rom_path

        print(f"Testing game: {original_game.title}")
        print(f"Original ROM: {original_rom_path or 'None'}")

        attached_game = repository.attach_rom_to_game(
            game_id=game_id,
            rom_path=rom_path
        )

        print("ROM attachment successful.")
        print(f"File name: {attached_game.file_name}")
        print(f"ROM path: {attached_game.rom_path}")
        print(f"Status: {attached_game.status}")

        result = repository.detach_rom_from_game(game_id)

        print("ROM detachment successful.")
        print(
            "Previous attachment: "
            f"{result['previous_attachment']['rom_path']}"
        )
        print(
            "Current ROM path: "
            f"{result['game'].rom_path}"
        )

        # Restore an existing original attachment when possible.
        if original_rom_path:
            restored_game = repository.attach_rom_to_game(
                game_id=game_id,
                rom_path=original_rom_path
            )
            print(
                "Original ROM restored: "
                f"{restored_game.rom_path}"
            )

    except Exception as error:
        print(f"ROM attachment test failed: {error}")

    finally:
        repository.close()


if __name__ == "__main__":
    main()
