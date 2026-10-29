#!/usr/bin/env python
# Authors: Ivan A-R, Floris Lambrechts
# GitHub repository: https://github.com/florisla/stm32loader
#
# This file is part of stm32loader.
#
# stm32loader is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 3, or (at your option) any later
# version.
#
# stm32loader is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with stm32loader; see the file LICENSE.  If not see
# <http://www.gnu.org/licenses/>.

"""Flash firmware to STM32 microcontrollers over a serial connection."""

import logging
import sys
from pathlib import Path
from types import SimpleNamespace

import serial

try:
    from progress.bar import ChargingBar as progress_bar
except ImportError:
    progress_bar = None

from stm32loader import args, bootloader, hexfile
from stm32loader.device_family import DEVICE_FAMILIES, DeviceFamily, DeviceFlag
from stm32loader.uart import SerialConnection

logger = logging.getLogger(__name__)

# Handlers added by _configure_logging, removed again on the next call.
_console_handlers = []


class Stm32Loader:
    """Main application: parse arguments and handle commands."""

    # serial link bit parity, compatible to pyserial serial.PARTIY_EVEN
    PARITY = {"even": serial.PARITY_EVEN, "none": serial.PARITY_NONE}

    def __init__(self):
        """Construct Stm32Loader object with default settings."""
        self.stm32 = None
        self.configuration = SimpleNamespace()

    def parse_arguments(self, arguments):
        """Parse the list of command-line arguments."""
        self.configuration = args.parse_arguments(arguments)

        # parse successful, process options further
        self.configuration.parity = Stm32Loader.PARITY[self.configuration.parity.lower()]

        if self.configuration.family:
            family = DeviceFamily[self.configuration.family]
            family_flags = DEVICE_FAMILIES[family].family_default_flags
            if family_flags & DeviceFlag.FORCE_PARITY_NONE:
                self.configuration.parity = serial.PARITY_NONE

    def connect(self):
        """Connect to the bootloader UART over an RS-232 serial port."""
        serial_connection = SerialConnection(
            self.configuration.port, self.configuration.baud, self.configuration.parity
        )
        logger.debug("Open port %s, baud %d", self.configuration.port, self.configuration.baud)
        try:
            serial_connection.connect()
        except IOError as e:
            logger.error(
                "%s\n\n"
                "Is the device connected and powered correctly?\n"
                "Please use the --port option to select the correct serial port. Examples:\n"
                "  --port COM3\n"
                "  --port /dev/ttyS0\n"
                "  --port /dev/ttyUSB0\n"
                "  --port /dev/tty.usbserial-ftCYPMYJ\n",
                e,
            )
            sys.exit(1)

        serial_connection.swap_rts_dtr = self.configuration.swap_rts_dtr
        serial_connection.reset_active_high = self.configuration.reset_active_high
        serial_connection.boot0_active_low = self.configuration.boot0_active_low

        show_progress = self._get_progress_bar(self.configuration.no_progress)

        self.stm32 = bootloader.Stm32Bootloader(
            serial_connection,
            show_progress=show_progress,
            device_family=self.configuration.family,
        )

        try:
            logger.info("Activating bootloader (select UART)")
            self.stm32.reset_from_system_memory()
        except bootloader.CommandError:
            logger.error(
                "Can't init into bootloader. Ensure that BOOT0 is enabled and reset the device."
            )
            self.stm32.reset_from_flash()
            sys.exit(1)

    def perform_commands(self):
        """Run all operations as defined by the configuration."""
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        binary_data = None
        if self.configuration.write or self.configuration.verify:
            data_file_path = Path(self.configuration.data_file)
            if data_file_path.suffix == ".hex":
                binary_data = hexfile.load_hex(data_file_path)
            else:
                binary_data = data_file_path.read_bytes()
            binary_data = self._apply_length(binary_data, data_file_path.name)

        # Check the target range before touching the device.
        address = self._target_address()
        erase_pages = None
        try:
            if self.configuration.erase and self.configuration.length is not None:
                erase_pages = self.stm32.pages_from_range(
                    address, address + self.configuration.length
                )
            elif self.configuration.auto_erase and binary_data:
                erase_pages = self.stm32.pages_covering_range(address, address + len(binary_data))
        except bootloader.PageIndexError as e:
            logger.error("%s", e)
            sys.exit(1)

        if self.configuration.unprotect:
            try:
                self.stm32.readout_unprotect()
            except bootloader.CommandError:
                logger.error("Flash readout unprotect failed")
                self.stm32.reset_from_flash()
                sys.exit(1)
        if self.configuration.protect:
            try:
                self.stm32.readout_protect()
            except bootloader.CommandError:
                logger.error("Flash readout protect failed")
                self.stm32.reset_from_flash()
                sys.exit(1)

        if self.configuration.write_unprotect:
            try:
                self.stm32.write_unprotect()
            except bootloader.CommandError:
                logger.error("Flash write unprotect failed")
                self.stm32.reset_from_flash()
                sys.exit(1)

        if self.configuration.erase or erase_pages:
            try:
                if self.configuration.auto_erase:
                    logger.info(
                        "Performing auto erase (0x%X - 0x%X, %d pages)... ",
                        address,
                        address + len(binary_data),
                        len(erase_pages),
                    )
                    self.stm32.erase_memory(erase_pages)
                elif erase_pages is None:
                    # Erase full device.
                    logger.info("Performing full erase...")
                    self.stm32.erase_memory(pages=None)
                else:
                    # Erase from address to address + length.
                    logger.info(
                        "Performing partial erase (0x%X - 0x%X, %d pages)... ",
                        address,
                        address + self.configuration.length,
                        len(erase_pages),
                    )
                    self.stm32.erase_memory(erase_pages)

            except bootloader.CommandError:
                # may be caused by readout protection
                logger.error(
                    "Erase failed -- probably due to readout protection.\n"
                    "Consider using the --unprotect option."
                )
                self.stm32.reset_from_flash()
                sys.exit(1)
        if self.configuration.write:
            self.stm32.write_memory_data(address, binary_data)

        if self.configuration.write_protect:
            try:
                self.stm32.write_protect(sectors=None)
            except bootloader.CommandError:
                logger.error("Flash write protect failed")
                self.stm32.reset_from_flash()
                sys.exit(1)

        if self.configuration.verify:
            read_data = self.stm32.read_memory_data(address, len(binary_data))
            try:
                bootloader.Stm32Bootloader.verify_data(read_data, binary_data)
                logger.info("Verification OK")
            except bootloader.DataMismatchError as e:
                logger.error("Verification FAILED: %s", e)
                sys.exit(1)
        if not self.configuration.write and self.configuration.read:
            read_data = self.stm32.read_memory_data(address, self.configuration.length)
            with open(self.configuration.data_file, "wb") as out_file:
                out_file.write(read_data)
        if self.configuration.go_address is not None:
            self.stm32.go(self.configuration.go_address)

    def _apply_length(self, data, file_name):
        """Truncate the file data to --length, warning when sizes differ."""
        length = self.configuration.length
        if length is None or length == len(data):
            return data

        if length < len(data):
            logger.warning(
                "--length %d is smaller than %s (%d bytes); using only the first %d bytes.",
                length,
                file_name,
                len(data),
                length,
            )
            return data[:length]

        logger.warning(
            "--length %d is larger than %s (%d bytes); using all %d bytes.",
            length,
            file_name,
            len(data),
            len(data),
        )
        return data

    def _target_address(self):
        """
        Return the global address for read, write, verify and erase.

        Resolve --offset against the flash start. Abort when --address
        looks like an offset, i.e. lies below the flash start.
        """
        flash_start = self.stm32.flash_start
        base = flash_start
        if base is None:
            base = bootloader.Stm32Bootloader.FLASH_START_DEFAULT

        offset = self.configuration.offset
        if offset is not None:
            flash = self.stm32.device.flash if self.stm32.device else None
            if flash is not None and flash.size is not None and offset >= flash.size:
                logger.error(
                    "Offset 0x%X is beyond the end of flash memory (size 0x%X).",
                    offset,
                    flash.size,
                )
                sys.exit(1)
            return base + offset

        address = self.configuration.address
        if address is None:
            return base

        uses_address = (
            self.configuration.write
            or self.configuration.verify
            or self.configuration.read
            or (self.configuration.erase and self.configuration.length is not None)
        )
        if uses_address and flash_start is not None and address < flash_start:
            logger.error(
                "Address 0x%08X is below the flash start 0x%08X; "
                "use --offset 0x%X for an offset inside flash memory.",
                address,
                flash_start,
                address,
            )
            sys.exit(1)
        return address

    def reset(self):
        """Reset the microcontroller."""
        self.stm32.reset_from_flash()

    def detect_device(self) -> None:
        """Detect the STM32 device type by querying bootloader and regs."""
        boot_version = self.stm32.get()
        logger.info("Bootloader version: 0x%X", boot_version)
        self.stm32.detect_device()
        if self.stm32.device.bootloader_id is not None:
            logger.info("Bootloader ID: 0x%02X", self.stm32.device.bootloader_id)
        logger.info("Chip ID: 0x%03X", self.stm32.device.product_id)
        logger.info("Chip model: %s", self.stm32.device.device_name)

    def read_device_uid(self):
        """Show chip UID."""
        try:
            device_uid = self.stm32.get_uid()
        except bootloader.CommandError as e:
            logger.warning("Something was wrong with reading chip UID: %s", e)
            return

        if device_uid != bootloader.Stm32Bootloader.UID_NOT_SUPPORTED:
            device_uid_string = self.stm32.format_uid(device_uid)
            logger.info("Device UID: %s", device_uid_string)

    def read_flash_size(self):
        """Show chip flash size."""
        try:
            flash_size = self.stm32.get_flash_size()
        except bootloader.CommandError as e:
            logger.warning("Something was wrong with reading chip flash size: %s", e)
            return

        if flash_size != bootloader.Stm32Bootloader.FLASH_SIZE_UNKNOWN:
            logger.info("Flash size: %d kiB", flash_size)

    @staticmethod
    def _get_progress_bar(no_progress=False):
        if no_progress or not progress_bar:
            return None

        return bootloader.ShowProgress(progress_bar)


class _BelowWarningFilter(logging.Filter):  # pylint: disable=too-few-public-methods
    """Pass only records below WARNING level."""

    def filter(self, record):
        return record.levelno < logging.WARNING


class _ConsoleHandler(logging.StreamHandler):
    """Write to the current sys.stdout or sys.stderr, even if replaced."""

    # pylint: disable-next=super-init-not-called
    def __init__(self, stream_name):
        # Skip StreamHandler.__init__: it assigns to the stream property.
        logging.Handler.__init__(self)  # pylint: disable=non-parent-init-called
        self.stream_name = stream_name

    @property
    def stream(self):
        """Return the stream that sys currently uses."""
        return getattr(sys, self.stream_name)


def _configure_logging(verbosity):
    """
    Send stm32loader's log output to the console.

    Info and debug messages go to stdout, warnings and errors to stderr.
    """
    package_logger = logging.getLogger("stm32loader")
    for handler in _console_handlers:
        package_logger.removeHandler(handler)

    formatter = logging.Formatter("%(message)s")
    stdout_handler = _ConsoleHandler("stdout")
    stdout_handler.addFilter(_BelowWarningFilter())
    stderr_handler = _ConsoleHandler("stderr")
    stderr_handler.setLevel(logging.WARNING)
    _console_handlers[:] = [stdout_handler, stderr_handler]
    for handler in _console_handlers:
        handler.setFormatter(formatter)
        package_logger.addHandler(handler)

    if verbosity <= 0:
        package_logger.setLevel(logging.WARNING)
    elif verbosity <= args.DEFAULT_VERBOSITY:
        package_logger.setLevel(logging.INFO)
    else:
        package_logger.setLevel(logging.DEBUG)
    package_logger.propagate = False


def main(*arguments, **kwargs):
    """
    Parse arguments and execute tasks.

    Default usage is to supply *sys.argv[1:].
    """
    try:
        loader = Stm32Loader()
        loader.parse_arguments(arguments)
        _configure_logging(loader.configuration.verbosity)
        loader.connect()
        try:
            loader.detect_device()
            loader.read_device_uid()
            loader.read_flash_size()
            loader.perform_commands()
        finally:
            loader.reset()
    except SystemExit:
        if not kwargs.get("avoid_system_exit", False):
            raise


if __name__ == "__main__":
    main(*sys.argv[1:])
