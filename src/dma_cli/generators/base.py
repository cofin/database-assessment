"""Base generator class for database collectors.

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
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Callable, ClassVar

from jinja2 import Environment, FileSystemLoader

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class CollectorGenerator(ABC):
    """Base class for generating database collector scripts."""

    # Registry of database types to their generator classes
    _registry: ClassVar[dict[str, type[CollectorGenerator]]] = {}

    def __init__(self, template_dir: Path | None = None) -> None:
        """Initialize the generator.

        Args:
            template_dir: Optional custom template directory. If not provided,
                        uses the default templates bundled with the package.
        """
        self.template_dir = template_dir or self._get_default_template_dir()
        self.env = self._create_jinja_env()

    @abstractmethod
    def _get_default_template_dir(self) -> Path:
        """Get the default template directory for this database type.

        Returns:
            Path to the default template directory
        """
        ...

    def _create_jinja_env(self) -> Environment:
        """Create and configure the Jinja environment.

        Returns:
            Configured Jinja Environment
        """
        env = Environment(  # noqa: S701
            loader=FileSystemLoader(searchpath=self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )
        # Add any custom filters or globals here
        env.globals.update({
            "copyright_year": "2024",
            "google_license": self._get_license_text(),
        })
        return env

    @abstractmethod
    def generate(self, output_dir: Path) -> None:
        """Generate the collector scripts.

        Args:
            output_dir: Directory where the generated scripts will be written
        """
        ...

    @classmethod
    def register(cls, db_type: str) -> Callable[[type[CollectorGenerator]], type[CollectorGenerator]]:
        """Class decorator to register a generator for a database type.

        Args:
            db_type: Database type identifier (e.g., 'oracle', 'postgres')

        Returns:
            Decorator function
        """

        def decorator(subclass: type[CollectorGenerator]) -> type[CollectorGenerator]:
            cls._registry[db_type] = subclass
            return subclass

        return decorator

    @classmethod
    def create(cls, db_type: str, template_dir: Path | None = None) -> CollectorGenerator:
        """Factory method to create a generator for the specified database type.

        Args:
            db_type: Database type identifier
            template_dir: Optional custom template directory

        Returns:
            Appropriate CollectorGenerator instance

        Raises:
            ValueError: If db_type is not supported
        """
        if db_type not in cls._registry:
            msg = f"Unsupported database type: {db_type}"
            raise ValueError(msg)
        return cls._registry[db_type](template_dir)

    @staticmethod
    def _get_license_text() -> str:
        """Get the Google license text.

        Returns:
            License text as a string
        """
        copyright_year = datetime.now(tz=timezone.utc).year
        return f"""Copyright {copyright_year} Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License."""

    def _render_template(self, template_name: str, context: dict) -> str:
        """Render a template with the given context.

        Args:
            template_name: Name of the template file
            context: Dictionary of variables to pass to the template

        Returns:
            Rendered template as a string
        """
        template = self.env.get_template(name=template_name)
        return template.render(**context)
