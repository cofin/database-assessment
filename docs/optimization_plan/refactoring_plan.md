# Refactoring Plan

This plan outlines the steps to implement the identified improvements.

**Constraint Checklist**:
*   [ ] NO changes to existing SQL files (content or output structure).
*   [ ] New data = New File.
*   [ ] Oracle SQL/Data Logic changes are DEFERRED (Shell/Structure improvements are OK).

## Phase 1: Shared Library & Standardization (Low Risk)

1.  **Create `scripts/collector/lib/`**:
    *   Create `scripts/collector/lib/dma_common.sh`.
2.  **Consolidate Platform Logic**:
    *   Extract `checkPlatform` / `init_variables` logic from `mysql` or `postgres` scripts (Oracle is ignored for now).
    *   Generalize it in `dma_common.sh`.
    *   Update MySQL and Postgres `collect-data.sh` to source this file.
    *   *Verify*: Run on Linux (and cross-check logic for others).
3.  **Consolidate Machine Specs**:
    *   Move `scripts/collector/mysql/db-machine-specs.sh` to `scripts/collector/common/db-machine-specs.sh`.
    *   Update MySQL and Postgres scripts to call this common path.
    *   Remove `scripts/collector/postgres/db-machine-specs.sh`.

## Phase 2: Postgres Improvements (Medium Risk)

1.  **Refactor `collect-data.sh`**:
    *   Source `dma_common.sh`.
    *   Replace `grep ERROR` with checking `psql` exit codes (where applicable).
    *   Update `cleanupOpOutput` to use the shared function.
2.  **Parallelism (Optional)**:
    *   Implement `--maxParallel` for `--allDbs` flag.

## Phase 3: MySQL Improvements (Medium Risk)

1.  **Refactor `collect-data.sh`**:
    *   Source `dma_common.sh`.
    *   Improve the `for f in sql/*.sql` loop logic to be safer.
    *   Use shared compression functions.

## Phase 4: Oracle Shell Refactoring (High Complexity)

**Scope**: Shell scripts only (`collect-data.sh`, `dma_batch_run.sh`).
**Constraint**: No SQL changes.

1.  **Refactor `collect-data.sh`**:
    *   Source `dma_common.sh` to replace the repetitive OS/Platform detection logic (Solaris/AIX/Linux checks).
    *   Standardize logging using the shared library.
    *   Modularize the script by extracting OEE-specific shell logic into `dma_oee.sh` (or a new `lib/oracle_oee.sh`) if not already cleanly separated.
2.  **Refactor `dma_batch_run.sh`**:
    *   Update to use shared logging and potentially shared job control functions if applicable.
3.  **Pre-checks**:
    *   Update `dma_precheck.sh` to use the shared platform detection library to ensure consistency with the main collector.

## Validation Plan

For each phase:
1.  **Linting**: Run `shellcheck` on all `.sh` files.
2.  **Dry Run**: Execute scripts with `--help` to ensure flags parse correctly.
3.  **Functional Test**:
    *   Spin up Docker containers for MySQL 5.7/8.0, Postgres 13/15.
    *   Run collectors against them.
    *   Verify output ZIP content (file list, CSV headers).
    *   **Regression Check**: Compare output CSV structure against "pre-refactor" output to ensure NO columns changed.
