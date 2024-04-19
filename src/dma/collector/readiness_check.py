from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import duckdb
import polars as pl
from rich.table import Table

if TYPE_CHECKING:
    import duckdb
    from rich.console import Console

    from dma.collector.query_managers import CanonicalQueryManager


class AssessmentWorkflow:
    """A collection of tasks that interact with DuckDB"""

    def __init__(
        self,
        local_db: duckdb.DuckDBPyConnection,
        canonical_query_manager: CanonicalQueryManager,
        db_type: Literal["mysql", "postgres", "mssql", "oracle"],
        console: Console,
    ) -> None:
        """Initialize a workflow on a local duckdb instance."""
        self.local_db = local_db
        self.console = console
        self.db_type = db_type
        self.canonical_query_manager = canonical_query_manager

    def import_to_table(self, data: dict[str, list[dict]]) -> None:
        """Load a dictionary of result sets into duckdb.

        The key of the dictionary becomes the table name in the database.
        """
        for table_name, table_data in data.items():
            if len(table_data) > 0:
                self.local_db.register(table_name, pl.from_dicts(table_data, infer_schema_length=10000))


class ReadinessCheck(AssessmentWorkflow):
    async def process(self) -> None:
        _ = await self.canonical_query_manager.execute_transformation_queries()
        _ = await self.canonical_query_manager.execute_assessment_queries()

    def print_summary(self) -> None:
        """Print Summary of the Migration Readiness Assessment."""
        if self.db_type == "postgres":
            _print_summary_postgres(console=self.console, local_db=self.local_db, manager=self.canonical_query_manager)
        elif self.db_type == "mysql":
            _print_summary_mysql(console=self.console, local_db=self.local_db, manager=self.canonical_query_manager)
        else:
            msg = f"{self.db_type} is not implemented."
            raise NotImplementedError(msg)


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


def _print_summary_mysql(
    console: Console,
    local_db: duckdb.DuckDBPyConnection,
    manager: CanonicalQueryManager,
) -> None:
    """Print Summary of the Migration Readiness Assessment."""
    calculated_metrics = local_db.sql(
        """
            select variable_category, variable_name, variable_value
            from collection_mysql_config
        """,
    ).fetchall()
    count_table = Table(show_edge=False)
    count_table.add_column("Variable Category", justify="right", style="green")
    count_table.add_column("Variable", justify="right", style="green")
    count_table.add_column("Value", justify="right", style="green")

    for row in calculated_metrics:
        count_table.add_row(*[str(col) for col in row])
    console.print(count_table)
