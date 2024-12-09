"""Database Migration Assessment CLI Tool.

This tool generates and manages database collection scripts for various database platforms.

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

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click>=8.0.0",
#     "rich>=10.0.0",
#     "Jinja2>=3.0.0",
#     "PyYAML>=6.0.0",
# ]
# ///
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from dma_cli.generators.base import CollectorGenerator
from dma_cli.utils.config import load_config
from dma_cli.utils.logger import setup_logging

console = Console()


@click.group()
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable debug logging",
)
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to config file",
)
@click.version_option()
def cli(debug: bool, config: Optional[Path] = None) -> None:
    """Database Migration Assessment CLI Tool.

    Generates and manages database collection scripts for various database platforms.
    """
    setup_logging(debug)
    if config:
        load_config(config)


@cli.command()
@click.argument("db_type", type=click.Choice(["oracle", "postgres", "mysql", "sqlserver"]))
@click.argument("output_dir", type=click.Path(path_type=Path))
@click.option("--template-dir", type=click.Path(exists=True, path_type=Path), help="Custom template directory")
def generate(db_type: str, output_dir: Path, template_dir: Optional[Path] = None) -> None:
    """Generate collection scripts for a specific database type."""
    try:
        generator = CollectorGenerator.create(db_type, template_dir)
        generator.generate(output_dir)
        console.print(f"[green]Successfully generated {db_type} collector scripts in {output_dir}[/green]")
    except Exception as e:
        console.print(f"[red]Error generating collector scripts: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()
