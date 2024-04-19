# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations

from collections.abc import Awaitable
from functools import wraps
from inspect import iscoroutinefunction
from typing import TYPE_CHECKING, Any, Callable, TypeVar, cast

import aiosql
from rich.padding import Padding
from typing_extensions import ParamSpec

from dma.cli._utils import console
from dma.lib.db.query_manager import QueryManager
from dma.utils import module_to_os_path

if TYPE_CHECKING:
    from aiosql.queries import Queries
    from rich.status import Status

_root_path = module_to_os_path("dma")

P = ParamSpec("P")
R = TypeVar("R")

SyncOrAsyncCallable = Callable[[Callable[P, Awaitable[R]]], Callable[P, R] | Callable[P, Awaitable[R]]]


def printed_execution(
    section_title: str,
) -> SyncOrAsyncCallable:
    def wrapper(func: Callable[P, R] | Callable[P, Awaitable[R]]) -> Callable[P, R] | Callable[P, Awaitable[R]]:
        console.print(Padding(f"{section_title}", 1, style="bold", expand=True), width=80)
        with console.status("[bold green]Executing queries...[/]") as _status:
            if iscoroutinefunction(func):

                async def async_inner(*args: P.args, **kwargs: P.kwargs) -> R:
                    kwargs["_status"] = _status
                    return await cast("Awaitable[R]", func(*args, **kwargs))

                return wraps(func)(async_inner)

            def sync_inner(*args: P.args, **kwargs: P.kwargs) -> R:
                kwargs["_status"] = _status
                return cast("R", func(*args, **kwargs))

            return wraps(func)(sync_inner)

    return cast("SyncOrAsyncCallable", wrapper)


class CanonicalQueryManager(QueryManager):
    """Canonical Query Manager"""

    def __init__(
        self,
        connection: Any,
        queries: Queries = aiosql.from_path(sql_path=f"{_root_path}/collector/sql/canonical/", driver_adapter="duckdb"),
    ) -> None:
        super().__init__(connection, queries)

    @printed_execution(section_title="THE TRANSFORMATION QUERIES")
    async def execute_transformation_queries(self, *args: Any, **kwargs: Any) -> None:
        """Execute pre-processing queries."""
        status = cast("Status", kwargs.pop("_status"))
        for script in self.available_queries("transformation"):
            status.update(rf" [yellow]*[/] Executing [bold magenta]`{script}`[/]")
            await self.execute(script)
            status.console.print(rf" [green]:heavy_check_mark:[/] Gathered [bold magenta]`{script}`[/]")
        if not self.available_queries("transformation"):
            console.print(" [dim grey]:heavy_check_mark: No transformation queries for this database type[/]")

    @printed_execution(section_title="THE ASSESSMENT QUERIES")
    async def execute_assessment_queries(
        self,
        pkey: str = "test",
        dma_source_id: str = "testing",
        dma_manual_id: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute pre-processing queries."""
        status = cast("Status", kwargs.pop("_status"))
        results: dict[str, Any] = {}
        for script in self.available_queries("assessment"):
            status.update(rf" [yellow]*[/] Executing [bold magenta]`{script}`[/]")
            script_result = self.select(script, PKEY=pkey, DMA_SOURCE_ID=dma_source_id, DMA_MANUAL_ID=dma_manual_id)
            results[script] = script_result
            status.console.print(rf" [green]:heavy_check_mark:[/] Gathered [bold magenta]`{script}`[/]")
        if not self.available_queries("assessment"):
            console.print(" [dim grey]:heavy_check_mark: No assessment queries for this database type[/]")
        return results


class CollectionQueryManager(QueryManager):
    """Collection Query Manager"""

    @printed_execution(section_title="COLLECTION QUERIES")
    async def execute_collection_queries(
        self,
        pkey: str = "test",
        dma_source_id: str = "testing",
        dma_manual_id: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute pre-processing queries."""
        status = cast("Status", kwargs.pop("_status"))
        results: dict[str, Any] = {}
        for script in self.available_queries("collection"):
            status.update(rf" [yellow]*[/] Executing [bold magenta]`{script}`[/]")
            script_result = await self.select(
                script, PKEY=pkey, DMA_SOURCE_ID=dma_source_id, DMA_MANUAL_ID=dma_manual_id
            )
            results[script] = script_result
            status.console.print(rf" [green]:heavy_check_mark:[/] Gathered [bold magenta]`{script}`[/]")
        if not self.available_queries("collection"):
            status.console.print(" [dim grey]:heavy_check_mark: No collection queries for this database type[/]")
        return results

    @printed_execution(section_title="EXTENDED COLLECTION QUERIES")
    async def execute_extended_collection_queries(
        self,
        pkey: str = "test",
        dma_source_id: str = "testing",
        dma_manual_id: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute extended collection queries.

        Returns: None
        """
        status = cast("Status", kwargs.pop("_status"))
        results: dict[str, Any] = {}
        for script in self.available_queries("extended_collection"):
            status.update(rf" [yellow]*[/] Executing [bold magenta]`{script}`[/]")
            script_result = await self.select(
                script, PKEY=pkey, DMA_SOURCE_ID=dma_source_id, DMA_MANUAL_ID=dma_manual_id
            )
            results[script] = script_result
            status.console.print(rf" [green]:heavy_check_mark:[/] Gathered [bold magenta]`{script}`[/]")
        if not self.available_queries("extended_collection"):
            console.print(" [dim grey]:heavy_check_mark: No extended collection queries for this database type[/]")
        return results


class PostgresCollectionQueryManager(CollectionQueryManager):
    def __init__(
        self,
        connection: Any,
        queries: Queries = aiosql.from_path(
            sql_path=f"{_root_path}/collector/sql/sources/postgres", driver_adapter="asyncpg"
        ),
    ) -> None:
        super().__init__(connection, queries)


class MySQLCollectionQueryManager(CollectionQueryManager):
    def __init__(
        self,
        connection: Any,
        queries: Queries = aiosql.from_path(
            sql_path=f"{_root_path}/collector/sql/sources/mysql", driver_adapter="asyncmy"
        ),
    ) -> None:
        super().__init__(connection, queries)


class OracleCollectionQueryManager(CollectionQueryManager):
    def __init__(
        self,
        connection: Any,
        queries: Queries = aiosql.from_path(
            sql_path=f"{_root_path}/collector/sql/sources/oracle", driver_adapter="async_oracledb"
        ),
    ) -> None:
        super().__init__(connection, queries)


class SQLServerCollectionQueryManager(CollectionQueryManager):
    def __init__(
        self,
        connection: Any,
        queries: Queries = aiosql.from_path(
            sql_path=f"{_root_path}/collector/sql/sources/mssql", driver_adapter="aioodbc"
        ),
    ) -> None:
        super().__init__(connection, queries)
