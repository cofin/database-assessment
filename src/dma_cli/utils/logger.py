"""Logging configuration for the DMA CLI tool.

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

import logging

from rich.logging import RichHandler


def setup_logging(debug: bool = False) -> None:
    """Configure logging for the application.

    Args:
        debug: Enable debug logging if True
    """
    level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(level=level, format="%(message)s", datefmt="[%X]", handlers=[RichHandler(rich_tracebacks=True)])

    # Reduce noise from other libraries
    if not debug:
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("jinja2").setLevel(logging.WARNING)
