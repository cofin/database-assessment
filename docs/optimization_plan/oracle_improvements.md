# Oracle Collector Improvements

**Scope**: Strictly limited to Shell Script (`.sh`) refactoring, output parsing, and script structure optimization.
**Constraint**: Do NOT modify any `sql/` files or change the data collection logic/output format.

## 1. Modularization

**Current**: `collect-data.sh` is huge and complex, mixing OEE logic, SQL*Plus interaction, and output processing.
**Improvement**:
*   Break `collect-data.sh` into smaller source-able chunks (e.g., `lib/oracle_conn.sh`, `lib/oracle_oee.sh`).
*   The `dma_oee.sh` file already exists; move more logic there if it relates to OEE.

## 2. SQL*Plus Interaction

**Current**:
```bash
${sqlplus_cmd} -s /nolog << EOF
...
EOF
```
**Improvement**:
*   This is standard. Ensure `WHENEVER SQLERROR EXIT FAILURE` is used consistently in *all* wrapper SQL scripts (`dma_collect.sql` etc).
*   Output parsing for `DMAFILETAG` is robust but relies on specific formatting. Ensure `set markup html off` and other formatting options don't interfere (scripts seem to handle this).

## 3. OEE Integration

**Current**: Logic for `oee_check_conditions` and `oee_run`.
**Improvement**:
*   Ensure OEE failures don't block DMA (SQL) collection unless necessary.
*   The `dma_batch_run.sh` script handles OEE and DMA in parallel. Verify that resource contention (temp space) is managed if `maxParallel` is high.

## 4. `dma_batch_run.sh`

**Current**: Reads a CSV and background processes `collect-data.sh`.
**Improvement**:
*   Use a proper job control loop or `xargs -P` if possible (portability concern).
*   The current `while` loop with `count_children` is a classic shell pattern. Ensure it handles PIDs correctly if a child crashes hard (zombies). `wait` is used at the end, which is good.

## 5. Platform Overrides (Solaris/AIX)

**Current**: Lots of checks for `awk`, `sed`, `grep` locations.
**Action**: Move ALL of this to `lib/dma_common.sh`. The Oracle script has the most comprehensive checks; these should be the "gold standard" used by MySQL and Postgres collectors too.

## 6. Prechecks

**Current**: `dma_precheck.sh` is robust.
**Improvement**:
*   Add a check for disk space in `OUTPUT_DIR` before starting large collections (especially AWR dumps).
*   Add a check for `write` permissions in `tmp` and `log` dirs.
