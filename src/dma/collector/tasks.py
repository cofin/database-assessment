from __future__ import annotations

from sys import version_info
from typing import TYPE_CHECKING, Literal, cast

import polars as pl
from rich.padding import Padding
from sqlalchemy.ext.asyncio import AsyncSession

from dma.collector.dependencies import provide_canonical_queries, provide_collection_query_manager
from dma.collector.readiness_check import ReadinessCheck
from dma.lib.db.base import get_engine
from dma.lib.db.local import get_duckdb_connection

if TYPE_CHECKING:
    from pathlib import Path

    import duckdb
    from rich.console import Console

    from dma.collector.query_managers import CanonicalQueryManager, CollectionQueryManager

if version_info < (3, 10):  # pragma: nocover
    from dma.utils import anext_ as anext  # noqa: A001


async def readiness_check(
    console: Console,
    db_type: Literal["mysql", "postgres", "mssql", "oracle"],
    username: str,
    password: str,
    hostname: str,
    port: int,
    database: str,
    # pkey: str,
    # dma_source_id: str,
    # dma_manual_id: str,
    working_path: Path | None = None,
) -> None:
    """Assess the migration readiness for a Database for Database Migration Services"""
    async_engine = get_engine(db_type, username, password, hostname, port, database)
    with get_duckdb_connection(working_path) as local_db:
        async with AsyncSession(async_engine) as db_session:
            collection_manager = cast(
                "CollectionQueryManager", await anext(provide_collection_query_manager(db_session))
            )
            pipeline_manager = next(provide_canonical_queries(local_db))
            readiness_check = ReadinessCheck(
                local_db=local_db, canonical_query_manager=pipeline_manager, db_type=db_type, console=console
            )
            # collect data
            _collection = await collection_manager.execute_collection_queries()
            _extended_collection = await collection_manager.execute_extended_collection_queries()
            # import data locally
            local_db = import_data_to_local_db(local_db, _collection)
            local_db = import_data_to_local_db(local_db, _extended_collection)

            # transform data
            local_db = await execute_local_db_pipeline(local_db, pipeline_manager)
            console.print(Padding("COLLECTION SUMMARY", 1, style="bold", expand=True), width=80)
            # print summary
            readiness_check.print_summary()
    await async_engine.dispose()


def import_data_to_local_db(
    local_db: duckdb.DuckDBPyConnection, data: dict[str, list[dict]]
) -> duckdb.DuckDBPyConnection:
    """Loads Dictionary of type dict[str,list[dict]] to a DuckDB connection."""
    for table_name, table_data in data.items():
        if len(table_data) > 0:
            local_db.register(table_name, pl.from_dicts(table_data, infer_schema_length=10000))
    return local_db


async def execute_local_db_pipeline(
    local_db: duckdb.DuckDBPyConnection, manager: CanonicalQueryManager
) -> duckdb.DuckDBPyConnection:
    """Transforms Loaded Data into the Canonical Model Tables."""
    await manager.execute_transformation_queries()
    await manager.execute_assessment_queries()
    return local_db
