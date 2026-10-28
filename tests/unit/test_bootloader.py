"""Unit tests for the Stm32Loader class."""

from unittest.mock import MagicMock

import pytest

from stm32loader import bootloader as Stm32
from stm32loader.bootloader import PageIndexError, Stm32Bootloader
from stm32loader.device_info import DeviceInfo
from stm32loader.devices import DEVICES

# pylint: disable=missing-docstring, redefined-outer-name


@pytest.fixture
def connection():
    connection = MagicMock()
    connection.read.return_value = [Stm32Bootloader.Reply.ACK]
    return connection


@pytest.fixture
def write(connection):
    connection.write.written_data = bytearray()

    def log_written_data(data):
        connection.write.written_data.extend(data)

    def data_was_written(data):
        return data in connection.write.written_data

    connection.write.data_was_written = data_was_written
    connection.write.side_effect = log_written_data
    return connection.write


@pytest.fixture
def bootloader(connection):
    # STM32F358xx
    device = DEVICES.get((0x422, 0x50))
    assert device is not None, "Device not found in DEVICES mapping"
    return Stm32Bootloader(connection, device=device)


def test_constructor_with_connection_none_passes():
    Stm32Bootloader(connection=None)


def test_constructor_does_not_use_connection_directly(connection):
    Stm32Bootloader(connection)
    assert not connection.method_calls


def test_constructor_with_verbosity_warns_deprecation(connection):
    with pytest.deprecated_call(match="verbosity is ignored"):
        Stm32Bootloader(connection, verbosity=5)


def test_write_without_data_sends_no_bytes(bootloader, write):
    bootloader.write()
    assert not write.written_data


def test_write_with_bytes_sends_bytes_verbatim(bootloader, write):
    bootloader.write(b"\x00\x11")
    assert write.data_was_written(b"\x00\x11")


def test_write_with_integers_sends_integers_as_bytes(bootloader, write):
    bootloader.write(0x03, 0x0A)
    assert write.data_was_written(b"\x03\x0a")


def test_write_and_ack_with_nack_response_raises_commandexception(bootloader):
    bootloader.connection.read = MagicMock()
    bootloader.connection.read.return_value = [Stm32Bootloader.Reply.NACK]
    with pytest.raises(Stm32.CommandError, match="custom message"):
        bootloader.write_and_ack("custom message", 0x00)


def test_write_memory_with_length_higher_than_256_raises_data_length_error(bootloader):
    with pytest.raises(
        Stm32.DataLengthError, match=r"Can not write more than 256 bytes at once\."
    ):
        bootloader.write_memory(0, [1] * 257)


def test_write_memory_with_zero_bytes_does_not_send_anything(bootloader, connection):
    bootloader.write_memory(0, b"")
    assert not connection.method_calls


def test_write_memory_with_single_byte_sends_four_data_bytes_padded_with_0xff(bootloader, write):
    bootloader.write_memory(0, b"1")
    assert write.data_was_written(b"1\xff\xff\xff")


def test_write_memory_sends_correct_number_of_bytes(bootloader, write):
    bootloader.write_memory(0, bytearray([0] * 4))
    # command byte, control byte, 4 address bytes, address checksum,
    # length byte, 4 data bytes, checksum byte
    byte_count = 2 + 4 + 1 + 1 + 4 + 1
    assert len(write.written_data) == byte_count


def test_read_memory_with_length_higher_than_256_raises_data_length_error(bootloader):
    with pytest.raises(
        Stm32.DataLengthError, match=r"Can not read more than 256 bytes at once\."
    ):
        bootloader.read_memory(0, length=257)


def test_read_memory_sends_address_with_checksum(bootloader, write):
    bootloader.read_memory(0x0F, 4)
    assert write.data_was_written(b"\x00\x00\x00\x0f\x0f")


def test_read_memory_sends_length_with_checksum(bootloader, write):
    bootloader.read_memory(0, 0x0F + 1)
    assert write.data_was_written(b"\x0f\xf0")


def test_command_sends_command_and_control_bytes(bootloader, write):
    bootloader.command(0x01, "bogus command")
    assert write.data_was_written(b"\x01\xfe")


def test_reset_from_system_memory_sends_command_synchronize(bootloader, write):
    bootloader.reset_from_system_memory()
    synchro_command = Stm32Bootloader.Command.SYNCHRONIZE
    assert write.data_was_written(bytearray([synchro_command]))


def test_encode_address_returns_correct_bytes_with_checksum():
    # pylint:disable=protected-access
    encoded_address = Stm32Bootloader._encode_address(0x04030201)
    assert bytes(encoded_address) == b"\x04\x03\x02\x01\x04"


def test_erase_memory_without_pages_sends_global_erase(bootloader, write):
    bootloader.erase_memory()
    assert write.data_was_written(b"\xff\x00")


def test_erase_memory_with_pages_sends_sector_count_and_eight_bit_page_indices(bootloader, write):
    bootloader.erase_memory([0x11, 0x12, 0x13, 0x14])
    assert write.data_was_written(b"\x03")
    assert write.data_was_written(b"\x11\x12\x13\x14")


def test_extended_erase_memory_with_pages_sends_sector_count_and_sixteen_bit_page_indices(
    bootloader, write
):
    bootloader.extended_erase_memory([0x11, 0x12, 0x13, 0x14])
    assert write.data_was_written(b"\x00\x03")
    assert write.data_was_written(b"\x00\x11\x00\x12\x00\x13\x00\x14")


def test_erase_memory_with_pages_sends_sector_addresses_with_checksum(bootloader, write):
    bootloader.erase_memory([0x01, 0x02, 0x04, 0x08])
    print(write.written_data)
    assert write.data_was_written(b"\x01\x02\x04\x08\x0c")


def test_erase_memory_with_more_than_255_pages_sends_multiple_erase_commands(bootloader, write):
    bootloader.erase_memory(list(range(256)))

    erase_command = bytes([0x43, 0x43 ^ 0xFF])
    assert write.written_data.count(erase_command) == 2
    # First batch: 255 pages (count - 1 = 254), second batch: page 255 only.
    assert write.data_was_written(bytes([254]) + bytes(range(255)))
    assert write.data_was_written(bytes([0, 255]))


def test_erase_memory_with_page_index_above_255_raises_page_index_error(bootloader):
    with pytest.raises(Stm32.PageIndexError, match="too large for the ERASE command"):
        bootloader.erase_memory([1, 256])


def test_erase_memory_with_empty_pages_raises_page_index_error(bootloader, write):
    with pytest.raises(Stm32.PageIndexError, match="No pages to erase"):
        bootloader.erase_memory([])
    assert not write.written_data


def test_extended_erase_memory_with_empty_pages_raises_page_index_error(bootloader, write):
    with pytest.raises(Stm32.PageIndexError, match="No pages to erase"):
        bootloader.extended_erase_memory([])
    assert not write.written_data


def test_extended_erase_memory_without_pages_sends_global_mass_erase(bootloader, write):
    bootloader.extended_erase_memory()
    assert write.data_was_written(b"\xff\xff\x00")


def test_extended_erase_memory_with_page_count_higher_than_65535_raises_page_index_error(
    bootloader,
):
    with pytest.raises(
        Stm32.PageIndexError, match="Can not erase more than 65535 pages at once."
    ):
        bootloader.extended_erase_memory([1] * 65536)


def test_extended_erase_memory_with_pages_sends_two_byte_sector_count(bootloader, write):
    bootloader.extended_erase_memory([0x11, 0x12, 0x13, 0x14])
    assert write.data_was_written(b"\x00\x03")


def test_extended_erase_with_pages_sends_two_byte_sector_addresses_with_single_byte_checksum(
    bootloader, write
):
    bootloader.extended_erase_memory([0x01, 0x02, 0x04, 0x0FF0])
    assert write.data_was_written(b"\x00\x01\x00\x02\x00\x04\x0f\xf0\xfb")


def test_write_protect_sends_command_page_addresses_and_checksum(bootloader, write):
    bootloader.get_flash_size = MagicMock()
    bootloader.get_flash_size.return_value = 16
    bootloader.write_protect([0x01, 0x08])
    assert write.data_was_written(b"\x63\x9c\x01\x01\x08\x08\x7f"), write.written_data


def test_write_protect_fails_when_no_device(bootloader):
    bootloader = Stm32Bootloader(connection, device_family="F0", device=None)
    with pytest.raises(
        Stm32.Stm32LoaderError,
        match="Device type must be detected before write protection can be enabled.",
    ):
        bootloader.write_protect([0x01, 0x08])


def test_write_protect_fails_when_not_supported(bootloader):
    device = DeviceInfo(
        device_family="F0", device_name="STM32F012", pid=0, bid=0, write_protect_supported=False
    )
    bootloader = Stm32Bootloader(connection, device_family="F0", device=device)
    bootloader.get_flash_size = MagicMock()
    bootloader.get_flash_size.return_value = 16
    with pytest.raises(
        Stm32.Stm32LoaderError,
        match="Write protection support for 'STM32F012' not currently implemented.",
    ):
        bootloader.write_protect([0x01, 0x08])


def test_write_protect_fails_on_invalid_sector_index(bootloader):
    bootloader.get_flash_size = MagicMock()
    bootloader.get_flash_size.return_value = 16
    with pytest.raises(Stm32.PageIndexError):
        bootloader.write_protect([0x01, 0x08, 0x100])


def test_write_protect_fails_on_too_many_sectors(bootloader):
    bootloader.get_flash_size = MagicMock()
    bootloader.get_flash_size.return_value = 16
    with pytest.raises(Stm32.DataLengthError):
        bootloader.write_protect(list(range(256)) + [0, 1])


def test_write_protect_fails_on_no_flash_info(connection, bootloader):
    device = DeviceInfo(
        device_family="F0", device_name="STM32F012", pid=0, bid=0, write_protect_supported=True
    )
    device.flash = None
    bootloader = Stm32Bootloader(connection, device_family="F0", device=device)

    bootloader.get_flash_size = MagicMock()
    bootloader.get_flash_size.return_value = 16
    with pytest.raises(
        Stm32.Stm32LoaderError, match="Device flash info is missing for family 'F0'"
    ):
        bootloader.write_protect()


def test_write_protect_fails_on_no_flash_sector_info(connection, bootloader):
    device = DeviceInfo(
        device_family="F0", device_name="STM32F012", pid=0, bid=0, write_protect_supported=True
    )
    device.flash = MagicMock()
    device.flash.num_sectors = MagicMock(return_value=None)
    bootloader = Stm32Bootloader(connection, device_family="F0", device=device)

    bootloader.get_flash_size = MagicMock()
    bootloader.get_flash_size.return_value = 16
    with pytest.raises(
        Stm32.Stm32LoaderError, match="Device flash sector info is missing for device 'STM32F012'"
    ):
        bootloader.write_protect()


def test_write_protect_no_pages_specified(connection, write):
    device = DEVICES.get((0x417, 0xC0))
    assert device is not None, "Device not found in DEVICES mapping"

    bootloader = Stm32Bootloader(connection, device_family="L0", device=device)
    bootloader.get_flash_size = MagicMock()
    bootloader.get_flash_size.return_value = 8
    # bootloader.write = write
    bootloader.write_protect()
    assert write.data_was_written(b"\x63"), write.written_data
    # Write protect sector size is 4KB, flash size is 64KB
    # 64KB / 4KB = 16 sectors (index 1)
    # Checksum is 0x0f
    sectors = bytes(range(0, 16))
    assert write.data_was_written(b"\x63\x9c\x0f" + sectors + b"\x0f\x7f"), write.written_data


def test_write_unprotect_sends_command(bootloader, write):
    bootloader.write_unprotect()
    assert write.data_was_written(b"\x73"), write.written_data
    assert write.data_was_written(bytearray([Stm32Bootloader.Command.SYNCHRONIZE])), (
        write.written_data
    )


def test_verify_data_with_identical_data_passes():
    Stm32Bootloader.verify_data(b"\x05", b"\x05")


def test_verify_different_byte_count_raises_verify_error_complaining_about_length_difference():
    with pytest.raises(
        Stm32.DataMismatchError, match=r"Data length does not match.*2.*vs.*1.*bytes"
    ):
        Stm32Bootloader.verify_data(b"\x05\x06", b"\x01")


def test_verify_non_identical_data_raises_verify_error_complaining_about_mismatched_byte():
    with pytest.raises(
        Stm32.DataMismatchError,
        match=r"Verification data does not match read data.*mismatch.*0x1.*0x6.*0x7",
    ):
        Stm32Bootloader.verify_data(b"\x05\x06", b"\x05\x07")


@pytest.mark.parametrize(
    "pid_bid, uid_address",
    [
        ((0x412, None), 0x_1FFF_F7E8),
        ((0x432, 0x50), 0x_1FFF_F7AC),
        ((0x452, 0x90), 0x_1FF0_F420),
    ],
    ids=("F1", "F3", "F7"),
)
def test_get_uid_for_known_device_reads_at_correct_address(connection, pid_bid, uid_address):
    device = DEVICES.get(pid_bid)
    bootloader = Stm32Bootloader(connection, device=device)
    bootloader.read_memory = MagicMock()

    bootloader.get_uid()
    bootloader.read_memory.assert_called_once_with(uid_address, 12)


def test_get_uid_for_family_without_uid_returns_uid_not_supported(connection):
    device = DEVICES.get((0x443, 0x51))
    bootloader = Stm32Bootloader(connection, device=device)
    assert bootloader.UID_NOT_SUPPORTED == bootloader.get_uid()


@pytest.mark.parametrize(
    "uid_string",
    [
        (Stm32Bootloader.UID_NOT_SUPPORTED, "UID not supported in this part"),
        (Stm32Bootloader.UID_ADDRESS_UNKNOWN, "UID address unknown"),
        (
            bytearray(b"\x12\x34\x56\x78\x9a\xbc\xde\x01\x12\x34\x56\x78"),
            "3412-7856-01DEBC9A-78563412",
        ),
    ],
)
def test_format_uid_returns_correct_string(bootloader, uid_string):
    uid, expected_description = uid_string
    description = bootloader.format_uid(uid)
    assert description == expected_description


FLASH = 0x_0800_0000


def test_get_pages_from_range_with_invalid_start_address_raises_page_index_error(bootloader):
    with pytest.raises(
        PageIndexError, match=".*start address should be at a flash page boundary.*"
    ):
        bootloader.pages_from_range(FLASH + 10, FLASH + 1024)


def test_get_pages_from_range_with_flash_start_returns_single_page(bootloader):
    pages = bootloader.pages_from_range(FLASH, FLASH + 2048)
    assert pages == [0]


def test_get_pages_from_range_with_end_too_small_raises_page_index_error(bootloader):
    with pytest.raises(
        PageIndexError, match="Erase .* address should be at a flash page boundary:.*0400.*0800"
    ):
        bootloader.pages_from_range(FLASH, FLASH + 1024)


def test_get_pages_from_large_range_returns_multiple_pages(bootloader):
    pages = bootloader.pages_from_range(FLASH + 4 * 1024, FLASH + 20 * 1024)
    assert pages == list(range(2, 10))


def test_get_pages_from_range_below_flash_start_raises_page_index_error(bootloader):
    with pytest.raises(PageIndexError, match="below the flash start 0x08000000"):
        bootloader.pages_from_range(0, 2048)


def test_get_pages_from_range_beyond_flash_end_raises_page_index_error(bootloader):
    flash_end = bootloader.device.flash.end
    with pytest.raises(PageIndexError, match="beyond the flash end"):
        bootloader.pages_from_range(flash_end - 2048, flash_end + 2048)


def test_get_pages_from_range_without_device_assumes_default_flash_start(connection):
    bootloader = Stm32Bootloader(connection, device_family="F1")
    pages = bootloader.pages_from_range(FLASH + 1024, FLASH + 3 * 1024)
    assert pages == [1, 2]


@pytest.fixture
def f4_bootloader(connection):
    # STM32F40xxx/41xxx: sectors of 4x16K, 1x64K, 7x128K.
    return Stm32Bootloader(connection, device=DEVICES[(0x413, 0x31)])


@pytest.mark.parametrize(
    "start, end, expected_pages",
    [
        (FLASH, FLASH + 16 * 1024, [0]),
        (FLASH + 16 * 1024, FLASH + 128 * 1024, [1, 2, 3, 4]),
        (FLASH + 128 * 1024, FLASH + 384 * 1024, [5, 6]),
    ],
)
def test_get_pages_from_range_with_mixed_sector_sizes(f4_bootloader, start, end, expected_pages):
    assert f4_bootloader.pages_from_range(start, end) == expected_pages


def test_get_pages_from_range_with_mixed_sector_sizes_requires_sector_boundary(f4_bootloader):
    # FLASH + 96K lies inside sector 4, which spans 64K-128K.
    with pytest.raises(PageIndexError, match="end address should be at a flash sector boundary"):
        f4_bootloader.pages_from_range(FLASH, FLASH + 96 * 1024)


def test_get_flash_size_for_standard_family(connection):
    device = DEVICES.get((0x412, None))
    bootloader = Stm32Bootloader(connection, device=device)
    bootloader.read_memory = MagicMock(return_value=b"\x80\x00")

    assert bootloader.get_flash_size() == 128
    bootloader.read_memory.assert_called_once_with(0x_1FFF_F7E0, 2)


def test_get_uid_for_standard_family(connection):
    device = DEVICES.get((0x412, None))
    bootloader = Stm32Bootloader(connection, device=device)
    bootloader.read_memory = MagicMock(return_value=b"some uid 12b")

    assert bootloader.get_uid() == b"some uid 12b"
    bootloader.read_memory.assert_called_once_with(0x_1FFF_F7E8, 12)


@pytest.mark.parametrize(
    "optr, page_size",
    [
        (0xFFEFF8AA, 2048),  # DBANK set: dual bank
        (0xFFAFF8AA, 4096),  # DBANK clear: single bank
    ],
)
def test_update_flash_bank_mode_sets_g47x_page_size_from_dbank(connection, optr, page_size):
    device = DEVICES.get((0x469, 0xD5))
    bootloader = Stm32Bootloader(connection, device=device)
    bootloader.read_memory = MagicMock(return_value=bytearray(optr.to_bytes(4, "little")))
    bootloader.update_flash_bank_mode()
    bootloader.read_memory.assert_called_once_with(0x1FFF7800, 4)
    assert bootloader.flash_page_size == page_size


def test_update_flash_bank_mode_keeps_page_size_when_option_read_fails(connection):
    device = DEVICES.get((0x469, 0xD5))
    bootloader = Stm32Bootloader(connection, device=device)
    bootloader.read_memory = MagicMock(side_effect=Stm32.CommandError("NACK"))
    bootloader.update_flash_bank_mode()
    assert bootloader.flash_page_size == 2048


def test_update_flash_bank_mode_ignores_g4_without_dual_bank(connection):
    device = DEVICES.get((0x468, 0xD4))
    bootloader = Stm32Bootloader(connection, device=device)
    bootloader.read_memory = MagicMock()
    bootloader.update_flash_bank_mode()
    bootloader.read_memory.assert_not_called()
    assert bootloader.flash_page_size == 2048
