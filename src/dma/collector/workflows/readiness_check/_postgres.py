from __future__ import annotations

from typing import TYPE_CHECKING

import duckdb
from rich.table import Table

if TYPE_CHECKING:
    import duckdb
    from rich.console import Console

    from dma.collector.query_managers import CanonicalQueryManager


def _print_summary_postgres(
    console: Console,
    local_db: duckdb.DuckDBPyConnection,
    manager: CanonicalQueryManager,
) -> None:
    """Print Summary of the Migration Readiness Assessment."""
    calculated_metrics = local_db.sql(
        """
            select metric_category, metric_name, metric_value
            from collection_postgres_calculated_metrics
        """,
    ).fetchall()
    count_table = Table(show_edge=False)
    count_table.add_column("Metric Category", justify="right", style="green")
    count_table.add_column("Metric", justify="right", style="green")
    count_table.add_column("Value", justify="right", style="green")

    for row in calculated_metrics:
        count_table.add_row(*[str(col) for col in row])
    console.print(count_table)
