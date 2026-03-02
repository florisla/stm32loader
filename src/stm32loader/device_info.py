"""Hold information about different STM32 devices."""

from stm32loader.device_family import DEVICE_FAMILIES, DeviceFamily, DeviceFlag

kB = 1024  # pylint: disable=invalid-name


class DeviceInfo:  # pylint: disable=too-many-instance-attributes
    """Hold info about"""

    def __init__(  # pylint: disable=too-many-positional-arguments,too-many-arguments
        self,
        device_family,
        device_name,
        pid,
        bid,
        variant=None,
        line=None,
        ram=None,
        flash=None,
        system=None,
        option=None,
        bootloader_id_address=None,
        flags=DeviceFlag.NONE,
    ):
        self.family = DEVICE_FAMILIES[DeviceFamily[device_family]]
        self.device_name = device_name
        self.product_id = pid
        self.bootloader_id = bid
        self.variant = variant
        self.product_line = line
        self.ram = ram
        self.flash = Flash(*(flash or []))
        self.system_memory = system
        self.option_bytes = option
        self.flags = flags | self.family.family_default_flags
        self.bootloader_id_address = bootloader_id_address or self.family.bootloader_id_address

    @property
    def ram_size(self):
        """Return the device's RAM memory size in bytes."""
        if self.ram is None:
            return 0

        assert isinstance(self.ram, tuple)

        if isinstance(self.ram[0], tuple):
            # Multiple ranges.
            ram_size = 0
            for ram_range in self.ram:
                ram_size += ram_range[1] - ram_range[0]

            return ram_size

        start, end = self.ram
        ram_size = end - start
        return ram_size

    @property
    def flash_size(self):
        """Return the device's flash memory size in bytes."""
        return self.flash.size

    @property
    def system_memory_size(self):
        """Return the size of the system memory in bytes."""
        if self.system_memory is None:
            return 0

        assert isinstance(self.system_memory, tuple)

        if isinstance(self.system_memory[0], tuple):
            # Multiple ranges.
            flash_size = 0
            for flash_range in self.system_memory:
                flash_size += flash_range[1] - flash_range[0]

            return flash_size

        start, end = self.system_memory
        flash_size = end - start
        return flash_size

    def __str__(self):
        name = self.device_name
        if self.variant:
            name += f"-{self.variant}"
        if self.product_line:
            name += f"-{self.product_line}"
        return name

    def __repr__(self):
        return f"DeviceInfo(device_name={self.device_name!r}, variant={self.product_line!r})"


class Flash:  # pylint: disable=too-few-public-methods
    """Represent info about a device's flash layout."""

    # RM0090 4 sectors of 16 Kbytes, 1 sector of 64 Kbytes,
    # 7 sectors of 128 Kbytes
    F2_F4_PAGE_SIZE = (16 * kB, 16 * kB, 16 * kB, 16 * kB, 64 * kB, 128 * kB, 0)
    # RM0090 4 sectors of 16 Kbytes, 1 sector of 64 Kbytes,
    # 7 sectors of 128 Kbytes  but then per bank
    F4_DUAL_BANK_PAGE_SIZE = (
        16 * kB,
        16 * kB,
        16 * kB,
        16 * kB,
        64 * kB,
        128 * kB,
        128 * kB,
        128 * kB,
        128 * kB,
        16 * kB,
        16 * kB,
        16 * kB,
        16 * kB,
        64 * kB,
        128 * kB,
        0,
    )
    F7_PAGE_SIZE = (32 * kB, 32 * kB, 32 * kB, 32 * kB, 128 * kB, 256 * kB, 0)

    def __init__(self, start=None, end=None, page_size=None, pages_per_sector=None):
        self.start = start
        self.end = end
        self.page_size = page_size
        self.pages_per_sector = pages_per_sector

    @property
    def size(self) -> int:
        """Return the size of the flash memory in bytes."""
        if self.start is None:
            return 0

        return self.end - self.start
