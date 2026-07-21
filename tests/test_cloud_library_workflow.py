import json
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.game import Game
from repositories import game_repository as repository_module
from repositories.game_repository import GameRepository
from services.cloud import cloud_library_service as cloud_service_module
from services.cloud import library_share_service as share_service_module
from services.cloud.cloud_config_service import CloudConfigService
from services.cloud.cloud_library_service import (
    CloudLibraryError,
    CloudLibraryService
)
from services.cloud.library_export_service import LibraryExportService
from services.cloud.library_key_service import LibraryKeyService
from services.cloud.library_share_service import LibraryShareService
from services.db import Base


@pytest.fixture
def repository(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine)
    monkeypatch.setattr(repository_module, "SessionLocal", testing_session)

    repo = GameRepository()
    yield repo
    repo.close()


def _cloud_game(cloud_id, title, igdb_id=None):
    return {
        "cloud_id": cloud_id,
        "igdb_id": igdb_id,
        "title": title,
        "summary": f"Summary for {title}",
        "storyline": None,
        "cover_url": None,
        "release_year": "2008",
        "platform": "Nintendo DS",
        "status": "Saved"
    }


def test_add_mode_keeps_current_metadata_and_adds_missing_games(repository):
    existing = Game(
        cloud_id="igdb_1",
        igdb_id=1,
        title="My Custom Title",
        platform="Nintendo DS",
        status="Saved"
    )
    repository.session.add(existing)
    repository.session.commit()

    result = repository.import_cloud_games(
        [
            _cloud_game("igdb_1", "Cloud Title", igdb_id=1),
            _cloud_game("igdb_2", "New Game", igdb_id=2)
        ],
        mode=GameRepository.IMPORT_MODE_MERGE
    )

    assert result["imported_count"] == 1
    assert result["skipped_count"] == 1
    assert result["removed_count"] == 0
    assert repository.get_game_by_igdb_id(1).title == "My Custom Title"
    assert repository.get_game_by_igdb_id(2).title == "New Game"


def test_overwrite_replaces_metadata_but_never_deletes_rom_file(
    repository,
    tmp_path
):
    attached_rom = tmp_path / "owned.nds"
    attached_rom.write_bytes(b"ROM")
    unrelated_rom = tmp_path / "unrelated.nds"
    unrelated_rom.write_bytes(b"ROM")

    matching = Game(
        cloud_id="igdb_1",
        igdb_id=1,
        title="Old Metadata",
        platform="Nintendo DS",
        file_name=attached_rom.name,
        rom_path=str(attached_rom),
        status="Owned"
    )
    removed = Game(
        cloud_id="local_old",
        title="Not In Shared Library",
        platform="Nintendo DS",
        file_name=unrelated_rom.name,
        rom_path=str(unrelated_rom),
        status="Owned"
    )
    repository.session.add_all([matching, removed])
    repository.session.commit()

    result = repository.import_cloud_games(
        [_cloud_game("igdb_1", "Fresh Metadata", igdb_id=1)],
        mode=GameRepository.IMPORT_MODE_OVERWRITE
    )

    updated = repository.get_game_by_igdb_id(1)
    assert updated.title == "Fresh Metadata"
    assert updated.rom_path == str(attached_rom)
    assert updated.status == "Owned"
    assert repository.get_game_by_cloud_id("local_old") is None
    assert unrelated_rom.exists()
    assert result["removed_count"] == 1
    assert result["preserved_rom_file_count"] == 1


def test_overwrite_skips_duplicate_incoming_identity(repository):
    duplicate = _cloud_game("igdb_7", "Duplicate", igdb_id=7)
    result = repository.import_cloud_games(
        [duplicate, duplicate.copy()],
        mode=GameRepository.IMPORT_MODE_OVERWRITE
    )

    assert result["imported_count"] == 1
    assert result["skipped_count"] == 1
    assert len(repository.get_all_games()) == 1


def test_legacy_replace_value_maps_to_overwrite(repository):
    repository.session.add(Game(
        cloud_id="local_old",
        title="Old",
        platform="Nintendo DS"
    ))
    repository.session.commit()

    result = repository.import_cloud_games(
        [_cloud_game("igdb_1", "Shared", igdb_id=1)],
        mode=GameRepository.IMPORT_MODE_REPLACE
    )

    assert result["removed_count"] == 1
    assert repository.get_game_by_cloud_id("local_old") is None


def test_legacy_local_config_discards_private_access_fields(tmp_path):
    config_path = tmp_path / "cloud.json"
    config_path.write_text(
        json.dumps({
            "library_id": "lib_" + "a" * 32,
            "share_id": "RDX-SHARE-" + "b" * 20,
            "private_sync_key": "RDX-SYNC-" + "c" * 24,
            "link_key_hash": "hash",
            "writer_uids": ["owner", "old-writer"],
            "library_name": "Legacy"
        }),
        encoding="utf-8"
    )

    config = CloudConfigService(config_path).load_config()

    assert config == {
        "library_id": "lib_" + "a" * 32,
        "share_id": "RDX-SHARE-" + "b" * 20,
        "library_name": "Legacy"
    }


def test_cloud_upload_is_always_an_exact_owner_snapshot(monkeypatch):
    service = CloudLibraryService.__new__(CloudLibraryService)
    service.auth_service = SimpleNamespace(uid="owner")
    service.export_service = LibraryExportService()
    service.key_service = LibraryKeyService()
    service.get_library = lambda library_id: {
        "library_id": library_id,
        "owner_uid": "owner"
    }
    service._list_library_game_documents = lambda library_id: [
        {"cloud_id": "igdb_1", "fields": {}},
        {"cloud_id": "igdb_99", "fields": {}}
    ]

    uploaded = []
    deleted = []
    summaries = []
    monkeypatch.setattr(
        service,
        "_upsert_game_document",
        lambda library_id, game_id, game_data: uploaded.append(game_id)
    )
    monkeypatch.setattr(
        service,
        "_delete_game_document",
        lambda library_id, game_id: deleted.append(game_id)
    )
    monkeypatch.setattr(
        service,
        "_update_library_summary",
        lambda library_id, game_count: summaries.append(game_count)
    )

    game = SimpleNamespace(
        id=1,
        cloud_id="igdb_1",
        igdb_id=1,
        title="Game",
        summary=None,
        storyline=None,
        cover_url=None,
        release_year=None,
        platform="Nintendo DS",
        status="Saved",
        rom_path=None
    )
    result = service.upload_library_games(
        "lib_" + "a" * 32,
        [game],
        mode=CloudLibraryService.SYNC_MODE_ADDITIVE
    )

    assert uploaded == ["igdb_1"]
    assert deleted == ["igdb_99"]
    assert summaries == [1]
    assert result["mode"] == CloudLibraryService.SYNC_MODE_SNAPSHOT


def test_non_owner_cannot_upload_cloud_snapshot():
    service = CloudLibraryService.__new__(CloudLibraryService)
    service.auth_service = SimpleNamespace(uid="other")
    service.key_service = LibraryKeyService()
    service.get_library = lambda library_id: {
        "library_id": library_id,
        "owner_uid": "owner"
    }

    with pytest.raises(CloudLibraryError):
        service.upload_library_games("lib_" + "a" * 32, [])


def test_new_library_contains_no_private_or_link_access_fields(monkeypatch):
    service = CloudLibraryService.__new__(CloudLibraryService)
    service.auth_service = SimpleNamespace(
        uid="owner",
        get_valid_id_token=lambda: "token",
        get_auth_headers=lambda: {"Authorization": "Bearer token"}
    )
    service.key_service = LibraryKeyService()
    service.documents_url = "https://example.test/documents"
    captured = {}

    class Response:
        ok = True
        status_code = 200

    def fake_post(url, **kwargs):
        captured.update(kwargs["json"])
        return Response()

    monkeypatch.setattr(cloud_service_module.requests, "post", fake_post)
    library = service.create_library("Test Library")
    uploaded = service._decode_fields(captured["fields"])

    assert library["share_id"].startswith("RDX-SHARE-")
    assert "private_sync_key" not in uploaded
    assert "link_key_hash" not in uploaded
    assert "writer_uids" not in uploaded


def test_existing_library_keeps_share_key_during_legacy_cleanup(
    monkeypatch,
    tmp_path
):
    config_service = CloudConfigService(tmp_path / "cloud.json")
    share_key = "RDX-SHARE-" + "b" * 20
    library_id = "lib_" + "a" * 32
    config_service.save_config(
        library_id=library_id,
        share_id=share_key,
        private_sync_key="RDX-SYNC-" + "c" * 24,
        library_name="Existing"
    )

    service = CloudLibraryService.__new__(CloudLibraryService)
    service.config_service = config_service
    service.auth_service = SimpleNamespace(uid="owner")
    service.key_service = LibraryKeyService()
    legacy_library = {
        "library_id": library_id,
        "owner_uid": "owner",
        "share_id": share_key,
        "private_sync_key": "legacy",
        "link_key_hash": "hash",
        "writer_uids": ["owner", "writer"],
        "name": "Existing"
    }
    service.get_library = lambda requested_id: legacy_library
    cleaned = []
    monkeypatch.setattr(
        service,
        "_remove_legacy_access_fields",
        lambda library: cleaned.append(library)
    )
    monkeypatch.setattr(
        service,
        "upload_library_games",
        lambda **values: {
            "uploaded_count": 1,
            "deleted_count": 0,
            "retained_count": 0,
            "duplicate_count": 0,
            "cloud_game_count": 1,
            "mode": CloudLibraryService.SYNC_MODE_SNAPSHOT
        }
    )

    result = service.sync_library(games=[])
    saved_config = config_service.load_config()

    assert result["share_id"] == share_key
    assert saved_config["share_id"] == share_key
    assert set(saved_config) == {"library_id", "share_id", "library_name"}
    assert cleaned == [legacy_library]


def test_share_key_download_uses_server_function(monkeypatch):
    share_key = "RDX-SHARE-" + "s" * 20
    auth_service = SimpleNamespace(
        get_auth_headers=lambda: {"Authorization": "Bearer token"}
    )
    service = LibraryShareService(
        auth_service=auth_service,
        share_function_url="https://example.test/read_shared_library"
    )
    captured = {}

    class Response:
        ok = True
        status_code = 200

        @staticmethod
        def json():
            return {
                "library": {
                    "library_id": "lib_" + "a" * 32,
                    "share_id": share_key,
                    "name": "Friend"
                },
                "games": [_cloud_game("igdb_1", "Game", igdb_id=1)]
            }

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return Response()

    monkeypatch.setattr(share_service_module.requests, "post", fake_post)
    result = service.download_shared_library(share_key)

    assert captured["url"].endswith("read_shared_library")
    assert captured["json"] == {"share_key": share_key}
    assert result["library"]["name"] == "Friend"
    assert result["games"][0]["cloud_id"] == "igdb_1"
