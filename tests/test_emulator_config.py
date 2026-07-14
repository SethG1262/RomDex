from pathlib import Path
import sys

from services.emulator.emulator_config_service import (
    EmulatorConfigError,
    EmulatorConfigService
)


def main():
    if len(sys.argv) < 2:
        print(
            'Usage: python test_emulator_config.py '
            '"C:\\Path\\To\\melonDS.exe"'
        )
        return

    executable_path = sys.argv[1]
    test_file = Path("data") / "test_emulator_config.json"
    service = EmulatorConfigService(config_file=test_file)

    try:
        saved = service.save_emulator(
            system="Nintendo DS",
            emulator_name="melonDS",
            executable_path=executable_path
        )

        print("Emulator configuration saved.")
        print(f"Name: {saved['name']}")
        print(f"Executable: {saved['executable_path']}")

        loaded = service.get_emulator("Nintendo DS")

        print("Emulator configuration loaded.")
        print(f"Configuration matches: {loaded == saved}")
        print(
            "Executable is valid: "
            f"{service.is_configured('Nintendo DS')}"
        )

        service.remove_emulator("Nintendo DS")

        print(
            "Configuration removed: "
            f"{not service.is_configured('Nintendo DS')}"
        )

    except EmulatorConfigError as error:
        print(f"Emulator configuration test failed: {error}")

    finally:
        test_file.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
