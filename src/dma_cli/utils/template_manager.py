"""Template management utilities for the DMA CLI tool.

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
from typing import TYPE_CHECKING, Any

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class TemplateManager:
    """Manages template loading and rendering for collector scripts."""

    def __init__(self, template_dir: Path) -> None:
        """Initialize the template manager.

        Args:
            template_dir: Directory containing the templates
        """
        self.template_dir = template_dir
        self.env = self._create_environment()

    def _create_environment(self) -> Environment:
        """Create and configure the Jinja environment.

        Returns:
            Configured Jinja Environment
        """
        env = Environment(
            loader=FileSystemLoader(searchpath=self.template_dir),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        # Register custom filters
        env.filters.update({
            "to_shell_array": self._to_shell_array,
            "to_shell_var": self._to_shell_var,
        })

        return env

    def get_template(self, template_name: str) -> Template:
        """Get a template by name.

        Args:
            template_name: Name of the template file

        Returns:
            Jinja Template object

        Raises:
            TemplateNotFound: If template doesn't exist
        """
        return self.env.get_template(name=template_name)

    def render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """Render a template with the given context.

        Args:
            template_name: Name of the template file
            context: Variables to pass to the template

        Returns:
            Rendered template as a string
        """
        template = self.get_template(template_name)
        return template.render(**context)

    @staticmethod
    def _to_shell_array(value: list[str]) -> str:
        """Convert a Python list to a shell array declaration.

        Args:
            value: List of strings

        Returns:
            Shell array declaration
        """
        elements = " ".join(f'"{x}"' for x in value)
        return f"( {elements} )"

    @staticmethod
    def _to_shell_var(value: str) -> str:
        """Convert a string to a shell-safe variable name.

        Args:
            value: Input string

        Returns:
            Shell-safe variable name
        """
        return value.upper().replace("-", "_").replace(" ", "_")
