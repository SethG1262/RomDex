#!/usr/bin/env bash

# ============================================================
# RomDex Safe Source Backup
# ============================================================
# Purpose:
# Creates a compressed backup of the RomDex source code while
# excluding secrets, databases, ROMs, save files, caches, and
# other device-specific runtime files.
#
# Run from the RomDex project root with:
# bash scripts/romdex_safe_backup.sh
# ============================================================


# Exit immediately when:
# - a command fails (-e)
# - an undefined variable is used (-u)
# - any command inside a pipe fails (pipefail)
set -euo pipefail


# ------------------------------------------------------------
# Locate the RomDex project
# ------------------------------------------------------------

# BASH_SOURCE[0] is the path of this script.
# dirname gets the folder containing the script.
# cd and pwd convert that location into a full absolute path.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# The script is stored inside RomDex/scripts.
# Moving one folder up gives the RomDex project root.
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Get the folder that contains the RomDex project.
PROJECT_PARENT="$(dirname "$PROJECT_ROOT")"

# Get only the project folder name, such as "RomDex".
PROJECT_NAME="$(basename "$PROJECT_ROOT")"


# ------------------------------------------------------------
# Create backup names and paths
# ------------------------------------------------------------

# All backups will be stored in RomDex/backups.
BACKUP_DIR="$PROJECT_ROOT/backups"

# date creates a timestamp such as 20260713_055900.
# This prevents one backup from overwriting another.
TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"

# Build the compressed archive filename.
ARCHIVE_NAME="${PROJECT_NAME}_source_${TIMESTAMP}.tar.gz"

# Build the full archive path.
ARCHIVE_PATH="$BACKUP_DIR/$ARCHIVE_NAME"

# Build the manifest filename.
# The manifest is a text file listing everything inside the backup.
MANIFEST_NAME="${PROJECT_NAME}_source_${TIMESTAMP}_manifest.txt"

# Build the full manifest path.
MANIFEST_PATH="$BACKUP_DIR/$MANIFEST_NAME"

# Create the backups folder when it does not already exist.
# -p prevents an error when the folder already exists.
mkdir -p "$BACKUP_DIR"


# ------------------------------------------------------------
# Define files and folders that must not enter the backup
# ------------------------------------------------------------

# This Bash array contains exclusion filters.
# Wildcards such as *.nds match every file with that extension.
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

# This second array will hold tar-ready arguments such as:
# --exclude=.env
# --exclude=*.nds
TAR_EXCLUDES=()

# Loop through every exclusion pattern.
# Each pattern is converted into a tar --exclude argument.
for pattern in "${EXCLUDED_PATTERNS[@]}"; do
    TAR_EXCLUDES+=("--exclude=$pattern")
done


# ------------------------------------------------------------
# Display basic information before starting
# ------------------------------------------------------------

# printf prints formatted text to the terminal.
printf 'RomDex Safe Source Backup\n'
printf '=========================\n'
printf 'Project root: %s\n' "$PROJECT_ROOT"
printf 'Archive: %s\n\n' "$ARCHIVE_PATH"


# ------------------------------------------------------------
# Confirm that the tar command is available
# ------------------------------------------------------------

# command -v checks whether a command exists.
# Git Bash normally includes tar.
if ! command -v tar >/dev/null 2>&1; then
    printf 'ERROR: tar was not found. Run this script in Git Bash.\n' >&2
    exit 1
fi


# ------------------------------------------------------------
# Create the compressed source-code backup
# ------------------------------------------------------------

# tar creates the archive.
#
# Options:
# -c = create a new archive
# -z = compress it using gzip
# -f = use the filename that follows
#
# "${TAR_EXCLUDES[@]}" inserts all exclusion filters.
# -C changes to the parent folder before archiving RomDex.
tar \
    -czf "$ARCHIVE_PATH" \
    "${TAR_EXCLUDES[@]}" \
    -C "$PROJECT_PARENT" \
    "$PROJECT_NAME"


# ------------------------------------------------------------
# Create a sorted manifest of the archive contents
# ------------------------------------------------------------

# This is a command pipeline.
#
# tar -tzf lists the contents of the compressed archive.
# | sends that output to sort.
# sort arranges the file names alphabetically.
# | sends the sorted output to tee.
# tee writes the result into the manifest file.
#
# >/dev/null hides duplicate output from the terminal.
tar -tzf "$ARCHIVE_PATH" |
    sort |
    tee "$MANIFEST_PATH" >/dev/null


# ------------------------------------------------------------
# Validate that protected files were not included
# ------------------------------------------------------------

# This regular-expression filter matches protected file names
# and protected ROM/save extensions.
PROTECTED_PATTERN='(^|/)\.env($|\.)|romdex\.db$|firebase_auth_session\.json$|cloud_library_config\.json$|emulator_config\.json$|\.(nds|3ds|cci|cxi|sav|dsv)$'

# grep searches the manifest for protected files.
#
# -E = use extended regular expressions
# -i = ignore uppercase/lowercase differences
# -q = quiet mode; only return success or failure
if grep -Eiq "$PROTECTED_PATTERN" "$MANIFEST_PATH"; then
    printf 'ERROR: A protected file was found in the backup.\n' >&2
    printf 'The archive and manifest were removed.\n' >&2

    # rm -f deletes the unsafe archive and manifest.
    rm -f "$ARCHIVE_PATH" "$MANIFEST_PATH"

    # Exit code 1 indicates failure.
    exit 1
fi


# ------------------------------------------------------------
# Count included files
# ------------------------------------------------------------

# Command substitution $(...) stores command output in a variable.
#
# grep -Ev '/$' removes directory-only lines.
# wc -l counts the remaining lines.
# tr -d ' ' removes spaces from the number.
FILE_COUNT="$(
    grep -Ev '/$' "$MANIFEST_PATH" |
    wc -l |
    tr -d ' '
)"


# ------------------------------------------------------------
# Count included Python files
# ------------------------------------------------------------

# grep -E '\.py$' keeps only lines ending in .py.
# wc -l counts those Python files.
# tr removes extra spaces.
PYTHON_FILE_COUNT="$(
    grep -E '\.py$' "$MANIFEST_PATH" |
    wc -l |
    tr -d ' '
)"


# ------------------------------------------------------------
# Get the final archive size
# ------------------------------------------------------------

# du -h reports the archive size in a human-readable format,
# such as 24K or 3.2M.
#
# awk '{print $1}' keeps only the size column.
ARCHIVE_SIZE="$(
    du -h "$ARCHIVE_PATH" |
    awk '{print $1}'
)"


# ------------------------------------------------------------
# Display the final results
# ------------------------------------------------------------

printf 'Backup completed successfully.\n'
printf 'Files included: %s\n' "$FILE_COUNT"
printf 'Python files included: %s\n' "$PYTHON_FILE_COUNT"
printf 'Archive size: %s\n' "$ARCHIVE_SIZE"
printf 'Archive saved to:\n%s\n' "$ARCHIVE_PATH"
printf 'Manifest saved to:\n%s\n' "$MANIFEST_PATH"
printf '\nProtected secrets, databases, ROMs, saves, and runtime files were excluded.\n'
