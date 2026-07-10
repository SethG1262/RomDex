from pathlib import Path

from services.cloud.cloud_config_service import (
    CloudConfigError,
    CloudConfigService
)


def main():
    test_file = (
        Path("data")
        / "test_cloud_library_config.json"
    )

    service = CloudConfigService(
        config_file=test_file
    )

    try:
        saved_config = service.save_config(
            library_id=(
                "lib_0123456789abcdef"
                "0123456789abcdef"
            ),
            share_id=(
                "RDX-SHARE-"
                "exampleShareKey123456789"
            ),
            private_sync_key=(
                "RDX-SYNC-"
                "examplePrivateSyncKey123456789"
            ),
            library_name="Test RomDex Library"
        )

        print("Cloud configuration saved.")
        print(
            f"Library ID: "
            f"{saved_config['library_id']}"
        )

        loaded_config = service.load_config()

        print("Cloud configuration loaded.")
        print(
            "Config matches: "
            f"{loaded_config == saved_config}"
        )

        print(
            f"Has config: "
            f"{service.has_config()}"
        )

        service.clear_config()

        print(
            "Config removed: "
            f"{not service.has_config()}"
        )

    except CloudConfigError as error:
        print(
            f"Cloud configuration test failed: "
            f"{error}"
        )

    finally:
        try:
            test_file.unlink(
                missing_ok=True
            )
        except OSError:
            pass


if __name__ == "__main__":
    main()
