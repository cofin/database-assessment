# Changelog - Optimization Plan

## [Unreleased]

### Shared Library (Phase 1)
- Created `scripts/collector/lib/dma_common.sh`.
- **Extracted Logic**:
    - `dma_detect_os`: Consolidated OS detection logic.
    - `dma_log_*`: Standardized logging.
    - `dma_clean_csv`: Consolidated CSV cleaning logic with DB-specific regex and platform overrides.
    - `dma_archive_files`: Standardized compression logic (Zip vs Tar/Gzip).

### Machine Specifications
- **Consolidated**: Moved `scripts/collector/mysql/db-machine-specs.sh` to `scripts/collector/common/db-machine-specs.sh`.
- **Removed**: Deleted duplicate `scripts/collector/postgres/db-machine-specs.sh`.

### Integration & Build System
- **MySQL**: `collect-data.sh` uses `dma_clean_csv`, `dma_archive_files`, and consolidated `db-machine-specs.sh`.
- **Postgres**: `collect-data.sh` uses `dma_clean_csv`, `dma_archive_files`, and consolidated `db-machine-specs.sh`.
- **Oracle**: `collect-data.sh` uses `dma_clean_csv` and `dma_archive_files`.
- **Makefile**: Updated `build-collector` target to package `lib/` and `common/` directories.

### Naming Conventions
- Renamed shell functions to `snake_case` across all modified scripts (`mysql/collect-data.sh`, `postgres/collect-data.sh`, `oracle/dma_precheck.sh`, `oracle/dma_batch_run.sh`) for consistency.