"""PostgreSQL collector script generator.

Copyright 2024 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import annotations

import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import ClassVar

from dma_cli.generators.base import CollectorGenerator
from dma_cli.utils.constants import CURRENT_VERSION

logger = logging.getLogger(__name__)


@CollectorGenerator.register("postgres")
class PostgresCollectorGenerator(CollectorGenerator):
    """Generator for PostgreSQL collector scripts."""

    REQUIRED_COMMANDS: ClassVar[list[str]] = [
        "bash",
        "cat",
        "cut",
        "dirname",
        "grep",
        "locale",
        "mkdir",
        "psql",
        "sed",
        "tar",
        "tr",
        "which",
        "zip",
    ]

    SQL_TEMPLATES: ClassVar[dict[str, str]] = {
        # Core database information
        "version.sql": "Get PostgreSQL version information",
        "database_info.sql": "Collect database configuration and settings",
        "instance_info.sql": "Gather instance-level configuration",
        # Schema and object information
        "table_info.sql": "Collect table metadata and statistics",
        "index_info.sql": "Gather index information and statistics",
        "constraint_info.sql": "Collect constraint definitions",
        "sequence_info.sql": "Gather sequence information",
        "view_info.sql": "Collect view definitions",
        "function_info.sql": "Gather function and procedure definitions",
        "trigger_info.sql": "Collect trigger information",
        # Storage and performance
        "tablespace_info.sql": "Gather tablespace configuration",
        "table_bloat.sql": "Estimate table bloat",
        "index_bloat.sql": "Estimate index bloat",
        "table_stats.sql": "Collect table statistics",
        "index_stats.sql": "Gather index usage statistics",
        # Security
        "role_info.sql": "Collect role and permission information",
        "grant_info.sql": "Gather object permissions",
        # Extensions and custom features
        "extension_info.sql": "Collect installed extensions",
        "custom_types.sql": "Gather custom type definitions",
        # Performance and monitoring
        "pg_stat_statements.sql": "Collect query statistics if pg_stat_statements is enabled",
        "long_running_queries.sql": "Identify long-running queries",
        "connection_info.sql": "Gather connection and session information",
        "lock_info.sql": "Collect lock information",
        # Configuration
        "pg_settings.sql": "Gather PostgreSQL configuration parameters",
        "pg_hba_info.sql": "Collect authentication configuration",
    }

    SHELL_TEMPLATES: ClassVar[dict[str, str]] = {
        "collect_data.sh": "Main collection script",
        "utils/common.sh": "Common shell functions",
        "utils/logging.sh": "Logging utilities",
        "utils/postgres_utils.sh": "PostgreSQL-specific utilities",
        "utils/validation.sh": "Input validation functions",
        "utils/archive.sh": "Archive management functions",
    }

    def _get_default_template_dir(self) -> Path:
        """Get the default template directory for PostgreSQL.

        Returns:
            Path to the default template directory
        """
        return Path(__file__).parent.parent / "templates" / "postgres"

    def generate(self, output_dir: Path) -> None:
        """Generate the PostgreSQL collector scripts.

        Args:
            output_dir: Directory where the generated scripts will be written
        """
        logger.info("Generating PostgreSQL collector scripts in %s", output_dir)

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Generate directory structure
            self._create_directory_structure(output_dir)

            # Generate shell scripts
            self._generate_shell_scripts(output_dir)

            # Generate SQL scripts
            self._generate_sql_scripts(output_dir)

            # Copy static files if any
            self._copy_static_files(output_dir)

            # Generate documentation
            self._generate_documentation(output_dir)

            logger.info("Successfully generated collector scripts")

        except Exception as e:
            logger.exception("Failed to generate collector scripts: %s", e)
            raise

    def _create_directory_structure(self, output_dir: Path) -> None:
        """Create the required directory structure.

        Args:
            output_dir: Base output directory
        """
        dirs = [
            "sql",
            "utils",
            "docs",
            "output",
            "tmp",
            "log",
        ]

        for dir_name in dirs:
            (output_dir / dir_name).mkdir(exist_ok=True)

    def _generate_shell_scripts(self, output_dir: Path) -> None:
        """Generate shell scripts.

        Args:
            output_dir: Output directory
        """
        context = {
            "required_commands": self.REQUIRED_COMMANDS,
            "version": CURRENT_VERSION,
            "generation_date": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d"),
            "supported_postgres_versions": ["12", "13", "14", "15", "16"],
        }

        for template_name, description in self.SHELL_TEMPLATES.items():
            logger.debug("Generating %s: %s", template_name, description)

            content = self._render_template(f"{template_name}.j2", context)
            output_file = output_dir / template_name

            # Create parent directories if needed
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            output_file.write_text(content)

            # Make executable if it's a .sh file
            if output_file.suffix == ".sh":
                output_file.chmod(0o755)

    def _generate_sql_scripts(self, output_dir: Path) -> None:
        """Generate SQL scripts.

        Args:
            output_dir: Output directory
        """
        sql_dir = output_dir / "sql"
        context = {
            "version": CURRENT_VERSION,
            "generation_date": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d"),
        }

        for template_name, description in self.SQL_TEMPLATES.items():
            logger.debug("Generating %s: %s", template_name, description)

            content = self._render_template(f"sql/{template_name}.j2", context)
            output_file = sql_dir / template_name
            output_file.write_text(content)

    def _copy_static_files(self, output_dir: Path) -> None:
        """Copy static files that don't need templating.

        Args:
            output_dir: Output directory
        """
        static_dir = self.template_dir / "static"
        if static_dir.exists():
            for file in static_dir.rglob("*"):
                if file.is_file():
                    rel_path = file.relative_to(static_dir)
                    dest = output_dir / rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file, dest)

    def _generate_documentation(self, output_dir: Path) -> None:
        """Generate documentation files.

        Args:
            output_dir: Output directory
        """
        docs_dir = output_dir / "docs"

        # Generate README
        context = {
            "version": CURRENT_VERSION,
            "generation_date": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d"),
            "required_commands": self.REQUIRED_COMMANDS,
            "sql_scripts": self.SQL_TEMPLATES,
        }

        readme_content = self._render_template("docs/README.md.j2", context)
        (docs_dir / "README.md").write_text(readme_content)

        # Generate other documentation
        for doc in ["USAGE.md", "TROUBLESHOOTING.md"]:
            content = self._render_template(f"docs/{doc}.j2", context)
            (docs_dir / doc).write_text(content)
