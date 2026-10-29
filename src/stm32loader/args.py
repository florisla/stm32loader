"""Parse command-line arguments."""

import argparse
import atexit
import copy
import os
import sys

from stm32loader import __version__
from stm32loader.device_family import DeviceFamily

DEFAULT_VERBOSITY = 5

FAMILY_NAMES = [family.value for family in DeviceFamily]


class HelpFormatter(argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    """Custom help formatter -- don't print confusing default values."""

    def _get_help_string(self, action):
        action = copy.copy(action)
        # Don't show "(default: None)" for arguments without defaults,
        # or "(default: False)" for boolean flags, and hide the
        # (default: 5) from --verbose's help because it's confusing.
        if not action.default or action.dest == "verbosity":
            action.default = argparse.SUPPRESS
        return super()._get_help_string(action)

    @staticmethod
    def _require_port(actions):
        # Always treat -p/--port as required. See the note about the
        # argparse hack in Stm32Loader.parse_arguments for why.
        # Only copy the port action: argparse recognizes the members of
        # mutually exclusive groups by identity.
        def tweak_action(action):
            if action.dest != "port":
                return action
            action = copy.copy(action)
            action.required = True
            return action

        return [tweak_action(action) for action in actions]

    # The entry point for the usage line in all Python versions. The helpers
    # it calls differ between (patch) versions, so don't hook into those.
    def _format_usage(self, usage, actions, groups, prefix):
        return super()._format_usage(usage, self._require_port(actions), groups, prefix)  # pylint: disable=no-member


def _auto_int(x):
    """Convert to int with automatic base detection."""
    # This supports 0x10 == 16 and 10 == 10
    return int(x, 0)


def _auto_positive_int(x):
    """Convert to a positive int with automatic base detection."""
    value = _auto_int(x)
    if value <= 0:
        raise argparse.ArgumentTypeError(f"must be a positive number: '{x}'")
    return value


def _auto_non_negative_int(x):
    """Convert to a non-negative int with automatic base detection."""
    value = _auto_int(x)
    if value < 0:
        raise argparse.ArgumentTypeError(f"must not be negative: '{x}'")
    return value


def _family(value):
    """Normalize and validate a device family name."""
    family = value.upper()
    if family not in FAMILY_NAMES:
        raise argparse.ArgumentTypeError(
            f"invalid family '{value}'; choose from {', '.join(FAMILY_NAMES)}"
        )
    return family


def parse_arguments(arguments):
    """Parse the given command-line arguments and return the configuration."""

    parser = argparse.ArgumentParser(
        prog="stm32loader",
        description="Flash firmware to STM32 microcontrollers.",
        epilog="\n".join(
            [
                "examples:",
                "  %(prog)s --port COM7 --family F1",
                "  %(prog)s --erase --write --verify example/main.bin",
            ]
        ),
        formatter_class=HelpFormatter,
    )

    data_file_arg = parser.add_argument(
        "data_file",
        metavar="FILE.BIN",
        type=str,
        nargs="?",
        help="File to read from or store to flash.",
    )

    parser.add_argument(
        "-e",
        "--erase",
        action="store_true",
        help=(
            "Erase the full flash memory or a specific region (support --address and --length)."
            " Note: this is required on previously written memory."
        ),
    )

    parser.add_argument(
        "-E",
        "--auto-erase",
        action="store_true",
        help="Before writing, erase only the flash pages that the written data covers.",
    )

    parser.add_argument(
        "-u", "--unprotect", action="store_true", help="Unprotect flash from readout."
    )

    parser.add_argument(
        "-x", "--protect", action="store_true", help="Protect flash against readout."
    )

    parser.add_argument(
        "--write-unprotect", action="store_true", help="Disable write protection before flashing"
    )

    parser.add_argument(
        "--write-protect", action="store_true", help="Enable write protection after flashing"
    )

    parser.add_argument("-w", "--write", action="store_true", help="Write file content to flash.")

    parser.add_argument(
        "-v",
        "--verify",
        action="store_true",
        help="Verify flash content versus local file (recommended).",
    )

    parser.add_argument(
        "-r", "--read", action="store_true", help="Read from flash and store in local file."
    )

    length_arg = parser.add_argument(
        "-l",
        "--length",
        action="store",
        type=_auto_positive_int,
        help=(
            "Length of read or erase. For write and verify, use only this many bytes of the file."
        ),
    )

    default_port = os.environ.get("STM32LOADER_SERIAL_PORT")
    port_arg = parser.add_argument(
        "-p",
        "--port",
        action="store",
        type=str,  # morally required=True
        default=default_port,
        help=("Serial port" + ("." if default_port else " (default: $STM32LOADER_SERIAL_PORT).")),
    )

    parser.add_argument(
        "-b", "--baud", action="store", type=int, default=115200, help="Baudrate."
    )

    location_group = parser.add_mutually_exclusive_group()
    location_group.add_argument(
        "-a",
        "--address",
        action="store",
        type=_auto_int,
        help=(
            "Target address for read or write. For erase, this is used when you supply --length."
            " Default: the start of flash memory."
        ),
    )
    location_group.add_argument(
        "-o",
        "--offset",
        action="store",
        type=_auto_non_negative_int,
        help="Alternative to --address: an offset from the start of flash memory.",
    )

    parser.add_argument(
        "-g",
        "--go-address",
        action="store",
        type=_auto_int,
        metavar="ADDRESS",
        help="Start executing from address (0x08000000, usually).",
    )

    default_family = os.environ.get("STM32LOADER_FAMILY")
    parser.add_argument(
        "-f",
        "--family",
        action="store",
        type=_family,
        default=default_family,
        help=(
            "Device family to read out device UID and flash size; "
            "e.g F1 for STM32F1xx. Possible values: "
            + ", ".join(FAMILY_NAMES)
            + ("." if default_family else " (default: $STM32LOADER_FAMILY).")
        ),
    )

    parser.add_argument(
        "-V",
        "--verbose",
        dest="verbosity",
        action="store_const",
        const=10,
        default=DEFAULT_VERBOSITY,
        help="Verbose mode.",
    )

    parser.add_argument(
        "-q", "--quiet", dest="verbosity", action="store_const", const=0, help="Quiet mode."
    )

    parser.add_argument(
        "-s",
        "--swap-rts-dtr",
        action="store_true",
        help="Swap RTS and DTR: use RTS for reset and DTR for boot0.",
    )

    parser.add_argument(
        "-R", "--reset-active-high", action="store_true", help="Make RESET active high."
    )

    parser.add_argument(
        "-B", "--boot0-active-low", action="store_true", help="Make BOOT0 active low."
    )

    parser.add_argument(
        "-n", "--no-progress", action="store_true", help="Don't show progress bar."
    )

    parser.add_argument(
        "-P",
        "--parity",
        action="store",
        type=str,
        default="even",
        choices=["even", "none"],
        help='Parity: "even" for STM32, "none" for BlueNRG.',
    )

    parser.add_argument("--version", action="version", version=__version__)

    # Hack: We want certain arguments to be required when one
    # of -rwv is specified, but argparse doesn't support
    # conditional dependencies like that. Instead, we add the
    # requirements post-facto and re-run the parse to get the error
    # messages we want. A better solution would be to use
    # subcommands instead of options for -rwv, but this would
    # change the command-line interface.
    #
    # We also use this gross hack to provide a hint about the
    # STM32LOADER_SERIAL_PORT environment variable when -p
    # is omitted; we only set --port as required after the first
    # parse so we can hook in a custom error message.

    configuration = parser.parse_args(arguments)

    if not configuration.port:
        port_arg.required = True
        atexit.register(
            lambda: print(
                f"{parser.prog}: note: you can also set the environment"
                " variable STM32LOADER_SERIAL_PORT",
                file=sys.stderr,
            )
        )

    if configuration.auto_erase and not configuration.write:
        parser.error("argument -E/--auto-erase: requires -w/--write")
    if configuration.auto_erase and configuration.erase:
        parser.error("argument -E/--auto-erase: not allowed with argument -e/--erase")

    if configuration.read or configuration.write or configuration.verify:
        data_file_arg.nargs = None
        data_file_arg.required = True

    if configuration.read:
        length_arg.required = True
        location_group.required = True

    parser.parse_args(arguments)

    return configuration
