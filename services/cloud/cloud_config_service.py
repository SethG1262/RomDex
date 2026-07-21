import json
from pathlib import Path


class CloudConfigError(Exception):
    """Raised when RomDex cannot read or write cloud configuration."""


class CloudConfigService:
    """Stores this installation's cloud library identity locally."""

    def __init__(self, config_file=None):
        if config_file is None:
            project_root = Path(__file__).resolve().parents[2]
            config_file = project_root / "data" / "cloud_library_config.json"

        self.config_file = Path(config_file)

    def save_config(
        self,
        library_id,
        share_id,
        private_sync_key=None,
        library_name="My RomDex Library",
        **_legacy_values
    ):
        """
        Saves the active cloud-library identity.

        ``private_sync_key`` and extra keyword arguments are accepted only so
        an older caller can upgrade without crashing. Access keys are no
        longer stored locally.
        """
        config = {
            "library_id": library_id.strip(),
            "share_id": share_id.strip(),
            "library_name": library_name.strip() or "My RomDex Library"
        }
        self._validate_config(config)

        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with self.config_file.open("w", encoding="utf-8") as file:
                json.dump(config, file, indent=2)
        except OSError as error:
            raise CloudConfigError(
                f"Could not save cloud configuration: {error}"
            ) from error

        return config.copy()

    def load_config(self):
        """Loads the saved identity or returns an empty dictionary."""
        if not self.config_file.exists():
            return {}

        try:
            with self.config_file.open("r", encoding="utf-8") as file:
                config = json.load(file)
        except json.JSONDecodeError as error:
            raise CloudConfigError(
                "The cloud configuration file contains invalid JSON."
            ) from error
        except OSError as error:
            raise CloudConfigError(
                f"Could not read cloud configuration: {error}"
            ) from error

        if not isinstance(config, dict):
            raise CloudConfigError(
                "The cloud configuration file must contain an object."
            )

        # Old private/link fields are deliberately discarded. The file is
        # rewritten in the new format on the next normal synchronization.
        normalized = {
            "library_id": config.get("library_id"),
            "share_id": config.get("share_id"),
            "library_name": config.get("library_name")
        }
        self._validate_config(normalized)
        return normalized

    def has_config(self):
        try:
            return bool(self.load_config())
        except CloudConfigError:
            return False

    def get_library_id(self):
        return self.load_config().get("library_id")

    def get_share_id(self):
        return self.load_config().get("share_id")

    def get_private_sync_key(self):
        """Compatibility method; private synchronization keys were removed."""
        return None

    def get_link_key(self):
        """Compatibility method; Link Keys were removed."""
        return None

    def clear_config(self):
        try:
            self.config_file.unlink(missing_ok=True)
        except OSError as error:
            raise CloudConfigError(
                f"Could not remove cloud configuration: {error}"
            ) from error

    @staticmethod
    def _validate_config(config):
        required_fields = ("library_id", "share_id", "library_name")
        missing_fields = [
            field
            for field in required_fields
            if not isinstance(config.get(field), str)
            or not config.get(field).strip()
        ]
        if missing_fields:
            raise CloudConfigError(
                "Cloud configuration is missing required value(s): "
                + ", ".join(missing_fields)
            )
