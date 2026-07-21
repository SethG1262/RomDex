"""Public Firebase settings that are safe to bundle with the desktop app."""

import os


DEFAULT_FIREBASE_PROJECT_ID = "romdex-d6b1b"

# Firebase client API keys identify a Firebase project; they are not server
# credentials. Access is still enforced by Firebase Auth and Security Rules.
DEFAULT_FIREBASE_API_KEY = "AIzaSyCxggIZZ6Tmj701ca3BpfknEt4RytUHEZM"


def get_firebase_project_id():
    return (
        os.getenv("FIREBASE_PROJECT_ID", "").strip()
        or DEFAULT_FIREBASE_PROJECT_ID
    )


def get_firebase_api_key():
    return (
        os.getenv("FIREBASE_API_KEY", "").strip()
        or DEFAULT_FIREBASE_API_KEY
    )


def get_igdb_proxy_url():
    override = os.getenv("ROMDEX_IGDB_PROXY_URL", "").strip()
    if override:
        return override.rstrip("/")

    project_id = get_firebase_project_id()
    return (
        f"https://us-central1-{project_id}.cloudfunctions.net/igdb_proxy"
    )
