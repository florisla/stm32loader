"""Hold information about different STM32 devices."""

# FIXME: remove and switch to '|' syntax when Python 3.10+ is required.
from typing import Optional, Union

from stm32loader.device_family import DEVICE_FAMILIES, DeviceFamily, DeviceFlag

kB = 1024  # pylint: disable=invalid-name


class DeviceInfo:  # pylint: disable=too-many-instance-attributes
    """Hold info about an STM32 device."""

    write_protect_supported: bool

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
        write_protect_supported=False,
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
        self.write_protect_supported = write_protect_supported

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

    start: Optional[int]
    end: Optional[int]
    page_size: Union[int, list[int], None]
    pages_per_sector: Optional[int]
    max_write_protection_sectors: int

    # RM0090 4 sectors of 16 Kbytes, 1 sector of 64 Kbytes,
    # 7 sectors of 128 Kbytes
    F2_F4_PAGE_SIZE = 4 * [16 * kB] + [64 * kB] + 7 * [128 * kB]

    F4_EXTENDED_PAGE_SIZE = 4 * [16 * kB] + [64 * kB] + 11 * [128 * kB]

    # RM0090 4 sectors of 16 Kbytes, 1 sector of 64 Kbytes,
    # 7 sectors of 128 Kbytes  but then per bank
    F4_DUAL_BANK_PAGE_SIZE = (4 * [16 * kB] + [64 * kB] + 7 * [128 * kB]) * 2

    F7_PAGE_SIZE = 4 * [32 * kB] + [128 * kB] + 7 * [256 * kB]

    def __init__(
        self,
        start=None,
        end=None,
        page_size=None,
        pages_per_sector=None,
        max_write_protection_sectors=63,
    ):  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self.start = start
        self.end = end
        self.page_size = page_size
        self.pages_per_sector = pages_per_sector
        # Some devices, like the STM32F101, use a regular scheme up to 62
        # sectors, and the 63rd "sector" applies to the remaining flash. This
        # parameter allows for devices which have a different max number of
        # sectors.
        self.max_write_protection_sectors = max_write_protection_sectors

    @property
    def size(self) -> Optional[int]:
        """Return the size of the flash memory in bytes."""
        if self.start is None or self.end is None:
            return None

        return self.end - self.start

    def num_pages(self) -> Optional[int]:
        """Return the number of pages in the flash memory."""
        if self.size is None or self.page_size is None:
            return None

        if isinstance(self.page_size, int):
            return self.size // self.page_size

        flash_size = self.size

        num_pages = 0
        for page_size in self.page_size:
            flash_size -= page_size
            num_pages += 1
            if flash_size <= 0:
                return num_pages

        raise ValueError(
            "Flash size is larger than the total size of all pages. "
            f"Flash size: {self.size}, total page size: {sum(self.page_size)}"
        )

    def num_sectors(self) -> Optional[int]:
        """Return the number of sectors in the flash memory."""
        num_pages = self.num_pages()
        if num_pages is None or self.pages_per_sector is None:
            return None

        return min(num_pages // self.pages_per_sector, self.max_write_protection_sectors)
