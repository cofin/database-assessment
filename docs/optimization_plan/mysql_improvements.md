# MySQL Collector Improvements

## 1. Error Handling & Connection Validation

**Current Issue**: The `checkVersionMysql` function captures output but error handling relies on checking `$retcd` and string parsing.
**Improvement**:
*   Explicitly check for the presence of the `mysql` binary before attempting connection (already partially done, but can be robustified).
*   Use `mysqladmin ping` for a lighter-weight connectivity check if possible before running queries.

## 2. SQL Execution Loop

**Current Logic**:
```bash
for f in $(ls -1 sql/*.sql ...)
```
**Improvement**:
*   Avoid parsing `ls` output. Use `for f in sql/*.sql` directly to handle filenames with spaces (unlikely here, but good practice).
*   Structure the loop to allow for "critical" vs "optional" scripts. If a critical script fails, abort; if optional, log warning and continue.

## 3. Version Detection

**Current**: Uses `SELECT version();` and parses with `cut`.
**Improvement**:
*   Make the version parsing regex more robust to handle MariaDB variations or custom builds suffixing.
*   Ensure `dbmajor` extraction handles versions like `8.0.30` vs `5.7` correctly (logic seems to exist but verifying against edge cases is good).

## 4. Output Processing

**Current**:
```bash
sed -r 's/[[:space:]]+\|/\|/g;...'
```
**Improvement**:
*   Move this to the shared library (`clean_csv_output`).
*   Ensure the `sed` command doesn't inadvertently strip valid whitespace *inside* data columns if the delimiter logic isn't strict enough. (MySQL output formatting usually adds padding).

## 5. Metadata Collection (Additions Only)

**Constraint**: Do not modify existing `sql/*.sql` files.

**Improvement**:
*   Verify if `performance_schema` is enabled/accessible.
*   If enabled, allow for *new* optional SQL scripts to collect basic performance metrics (similar to AWR/ASH in Oracle, but for MySQL).
*   **Crucial**: These must be *new* `.sql` files generating *new* `.csv` output files. Existing files (e.g., `config.sql`, `database_details.sql`) must remain untouched to preserve upstream compatibility.
*   Add a check for `innodb_stats_on_metadata` (for older versions) to warn if metadata collection might be slow (log warning only).
