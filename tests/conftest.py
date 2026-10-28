"""Shared pytest fixtures."""

import logging

import pytest

from stm32loader import main as stm32loader_main

# pylint: disable=protected-access


@pytest.fixture(autouse=True)
def reset_stm32loader_logging():
    """Undo the console logging setup that main() applies."""
    yield

    package_logger = logging.getLogger("stm32loader")
    for handler in stm32loader_main._console_handlers:
        package_logger.removeHandler(handler)
    stm32loader_main._console_handlers.clear()
    package_logger.setLevel(logging.NOTSET)
    package_logger.propagate = True
