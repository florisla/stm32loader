"""
Run unit tests in a fresh virtualenv using nox.

Usage:

    uv run nox
"""

from nox import Session, options
from nox_uv import session

options.default_venv_backend = "uv"


PYTHON_VERSIONS = ["3.9", "3.10", "3.11", "3.12", "3.13", "3.14", "pypy-3.10", "pypy-3.11"]
DEFAULT_PYTHON_VERSION = "3.14"


@session(python=PYTHON_VERSIONS, uv_groups=("test", "hex"))
def test(session: Session) -> None:
    """Execute unit tests."""
    session.run("pytest")


@session(python=DEFAULT_PYTHON_VERSION, uv_groups=("lint",))
def lint(session: Session) -> None:
    """
    Run code verification tools ruff and pylint.

    Do this in order of expected failures for performance reasons.
    """
    session.run("ruff", "format", "--check", "src/stm32loader")
    session.run("ruff", "check", "src/stm32loader")
    session.run("pylint", "stm32loader")
