
from stm32loader.devices import DEVICES

KNOWN_DUPLICATE_DEVICE_NAMES = [
    "STM32F2xxxx",
    "STM32F40xxx/41xxx",
    "STM32F42xxx/43xxx",
    "STM32F74xxx/75xxx",
    "STM32L07xxx/08xxx",
    "STM32L47xxx/48xxx",
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
