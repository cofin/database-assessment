from __future__ import annotations

from dma.collector.workflows.base import BaseWorkflow
from dma.collector.workflows.readiness_check._mysql import _print_summary_mysql
from dma.collector.workflows.readiness_check._postgres import _print_summary_postgres


class ReadinessCheck(BaseWorkflow):
    async def process(self) -> None:
        await self.canonical_query_manager.execute_transformation_queries()
        await self.canonical_query_manager.execute_assessment_queries()

    def print_summary(self) -> None:
        """Print Summary of the Migration Readiness Assessment."""
        if self.db_type == "postgres":
            _print_summary_postgres(console=self.console, local_db=self.local_db, manager=self.canonical_query_manager)
        elif self.db_type == "mysql":
            _print_summary_mysql(console=self.console, local_db=self.local_db, manager=self.canonical_query_manager)
        else:
            msg = f"{self.db_type} is not implemented."
            raise NotImplementedError(msg)
