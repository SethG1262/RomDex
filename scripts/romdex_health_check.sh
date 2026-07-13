#!/usr/bin/env bash

# RomDex Project Health Check
# Run from the RomDex project root with:
# bash scripts/romdex_health_check.sh

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPORT_DIR="$PROJECT_ROOT/reports"
TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"
REPORT_FILE="$REPORT_DIR/romdex_health_check_$TIMESTAMP.txt"

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

mkdir -p "$REPORT_DIR"

log() {
    printf '%s\n' "$1" | tee -a "$REPORT_FILE"
}

pass() {
    PASS_COUNT=$((PASS_COUNT + 1))
    log "[PASS] $1"
}

warn() {
    WARN_COUNT=$((WARN_COUNT + 1))
    log "[WARN] $1"
}

fail() {
    FAIL_COUNT=$((FAIL_COUNT + 1))
    log "[FAIL] $1"
}

find_python() {
    if command -v python >/dev/null 2>&1; then
        PYTHON_CMD="python"
    elif command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD="python3"
    elif command -v py >/dev/null 2>&1; then
        PYTHON_CMD="py"
    else
        PYTHON_CMD=""
    fi
}

check_project_structure() {
    log ""
    log "Project Structure"
    log "-----------------"

    REQUIRED_DIRECTORIES=(
        "models"
        "repositories"
        "services"
        "ui"
    )

    REQUIRED_FILES=(
        "main.py"
        "requirements.txt"
        ".gitignore"
    )

    for directory in "${REQUIRED_DIRECTORIES[@]}"; do
        if [[ -d "$PROJECT_ROOT/$directory" ]]; then
            pass "Directory exists: $directory/"
        else
            fail "Missing directory: $directory/"
        fi
    done

    for file in "${REQUIRED_FILES[@]}"; do
        if [[ -f "$PROJECT_ROOT/$file" ]]; then
            pass "File exists: $file"
        else
            fail "Missing file: $file"
        fi
    done
}

check_python() {
    log ""
    log "Python Environment"
    log "------------------"

    find_python

    if [[ -z "$PYTHON_CMD" ]]; then
        fail "Python was not found."
        return
    fi

    VERSION="$("$PYTHON_CMD" --version 2>&1)"
    pass "Python found: $VERSION"

    REQUIRED_MODULES=(
        "sqlalchemy"
        "requests"
        "dotenv"
        "PIL"
    )

    for module in "${REQUIRED_MODULES[@]}"; do
        if "$PYTHON_CMD" -c "import $module" >/dev/null 2>&1; then
            pass "Python module available: $module"
        else
            warn "Python module missing: $module"
        fi
    done
}

check_gitignore() {
    log ""
    log "Git Ignore Protection"
    log "---------------------"

    GITIGNORE_FILE="$PROJECT_ROOT/.gitignore"

    if [[ ! -f "$GITIGNORE_FILE" ]]; then
        fail ".gitignore was not found."
        return
    fi

    PROTECTED_PATTERNS=(
        ".env"
        "romdex.db"
        "firebase_auth_session.json"
        "cloud_library_config.json"
        "emulator_config.json"
    )

    for pattern in "${PROTECTED_PATTERNS[@]}"; do
        if grep -Fq "$pattern" "$GITIGNORE_FILE"; then
            pass ".gitignore contains: $pattern"
        else
            warn ".gitignore may be missing: $pattern"
        fi
    done
}

show_source_statistics() {
    log ""
    log "Source Statistics"
    log "-----------------"

    PYTHON_FILE_COUNT="$(
        find "$PROJECT_ROOT" \
            -type f \
            -name "*.py" \
            ! -path "*/.git/*" \
            ! -path "*/.venv/*" \
            ! -path "*/venv/*" \
            ! -path "*/__pycache__/*" |
        wc -l |
        tr -d ' '
    )"

    CLASS_COUNT="$(
        grep -RhsE \
            --include="*.py" \
            --exclude-dir=".git" \
            --exclude-dir=".venv" \
            --exclude-dir="venv" \
            --exclude-dir="__pycache__" \
            '^[[:space:]]*class[[:space:]]+' \
            "$PROJECT_ROOT" |
        wc -l |
        tr -d ' '
    )"

    FUNCTION_COUNT="$(
        grep -RhsE \
            --include="*.py" \
            --exclude-dir=".git" \
            --exclude-dir=".venv" \
            --exclude-dir="venv" \
            --exclude-dir="__pycache__" \
            '^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+' \
            "$PROJECT_ROOT" |
        wc -l |
        tr -d ' '
    )"

    TEST_FILE_COUNT="$(
        find "$PROJECT_ROOT" \
            -type f \
            -name "test_*.py" \
            ! -path "*/.git/*" |
        wc -l |
        tr -d ' '
    )"

    log "Python files: $PYTHON_FILE_COUNT"
    log "Class definitions: $CLASS_COUNT"
    log "Function or method definitions: $FUNCTION_COUNT"
    log "Test files: $TEST_FILE_COUNT"
}

check_python_syntax() {
    log ""
    log "Python Syntax Check"
    log "-------------------"

    find_python

    if [[ -z "$PYTHON_CMD" ]]; then
        fail "Syntax check skipped because Python was not found."
        return
    fi

    SYNTAX_ERRORS=0

    while IFS= read -r -d '' file; do
        if "$PYTHON_CMD" -m py_compile "$file" >/dev/null 2>&1; then
            pass "Syntax valid: ${file#$PROJECT_ROOT/}"
        else
            fail "Syntax error: ${file#$PROJECT_ROOT/}"
            SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
        fi
    done < <(
        find "$PROJECT_ROOT" \
            -type f \
            -name "*.py" \
            ! -path "*/.git/*" \
            ! -path "*/.venv/*" \
            ! -path "*/venv/*" \
            ! -path "*/__pycache__/*" \
            -print0
    )

    if [[ "$SYNTAX_ERRORS" -eq 0 ]]; then
        log "All Python files passed syntax validation."
    fi
}

print_summary() {
    log ""
    log "Health Check Summary"
    log "--------------------"
    log "Passed: $PASS_COUNT"
    log "Warnings: $WARN_COUNT"
    log "Failed: $FAIL_COUNT"
    log "Report saved to:"
    log "$REPORT_FILE"

    if [[ "$FAIL_COUNT" -gt 0 ]]; then
        log ""
        log "RomDex has one or more issues that should be reviewed."
        exit 1
    fi

    log ""
    log "RomDex passed the required health checks."
    exit 0
}

log "RomDex Project Health Check"
log "Project root: $PROJECT_ROOT"
log "Date: $(date)"

check_project_structure
check_python
check_gitignore
show_source_statistics
check_python_syntax
print_summary
