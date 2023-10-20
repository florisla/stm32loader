import enum


@enum.unique
class DeviceFamily(enum.Enum):
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
    NRG1 = "NRG1"
    NRG2 = "NRG2"
    WIZ = "WIZ"


class DeviceFamilyInfo:

    def __init__(
            self,
            uid_address=None,
            flash_size_address=None,
            flash_page_size=1024,
            transfer_size=256,
            mass_erase=True,
            option_bytes=None,
    ):
        self.uid_address = uid_address
        self.flash_size_address = flash_size_address
        self.flash_page_size = flash_page_size
        self.transfer_size = transfer_size
        self.mass_erase = mass_erase
        self.option_bytes = option_bytes


DEVICE_FAMILIES = {
    DeviceFamily.C0: DeviceFamilyInfo(),
    # RM0360
    DeviceFamily.F0: DeviceFamilyInfo(flash_size_address=0x1FFFF7CC, option_bytes=(0x1FFFF800, 0x1FFFF80F)),
    # RM0008
    DeviceFamily.F1: DeviceFamilyInfo(uid_address=0x1FFFF7E8, flash_size_address=0x1FFFF7E0, option_bytes=(0x1FFFF800, 0x1FFFF80F)),
    DeviceFamily.F2: DeviceFamilyInfo(option_bytes=(0x1FFFC000, 0x1FFFC00F)),
    # RM0366, RM0365, RM0316, RM0313, RM4510
    DeviceFamily.F3: DeviceFamilyInfo(uid_address=0x1FFFF7AC, flash_size_address=0x1FFFF7CC, flash_page_size=2048),
    # RM0090
    DeviceFamily.F4: DeviceFamilyInfo(uid_address=0x1FFF7A10, flash_size_address=0x1FFF7A22),
    # RM0385
    DeviceFamily.F7: DeviceFamilyInfo(uid_address=0x1FF0F420, flash_size_address=0x1FF0F442),
    # RM0444
    DeviceFamily.G0: DeviceFamilyInfo(uid_address=0x1FFF7590, flash_size_address=0x1FFF75E0),
    DeviceFamily.G4: DeviceFamilyInfo(),
    DeviceFamily.H5: DeviceFamilyInfo(),
    # RM0433
    DeviceFamily.H7: DeviceFamilyInfo(uid_address=0x1FF1E800, flash_size_address=0x1FF1E880, flash_page_size=128 * 1024),
    # FIXME TWO RMs?
    # RM0451, RM4510
    DeviceFamily.L0: DeviceFamilyInfo(uid_address=0x1FF80050, flash_size_address=0x1FF8007C, transfer_size=128, flash_page_size=128, mass_erase=False),
    DeviceFamily.L1: DeviceFamilyInfo(mass_erase=False),
    # RM0394
    DeviceFamily.L4: DeviceFamilyInfo(uid_address=0x1FFF7590, flash_size_address=0x1FFF75E0),
    DeviceFamily.L5: DeviceFamilyInfo(),
    DeviceFamily.WBA: DeviceFamilyInfo(),
    DeviceFamily.WB: DeviceFamilyInfo(),
    # RM0453
    DeviceFamily.WL: DeviceFamilyInfo(uid_address=0x1FFF7590, flash_size_address=0x1FFF75E0),
    DeviceFamily.U5: DeviceFamilyInfo(),
    DeviceFamily.W: DeviceFamilyInfo(),
    # ST BlueNRG has DIE_ID register with PRODUCT, but no UID.
    # NRG BlueNRG-2 datasheet
    # Flash page size: 128 pages of 8 * 64 * 4 bytes
    DeviceFamily.NRG1: DeviceFamilyInfo(flash_size_address=0x40100014, flash_page_size=2048),
    DeviceFamily.NRG2: DeviceFamilyInfo(flash_size_address=0x40100014, flash_page_size=2048),
    DeviceFamily.WIZ: DeviceFamilyInfo(),
}


class DeviceInfo:

    def __init__(self, device_family, device_name, variant, product_line, product_id, bootloader_id, ram, system_memory):
        self.device_family = DeviceFamily[device_family]
        self.device_name = device_name
        self.product_line = product_line
        self.product_id = product_id
        self.bootloader_id = bootloader_id
        self.ram = ram
        self.system_memory = system_memory

    @property
    def ram_size(self):
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
    def system_memory_size(self):
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
        return self.device_name


DEVICE_DETAILS = [
    # Based on ST AN2606 section "Device-dependent bootloader parameters"
    # Key: ProductID, BootloaderID
    DeviceInfo("C0", "STM32C011xx", "", "", 0x443, 0x51, (0x_2000_0000, 0x_2000_3000), (0x_1FFF_0000, 0x_1FFF_1800)),
    # Error in AN2606? Ram is mentioned as 0x_2000_2000 - 0x_2000_17FF
    DeviceInfo("C0", "STM32C031xx", "", "", 0x453, 0x52, (0x_2000_2000, 0x_2000_2800), (0x_1FFF_0000, 0x_1FFF_1800)),
    DeviceInfo("F0", "STM32F05xxx/STM32F030x8", "", "", 0x440, 0x21, (0x_2000_0800, 0x_2000_2000), (0x_1FFF_EC00, 0x_1FFF_F800)),
    DeviceInfo("F0", "STM32F03xx4/6", "", "", 0x444, 0x10, (0x_2000_0800, 0x_2000_1000), (0x_1FFF_EC00, 0x_1FFF_F800)),
    DeviceInfo("F0", "STM32F030xC", "", "", 0x442, 0x52, (0x_2000_1800, 0x_2000_8000), (0x_1FFF_D800, 0x_1FFF_F800)),
    DeviceInfo("F0", "STM32F04xxx", "", "", 0x445, 0xA1, None, (0x_1FFF_C400, 0x_1FFF_F800)),
    DeviceInfo("F0", "STM32F070x6", "", "", 0x445, 0xA2, None, (0x_1FFF_C400, 0x_1FFF_F800)),
    DeviceInfo("F0", "STM32F070xB", "", "", 0x448, 0xA2, None, (0x_1FFF_C800, 0x_1FFF_F800)),
    DeviceInfo("F0", "STM32F071xx/072xx", "", "", 0x448, 0xA1, (0x_2000_1800, 0x_2000_4000), (0x_1FFF_C800, 0x_1FFF_F800)),
    DeviceInfo("F0", "STM32F09xxx", 0x442, "", "",  0x50, None, (0x_1FFF_D800, 0x_1FFF_F800)),
    DeviceInfo("F1", "STM32F10xxx", "", "Low-density",  0x412, None, (0x_2000_0200, 0x_2000_2800), (0x_1FFF_F000, 0x_1FFF_F800)),
    DeviceInfo("F1", "STM32F10xxx", "", "Medium-density",  0x410, None, (0x_2000_0200, 0x_2000_5000), (0x_1FFF_F000, 0x_1FFF_F800)),
    DeviceInfo("F1", "STM32F10xxx", "", "High-density",  0x414, None, (0x_2000_0200, 0x_2001_0000), (0x_1FFF_F000, 0x_1FFF_F800)),
    DeviceInfo("F1", "STM32F10xxx", "", "Medium-density value", 0x420, 0x10, (0x_2000_0200, 0x_2000_2000), (0x_1FFF_F000, 0x_1FFF_F800)),
    DeviceInfo("F1", "STM32F10xxx", "", "High-density value", 0x428, 0x10, (0x_2000_0200, 0x_2000_8000), (0x_1FFF_F000, 0x_1FFF_F800)),
    DeviceInfo("F1", "STM32F105xx/107xx", "", "Connectivity", 0x418, None, (0x_2000_1000, 0x_2001_0000), (0x_1FFF_B000, 0x_1FFF_F800)),
    DeviceInfo("F1", "STM32F10xxx", "", "XL-density", 0x430, 0x21, (0x_2000_0800, 0x_2001_8000), (0x_1FFF_E000, 0x_1FFF_F800)),
    DeviceInfo("F2", "STM32F2xxxx", "", "", 0x411, 0x20, (0x_2000_2000, 0x_2002_0000), (0x_1FFF_0000, 0x_1FFF_7800)),
    DeviceInfo("F2", "STM32F2xxxx", "", "", 0x411, 0x33, (0x_2000_2000, 0x_2002_0000), (0x_1FFF_0000, 0x_1FFF_7800)),
    DeviceInfo("F3", "STM32F373xx", "", "", 0x432, 0x41, (0x_2000_1400, 0x_2000_8000), (0x_1FFF_D800, 0x_1FFF_F800)),
    DeviceInfo("F3", "STM32F378xx", "", "", 0x432, 0x50, (0x_2000_1000, 0x_2000_8000), (0x_1FFF_D800, 0x_1FFF_F800)),
    DeviceInfo("F3", "STM32F302xB(C)/303xB(C)", "", "", 0x422, 0x41, (0x_2000_1400, 0x_2000_A000), (0x_1FFF_D800, 0x_1FFF_F800)),
    DeviceInfo("F3", "STM32F358xx", "", "", 0x422, 0x50, (0x_2000_1400, 0x_2000_A000), (0x_1FFF_D800, 0x_1FFF_F800)),
    DeviceInfo("F3", "STM32F301xx/302x4(6/8)", "", "", 0x439, 0x40, (0x_2000_1800, 0x_2000_4000), (0x_1FFF_D800, 0x_1FFF_F800)),
    DeviceInfo("F3", "STM32F318xx", "", "", 0x439, 0x50, (0x_2000_1800, 0x_2000_4000), (0x_1FFF_D800, 0x_1FFF_F800)),
    DeviceInfo("F3", "STM32F303x4(6/8)/334xx/328xx", "", "", 0x438, 0x50, (0x_2000_1800, 0x_2000_3000), (0x_1FFF_D800, 0x_1FFF_F800)),
    DeviceInfo("F3", "STM32F302xD(E)/303xD(E)", "", "", 0x446, 0x40, (0x_2000_1800, 0x_2001_0000), (0x_1FFF_D800, 0x_1FFF_F800)),
    DeviceInfo("F3", "STM32F398xx", "", "", 0x446, 0x50, (0x_2000_1800, 0x_2001_0000), (0x_1FFF_D800, 0x_1FFF_F800)),
    DeviceInfo("F4", "STM32F40xxx/41xxx", "", "", 0x413, 0x31, (0x_2000_2000, 0x_2002_0000), (0x_1FFF_0000, 0x_1FFF_7800)),
    DeviceInfo("F4", "STM32F40xxx/41xxx", "", "", 0x413, 0x91, (0x_2000_3000, 0x_2002_0000), (0x_1FFF_0000, 0x_1FFF_7800)),
    DeviceInfo("F4", "STM32F42xxx/43xxx", "", "", 0x419, 0x70, (0x_2000_3000, 0x_2003_0000), (0x_1FFF_0000, 0x_1FFF_7800)),
    DeviceInfo("F4", "STM32F42xxx/43xxx", "", "", 0x419, 0x91, (0x_2000_3000, 0x_2003_0000), (0x_1FFF_0000, 0x_1FFF_7800)),
    # check ram upper end
    DeviceInfo("F4", "STM32F401xB(C)", "", "", 0x423, 0xD1, (0x_2000_3000, 0x_2001_0000), (0x_1FFF_0000, 0x_1FFF_7800)),
    DeviceInfo("F4", "STM32F401xD(E)", "", "", 0x433, 0xD1, (0x_2000_3000, 0x_2001_8000), (0x_1FFF_0000, 0x_1FFF_7800)),
    DeviceInfo("F4", "STM32F410xx", "", "", 0x458, 0xB1, (0x_2000_3000, 0x_2000_8000), (0x_1FFF_0000, 0x_1FFF_7800)),
    DeviceInfo("F4", "STM32F411xx", "", "", 0x431, 0xD0, (0x_2000_3000, 0x_2002_0000), (0x_1FFF_0000, 0x_1FFF_7800)),
    DeviceInfo("F4", "STM32F412xx", "", "", 0x441, 0x90, (0x_2000_3000, 0x_2004_0000), (0x_1FFF_0000, 0x_1FFF_7800)),
    DeviceInfo("F4", "STM32F446xx", "", "", 0x421, 0x90, (0x_2000_3000, 0x_2002_0000), (0x_1FFF_0000, 0x_1FFF_7800)),
    DeviceInfo("F4", "STM32F469xx/479xx", "", "", 0x434, 0x90, (0x_2000_3000, 0x_2006_0000), (0x_1FFF_0000, 0x_1FFF_7800)),
    DeviceInfo("F4", "STM32F413xx/423xx", "", "", 0x463, 0x90, (0x_2000_3000, 0x_2005_0000), (0x_1FFF_0000, 0x_1FFF_7800)),
    DeviceInfo("F7", "STM32F72xxx/73xxx", "", "", 0x452, 0x90, (0x_2000_4000, 0x_2004_0000), (0x_1FF0_0000, 0x_1FF0_EDC0)),
    DeviceInfo("F7", "STM32F74xxx/75xxx", "", "", 0x449, 0x70, (0x_2000_4000, 0x_2005_0000), (0x_1FF0_0000, 0x_1FF0_EDC0)),
    DeviceInfo("F7", "STM32F74xxx/75xxx", "", "", 0x449, 0x90, (0x_2000_4000, 0x_2005_0000), (0x_1FF0_0000, 0x_1FF0_EDC0)),
    DeviceInfo("F7", "STM32F76xxx/77xxx", "", "", 0x451, 0x93, (0x_2000_4000, 0x_2008_0000), (0x_1FF0_0000, 0x_1FF0_EDC0)),
    DeviceInfo("G0", "STM32G03xxx/04xxx", "", "", 0x466, 0x52, (0x_2000_1000, 0x_2000_2000), (0x_1FFF_0000, 0x_1FFF_2000)),
    DeviceInfo("G0", "STM32G07xxx/08xxx", "", "", 0x460, 0xB3, (0x_2000_2700, 0x_2000_9000), (0x_1FFF_0000, 0x_1FFF_7000)),
    DeviceInfo("G0", "STM32G0B0xx", "", "", 0x467, 0xD0, (0x_2000_4000, 0x_2002_0000), ((0x_1FFF_0000, 0x_1FFF_7000), (0x_1FFF_8000, 0x_1FFF_F000))),
    DeviceInfo("G0", "STM32G0B1xx/0C1xx", "", "", 0x467, 0x92, (0x_2000_4000, 0x_2002_0000), ((0x_1FFF_0000, 0x_1FFF_6000), (0x_1FFF_8000, 0x_1FFF_F000))),
    # Note: STM32flash has 0x_2000_4800 as upper flash range.
    DeviceInfo("G0", "STM32G05xxx/061xx", "", "", 0x456, 0x51, (0x_2000_1000, 0x_2000_2000), (0x_1FFF_0000, 0x_1FFF_1000)),
    DeviceInfo("G4", "STM32G431xx/441xx", "", "", 0x468, 0xD4, (0x_2000_4000, 0x_2000_5800), (0x_1FFF_0000, 0x_1FFF_7000)),
    DeviceInfo("G4", "STM32G47xxx/48xxx", "", "", 0x469, 0xD5, (0x_2000_4000, 0x_2001_8000), (0x_1FFF_0000, 0x_1FFF_7000)),
    DeviceInfo("G4", "STM32G491xx/A1xx", "", "", 0x479, 0xD2, (0x_2000_4000, 0x_2001_C000), (0x_1FFF_0000, 0x_1FFF_7000)),
    DeviceInfo("H5", "STM32H503xx", "", "", 0x474, 0xE1, (0x_2000_4000, 0x_2000_8000), (0x_0BF8_7000, 0x_0BF9_0000)),
    DeviceInfo("H5", "STM32H563xx/573xx", "", "", 0x484, 0xE3, (0x_2000_0000, 0x_200A_0000), (0x_0BF9_7000, 0x_0BFA_0000)),
    DeviceInfo("H7", "STM32H72xxx/73xxx", "", "", 0x483, 0x93, ((0x_2000_4100, 0x_2002_0000), (0x_2400_4000, 0x_2405_0000)), (0x_1FF0_0000, 0x_1FF1_E800)),
    DeviceInfo("H7", "STM32H74xxx/75xxx", "", "", 0x450, 0x91, ((0x_2000_4100, 0x_2002_0000), (0x_2400_5000, 0x_2408_0000)), (0x_1FF0_0000, 0x_1FF1_E800)),
    DeviceInfo("H7", "STM32H7A3xx/B3xx", "", "", 0x480, 0x92, ((0x_2000_4100, 0x_2002_0000), (0x_2403_4000, 0x_2408_0000)), (0x_1FF0_0000, 0x_1FF1_4000)),
    DeviceInfo("L0", "STM32L01xxx/02xxx", "", "", 0x457, 0xC3, None, (0x_1FF0_0000, 0x_1FF0_1000)),
    DeviceInfo("L0", "STM32L031xx/041xx", "", "", 0x425, 0xC0, (0x_2000_1000, 0x_2000_2000), (0x_1FF0_0000, 0x_1FF0_1000)),
    DeviceInfo("L0", "STM32L05xxx/06xxx", "", "", 0x417, 0xC0, (0x_2000_1000, 0x_2000_2000), (0x_1FF0_0000, 0x_1FF0_1000)),
    # Note: STM32flash has 0x_2000_2000 as lower flash range.
    DeviceInfo("L0", "STM32L07xxx/08xxx", "", "", 0x447, 0x41, (0x_2000_1000, 0x_2000_5000), (0x_1FF0_0000, 0x_1FF0_2000)),
    DeviceInfo("L0", "STM32L07xxx/08xxx", "", "", 0x447, 0xB2, (0x_2000_1400, 0x_2000_5000), (0x_1FF0_0000, 0x_1FF0_2000)),
    DeviceInfo("L1", "STM32L1xxx6(8/B)", "", "Medium-density ULP", 0x416, 0x20, (0x_2000_0800, 0x_2000_4000), (0x_1FF0_0000, 0x_1FF0_2000)),
    DeviceInfo("L1", "STM32L1xxx6(8/B)A", "", "", 0x429, 0x20, (0x_2000_1000, 0x_2000_8000), (0x_1FF0_0000, 0x_1FF0_2000)),
    DeviceInfo("L1", "STM32L1xxxC", "", "", 0x427, 0x40, (0x_2000_1000, 0x_2000_8000), (0x_1FF0_0000, 0x_1FF0_2000)),
    DeviceInfo("L1", "STM32L1xxxD", "", "", 0x436, 0x45, (0x_2000_1000, 0x_2000_C000), (0x_1FF0_0000, 0x_1FF0_2000)),
    DeviceInfo("L1", "STM32L1xxxE", "", "", 0x437, 0x40, (0x_2000_1000, 0x_2001_4000), (0x_1FF0_0000, 0x_1FF0_2000)),
    # Note: Stm32flash has 0x_2000_3100 as ram start.
    DeviceInfo("L4", "STM32L412xx/422xx", "", "Low-density", 0x464, 0xD1, (0x_2000_2100, 0x_2000_8000), (0x_1FFF_0000, 0x_1FFF_7000)),
    DeviceInfo("L4", "STM32L43xxx/44xxx", "", "", 0x435, 0x91, (0x_2000_3100, 0x_2000_C000), (0x_1FFF_0000, 0x_1FFF_7000)),
    DeviceInfo("L4", "STM32L45xxx/46xxx", "", "", 0x462, 0x92, (0x_2000_3100, 0x_2002_0000), (0x_1FFF_0000, 0x_1FFF_7000)),
    DeviceInfo("L4", "STM32L47xxx/48xxx", "", "", 0x415, 0xA3, (0x_2000_3000, 0x_2001_8000), (0x_1FFF_0000, 0x_1FFF_7000)),
    DeviceInfo("L4", "STM32L47xxx/48xxx", "", "", 0x415, 0x92, (0x_2000_3100, 0x_2001_8000), (0x_1FFF_0000, 0x_1FFF_7000)),
    DeviceInfo("L4", "STM32L496xx/4A6xx", "", "", 0x461, 0x93, (0x_2000_3100, 0x_2004_0000), (0x_1FFF_0000, 0x_1FFF_7000)),
    DeviceInfo("L4", "STM32L4Rxx/4Sxx", "", "", 0x470, 0x95, (0x_2000_3200, 0x_200A_0000), (0x_1FFF_0000, 0x_1FFF_7000)),
    DeviceInfo("L4", "STM32L4P5xx/Q5xx", "", "", 0x471, 0x90, (0x_2000_4000, 0x_2005_0000), (0x_1FFF_0000, 0x_1FFF_7000)),
    DeviceInfo("L5", "L5STM32L552xx/562xx", "", "", 0x472, 0x92, (0x_2000_4000, 0x_2004_0000), (0x_0BF9_0000, 0x_0BF9_8000)),
    DeviceInfo("WBA", "STM32WBA52xx", "", "", 0x492, 0xB0, (0x_2000_0000, 0x_2000_2000), (0x_0BF8_8000, 0x_0BF9_0000)),
    DeviceInfo("WB", "STM32WB10xx/15xx", "", "", 0x494, 0xB1, (0x_2000_5000, 0x_2004_0000), (0x_1FFF_0000, 0x_1FFF_7000)),
    DeviceInfo("WB", "STM32WB30xx/35xx/50xx/WB55xx", "", "", 0x495, 0xD5, (0x_2000_4000, 0x_2000_C000), (0x_1FFF_0000, 0x_1FFF_7000)),
    DeviceInfo("WL", "STM32WLE5xx/WL55xx", "", "", 0x497, 0xC4, (0x_2000_2000, 0x_2001_0000), (0x_1FFF_0000, 0x_1FFF_4000)),
    DeviceInfo("U5", "STM32U535xx/545xx", "", "", 0x455, 0x91, (0x_2000_4000, 0x_2024_0000), (0x_0BF9_0000, 0x_0BFA_0000)),
    DeviceInfo("U5", "STM32U575xx/ STM32U585xx", "", "", 0x482, 0x92, (0x_2000_4000, 0x_200C_0000), (0x_0BF9_0000, 0x_0BFA_0000)),
    DeviceInfo("U5", "STM32U595xx/599xx/5A9xx", "", "", 0x481, 0x92, (0x_2000_4000, 0x_2027_0000), (0x_0BF9_0000, 0x_0BFA_0000)),

    # Not yet in AN2606.  Bootloader IDs are unknown.
    # F1 is assumed here.
    DeviceInfo("F1", "STM32F103x8/B", "", "Medium-density performance", 0x641, None, (0x20000200, 0x20005000), (0x1FFFF000, 0x1FFFF800)),
    # WBA, WB, WL or simply 'W'?
    DeviceInfo("W", "STM32W 128k", "", "", 0x9A8, None, (0x20000200, 0x20002000), (0x08040000, 0x08040800)),
    DeviceInfo("W", "STM32W 256k", "", "", 0x9B0, None, (0x20000200, 0x20004000), (0x08040000, 0x08040800)),

    # ST BlueNRG
    DeviceInfo("NRG1", "BlueNRG-1", "160kB", "", 0x03, None, None, None),
    DeviceInfo("NRG1", "BlueNRG-1", "256kB", "", 0x0F, None, None, None),
    DeviceInfo("NRG2", "BlueNRG-1", "160kB", "", 0x23, None, None, None),
    DeviceInfo("NRG2", "BlueNRG-1", "256kB", "", 0x2F, None, None, None),

    # Wiznet W7500
    DeviceInfo("WIZ", "Wiznet W7500", "", "", 0x801, None, None, None),
]

DEVICES = {(dev.product_id, dev.bootloader_id): dev for dev in DEVICE_DETAILS}
