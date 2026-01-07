# Changelog - Optimization Plan

## [Unreleased]

### Shared Library (Phase 1)
- Created `scripts/collector/lib/dma_common.sh`.
- **Extracted Logic**:
    - `dma_detect_os`: Consolidated OS detection logic (Solaris, AIX, HP-UX) derived from `scripts/collector/oracle/collect-data.sh`.
    - `dma_log_*`: Standardized logging functions.
    - `dma_clean_csv`: Added but **not yet integrated** due to regex differences between engines.

### Machine Specifications
- **Consolidated**: Moved `scripts/collector/mysql/db-machine-specs.sh` to `scripts/collector/common/db-machine-specs.sh`.
- **Removed**: Deleted duplicate `scripts/collector/postgres/db-machine-specs.sh`.

### Integration & Build System
- **MySQL**: `collect-data.sh` updated to source `dma_common.sh` via local (`./lib/`) or dev (`../lib/`) paths.
- **Postgres**: `collect-data.sh` updated to source `dma_common.sh` via local (`./lib/`) or dev (`../lib/`) paths.
- **Oracle**: `collect-data.sh` updated to source `dma_common.sh` via local (`./lib/`) or dev (`../lib/`) paths.
- **Makefile**: Updated `build-collector` target to:
    - Create `lib/` and `common/` directories inside the build artifact for each database engine (MySQL, Postgres, Oracle).
    - Copy `dma_common.sh` and `db-machine-specs.sh` into these local directories.
    - This ensures that the packaged zip files contain all dependencies and the relative paths in `collect-data.sh` resolve correctly when run by the end user.
