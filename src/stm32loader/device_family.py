"""Offer information about STM32 device families."""

import enum


@enum.unique
class DeviceFamily(enum.Enum):
    """Enumeration of STM32 device families."""

    # AN2606
    C0 = "C0"
    F0 = "F0"
    F1 = "F1"
    F2 = "F2"
    F3 = "F3"
    F4 = "F4"
    F7 = "F7"
    G0 = "G0"
    G4 = "G4"
    H5 = "H5"
    H7 = "H7"
    L0 = "L0"
    L1 = "L1"
    L4 = "L4"
    L5 = "L5"
    WBA = "WBA"
    WB = "WB"
    WL = "WL"
    U5 = "U5"
    # Not sure if these really exist?
    W = "W"

    # Non-STM devices.
    NRG = "NRG"
    WIZ = "WIZ"


@enum.unique
class DeviceFlag(enum.IntEnum):
    """Represent device functionality as composable flags."""

    NONE = 0
    OBL_LAUNCH = 1
    CLEAR_PEMPTY = 2
    # For some reason, F4 (at least, NUCLEO F401RE) can't read the 12 or 2
    # bytes for UID and flash size directly.
    # Reading a whole chunk of 256 bytes at 0x1FFFA700 does work and
    # requires some data extraction.
    LONG_UID_ACCESS = 8
    FORCE_PARITY_NONE = 16


class DeviceFamilyInfo:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Hold info about an STM32 device family."""

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        name,
        uid_address=None,
        flash_size_address=None,
        flash_page_size=1024,
        transfer_size=256,
        mass_erase=True,
        option_bytes=None,
        bootloader_id_address=None,
        flags=DeviceFlag.NONE,
    ):
        self.name = name
        self.uid_address = uid_address
        self.flash_size_address = flash_size_address
        self.flash_page_size = flash_page_size
        self.transfer_size = transfer_size
        self.mass_erase = mass_erase
        self.option_bytes = option_bytes
        self.bootloader_id_address = bootloader_id_address
        self.family_default_flags = flags


DEVICE_FAMILIES = {
    DeviceFamily.C0: DeviceFamilyInfo("C0", bootloader_id_address=0x_1FFF_17FE),
    # RM0360
    DeviceFamily.F0: DeviceFamilyInfo(
        "F0", flash_size_address=0x_1FFF_F7CC, option_bytes=(0x_1FFF_F800, 0x_1FFF_F80F)
    ),
    # RM0008
    DeviceFamily.F1: DeviceFamilyInfo(
        "F1",
        uid_address=0x_1FFF_F7E8,
        flash_size_address=0x_1FFF_F7E0,
        option_bytes=(0x_1FFF_F800, 0x_1FFF_F80F),
    ),
    DeviceFamily.F2: DeviceFamilyInfo(
        "F2", option_bytes=(0x_1FFF_C000, 0x_1FFF_C00F), bootloader_id_address=0x_1FFF_77DE
    ),
    # RM0366, RM0365, RM0316, RM0313, RM4510
    DeviceFamily.F3: DeviceFamilyInfo(
        "F3",
        uid_address=0x_1FFF_F7AC,
        flash_size_address=0x_1FFF_F7CC,
        flash_page_size=2048,
        bootloader_id_address=0x_1FFF_F796,
    ),
    # RM0090
    DeviceFamily.F4: DeviceFamilyInfo(
        "F4",
        uid_address=0x_1FFF_7A10,
        flash_size_address=0x_1FFF_7A22,
        bootloader_id_address=0x_1FFF_76DE,
        flags=DeviceFlag.LONG_UID_ACCESS,
    ),
    # RM0385
    DeviceFamily.F7: DeviceFamilyInfo(
        "F7",
        uid_address=0x_1FF0_F420,
        flash_size_address=0x_1FF0_F442,
        bootloader_id_address=0x_1FF0_EDBE,
    ),
    # RM0444
    DeviceFamily.G0: DeviceFamilyInfo(
        "G0", uid_address=0x_1FFF_7590, flash_size_address=0x_1FFF_75E0
    ),
    DeviceFamily.G4: DeviceFamilyInfo(
        "G4",
        uid_address=0x1FFF7590,
        flash_size_address=0x1FFF75E0,
        bootloader_id_address=0x_1FFF_6FFE,
    ),
    DeviceFamily.H5: DeviceFamilyInfo(
        "H5",
    ),
    # RM0433
    DeviceFamily.H7: DeviceFamilyInfo(
        "H7",
        uid_address=0x_1FF1_E800,
        flash_size_address=0x_1FF1_E880,
        flash_page_size=128 * 1024,
    ),
    # FIXME TWO RMs?
    # RM0451, RM4510
    DeviceFamily.L0: DeviceFamilyInfo(
        "L0",
        uid_address=0x_1FF8_0050,
        flash_size_address=0x_1FF8_007C,
        transfer_size=128,
        flash_page_size=128,
        mass_erase=False,
        flags=DeviceFlag.LONG_UID_ACCESS,
    ),
    DeviceFamily.L1: DeviceFamilyInfo("L1", mass_erase=False),
    # RM0394
    DeviceFamily.L4: DeviceFamilyInfo(
        "L4",
        uid_address=0x_1FFF_7590,
        flash_size_address=0x_1FFF_75E0,
        bootloader_id_address=0x_1FFF_6FFE,
    ),
    DeviceFamily.L5: DeviceFamilyInfo(
        "L5",
    ),
    DeviceFamily.WBA: DeviceFamilyInfo(
        "WBA",
    ),
    DeviceFamily.WB: DeviceFamilyInfo(
        "WB",
    ),
    # RM0453
    DeviceFamily.WL: DeviceFamilyInfo(
        "WL", uid_address=0x_1FFF_7590, flash_size_address=0x_1FFF_75E0
    ),
    DeviceFamily.U5: DeviceFamilyInfo(
        "U5",
    ),
    DeviceFamily.W: DeviceFamilyInfo(
        "W",
    ),
    # ST BlueNRG series; see ST AN4872 (BlueNRG-1/2)
    # and AN5471 (BlueNRG-LP/LPS).
    # BlueNRG requires parity 'none'.
    #   Product ID:
    #       Byte 1: metal fix (masked out)
    #       Byte 2: mask set (masked out)
    #       Byte 3: 0xHL
    #           H: [0] BlueNRG-1, [2] BlueNRG-2, [3] BlueNRG-LP/LPS
    #           L: [3] 160kB, [B] 192kB, [F] 256kB
    #   There is no access to peripherals/system memory from bootloader,
    #   so flash size and UID can not be read.
    #       NRG-1/2: flash_size_address=0x_4010_0014, uid_address=0x_1000_07F4
    #       NRG-LP:  flash_size_address=0x_4000_1014, uid_address=0x_1000_1EF0
    DeviceFamily.NRG: DeviceFamilyInfo(
        "NRG", flags=DeviceFlag.FORCE_PARITY_NONE, flash_page_size=2048
    ),
    DeviceFamily.WIZ: DeviceFamilyInfo(
        "WIZ",
    ),
}


@enum.unique
class BootloaderSerialPeripherals(enum.IntEnum):
    """Enumeration of bootloader serial interface peripherals."""

    # AN2606
    USART = 1
    DUAL_USART = 2
    UART_CAN_DFU = 3
    USART_DFU = 4
    USART_I2C = 5
    I2C = 6
    I2C_CAN_DFU_I2C = 7
    I2C_SPI = 8
    USART_CAN_FDCAN_DFU_I2C_SPI = 9
    USART_DFU_FDCAN_SPI = 10
    USART_I2C_SPI = 11
    USART_SPI = 12
    USART_DFU_I2C_SPI = 13
    USART_DFU_I2C_I3C_FDCAN_SPI = 14
