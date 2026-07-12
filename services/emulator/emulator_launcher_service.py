import subprocess
from pathlib import Path

from services.emulator.emulator_config_service import (
    EmulatorConfigError,
    EmulatorConfigService
)


class EmulatorLaunchError(Exception):
    """Raised when RomDex cannot prepare or launch a game."""


class EmulatorLauncherService:
    """
    Validates and launches a Game through its configured emulator.
    """

    def __init__(self, config_service=None):
        self.config_service = (
            config_service
            if config_service is not None
            else EmulatorConfigService()
        )

    def build_launch_command(self, game):
        """
        Returns the command RomDex will use to launch a game.

        This performs all validation but does not start the emulator.
        """
        platform = self._get_game_platform(game)
        rom_path = self._get_valid_rom_path(game)
        emulator_path = self._get_valid_emulator_path(platform)

        return [
            str(emulator_path),
            str(rom_path)
        ]

    def launch_game(self, game):
        """
        Launches the selected ROM through its configured emulator.

        Returns the subprocess.Popen object when the process starts.
        """
        command = self.build_launch_command(game)
        emulator_directory = str(Path(command[0]).parent)

        try:
            return subprocess.Popen(
                command,
                cwd=emulator_directory,
                shell=False
            )

        except OSError as error:
            raise EmulatorLaunchError(
                f"Windows could not start the emulator: {error}"
            ) from error

    def can_launch(self, game):
        """
        Returns True when the game and emulator paths are valid.
        """
        try:
            self.build_launch_command(game)
            return True
        except (
            EmulatorLaunchError,
            EmulatorConfigError,
            ValueError
        ):
            return False

    def get_launch_status(self, game):
        """
        Returns a user-friendly readiness result for the frontend.
        """
        try:
            command = self.build_launch_command(game)

            return {
                "ready": True,
                "message": "Ready to launch.",
                "command": command
            }

        except (
            EmulatorLaunchError,
            EmulatorConfigError,
            ValueError
        ) as error:
            return {
                "ready": False,
                "message": str(error),
                "command": None
            }

    def _get_game_platform(self, game):
        platform = getattr(game, "platform", None)

        if not platform or not platform.strip():
            raise EmulatorLaunchError(
                "This game does not have a supported platform."
            )

        return platform.strip()

    def _get_valid_rom_path(self, game):
        rom_path = getattr(game, "rom_path", None)

        if not rom_path:
            raise EmulatorLaunchError(
                "This game does not have a ROM attached."
            )

        path = Path(rom_path).expanduser()

        if not path.exists():
            raise EmulatorLaunchError(
                "The attached ROM file could not be found."
            )

        if not path.is_file():
            raise EmulatorLaunchError(
                "The attached ROM path does not point to a file."
            )

        return path.resolve()

    def _get_valid_emulator_path(self, platform):
        try:
            emulator = self.config_service.get_emulator(platform)
        except EmulatorConfigError as error:
            raise EmulatorLaunchError(str(error)) from error

        if not emulator:
            raise EmulatorLaunchError(
                f'No emulator is configured for "{platform}".'
            )

        executable_path = emulator.get("executable_path")

        if not executable_path:
            raise EmulatorLaunchError(
                f'The emulator configuration for "{platform}" '
                "does not include an executable path."
            )

        path = Path(executable_path).expanduser()

        if not path.exists():
            raise EmulatorLaunchError(
                "The configured emulator executable could not be found."
            )

        if not path.is_file():
            raise EmulatorLaunchError(
                "The configured emulator path does not point to a file."
            )

        if path.suffix.lower() != ".exe":
            raise EmulatorLaunchError(
                "The configured emulator must be a Windows .exe file."
            )

        return path.resolve()
