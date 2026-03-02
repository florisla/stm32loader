from pathlib import Path

from stm32loader.bootloader import Stm32Bootloader
from stm32loader.emulated.fake import FakeConfiguration, FakeConnection
from stm32loader.main import Stm32Loader

FIRMWARE_FILE = Path(__file__).parent / "../../firmware/generic_boot20_pc13.binary.bin"


def test_erase_write_verify_passes():
    loader = Stm32Loader()
    loader.configuration = FakeConfiguration(
        erase=True, write=True, verify=True, firmware_file=FIRMWARE_FILE, family=None
    )
    loader.connection = FakeConnection()
    loader.stm32 = Stm32Bootloader(loader.connection, device_family="F1", verbosity=5)

    loader.detect_device()
    loader.read_device_uid()
    loader.read_flash_size()
    loader.perform_commands()
