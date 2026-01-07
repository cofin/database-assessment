# Changelog - Optimization Plan

## [Unreleased]

### Shared Library (Phase 1)
- Created `scripts/collector/lib/dma_common.sh`.
- **Extracted Logic**:
    - `dma_detect_os`: Consolidated OS detection logic (Solaris, AIX, HP-UX) derived from `scripts/collector/oracle/collect-data.sh`.
    - `dma_log_*`: Standardized logging functions.
    - `dma_clean_csv`: Consolidated CSV cleaning logic. Includes specific handling for:
        - **MySQL**: Removing decorative pipes and separators.
        - **Postgres**: Uppercasing headers (Linux/Darwin only).
        - **Oracle**: Whitespace trimming.
        - **Platform Specifics**: Preserved legacy `sed` logic for SunOS, AIX, and HP-UX.

### Machine Specifications
- **Consolidated**: Moved `scripts/collector/mysql/db-machine-specs.sh` to `scripts/collector/common/db-machine-specs.sh`.
- **Removed**: Deleted duplicate `scripts/collector/postgres/db-machine-specs.sh`.

### Integration & Build System
- **MySQL**: `collect-data.sh` updated to source `dma_common.sh` and use `dma_clean_csv` and consolidated `db-machine-specs.sh`.
- **Postgres**: `collect-data.sh` updated to source `dma_common.sh` and use `dma_clean_csv` and consolidated `db-machine-specs.sh`.
- **Oracle**: `collect-data.sh` updated to source `dma_common.sh` and use `dma_clean_csv`.
- **Makefile**: Updated `build-collector` target to package `lib/` and `common/` directories.