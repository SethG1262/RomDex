# -u causes the script to stop when an undefined variable is used.
# This helps detect typing mistakes in variable names.
set -u


# ------------------------------------------------------------
# Locate the RomDex project
# ------------------------------------------------------------

# BASH_SOURCE[0] stores the path of this script.
# dirname gets the folder containing the script.
# cd and pwd convert the location to an absolute path.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# The script is expected to be stored in RomDex/scripts.
# Moving one folder up gives the RomDex project root.
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"


# ------------------------------------------------------------
# Create the report path
# ------------------------------------------------------------

# Health-check reports will be saved in RomDex/reports.
REPORT_DIR="$PROJECT_ROOT/reports"

# date creates a timestamp such as 20260713_060500.
# The timestamp prevents reports from overwriting each other.
TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"

# Build the full report filename.
REPORT_FILE="$REPORT_DIR/romdex_health_check_$TIMESTAMP.txt"

# Counters used in the final summary.
PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

# mkdir -p creates the reports folder when it does not exist.
# -p prevents an error if the folder already exists.
mkdir -p "$REPORT_DIR"


# ------------------------------------------------------------
# Reusable output functions
# ------------------------------------------------------------

# log prints text to the terminal and writes it to the report.
#
# The pipe | sends printf output into tee.
# tee displays the text and appends it to the report file.
log() {
    printf '%s\n' "$1" | tee -a "$REPORT_FILE"
}

# pass increases the passed-check counter and records the result.
pass() {
    PASS_COUNT=$((PASS_COUNT + 1))
    log "[PASS] $1"
}

# warn increases the warning counter and records the result.
warn() {
    WARN_COUNT=$((WARN_COUNT + 1))
    log "[WARN] $1"
}

# fail increases the failed-check counter and records the result.
fail() {
    FAIL_COUNT=$((FAIL_COUNT + 1))
    log "[FAIL] $1"
}


# ------------------------------------------------------------
# Find an available Python command
# ------------------------------------------------------------

# command -v checks whether a command exists.
#
# Windows may use python or py.
# Linux/macOS may use python3.
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


# ------------------------------------------------------------
# Check required folders and files
# ------------------------------------------------------------

check_project_structure() {
    log ""
    log "Project Structure"
    log "-----------------"

    # Bash arrays store the expected project folders and files.
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

    # Loop through each required directory.
    for directory in "${REQUIRED_DIRECTORIES[@]}"; do

        # -d checks whether the path exists and is a directory.
        if [[ -d "$PROJECT_ROOT/$directory" ]]; then
            pass "Directory exists: $directory/"
        else
            fail "Missing directory: $directory/"
        fi
    done

    # Loop through each required file.
    for file in "${REQUIRED_FILES[@]}"; do

        # -f checks whether the path exists and is a regular file.
        if [[ -f "$PROJECT_ROOT/$file" ]]; then
            pass "File exists: $file"
        else
            fail "Missing file: $file"
        fi
    done
}


# ------------------------------------------------------------
# Check Python and required modules
# ------------------------------------------------------------

check_python() {
    log ""
    log "Python Environment"
    log "------------------"

    # Run the helper function that chooses a Python command.
    find_python

    # -z checks whether a string is empty.
    if [[ -z "$PYTHON_CMD" ]]; then
        fail "Python was not found."
        return
    fi

    # Command substitution $(...) stores command output in a variable.
    VERSION="$("$PYTHON_CMD" --version 2>&1)"
    pass "Python found: $VERSION"

    # These modules are used by RomDex.
    REQUIRED_MODULES=(
        "sqlalchemy"
        "requests"
        "dotenv"
        "PIL"
    )

    # Loop through each Python module.
    for module in "${REQUIRED_MODULES[@]}"; do

        # python -c runs a short Python statement.
        # Importing the module confirms that it is installed.
        #
        # >/dev/null hides normal output.
        # 2>&1 also hides error output.
        if "$PYTHON_CMD" -c "import $module" >/dev/null 2>&1; then
            pass "Python module available: $module"
        else
            warn "Python module missing: $module"
        fi
    done
}


# ------------------------------------------------------------
# Check .gitignore protection
# ------------------------------------------------------------

check_gitignore() {
    log ""
    log "Git Ignore Protection"
    log "---------------------"

    GITIGNORE_FILE="$PROJECT_ROOT/.gitignore"

    # Stop this section if .gitignore does not exist.
    if [[ ! -f "$GITIGNORE_FILE" ]]; then
        fail ".gitignore was not found."
        return
    fi

    # These files contain secrets, databases, authentication
    # sessions, or local computer settings.
    PROTECTED_PATTERNS=(
        ".env"
        "romdex.db"
        "firebase_auth_session.json"
        "cloud_library_config.json"
        "emulator_config.json"
    )

    # Loop through every protected file pattern.
    for pattern in "${PROTECTED_PATTERNS[@]}"; do

        # grep searches the .gitignore file for the exact pattern.
        #
        # -F treats the search as plain text.
        # -q enables quiet mode and returns only success or failure.
        if grep -Fq "$pattern" "$GITIGNORE_FILE"; then
            pass ".gitignore contains: $pattern"
        else
            warn ".gitignore may be missing: $pattern"
        fi
    done
}


# ------------------------------------------------------------
# Collect source-code statistics
# ------------------------------------------------------------

show_source_statistics() {
    log ""
    log "Source Statistics"
    log "-----------------"

    # find searches the project for Python files.
    #
    # -type f keeps only files.
    # -name "*.py" keeps files ending in .py.
    # ! -path excludes Git, virtual environments, and caches.
    #
    # The pipe sends the result to wc -l, which counts lines.
    # tr -d ' ' removes spaces from the count.
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

    # grep searches all Python files for class definitions.
    #
    # -R searches folders recursively.
    # -h hides filenames.
    # -s hides missing-file errors.
    # -E enables extended regular expressions.
    # --include keeps only Python files.
    # --exclude-dir skips Git, virtual environments, and caches.
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

    # This grep filter counts function and method definitions.
    #
    # The expression matches both:
    # def function_name(...)
    # async def function_name(...)
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

    # Count Python test files whose names begin with test_.
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


# ------------------------------------------------------------
# Validate Python syntax
# ------------------------------------------------------------

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

    # find -print0 separates file paths with a null character.
    # This allows file paths containing spaces to be handled safely.
    #
    # The while loop reads one Python file at a time.
    while IFS= read -r -d '' file; do

        # py_compile checks Python syntax without running the application.
        if "$PYTHON_CMD" -m py_compile "$file" >/dev/null 2>&1; then

            # ${file#$PROJECT_ROOT/} removes the project-root part
            # so the report displays a shorter relative path.
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

    # Report success when no syntax errors were counted.
    if [[ "$SYNTAX_ERRORS" -eq 0 ]]; then
        log "All Python files passed syntax validation."
    fi
}


# ------------------------------------------------------------
# Print the final summary
# ------------------------------------------------------------

print_summary() {
    log ""
    log "Health Check Summary"
    log "--------------------"
    log "Passed: $PASS_COUNT"
    log "Warnings: $WARN_COUNT"
    log "Failed: $FAIL_COUNT"
    log "Report saved to:"
    log "$REPORT_FILE"

    # A failed check gives the script exit code 1.
    if [[ "$FAIL_COUNT" -gt 0 ]]; then
        log ""
        log "RomDex has one or more issues that should be reviewed."
        exit 1
    fi

    # Exit code 0 indicates success.
    log ""
    log "RomDex passed the required health checks."
    exit 0
}


# ------------------------------------------------------------
# Main script execution
# ------------------------------------------------------------

log "RomDex Project Health Check"
log "Project root: $PROJECT_ROOT"
log "Date: $(date)"

# Call each major section in order.
check_project_structure
check_python
check_gitignore
show_source_statistics
check_python_syntax
print_summary