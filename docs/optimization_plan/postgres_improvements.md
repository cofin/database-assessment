# Postgres Collector Improvements

## 1. Recursive Collection (`--allDbs`)

**Current Logic**:
The script calls itself recursively:
```bash
./collect-data.sh ... --allDbs N
```
**Optimization**:
*   While functional, this spawns new shells. Ensure that `trap` handlers in the parent don't conflict with children.
*   Ensure that failures in one DB collection don't abort the entire loop if one DB is inaccessible.
*   **Parallelism**: Consider adding a `--maxParallel` flag (similar to Oracle) to collect from multiple DBs in parallel using `xargs` or background jobs `&`, speeding up instance-wide collection.

## 2. Password Security

**Current**: Sets `export PGPASSWORD="${pass}"`.
**Improvement**: This is generally safe from `ps`, but using a `.pgpass` file (generated temporarily and secured with `chmod 0600`) is the canonical "most secure" method if the environment allows file creation. Stick to `PGPASSWORD` if file creation is risky, but ensure it's unset immediately after use.

## 3. Version Specific SQL

**Constraint**: Do NOT modify existing SQL files.

**Current**: Logic selects `sql/11`, `sql/12`, etc.
**Improvement**:
*   The fallback logic to `base` is good.
*   Verify if `base` covers Postgres 14, 15, 16 adequately.
*   Consider a directory structure like `sql/common` and `sql/overrides/{version}` to minimize duplication of SQL files between versions if they are identical. **Implementation Note**: This file reorganization is only permitted if it does not change the query text or output. If unsure, leave as is to respect the "SQL Immutability" rule.

## 4. Error Parsing

**Current**:
```bash
$GREP -i -E 'ERROR:' ...
```
**Improvement**:
*   `psql` returns exit codes.
    *   0: Success
    *   1: Fatal error
    *   2: Connection error
    *   3: Script error
*   Use these codes! If `psql` returns 2, stop immediately. If 3, maybe continue but log. Relying solely on grep is fragile if the error message language/locale changes (though `LANG=C` is set, which is good).

## 5. Machine Specs

**Current**: Duplicates `db-machine-specs.sh`.
**Action**: Delete the duplicate and symlink or reference the shared script.
