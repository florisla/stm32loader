"""Tests for --address, --offset and --length handling, on the emulated device."""

import logging

import pytest

from stm32loader.bootloader import Stm32Bootloader
from stm32loader.emulated.fake import FakeConfiguration, FakeConnection
from stm32loader.main import Stm32Loader

# pylint: disable=missing-docstring, redefined-outer-name

FLASH = 0x_0800_0000
DATA = bytes((index % 255) + 1 for index in range(4096))


@pytest.fixture
def loader(tmp_path):
    """Return a loader that writes and verifies DATA on the emulated F3 device."""
    firmware_file = tmp_path / "firmware.bin"
    firmware_file.write_bytes(DATA)

    loader = Stm32Loader()
    loader.configuration = FakeConfiguration(
        erase=False,
        write=True,
        verify=True,
        write_protect=False,
        write_unprotect=False,
        firmware_file=firmware_file,
    )
    loader.connection = FakeConnection()
    loader.stm32 = Stm32Bootloader(loader.connection)
    loader.detect_device()
    return loader


def flash_at(loader, address, length):
    offset = address - FLASH
    return bytes(loader.connection.flash_memory[offset : offset + length])


def test_offset_writes_relative_to_flash_start(loader):
    loader.configuration.address = None
    loader.configuration.offset = 0x400

    loader.perform_commands()

    assert flash_at(loader, FLASH + 0x400, len(DATA)) == DATA
    assert flash_at(loader, FLASH, 0x400) == bytes(0x400)


def test_offset_beyond_flash_size_aborts(loader, caplog):
    loader.configuration.address = None
    loader.configuration.offset = loader.stm32.device.flash.size

    with pytest.raises(SystemExit):
        loader.perform_commands()

    assert "beyond the end of flash memory" in caplog.text
    assert not any(loader.connection.flash_memory)


def test_address_below_flash_start_aborts_with_offset_hint(loader, caplog):
    loader.configuration.address = 0x1000

    with pytest.raises(SystemExit):
        loader.perform_commands()

    assert "below the flash start 0x08000000" in caplog.text
    assert "use --offset 0x1000" in caplog.text
    assert not any(loader.connection.flash_memory)


def test_default_address_is_flash_start(loader):
    loader.configuration.address = None

    loader.perform_commands()

    assert flash_at(loader, FLASH, len(DATA)) == DATA


def test_length_smaller_than_file_truncates_with_warning(loader, caplog):
    loader.configuration.length = 1000

    with caplog.at_level(logging.WARNING):
        loader.perform_commands()

    assert "using only the first 1000 bytes" in caplog.text
    assert flash_at(loader, FLASH, 1000) == DATA[:1000]
    assert flash_at(loader, FLASH + 1000, 16) == bytes(16)


def test_length_larger_than_file_writes_whole_file_with_warning(loader, caplog):
    loader.configuration.length = 8192

    with caplog.at_level(logging.WARNING):
        loader.perform_commands()

    assert "using all 4096 bytes" in caplog.text
    assert flash_at(loader, FLASH, len(DATA)) == DATA


def test_erase_and_write_with_length_erases_only_needed_pages(loader, caplog):
    loader.configuration.erase = True
    loader.configuration.length = 4096

    with caplog.at_level(logging.INFO):
        loader.perform_commands()

    # The emulated F3 device has 2 KiB pages.
    assert "Performing partial erase (0x8000000 - 0x8001000, 2 pages)" in caplog.text
    assert "Flash erase 2 pages from 0 to 1" in caplog.text
    assert flash_at(loader, FLASH, len(DATA)) == DATA


def test_erase_with_unaligned_length_aborts_before_touching_device(loader, caplog):
    loader.configuration.erase = True
    loader.configuration.length = 1000

    with pytest.raises(SystemExit):
        loader.perform_commands()

    assert "end address should be at a flash page boundary" in caplog.text
    assert not any(loader.connection.flash_memory)


def test_auto_erase_erases_only_pages_covered_by_data(loader, caplog):
    loader.configuration.auto_erase = True
    loader.configuration.address = FLASH + 0x100

    with caplog.at_level(logging.INFO):
        loader.perform_commands()

    # 4 KiB of data at offset 0x100 spans three 2 KiB pages.
    assert "Performing auto erase (0x8000100 - 0x8001100, 3 pages)" in caplog.text
    assert "Flash erase 3 pages from 0 to 2" in caplog.text
    assert flash_at(loader, FLASH + 0x100, len(DATA)) == DATA


def test_auto_erase_beyond_flash_end_aborts_before_touching_device(loader, caplog):
    loader.configuration.auto_erase = True
    loader.configuration.address = loader.stm32.device.flash.end - 1024

    with pytest.raises(SystemExit):
        loader.perform_commands()

    assert "beyond the flash end" in caplog.text
    assert not any(loader.connection.flash_memory)
