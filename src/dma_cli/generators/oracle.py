"""Oracle template generator module.

This module handles the generation of Oracle database collection scripts
from Jinja2 templates.
"""

import datetime
from pathlib import Path
from typing import Dict, List

from jinja2 import Environment, FileSystemLoader

from dma_cli.config import Config
from dma_cli.utils.template import TemplateGenerator


class OracleGenerator(TemplateGenerator):
    """Oracle template generator class."""

    def __init__(self, config: Config):
        """Initialize Oracle generator.

        Args:
            config: Application configuration object
        """
        super().__init__(config)
        self.template_dir = Path(__file__).parent.parent / "templates" / "oracle"
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

    def get_context(self) -> Dict:
        """Get template rendering context.

        Returns:
            Dict containing template variables
        """
        return {
            "version": self.config.version,
            "generation_date": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "copyright_year": datetime.datetime.utcnow().year,
            "supported_oracle_versions": ["19", "18", "12.2", "12.1"],
            "required_commands": ["sqlplus", "grep", "awk", "sed"],
            "sql_scripts": {
                "version_info.csv": "Database version information",
                "database_config.csv": "Database configuration settings",
                "table_info.csv": "Table definitions and statistics",
                "index_info.csv": "Index definitions and statistics",
                "performance_stats.csv": "Performance statistics",
                "security_info.csv": "Security configuration",
                "storage_info.csv": "Storage and tablespace information",
                "extension_info.csv": "Extension and custom type information",
            },
        }

    def generate_collection_scripts(self, output_dir: Path, force: bool = False) -> None:
        """Generate Oracle collection scripts.

        Args:
            output_dir: Output directory path
            force: Force overwrite existing files

        Raises:
            FileExistsError: If output files exist and force is False
        """
        context = self.get_context()

        # Create output directory structure
        script_dir = output_dir / "oracle"
        utils_dir = script_dir / "utils"
        sql_dir = script_dir / "sql"
        docs_dir = script_dir / "docs"
        headers_dir = sql_dir / "headers"

        for directory in [script_dir, utils_dir, sql_dir, docs_dir, headers_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Generate shell scripts
        shell_scripts = [
            "collect_data.sh",
            "utils/common.sh",
            "utils/logging.sh",
            "utils/oracle_utils.sh",
            "utils/validation.sh",
            "utils/archive.sh",
        ]

        for script in shell_scripts:
            template = self.env.get_template(f"{script}.j2")
            output_file = script_dir / script

            if output_file.exists() and not force:
                raise FileExistsError(f"File exists: {output_file}")

            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(template.render(context))
            output_file.chmod(0o755)

        # Generate SQL scripts
        sql_scripts = [
            "version.sql",
            "database_info.sql",
            "table_info.sql",
            "index_info.sql",
            "performance_stats.sql",
            "security_info.sql",
            "storage_info.sql",
            "extension_info.sql",
        ]

        for script in sql_scripts:
            template = self.env.get_template(f"sql/{script}.j2")
            output_file = sql_dir / script

            if output_file.exists() and not force:
                raise FileExistsError(f"File exists: {output_file}")

            output_file.write_text(template.render(context))

        # Generate documentation
        doc_files = [
            "README.md",
            "TROUBLESHOOTING.md",
        ]

        for doc in doc_files:
            template = self.env.get_template(f"docs/{doc}.j2")
            output_file = docs_dir / doc

            if output_file.exists() and not force:
                raise FileExistsError(f"File exists: {output_file}")

            output_file.write_text(template.render(context))

        # Generate SQL headers
        for script in sql_scripts:
            base_name = Path(script).stem
            template = self.env.get_template(f"sql/headers/{base_name}.header.j2")
            output_file = headers_dir / f"{base_name}.header"

            if output_file.exists() and not force:
                raise FileExistsError(f"File exists: {output_file}")

            output_file.write_text(template.render(context))

    def validate_environment(self) -> List[str]:
        """Validate environment for Oracle collection.

        Returns:
            List of validation error messages
        """
        errors = []

        # Check for required commands
        for cmd in self.get_context()["required_commands"]:
            if not self.check_command(cmd):
                errors.append(f"Required command not found: {cmd}")

        # Check for Oracle environment variables
        if not self.config.env.get("ORACLE_HOME"):
            errors.append("ORACLE_HOME environment variable not set")

        return errors
