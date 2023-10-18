from pathlib import Path

from stm32loader.main import Stm32Loader
from stm32loader.bootloader import Stm32Bootloader

ACK = Stm32Bootloader.Reply.ACK.value


FIRMWARE_FILE = Path(__file__).parent / "../../firmware/generic_boot20_pc13.binary.bin"


class FakeConnection:

    def __init__(self):
        self.is_command = True
        self.next_return = []
        self.timeout = 2

    def write(self, data):
        if self.is_command:
            # print("Command", data)

            if data == Stm32Bootloader.Command.GET:
                # Return length, version, commands, ack
                self.next_return.append(2)
                self.next_return.append(0x11)
                self.next_return.append(0x0)
                self.next_return.append(Stm32Bootloader.Reply.ACK)

        self.is_command = not self.is_command

    def read(self, length=1):
        if length == 121:
            return bytes([0] * 121)

        if self.next_return:
            value = self.next_return.pop(0)
            if isinstance(value, int):
                return [value]
            return value

        return [Stm32Bootloader.Reply.ACK]


class FakeConfiguration:

    def __init__(self, erase, write, verify, firmware_file):
        self.erase = erase
        self.write = write
        self.verify = verify
        self.data_file = firmware_file
        self.unprotect = False
        self.protect = False
        self.length = None
        self.verbosity = 5
        self.address = 0x_0800_0000
        self.go_address = None
        self.family = "F1"


def erase_write_verify():
    loader = Stm32Loader()
    loader.configuration = FakeConfiguration(erase=True, write=True, verify=True, firmware_file=FIRMWARE_FILE)
    loader.connection = FakeConnection()
    loader.stm32 = Stm32Bootloader(loader.connection, device_family="F1")

    # GET
    loader.connection.next_return.extend([ACK, 1, 0x05, 0x44, ACK])
    # Device ID
    loader.connection.next_return.extend([ACK, 1, [0x04, 0x12], ACK])
    loader.read_device_id()

    # Read flash size
    loader.connection.next_return.extend([ACK, ACK, ACK, [0x00, 0x01], ACK])
    # Read device UID
    loader.connection.next_return.extend([ACK, ACK, list(range(12)), ACK])
    loader.read_device_uid()

    loader.perform_commands()


if __name__ == "__main__":
    erase_write_verify()
