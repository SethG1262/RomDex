import json
from pathlib import Path


class EmulatorConfigError(Exception):
    """Raised when emulator configuration cannot be read or written."""


class EmulatorConfigService:
    """
    Stores and retrieves emulator executable settings for RomDex.
    """

    SUPPORTED_SYSTEMS = {
        "Nintendo DS": "nintendo_ds",
        "Nintendo DSi": "nintendo_ds",
        "Nintendo 3DS": "nintendo_3ds"
    }

    def __init__(self, config_file=None):
        if config_file is None:
            project_root = Path(__file__).resolve().parents[2]
            config_file = project_root / "data" / "emulator_config.json"

        self.config_file = Path(config_file)

    def save_emulator(self, system, emulator_name, executable_path):
        system_key = self._get_system_key(system)
        path = Path(executable_path).expanduser()

        if not emulator_name or not emulator_name.strip():
            raise EmulatorConfigError("An emulator name is required.")

        if not path.exists():
            raise EmulatorConfigError(
                "The selected emulator executable does not exist."
            )

        if not path.is_file():
            raise EmulatorConfigError(
                "The emulator path must point to a file."
            )

        if path.suffix.lower() != ".exe":
            raise EmulatorConfigError(
                "The selected emulator must be a Windows .exe file."
            )

        config = self.load_config()
        config.setdefault("emulators", {})

        config["emulators"][system_key] = {
            "name": emulator_name.strip(),
            "executable_path": str(path.resolve())
        }

        self._save_config(config)
        return config["emulators"][system_key].copy()

    def get_emulator(self, system):
        system_key = self._get_system_key(system)
        config = self.load_config()
        return config.get("emulators", {}).get(system_key)

    def get_executable_path(self, system):
        emulator = self.get_emulator(system)
        return emulator.get("executable_path") if emulator else None

    def is_configured(self, system):
        executable_path = self.get_executable_path(system)
        return bool(executable_path and Path(executable_path).is_file())

    def remove_emulator(self, system):
        system_key = self._get_system_key(system)
        config = self.load_config()
        emulators = config.get("emulators", {})
        removed = emulators.pop(system_key, None)

        if removed is not None:
            config["emulators"] = emulators
            self._save_config(config)

        return removed

    def load_config(self):
        if not self.config_file.exists():
            return {"emulators": {}}

        try:
            with self.config_file.open("r", encoding="utf-8") as file:
                config = json.load(file)
        except json.JSONDecodeError as error:
            raise EmulatorConfigError(
                "The emulator configuration contains invalid JSON."
            ) from error
        except OSError as error:
            raise EmulatorConfigError(
                f"Could not read emulator configuration: {error}"
            ) from error

        if not isinstance(config, dict):
            raise EmulatorConfigError(
                "The emulator configuration must contain a JSON object."
            )

        config.setdefault("emulators", {})
        return config

    def clear_config(self):
        try:
            self.config_file.unlink(missing_ok=True)
        except OSError as error:
            raise EmulatorConfigError(
                f"Could not remove emulator configuration: {error}"
            ) from error

    def _save_config(self, config):
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with self.config_file.open("w", encoding="utf-8") as file:
                json.dump(config, file, indent=2)
        except OSError as error:
            raise EmulatorConfigError(
                f"Could not save emulator configuration: {error}"
            ) from error

    def _get_system_key(self, system):
        normalized_system = (system or "").strip()
        system_key = self.SUPPORTED_SYSTEMS.get(normalized_system)

        if not system_key:
            raise EmulatorConfigError(
                f'Unsupported platform: "{normalized_system}".'
            )

        return system_key
