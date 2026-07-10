import json
from pathlib import Path


class CloudConfigError(Exception):
    """Raised when RomDex cannot read or write cloud configuration."""


class CloudConfigService:
    """
    Stores the current RomDex cloud-library configuration locally.

    This service does not communicate with Firebase. It only manages the
    local JSON file that remembers which cloud library this installation
    is connected to.
    """

    def __init__(self, config_file=None):
        if config_file is None:
            project_root = Path(__file__).resolve().parents[2]
            config_file = (
                project_root
                / "data"
                / "cloud_library_config.json"
            )

        self.config_file = Path(config_file)

    def save_config(
        self,
        library_id,
        share_id,
        private_sync_key,
        library_name="My RomDex Library"
    ):
        """
        Saves the active cloud-library configuration locally.
        """
        config = {
            "library_id": library_id.strip(),
            "share_id": share_id.strip(),
            "private_sync_key": private_sync_key.strip(),
            "library_name": (
                library_name.strip()
                or "My RomDex Library"
            )
        }

        self._validate_config(config)

        try:
            self.config_file.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            with self.config_file.open(
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(
                    config,
                    file,
                    indent=2
                )

        except OSError as error:
            raise CloudConfigError(
                f"Could not save cloud configuration: {error}"
            ) from error

        return config.copy()

    def load_config(self):
        """
        Loads the saved cloud-library configuration.

        Returns an empty dictionary when no configuration exists yet.
        """
        if not self.config_file.exists():
            return {}

        try:
            with self.config_file.open(
                "r",
                encoding="utf-8"
            ) as file:
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

        self._validate_config(config)
        return config

    def has_config(self):
        """
        Returns True when a valid local cloud configuration exists.
        """
        try:
            config = self.load_config()
        except CloudConfigError:
            return False

        return bool(config)

    def get_library_id(self):
        """
        Returns the saved cloud library ID, or None when unavailable.
        """
        return self.load_config().get("library_id")

    def get_share_id(self):
        """
        Returns the saved public share key, or None when unavailable.
        """
        return self.load_config().get("share_id")

    def get_private_sync_key(self):
        """
        Returns the saved private sync key, or None when unavailable.
        """
        return self.load_config().get(
            "private_sync_key"
        )

    def clear_config(self):
        """
        Removes the local cloud-library configuration.
        """
        try:
            self.config_file.unlink(
                missing_ok=True
            )
        except OSError as error:
            raise CloudConfigError(
                f"Could not remove cloud configuration: {error}"
            ) from error

    @staticmethod
    def _validate_config(config):
        required_fields = (
            "library_id",
            "share_id",
            "private_sync_key",
            "library_name"
        )

        missing_fields = [
            field
            for field in required_fields
            if not isinstance(
                config.get(field),
                str
            )
            or not config.get(field).strip()
        ]

        if missing_fields:
            fields_text = ", ".join(missing_fields)

            raise CloudConfigError(
                "Cloud configuration is missing required "
                f"value(s): {fields_text}"
            )
