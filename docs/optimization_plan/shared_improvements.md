# Shared Improvements

These improvements apply to the codebase as a whole and aim to reduce duplication and improve robustness across all three collectors.

## 1. Common Shell Library (`lib/dma_common.sh`)

Create a shared shell script that can be sourced by all `collect-data.sh` scripts. This library should contain:

### A. Platform Abstraction
Move the OS detection and command aliasing logic here.

```bash
# Example function signature
detect_os() {
    # Sets global variables: OS_TYPE, GREP_CMD, SED_CMD, AWK_CMD, MD5_CMD
}
```

**Current State**: Each script repeats logic to check for `SunOS`, `AIX`, `HP-UX`, `MSYS` (Windows), etc., and sets `GREP`, `SED` accordingly.
**Improvement**: Centralize this. If a bug is found in Solaris `grep` detection, fixing it in one place fixes it for all.

### B. Logging Standard
Implement consistent logging functions.

```bash
log_info() { echo "[INFO] $(date +'%Y-%m-%d %H:%M:%S') - $1"; }
log_warn() { echo "[WARN] $(date +'%Y-%m-%d %H:%M:%S') - $1" >&2; }
log_error() { echo "[ERROR] $(date +'%Y-%m-%d %H:%M:%S') - $1" >&2; }
```

**Current State**: Mixed usage of `echo`, `writeLog` (in `db-machine-specs.sh`), and raw output.
**Improvement**: Standardized logs make parsing and debugging easier for users and automated tools.

### C. Output Sanitization
The logic to clean up CSV delimiters and headers is nearly identical.

```bash
clean_csv_output() {
    local file_path=$1
    # Centralized sed logic for removing extra pipes, whitespace, etc.
}
```

### D. Compression Wrapper
Centralize the "Zip vs Gzip vs Tar" logic.

```bash
compress_files() {
    local output_name=$1
    local file_list=$2
    # Logic to select zip or tar.gz and perform the action
}
```

## 2. Unified Machine Specifications Script

Currently, `db-machine-specs.sh` exists in both `mysql` and `postgres` directories (and potentially logically in Oracle).

**Action**: Move `db-machine-specs.sh` to a common location (e.g., `scripts/collector/common/`) or the root `scripts/` folder if appropriate, and have all collectors reference it.
**Improvement**: Ensures consistent hardware data collection regardless of the database engine.

## 3. Dependency Checking (Pre-flight)

The `dma_precheck.sh` script in Oracle is excellent.
**Action**: Generalize `dma_precheck.sh` into a shared tool that can optionally check for specific DB client tools (`sqlplus`, `psql`, `mysql`) based on arguments.
**Benefit**: Allows users to verify their environment for *any* collector before running.

## 4. Argument Parsing Standardization

While flags must stay the same, the *implementation* of parsing can be standardized.
**Current**: `while` loops with `shift`.
**Improvement**: Ensure all scripts handle:
*   quoted arguments correctly.
*   unknown arguments gracefully (print usage and exit).
*   missing required arguments with clear error messages.

## 5. Security & Best Practices

*   **Password Handling**: Ensure passwords passed via CLI are not logged or exposed in `ps -ef` where possible (hard with shell, but we can minimize the window). The Postgres script already uses `PGPASSWORD` env var, which is better than CLI args. Ensure MySQL and Oracle scripts use environment variables or config files where possible for the actual tool invocation to hide secrets.
*   **Temporary Files**: Ensure `tmp` directories are cleaned up on `EXIT` (using `trap`).
