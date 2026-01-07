# DMA Collector Optimization Analysis Summary

## Overview

This document summarizes the findings from a code review of the Google Database Migration Assessment (DMA) collectors for MySQL, PostgreSQL, and Oracle. The goal is to identify opportunities for optimization, debugging improvements, and code consolidation without altering the external CLI interface or breaking existing functionality.

## Key Findings

1. **Code Duplication**: Significant duplication exists across the three collectors, particularly in:
    * OS command detection and platform-specific overrides (Solaris, AIX, HP-UX handling).
    * Output file processing (cleaning up headers/separators using `sed`).
    * Compression and archiving logic.
    * Argument parsing structures.
    * Hardware specification collection (`db-machine-specs.sh` is duplicated).

2. **Error Handling**:
    * Error detection often relies on `grep`-ing output logs for specific strings (`ORA-`, `ERROR:`, `SP2-`) after execution, rather than checking return codes immediately during execution in all cases.
    * Failure states in one step do not always cleanly stop subsequent steps in a graceful manner.

3. **Maintainability**:
    * Monolithic shell scripts (`collect-data.sh`) are becoming large and difficult to maintain.
    * Hardcoded lists of SQL files or version logic embedded within the main script makes adding new database versions/features harder.

4. **Portability**:
    * Platform-specific logic (for `sed`, `grep`, `awk`, `md5sum`) is repeated in every script. This creates a risk of inconsistent behavior across collectors on niche platforms.

## Constraints & Guardrails

* **SQL Immutability**: Absolutely **NO** changes to existing SQL query logic or output schemas (columns/headers) are permitted. Upstream tools rely on exact format matches.
    * Any new data collection must be implemented as a **new** SQL file producing a **new** CSV output file.
* **Oracle Constraints**:
    * **SQL Logic**: No changes to `sql/` files or data collection logic due to pending external updates.
    * **Shell Scripts**: Refactoring of `collect-data.sh`, `dma_batch_run.sh`, `dma_precheck.sh`, and output parsing logic **IS IN SCOPE** to improve maintainability and robustness.
* **Flag Preservation**: All existing CLI flags must remain unchanged.

## Proposed Strategy

The optimization strategy focuses on "refactoring by extraction" to create a shared library of shell functions for all collectors (MySQL, Postgres, and Oracle), keeping the entry point scripts compliant with existing CLI arguments.

### Phases

1. **Phase 1: Standardization & Shared Library**: Create a `lib/` directory for common bash functions (logging, OS detection).
2. **Phase 2: Postgres & MySQL Alignment**: Update Postgres and MySQL collectors to use the shared library and unify `db-machine-specs.sh`.
3. **Phase 3: Enhanced Logging**: Implement standard logging.
4. **Phase 4: Oracle Shell Refactoring**: Refactor Oracle shell scripts to use the shared library and improve modularity (structure, parsing), strictly avoiding SQL logic changes.

## Risk Mitigation

* **Output Compatibility**: The CSV output format and directory structure will be preserved 1:1.
* **Testing**: Changes verified against Linux, with consideration for Solaris/AIX logic which will be moved to shared libraries.
