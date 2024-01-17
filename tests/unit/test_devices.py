
import pytest

from stm32loader.devices import DEVICES, DEVICE_FAMILIES, DeviceFamily
from stm32loader.bootloader import CHIP_IDS, Stm32Bootloader
from devices_stm32flash import DEVICES as STM32FLASH_DEVICES


KNOWN_DUPLICATE_DEVICE_NAMES = [
    "STM32F2xxxx",
    "STM32F40xxx/41xxx",
    "STM32F42xxx/43xxx",
    "STM32F74xxx/75xxx",
    "STM32L07xxx/08xxx",
    "STM32L47xxx/48xxx",
    "STM32F10xxx",
    "BlueNRG-1",
    "BlueNRG-2",
    "STM32W"
]

KNOWN_RAM_EXCEPTIONS = [
    # Most of these belong to the 'known duplicate' category,
    # they share the same product ID (with differing bootloader ID).
    # The others received a comment in the device table.
    0x442,
    0x448,
    0x432,
    0x413,
    0x456,
    0x447,
    0x464,
    0x415,
]


def test_only_specific_device_names_occur_twice():
    all_names = set()
    for (product_id, bootloader_id), dev in DEVICES.items():
        if bootloader_id is None:
            continue
        if dev.device_name in all_names:
            assert dev.device_name in KNOWN_DUPLICATE_DEVICE_NAMES, dev.device_name
        all_names.add(dev.device_name)


@pytest.mark.parametrize(
    "ids",
    DEVICES.keys(),
    ids=lambda x: f"{x[0]}-{x[1]}",
)
def test_product_id_and_bootloader_id_match_device_properties(ids):
    dev = DEVICES[ids]
    device_id, bootloader_id = ids
    assert dev.product_id == device_id
    if bootloader_id is not None:
        assert dev.bootloader_id == bootloader_id


@pytest.mark.parametrize(
    "dev",
    DEVICES.values(),
    ids=lambda dev: str(dev).replace(" ", "-"),
)
def test_ram_size_is_multiple_of_256(dev):
    if dev.ram_size == 0:
        return

    assert isinstance(dev.ram_size, int)
    assert dev.ram_size > 0, f"{dev} ram size not None but still too low: {dev.ram_size}"
    assert dev.ram_size % 256 == 0, f"{dev} ram size not a multiple of 256: {dev.ram_size}"


@pytest.mark.parametrize(
    "dev",
    DEVICES.values(),
    ids=lambda dev: str(dev).replace(" ", "-"),
)
def test_flash_size_multiple_of_16k(dev):
    if dev.flash_size == 0:
        return

    assert isinstance(dev.flash_size, int)
    assert dev.flash_size > 0, f"{dev} flash size not None but still too low: {dev.flash_size}"
    assert dev.flash_size % (16 * 1024) == 0, f"{dev} flash size not a multiple of 64: {dev.flash_size}"


@pytest.mark.parametrize(
    "dev",
    DEVICES.values(),
    ids=lambda dev: str(dev).replace(" ", "-"),
)
def test_system_memory_size_multiple_of_64(dev):
    if dev.system_memory_size == 0:
        return

    assert isinstance(dev.system_memory_size, int)
    assert dev.system_memory_size > 0, f"{dev} system memory size not None but still too low: {dev.system_memory_size}"
    assert dev.system_memory_size % 64 == 0, f"{dev} system memory size not a multiple of 64: {dev.system_memory_size}"


@pytest.mark.parametrize(
    "dev",
    DEVICES.values(),
    ids=lambda dev: str(dev).replace(" ", "-"),
)
def test_device_name_does_not_contain_underscore(dev):
    assert "_" not in dev.device_name, dev.device_name


def test_existing_product_ids_are_present_in_devices():
    all_product_ids = set(dev.product_id for dev in DEVICES.values())
    chip_ids = set(CHIP_IDS)
    unknown_chip_ids = chip_ids - all_product_ids
    assert len(unknown_chip_ids) == 0, unknown_chip_ids


def test_stm32flash_product_ids_are_present_in_devices():
    all_product_ids = set(dev.product_id for dev in DEVICES.values())
    chip_ids = set(dev["product_id"] for dev in STM32FLASH_DEVICES)
    unknown_chip_ids = chip_ids - all_product_ids
    assert len(unknown_chip_ids) == 0, unknown_chip_ids


@pytest.mark.parametrize(
    "device",
    DEVICES.values(),
    ids=lambda device: str(device).replace(" ", "-"),
)
def test_stm32flash_device_names_match(device):
    stm32flash_device = None
    for dev in STM32FLASH_DEVICES:
        if dev["product_id"] == device.product_id:
            stm32flash_device = dev
            break

    # Some devices don't exist in STM32Flash.
    if not stm32flash_device and device.product_id in [0x443, 0x453, 0x474, 0x484, 0x492, 0x455, 0x481, 0x003, 0x00F, 0x0023, 0x002F, 0x801]:
        return

    # Known / reviewed deviating names.
    if device.product_id in [
        0x440, 0x442, 0x445, 0x448, 0x412, 0x410, 0x414, 0x420, 0x428, 0x418, 0x430, 0x432,
        0x422, 0x439, 0X438, 0x446, 0x467, 0x495, 0x641, 0x9A8, 0x9B0,
    ]:
        return

    assert stm32flash_device, f"{device.device_name} 0x{device.product_id:03X}"
    assert stm32flash_device["device_name"] == device.device_name, f"{device.device_name} 0x{device.product_id:03X}"


@pytest.mark.parametrize(
    "device",
    DEVICES.values(),
    ids=lambda device: str(device).replace(" ", "-"),
)
def test_stm32flash_ram_addresses_match(device):
    ref = None
    for _ref in STM32FLASH_DEVICES:
        if _ref["product_id"] == device.product_id:
            ref = _ref
            break

    if ref is None:
        # not found
        return

    if device.product_id in KNOWN_RAM_EXCEPTIONS:
        return

    if device.ram is None:
        assert ref["ram_start"] == ref["ram_end"], f"RAM size not 0 for device '{device.device_name}' 0x{device.product_id:03X}"
        return

    if isinstance(device.ram[0], tuple):
        return

    # print(hex(device.product_id), device, device.ram, ref)
    assert device.ram[0] == ref["ram_start"], f"RAM start differs for device: '{device.device_name}' 0x{device.product_id:03X}: 0x{device.ram[0]:08X} vs 0x{ref['ram_start']:08X}."
    assert device.ram[1] == ref["ram_end"], f"RAM end differs for device: '{device.device_name}' 0x{device.product_id:03X}: 0x{device.ram[1]:08X} vs 0x{ref['ram_end']:08X}."


def test_family_uid_address_matches_existing():
    for family_code, uid_address in Stm32Bootloader.UID_ADDRESS.items():
        if family_code == "NRG":
            continue
        family = DeviceFamily[family_code]
        family_uid_address = DEVICE_FAMILIES[family].uid_address
        assert uid_address == family_uid_address, (
            f"Device family UID address does not match: '{family_code}': 0x{uid_address:08X} vs 0x{family_uid_address:08X}."
        )


def test_family_flash_size_address_matches_existing():
    for family_code, size_address in Stm32Bootloader.FLASH_SIZE_ADDRESS.items():
        if family_code == "NRG":
            continue
        family = DeviceFamily[family_code]
        family_size_address = DEVICE_FAMILIES[family].flash_size_address
        assert size_address == family_size_address, (
            f"Device family flash size address does not match: '{family_code}': 0x{size_address:08X} vs 0x{family_size_address:08X}."
        )


def test_family_transfer_size_matches_existing():
    for family_code, transfer_size in Stm32Bootloader.DATA_TRANSFER_SIZE.items():
        if family_code in ["default", "NRG"]:
            continue
        family = DeviceFamily[family_code]
        family_transfer_size = DEVICE_FAMILIES[family].transfer_size
        assert transfer_size == family_transfer_size, (
            f"Device family transfer size does not match: '{family_code}': 0x{transfer_size:08X} vs 0x{family_transfer_size:08X}."
        )
