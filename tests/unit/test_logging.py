"""Tests for the console logging set up by the stm32loader CLI."""

import logging

import pytest

from stm32loader import main as stm32loader_main
from stm32loader.main import _configure_logging

# pylint: disable=missing-docstring, redefined-outer-name, protected-access

VERBOSE = 10
DEFAULT = 5
QUIET = 0


@pytest.fixture
def logger():
    yield logging.getLogger("stm32loader.test")

    package_logger = logging.getLogger("stm32loader")
    for handler in stm32loader_main._console_handlers:
        package_logger.removeHandler(handler)
    package_logger.setLevel(logging.NOTSET)
    package_logger.propagate = True


def test_default_verbosity_sends_info_to_stdout_and_hides_debug(logger, capsys):
    _configure_logging(DEFAULT)
    logger.info("some info")
    logger.debug("some debug")

    output, error_output = capsys.readouterr()
    assert output == "some info\n"
    assert error_output == ""


def test_verbose_sends_debug_to_stdout(logger, capsys):
    _configure_logging(VERBOSE)
    logger.debug("some debug")

    output, _error_output = capsys.readouterr()
    assert output == "some debug\n"


def test_quiet_hides_info_but_shows_warning_on_stderr(logger, capsys):
    _configure_logging(QUIET)
    logger.info("some info")
    logger.warning("some warning")

    output, error_output = capsys.readouterr()
    assert output == ""
    assert error_output == "some warning\n"


def test_error_goes_to_stderr_only(logger, capsys):
    _configure_logging(DEFAULT)
    logger.error("some error")

    output, error_output = capsys.readouterr()
    assert output == ""
    assert error_output == "some error\n"


def test_configuring_twice_does_not_duplicate_output(logger, capsys):
    _configure_logging(DEFAULT)
    _configure_logging(DEFAULT)
    logger.info("some info")

    output, _error_output = capsys.readouterr()
    assert output == "some info\n"
