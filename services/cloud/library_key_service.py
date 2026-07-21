import re
import secrets
import uuid


class LibraryKeyService:
    """
    Generates and validates RomDex library identifiers and access keys.
    """

    LIBRARY_ID_PATTERN = re.compile(r"^lib_[0-9a-f]{32}$")
    SHARE_KEY_PATTERN = re.compile(r"^RDX-SHARE-[A-Za-z0-9_-]{20,}$")

    def generate_library_id(self):
        return f"lib_{uuid.uuid4().hex}"

    def generate_share_key(self):
        return f"RDX-SHARE-{secrets.token_urlsafe(18)}"

    def is_valid_library_id(self, library_id):
        return (
            isinstance(library_id, str)
            and bool(self.LIBRARY_ID_PATTERN.fullmatch(library_id.strip()))
        )

    def is_valid_share_key(self, share_key):
        return (
            isinstance(share_key, str)
            and bool(self.SHARE_KEY_PATTERN.fullmatch(share_key.strip()))
        )
