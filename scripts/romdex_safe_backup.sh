#!/usr/bin/env bash

# RomDex Safe Source Backup
# Run from the RomDex project root with:
# bash scripts/romdex_safe_backup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_PARENT="$(dirname "$PROJECT_ROOT")"
PROJECT_NAME="$(basename "$PROJECT_ROOT")"

BACKUP_DIR="$PROJECT_ROOT/backups"
TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"
ARCHIVE_NAME="${PROJECT_NAME}_source_${TIMESTAMP}.tar.gz"
ARCHIVE_PATH="$BACKUP_DIR/$ARCHIVE_NAME"
MANIFEST_NAME="${PROJECT_NAME}_source_${TIMESTAMP}_manifest.txt"
MANIFEST_PATH="$BACKUP_DIR/$MANIFEST_NAME"

mkdir -p "$BACKUP_DIR"

EXCLUDED_PATTERNS=(
    ".git"
    ".github"
    ".venv"
    "venv"
    "__pycache__"
    "*.pyc"
    "*.pyo"
    ".env"
    ".env.*"
    "data/romdex.db"
    "data/*.db"
    "data/firebase_auth_session.json"
    "data/cloud_library_config.json"
    "data/emulator_config.json"
    "*.nds"
    "*.3ds"
    "*.cci"
    "*.cxi"
    "*.sav"
    "*.dsv"
    "backups"
    "reports"
)

TAR_EXCLUDES=()

for pattern in "${EXCLUDED_PATTERNS[@]}"; do
    TAR_EXCLUDES+=("--exclude=$pattern")
done

printf 'RomDex Safe Source Backup\n'
printf '=========================\n'
printf 'Project root: %s\n' "$PROJECT_ROOT"
printf 'Archive: %s\n\n' "$ARCHIVE_PATH"

if ! command -v tar >/dev/null 2>&1; then
    printf 'ERROR: tar was not found. Run this script in Git Bash.\n' >&2
    exit 1
fi

tar \
    -czf "$ARCHIVE_PATH" \
    "${TAR_EXCLUDES[@]}" \
    -C "$PROJECT_PARENT" \
    "$PROJECT_NAME"

tar -tzf "$ARCHIVE_PATH" |
    sort |
    tee "$MANIFEST_PATH" >/dev/null

PROTECTED_PATTERN='(^|/)\.env($|\.)|romdex\.db$|firebase_auth_session\.json$|cloud_library_config\.json$|emulator_config\.json$|\.(nds|3ds|cci|cxi|sav|dsv)$'

if grep -Eiq "$PROTECTED_PATTERN" "$MANIFEST_PATH"; then
    printf 'ERROR: A protected file was found in the backup.\n' >&2
    printf 'The archive and manifest were removed.\n' >&2

    rm -f "$ARCHIVE_PATH" "$MANIFEST_PATH"
    exit 1
fi

FILE_COUNT="$(
    grep -Ev '/$' "$MANIFEST_PATH" |
    wc -l |
    tr -d ' '
)"

PYTHON_FILE_COUNT="$(
    grep -E '\.py$' "$MANIFEST_PATH" |
    wc -l |
    tr -d ' '
)"

ARCHIVE_SIZE="$(
    du -h "$ARCHIVE_PATH" |
    awk '{print $1}'
)"

printf 'Backup completed successfully.\n'
printf 'Files included: %s\n' "$FILE_COUNT"
printf 'Python files included: %s\n' "$PYTHON_FILE_COUNT"
printf 'Archive size: %s\n' "$ARCHIVE_SIZE"
printf 'Archive saved to:\n%s\n' "$ARCHIVE_PATH"
printf 'Manifest saved to:\n%s\n' "$MANIFEST_PATH"
printf '\nProtected secrets, databases, ROMs, saves, and runtime files were excluded.\n'
