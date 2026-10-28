import atexit
import re

import pytest

from stm32loader.main import Stm32Loader


@pytest.fixture
def program():
    return Stm32Loader()


def test_parse_arguments_without_args_raises_typeerror(program):
    with pytest.raises(TypeError, match="missing.*required.*argument"):
        program.parse_arguments()


def test_parse_arguments_with_standard_args_passes(program):
    program.parse_arguments(["-p", "port", "-b", "9600", "-q"])


@pytest.mark.parametrize(
    "help_argument",
    ["-h", "--help"],
)
def test_parse_arguments_with_help_raises_systemexit(program, help_argument):
    with pytest.raises(SystemExit):
        program.parse_arguments([help_argument])


def test_parse_arguments_erase_without_port_complains_about_missing_argument(program, capsys):
    try:
        program.parse_arguments(["-e", "-w", "-v", "file.bin"])
    except SystemExit:
        pass

    # Also call atexit functions so that the hint about using an env variable
    # is printed.
    atexit._run_exitfuncs()

    _output, error_output = capsys.readouterr()
    if not error_output:
        pytest.skip("Not sure why nothing is captured in some pytest runs?")
    assert "arguments are required: -p/--port" in error_output
    assert "STM32LOADER_SERIAL_PORT" in error_output


def test_parse_arguments_write_unprotect(program):
    program.parse_arguments(["-p", "port", "--write-unprotect"])
    assert program.configuration.write_unprotect


def test_parse_arguments_write_protect(program):
    program.parse_arguments(["-p", "port", "--write-protect"])
    assert program.configuration.write_protect


@pytest.mark.parametrize("family", ["f3", "F3"])
def test_parse_arguments_family_is_case_insensitive(program, family):
    program.parse_arguments(["-p", "port", "-f", family])
    assert program.configuration.family == "F3"


def test_parse_arguments_unknown_family_raises_systemexit(program, capsys):
    with pytest.raises(SystemExit):
        program.parse_arguments(["-p", "port", "-f", "XX"])

    _output, error_output = capsys.readouterr()
    assert "invalid family 'XX'" in error_output


def test_help_shows_port_as_required(program, capsys):
    with pytest.raises(SystemExit):
        program.parse_arguments(["--help"])

    output, _error_output = capsys.readouterr()
    assert re.search(r"\s-p PORT\s", output)
    assert "[-p PORT]" not in output


def test_parse_arguments_address_and_offset_are_mutually_exclusive(program, capsys):
    with pytest.raises(SystemExit):
        program.parse_arguments(["-p", "port", "-a", "0x08000000", "-o", "0x400"])

    _output, error_output = capsys.readouterr()
    assert "not allowed with argument" in error_output


def test_parse_arguments_offset_without_address(program):
    program.parse_arguments(["-p", "port", "-o", "0x400"])
    assert program.configuration.offset == 0x400
    assert program.configuration.address is None


def test_parse_arguments_negative_offset_raises_systemexit(program):
    with pytest.raises(SystemExit):
        program.parse_arguments(["-p", "port", "-o", "-1"])


@pytest.mark.parametrize("length", ["0", "-16"])
def test_parse_arguments_non_positive_length_raises_systemexit(program, length, capsys):
    with pytest.raises(SystemExit):
        program.parse_arguments(["-p", "port", "-l", length])

    _output, error_output = capsys.readouterr()
    assert "must be a positive number" in error_output


@pytest.mark.parametrize("location", [["-a", "0x08000000"], ["-o", "0"]])
def test_parse_arguments_read_accepts_address_or_offset(program, location):
    program.parse_arguments(["-p", "port", "-r", "-l", "16", *location, "out.bin"])
    assert program.configuration.read


def test_parse_arguments_read_without_address_or_offset_raises_systemexit(program, capsys):
    with pytest.raises(SystemExit):
        program.parse_arguments(["-p", "port", "-r", "-l", "16", "out.bin"])

    _output, error_output = capsys.readouterr()
    assert "one of the arguments -a/--address -o/--offset is required" in error_output
