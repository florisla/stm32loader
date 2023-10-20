
from stm32loader.devices import DEVICES
from stm32loader.bootloader import CHIP_IDS
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
]

KNOWN_RAM_EXCEPTIONS = [
    # Most of these have belong to the 'known duplicate' category,
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


def test_only_specific_names_occur_twice():
    all_names = set()
    for dev in DEVICES.values():
        if dev.device_name in all_names:
            assert dev.device_name in KNOWN_DUPLICATE_DEVICE_NAMES, dev.device_name
        all_names.add(dev.device_name)


def test_product_id_and_bootloader_id_match_device_properties():
    for ids, dev in DEVICES.items():
        device_id, bootloader_id = ids
        assert dev.product_id == device_id
        assert dev.bootloader_id == bootloader_id


def test_ram_size_is_multiple_of_256():
    for dev in DEVICES.values():
        if dev.ram_size == 0:
            continue

        assert isinstance(dev.ram_size, int)
        assert dev.ram_size > 0, f"{dev} ram size not None but still too low: {dev.ram_size}"
        assert dev.ram_size % 256 == 0, f"{dev} ram size not a multiple of 256: {dev.ram_size}"


def test_system_memory_size_multiple_of_64():
    for dev in DEVICES.values():
        if dev.system_memory_size == 0:
            continue

        assert isinstance(dev.system_memory_size, int)
        assert dev.system_memory_size > 0, f"{dev} flash size not None but still 0: {dev.system_memory_size}"
        assert dev.system_memory_size % 64 == 0, f"{dev} flash size not a multiple of 64: {dev.system_memory_size}"


def test_device_name_does_not_contain_underscore():
    for dev in DEVICES.values():
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


def test_stm32flash_ram_addresses_match():
    for device in DEVICES.values():
        ref = None
        for _ref in STM32FLASH_DEVICES:
            if _ref["product_id"] == device.product_id:
                ref = _ref
                break

        if ref is None:
            # not found
            continue

        if device.product_id in KNOWN_RAM_EXCEPTIONS:
            continue

        if device.ram is None:
            assert ref["ram_start"] == ref["ram_end"], f"RAM size not 0 for device '{device.device_name}' 0x{device.product_id:03X}"
            continue

        if isinstance(device.ram[0], tuple):
            continue

        # print(hex(device.product_id), device, device.ram, ref)
        assert device.ram[0] == ref["ram_start"], f"RAM start differs for device: '{device.device_name}' 0x{device.product_id:03X}: 0x{device.ram[0]:08X} vs 0x{ref['ram_start']:08X}."
        assert device.ram[1] == ref["ram_end"], f"RAM end differs for device: '{device.device_name}' 0x{device.product_id:03X}: 0x{device.ram[1]:08X} vs 0x{ref['ram_end']:08X}."
