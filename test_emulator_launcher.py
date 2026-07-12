import argparse
from pathlib import Path

from repositories.game_repository import GameRepository
from services.emulator.emulator_config_service import (
    EmulatorConfigError,
    EmulatorConfigService
)
from services.emulator.emulator_launcher_service import (
    EmulatorLaunchError,
    EmulatorLauncherService
)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Configure an emulator and test launching a RomDex game."
        )
    )

    parser.add_argument(
        "game_id",
        type=int,
        help="Local database ID of the game to test."
    )

    parser.add_argument(
        "emulator_path",
        help="Full path to the emulator .exe file."
    )

    parser.add_argument(
        "--launch",
        action="store_true",
        help="Actually start the emulator after validation."
    )

    return parser.parse_args()


def main():
    arguments = parse_arguments()
    repository = GameRepository()

    try:
        game = repository.get_game_by_id(arguments.game_id)

        if not game:
            print(
                f"No game exists with ID {arguments.game_id}."
            )
            return

        if not game.rom_path:
            print(
                f'"{game.title}" does not have a ROM attached.'
            )
            return

        config_service = EmulatorConfigService()

        saved_config = config_service.save_emulator(
            system=game.platform,
            emulator_name=Path(
                arguments.emulator_path
            ).stem,
            executable_path=arguments.emulator_path
        )

        print("Emulator configuration saved.")
        print(f"Game: {game.title}")
        print(f"Platform: {game.platform}")
        print(f"Emulator: {saved_config['name']}")
        print(f"ROM: {game.rom_path}")

        launcher = EmulatorLauncherService(
            config_service=config_service
        )

        status = launcher.get_launch_status(game)

        print(f"Ready: {status['ready']}")
        print(f"Status: {status['message']}")

        if status["command"]:
            print("Launch command:")
            print(f'  Emulator: {status["command"][0]}')
            print(f'  ROM: {status["command"][1]}')

        if arguments.launch:
            process = launcher.launch_game(game)

            print("Launch request sent successfully.")
            print(f"Process ID: {process.pid}")
        else:
            print(
                "Validation only. Add --launch to actually "
                "start the emulator."
            )

    except (
        EmulatorConfigError,
        EmulatorLaunchError,
        ValueError
    ) as error:
        print(f"Emulator launch test failed: {error}")

    finally:
        repository.close()


if __name__ == "__main__":
    main()
